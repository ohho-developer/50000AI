from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
import json
import logging

from .models import Profile, Food, FoodLog
from .forms import ProfileForm, FoodAnalysisForm

logger = logging.getLogger(__name__)

def get_daily_summaries(user, days=7):
    """일별 영양소 종합 데이터를 생성하는 헬퍼 함수"""
    from django.db.models import Sum, Count
    from datetime import date, timedelta
    
    today = date.today()
    start_date = today - timedelta(days=days-1)
    
    # 일별로 그룹화하여 영양소 합계 계산
    daily_data = FoodLog.objects.filter(
        user=user,
        consumed_date__gte=start_date,
        consumed_date__lte=today
    ).values('consumed_date').annotate(
        # 기본 영양소
        total_calories=Sum('total_calories'),
        total_protein=Sum('total_protein'),
        total_carbs=Sum('total_carbs'),
        total_fat=Sum('total_fat'),
        total_fiber=Sum('total_fiber'),
        total_sugar=Sum('total_sugar'),
        
        # 미네랄
        total_sodium=Sum('total_sodium'),
        total_potassium=Sum('total_potassium'),
        total_calcium=Sum('total_calcium'),
        total_iron=Sum('total_iron'),
        total_magnesium=Sum('total_magnesium'),
        total_phosphorus=Sum('total_phosphorus'),
        total_zinc=Sum('total_zinc'),
        total_copper=Sum('total_copper'),
        total_manganese=Sum('total_manganese'),
        total_selenium=Sum('total_selenium'),
        
        # 비타민
        total_vitamin_a=Sum('total_vitamin_a'),
        total_vitamin_b1=Sum('total_vitamin_b1'),
        total_vitamin_b2=Sum('total_vitamin_b2'),
        total_vitamin_b3=Sum('total_vitamin_b3'),
        total_vitamin_b6=Sum('total_vitamin_b6'),
        total_vitamin_b12=Sum('total_vitamin_b12'),
        total_vitamin_c=Sum('total_vitamin_c'),
        total_vitamin_d=Sum('total_vitamin_d'),
        total_vitamin_e=Sum('total_vitamin_e'),
        total_vitamin_k=Sum('total_vitamin_k'),
        total_folate=Sum('total_folate'),
        total_choline=Sum('total_choline'),
        
        # 추가 비타민 및 영양소
        total_beta_carotene=Sum('total_beta_carotene'),
        total_niacin=Sum('total_niacin'),
        total_vitamin_d2=Sum('total_vitamin_d2'),
        total_vitamin_d3=Sum('total_vitamin_d3'),
        total_vitamin_k1=Sum('total_vitamin_k1'),
        total_vitamin_k2=Sum('total_vitamin_k2'),
        
        # 추가 미네랄
        total_iodine=Sum('total_iodine'),
        total_fluorine=Sum('total_fluorine'),
        total_chromium=Sum('total_chromium'),
        total_molybdenum=Sum('total_molybdenum'),
        total_chlorine=Sum('total_chlorine'),
        
        # 기타 영양소
        total_cholesterol=Sum('total_cholesterol'),
        total_saturated_fat=Sum('total_saturated_fat'),
        total_monounsaturated_fat=Sum('total_monounsaturated_fat'),
        total_polyunsaturated_fat=Sum('total_polyunsaturated_fat'),
        total_omega3=Sum('total_omega3'),
        total_omega6=Sum('total_omega6'),
        total_trans_fat=Sum('total_trans_fat'),
        total_caffeine=Sum('total_caffeine'),
        total_alcohol=Sum('total_alcohol'),
        total_water=Sum('total_water'),
        total_ash=Sum('total_ash'),
        
        # 음식 개수
        food_count=Count('id')
    ).order_by('-consumed_date')
    
    # 결과를 리스트로 변환하고 None 값을 0으로 처리
    daily_summaries = []
    for day_data in daily_data:
        summary = {
            'date': day_data['consumed_date'],
            'food_count': day_data['food_count'],
            'nutrition': {
                # 기본 영양소
                'calories': day_data['total_calories'] or 0,
                'protein': day_data['total_protein'] or 0,
                'carbs': day_data['total_carbs'] or 0,
                'fat': day_data['total_fat'] or 0,
                'fiber': day_data['total_fiber'] or 0,
                'sugar': day_data['total_sugar'] or 0,
                
                # 미네랄
                'sodium': day_data['total_sodium'] or 0,
                'potassium': day_data['total_potassium'] or 0,
                'calcium': day_data['total_calcium'] or 0,
                'iron': day_data['total_iron'] or 0,
                'magnesium': day_data['total_magnesium'] or 0,
                'phosphorus': day_data['total_phosphorus'] or 0,
                'zinc': day_data['total_zinc'] or 0,
                'copper': day_data['total_copper'] or 0,
                'manganese': day_data['total_manganese'] or 0,
                'selenium': day_data['total_selenium'] or 0,
                
                # 비타민
                'vitamin_a': day_data['total_vitamin_a'] or 0,
                'vitamin_b1': day_data['total_vitamin_b1'] or 0,
                'vitamin_b2': day_data['total_vitamin_b2'] or 0,
                'vitamin_b3': day_data['total_vitamin_b3'] or 0,
                'vitamin_b6': day_data['total_vitamin_b6'] or 0,
                'vitamin_b12': day_data['total_vitamin_b12'] or 0,
                'vitamin_c': day_data['total_vitamin_c'] or 0,
                'vitamin_d': day_data['total_vitamin_d'] or 0,
                'vitamin_e': day_data['total_vitamin_e'] or 0,
                'vitamin_k': day_data['total_vitamin_k'] or 0,
                'folate': day_data['total_folate'] or 0,
                'choline': day_data['total_choline'] or 0,
                
                # 추가 비타민 및 영양소
                'beta_carotene': day_data['total_beta_carotene'] or 0,
                'niacin': day_data['total_niacin'] or 0,
                'vitamin_d2': day_data['total_vitamin_d2'] or 0,
                'vitamin_d3': day_data['total_vitamin_d3'] or 0,
                'vitamin_k1': day_data['total_vitamin_k1'] or 0,
                'vitamin_k2': day_data['total_vitamin_k2'] or 0,
                
                # 추가 미네랄
                'iodine': day_data['total_iodine'] or 0,
                'fluorine': day_data['total_fluorine'] or 0,
                'chromium': day_data['total_chromium'] or 0,
                'molybdenum': day_data['total_molybdenum'] or 0,
                'chlorine': day_data['total_chlorine'] or 0,
                
                # 기타 영양소
                'cholesterol': day_data['total_cholesterol'] or 0,
                'saturated_fat': day_data['total_saturated_fat'] or 0,
                'monounsaturated_fat': day_data['total_monounsaturated_fat'] or 0,
                'polyunsaturated_fat': day_data['total_polyunsaturated_fat'] or 0,
                'omega3': day_data['total_omega3'] or 0,
                'omega6': day_data['total_omega6'] or 0,
                'trans_fat': day_data['total_trans_fat'] or 0,
                'caffeine': day_data['total_caffeine'] or 0,
                'alcohol': day_data['total_alcohol'] or 0,
                'water': day_data['total_water'] or 0,
                'ash': day_data['total_ash'] or 0,
            }
        }
        daily_summaries.append(summary)
    
    return daily_summaries

# Create your views here.

