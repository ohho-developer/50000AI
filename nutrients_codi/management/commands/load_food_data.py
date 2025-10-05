from django.core.management.base import BaseCommand
from nutrients_codi.models import Food
import pandas as pd
import os
from django.conf import settings
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor
import threading


class Command(BaseCommand):
    help = 'Excel 파일에서 음식 데이터를 로드합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='로드할 Excel 파일 경로'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=1000,
            help='로드할 최대 데이터 수 (기본값: 1000)'
        )

    def handle(self, *args, **options):
        # 기본 파일 경로들
        default_files = [
            'data1.csv',
            'data2.csv'
        ]
        
        file_path = options.get('file')
        limit = options.get('limit', 1000)
        
        if not file_path:
            # 기본 파일들 중 존재하는 것 찾기
            for filename in default_files:
                if os.path.exists(filename):
                    file_path = filename
                    break
        
        if not file_path or not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR('Excel 파일을 찾을 수 없습니다.')
            )
            return

        self.stdout.write(f'파일 로딩 중: {file_path}')
        
        try:
            # 파일 확장자에 따라 적절한 엔진 선택
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path)
            
            self.stdout.write(f'총 {len(df)}개의 데이터 발견')
            self.stdout.write(f'컬럼: {list(df.columns)}')
            
            # 초대용량 배치 처리로 최적화
            created_count = 0
            error_count = 0
            batch_size = 5000  # 대용량 배치 크기
            food_objects = []
            
            for index, row in df.head(limit).iterrows():
                try:
                    # 컬럼명 매핑 (파일에 따라 조정 필요)
                    food_data = self.map_columns(row, df.columns)
                    
                    if not food_data:
                        error_count += 1
                        continue
                    
                    # Food 객체 생성
                    food = Food(**food_data)
                    food_objects.append(food)
                    
                    # 배치 크기에 도달하면 일괄 저장
                    if len(food_objects) >= batch_size:
                        with transaction.atomic():
                            Food.objects.bulk_create(food_objects, ignore_conflicts=True)
                        created_count += len(food_objects)
                        food_objects = []
                        self.stdout.write(f'처리 완료: {created_count}개')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'행 {index} 처리 중 오류: {str(e)}')
                    )
                    error_count += 1
                    continue
            
            # 남은 데이터 처리
            if food_objects:
                with transaction.atomic():
                    Food.objects.bulk_create(food_objects, ignore_conflicts=True)
                created_count += len(food_objects)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'완료: {created_count}개 생성, {error_count}개 오류'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'파일 읽기 오류: {str(e)}')
            )

    def map_columns(self, row, columns):
        """CSV/Excel 컬럼을 Food 모델 필드로 매핑 (인덱스 기반)"""
        food_data = {}
        
        # 컬럼 인덱스 기반 매핑 (data1.csv, data2.xlsx 공통)
        # CSV 첫 줄 기준으로 인덱스 매핑
        column_mapping = {
            # 기본 정보 (인덱스 0-16)
            1: 'name',           # 식품명
            0: 'food_code',      # 식품코드
            8: 'category',       # 대표식품코드
            9: 'category',       # 대표식품명
            10: 'subcategory',   # 식품중분류코드
            11: 'subcategory',   # 식품중분류명
            12: 'subcategory',   # 식품소분류코드
            13: 'subcategory',   # 식품소분류명
            14: 'subcategory',   # 식품세분류코드
            15: 'subcategory',   # 식품세분류명
            
            # 기본 영양소 (인덱스 17-25)
            17: 'calories',      # 에너지(kcal)
            19: 'protein',       # 단백질(g)
            20: 'fat',           # 지방(g)
            21: 'ash',           # 회분(g)
            22: 'carbs',         # 탄수화물(g)
            23: 'sugar',         # 당류(g)
            24: 'fiber',         # 식이섬유(g)
            25: 'calcium',       # 칼슘(mg)
            26: 'iron',          # 철(mg)
            27: 'phosphorus',    # 인(mg)
            28: 'potassium',     # 칼륨(mg)
            29: 'sodium',        # 나트륨(mg)
            
            # 비타민 (인덱스 30-52)
            30: 'vitamin_a',     # 비타민A(μg RAE)
            31: 'beta_carotene', # 레티놀(μg)
            32: 'beta_carotene', # 베타카로틴(μg)
            33: 'vitamin_b1',    # 티아민(mg)
            34: 'vitamin_b2',    # 리보플라빈(mg)
            35: 'vitamin_b3',    # 니아신(mg)
            36: 'vitamin_c',     # 비타민C(mg)
            37: 'vitamin_d',     # 비타민D(μg)
            38: 'cholesterol',   # 콜레스테롤(mg)
            39: 'saturated_fat', # 포화지방산(g)
            40: 'trans_fat',     # 트랜스지방산(g)
            44: 'vitamin_b6',    # 비타민B6(mg)
            45: 'vitamin_b12',   # 비타민B12(μg)
            46: 'folate',        # 엽산(μg DFE)
            47: 'choline',       # 콜린(mg)
            49: 'vitamin_d2',    # 비타민D2(μg)
            50: 'vitamin_d3',    # 비타민D3(μg)
            51: 'vitamin_e',     # 비타민E(mg α-TE)
            60: 'vitamin_k',     # 비타민K(μg)
            61: 'vitamin_k1',    # 비타민K1(μg)
            62: 'vitamin_k2',    # 비타민K2(μg)
            
            # 지방산 (인덱스 53-101)
            53: 'monounsaturated_fat', # 단일불포화지방산(g)
            54: 'polyunsaturated_fat', # 다중불포화지방산(g)
            99: 'omega3',        # 오메가3지방산(g)
            100: 'omega6',       # 오메가6지방산(g)
            
            # 미네랄 (인덱스 102-150)
            102: 'zinc',         # 아연(mg)
            103: 'copper',       # 구리(mg)
            104: 'manganese',    # 망간(mg)
            105: 'molybdenum',   # 몰리브덴(μg)
            106: 'fluorine',     # 불소(mg)
            107: 'selenium',     # 셀레늄(μg)
            108: 'chlorine',     # 염소(mg)
            109: 'iodine',       # 요오드(μg)
            110: 'chromium',     # 크롬(μg)
        }
        
        # 컬럼 인덱스 기반 매핑
        for idx, (col, value) in enumerate(zip(columns, row)):
            if idx in column_mapping and pd.notna(value):
                field = column_mapping[idx]
                try:
                    # 숫자 필드 처리
                    numeric_fields = [
                        'calories', 'protein', 'fat', 'ash', 'carbs', 'sugar', 'fiber',
                        'calcium', 'iron', 'phosphorus', 'potassium', 'sodium',
                        'vitamin_a', 'beta_carotene', 'vitamin_b1', 'vitamin_b2', 'vitamin_b3',
                        'vitamin_b6', 'vitamin_b12', 'vitamin_c', 'vitamin_d', 'vitamin_e',
                        'vitamin_k', 'vitamin_k1', 'vitamin_k2', 'folate', 'choline',
                        'cholesterol', 'saturated_fat', 'trans_fat', 'monounsaturated_fat',
                        'polyunsaturated_fat', 'omega3', 'omega6',
                        'zinc', 'copper', 'manganese', 'molybdenum', 'fluorine', 'selenium',
                        'chlorine', 'iodine', 'chromium'
                    ]
                    
                    if field in numeric_fields:
                        food_data[field] = float(value)
                    else:
                        food_data[field] = str(value).strip()
                except (ValueError, TypeError):
                    continue
        
        # 필수 필드 확인
        if 'name' not in food_data:
            return None
            
        # 기본값 설정
        # 기본 영양소
        food_data.setdefault('calories', 0)
        food_data.setdefault('protein', 0)
        food_data.setdefault('carbs', 0)
        food_data.setdefault('fat', 0)
        food_data.setdefault('fiber', 0)
        food_data.setdefault('sugar', 0)
        food_data.setdefault('sodium', 0)
        
        # 미네랄
        food_data.setdefault('potassium', 0)
        food_data.setdefault('calcium', 0)
        food_data.setdefault('iron', 0)
        food_data.setdefault('magnesium', 0)
        food_data.setdefault('phosphorus', 0)
        food_data.setdefault('zinc', 0)
        food_data.setdefault('copper', 0)
        food_data.setdefault('manganese', 0)
        food_data.setdefault('selenium', 0)
        
        # 비타민
        food_data.setdefault('vitamin_a', 0)
        food_data.setdefault('vitamin_b1', 0)
        food_data.setdefault('vitamin_b2', 0)
        food_data.setdefault('vitamin_b3', 0)
        food_data.setdefault('vitamin_b6', 0)
        food_data.setdefault('vitamin_b12', 0)
        food_data.setdefault('vitamin_c', 0)
        food_data.setdefault('vitamin_d', 0)
        food_data.setdefault('vitamin_e', 0)
        food_data.setdefault('vitamin_k', 0)
        food_data.setdefault('folate', 0)
        food_data.setdefault('choline', 0)
        
        # 기타 영양소
        food_data.setdefault('cholesterol', 0)
        food_data.setdefault('saturated_fat', 0)
        food_data.setdefault('monounsaturated_fat', 0)
        food_data.setdefault('polyunsaturated_fat', 0)
        food_data.setdefault('omega3', 0)
        food_data.setdefault('omega6', 0)
        food_data.setdefault('trans_fat', 0)
        food_data.setdefault('caffeine', 0)
        food_data.setdefault('alcohol', 0)
        food_data.setdefault('water', 0)
        food_data.setdefault('ash', 0)
        
        # 분류 정보
        food_data.setdefault('category', '기타')
        food_data.setdefault('source', '식품의약품안전처')
        
        return food_data
