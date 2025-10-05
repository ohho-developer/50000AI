import google.generativeai as genai
import json
import logging
from django.conf import settings
from typing import List, Dict, Any, Optional
import re
from difflib import SequenceMatcher
import numpy as np
# sentence_transformers와 sklearn은 지연 로딩으로 변경
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class GeminiAIService:
    """Google Gemini API를 사용한 AI 서비스"""
    
    def __init__(self):
        # API 키 설정
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 임베딩 모델 초기화 (한국어 지원) - 지연 로딩
        self.embedding_model = None
        self._embedding_model_loaded = False
        
        # 음식 분석을 위한 프롬프트 (다국어 지원)
        self.food_analysis_prompts = {
            'ko': """
너는 한국 음식 영양 분석 AI야. 사용자가 입력한 자연어에서 음식명, 수량, 식사유형을 추출해서 JSON 형식으로 반환해줘.

규칙:
1. 수량이 명확하지 않으면 1로 간주
2. 한국 음식명을 정확히 인식
3. 단위는 g(그램) 사용
4. 식사유형을 자동으로 분석 (breakfast, lunch, dinner, snack)
5. JSON 형식만 반환

예시 입력: "김치찌개랑 계란말이 먹었어"
예시 출력: [
    {{"food_name": "김치찌개", "quantity": 300, "meal_type": "lunch"}},
    {{"food_name": "계란말이", "quantity": 150, "meal_type": "lunch"}}
]

분석할 문장: "{user_input}"
""",
            'en': """
You are a Korean food nutrition analysis AI. Extract food names, quantities, and meal types from the user's natural language input and return them in JSON format.

Rules:
1. If quantity is not clear, assume 1
2. Recognize Korean food names accurately
3. Use g(grams) as the unit
4. Automatically analyze meal type (breakfast, lunch, dinner, snack)
5. Return ONLY JSON format

Example input: "I had kimchi stew for lunch and samgyeopsal for dinner"
Example output: [
    {{"food_name": "kimchi stew", "quantity": 300, "meal_type": "lunch"}},
    {{"food_name": "samgyeopsal", "quantity": 200, "meal_type": "dinner"}}
]

Analyze this sentence: "{user_input}"
"""
        }


    def analyze_food_text(self, user_input: str, language: str = 'ko') -> List[Dict[str, Any]]:
        """
        사용자가 입력한 자연어에서 음식 정보를 추출
        
        Args:
            user_input: 사용자가 입력한 자연어 텍스트
            language: 언어 설정 ('ko' 또는 'en')
            
        Returns:
            List[Dict]: 추출된 음식 정보 리스트
        """
        try:
            logger.info(f"AI 분석 시작: {user_input} (언어: {language})")
            
            # 언어에 따른 프롬프트 선택
            prompt_template = self.food_analysis_prompts.get(language, self.food_analysis_prompts['ko'])
            
            # 프롬프트에 사용자 입력 삽입
            prompt = prompt_template.format(user_input=user_input)
            
            # Gemini API 호출
            response = self.model.generate_content(prompt)
            
            # 응답에서 JSON 추출
            response_text = response.text.strip()
            
            # JSON 파싱 시도
            try:
                # 응답에서 JSON 부분만 추출 (```json ... ``` 형태일 수 있음)
                if "```json" in response_text:
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    json_text = response_text[start:end].strip()
                elif "```" in response_text:
                    start = response_text.find("```") + 3
                    end = response_text.find("```", start)
                    json_text = response_text[start:end].strip()
                else:
                    json_text = response_text
                
                # JSON 파싱
                food_list = json.loads(json_text)
                
                # AI가 분석한 식사 유형이 없는 경우 기본값 설정
                if isinstance(food_list, list):
                    for item in food_list:
                        if isinstance(item, dict) and 'meal_type' not in item:
                            item['meal_type'] = 'lunch'  # 기본값
                
                return food_list
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {e}")
                logger.error(f"응답 텍스트: {response_text}")
                return []
                
        except Exception as e:
            logger.error(f"음식 분석 중 오류 발생: {e}")
            return []
    

    def test_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            response = self.model.generate_content("안녕하세요. 연결 테스트입니다.")
            return response.text is not None
        except Exception as e:
            logger.error(f"API 연결 테스트 실패: {e}")
            return False
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        두 문자열 간의 유사도를 계산합니다 (0-1 범위)
        """
        # 공백 제거 및 소문자 변환
        text1 = re.sub(r'\s+', '', text1.lower())
        text2 = re.sub(r'\s+', '', text2.lower())
        
        # SequenceMatcher를 사용한 유사도 계산
        return SequenceMatcher(None, text1, text2).ratio()
    
    def extract_keywords(self, food_name: str) -> List[str]:
        """
        음식명에서 키워드를 추출합니다
        """
        # 일반적인 음식 키워드들
        keywords = []
        food_name_lower = food_name.lower()
        
        # 조리법 키워드
        cooking_methods = ['볶음', '튀김', '구이', '찜', '탕', '찌개', '국', '밥', '면', '죽', '샐러드', '샌드위치']
        for method in cooking_methods:
            if method in food_name_lower:
                keywords.append(method)
        
        # 재료 키워드
        ingredients = ['김치', '된장', '고추장', '닭', '돼지', '소고기', '생선', '새우', '게', '오징어', '두부', '콩', '쌀', '밀가루']
        for ingredient in ingredients:
            if ingredient in food_name_lower:
                keywords.append(ingredient)
        
        # 음식 유형 키워드
        food_types = ['밥', '면', '국', '찌개', '탕', '볶음', '튀김', '구이', '찜', '죽', '샐러드', '샌드위치', '피자', '햄버거']
        for food_type in food_types:
            if food_type in food_name_lower:
                keywords.append(food_type)
        
        return keywords
    
    def find_similar_food_by_string_matching(self, food_name: str, threshold: float = 0.6) -> Optional[Dict]:
        """
        문자열 유사도를 사용하여 유사한 음식을 찾습니다.
        """
        try:
            from nutrients_codi.models import Food
            
            # 모든 음식 가져오기
            all_foods = Food.objects.all()
            
            best_match = None
            best_similarity = 0
            
            # 입력 음식명의 키워드 추출
            input_keywords = self.extract_keywords(food_name)
            
            for food in all_foods:
                # 1. 전체 문자열 유사도 계산
                similarity = self.calculate_similarity(food_name, food.name)
                
                # 2. 키워드 매칭 보너스
                food_keywords = self.extract_keywords(food.name)
                keyword_bonus = 0
                if input_keywords and food_keywords:
                    common_keywords = set(input_keywords) & set(food_keywords)
                    if common_keywords:
                        keyword_bonus = len(common_keywords) * 0.1
                
                # 3. 최종 유사도 계산
                final_similarity = min(similarity + keyword_bonus, 1.0)
                
                if final_similarity > best_similarity and final_similarity >= threshold:
                    best_similarity = final_similarity
                    best_match = {
                        'food': food,
                        'similarity': final_similarity,
                        'match_type': 'string_matching'
                    }
            
            return best_match
            
        except Exception as e:
            logger.error(f"문자열 유사도 기반 음식 검색 중 오류 발생: {e}")
            return None
    
    def _load_embedding_model(self):
        """임베딩 모델을 지연 로딩합니다."""
        if self._embedding_model_loaded:
            return
        
        try:
            # 지연 로딩으로 모듈 import
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')
            self._embedding_model_loaded = True
            logger.info("한국어 임베딩 모델 로드 완료")
        except ImportError as e:
            logger.warning(f"sentence_transformers 모듈을 찾을 수 없습니다: {e}")
            self.embedding_model = None
            self._embedding_model_loaded = True
        except Exception as e:
            logger.warning(f"임베딩 모델 로드 실패: {e}")
            self.embedding_model = None
            self._embedding_model_loaded = True  # 실패했어도 다시 시도하지 않음

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        텍스트의 임베딩 벡터를 생성합니다.
        """
        try:
            # 지연 로딩
            self._load_embedding_model()
            
            if not self.embedding_model:
                return None
            
            # 임베딩 생성
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"임베딩 생성 중 오류 발생: {e}")
            return None
    
    def find_similar_food_by_embedding(self, food_name: str, threshold: float = 0.7) -> Optional[Dict]:
        """
        임베딩을 사용하여 유사한 음식을 찾습니다.
        """
        try:
            from nutrients_codi.models import Food
            
            # 지연 로딩
            self._load_embedding_model()
            
            if not self.embedding_model:
                logger.info("임베딩 모델이 없어 임베딩 검색을 건너뜁니다.")
                return None
            
            # 입력 음식명의 임베딩 생성
            input_embedding = self.get_embedding(food_name)
            if not input_embedding:
                return None
            
            # 데이터베이스에서 임베딩이 있는 음식들 가져오기
            foods_with_embeddings = Food.objects.exclude(embedding__isnull=True)
            
            if not foods_with_embeddings.exists():
                return None
            
            best_match = None
            best_similarity = 0
            
            for food in foods_with_embeddings:
                if food.embedding:
                    try:
                        # 코사인 유사도 계산 (지연 로딩)
                        from sklearn.metrics.pairwise import cosine_similarity
                        similarity = cosine_similarity(
                            [input_embedding], 
                            [food.embedding]
                        )[0][0]
                        
                        if similarity > best_similarity and similarity >= threshold:
                            best_similarity = similarity
                            best_match = {
                                'food': food,
                                'similarity': similarity,
                                'match_type': 'embedding'
                            }
                    except Exception as e:
                        logger.warning(f"음식 {food.name}의 임베딩 계산 실패: {e}")
                        continue
            
            return best_match
            
        except Exception as e:
            logger.warning(f"임베딩 기반 유사 음식 검색 중 오류 발생: {e}")
            return None
    
    def get_nutrition_from_llm(self, food_name: str) -> Optional[Dict]:
        """
        Gemini LLM을 사용하여 음식의 영양성분을 추출합니다.
        """
        try:
            prompt = f"""
당신은 영양 전문가입니다. 다음 음식의 영양성분을 JSON 형태로 제공해주세요.

음식명: {food_name}

다음 형식으로 응답해주세요:
{{
    "name": "{food_name}",
    "calories": 100,
    "protein": 10.0,
    "carbs": 20.0,
    "fat": 5.0,
    "fiber": 2.0,
    "sugar": 3.0,
    "sodium": 500.0,
    "potassium": 300.0,
    "calcium": 50.0,
    "iron": 2.0,
    "magnesium": 25.0,
    "phosphorus": 100.0,
    "zinc": 1.0,
    "copper": 0.1,
    "manganese": 0.5,
    "selenium": 10.0,
    "vitamin_a": 50.0,
    "vitamin_b1": 0.1,
    "vitamin_b2": 0.1,
    "vitamin_b3": 1.0,
    "vitamin_b6": 0.2,
    "vitamin_b12": 1.0,
    "vitamin_c": 10.0,
    "vitamin_d": 2.0,
    "vitamin_e": 1.0,
    "vitamin_k": 5.0,
    "folate": 20.0,
    "choline": 50.0,
    "cholesterol": 0.0,
    "saturated_fat": 1.0,
    "monounsaturated_fat": 2.0,
    "polyunsaturated_fat": 1.0,
    "omega3": 0.1,
    "omega6": 0.5,
    "trans_fat": 0.0,
    "caffeine": 0.0,
    "alcohol": 0.0,
    "water": 70.0,
    "ash": 1.0
}}

단위:
- 칼로리: kcal
- 단백질, 탄수화물, 지방, 섬유질, 당분: g
- 나트륨, 칼륨, 칼슘, 철분, 마그네슘, 인, 아연, 구리, 망간, 셀레늄: mg
- 비타민 A, D, K, 엽산, 콜린: μg
- 비타민 B1, B2, B3, B6, C, E: mg
- 비타민 B12: μg
- 콜레스테롤: mg
- 포화지방, 단일불포화지방, 다중불포화지방, 오메가3, 오메가6, 트랜스지방: g
- 카페인: mg
- 알코올: g
- 수분, 회분: g

정확하지 않은 값은 0으로 설정해주세요. 100g 기준으로 계산해주세요.
"""
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSON 파싱 시도
            try:
                # 응답에서 JSON 부분만 추출
                if "```json" in response_text:
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    json_text = response_text[start:end].strip()
                elif "```" in response_text:
                    start = response_text.find("```") + 3
                    end = response_text.find("```", start)
                    json_text = response_text[start:end].strip()
                else:
                    json_text = response_text
                
                # JSON 파싱
                nutrition_data = json.loads(json_text)
                
                # 기본값 설정
                nutrition_data.setdefault('name', food_name)
                nutrition_data.setdefault('category', 'LLM 생성')
                nutrition_data.setdefault('subcategory', '')
                nutrition_data.setdefault('food_code', '')
                nutrition_data.setdefault('source', 'Gemini LLM')
                
                return nutrition_data
                
            except json.JSONDecodeError as e:
                logger.error(f"LLM 응답 JSON 파싱 오류: {e}")
                logger.error(f"응답 텍스트: {response_text}")
                return None
                
        except Exception as e:
            logger.error(f"LLM 영양성분 추출 중 오류 발생: {e}")
            return None
    
    def create_food_from_llm(self, food_name: str) -> Optional[Dict]:
        """
        LLM으로 영양성분을 추출하여 새로운 Food 객체를 생성합니다.
        """
        try:
            from nutrients_codi.models import Food
            
            # LLM으로 영양성분 추출
            nutrition_data = self.get_nutrition_from_llm(food_name)
            if not nutrition_data:
                return None
            
            # Food 객체 생성
            food = Food.objects.create(**nutrition_data)
            
            return {
                'food': food,
                'similarity': 1.0,
                'match_type': 'llm_generated'
            }
            
        except Exception as e:
            logger.error(f"LLM 기반 Food 생성 중 오류 발생: {e}")
            return None
