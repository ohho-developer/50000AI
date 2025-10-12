from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
import logging
import json

from .ai_service import RecipeAIService
from .youtube_service import YouTubeService
from .models import RecipeSearchHistory, FavoriteRecipe

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
        messages.error(request, _('검색어를 입력해주세요.'))
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
        
        # 브라우저 언어 감지
        browser_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'ko')
        language = 'en' if browser_language.startswith('en') else 'ko'
        
        # AI 서비스 초기화 및 메뉴 추천
        ai_service = RecipeAIService()
        result = ai_service.recommend_menus(user_input, language=language)
        
        if result['status'] != 'success' or not result['foods']:
            messages.error(request, result.get('message', _('메뉴 추천에 실패했습니다.')))
            return redirect('recipe_ai:index')
        
        # 메뉴 리스트 생성 (썸네일 없이 텍스트만)
        menus_with_thumbnails = []
        for menu_name in result['foods']:
            menus_with_thumbnails.append({
                'name': menu_name,
                'thumbnail': '',  # 썸네일 제거
                'has_thumbnail': False  # 썸네일 없음
            })
        
        # 세션에 보여준 메뉴 저장
        request.session['shown_menus'] = result['foods']
        
        context = {
            'query': user_input,
            'menus': menus_with_thumbnails,
            'quota_exceeded': False  # 썸네일 제거로 할당량 문제 없음
        }
        
        return render(request, 'recipe_ai/menu_recommend.html', context)
        
    except ValueError as e:
        logger.error(f"API 키 오류: {e}")
        messages.error(request, 'API 키가 설정되지 않았습니다. 관리자에게 문의하세요.')
        return redirect('recipe_ai:index')
    except Exception as e:
        logger.error(f"메뉴 추천 오류: {e}")
        messages.error(request, _('오류가 발생했습니다. 다시 시도해주세요.'))
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
                'message': _('검색어를 찾을 수 없습니다. 다시 검색해주세요.')
            })
        
        # 브라우저 언어 감지
        browser_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'ko')
        language = 'en' if browser_language.startswith('en') else 'ko'
        
        # AI에게 추가 메뉴 추천 요청
        ai_service = RecipeAIService()
        
        # 프롬프트 수정 - 이미 추천한 메뉴 제외
        if language == 'en':
            prompt_addition = f"\n\nAlready recommended: {', '.join(shown_menus)}\nExclude the above and recommend new dishes."
        else:
            prompt_addition = f"\n\n이미 추천한 메뉴: {', '.join(shown_menus)}\n위 메뉴들은 제외하고 새로운 메뉴를 추천하세요."
        
        result = ai_service.recommend_menus(user_query + prompt_addition, language=language)
        
        if result['status'] != 'success' or not result['foods']:
            return JsonResponse({
                'status': 'error',
                'message': result.get('message', _('추가 메뉴 추천에 실패했습니다.'))
            })
        
        # 새로운 메뉴 리스트 생성 (썸네일 없이 텍스트만)
        new_menus = []
        for menu_name in result['foods']:
            new_menus.append({
                'name': menu_name,
                'thumbnail': '',  # 썸네일 제거
                'has_thumbnail': False  # 썸네일 없음
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
            'message': _('오류가 발생했습니다.')
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
        messages.error(request, _('오류가 발생했습니다. 다시 시도해주세요.'))
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
                'message': _('메뉴 이름이 없습니다.')
            })
        
        youtube_service = YouTubeService()
        result = youtube_service.search_recipe_videos(menu_name, max_results=20)
        
        # 할당량 초과 확인
        if result['status'] == 'quota_exceeded':
            return JsonResponse({
                'status': 'quota_exceeded',
                'message': result.get('message', _('일일 검색 한도를 초과했습니다. 내일 다시 시도해주세요.'))
            })
        
        if result['status'] != 'success' or not result['videos']:
            return JsonResponse({
                'status': 'error',
                'message': result.get('message', _('레시피를 찾을 수 없습니다.'))
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
                'message': _('비디오 ID가 없습니다.')
            })
        
        # 브라우저 언어 감지
        browser_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'ko')
        language = 'en' if browser_language.startswith('en') else 'ko'
        
        youtube_service = YouTubeService()
        ai_service = RecipeAIService()
        
        # 댓글 수집
        comments_result = youtube_service.get_video_comments(video_id, max_comments=15)
        
        # 언어별 기본값 설정
        default_rating = '보통' if language == 'ko' else 'Neutral'
        default_difficulty = '보통' if language == 'ko' else 'Medium'
        
        response_data = {
            'video_id': video_id,
            'has_analysis': False,
            'comment_summary': '',
            'rating': default_rating,
            'difficulty': default_difficulty
        }
        
        if comments_result['status'] == 'success' and comments_result['comments']:
            # AI 댓글 분석
            analysis = ai_service.analyze_video_comments(title, comments_result['comments'], language=language)
            
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
        # API 키 확인 (선택적)
        try:
            from django.conf import settings
            api_key = getattr(settings, 'GOOGLE_API_KEY', None)
            if not api_key:
                logger.warning("GOOGLE_API_KEY가 설정되지 않음 - 기본 YouTube 정보만 표시")
        except Exception as e:
            logger.warning(f"API 키 확인 중 오류: {e}")
        
        youtube_service = YouTubeService()
        ai_service = RecipeAIService()
        
        # 영상 정보 가져오기
        try:
            video_info = youtube_service.get_video_info(video_id)
            
            if video_info['status'] != 'success':
                # API 오류 시 기본 정보만 표시
                logger.warning(f"YouTube API 오류: {video_info.get('message', '알 수 없는 오류')}")
                context = {
                    'video_id': video_id,
                    'title': f'YouTube Video {video_id}',
                    'channel': 'Unknown Channel',
                    'thumbnail': '',
                    'has_summary': False,
                    'error_message': 'YouTube API 접근에 실패했습니다. 직접 YouTube에서 영상을 시청해주세요.'
                }
                return render(request, 'recipe_ai/recipe_detail.html', context)
        except Exception as e:
            logger.error(f"YouTube 서비스 오류: {e}")
            context = {
                'video_id': video_id,
                'title': f'YouTube Video {video_id}',
                'channel': 'Unknown Channel',
                'thumbnail': '',
                'has_summary': False,
                'error_message': 'YouTube 서비스에 접근할 수 없습니다. 직접 YouTube에서 영상을 시청해주세요.'
            }
            return render(request, 'recipe_ai/recipe_detail.html', context)
        
        # 브라우저 언어 감지
        browser_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'ko')
        language = 'en' if browser_language.startswith('en') else 'ko'
        
        # ========================================
        # 1차 시도: Gemini 멀티모달 (YouTube URL 직접 분석)
        # ========================================
        logger.info(f"1차 시도: Gemini 멀티모달로 YouTube 링크 직접 분석 - {video_id}")
        summary_result = ai_service.summarize_recipe_from_url(video_id, video_info['title'], language=language)
        
        if summary_result['status'] == 'success':
            # 성공! URL 방식으로 요약 완료
            logger.info(f"✅ URL 방식 성공: {video_id}")
            
            # 즐겨찾기 상태 확인
            is_favorite = FavoriteRecipe.objects.filter(
                user=request.user, 
                video_id=video_id
            ).exists()
            
            context = {
                'video_id': video_id,
                'title': video_info['title'],
                'channel': video_info['channel'],
                'thumbnail': video_info['thumbnail'],
                'view_count': video_info.get('view_count', 0),
                'comment_count': video_info.get('comment_count', 0),
                'has_summary': True,
                'ingredients': summary_result['ingredients'],
                'steps': summary_result['steps'],
                'ingredients_json': json.dumps(summary_result['ingredients'], ensure_ascii=False),
                'steps_json': json.dumps(summary_result['steps'], ensure_ascii=False),
                'analysis_method': 'Gemini 영상 분석',  # 사용자에게 표시할 분석 방법
                'is_favorite': is_favorite
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
                transcript_result['transcript'],
                language=language
            )
            
            if summary_result['status'] == 'success':
                # 성공! 자막 방식으로 요약 완료
                logger.info(f"✅ 자막 방식 성공: {video_id}")
                
                # 즐겨찾기 상태 확인
                is_favorite = FavoriteRecipe.objects.filter(
                    user=request.user, 
                    video_id=video_id
                ).exists()
                
                context = {
                    'video_id': video_id,
                    'title': video_info['title'],
                    'channel': video_info['channel'],
                    'thumbnail': video_info['thumbnail'],
                    'view_count': video_info.get('view_count', 0),
                    'comment_count': video_info.get('comment_count', 0),
                    'has_summary': True,
                    'ingredients': summary_result['ingredients'],
                    'steps': summary_result['steps'],
                    'ingredients_json': json.dumps(summary_result['ingredients'], ensure_ascii=False),
                    'steps_json': json.dumps(summary_result['steps'], ensure_ascii=False),
                    'analysis_method': 'Gemini 자막 분석',
                    'is_favorite': is_favorite
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
        
        # 즐겨찾기 상태 확인
        is_favorite = FavoriteRecipe.objects.filter(
            user=request.user, 
            video_id=video_id
        ).exists()
        
        context = {
            'video_id': video_id,
            'title': video_info['title'],
            'channel': video_info['channel'],
            'thumbnail': video_info['thumbnail'],
            'view_count': video_info.get('view_count', 0),
            'comment_count': video_info.get('comment_count', 0),
            'has_summary': False,
            'error_message': error_message,
            'is_favorite': is_favorite
        }
        return render(request, 'recipe_ai/recipe_detail.html', context)
        
    except ValueError as e:
        logger.error(f"API 키 오류: {e}")
        messages.error(request, 'API 키가 설정되지 않았습니다. 관리자에게 문의하세요.')
        return redirect('recipe_ai:index')
    except Exception as e:
        logger.error(f"레시피 상세 조회 오류: {e}", exc_info=True)
        messages.error(request, f'오류가 발생했습니다: {str(e)}')
        return redirect('recipe_ai:index')


@login_required
def favorite_recipe_detail(request, video_id):
    """즐겨찾기된 레시피의 상세 정보를 저장된 데이터로 보여줍니다"""
    try:
        logger.info(f"즐겨찾기 상세 페이지 호출: {video_id}")
        # 즐겨찾기에서 해당 레시피 찾기
        favorite = FavoriteRecipe.objects.get(user=request.user, video_id=video_id)
        
        # 저장된 데이터에서 정보 추출
        ingredients = []
        steps = []
        
        # 레시피 재료와 단계 파싱
        if favorite.recipe_ingredients:
            try:
                ingredients = json.loads(favorite.recipe_ingredients)
            except:
                ingredients = []
        
        if favorite.recipe_steps:
            try:
                steps = json.loads(favorite.recipe_steps)
            except:
                steps = []
        
        # 분석 방법 결정
        analysis_method = None
        if ingredients and steps:
            analysis_method = 'Gemini 영상 분석'  # 저장된 데이터가 있으면 영상 분석으로 표시
        elif favorite.comment_summary:
            analysis_method = 'Gemini 댓글 분석'  # 댓글 분석만 있는 경우
        
        context = {
            'video_id': favorite.video_id,
            'title': favorite.title,
            'channel': favorite.channel_name,
            'thumbnail': favorite.thumbnail_url,
            'has_summary': bool(ingredients and steps),
            'ingredients': ingredients,
            'steps': steps,
            'analysis_method': analysis_method,
            'is_favorite': True,  # 즐겨찾기에서 온 것이므로 즐겨찾기 상태로 표시
            'comment_summary': favorite.comment_summary,
            'sentiment_rating': favorite.sentiment_rating,
            'difficulty_rating': favorite.difficulty_rating,
            'view_count': favorite.view_count,
            'comment_count': favorite.comment_count
        }
        
        logger.info(f"✅ 즐겨찾기 레시피 상세 표시: {video_id} - 저장된 데이터 사용")
        logger.info(f"저장된 데이터: ingredients={len(ingredients)}, steps={len(steps)}, comment_summary={bool(favorite.comment_summary)}")
        return render(request, 'recipe_ai/recipe_detail.html', context)
        
    except FavoriteRecipe.DoesNotExist:
        messages.error(request, '해당 레시피를 찾을 수 없습니다.')
        return redirect('recipe_ai:favorite_list')
    except Exception as e:
        logger.error(f"즐겨찾기 레시피 상세 조회 오류: {e}", exc_info=True)
        messages.error(request, f'오류가 발생했습니다: {str(e)}')
        return redirect('recipe_ai:favorite_list')


@login_required
@require_http_methods(["POST"])
def enhance_favorite_with_ai(request):
    """즐겨찾기에 AI 분석 결과를 추가합니다 (백그라운드 작업)"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        
        if not video_id:
            return JsonResponse({'status': 'error', 'message': 'video_id가 필요합니다.'}, status=400)
        
        try:
            favorite = FavoriteRecipe.objects.get(user=request.user, video_id=video_id)
            
            # 이미 AI 분석이 완료되었는지 확인
            if favorite.comment_summary and favorite.recipe_ingredients:
                return JsonResponse({
                    'status': 'success', 
                    'message': '이미 AI 분석이 완료되었습니다.'
                })
            
            # AI 분석 수행
            ai_service = RecipeAIService()
            youtube_service = YouTubeService()
            
            # 브라우저 언어 감지
            browser_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'ko')
            language = 'en' if browser_language.startswith('en') else 'ko'
            
            # 레시피 요약 분석
            recipe_summary = None
            try:
                recipe_summary = ai_service.summarize_recipe_from_url(video_id, favorite.title, language=language)
                if recipe_summary['status'] != 'success':
                    # 자막 방식으로 재시도
                    transcript_result = youtube_service.get_video_transcript(video_id)
                    if transcript_result['status'] == 'success':
                        recipe_summary = ai_service.summarize_recipe_from_transcript(
                            favorite.title, transcript_result['transcript'], language=language
                        )
            except Exception as e:
                logger.error(f"레시피 분석 오류: {e}")
            
            # 댓글 분석
            analysis_result = None
            try:
                comments_result = youtube_service.get_video_comments(video_id, max_results=50)
                if comments_result['status'] == 'success' and comments_result['comments']:
                    analysis_result = ai_service.analyze_video_comments(
                        favorite.title, comments_result['comments'], language=language
                    )
            except Exception as e:
                logger.error(f"댓글 분석 오류: {e}")
            
            # 결과 업데이트
            if recipe_summary and recipe_summary.get('status') == 'success':
                favorite.recipe_ingredients = json.dumps(recipe_summary.get('ingredients', []), ensure_ascii=False)
                favorite.recipe_steps = json.dumps(recipe_summary.get('steps', []), ensure_ascii=False)
            
            if analysis_result and analysis_result.get('status') == 'success':
                favorite.comment_summary = analysis_result.get('comment_summary', '')
                favorite.sentiment_rating = analysis_result.get('sentiment_rating', 0)
                favorite.difficulty_rating = analysis_result.get('difficulty_rating', 0)
                favorite.positive_keywords = analysis_result.get('positive_keywords', [])
                favorite.negative_keywords = analysis_result.get('negative_keywords', [])
            
            favorite.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'AI 분석이 완료되었습니다.',
                'has_recipe': bool(recipe_summary and recipe_summary.get('status') == 'success'),
                'has_comments': bool(analysis_result and analysis_result.get('status') == 'success')
            })
            
        except FavoriteRecipe.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '즐겨찾기를 찾을 수 없습니다.'}, status=404)
            
    except Exception as e:
        logger.error(f"AI 분석 강화 오류: {e}")
        return JsonResponse({'status': 'error', 'message': 'AI 분석 중 오류가 발생했습니다.'}, status=500)


@login_required
@require_http_methods(["POST"])
def add_favorite(request):
    """레시피를 즐겨찾기에 추가합니다 (AI 분석 데이터 포함)"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id', '')
        
        if not video_id:
            return JsonResponse({
                'status': 'error',
                'message': _('비디오 ID가 없습니다.')
            })
        
        # 이미 즐겨찾기에 있는지 확인
        if FavoriteRecipe.objects.filter(user=request.user, video_id=video_id).exists():
            return JsonResponse({
                'status': 'error',
                'message': _('이미 즐겨찾기에 추가된 레시피입니다.')
            })
        
        # YouTube 정보 가져오기
        youtube_service = YouTubeService()
        video_info = youtube_service.get_video_info(video_id)
        
        if video_info['status'] != 'success':
            return JsonResponse({
                'status': 'error',
                'message': _('영상 정보를 가져올 수 없습니다.')
            })
        
        # 브라우저 언어 감지
        browser_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'ko')
        language = 'en' if browser_language.startswith('en') else 'ko'
        
        # AI 댓글 분석
        ai_service = RecipeAIService()
        comments_result = youtube_service.get_video_comments(video_id, max_comments=20)
        
        comment_summary = ''
        sentiment_rating = 0
        difficulty_rating = 0
        positive_keywords = []
        negative_keywords = []
        
        if comments_result['status'] == 'success' and comments_result['comments']:
            analysis = ai_service.analyze_video_comments(
                video_info['title'],
                comments_result['comments'],
                language=language
            )
            
            if analysis['status'] == 'success':
                comment_summary = analysis.get('comment_summary', '')
                sentiment_rating = analysis.get('rating', 0)
                difficulty_rating = analysis.get('difficulty', 0)
                positive_keywords = analysis.get('positive_keywords', [])
                negative_keywords = analysis.get('negative_keywords', [])
        
        # 즐겨찾기 생성
        favorite = FavoriteRecipe.objects.create(
            user=request.user,
            video_id=video_id,
            title=video_info['title'],
            channel_name=video_info['channel'],
            thumbnail_url=video_info['thumbnail'],
            description=video_info.get('description', ''),
            view_count=video_info.get('view_count', 0),
            comment_count=video_info.get('comment_count', 0),
            comment_summary=comment_summary,
            sentiment_rating=sentiment_rating,
            difficulty_rating=difficulty_rating,
            positive_keywords=positive_keywords,
            negative_keywords=negative_keywords
        )
        
        logger.info(f"즐겨찾기 추가 성공: {request.user.username} - {video_id}")
        
        return JsonResponse({
            'status': 'success',
            'message': _('즐겨찾기에 추가되었습니다.'),
            'favorite_id': favorite.id
        })
        
    except Exception as e:
        logger.error(f"즐겨찾기 추가 오류: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def remove_favorite(request):
    """즐겨찾기에서 레시피를 삭제합니다"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id', '')
        
        if not video_id:
            return JsonResponse({
                'status': 'error',
                'message': _('비디오 ID가 없습니다.')
            })
        
        # 즐겨찾기 삭제
        deleted_count, _ = FavoriteRecipe.objects.filter(
            user=request.user,
            video_id=video_id
        ).delete()
        
        if deleted_count > 0:
            logger.info(f"즐겨찾기 삭제 성공: {request.user.username} - {video_id}")
            return JsonResponse({
                'status': 'success',
                'message': _('즐겨찾기에서 삭제되었습니다.')
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': _('즐겨찾기에 없는 레시피입니다.')
            })
        
    except Exception as e:
        logger.error(f"즐겨찾기 삭제 오류: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def check_favorite(request):
    """레시피가 즐겨찾기에 있는지 확인합니다"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id', '')
        
        if not video_id:
            return JsonResponse({
                'status': 'error',
                'message': _('비디오 ID가 없습니다.')
            })
        
        is_favorite = FavoriteRecipe.objects.filter(
            user=request.user,
            video_id=video_id
        ).exists()
        
        return JsonResponse({
            'status': 'success',
            'is_favorite': is_favorite
        })
        
    except Exception as e:
        logger.error(f"즐겨찾기 확인 오류: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@login_required
def favorite_list(request):
    """즐겨찾기 목록을 보여줍니다"""
    try:
        favorites = FavoriteRecipe.objects.filter(user=request.user)
        
        # 데이터가 없는 즐겨찾기 항목들 정리
        for favorite in favorites:
            if not favorite.title or not favorite.thumbnail_url:
                try:
                    # YouTube API에서 최신 정보 가져와서 업데이트
                    youtube_service = YouTubeService()
                    video_info = youtube_service.get_video_info(favorite.video_id)
                    
                    if video_info['status'] == 'success':
                        favorite.title = video_info['title']
                        favorite.channel_name = video_info['channel']
                        favorite.thumbnail_url = video_info['thumbnail']
                        favorite.view_count = video_info.get('view_count', 0)
                        favorite.comment_count = video_info.get('comment_count', 0)
                        favorite.save()
                    else:
                        # 정보를 가져올 수 없으면 삭제
                        favorite.delete()
                        logger.warning(f"즐겨찾기 삭제: {favorite.video_id} - YouTube 정보 없음")
                except Exception as e:
                    logger.error(f"즐겨찾기 업데이트 오류: {e}")
                    # 오류 발생 시에도 삭제하지 않고 그대로 유지
        
        context = {
            'favorites': favorites
        }
        
        return render(request, 'recipe_ai/favorite_list.html', context)
        
    except Exception as e:
        logger.error(f"즐겨찾기 목록 조회 오류: {e}")
        messages.error(request, _('오류가 발생했습니다. 다시 시도해주세요.'))
        return redirect('recipe_ai:index')


@login_required
@require_http_methods(["POST"])
def toggle_favorite(request):
    """즐겨찾기 토글 (추가/제거) - 상세 페이지에서 분석된 데이터 그대로 저장"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        
        if not video_id:
            return JsonResponse({'status': 'error', 'message': 'video_id가 필요합니다.'}, status=400)
        
        # 기존 즐겨찾기 확인
        try:
            favorite = FavoriteRecipe.objects.get(user=request.user, video_id=video_id)
            # 이미 존재하면 삭제
            favorite.delete()
            is_favorite = False
            logger.info(f"즐겨찾기 삭제: {video_id}")
        except FavoriteRecipe.DoesNotExist:
            # 존재하지 않으면 새로 생성 - 상세 페이지에서 받은 데이터 그대로 저장
            try:
                # 기본 정보
                favorite_data = {
                    'user': request.user,
                    'video_id': video_id,
                    'title': data.get('title', ''),
                    'channel_name': data.get('channel', ''),
                    'thumbnail_url': data.get('thumbnail', ''),
                    'view_count': data.get('view_count', 0),
                    'comment_count': data.get('comment_count', 0)
                }
                
                # AI 분석 결과가 있으면 함께 저장
                if 'ingredients' in data and 'steps' in data:
                    ingredients = data.get('ingredients', [])
                    steps = data.get('steps', [])
                    
                    # 안전하게 처리
                    if ingredients:
                        if isinstance(ingredients, str):
                            ingredients = json.loads(ingredients)
                        favorite_data['recipe_ingredients'] = json.dumps(ingredients, ensure_ascii=False)
                    
                    if steps:
                        if isinstance(steps, str):
                            steps = json.loads(steps)
                        favorite_data['recipe_steps'] = json.dumps(steps, ensure_ascii=False)
                
                if 'comment_summary' in data:
                    favorite_data['comment_summary'] = data.get('comment_summary', '')
                    favorite_data['sentiment_rating'] = data.get('sentiment_rating', 0)
                    favorite_data['difficulty_rating'] = data.get('difficulty_rating', 0)
                
                favorite = FavoriteRecipe.objects.create(**favorite_data)
                is_favorite = True
                
                logger.info(f"즐겨찾기 저장 완료: {video_id}")
                
            except Exception as e:
                logger.error(f"즐겨찾기 저장 중 오류: {e}", exc_info=True)
                return JsonResponse({
                    'status': 'error', 
                    'message': f'즐겨찾기 저장 중 오류가 발생했습니다: {str(e)}'
                }, status=500)
        
        return JsonResponse({
            'status': 'success',
            'is_favorite': is_favorite,
            'message': '즐겨찾기에 추가되었습니다.' if is_favorite else '즐겨찾기에서 제거되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"즐겨찾기 토글 오류: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': '오류가 발생했습니다.'}, status=500)
