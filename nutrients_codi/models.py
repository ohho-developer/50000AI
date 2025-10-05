from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Profile(models.Model):
    """사용자 프로필 및 일일 권장 섭취량 정보"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 기본 정보
    gender = models.CharField(max_length=10, choices=[
        ('male', '남성'),
        ('female', '여성'),
    ], default='male')
    
    birth_date = models.DateField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True, validators=[MinValueValidator(100), MaxValueValidator(250)], help_text="키 (cm)")
    weight = models.FloatField(null=True, blank=True, validators=[MinValueValidator(30), MaxValueValidator(300)], help_text="체중 (kg)")
    
    # 목표 설정
    goal = models.CharField(max_length=20, choices=[
        ('lose_weight', '체중 감량'),
        ('maintain_weight', '체중 유지'),
        ('gain_weight', '체중 증가'),
        ('muscle_gain', '근육 증가'),
    ], default='maintain_weight')
    
    activity_level = models.CharField(max_length=20, choices=[
        ('sedentary', '거의 활동 없음'),
        ('light', '가벼운 활동'),
        ('moderate', '보통 활동'),
        ('active', '활동적'),
        ('very_active', '매우 활동적'),
    ], default='moderate')
    
    # 계산된 권장 섭취량 (자동 계산)
    daily_calories = models.IntegerField(default=2000, help_text="일일 권장 칼로리")
    daily_protein = models.FloatField(default=150, help_text="일일 권장 단백질 (g)")
    daily_carbs = models.FloatField(default=250, help_text="일일 권장 탄수화물 (g)")
    daily_fat = models.FloatField(default=67, help_text="일일 권장 지방 (g)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}의 프로필"
    
    def calculate_daily_needs(self):
        """BMR과 활동 수준을 기반으로 일일 권장 섭취량 계산"""
        # 필수 정보가 없으면 기본값 사용
        if not self.height or not self.weight:
            self.daily_calories = 2000
            self.daily_protein = 150
            self.daily_carbs = 250
            self.daily_fat = 67
            self.save()
            return
            
        # BMR 계산 (Mifflin-St Jeor Equation)
        if self.gender == 'male':
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.get_age() + 5
        else:
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.get_age() - 161
        
        # 활동 수준에 따른 계수
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9,
        }
        
        # 목표에 따른 조정
        goal_multipliers = {
            'lose_weight': 0.8,
            'maintain_weight': 1.0,
            'gain_weight': 1.2,
            'muscle_gain': 1.1,
        }
        
        tdee = bmr * activity_multipliers.get(self.activity_level, 1.55)
        daily_calories = int(tdee * goal_multipliers.get(self.goal, 1.0))
        
        # 영양소 분배 (일반적인 비율)
        self.daily_calories = daily_calories
        self.daily_protein = round(self.weight * 1.6, 1)  # 체중 1kg당 1.6g
        self.daily_carbs = round((daily_calories * 0.45) / 4, 1)  # 45% 탄수화물
        self.daily_fat = round((daily_calories * 0.25) / 9, 1)  # 25% 지방
        
        self.save()
    
    def get_age(self):
        """나이 계산"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return 30  # 기본값


