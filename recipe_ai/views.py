from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging
import json

from .ai_service import RecipeAIService
from .youtube_service import YouTubeService
from .models import RecipeSearchHistory

logger = logging.getLogger(__name__)


@login_required
def index(request):
    """메인 입력 화면"""
    return render(request, 'recipe_ai/index.html')


@login_required
def recommend_menus(request):
    """사용자 입력을 받아 메뉴를 추천합니다"""
    if request.method != 'POST':
        return redirect('recipe_ai:index')
    
    user_input = request.POST.get('query', '').strip()
    
    if not user_input:
        messages.error(request, '검색어를 입력해주세요.')
        return redirect('recipe_ai:index')
    
    try:
        # 검색 기록 저장
        RecipeSearchHistory.objects.create(
            user=request.user,
            query=user_input
        )
        
        # 세션에 검색어 저장 (더보기 기능을 위해)
        request.session['last_recipe_query'] = user_input
        request.session['shown_menus'] = []  # 이미 보여준 메뉴 추적
        
        # AI 서비스 초기화 및 메뉴 추천
        ai_service = RecipeAIService()
        result = ai_service.recommend_menus(user_input)
        
        if result['status'] != 'success' or not result['foods']:
            messages.error(request, result.get('message', '메뉴 추천에 실패했습니다.'))
            return redirect('recipe_ai:index')
        
        # YouTube에서 각 메뉴의 썸네일 가져오기 (중복 방지 배치 처리)
        youtube_service = YouTubeService()
        thumbnail_results = youtube_service.search_menu_thumbnails_batch(result['foods'])
        
        logger.info(f"썸네일 검색 결과: {thumbnail_results}")
        
        menus_with_thumbnails = []
        for menu_name in result['foods']:
            thumbnail_result = thumbnail_results.get(menu_name, {})
            logger.info(f"메뉴 '{menu_name}' 썸네일 결과: {thumbnail_result}")
            
            menus_with_thumbnails.append({
                'name': menu_name,
                'thumbnail': thumbnail_result.get('thumbnail_url', ''),
                'has_thumbnail': thumbnail_result.get('status') == 'success'
            })
        
        # 세션에 보여준 메뉴 저장
        request.session['shown_menus'] = result['foods']
        
        context = {
            'query': user_input,
            'menus': menus_with_thumbnails
        }
        
        return render(request, 'recipe_ai/menu_recommend.html', context)
        
    except ValueError as e:
        logger.error(f"API 키 오류: {e}")
        messages.error(request, 'API 키가 설정되지 않았습니다. 관리자에게 문의하세요.')
        return redirect('recipe_ai:index')
    except Exception as e:
        logger.error(f"메뉴 추천 오류: {e}")
        messages.error(request, '오류가 발생했습니다. 다시 시도해주세요.')
        return redirect('recipe_ai:index')


@login_required
@require_http_methods(["POST"])
def recommend_more_menus(request):
    """추가 메뉴를 AJAX로 추천합니다"""
    try:
        # 세션에서 검색어와 이미 보여준 메뉴 가져오기
        user_query = request.session.get('last_recipe_query', '')
        shown_menus = request.session.get('shown_menus', [])
        
        if not user_query:
            return JsonResponse({
                'status': 'error',
                'message': '검색어를 찾을 수 없습니다. 다시 검색해주세요.'
            })
        
        # AI에게 추가 메뉴 추천 요청
        ai_service = RecipeAIService()
        
        # 프롬프트 수정 - 이미 추천한 메뉴 제외
        prompt_addition = f"\n\n이미 추천한 메뉴: {', '.join(shown_menus)}\n위 메뉴들은 제외하고 새로운 메뉴를 추천하세요."
        result = ai_service.recommend_menus(user_query + prompt_addition)
        
        if result['status'] != 'success' or not result['foods']:
            return JsonResponse({
                'status': 'error',
                'message': result.get('message', '추가 메뉴 추천에 실패했습니다.')
            })
        
        # YouTube 썸네일 가져오기 (기존 영상 제외)
        youtube_service = YouTubeService()
        thumbnail_results = youtube_service.search_menu_thumbnails_batch(result['foods'])
        
        new_menus = []
        for menu_name in result['foods']:
            thumbnail_result = thumbnail_results.get(menu_name, {})
            new_menus.append({
                'name': menu_name,
                'thumbnail': thumbnail_result.get('thumbnail_url', ''),
                'has_thumbnail': thumbnail_result.get('status') == 'success'
            })
        
        # 세션에 새 메뉴 추가
        updated_shown_menus = shown_menus + result['foods']
        request.session['shown_menus'] = updated_shown_menus
        
        return JsonResponse({
            'status': 'success',
            'menus': new_menus
        })
        
    except Exception as e:
        logger.error(f"추가 메뉴 추천 오류: {e}")
        return JsonResponse({
            'status': 'error',
            'message': '오류가 발생했습니다.'
        })


