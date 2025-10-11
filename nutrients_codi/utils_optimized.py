"""
최적화된 유틸리티 함수들
- 선택적 영양소 집계
- 캐싱 활용
- 성능 최적화
"""

from django.db.models import Sum
from django.core.cache import cache
from datetime import date, timedelta
from .models import FoodLog


def get_basic_nutrition_aggregate():
    """기본 영양소만 집계 (가장 자주 사용)"""
    return {
        'total_calories': Sum('total_calories'),
        'total_protein': Sum('total_protein'),
        'total_carbs': Sum('total_carbs'),
        'total_fat': Sum('total_fat'),
        'total_fiber': Sum('total_fiber'),
        'total_sugar': Sum('total_sugar'),
        'total_sodium': Sum('total_sodium'),
    }


def get_full_nutrition_aggregate():
    """전체 영양소 집계 (상세 페이지용)"""
    return {
        # 기본 영양소
        'total_calories': Sum('total_calories'),
        'total_protein': Sum('total_protein'),
        'total_carbs': Sum('total_carbs'),
        'total_fat': Sum('total_fat'),
        'total_fiber': Sum('total_fiber'),
        'total_sugar': Sum('total_sugar'),
        
        # 주요 미네랄
        'total_sodium': Sum('total_sodium'),
        'total_potassium': Sum('total_potassium'),
        'total_calcium': Sum('total_calcium'),
        'total_iron': Sum('total_iron'),
        'total_magnesium': Sum('total_magnesium'),
        'total_phosphorus': Sum('total_phosphorus'),
        'total_zinc': Sum('total_zinc'),
        
        # 주요 비타민
        'total_vitamin_a': Sum('total_vitamin_a'),
        'total_vitamin_b1': Sum('total_vitamin_b1'),
        'total_vitamin_b2': Sum('total_vitamin_b2'),
        'total_vitamin_b3': Sum('total_vitamin_b3'),
        'total_vitamin_b6': Sum('total_vitamin_b6'),
        'total_vitamin_b12': Sum('total_vitamin_b12'),
        'total_vitamin_c': Sum('total_vitamin_c'),
        'total_vitamin_d': Sum('total_vitamin_d'),
        'total_vitamin_e': Sum('total_vitamin_e'),
        'total_vitamin_k': Sum('total_vitamin_k'),
        'total_folate': Sum('total_folate'),
        
        # 기타 영양소
        'total_cholesterol': Sum('total_cholesterol'),
        'total_saturated_fat': Sum('total_saturated_fat'),
        'total_omega3': Sum('total_omega3'),
        'total_omega6': Sum('total_omega6'),
    }


def get_today_nutrition_cached(user, use_cache=True):
    """
    오늘의 영양소 합계를 캐시를 활용하여 조회
    
    Args:
        user: 사용자 객체
        use_cache: 캐시 사용 여부 (기본 True)
    
    Returns:
        dict: 영양소 합계 데이터
    """
    today = date.today()
    cache_key = f'nutrition_today_{user.id}_{today}'
    
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
    
    # 기본 영양소만 조회 (빠름)
    today_aggregates = FoodLog.objects.filter(
        user=user,
        consumed_date=today
    ).aggregate(**get_basic_nutrition_aggregate())
    
    # None 값을 0으로 변환
    result = {k: v or 0 for k, v in today_aggregates.items()}
    
    # 1시간 캐시
    if use_cache:
        cache.set(cache_key, result, 3600)
    
    return result


def get_date_nutrition_cached(user, target_date, use_cache=True):
    """
    특정 날짜의 영양소 합계를 캐시를 활용하여 조회
    
    Args:
        user: 사용자 객체
        target_date: 조회할 날짜
        use_cache: 캐시 사용 여부
    
    Returns:
        dict: 영양소 합계 데이터
    """
    cache_key = f'nutrition_date_{user.id}_{target_date}'
    
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
    
    # 기본 영양소만 조회
    date_aggregates = FoodLog.objects.filter(
        user=user,
        consumed_date=target_date
    ).aggregate(**get_basic_nutrition_aggregate())
    
    # None 값을 0으로 변환
    result = {k: v or 0 for k, v in date_aggregates.items()}
    
    # 과거 날짜는 24시간 캐시, 오늘은 1시간
    cache_time = 86400 if target_date < date.today() else 3600
    if use_cache:
        cache.set(cache_key, result, cache_time)
    
    return result


def get_daily_summaries_optimized(user, days=7):
    """
    최적화된 일별 영양소 종합 데이터 생성
    
    기존 함수보다 50개 필드 → 7개 필드로 축소하여 성능 대폭 향상
    """
    today = date.today()
    start_date = today - timedelta(days=days-1)
    
    # 기본 영양소만 집계 (빠름!)
    daily_data = FoodLog.objects.filter(
        user=user,
        consumed_date__gte=start_date,
        consumed_date__lte=today
    ).values('consumed_date').annotate(
        **get_basic_nutrition_aggregate()
    ).order_by('-consumed_date')
    
    # 결과 변환
    daily_summaries = []
    for day_data in daily_data:
        summary = {
            'date': day_data['consumed_date'],
            'nutrients': {
                'calories': day_data['total_calories'] or 0,
                'protein': day_data['total_protein'] or 0,
                'carbs': day_data['total_carbs'] or 0,
                'fat': day_data['total_fat'] or 0,
                'fiber': day_data['total_fiber'] or 0,
                'sugar': day_data['total_sugar'] or 0,
                'sodium': day_data['total_sodium'] or 0,
            }
        }
        daily_summaries.append(summary)
    
    return daily_summaries


def invalidate_nutrition_cache(user, target_date=None):
    """
    영양소 캐시 무효화 (FoodLog 생성/수정/삭제 시 호출)
    
    Args:
        user: 사용자 객체
        target_date: 특정 날짜 (None이면 오늘)
    """
    if target_date is None:
        target_date = date.today()
    
    cache_keys = [
        f'nutrition_today_{user.id}_{target_date}',
        f'nutrition_date_{user.id}_{target_date}',
    ]
    
    for key in cache_keys:
        cache.delete(key)