@login_required
def dashboard(request):
    """뉴트리언트코디 메인 대시보드"""
    # 프로필 확인 및 생성
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
        # 기본 권장 섭취량 설정
        profile.calculate_daily_needs()
    
    # 오늘의 식단 기록
    today = date.today()
    today_logs = FoodLog.objects.select_related('food').filter(
        user=request.user,
        consumed_date=today
    ).order_by('-consumed_at')
    
    # 오늘의 영양소 합계 (데이터베이스에서 직접 계산)
    from django.db.models import Sum
    today_aggregates = FoodLog.objects.filter(
        user=request.user,
        consumed_date=today
    ).aggregate(
        # 기본 영양소
        total_calories=Sum('total_calories'),
        total_protein=Sum('total_protein'),
        total_carbs=Sum('total_carbs'),
        total_fat=Sum('total_fat'),
        total_fiber=Sum('total_fiber'),
        total_sugar=Sum('total_sugar'),
        
        # 미네랄
        total_sodium=Sum('total_sodium'),
        total_potassium=Sum('total_potassium'),
        total_calcium=Sum('total_calcium'),
        total_iron=Sum('total_iron'),
        total_magnesium=Sum('total_magnesium'),
        total_phosphorus=Sum('total_phosphorus'),
        total_zinc=Sum('total_zinc'),
        total_copper=Sum('total_copper'),
        total_manganese=Sum('total_manganese'),
        total_selenium=Sum('total_selenium'),
        
        # 비타민
        total_vitamin_a=Sum('total_vitamin_a'),
        total_vitamin_b1=Sum('total_vitamin_b1'),
        total_vitamin_b2=Sum('total_vitamin_b2'),
        total_vitamin_b3=Sum('total_vitamin_b3'),
        total_vitamin_b6=Sum('total_vitamin_b6'),
        total_vitamin_b12=Sum('total_vitamin_b12'),
        total_vitamin_c=Sum('total_vitamin_c'),
        total_vitamin_d=Sum('total_vitamin_d'),
        total_vitamin_e=Sum('total_vitamin_e'),
        total_vitamin_k=Sum('total_vitamin_k'),
        total_folate=Sum('total_folate'),
        total_choline=Sum('total_choline'),
        
        # 추가 비타민 및 영양소
        total_beta_carotene=Sum('total_beta_carotene'),
        total_niacin=Sum('total_niacin'),
        total_vitamin_d2=Sum('total_vitamin_d2'),
        total_vitamin_d3=Sum('total_vitamin_d3'),
        total_vitamin_k1=Sum('total_vitamin_k1'),
        total_vitamin_k2=Sum('total_vitamin_k2'),
        
        # 추가 미네랄
        total_iodine=Sum('total_iodine'),
        total_fluorine=Sum('total_fluorine'),
        total_chromium=Sum('total_chromium'),
        total_molybdenum=Sum('total_molybdenum'),
        total_chlorine=Sum('total_chlorine'),
        
        # 기타 영양소
        total_cholesterol=Sum('total_cholesterol'),
        total_saturated_fat=Sum('total_saturated_fat'),
        total_monounsaturated_fat=Sum('total_monounsaturated_fat'),
        total_polyunsaturated_fat=Sum('total_polyunsaturated_fat'),
        total_omega3=Sum('total_omega3'),
        total_omega6=Sum('total_omega6'),
        total_trans_fat=Sum('total_trans_fat'),
        total_caffeine=Sum('total_caffeine'),
        total_alcohol=Sum('total_alcohol'),
        total_water=Sum('total_water'),
        total_ash=Sum('total_ash')
    )
    
    today_nutrition = {
        # 기본 영양소
        'calories': today_aggregates['total_calories'] or 0,
        'protein': today_aggregates['total_protein'] or 0,
        'carbs': today_aggregates['total_carbs'] or 0,
        'fat': today_aggregates['total_fat'] or 0,
        'fiber': today_aggregates['total_fiber'] or 0,
        'sugar': today_aggregates['total_sugar'] or 0,
        
        # 미네랄
        'sodium': today_aggregates['total_sodium'] or 0,
        'potassium': today_aggregates['total_potassium'] or 0,
        'calcium': today_aggregates['total_calcium'] or 0,
        'iron': today_aggregates['total_iron'] or 0,
        'magnesium': today_aggregates['total_magnesium'] or 0,
        'phosphorus': today_aggregates['total_phosphorus'] or 0,
        'zinc': today_aggregates['total_zinc'] or 0,
        'copper': today_aggregates['total_copper'] or 0,
        'manganese': today_aggregates['total_manganese'] or 0,
        'selenium': today_aggregates['total_selenium'] or 0,
        
        # 비타민
        'vitamin_a': today_aggregates['total_vitamin_a'] or 0,
        'vitamin_b1': today_aggregates['total_vitamin_b1'] or 0,
        'vitamin_b2': today_aggregates['total_vitamin_b2'] or 0,
        'vitamin_b3': today_aggregates['total_vitamin_b3'] or 0,
        'vitamin_b6': today_aggregates['total_vitamin_b6'] or 0,
        'vitamin_b12': today_aggregates['total_vitamin_b12'] or 0,
        'vitamin_c': today_aggregates['total_vitamin_c'] or 0,
        'vitamin_d': today_aggregates['total_vitamin_d'] or 0,
        'vitamin_e': today_aggregates['total_vitamin_e'] or 0,
        'vitamin_k': today_aggregates['total_vitamin_k'] or 0,
        'folate': today_aggregates['total_folate'] or 0,
        'choline': today_aggregates['total_choline'] or 0,
        
        # 추가 비타민 및 영양소
        'beta_carotene': today_aggregates['total_beta_carotene'] or 0,
        'niacin': today_aggregates['total_niacin'] or 0,
        'vitamin_d2': today_aggregates['total_vitamin_d2'] or 0,
        'vitamin_d3': today_aggregates['total_vitamin_d3'] or 0,
        'vitamin_k1': today_aggregates['total_vitamin_k1'] or 0,
        'vitamin_k2': today_aggregates['total_vitamin_k2'] or 0,
        
        # 추가 미네랄
        'iodine': today_aggregates['total_iodine'] or 0,
        'fluorine': today_aggregates['total_fluorine'] or 0,
        'chromium': today_aggregates['total_chromium'] or 0,
        'molybdenum': today_aggregates['total_molybdenum'] or 0,
        'chlorine': today_aggregates['total_chlorine'] or 0,
        
        # 기타 영양소
        'cholesterol': today_aggregates['total_cholesterol'] or 0,
        'saturated_fat': today_aggregates['total_saturated_fat'] or 0,
        'monounsaturated_fat': today_aggregates['total_monounsaturated_fat'] or 0,
        'polyunsaturated_fat': today_aggregates['total_polyunsaturated_fat'] or 0,
        'omega3': today_aggregates['total_omega3'] or 0,
        'omega6': today_aggregates['total_omega6'] or 0,
        'trans_fat': today_aggregates['total_trans_fat'] or 0,
        'caffeine': today_aggregates['total_caffeine'] or 0,
        'alcohol': today_aggregates['total_alcohol'] or 0,
        'water': today_aggregates['total_water'] or 0,
        'ash': today_aggregates['total_ash'] or 0,
    }
    
    # 영양소별 권장량 대비 비율 계산
    nutrient_percentages = {}
    
    # 권장량 정의 (mg/g 단위)
    recommended_amounts = {
        'fiber': 25,  # 식이섬유 25g
        'sugar': 50,  # 당분 50g
        'sodium': 2000,  # 나트륨 2000mg
        'potassium': 3500,  # 칼륨 3500mg
        'calcium': 1000,  # 칼슘 1000mg
        'iron': 8,  # 철분 8mg (성인 남성 기준)
        'magnesium': 400,  # 마그네슘 400mg
        'phosphorus': 700,  # 인 700mg
        'zinc': 8,  # 아연 8mg (성인 남성 기준)
        'copper': 0.9,  # 구리 0.9mg
        'manganese': 2.3,  # 망간 2.3mg
        'selenium': 55,  # 셀레늄 55μg
        'iodine': 150,  # 요오드 150μg
        'fluorine': 3,  # 불소 3mg
        'chromium': 35,  # 크롬 35μg
        'molybdenum': 45,  # 몰리브덴 45μg
        'chlorine': 2300,  # 염소 2300mg
        'vitamin_a': 700,  # 비타민 A 700μg
        'vitamin_b1': 1.1,  # 비타민 B1 1.1mg
        'vitamin_b2': 1.1,  # 비타민 B2 1.1mg
        'vitamin_b3': 14,  # 비타민 B3 14mg
        'vitamin_b6': 1.3,  # 비타민 B6 1.3mg
        'vitamin_b12': 2.4,  # 비타민 B12 2.4μg
        'vitamin_c': 65,  # 비타민 C 65mg
        'vitamin_d': 15,  # 비타민 D 15μg
        'vitamin_e': 15,  # 비타민 E 15mg
        'vitamin_k': 90,  # 비타민 K 90μg
        'folate': 400,  # 엽산 400μg
        'choline': 425,  # 콜린 425mg
        'beta_carotene': 700,  # 베타카로틴 700μg
        'niacin': 14,  # 나이아신 14mg
        'vitamin_d2': 15,  # 비타민 D2 15μg
        'vitamin_d3': 15,  # 비타민 D3 15μg
        'vitamin_k1': 90,  # 비타민 K1 90μg
        'vitamin_k2': 90,  # 비타민 K2 90μg
        'cholesterol': 300,  # 콜레스테롤 300mg
        'saturated_fat': 20,  # 포화지방 20g
        'monounsaturated_fat': 25,  # 단일불포화지방 25g
        'polyunsaturated_fat': 20,  # 다중불포화지방 20g
        'omega3': 1.6,  # 오메가3 1.6g
        'omega6': 17,  # 오메가6 17g
        'trans_fat': 2,  # 트랜스지방 2g
        'caffeine': 400,  # 카페인 400mg
        'alcohol': 20,  # 알코올 20g
        'water': 3000,  # 수분 3000g
        'ash': 10,  # 회분 10g
    }
    
    # 각 영양소의 권장량 대비 비율 계산
    for nutrient, current_amount in today_nutrition.items():
        if nutrient in recommended_amounts:
            recommended = recommended_amounts[nutrient]
            if recommended > 0:
                percentage = (current_amount / recommended) * 100
                nutrient_percentages[nutrient] = round(percentage, 1)
            else:
                nutrient_percentages[nutrient] = 0
        else:
            nutrient_percentages[nutrient] = 0
    
    # 브라우저 언어 감지
    from .utils import get_browser_language, get_language_messages
    browser_language = get_browser_language(request)
    messages = get_language_messages(browser_language)
    
    # 영양소 카테고리별 데이터 구조화 (다국어 지원)
    if browser_language == 'en':
        nutrient_categories = {
            'basic': {
                'title': 'Basic Nutrients',
                'nutrients': [
                    {'key': 'fiber', 'name': 'Dietary Fiber', 'unit': 'g', 'recommended': '25-35g', 'color': 'from-green-400 to-green-500'},
                    {'key': 'sugar', 'name': 'Sugar', 'unit': 'g', 'recommended': '<50g', 'color': 'from-pink-400 to-pink-500'},
                ]
            },
            'minerals': {
                'title': 'Minerals',
                'nutrients': [
                    {'key': 'sodium', 'name': 'Sodium', 'unit': 'mg', 'recommended': '<2000mg', 'color': 'from-purple-400 to-purple-500'},
                    {'key': 'potassium', 'name': 'Potassium', 'unit': 'mg', 'recommended': '3500mg', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'calcium', 'name': 'Calcium', 'unit': 'mg', 'recommended': '1000mg', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'iron', 'name': 'Iron', 'unit': 'mg', 'recommended': '8-18mg', 'color': 'from-red-400 to-red-500'},
                    {'key': 'magnesium', 'name': 'Magnesium', 'unit': 'mg', 'recommended': '400mg', 'color': 'from-teal-400 to-teal-500'},
                    {'key': 'phosphorus', 'name': 'Phosphorus', 'unit': 'mg', 'recommended': '700mg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'zinc', 'name': 'Zinc', 'unit': 'mg', 'recommended': '8-11mg', 'color': 'from-gray-400 to-gray-500'},
                    {'key': 'copper', 'name': 'Copper', 'unit': 'mg', 'recommended': '0.9mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'manganese', 'name': 'Manganese', 'unit': 'mg', 'recommended': '2.3mg', 'color': 'from-cyan-400 to-cyan-500'},
                    {'key': 'selenium', 'name': 'Selenium', 'unit': 'μg', 'recommended': '55μg', 'color': 'from-lime-400 to-lime-500'},
                ]
            },
            'vitamins': {
                'title': 'Vitamins',
                'nutrients': [
                    {'key': 'vitamin_a', 'name': 'Vitamin A', 'unit': 'μg', 'recommended': '700μg', 'color': 'from-yellow-400 to-yellow-500'},
                    {'key': 'vitamin_b1', 'name': 'Vitamin B1', 'unit': 'mg', 'recommended': '1.1mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'vitamin_b2', 'name': 'Vitamin B2', 'unit': 'mg', 'recommended': '1.1mg', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'vitamin_b3', 'name': 'Vitamin B3', 'unit': 'mg', 'recommended': '14mg', 'color': 'from-red-400 to-red-500'},
                    {'key': 'vitamin_b6', 'name': 'Vitamin B6', 'unit': 'mg', 'recommended': '1.3mg', 'color': 'from-pink-400 to-pink-500'},
                    {'key': 'vitamin_b12', 'name': 'Vitamin B12', 'unit': 'μg', 'recommended': '2.4μg', 'color': 'from-purple-400 to-purple-500'},
                    {'key': 'vitamin_c', 'name': 'Vitamin C', 'unit': 'mg', 'recommended': '65mg', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'vitamin_d', 'name': 'Vitamin D', 'unit': 'μg', 'recommended': '15μg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'vitamin_e', 'name': 'Vitamin E', 'unit': 'mg', 'recommended': '15mg', 'color': 'from-teal-400 to-teal-500'},
                    {'key': 'vitamin_k', 'name': 'Vitamin K', 'unit': 'μg', 'recommended': '90μg', 'color': 'from-green-400 to-green-500'},
                    {'key': 'folate', 'name': 'Folate', 'unit': 'μg', 'recommended': '400μg', 'color': 'from-emerald-400 to-emerald-500'},
                    {'key': 'choline', 'name': 'Choline', 'unit': 'mg', 'recommended': '425mg', 'color': 'from-sky-400 to-sky-500'},
                ]
            },
            'other': {
                'title': 'Other Nutrients',
                'nutrients': [
                    {'key': 'cholesterol', 'name': 'Cholesterol', 'unit': 'mg', 'recommended': '300mg', 'color': 'from-rose-400 to-rose-500'},
                    {'key': 'saturated_fat', 'name': 'Saturated Fat', 'unit': 'g', 'recommended': '20g', 'color': 'from-red-400 to-red-500'},
                    {'key': 'omega3', 'name': 'Omega-3', 'unit': 'g', 'recommended': '1.6g', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'omega6', 'name': 'Omega-6', 'unit': 'g', 'recommended': '17g', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'trans_fat', 'name': 'Trans Fat', 'unit': 'g', 'recommended': '2g', 'color': 'from-gray-400 to-gray-500'},
                    {'key': 'caffeine', 'name': 'Caffeine', 'unit': 'mg', 'recommended': '400mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'alcohol', 'name': 'Alcohol', 'unit': 'g', 'recommended': '20g', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'water', 'name': 'Water', 'unit': 'g', 'recommended': '2000-3000g', 'color': 'from-cyan-400 to-cyan-500'},
                ]
            }
        }
    else:
        # 한국어 버전 (기본값)
        nutrient_categories = {
            'basic': {
                'title': '기초 영양소',
                'nutrients': [
                    {'key': 'fiber', 'name': '식이섬유', 'unit': 'g', 'recommended': '25-35g', 'color': 'from-green-400 to-green-500'},
                    {'key': 'sugar', 'name': '당분', 'unit': 'g', 'recommended': '<50g', 'color': 'from-pink-400 to-pink-500'},
                ]
            },
            'minerals': {
                'title': '미네랄',
                'nutrients': [
                    {'key': 'sodium', 'name': '나트륨', 'unit': 'mg', 'recommended': '<2000mg', 'color': 'from-purple-400 to-purple-500'},
                    {'key': 'potassium', 'name': '칼륨', 'unit': 'mg', 'recommended': '3500mg', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'calcium', 'name': '칼슘', 'unit': 'mg', 'recommended': '1000mg', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'iron', 'name': '철분', 'unit': 'mg', 'recommended': '8-18mg', 'color': 'from-red-400 to-red-500'},
                    {'key': 'magnesium', 'name': '마그네슘', 'unit': 'mg', 'recommended': '400mg', 'color': 'from-teal-400 to-teal-500'},
                    {'key': 'phosphorus', 'name': '인', 'unit': 'mg', 'recommended': '700mg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'zinc', 'name': '아연', 'unit': 'mg', 'recommended': '8-11mg', 'color': 'from-gray-400 to-gray-500'},
                    {'key': 'copper', 'name': '구리', 'unit': 'mg', 'recommended': '0.9mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'manganese', 'name': '망간', 'unit': 'mg', 'recommended': '2.3mg', 'color': 'from-cyan-400 to-cyan-500'},
                    {'key': 'selenium', 'name': '셀레늄', 'unit': 'μg', 'recommended': '55μg', 'color': 'from-lime-400 to-lime-500'},
                ]
            },
            'vitamins': {
                'title': '비타민',
                'nutrients': [
                    {'key': 'vitamin_a', 'name': '비타민 A', 'unit': 'μg', 'recommended': '700μg', 'color': 'from-yellow-400 to-yellow-500'},
                    {'key': 'vitamin_b1', 'name': '비타민 B1', 'unit': 'mg', 'recommended': '1.1mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'vitamin_b2', 'name': '비타민 B2', 'unit': 'mg', 'recommended': '1.1mg', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'vitamin_b3', 'name': '비타민 B3', 'unit': 'mg', 'recommended': '14mg', 'color': 'from-red-400 to-red-500'},
                    {'key': 'vitamin_b6', 'name': '비타민 B6', 'unit': 'mg', 'recommended': '1.3mg', 'color': 'from-pink-400 to-pink-500'},
                    {'key': 'vitamin_b12', 'name': '비타민 B12', 'unit': 'μg', 'recommended': '2.4μg', 'color': 'from-purple-400 to-purple-500'},
                    {'key': 'vitamin_c', 'name': '비타민 C', 'unit': 'mg', 'recommended': '65mg', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'vitamin_d', 'name': '비타민 D', 'unit': 'μg', 'recommended': '15μg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'vitamin_e', 'name': '비타민 E', 'unit': 'mg', 'recommended': '15mg', 'color': 'from-teal-400 to-teal-500'},
                    {'key': 'vitamin_k', 'name': '비타민 K', 'unit': 'μg', 'recommended': '90μg', 'color': 'from-green-400 to-green-500'},
                    {'key': 'folate', 'name': '엽산', 'unit': 'μg', 'recommended': '400μg', 'color': 'from-emerald-400 to-emerald-500'},
                    {'key': 'choline', 'name': '콜린', 'unit': 'mg', 'recommended': '425mg', 'color': 'from-sky-400 to-sky-500'},
                ]
            },
            'other': {
                'title': '기타 영양소',
                'nutrients': [
                    {'key': 'cholesterol', 'name': '콜레스테롤', 'unit': 'mg', 'recommended': '300mg', 'color': 'from-rose-400 to-rose-500'},
                    {'key': 'saturated_fat', 'name': '포화지방', 'unit': 'g', 'recommended': '20g', 'color': 'from-red-400 to-red-500'},
                    {'key': 'omega3', 'name': '오메가3', 'unit': 'g', 'recommended': '1.6g', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'omega6', 'name': '오메가6', 'unit': 'g', 'recommended': '17g', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'trans_fat', 'name': '트랜스지방', 'unit': 'g', 'recommended': '2g', 'color': 'from-gray-400 to-gray-500'},
                    {'key': 'caffeine', 'name': '카페인', 'unit': 'mg', 'recommended': '400mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'alcohol', 'name': '알코올', 'unit': 'g', 'recommended': '20g', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'water', 'name': '수분', 'unit': 'g', 'recommended': '2000-3000g', 'color': 'from-cyan-400 to-cyan-500'},
                ]
            }
        }
    
    # 각 영양소에 현재 값과 비율 추가
    for category_data in nutrient_categories.values():
        for nutrient_info in category_data['nutrients']:
            key = nutrient_info['key']
            nutrient_info['current'] = today_nutrition.get(key, 0)
            nutrient_info['percentage'] = nutrient_percentages.get(key, 0)
    
    # 최근 기록 (최근 7일 일별 종합)
    recent_daily_summaries = get_daily_summaries(request.user, days=7)
    
    context = {
        'profile': profile,
        'today_logs': today_logs,
        'today_nutrition': today_nutrition,
        'nutrient_percentages': nutrient_percentages,
        'nutrient_categories': nutrient_categories,
        'recent_daily_summaries': recent_daily_summaries,
    }
    
    return render(request, 'nutrients_codi/dashboard.html', context)

@login_required
def daily_detail(request, year, month, day):
    """일별 세부 정보 페이지"""
    from datetime import date
    
    try:
        target_date = date(int(year), int(month), int(day))
    except (ValueError, TypeError):
        messages.error(request, '유효하지 않은 날짜입니다.')
        return redirect('nutrients_codi:dashboard')
    
    # 해당 날짜의 모든 음식 기록
    daily_logs = FoodLog.objects.select_related('food').filter(
        user=request.user,
        consumed_date=target_date
    ).order_by('-consumed_at')
    
    if not daily_logs.exists():
        messages.info(request, f'{target_date.strftime("%Y년 %m월 %d일")}에는 기록된 음식이 없습니다.')
        return redirect('nutrients_codi:dashboard')
    
    # 해당 날짜의 영양소 합계
    from django.db.models import Sum
    daily_aggregates = daily_logs.aggregate(
        # 기본 영양소
        total_calories=Sum('total_calories'),
        total_protein=Sum('total_protein'),
        total_carbs=Sum('total_carbs'),
        total_fat=Sum('total_fat'),
        total_fiber=Sum('total_fiber'),
        total_sugar=Sum('total_sugar'),
        
        # 미네랄
        total_sodium=Sum('total_sodium'),
        total_potassium=Sum('total_potassium'),
        total_calcium=Sum('total_calcium'),
        total_iron=Sum('total_iron'),
        total_magnesium=Sum('total_magnesium'),
        total_phosphorus=Sum('total_phosphorus'),
        total_zinc=Sum('total_zinc'),
        total_copper=Sum('total_copper'),
        total_manganese=Sum('total_manganese'),
        total_selenium=Sum('total_selenium'),
        
        # 비타민
        total_vitamin_a=Sum('total_vitamin_a'),
        total_vitamin_b1=Sum('total_vitamin_b1'),
        total_vitamin_b2=Sum('total_vitamin_b2'),
        total_vitamin_b3=Sum('total_vitamin_b3'),
        total_vitamin_b6=Sum('total_vitamin_b6'),
        total_vitamin_b12=Sum('total_vitamin_b12'),
        total_vitamin_c=Sum('total_vitamin_c'),
        total_vitamin_d=Sum('total_vitamin_d'),
        total_vitamin_e=Sum('total_vitamin_e'),
        total_vitamin_k=Sum('total_vitamin_k'),
        total_folate=Sum('total_folate'),
        total_choline=Sum('total_choline'),
        
        # 추가 비타민 및 영양소
        total_beta_carotene=Sum('total_beta_carotene'),
        total_niacin=Sum('total_niacin'),
        total_vitamin_d2=Sum('total_vitamin_d2'),
        total_vitamin_d3=Sum('total_vitamin_d3'),
        total_vitamin_k1=Sum('total_vitamin_k1'),
        total_vitamin_k2=Sum('total_vitamin_k2'),
        
        # 추가 미네랄
        total_iodine=Sum('total_iodine'),
        total_fluorine=Sum('total_fluorine'),
        total_chromium=Sum('total_chromium'),
        total_molybdenum=Sum('total_molybdenum'),
        total_chlorine=Sum('total_chlorine'),
        
        # 기타 영양소
        total_cholesterol=Sum('total_cholesterol'),
        total_saturated_fat=Sum('total_saturated_fat'),
        total_monounsaturated_fat=Sum('total_monounsaturated_fat'),
        total_polyunsaturated_fat=Sum('total_polyunsaturated_fat'),
        total_omega3=Sum('total_omega3'),
        total_omega6=Sum('total_omega6'),
        total_trans_fat=Sum('total_trans_fat'),
        total_caffeine=Sum('total_caffeine'),
        total_alcohol=Sum('total_alcohol'),
        total_water=Sum('total_water'),
        total_ash=Sum('total_ash')
    )
    
    # 프로필 정보 (권장량 계산용)
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
        profile.calculate_daily_needs()
    
    # 영양소 데이터 정리
    daily_nutrition = {
        # 기본 영양소
        'calories': daily_aggregates['total_calories'] or 0,
        'protein': daily_aggregates['total_protein'] or 0,
        'carbs': daily_aggregates['total_carbs'] or 0,
        'fat': daily_aggregates['total_fat'] or 0,
        'fiber': daily_aggregates['total_fiber'] or 0,
        'sugar': daily_aggregates['total_sugar'] or 0,
        
        # 미네랄
        'sodium': daily_aggregates['total_sodium'] or 0,
        'potassium': daily_aggregates['total_potassium'] or 0,
        'calcium': daily_aggregates['total_calcium'] or 0,
        'iron': daily_aggregates['total_iron'] or 0,
        'magnesium': daily_aggregates['total_magnesium'] or 0,
        'phosphorus': daily_aggregates['total_phosphorus'] or 0,
        'zinc': daily_aggregates['total_zinc'] or 0,
        'copper': daily_aggregates['total_copper'] or 0,
        'manganese': daily_aggregates['total_manganese'] or 0,
        'selenium': daily_aggregates['total_selenium'] or 0,
        
        # 비타민
        'vitamin_a': daily_aggregates['total_vitamin_a'] or 0,
        'vitamin_b1': daily_aggregates['total_vitamin_b1'] or 0,
        'vitamin_b2': daily_aggregates['total_vitamin_b2'] or 0,
        'vitamin_b3': daily_aggregates['total_vitamin_b3'] or 0,
        'vitamin_b6': daily_aggregates['total_vitamin_b6'] or 0,
        'vitamin_b12': daily_aggregates['total_vitamin_b12'] or 0,
        'vitamin_c': daily_aggregates['total_vitamin_c'] or 0,
        'vitamin_d': daily_aggregates['total_vitamin_d'] or 0,
        'vitamin_e': daily_aggregates['total_vitamin_e'] or 0,
        'vitamin_k': daily_aggregates['total_vitamin_k'] or 0,
        'folate': daily_aggregates['total_folate'] or 0,
        'choline': daily_aggregates['total_choline'] or 0,
        
        # 추가 비타민 및 영양소
        'beta_carotene': daily_aggregates['total_beta_carotene'] or 0,
        'niacin': daily_aggregates['total_niacin'] or 0,
        'vitamin_d2': daily_aggregates['total_vitamin_d2'] or 0,
        'vitamin_d3': daily_aggregates['total_vitamin_d3'] or 0,
        'vitamin_k1': daily_aggregates['total_vitamin_k1'] or 0,
        'vitamin_k2': daily_aggregates['total_vitamin_k2'] or 0,
        
        # 추가 미네랄
        'iodine': daily_aggregates['total_iodine'] or 0,
        'fluorine': daily_aggregates['total_fluorine'] or 0,
        'chromium': daily_aggregates['total_chromium'] or 0,
        'molybdenum': daily_aggregates['total_molybdenum'] or 0,
        'chlorine': daily_aggregates['total_chlorine'] or 0,
        
        # 기타 영양소
        'cholesterol': daily_aggregates['total_cholesterol'] or 0,
        'saturated_fat': daily_aggregates['total_saturated_fat'] or 0,
        'monounsaturated_fat': daily_aggregates['total_monounsaturated_fat'] or 0,
        'polyunsaturated_fat': daily_aggregates['total_polyunsaturated_fat'] or 0,
        'omega3': daily_aggregates['total_omega3'] or 0,
        'omega6': daily_aggregates['total_omega6'] or 0,
        'trans_fat': daily_aggregates['total_trans_fat'] or 0,
        'caffeine': daily_aggregates['total_caffeine'] or 0,
        'alcohol': daily_aggregates['total_alcohol'] or 0,
        'water': daily_aggregates['total_water'] or 0,
        'ash': daily_aggregates['total_ash'] or 0,
    }
    
    # 브라우저 언어 감지
    from .utils import get_browser_language
    browser_language = get_browser_language(request)
    
    # 권장량 대비 비율 계산
    nutrient_percentages = {}
    recommended_amounts = {
        'fiber': 25, 'sugar': 50, 'sodium': 2000, 'potassium': 3500,
        'calcium': 1000, 'iron': 8, 'magnesium': 400, 'phosphorus': 700,
        'zinc': 8, 'copper': 0.9, 'manganese': 2.3, 'selenium': 55,
        'iodine': 150, 'fluorine': 3, 'chromium': 35, 'molybdenum': 45, 'chlorine': 2300,
        'vitamin_a': 700, 'vitamin_b1': 1.1, 'vitamin_b2': 1.1, 'vitamin_b3': 14,
        'vitamin_b6': 1.3, 'vitamin_b12': 2.4, 'vitamin_c': 65, 'vitamin_d': 15,
        'vitamin_e': 15, 'vitamin_k': 90, 'folate': 400, 'choline': 425,
        'beta_carotene': 700, 'niacin': 14, 'vitamin_d2': 15, 'vitamin_d3': 15,
        'vitamin_k1': 90, 'vitamin_k2': 90,
        'cholesterol': 300, 'saturated_fat': 20, 'monounsaturated_fat': 25, 'polyunsaturated_fat': 20,
        'omega3': 1.6, 'omega6': 17, 'trans_fat': 2, 'caffeine': 400, 'alcohol': 20, 
        'water': 3000, 'ash': 10,
    }
    
    for nutrient, current_amount in daily_nutrition.items():
        if nutrient in recommended_amounts:
            recommended = recommended_amounts[nutrient]
            if recommended > 0:
                percentage = (current_amount / recommended) * 100
                nutrient_percentages[nutrient] = round(percentage, 1)
            else:
                nutrient_percentages[nutrient] = 0
        else:
            nutrient_percentages[nutrient] = 0
    
    # 영양소 카테고리별 데이터 구조화 (다국어 지원)
    if browser_language == 'en':
        nutrient_categories = {
            'basic': {
                'title': 'Basic Nutrients',
                'nutrients': [
                    {'key': 'fiber', 'name': 'Dietary Fiber', 'unit': 'g', 'recommended': '25-35g', 'color': 'from-green-400 to-green-500'},
                    {'key': 'sugar', 'name': 'Sugar', 'unit': 'g', 'recommended': '<50g', 'color': 'from-pink-400 to-pink-500'},
                ]
            },
            'minerals': {
                'title': 'Minerals',
                'nutrients': [
                    {'key': 'sodium', 'name': 'Sodium', 'unit': 'mg', 'recommended': '<2000mg', 'color': 'from-purple-400 to-purple-500'},
                    {'key': 'potassium', 'name': 'Potassium', 'unit': 'mg', 'recommended': '3500mg', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'calcium', 'name': 'Calcium', 'unit': 'mg', 'recommended': '1000mg', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'iron', 'name': 'Iron', 'unit': 'mg', 'recommended': '8-18mg', 'color': 'from-red-400 to-red-500'},
                    {'key': 'magnesium', 'name': 'Magnesium', 'unit': 'mg', 'recommended': '400mg', 'color': 'from-teal-400 to-teal-500'},
                    {'key': 'phosphorus', 'name': 'Phosphorus', 'unit': 'mg', 'recommended': '700mg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'zinc', 'name': 'Zinc', 'unit': 'mg', 'recommended': '8-11mg', 'color': 'from-gray-400 to-gray-500'},
                    {'key': 'copper', 'name': 'Copper', 'unit': 'mg', 'recommended': '0.9mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'manganese', 'name': 'Manganese', 'unit': 'mg', 'recommended': '2.3mg', 'color': 'from-cyan-400 to-cyan-500'},
                    {'key': 'selenium', 'name': 'Selenium', 'unit': 'μg', 'recommended': '55μg', 'color': 'from-lime-400 to-lime-500'},
                    {'key': 'iodine', 'name': 'Iodine', 'unit': 'μg', 'recommended': '150μg', 'color': 'from-emerald-400 to-emerald-500'},
                    {'key': 'fluorine', 'name': 'Fluorine', 'unit': 'mg', 'recommended': '3mg', 'color': 'from-sky-400 to-sky-500'},
                    {'key': 'chromium', 'name': 'Chromium', 'unit': 'μg', 'recommended': '35μg', 'color': 'from-violet-400 to-violet-500'},
                    {'key': 'molybdenum', 'name': 'Molybdenum', 'unit': 'μg', 'recommended': '45μg', 'color': 'from-fuchsia-400 to-fuchsia-500'},
                    {'key': 'chlorine', 'name': 'Chlorine', 'unit': 'mg', 'recommended': '2300mg', 'color': 'from-rose-400 to-rose-500'},
                ]
            },
            'vitamins': {
                'title': 'Vitamins',
                'nutrients': [
                    {'key': 'vitamin_a', 'name': 'Vitamin A', 'unit': 'μg', 'recommended': '700μg', 'color': 'from-yellow-400 to-yellow-500'},
                    {'key': 'vitamin_b1', 'name': 'Vitamin B1', 'unit': 'mg', 'recommended': '1.1mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'vitamin_b2', 'name': 'Vitamin B2', 'unit': 'mg', 'recommended': '1.1mg', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'vitamin_b3', 'name': 'Vitamin B3', 'unit': 'mg', 'recommended': '14mg', 'color': 'from-red-400 to-red-500'},
                    {'key': 'vitamin_b6', 'name': 'Vitamin B6', 'unit': 'mg', 'recommended': '1.3mg', 'color': 'from-pink-400 to-pink-500'},
                    {'key': 'vitamin_b12', 'name': 'Vitamin B12', 'unit': 'μg', 'recommended': '2.4μg', 'color': 'from-purple-400 to-purple-500'},
                    {'key': 'vitamin_c', 'name': 'Vitamin C', 'unit': 'mg', 'recommended': '65mg', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'vitamin_d', 'name': 'Vitamin D', 'unit': 'μg', 'recommended': '15μg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'vitamin_e', 'name': 'Vitamin E', 'unit': 'mg', 'recommended': '15mg', 'color': 'from-teal-400 to-teal-500'},
                    {'key': 'vitamin_k', 'name': 'Vitamin K', 'unit': 'μg', 'recommended': '90μg', 'color': 'from-green-400 to-green-500'},
                    {'key': 'folate', 'name': 'Folate', 'unit': 'μg', 'recommended': '400μg', 'color': 'from-emerald-400 to-emerald-500'},
                    {'key': 'choline', 'name': 'Choline', 'unit': 'mg', 'recommended': '425mg', 'color': 'from-sky-400 to-sky-500'},
                    {'key': 'beta_carotene', 'name': 'Beta Carotene', 'unit': 'μg', 'recommended': '700μg', 'color': 'from-yellow-400 to-yellow-500'},
                    {'key': 'niacin', 'name': 'Niacin', 'unit': 'mg', 'recommended': '14mg', 'color': 'from-red-400 to-red-500'},
                    {'key': 'vitamin_d2', 'name': 'Vitamin D2', 'unit': 'μg', 'recommended': '15μg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'vitamin_d3', 'name': 'Vitamin D3', 'unit': 'μg', 'recommended': '15μg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'vitamin_k1', 'name': 'Vitamin K1', 'unit': 'μg', 'recommended': '90μg', 'color': 'from-green-400 to-green-500'},
                    {'key': 'vitamin_k2', 'name': 'Vitamin K2', 'unit': 'μg', 'recommended': '90μg', 'color': 'from-green-400 to-green-500'},
                ]
            },
            'other': {
                'title': 'Other Nutrients',
                'nutrients': [
                    {'key': 'cholesterol', 'name': 'Cholesterol', 'unit': 'mg', 'recommended': '300mg', 'color': 'from-rose-400 to-rose-500'},
                    {'key': 'saturated_fat', 'name': 'Saturated Fat', 'unit': 'g', 'recommended': '20g', 'color': 'from-red-400 to-red-500'},
                    {'key': 'monounsaturated_fat', 'name': 'Monounsaturated Fat', 'unit': 'g', 'recommended': '25g', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'polyunsaturated_fat', 'name': 'Polyunsaturated Fat', 'unit': 'g', 'recommended': '20g', 'color': 'from-yellow-400 to-yellow-500'},
                    {'key': 'omega3', 'name': 'Omega-3', 'unit': 'g', 'recommended': '1.6g', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'omega6', 'name': 'Omega-6', 'unit': 'g', 'recommended': '17g', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'trans_fat', 'name': 'Trans Fat', 'unit': 'g', 'recommended': '2g', 'color': 'from-gray-400 to-gray-500'},
                    {'key': 'caffeine', 'name': 'Caffeine', 'unit': 'mg', 'recommended': '400mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'alcohol', 'name': 'Alcohol', 'unit': 'g', 'recommended': '20g', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'water', 'name': 'Water', 'unit': 'g', 'recommended': '2000-3000g', 'color': 'from-cyan-400 to-cyan-500'},
                    {'key': 'ash', 'name': 'Ash', 'unit': 'g', 'recommended': '10g', 'color': 'from-gray-400 to-gray-500'},
                ]
            }
        }
    else:
        # 한국어 버전 (기본값)
        nutrient_categories = {
            'basic': {
                'title': '기초 영양소',
                'nutrients': [
                    {'key': 'fiber', 'name': '식이섬유', 'unit': 'g', 'recommended': '25-35g', 'color': 'from-green-400 to-green-500'},
                    {'key': 'sugar', 'name': '당분', 'unit': 'g', 'recommended': '<50g', 'color': 'from-pink-400 to-pink-500'},
                ]
            },
            'minerals': {
                'title': '미네랄',
                'nutrients': [
                    {'key': 'sodium', 'name': '나트륨', 'unit': 'mg', 'recommended': '<2000mg', 'color': 'from-purple-400 to-purple-500'},
                    {'key': 'potassium', 'name': '칼륨', 'unit': 'mg', 'recommended': '3500mg', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'calcium', 'name': '칼슘', 'unit': 'mg', 'recommended': '1000mg', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'iron', 'name': '철분', 'unit': 'mg', 'recommended': '8-18mg', 'color': 'from-red-400 to-red-500'},
                    {'key': 'magnesium', 'name': '마그네슘', 'unit': 'mg', 'recommended': '400mg', 'color': 'from-teal-400 to-teal-500'},
                    {'key': 'phosphorus', 'name': '인', 'unit': 'mg', 'recommended': '700mg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'zinc', 'name': '아연', 'unit': 'mg', 'recommended': '8-11mg', 'color': 'from-gray-400 to-gray-500'},
                    {'key': 'copper', 'name': '구리', 'unit': 'mg', 'recommended': '0.9mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'manganese', 'name': '망간', 'unit': 'mg', 'recommended': '2.3mg', 'color': 'from-cyan-400 to-cyan-500'},
                    {'key': 'selenium', 'name': '셀레늄', 'unit': 'μg', 'recommended': '55μg', 'color': 'from-lime-400 to-lime-500'},
                    {'key': 'iodine', 'name': '요오드', 'unit': 'μg', 'recommended': '150μg', 'color': 'from-emerald-400 to-emerald-500'},
                    {'key': 'fluorine', 'name': '불소', 'unit': 'mg', 'recommended': '3mg', 'color': 'from-sky-400 to-sky-500'},
                    {'key': 'chromium', 'name': '크롬', 'unit': 'μg', 'recommended': '35μg', 'color': 'from-violet-400 to-violet-500'},
                    {'key': 'molybdenum', 'name': '몰리브덴', 'unit': 'μg', 'recommended': '45μg', 'color': 'from-fuchsia-400 to-fuchsia-500'},
                    {'key': 'chlorine', 'name': '염소', 'unit': 'mg', 'recommended': '2300mg', 'color': 'from-rose-400 to-rose-500'},
                ]
            },
            'vitamins': {
                'title': '비타민',
                'nutrients': [
                    {'key': 'vitamin_a', 'name': '비타민 A', 'unit': 'μg', 'recommended': '700μg', 'color': 'from-yellow-400 to-yellow-500'},
                    {'key': 'vitamin_b1', 'name': '비타민 B1', 'unit': 'mg', 'recommended': '1.1mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'vitamin_b2', 'name': '비타민 B2', 'unit': 'mg', 'recommended': '1.1mg', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'vitamin_b3', 'name': '비타민 B3', 'unit': 'mg', 'recommended': '14mg', 'color': 'from-red-400 to-red-500'},
                    {'key': 'vitamin_b6', 'name': '비타민 B6', 'unit': 'mg', 'recommended': '1.3mg', 'color': 'from-pink-400 to-pink-500'},
                    {'key': 'vitamin_b12', 'name': '비타민 B12', 'unit': 'μg', 'recommended': '2.4μg', 'color': 'from-purple-400 to-purple-500'},
                    {'key': 'vitamin_c', 'name': '비타민 C', 'unit': 'mg', 'recommended': '65mg', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'vitamin_d', 'name': '비타민 D', 'unit': 'μg', 'recommended': '15μg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'vitamin_e', 'name': '비타민 E', 'unit': 'mg', 'recommended': '15mg', 'color': 'from-teal-400 to-teal-500'},
                    {'key': 'vitamin_k', 'name': '비타민 K', 'unit': 'μg', 'recommended': '90μg', 'color': 'from-green-400 to-green-500'},
                    {'key': 'folate', 'name': '엽산', 'unit': 'μg', 'recommended': '400μg', 'color': 'from-emerald-400 to-emerald-500'},
                    {'key': 'choline', 'name': '콜린', 'unit': 'mg', 'recommended': '425mg', 'color': 'from-sky-400 to-sky-500'},
                    {'key': 'beta_carotene', 'name': '베타카로틴', 'unit': 'μg', 'recommended': '700μg', 'color': 'from-yellow-400 to-yellow-500'},
                    {'key': 'niacin', 'name': '나이아신', 'unit': 'mg', 'recommended': '14mg', 'color': 'from-red-400 to-red-500'},
                    {'key': 'vitamin_d2', 'name': '비타민 D2', 'unit': 'μg', 'recommended': '15μg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'vitamin_d3', 'name': '비타민 D3', 'unit': 'μg', 'recommended': '15μg', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'vitamin_k1', 'name': '비타민 K1', 'unit': 'μg', 'recommended': '90μg', 'color': 'from-green-400 to-green-500'},
                    {'key': 'vitamin_k2', 'name': '비타민 K2', 'unit': 'μg', 'recommended': '90μg', 'color': 'from-green-400 to-green-500'},
                ]
            },
            'other': {
                'title': '기타 영양소',
                'nutrients': [
                    {'key': 'cholesterol', 'name': '콜레스테롤', 'unit': 'mg', 'recommended': '300mg', 'color': 'from-rose-400 to-rose-500'},
                    {'key': 'saturated_fat', 'name': '포화지방', 'unit': 'g', 'recommended': '20g', 'color': 'from-red-400 to-red-500'},
                    {'key': 'monounsaturated_fat', 'name': '단일불포화지방', 'unit': 'g', 'recommended': '25g', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'polyunsaturated_fat', 'name': '다중불포화지방', 'unit': 'g', 'recommended': '20g', 'color': 'from-yellow-400 to-yellow-500'},
                    {'key': 'omega3', 'name': '오메가3', 'unit': 'g', 'recommended': '1.6g', 'color': 'from-blue-400 to-blue-500'},
                    {'key': 'omega6', 'name': '오메가6', 'unit': 'g', 'recommended': '17g', 'color': 'from-indigo-400 to-indigo-500'},
                    {'key': 'trans_fat', 'name': '트랜스지방', 'unit': 'g', 'recommended': '2g', 'color': 'from-gray-400 to-gray-500'},
                    {'key': 'caffeine', 'name': '카페인', 'unit': 'mg', 'recommended': '400mg', 'color': 'from-amber-400 to-amber-500'},
                    {'key': 'alcohol', 'name': '알코올', 'unit': 'g', 'recommended': '20g', 'color': 'from-orange-400 to-orange-500'},
                    {'key': 'water', 'name': '수분', 'unit': 'g', 'recommended': '2000-3000g', 'color': 'from-cyan-400 to-cyan-500'},
                    {'key': 'ash', 'name': '회분', 'unit': 'g', 'recommended': '10g', 'color': 'from-gray-400 to-gray-500'},
                ]
            }
        }
    
    # 각 영양소에 현재 값과 비율 추가
    for category_data in nutrient_categories.values():
        for nutrient_info in category_data['nutrients']:
            key = nutrient_info['key']
            nutrient_info['current'] = daily_nutrition.get(key, 0)
            nutrient_info['percentage'] = nutrient_percentages.get(key, 0)

    context = {
        'target_date': target_date,
        'daily_logs': daily_logs,
        'daily_nutrition': daily_nutrition,
        'nutrient_percentages': nutrient_percentages,
        'nutrient_categories': nutrient_categories,
        'profile': profile,
        'browser_language': browser_language,
    }
    
    return render(request, 'nutrients_codi/daily_detail.html', context)

@login_required
def profile_setup(request):
    """프로필 설정 페이지"""
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
        profile.calculate_daily_needs()
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            # 권장 섭취량 자동 계산
            profile.calculate_daily_needs()
            messages.success(request, '프로필이 성공적으로 저장되었습니다!')
            return redirect('nutrients_codi:dashboard')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'nutrients_codi/profile_setup.html', {
        'form': form,
        'profile': profile,
    })

@login_required
def analyze_food(request):
    """음식 분석 처리 (AJAX용)"""
    logger.info(f"음식 분석 요청 시작: {request.user.username}")
    
    if request.method == 'POST':
        logger.info(f"📝 POST 요청 수신: {request.POST}")
        
        form = FoodAnalysisForm(request.POST)
        if form.is_valid():
            food_text = form.cleaned_data['food_text']
            
            logger.info(f"✅ 폼 검증 성공: food_text='{food_text}'")
            
            try:
                # AI 서비스 초기화
                from .ai_service import GeminiAIService
                try:
                    ai_service = GeminiAIService()
                    logger.info("🤖 AI 서비스 초기화 성공")
                except ValueError as e:
                    logger.error(f"❌ AI 서비스 초기화 실패: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': 'AI 서비스가 설정되지 않았습니다. 관리자에게 문의하세요.'
                    })
                
                # 브라우저 언어 감지
                from .utils import get_browser_language, get_language_messages
                browser_language = get_browser_language(request)
                messages = get_language_messages(browser_language)
                
                # AI 분석 실행 (식사 유형 자동 분석)
                logger.info(f"🔍 AI 분석 시작: '{food_text}' (언어: {browser_language})")
                ai_results = ai_service.analyze_food_text(food_text, browser_language)
                logger.info(f"📋 AI 분석 결과: {ai_results}")
                
                if not ai_results:
                    logger.warning("⚠️ AI 분석 결과가 비어있음")
                    return JsonResponse({
                        'success': False,
                        'message': messages['analysis_failed']
                    })
                
                # 분석 결과를 FoodLog로 저장
                saved_count = 0
                not_found_foods = []
                saved_foods = []
                
                logger.info(f"🎯 음식 매칭 시작: {len(ai_results)}개 결과")
                
                for i, result in enumerate(ai_results):
                    logger.info(f"🍽️ 음식 {i+1} 처리 시작: {result}")
                    
                    food_name = result.get('food_name', '')
                    quantity = result.get('quantity', 100)  # 기본값 100g
                    # AI가 분석한 식사유형 (기본값: lunch)
                    result_meal_type = result.get('meal_type', 'lunch')
                    
                    logger.info(f"음식명: '{food_name}', 수량: {quantity}, 식사유형: '{result_meal_type}'")
                    
                    # meal_type 검증 및 정규화
                    valid_meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
                    if result_meal_type not in valid_meal_types:
                        logger.warning(f"유효하지 않은 meal_type: '{result_meal_type}', 'lunch'로 변경")
                        result_meal_type = 'lunch'
                    
                    # 음식 데이터베이스에서 검색
                    food = None
                    search_method = None
                    
                    # 1. 정확한 이름으로 검색 (인덱스 최적화)
                    try:
                        food = Food.objects.select_related().get(name=food_name)
                        search_method = "정확한 이름 매칭"
                        logger.info(f"✅ [{search_method}] 성공: '{food_name}'")
                    except Food.DoesNotExist:
                        logger.info(f"❌ [정확한 이름 매칭] 실패: '{food_name}'")
                        pass
                    
                    # 2. 임베딩 기반 유사 음식 검색
                    if not food:
                        try:
                            logger.info(f"🔍 [임베딩 검색] 시도: '{food_name}'")
                            similar_match = ai_service.find_similar_food_by_embedding(food_name, threshold=0.7)
                            if similar_match:
                                food = similar_match['food']
                                search_method = "임베딩 기반 유사 검색"
                                logger.info(f"✅ [{search_method}] 성공: '{food_name}' -> '{food.name}' (유사도: {similar_match['similarity']:.3f})")
                            else:
                                logger.info(f"❌ [임베딩 검색] 실패: '{food_name}' (유사도 임계값 미달)")
                        except Exception as e:
                            logger.warning(f"❌ [임베딩 검색] 오류: {e}")
                    
                    # 3. 문자열 유사도 기반 유사 음식 검색
                    if not food:
                        try:
                            logger.info(f"🔍 [문자열 유사도 검색] 시도: '{food_name}'")
                            similar_match = ai_service.find_similar_food_by_string_matching(food_name, threshold=0.6)
                            if similar_match:
                                food = similar_match['food']
                                search_method = "문자열 유사도 기반 검색"
                                logger.info(f"✅ [{search_method}] 성공: '{food_name}' -> '{food.name}' (유사도: {similar_match['similarity']:.3f})")
                            else:
                                logger.info(f"❌ [문자열 유사도 검색] 실패: '{food_name}' (유사도 임계값 미달)")
                        except Exception as e:
                            logger.error(f"❌ [문자열 유사도 검색] 오류: {e}")
                    
                    # 4. LLM으로 새로운 음식 생성
                    if not food:
                        try:
                            logger.info(f"🤖 [LLM 생성] 시도: '{food_name}'")
                            llm_match = ai_service.create_food_from_llm(food_name)
                            if llm_match:
                                food = llm_match['food']
                                search_method = "LLM 기반 새 음식 생성"
                                logger.info(f"✅ [{search_method}] 성공: '{food_name}' -> '{food.name}'")
                            else:
                                logger.info(f"❌ [LLM 생성] 실패: '{food_name}'")
                        except Exception as e:
                            logger.error(f"LLM 기반 음식 생성 실패: {e}")
                    
                    if food:
                        # FoodLog 생성
                        try:
                            food_log = FoodLog.objects.create(
                                user=request.user,
                                food=food,
                                quantity=quantity,
                                meal_type=result_meal_type,
                                original_text=food_text,
                                ai_analysis=result
                            )
                            logger.info(f"💾 FoodLog 저장 완료: {food.name} ({quantity}g) - {search_method}")
                        except Exception as e:
                            logger.error(f"❌ FoodLog 생성 실패: {e}")
                            logger.error(f"Food: {food.name}, Quantity: {quantity}, Meal Type: {result_meal_type}")
                            continue
                        
                        saved_count += 1
                        saved_foods.append({
                            'name': food.name,
                            'quantity': quantity,
                            'meal_type': result_meal_type,
                            'calories': food_log.total_calories,
                            'protein': food_log.total_protein,
                            'carbs': food_log.total_carbs,
                            'fat': food_log.total_fat,
                        })
                    else:
                        logger.warning(f"❌ 모든 검색 방법 실패: '{food_name}'")
                        not_found_foods.append(food_name)
                
                # 결과 메시지 생성
                logger.info(f"📊 분석 결과 요약: 총 {len(ai_results)}개 음식 분석, {saved_count}개 저장 성공, {len(not_found_foods)}개 실패")
                
                if saved_count > 0:
                    message = f'{saved_count}{messages["analysis_success"]}'
                    if not_found_foods:
                        if browser_language == 'ko':
                            message += f' (찾을 수 없는 음식: {", ".join(not_found_foods)})'
                        else:
                            message += f' (Foods not found: {", ".join(not_found_foods)})'
                    
                    logger.info(f"✅ 최종 결과: {message}")
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'saved_foods': saved_foods,
                        'not_found_foods': not_found_foods,
                        'saved_count': saved_count,
                        'language': browser_language
                    })
                else:
                    logger.warning(f"❌ 최종 결과: 모든 음식 분석 실패")
                    return JsonResponse({
                        'success': False,
                        'message': messages['food_not_found'],
                        'not_found_foods': not_found_foods,
                        'language': browser_language
                    })
                
            except Exception as e:
                logger.error(f"음식 분석 중 오류: {e}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': f'음식 분석 중 오류가 발생했습니다: {str(e)}'
                })
        else:
            logger.error(f"폼 검증 실패: {form.errors}")
            return JsonResponse({
                'success': False,
                'message': messages.get('form_validation_error', '입력이 올바르지 않습니다.')
            })
    
    return JsonResponse({
        'success': False,
        'message': '잘못된 요청입니다.'
    })


@login_required
def delete_food_log(request, log_id):
    """음식 기록 삭제"""
    if request.method == 'POST':
        food_log = get_object_or_404(FoodLog, id=log_id, user=request.user)
        consumed_date = food_log.consumed_date
        food_log.delete()
        messages.success(request, '음식 기록이 삭제되었습니다.')
        
        # 일별 상세정보 페이지에서 온 경우 해당 날짜로 리다이렉트
        if 'daily_detail' in request.META.get('HTTP_REFERER', ''):
            return redirect('nutrients_codi:daily_detail', 
                          year=consumed_date.year, 
                          month=consumed_date.month, 
                          day=consumed_date.day)
    
    return redirect('nutrients_codi:dashboard')

@login_required
def edit_food_log(request, log_id):
    """음식 기록 수정 (인라인 수정용)"""
    food_log = get_object_or_404(FoodLog, id=log_id, user=request.user)
    
    if request.method == 'POST':
        # 수정된 영양소 값들 받기
        quantity = float(request.POST.get('quantity', food_log.quantity))
        
        # 영양소 값들 업데이트
        food_log.quantity = quantity
        food_log.save()  # save() 메서드에서 total_* 값들이 자동으로 재계산됨
        
        messages.success(request, '음식 기록이 수정되었습니다.')
        
        # 일별 상세정보 페이지로 리다이렉트
        return redirect('nutrients_codi:daily_detail', 
                      year=food_log.consumed_date.year, 
                      month=food_log.consumed_date.month, 
                      day=food_log.consumed_date.day)
    
    # GET 요청 시 404 (인라인 수정만 지원)
    from django.http import Http404
    raise Http404("Page not found")