class Food(models.Model):
    """식약처 DB 기반의 개별 음식 영양 정보"""
    name = models.CharField(max_length=200, help_text="음식명")
    name_english = models.CharField(max_length=200, blank=True, help_text="영문 음식명")
    
    # 기본 영양소 (100g 기준)
    calories = models.FloatField(help_text="칼로리 (kcal)")
    protein = models.FloatField(help_text="단백질 (g)")
    carbs = models.FloatField(help_text="탄수화물 (g)")
    fat = models.FloatField(help_text="지방 (g)")
    fiber = models.FloatField(default=0, help_text="식이섬유 (g)")
    sugar = models.FloatField(default=0, help_text="당분 (g)")
    
    # 미네랄
    sodium = models.FloatField(default=0, help_text="나트륨 (mg)")
    potassium = models.FloatField(default=0, help_text="칼륨 (mg)")
    calcium = models.FloatField(default=0, help_text="칼슘 (mg)")
    iron = models.FloatField(default=0, help_text="철분 (mg)")
    magnesium = models.FloatField(default=0, help_text="마그네슘 (mg)")
    phosphorus = models.FloatField(default=0, help_text="인 (mg)")
    zinc = models.FloatField(default=0, help_text="아연 (mg)")
    copper = models.FloatField(default=0, help_text="구리 (mg)")
    manganese = models.FloatField(default=0, help_text="망간 (mg)")
    selenium = models.FloatField(default=0, help_text="셀레늄 (μg)")
    
    # 비타민
    vitamin_a = models.FloatField(default=0, help_text="비타민 A (μg)")
    vitamin_b1 = models.FloatField(default=0, help_text="비타민 B1 (mg)")
    vitamin_b2 = models.FloatField(default=0, help_text="비타민 B2 (mg)")
    vitamin_b3 = models.FloatField(default=0, help_text="비타민 B3 (mg)")
    vitamin_b6 = models.FloatField(default=0, help_text="비타민 B6 (mg)")
    vitamin_b12 = models.FloatField(default=0, help_text="비타민 B12 (μg)")
    vitamin_c = models.FloatField(default=0, help_text="비타민 C (mg)")
    vitamin_d = models.FloatField(default=0, help_text="비타민 D (μg)")
    vitamin_e = models.FloatField(default=0, help_text="비타민 E (mg)")
    vitamin_k = models.FloatField(default=0, help_text="비타민 K (μg)")
    folate = models.FloatField(default=0, help_text="엽산 (μg)")
    choline = models.FloatField(default=0, help_text="콜린 (mg)")
    
    # 추가 비타민 및 영양소
    beta_carotene = models.FloatField(default=0, help_text="베타카로틴 (μg)")
    niacin = models.FloatField(default=0, help_text="나이아신 (mg)")
    vitamin_d2 = models.FloatField(default=0, help_text="비타민 D2 (μg)")
    vitamin_d3 = models.FloatField(default=0, help_text="비타민 D3 (μg)")
    vitamin_k1 = models.FloatField(default=0, help_text="비타민 K1 (μg)")
    vitamin_k2 = models.FloatField(default=0, help_text="비타민 K2 (μg)")
    
    # 추가 미네랄
    iodine = models.FloatField(default=0, help_text="요오드 (μg)")
    fluorine = models.FloatField(default=0, help_text="불소 (mg)")
    chromium = models.FloatField(default=0, help_text="크롬 (μg)")
    molybdenum = models.FloatField(default=0, help_text="몰리브덴 (μg)")
    chlorine = models.FloatField(default=0, help_text="염소 (mg)")
    
    # 기타 영양소
    cholesterol = models.FloatField(default=0, help_text="콜레스테롤 (mg)")
    saturated_fat = models.FloatField(default=0, help_text="포화지방 (g)")
    monounsaturated_fat = models.FloatField(default=0, help_text="단일불포화지방 (g)")
    polyunsaturated_fat = models.FloatField(default=0, help_text="다중불포화지방 (g)")
    omega3 = models.FloatField(default=0, help_text="오메가3 (g)")
    omega6 = models.FloatField(default=0, help_text="오메가6 (g)")
    trans_fat = models.FloatField(default=0, help_text="트랜스지방 (g)")
    caffeine = models.FloatField(default=0, help_text="카페인 (mg)")
    alcohol = models.FloatField(default=0, help_text="알코올 (g)")
    water = models.FloatField(default=0, help_text="수분 (g)")
    ash = models.FloatField(default=0, help_text="회분 (g)")
    
    # 분류
    category = models.CharField(max_length=100, blank=True, help_text="음식 카테고리")
    subcategory = models.CharField(max_length=100, blank=True, help_text="음식 하위 카테고리")
    
    # 식약처 DB 정보
    food_code = models.CharField(max_length=50, blank=True, help_text="식약처 음식 코드")
    source = models.CharField(max_length=100, default='식품의약품안전처', help_text="데이터 출처")
    
    # Gemini 임베딩 벡터 (JSON 형태로 저장)
    embedding = models.JSONField(null=True, blank=True, help_text="Gemini 임베딩 벡터")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            # 단일 컬럼 인덱스
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['food_code']),
            models.Index(fields=['source']),
            
            # 복합 인덱스 (검색 성능 향상)
            models.Index(fields=['name', 'category']),
            models.Index(fields=['category', 'subcategory']),
            
            # 영양소 범위 검색용 인덱스
            models.Index(fields=['calories']),
            models.Index(fields=['protein']),
            models.Index(fields=['carbs']),
            models.Index(fields=['fat']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_nutrition_per_gram(self):
        """1g당 영양소 정보 반환"""
        return {
            # 기본 영양소
            'calories': self.calories / 100,
            'protein': self.protein / 100,
            'carbs': self.carbs / 100,
            'fat': self.fat / 100,
            'fiber': self.fiber / 100,
            'sugar': self.sugar / 100,
            
            # 미네랄
            'sodium': self.sodium / 100,
            'potassium': self.potassium / 100,
            'calcium': self.calcium / 100,
            'iron': self.iron / 100,
            'magnesium': self.magnesium / 100,
            'phosphorus': self.phosphorus / 100,
            'zinc': self.zinc / 100,
            'copper': self.copper / 100,
            'manganese': self.manganese / 100,
            'selenium': self.selenium / 100,
            
            # 비타민
            'vitamin_a': self.vitamin_a / 100,
            'vitamin_b1': self.vitamin_b1 / 100,
            'vitamin_b2': self.vitamin_b2 / 100,
            'vitamin_b3': self.vitamin_b3 / 100,
            'vitamin_b6': self.vitamin_b6 / 100,
            'vitamin_b12': self.vitamin_b12 / 100,
            'vitamin_c': self.vitamin_c / 100,
            'vitamin_d': self.vitamin_d / 100,
            'vitamin_e': self.vitamin_e / 100,
            'vitamin_k': self.vitamin_k / 100,
            'folate': self.folate / 100,
            'choline': self.choline / 100,
            
            # 추가 비타민 및 영양소
            'beta_carotene': self.beta_carotene / 100,
            'niacin': self.niacin / 100,
            'vitamin_d2': self.vitamin_d2 / 100,
            'vitamin_d3': self.vitamin_d3 / 100,
            'vitamin_k1': self.vitamin_k1 / 100,
            'vitamin_k2': self.vitamin_k2 / 100,
            
            # 추가 미네랄
            'iodine': self.iodine / 100,
            'fluorine': self.fluorine / 100,
            'chromium': self.chromium / 100,
            'molybdenum': self.molybdenum / 100,
            'chlorine': self.chlorine / 100,
            
            # 기타 영양소
            'cholesterol': self.cholesterol / 100,
            'saturated_fat': self.saturated_fat / 100,
            'monounsaturated_fat': self.monounsaturated_fat / 100,
            'polyunsaturated_fat': self.polyunsaturated_fat / 100,
            'omega3': self.omega3 / 100,
            'omega6': self.omega6 / 100,
            'trans_fat': self.trans_fat / 100,
            'caffeine': self.caffeine / 100,
            'alcohol': self.alcohol / 100,
            'water': self.water / 100,
            'ash': self.ash / 100,
        }


class FoodLog(models.Model):
    """사용자가 섭취한 음식 기록 (AI 분석을 통해 생성됨)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_logs')
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='food_logs')
    
    # 섭취 정보
    quantity = models.FloatField(help_text="섭취량 (g)")
    meal_type = models.CharField(max_length=20, choices=[
        ('breakfast', '아침'),
        ('lunch', '점심'),
        ('dinner', '저녁'),
        ('snack', '간식'),
    ], default='lunch')
    
    # AI 분석 정보
    original_text = models.TextField(help_text="사용자가 입력한 원본 텍스트")
    ai_analysis = models.JSONField(default=dict, help_text="AI 분석 결과")
    
    # 섭취 날짜/시간
    consumed_at = models.DateTimeField(auto_now_add=True)
    consumed_date = models.DateField(auto_now_add=True)
    
    # 계산된 영양소 (섭취량 기준) - 기본 영양소
    total_calories = models.FloatField(help_text="총 칼로리")
    total_protein = models.FloatField(help_text="총 단백질 (g)")
    total_carbs = models.FloatField(help_text="총 탄수화물 (g)")
    total_fat = models.FloatField(help_text="총 지방 (g)")
    total_fiber = models.FloatField(default=0, help_text="총 식이섬유 (g)")
    total_sugar = models.FloatField(default=0, help_text="총 당분 (g)")
    
    # 미네랄
    total_sodium = models.FloatField(default=0, help_text="총 나트륨 (mg)")
    total_potassium = models.FloatField(default=0, help_text="총 칼륨 (mg)")
    total_calcium = models.FloatField(default=0, help_text="총 칼슘 (mg)")
    total_iron = models.FloatField(default=0, help_text="총 철분 (mg)")
    total_magnesium = models.FloatField(default=0, help_text="총 마그네슘 (mg)")
    total_phosphorus = models.FloatField(default=0, help_text="총 인 (mg)")
    total_zinc = models.FloatField(default=0, help_text="총 아연 (mg)")
    total_copper = models.FloatField(default=0, help_text="총 구리 (mg)")
    total_manganese = models.FloatField(default=0, help_text="총 망간 (mg)")
    total_selenium = models.FloatField(default=0, help_text="총 셀레늄 (μg)")
    
    # 비타민
    total_vitamin_a = models.FloatField(default=0, help_text="총 비타민 A (μg)")
    total_vitamin_b1 = models.FloatField(default=0, help_text="총 비타민 B1 (mg)")
    total_vitamin_b2 = models.FloatField(default=0, help_text="총 비타민 B2 (mg)")
    total_vitamin_b3 = models.FloatField(default=0, help_text="총 비타민 B3 (mg)")
    total_vitamin_b6 = models.FloatField(default=0, help_text="총 비타민 B6 (mg)")
    total_vitamin_b12 = models.FloatField(default=0, help_text="총 비타민 B12 (μg)")
    total_vitamin_c = models.FloatField(default=0, help_text="총 비타민 C (mg)")
    total_vitamin_d = models.FloatField(default=0, help_text="총 비타민 D (μg)")
    total_vitamin_e = models.FloatField(default=0, help_text="총 비타민 E (mg)")
    total_vitamin_k = models.FloatField(default=0, help_text="총 비타민 K (μg)")
    total_folate = models.FloatField(default=0, help_text="총 엽산 (μg)")
    total_choline = models.FloatField(default=0, help_text="총 콜린 (mg)")
    
    # 추가 비타민 및 영양소
    total_beta_carotene = models.FloatField(default=0, help_text="총 베타카로틴 (μg)")
    total_niacin = models.FloatField(default=0, help_text="총 나이아신 (mg)")
    total_vitamin_d2 = models.FloatField(default=0, help_text="총 비타민 D2 (μg)")
    total_vitamin_d3 = models.FloatField(default=0, help_text="총 비타민 D3 (μg)")
    total_vitamin_k1 = models.FloatField(default=0, help_text="총 비타민 K1 (μg)")
    total_vitamin_k2 = models.FloatField(default=0, help_text="총 비타민 K2 (μg)")
    
    # 추가 미네랄
    total_iodine = models.FloatField(default=0, help_text="총 요오드 (μg)")
    total_fluorine = models.FloatField(default=0, help_text="총 불소 (mg)")
    total_chromium = models.FloatField(default=0, help_text="총 크롬 (μg)")
    total_molybdenum = models.FloatField(default=0, help_text="총 몰리브덴 (μg)")
    total_chlorine = models.FloatField(default=0, help_text="총 염소 (mg)")
    
    # 기타 영양소
    total_cholesterol = models.FloatField(default=0, help_text="총 콜레스테롤 (mg)")
    total_saturated_fat = models.FloatField(default=0, help_text="총 포화지방 (g)")
    total_monounsaturated_fat = models.FloatField(default=0, help_text="총 단일불포화지방 (g)")
    total_polyunsaturated_fat = models.FloatField(default=0, help_text="총 다중불포화지방 (g)")
    total_omega3 = models.FloatField(default=0, help_text="총 오메가3 (g)")
    total_omega6 = models.FloatField(default=0, help_text="총 오메가6 (g)")
    total_trans_fat = models.FloatField(default=0, help_text="총 트랜스지방 (g)")
    total_caffeine = models.FloatField(default=0, help_text="총 카페인 (mg)")
    total_alcohol = models.FloatField(default=0, help_text="총 알코올 (g)")
    total_water = models.FloatField(default=0, help_text="총 수분 (g)")
    total_ash = models.FloatField(default=0, help_text="총 회분 (g)")
    
    class Meta:
        ordering = ['-consumed_at']
        indexes = [
            # 사용자별 날짜 검색 최적화
            models.Index(fields=['user', 'consumed_date']),
            models.Index(fields=['consumed_date']),
            
            # 사용자별 식사 유형 검색
            models.Index(fields=['user', 'meal_type']),
            models.Index(fields=['user', 'consumed_date', 'meal_type']),
            
            # 음식별 검색 최적화
            models.Index(fields=['food']),
            models.Index(fields=['user', 'food']),
            
            # 영양소 범위 검색용 인덱스
            models.Index(fields=['total_calories']),
            models.Index(fields=['total_protein']),
            models.Index(fields=['total_carbs']),
            models.Index(fields=['total_fat']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.food.name} ({self.quantity}g)"
    
    def save(self, *args, **kwargs):
        """섭취량에 따른 영양소 계산"""
        if self.food:
            nutrition_per_gram = self.food.get_nutrition_per_gram()
            
            # 기본 영양소
            self.total_calories = round(nutrition_per_gram['calories'] * self.quantity, 1)
            self.total_protein = round(nutrition_per_gram['protein'] * self.quantity, 1)
            self.total_carbs = round(nutrition_per_gram['carbs'] * self.quantity, 1)
            self.total_fat = round(nutrition_per_gram['fat'] * self.quantity, 1)
            self.total_fiber = round(nutrition_per_gram['fiber'] * self.quantity, 1)
            self.total_sugar = round(nutrition_per_gram['sugar'] * self.quantity, 1)
            
            # 미네랄
            self.total_sodium = round(nutrition_per_gram['sodium'] * self.quantity, 1)
            self.total_potassium = round(nutrition_per_gram['potassium'] * self.quantity, 1)
            self.total_calcium = round(nutrition_per_gram['calcium'] * self.quantity, 1)
            self.total_iron = round(nutrition_per_gram['iron'] * self.quantity, 1)
            self.total_magnesium = round(nutrition_per_gram['magnesium'] * self.quantity, 1)
            self.total_phosphorus = round(nutrition_per_gram['phosphorus'] * self.quantity, 1)
            self.total_zinc = round(nutrition_per_gram['zinc'] * self.quantity, 1)
            self.total_copper = round(nutrition_per_gram['copper'] * self.quantity, 1)
            self.total_manganese = round(nutrition_per_gram['manganese'] * self.quantity, 1)
            self.total_selenium = round(nutrition_per_gram['selenium'] * self.quantity, 1)
            
            # 비타민
            self.total_vitamin_a = round(nutrition_per_gram['vitamin_a'] * self.quantity, 1)
            self.total_vitamin_b1 = round(nutrition_per_gram['vitamin_b1'] * self.quantity, 1)
            self.total_vitamin_b2 = round(nutrition_per_gram['vitamin_b2'] * self.quantity, 1)
            self.total_vitamin_b3 = round(nutrition_per_gram['vitamin_b3'] * self.quantity, 1)
            self.total_vitamin_b6 = round(nutrition_per_gram['vitamin_b6'] * self.quantity, 1)
            self.total_vitamin_b12 = round(nutrition_per_gram['vitamin_b12'] * self.quantity, 1)
            self.total_vitamin_c = round(nutrition_per_gram['vitamin_c'] * self.quantity, 1)
            self.total_vitamin_d = round(nutrition_per_gram['vitamin_d'] * self.quantity, 1)
            self.total_vitamin_e = round(nutrition_per_gram['vitamin_e'] * self.quantity, 1)
            self.total_vitamin_k = round(nutrition_per_gram['vitamin_k'] * self.quantity, 1)
            self.total_folate = round(nutrition_per_gram['folate'] * self.quantity, 1)
            self.total_choline = round(nutrition_per_gram['choline'] * self.quantity, 1)
            
            # 추가 비타민 및 영양소
            self.total_beta_carotene = round(nutrition_per_gram['beta_carotene'] * self.quantity, 1)
            self.total_niacin = round(nutrition_per_gram['niacin'] * self.quantity, 1)
            self.total_vitamin_d2 = round(nutrition_per_gram['vitamin_d2'] * self.quantity, 1)
            self.total_vitamin_d3 = round(nutrition_per_gram['vitamin_d3'] * self.quantity, 1)
            self.total_vitamin_k1 = round(nutrition_per_gram['vitamin_k1'] * self.quantity, 1)
            self.total_vitamin_k2 = round(nutrition_per_gram['vitamin_k2'] * self.quantity, 1)
            
            # 추가 미네랄
            self.total_iodine = round(nutrition_per_gram['iodine'] * self.quantity, 1)
            self.total_fluorine = round(nutrition_per_gram['fluorine'] * self.quantity, 1)
            self.total_chromium = round(nutrition_per_gram['chromium'] * self.quantity, 1)
            self.total_molybdenum = round(nutrition_per_gram['molybdenum'] * self.quantity, 1)
            self.total_chlorine = round(nutrition_per_gram['chlorine'] * self.quantity, 1)
            
            # 기타 영양소
            self.total_cholesterol = round(nutrition_per_gram['cholesterol'] * self.quantity, 1)
            self.total_saturated_fat = round(nutrition_per_gram['saturated_fat'] * self.quantity, 1)
            self.total_monounsaturated_fat = round(nutrition_per_gram['monounsaturated_fat'] * self.quantity, 1)
            self.total_polyunsaturated_fat = round(nutrition_per_gram['polyunsaturated_fat'] * self.quantity, 1)
            self.total_omega3 = round(nutrition_per_gram['omega3'] * self.quantity, 1)
            self.total_omega6 = round(nutrition_per_gram['omega6'] * self.quantity, 1)
            self.total_trans_fat = round(nutrition_per_gram['trans_fat'] * self.quantity, 1)
            self.total_caffeine = round(nutrition_per_gram['caffeine'] * self.quantity, 1)
            self.total_alcohol = round(nutrition_per_gram['alcohol'] * self.quantity, 1)
            self.total_water = round(nutrition_per_gram['water'] * self.quantity, 1)
            self.total_ash = round(nutrition_per_gram['ash'] * self.quantity, 1)
            
        super().save(*args, **kwargs)

