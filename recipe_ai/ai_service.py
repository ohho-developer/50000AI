import google.generativeai as genai
import json
import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)


class RecipeAIService:
    """Gemini API를 사용한 레시피 추천 및 요약 서비스"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Gemini API 초기화
        
        Args:
            max_retries: API 호출 실패 시 최대 재시도 횟수
            retry_delay: 재시도 간 대기 시간(초)
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _retry_on_error(self, func, *args, **kwargs):
        """API 호출 실패 시 재시도하는 래퍼 함수
        
        Args:
            func: 실행할 함수
            *args, **kwargs: 함수에 전달할 인자
            
        Returns:
            함수 실행 결과
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # 재시도 가능한 오류: 네트워크, 타임아웃, 할당량 초과 등
                retriable_errors = ['timeout', 'network', 'quota', '429', '500', '502', '503', '504']
                is_retriable = any(err in error_str for err in retriable_errors)
                
                if is_retriable and attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # 지수 백오프
                    logger.warning(f"Gemini API 오류, {wait_time}초 후 재시도 ({attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(wait_time)
                    continue
                
                # 재시도 불가능한 오류 또는 마지막 시도
                logger.error(f"Gemini API 오류 (재시도 불가 또는 최종 실패): {e}")
                raise
        
        # 모든 재시도 실패
        if last_error:
            raise last_error
    
    def recommend_menus(self, user_input: str) -> dict:
        """
        사용자 입력을 기반으로 음식 메뉴를 추천합니다.
        
        Args:
            user_input: 사용자가 입력한 텍스트 (예: "비 오는 날 뜨끈한 국물 요리")
        
        Returns:
            dict: {"foods": ["메뉴1", "메뉴2", "메뉴3", "메뉴4"], "status": "success"}
        """
        try:
            prompt = f"""
당신은 요리 추천 전문가입니다. 사용자의 요청에 따라 적절한 음식 메뉴를 추천해주세요.

규칙:
1. 정확히 4개의 메뉴를 추천하세요
2. 한국 요리를 우선적으로 추천하되, 다양한 메뉴를 포함하세요
3. 메뉴명은 간결하고 명확하게 작성하세요
4. JSON 형식으로만 응답하세요 (다른 설명은 포함하지 마세요)

응답 형식:
{{"foods": ["메뉴1", "메뉴2", "메뉴3", "메뉴4"]}}

사용자 요청: {user_input}
"""
            
            logger.info(f"Gemini API 호출 - 메뉴 추천: {user_input}")
            
            # 재시도 로직을 사용하여 API 호출
            response = self._retry_on_error(self.model.generate_content, prompt)
            response_text = response.text.strip()
            
            # JSON 파싱
            # 마크다운 코드 블록 제거
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # 응답 검증
            if 'foods' not in result or not isinstance(result['foods'], list):
                raise ValueError("잘못된 응답 형식")
            
            if len(result['foods']) < 3:
                raise ValueError("추천 메뉴가 너무 적습니다")
            
            logger.info(f"메뉴 추천 성공: {result['foods']}")
            return {"foods": result['foods'][:4], "status": "success"}
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}, 응답: {response_text}")
            return {
                "foods": [],
                "status": "error",
                "message": "AI 응답 형식이 올바르지 않습니다."
            }
        except Exception as e:
            logger.error(f"메뉴 추천 오류: {e}")
            return {
                "foods": [],
                "status": "error",
                "message": "메뉴 추천 중 오류가 발생했습니다."
            }
    
    def summarize_recipe_from_url(self, video_id: str, video_title: str) -> dict:
        """
        YouTube 링크로 직접 영상을 분석하여 레시피를 요약합니다. (Gemini 멀티모달 기능 사용)
        
        Args:
            video_id: YouTube 비디오 ID
            video_title: 영상 제목
        
        Returns:
            dict: {
                "ingredients": ["재료1", "재료2", ...],
                "steps": ["1단계", "2단계", ...],
                "status": "success"
            }
        """
        try:
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            
            prompt = f"""
당신은 요리 레시피 분석 전문가입니다. 이 유튜브 영상을 시청하고 레시피를 요약해주세요.

영상: {youtube_url}
제목: {video_title}

규칙:
1. 영상에서 사용하는 주요 재료를 모두 추출하세요 (계량 단위 포함)
2. 요리 순서를 시간 순서대로 명확하고 간결하게 정리하세요
3. 중요한 조리 팁이나 주의사항도 단계에 포함하세요
4. JSON 형식으로만 응답하세요 (다른 설명 없이)

응답 형식:
{{
  "ingredients": ["재료1 (분량)", "재료2 (분량)", ...],
  "steps": ["단계 1: 설명", "단계 2: 설명", ...]
}}
"""
            
            logger.info(f"Gemini API 호출 (YouTube URL) - 레시피 요약: {video_title}")
            
            # 재시도 로직을 사용하여 API 호출
            response = self._retry_on_error(self.model.generate_content, prompt)
            response_text = response.text.strip()
            
            # JSON 파싱
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # 응답 검증
            if 'ingredients' not in result or 'steps' not in result:
                raise ValueError("잘못된 응답 형식")
            
            if not result['ingredients'] or not result['steps']:
                raise ValueError("빈 레시피 데이터")
            
            logger.info(f"레시피 요약 성공 (URL 방식): {len(result['ingredients'])}개 재료, {len(result['steps'])}개 단계")
            return {
                "ingredients": result['ingredients'],
                "steps": result['steps'],
                "status": "success",
                "method": "url"
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류 (URL 방식): {e}")
            return {
                "ingredients": [],
                "steps": [],
                "status": "error",
                "message": "AI 응답 형식이 올바르지 않습니다.",
                "method": "url"
            }
        except Exception as e:
            logger.error(f"레시피 요약 오류 (URL 방식): {e}")
            return {
                "ingredients": [],
                "steps": [],
                "status": "error",
                "message": str(e),
                "method": "url"
            }
    
    def analyze_video_comments(self, video_title: str, comments: list) -> dict:
        """
        영상의 댓글을 분석하여 시청자 평가를 요약합니다.
        
        Args:
            video_title: 영상 제목
            comments: 댓글 리스트
        
        Returns:
            dict: {
                "comment_summary": "한 줄 요약",
                "rating": "매우긍정적/긍정적/보통/부정적/매우부정적",
                "difficulty": "매우쉬움/쉬움/보통/어려움/매우어려움",
                "has_analysis": true,
                "status": "success"
            }
        """
        try:
            # 댓글이 너무 많으면 제한
            comments_text = '\n'.join(comments[:20])
            
            prompt = f"""
당신은 YouTube 댓글 분석 전문가입니다. 아래 레시피 영상의 댓글들을 분석하여 요약해주세요.

영상 제목: {video_title}

댓글들:
{comments_text}

규칙:
1. 시청자들의 전반적인 평가를 5단계로 파악하세요:
   - "매우긍정적": 대부분이 매우 만족하고 추천하는 경우
   - "긍정적": 대부분이 만족하고 좋다고 하는 경우  
   - "보통": 긍정적과 부정적이 비슷하거나 중립적인 경우
   - "부정적": 대부분이 아쉬워하거나 개선점을 지적하는 경우
   - "매우부정적": 대부분이 매우 불만족하는 경우

2. 레시피의 난이도를 5단계로 평가하세요:
   - "매우쉬움": 초보자도 쉽게 따라할 수 있는 매우 간단한 요리
   - "쉬움": 기본적인 요리 경험이 있으면 쉽게 만들 수 있는 요리
   - "보통": 중간 정도의 요리 실력이 필요한 요리
   - "어려움": 상당한 요리 경험이나 기술이 필요한 요리
   - "매우어려움": 전문적인 기술이나 복잡한 과정이 필요한 요리

3. 댓글에서 자주 언급되는 맛, 특징, 팁을 50자 이내로 요약하세요
4. JSON 형식으로만 응답하세요

응답 형식:
{{
  "comment_summary": "한 줄 요약 (50자 이내)",
  "rating": "매우긍정적" 또는 "긍정적" 또는 "보통" 또는 "부정적" 또는 "매우부정적",
  "difficulty": "매우쉬움" 또는 "쉬움" 또는 "보통" 또는 "어려움" 또는 "매우어려움"
}}
"""
            
            logger.info(f"Gemini API 호출 - 댓글 분석: {video_title}")
            
            response = self._retry_on_error(self.model.generate_content, prompt)
            response_text = response.text.strip()
            
            # JSON 파싱
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # 응답 검증
            if 'comment_summary' not in result:
                raise ValueError("잘못된 응답 형식")
            
            logger.info(f"댓글 분석 성공: {result.get('rating', 'N/A')}, {result.get('difficulty', 'N/A')}")
            return {
                "comment_summary": result.get('comment_summary', ''),
                "rating": result.get('rating', '보통'),
                "difficulty": result.get('difficulty', '보통'),
                "has_analysis": True,
                "status": "success"
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류 (댓글 분석): {e}")
            return {
                "comment_summary": "",
                "rating": "보통",
                "difficulty": "보통",
                "has_analysis": False,
                "status": "error",
                "message": "댓글 분석 실패"
            }
        except Exception as e:
            logger.error(f"댓글 분석 오류: {e}")
            return {
                "comment_summary": "",
                "rating": "보통",
                "difficulty": "보통",
                "status": "error",
                "message": str(e)
            }
    
    def summarize_recipe_from_transcript(self, video_title: str, transcript: str) -> dict:
        """
        유튜브 영상 자막을 분석하여 레시피를 요약합니다. (폴백 방식)
        
        Args:
            video_title: 영상 제목
            transcript: 영상 자막 텍스트
        
        Returns:
            dict: {
                "ingredients": ["재료1", "재료2", ...],
                "steps": ["1단계", "2단계", ...],
                "status": "success"
            }
        """
        try:
            prompt = f"""
당신은 요리 레시피 분석 전문가입니다. 아래 유튜브 영상의 자막을 분석하여 레시피를 요약해주세요.

영상 제목: {video_title}

자막 내용:
{transcript[:5000]}  # 자막이 너무 길 경우를 대비해 제한

규칙:
1. 주요 재료만 추출하세요 (계량 단위 포함)
2. 요리 순서를 명확하고 간결하게 정리하세요
3. JSON 형식으로만 응답하세요

응답 형식:
{{
  "ingredients": ["재료1 (분량)", "재료2 (분량)", ...],
  "steps": ["단계 1: 설명", "단계 2: 설명", ...]
}}
"""
            
            logger.info(f"Gemini API 호출 (자막 방식) - 레시피 요약: {video_title}")
            
            # 재시도 로직을 사용하여 API 호출
            response = self._retry_on_error(self.model.generate_content, prompt)
            response_text = response.text.strip()
            
            # JSON 파싱
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # 응답 검증
            if 'ingredients' not in result or 'steps' not in result:
                raise ValueError("잘못된 응답 형식")
            
            logger.info(f"레시피 요약 성공 (자막 방식): {len(result['ingredients'])}개 재료, {len(result['steps'])}개 단계")
            return {
                "ingredients": result['ingredients'],
                "steps": result['steps'],
                "status": "success",
                "method": "transcript"
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}, 응답: {response_text}")
            return {
                "ingredients": [],
                "steps": [],
                "status": "error",
                "message": "AI 응답 형식이 올바르지 않습니다.",
                "method": "transcript"
            }
        except Exception as e:
            logger.error(f"레시피 요약 오류: {e}")
            return {
                "ingredients": [],
                "steps": [],
                "status": "error",
                "message": "레시피 요약 중 오류가 발생했습니다.",
                "method": "transcript"
            }

