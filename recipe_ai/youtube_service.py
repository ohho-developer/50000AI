from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import logging
import time
from django.conf import settings
from django.core.cache import cache
import hashlib
import json

logger = logging.getLogger(__name__)


class YouTubeService:
    """YouTube Data API를 사용한 영상 검색 및 자막 추출 서비스"""
    
    # 캐시 만료 시간 (초)
    CACHE_TIMEOUT = 604800  # 7일 (사용자 적을 때 API 절약)
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """YouTube API 초기화
        
        Args:
            max_retries: API 호출 실패 시 최대 재시도 횟수
            retry_delay: 재시도 간 대기 시간(초)
        """
        api_key = settings.YOUTUBE_API_KEY
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY가 설정되지 않았습니다.")
        
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """캐시 키 생성
        
        Args:
            prefix: 캐시 키 접두사
            *args, **kwargs: 해시에 포함할 파라미터들
        
        Returns:
            str: 생성된 캐시 키
        """
        # 파라미터들을 문자열로 변환하여 해시 생성
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"youtube:{prefix}:{key_hash}"
    
    def _get_cached_or_fetch(self, cache_key: str, fetch_func, *args, **kwargs):
        """캐시에서 데이터를 가져오거나, 없으면 fetch 후 캐싱
        
        Args:
            cache_key: 캐시 키
            fetch_func: 데이터를 가져올 함수
            *args, **kwargs: fetch_func에 전달할 인자
        
        Returns:
            캐시된 데이터 또는 새로 가져온 데이터
        """
        # 캐시 확인
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"캐시 히트: {cache_key}")
            return cached_data
        
        # 캐시 미스 - API 호출
        logger.info(f"캐시 미스: {cache_key}, API 호출")
        data = fetch_func(*args, **kwargs)
        
        # 성공한 경우에만 캐싱
        if data and data.get('status') == 'success':
            cache.set(cache_key, data, timeout=self.CACHE_TIMEOUT)
            logger.info(f"캐시 저장: {cache_key}")
        
        return data
    
    def _retry_on_error(self, func, *args, **kwargs):
        """API 호출 실패 시 재시도하는 래퍼 함수
        
        Args:
            func: 실행할 함수
            *args, **kwargs: 함수에 전달할 인자
            
        Returns:
            함수 실행 결과 또는 None (모든 재시도 실패 시)
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                last_error = e
                error_code = e.resp.status
                
                # 429 (할당량 초과), 500+ (서버 오류)는 재시도 가능
                if error_code in [429, 500, 502, 503, 504]:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # 지수 백오프
                        logger.warning(f"API 오류 (코드 {error_code}), {wait_time}초 후 재시도 ({attempt + 1}/{self.max_retries})")
                        time.sleep(wait_time)
                        continue
                
                # 403 (권한 오류), 400 (잘못된 요청) 등은 재시도 불가
                logger.error(f"API 오류 (재시도 불가): {e}")
                raise
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"오류 발생, {wait_time}초 후 재시도 ({attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(wait_time)
                    continue
                raise
        
        # 모든 재시도 실패
        if last_error:
            raise last_error
    
    def search_menu_thumbnails_batch(self, menu_names: list) -> dict:
        """
        여러 메뉴명에 대해 중복되지 않는 썸네일을 가져옵니다.
        
        Args:
            menu_names: 음식 메뉴 이름 리스트
        
        Returns:
            dict: {menu_name: {"thumbnail_url": "URL", "video_id": "ID", "status": "success"}, ...}
        """
        results = {}
        used_video_ids = set()  # 이미 사용된 비디오 ID 추적
        
        for menu_name in menu_names:
            try:
                # 각 메뉴당 최소한의 결과만 가져옴 (쿼터 절약)
                def search_func():
                    return self.youtube.search().list(
                        q=menu_name,
                        part='snippet',
                        type='video',
                        maxResults=3,  # 쿼터 절약을 위해 최소화 (중복 방지용)
                        regionCode='KR',
                        relevanceLanguage='ko',
                        fields='items(id/videoId,snippet/title,snippet/thumbnails/high/url)'
                    ).execute()
                
                search_response = self._retry_on_error(search_func)
                
                if not search_response.get('items'):
                    logger.warning(f"'{menu_name}' 검색 결과 없음")
                    results[menu_name] = {
                        "thumbnail_url": "",
                        "video_id": "",
                        "status": "error",
                        "message": "검색 결과가 없습니다."
                    }
                    continue
                
                # 중복되지 않는 첫 번째 영상 선택
                selected_item = None
                for item in search_response['items']:
                    video_id = item['id']['videoId']
                    if video_id not in used_video_ids:
                        selected_item = item
                        used_video_ids.add(video_id)
                        break
                
                # 모든 영상이 이미 사용된 경우 첫 번째 영상 사용
                if not selected_item:
                    selected_item = search_response['items'][0]
                    video_id = selected_item['id']['videoId']
                    used_video_ids.add(video_id)
                
                thumbnail_url = selected_item['snippet']['thumbnails']['high']['url']
                
                logger.info(f"'{menu_name}' 썸네일 검색 성공: {video_id}")
                results[menu_name] = {
                    "thumbnail_url": thumbnail_url,
                    "video_id": video_id,
                    "status": "success"
                }
                
            except HttpError as e:
                # YouTube API 할당량 초과 처리
                if e.resp.status == 403 and 'quota' in str(e).lower():
                    logger.error(f"YouTube API 할당량 초과 ({menu_name})")
                    results[menu_name] = {
                        "thumbnail_url": "",
                        "video_id": "",
                        "status": "quota_exceeded",
                        "message": "일일 검색 한도를 초과했습니다."
                    }
                else:
                    logger.error(f"YouTube API 오류 ({menu_name}): {e}")
                    results[menu_name] = {
                        "thumbnail_url": "",
                        "video_id": "",
                        "status": "error",
                        "message": f"YouTube API 오류: {e}"
                    }
            except Exception as e:
                logger.error(f"썸네일 검색 오류 ({menu_name}): {e}")
                results[menu_name] = {
                    "thumbnail_url": "",
                    "video_id": "",
                    "status": "error",
                    "message": str(e)
                }
        
        return results
    
    def search_menu_thumbnail(self, menu_name: str) -> dict:
        """
        메뉴명으로 검색하여 대표 썸네일 URL을 가져옵니다. (캐싱 적용)
        
        Args:
            menu_name: 음식 메뉴 이름
        
        Returns:
            dict: {"thumbnail_url": "URL", "video_id": "ID", "status": "success"}
        """
        # 캐시 키 생성
        cache_key = self._get_cache_key('menu_thumb', menu_name)
        
        # 캐시에서 가져오거나 API 호출
        def fetch_thumbnail():
            try:
                def search_func():
                    return self.youtube.search().list(
                        q=menu_name,
                        part='snippet',
                        type='video',
                        maxResults=1,
                        regionCode='KR',
                        relevanceLanguage='ko',
                        fields='items(id/videoId,snippet/title,snippet/thumbnails/high/url)'
                    ).execute()
                
                search_response = self._retry_on_error(search_func)
                
                if not search_response.get('items'):
                    logger.warning(f"'{menu_name}' 검색 결과 없음")
                    return {
                        "thumbnail_url": "",
                        "video_id": "",
                        "status": "error",
                        "message": "검색 결과가 없습니다."
                    }
                
                item = search_response['items'][0]
                thumbnail_url = item['snippet']['thumbnails']['high']['url']
                video_id = item['id']['videoId']
                
                logger.info(f"'{menu_name}' 썸네일 검색 성공: {video_id}")
                return {
                    "thumbnail_url": thumbnail_url,
                    "video_id": video_id,
                    "status": "success"
                }
                
            except HttpError as e:
                # YouTube API 할당량 초과 처리
                if e.resp.status == 403 and 'quota' in str(e).lower():
                    logger.error(f"YouTube API 할당량 초과 ({menu_name})")
                    return {
                        "thumbnail_url": "",
                        "video_id": "",
                        "status": "quota_exceeded",
                        "message": "일일 검색 한도를 초과했습니다."
                    }
                else:
                    logger.error(f"YouTube API 오류 ({menu_name}): {e}")
                    return {
                        "thumbnail_url": "",
                        "video_id": "",
                        "status": "error",
                        "message": f"YouTube API 오류: {e}"
                    }
            except Exception as e:
                logger.error(f"썸네일 검색 오류 ({menu_name}): {e}")
                return {
                    "thumbnail_url": "",
                    "video_id": "",
                    "status": "error",
                    "message": str(e)
                }
        
        return self._get_cached_or_fetch(cache_key, fetch_thumbnail)
    
    def search_recipe_videos(self, menu_name: str, max_results: int = 20) -> dict:
        """
        메뉴명으로 레시피 영상을 검색합니다. (캐싱 적용)
        
        Args:
            menu_name: 음식 메뉴 이름
            max_results: 검색할 영상 개수 (기본 20개, 순차 로딩용)
        
        Returns:
            dict: {
                "videos": [
                    {
                        "video_id": "ID",
                        "title": "제목",
                        "channel": "채널명",
                        "thumbnail": "썸네일 URL",
                        "description": "설명",
                        "view_count": 조회수,
                        "comment_count": 댓글수
                    },
                    ...
                ],
                "status": "success"
            }
        """
        # 캐시 키 생성
        cache_key = self._get_cache_key('recipe_videos', menu_name, max_results=max_results)
        
        # 캐시에서 가져오거나 API 호출
        def fetch_videos():
            return self._fetch_recipe_videos_from_api(menu_name, max_results)
        
        return self._get_cached_or_fetch(cache_key, fetch_videos)
    
    def _fetch_recipe_videos_from_api(self, menu_name: str, max_results: int) -> dict:
        """API에서 레시피 영상을 실제로 가져오는 내부 메서드"""
        try:
            search_query = f"{menu_name} 레시피"
            
            def search_func():
                return self.youtube.search().list(
                    q=search_query,
                    part='snippet',
                    type='video',
                    maxResults=max_results,
                    regionCode='KR',
                    relevanceLanguage='ko',
                    order='relevance',
                    fields='items(id/videoId,snippet/title,snippet/channelTitle,snippet/thumbnails/high/url,snippet/description)'
                ).execute()
            
            search_response = self._retry_on_error(search_func)
        
        except HttpError as e:
            # YouTube API 할당량 초과 처리
            if e.resp.status == 403 and 'quota' in str(e).lower():
                logger.error(f"YouTube API 할당량 초과: {menu_name}")
                return {
                    "videos": [],
                    "status": "quota_exceeded",
                    "message": "일일 검색 한도를 초과했습니다. 내일 다시 시도해주세요. 즐겨찾기한 레시피를 확인해보세요!"
                }
            # 기타 HTTP 오류
            logger.error(f"YouTube API 오류 ({menu_name}): {e}")
            return {
                "videos": [],
                "status": "error",
                "message": f"YouTube API 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }
        except Exception as e:
            logger.error(f"레시피 검색 오류 ({menu_name}): {e}")
            return {
                "videos": [],
                "status": "error",
                "message": "레시피를 가져오는 중 오류가 발생했습니다."
            }
        
        # 검색 결과 확인
        if not search_response.get('items'):
            logger.warning(f"'{search_query}' 검색 결과 없음")
            return {
                "videos": [],
                "status": "error",
                "message": "레시피 영상을 찾을 수 없습니다."
            }
        
        # 비디오 ID 목록 수집
        video_ids = [item['id']['videoId'] for item in search_response['items']]
        
        # 통계 정보를 한 번에 가져오기
        try:
            def stats_func():
                return self.youtube.videos().list(
                    part='statistics',
                    id=','.join(video_ids),
                    fields='items(id,statistics/viewCount,statistics/commentCount)'
                ).execute()
            
            stats_response = self._retry_on_error(stats_func)
        except Exception as e:
            logger.warning(f"통계 정보 조회 실패: {e}, 기본값 사용")
            stats_response = {'items': []}
        
        # 통계 정보를 딕셔너리로 매핑
        stats_map = {}
        if stats_response.get('items'):
            for item in stats_response['items']:
                video_id = item['id']
                statistics = item.get('statistics', {})
                stats_map[video_id] = {
                    'view_count': int(statistics.get('viewCount', 0)),
                    'comment_count': int(statistics.get('commentCount', 0))
                }
        
        videos = []
        for item in search_response['items']:
            video_id = item['id']['videoId']
            stats = stats_map.get(video_id, {'view_count': 0, 'comment_count': 0})
            
            video_data = {
                "video_id": video_id,
                "title": item['snippet']['title'],
                "channel": item['snippet']['channelTitle'],
                "thumbnail": item['snippet']['thumbnails']['high']['url'],
                "description": item['snippet']['description'],
                "view_count": stats['view_count'],
                "comment_count": stats['comment_count']
            }
            videos.append(video_data)
        
        logger.info(f"'{search_query}' 레시피 검색 성공: {len(videos)}개 영상")
        return {
            "videos": videos,
            "status": "success"
        }
    
    def get_video_info(self, video_id: str) -> dict:
        """
        비디오 ID로 영상 정보를 가져옵니다.
        
        Args:
            video_id: YouTube 비디오 ID
        
        Returns:
            dict: 영상 정보 (조회수, 댓글 수 포함)
        """
        try:
            def video_func():
                return self.youtube.videos().list(
                    part='snippet,statistics',
                    id=video_id,
                    fields='items(snippet/title,snippet/channelTitle,snippet/thumbnails/high/url,snippet/description,statistics/viewCount,statistics/commentCount)'
                ).execute()
            
            video_response = self._retry_on_error(video_func)
            
            if not video_response.get('items'):
                return {
                    "status": "error",
                    "message": "영상을 찾을 수 없습니다."
                }
            
            item = video_response['items'][0]
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            
            # 조회수와 댓글 수 파싱
            view_count = int(statistics.get('viewCount', 0))
            comment_count = int(statistics.get('commentCount', 0))
            
            return {
                "title": snippet['title'],
                "channel": snippet['channelTitle'],
                "thumbnail": snippet['thumbnails']['high']['url'],
                "description": snippet['description'],
                "view_count": view_count,
                "comment_count": comment_count,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"영상 정보 조회 오류 ({video_id}): {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_video_comments(self, video_id: str, max_comments: int = 20) -> dict:
        """
        영상의 댓글을 가져옵니다.
        
        Args:
            video_id: YouTube 비디오 ID
            max_comments: 가져올 댓글 개수 (기본 20개)
        
        Returns:
            dict: {
                "comments": ["댓글1", "댓글2", ...],
                "status": "success"
            }
        """
        try:
            def comment_func():
                return self.youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=max_comments,
                    order='relevance',  # 관련성 높은 댓글 우선
                    textFormat='plainText',
                    fields='items(snippet/topLevelComment/snippet/textDisplay)'
                ).execute()
            
            comment_response = self._retry_on_error(comment_func)
            
            if not comment_response.get('items'):
                logger.warning(f"'{video_id}' 댓글 없음")
                return {
                    "comments": [],
                    "status": "error",
                    "message": "댓글이 없습니다."
                }
            
            comments = []
            for item in comment_response['items']:
                comment_text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment_text)
            
            logger.info(f"댓글 수집 성공 ({video_id}): {len(comments)}개")
            return {
                "comments": comments,
                "status": "success"
            }
            
        except HttpError as e:
            # 댓글이 비활성화된 경우 등
            error_message = str(e)
            if 'commentsDisabled' in error_message or 'disabled comments' in error_message.lower():
                logger.warning(f"댓글이 비활성화됨 ({video_id})")
                return {
                    "comments": [],
                    "status": "error",
                    "message": "이 영상은 댓글이 비활성화되어 있습니다."
                }
            
            logger.error(f"YouTube 댓글 조회 오류 ({video_id}): {e}")
            return {
                "comments": [],
                "status": "error",
                "message": f"댓글 조회 오류: {e}"
            }
        except Exception as e:
            logger.error(f"댓글 수집 오류 ({video_id}): {e}")
            return {
                "comments": [],
                "status": "error",
                "message": str(e)
            }
    
    def get_video_transcript(self, video_id: str) -> dict:
        """
        영상의 자막을 추출합니다.
        
        Args:
            video_id: YouTube 비디오 ID
        
        Returns:
            dict: {
                "transcript": "전체 자막 텍스트",
                "language": "ko",
                "status": "success"
            }
        """
        try:
            # 한국어 자막 우선 시도
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(
                    video_id,
                    languages=['ko', 'ko-KR']
                )
            except NoTranscriptFound:
                # 영어 자막 시도
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(
                        video_id,
                        languages=['en', 'en-US']
                    )
                except NoTranscriptFound:
                    # 자동 생성 자막 사용
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # 자막 텍스트 조합
            transcript_text = ' '.join([item['text'] for item in transcript_list])
            
            logger.info(f"자막 추출 성공 ({video_id}): {len(transcript_text)} 글자")
            return {
                "transcript": transcript_text,
                "status": "success"
            }
            
        except TranscriptsDisabled:
            logger.warning(f"자막이 비활성화됨 ({video_id})")
            return {
                "transcript": "",
                "status": "error",
                "message": "이 영상은 자막이 제공되지 않습니다."
            }
        except NoTranscriptFound:
            logger.warning(f"자막을 찾을 수 없음 ({video_id})")
            return {
                "transcript": "",
                "status": "error",
                "message": "이 영상의 자막을 찾을 수 없습니다."
            }
        except Exception as e:
            logger.error(f"자막 추출 오류 ({video_id}): {e}")
            return {
                "transcript": "",
                "status": "error",
                "message": f"자막 추출 중 오류가 발생했습니다: {str(e)}"
            }

