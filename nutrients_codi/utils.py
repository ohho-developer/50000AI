"""
다국어 지원을 위한 유틸리티 함수들
"""

def get_browser_language(request):
    """
    브라우저의 언어 설정을 감지하여 지원하는 언어 코드를 반환
    
    Args:
        request: Django request 객체
        
    Returns:
        str: 지원하는 언어 코드 ('ko' 또는 'en')
    """
    # Accept-Language 헤더에서 언어 우선순위 추출
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    
    # 지원하는 언어 목록
    supported_languages = ['ko', 'en']
    
    # 브라우저 언어 설정 파싱
    if accept_language:
        # Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7
        languages = []
        for lang in accept_language.split(','):
            lang = lang.strip().split(';')[0]  # 품질 값 제거
            lang = lang.split('-')[0]  # 지역 코드 제거 (ko-KR -> ko)
            languages.append(lang)
        
        # 지원하는 언어 중 첫 번째로 일치하는 것 반환
        for lang in languages:
            if lang in supported_languages:
                return lang
    
    # 기본값: 한국어
    return 'ko'


def get_language_messages(language='ko'):
    """
    언어에 따른 메시지 딕셔너리 반환
    
    Args:
        language: 언어 코드 ('ko' 또는 'en')
        
    Returns:
        dict: 언어별 메시지 딕셔너리
    """
    messages = {
        'ko': {
            'analysis_success': '개의 음식이 성공적으로 기록되었습니다.',
            'analysis_failed': '음식 분석에 실패했습니다. 다시 시도해주세요.',
            'food_not_found': '분석된 음식 중 데이터베이스에 있는 음식이 없습니다.',
            'ai_service_error': 'AI 서비스가 설정되지 않았습니다. 관리자에게 문의하세요.',
            'form_validation_error': '입력값이 올바르지 않습니다.',
            'meal_types': {
                'breakfast': '아침',
                'lunch': '점심',
                'dinner': '저녁',
                'snack': '간식'
            },
            'nutrients': {
                'calories': '칼로리',
                'protein': '단백질',
                'carbs': '탄수화물',
                'fat': '지방',
                'fiber': '식이섬유',
                'sugar': '당분',
                'sodium': '나트륨',
                'potassium': '칼륨',
                'calcium': '칼슘',
                'iron': '철분',
                'vitamin_c': '비타민 C',
                'vitamin_a': '비타민 A',
                'cholesterol': '콜레스테롤'
            }
        },
        'en': {
            'analysis_success': ' foods have been successfully recorded.',
            'analysis_failed': 'Food analysis failed. Please try again.',
            'food_not_found': 'None of the analyzed foods were found in the database.',
            'ai_service_error': 'AI service is not configured. Please contact the administrator.',
            'form_validation_error': 'Invalid input values.',
            'meal_types': {
                'breakfast': 'Breakfast',
                'lunch': 'Lunch',
                'dinner': 'Dinner',
                'snack': 'Snack'
            },
            'nutrients': {
                'calories': 'Calories',
                'protein': 'Protein',
                'carbs': 'Carbs',
                'fat': 'Fat',
                'fiber': 'Fiber',
                'sugar': 'Sugar',
                'sodium': 'Sodium',
                'potassium': 'Potassium',
                'calcium': 'Calcium',
                'iron': 'Iron',
                'vitamin_c': 'Vitamin C',
                'vitamin_a': 'Vitamin A',
                'cholesterol': 'Cholesterol'
            }
        }
    }
    
    return messages.get(language, messages['ko'])