@login_required
def recipe_list(request, menu_name):
    """선택한 메뉴의 레시피 영상 목록을 보여줍니다 (처음 4개만)"""
    try:
        # 세션에 메뉴 이름 저장 (더보기용)
        request.session['current_menu'] = menu_name
        request.session['loaded_video_ids'] = []  # 이미 로드한 영상 ID 추적
        
        context = {
            'menu_name': menu_name
        }
        
        return render(request, 'recipe_ai/recipe_list.html', context)
        
    except Exception as e:
        logger.error(f"레시피 검색 오류: {e}")
        messages.error(request, '오류가 발생했습니다. 다시 시도해주세요.')
        return redirect('recipe_ai:index')


@login_required
@require_http_methods(["POST"])
def get_recipe_videos(request):
    """레시피 영상 ID 목록만 가져옵니다 (AJAX)"""
    try:
        data = json.loads(request.body)
        menu_name = data.get('menu_name', '')
        
        if not menu_name:
            return JsonResponse({
                'status': 'error',
                'message': '메뉴 이름이 없습니다.'
            })
        
        youtube_service = YouTubeService()
        result = youtube_service.search_recipe_videos(menu_name, max_results=20)
        
        if result['status'] != 'success' or not result['videos']:
            return JsonResponse({
                'status': 'error',
                'message': '레시피를 찾을 수 없습니다.'
            })
        
        # 영상 ID와 기본 정보만 반환 (조회수, 댓글 수 포함)
        video_list = [{
            'video_id': video['video_id'],
            'title': video['title'],
            'channel': video['channel'],
            'thumbnail': video['thumbnail'],
            'view_count': video.get('view_count', 0),
            'comment_count': video.get('comment_count', 0)
        } for video in result['videos']]
        
        return JsonResponse({
            'status': 'success',
            'videos': video_list
        })
        
    except Exception as e:
        logger.error(f"영상 목록 조회 오류: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def get_recipe_detail(request):
    """개별 레시피의 상세 정보와 댓글 분석을 가져옵니다 (AJAX)"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id', '')
        title = data.get('title', '')
        
        if not video_id:
            return JsonResponse({
                'status': 'error',
                'message': '비디오 ID가 없습니다.'
            })
        
        youtube_service = YouTubeService()
        ai_service = RecipeAIService()
        
        # 댓글 수집
        comments_result = youtube_service.get_video_comments(video_id, max_comments=15)
        
        response_data = {
            'video_id': video_id,
            'has_analysis': False,
            'comment_summary': '',
            'rating': '보통',
            'difficulty': '보통'
        }
        
        if comments_result['status'] == 'success' and comments_result['comments']:
            # AI 댓글 분석
            analysis = ai_service.analyze_video_comments(title, comments_result['comments'])
            
            if analysis['status'] == 'success':
                response_data.update({
                    'has_analysis': True,
                    'comment_summary': analysis['comment_summary'],
                    'rating': analysis['rating'],
                    'difficulty': analysis['difficulty']
                })
        
        return JsonResponse({
            'status': 'success',
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"레시피 상세 조회 오류: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@login_required
def recipe_detail(request, video_id):
    """선택한 레시피 영상의 상세 정보와 AI 요약을 보여줍니다 (Gemini 멀티모달 우선)"""
    try:
        youtube_service = YouTubeService()
        ai_service = RecipeAIService()
        
        # 영상 정보 가져오기
        video_info = youtube_service.get_video_info(video_id)
        
        if video_info['status'] != 'success':
            messages.error(request, video_info.get('message', '영상 정보를 가져올 수 없습니다.'))
            return redirect('recipe_ai:index')
        
        # ========================================
        # 1차 시도: Gemini 멀티모달 (YouTube URL 직접 분석)
        # ========================================
        logger.info(f"1차 시도: Gemini 멀티모달로 YouTube 링크 직접 분석 - {video_id}")
        summary_result = ai_service.summarize_recipe_from_url(video_id, video_info['title'])
        
        if summary_result['status'] == 'success':
            # 성공! URL 방식으로 요약 완료
            logger.info(f"✅ URL 방식 성공: {video_id}")
            context = {
                'video_id': video_id,
                'title': video_info['title'],
                'channel': video_info['channel'],
                'thumbnail': video_info['thumbnail'],
                'has_summary': True,
                'ingredients': summary_result['ingredients'],
                'steps': summary_result['steps'],
                'analysis_method': 'Gemini 영상 분석'  # 사용자에게 표시할 분석 방법
            }
            return render(request, 'recipe_ai/recipe_detail.html', context)
        
        # ========================================
        # 2차 시도: 자막 추출 후 분석 (폴백)
        # ========================================
        logger.info(f"1차 시도 실패, 2차 시도: 자막 추출 방식 - {video_id}")
        transcript_result = youtube_service.get_video_transcript(video_id)
        
        if transcript_result['status'] == 'success':
            # 자막이 있으면 자막으로 요약 시도
            summary_result = ai_service.summarize_recipe_from_transcript(
                video_info['title'],
                transcript_result['transcript']
            )
            
            if summary_result['status'] == 'success':
                # 성공! 자막 방식으로 요약 완료
                logger.info(f"✅ 자막 방식 성공: {video_id}")
                context = {
                    'video_id': video_id,
                    'title': video_info['title'],
                    'channel': video_info['channel'],
                    'thumbnail': video_info['thumbnail'],
                    'has_summary': True,
                    'ingredients': summary_result['ingredients'],
                    'steps': summary_result['steps'],
                    'analysis_method': 'Gemini 자막 분석'
                }
                return render(request, 'recipe_ai/recipe_detail.html', context)
        
        # ========================================
        # 모든 방법 실패
        # ========================================
        logger.error(f"❌ 모든 분석 방법 실패: {video_id}")
        
        # 자막 추출 실패 여부에 따라 다른 메시지
        if transcript_result['status'] != 'success':
            error_message = f"영상 분석과 자막 추출에 모두 실패했습니다. ({transcript_result.get('message', '자막 없음')})"
        else:
            error_message = f"레시피 요약에 실패했습니다. ({summary_result.get('message', 'AI 분석 오류')})"
        
        context = {
            'video_id': video_id,
            'title': video_info['title'],
            'channel': video_info['channel'],
            'thumbnail': video_info['thumbnail'],
            'has_summary': False,
            'error_message': error_message
        }
        return render(request, 'recipe_ai/recipe_detail.html', context)
        
    except ValueError as e:
        logger.error(f"API 키 오류: {e}")
        messages.error(request, 'API 키가 설정되지 않았습니다. 관리자에게 문의하세요.')
        return redirect('recipe_ai:index')
    except Exception as e:
        logger.error(f"레시피 상세 조회 오류: {e}")
        messages.error(request, '오류가 발생했습니다. 다시 시도해주세요.')
        return redirect('recipe_ai:index')
