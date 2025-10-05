"""
데이터베이스 최적화 명령어
- 인덱스 생성
- 통계 정보 업데이트
- 쿼리 성능 분석
"""

import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count, Avg
from nutrients_codi.models import Food, FoodLog, Profile


class Command(BaseCommand):
    help = '데이터베이스 최적화를 수행합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='데이터베이스 통계 분석만 수행',
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='PostgreSQL VACUUM 수행',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('데이터베이스 최적화를 시작합니다...'))
        
        start_time = time.time()
        
        if options['analyze']:
            self.analyze_database()
        elif options['vacuum']:
            self.vacuum_database()
        else:
            self.full_optimization()
        
        end_time = time.time()
        self.stdout.write(
            self.style.SUCCESS(f'최적화 완료! 소요 시간: {end_time - start_time:.2f}초')
        )

    def analyze_database(self):
        """데이터베이스 통계 분석"""
        self.stdout.write('[INFO] 데이터베이스 통계 분석 중...')
        
        # 모델별 데이터 수
        food_count = Food.objects.count()
        foodlog_count = FoodLog.objects.count()
        profile_count = Profile.objects.count()
        
        self.stdout.write(f'  - Food: {food_count:,}개')
        self.stdout.write(f'  - FoodLog: {foodlog_count:,}개')
        self.stdout.write(f'  - Profile: {profile_count:,}개')
        
        # 임베딩 데이터 통계
        embedding_count = Food.objects.filter(embedding__isnull=False).count()
        self.stdout.write(f'  - 임베딩 데이터: {embedding_count:,}개 ({embedding_count/food_count*100:.1f}%)')
        
        # 카테고리별 통계
        self.stdout.write('\n[INFO] 카테고리별 음식 수:')
        categories = Food.objects.values('category').annotate(count=Count('id')).order_by('-count')[:10]
        for cat in categories:
            self.stdout.write(f'  - {cat["category"]}: {cat["count"]:,}개')
        
        # 영양소 통계
        self.stdout.write('\n[INFO] 영양소 통계:')
        avg_nutrition = Food.objects.aggregate(
            avg_calories=Avg('calories'),
            avg_protein=Avg('protein'),
            avg_carbs=Avg('carbs'),
            avg_fat=Avg('fat')
        )
        
        for key, value in avg_nutrition.items():
            if value:
                self.stdout.write(f'  - {key.replace("avg_", "").title()}: {value:.1f}')
        
        # 인덱스 사용률 분석
        self.analyze_index_usage()

    def analyze_index_usage(self):
        """데이터베이스 인덱스 사용률 분석"""
        self.stdout.write('\n[INFO] 인덱스 사용률 분석:')
        
        # SQLite인 경우 인덱스 정보 조회
        if 'sqlite' in connection.settings_dict['ENGINE']:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
                indexes = cursor.fetchall()
                
                self.stdout.write(f'  - 생성된 인덱스 수: {len(indexes)}개')
                for idx in indexes[:10]:  # 상위 10개만 표시
                    self.stdout.write(f'    * {idx[0]}')
        else:
            # PostgreSQL인 경우
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            indexname,
                            idx_tup_read,
                            idx_tup_fetch
                        FROM pg_stat_user_indexes 
                        WHERE schemaname = 'public'
                        ORDER BY idx_tup_read DESC
                        LIMIT 10;
                    """)
                    
                    results = cursor.fetchall()
                    for row in results:
                        schema, table, index, reads, fetches = row
                        self.stdout.write(f'  - {table}.{index}: {reads:,} reads, {fetches:,} fetches')
            except Exception as e:
                self.stdout.write(f'  - 인덱스 통계 조회 실패: {e}')

    def vacuum_database(self):
        """데이터베이스 최적화 수행"""
        self.stdout.write('[INFO] 데이터베이스 최적화 수행 중...')
        
        with connection.cursor() as cursor:
            if 'sqlite' in connection.settings_dict['ENGINE']:
                # SQLite인 경우 VACUUM 수행
                cursor.execute("VACUUM;")
                self.stdout.write(self.style.SUCCESS('SQLite VACUUM 완료'))
                
                # SQLite는 ANALYZE 자동 수행
                self.stdout.write('  - SQLite는 자동으로 통계를 업데이트합니다')
            else:
                # PostgreSQL인 경우 VACUUM ANALYZE 수행
                cursor.execute("VACUUM ANALYZE;")
                self.stdout.write(self.style.SUCCESS('PostgreSQL VACUUM ANALYZE 완료'))
                
                # 테이블별 통계 업데이트
                tables = ['nutrients_codi_food', 'nutrients_codi_foodlog', 'nutrients_codi_profile', 'nutrients_codi_dailyreport']
                for table in tables:
                    cursor.execute(f"ANALYZE {table};")
                    self.stdout.write(f'  - {table} 통계 업데이트 완료')

    def full_optimization(self):
        """전체 최적화 수행"""
        # 1. 통계 분석
        self.analyze_database()
        
        # 2. VACUUM 수행
        self.vacuum_database()
        
        # 3. 추가 최적화 제안
        self.suggest_optimizations()

    def suggest_optimizations(self):
        """추가 최적화 제안"""
        self.stdout.write('\n[INFO] 추가 최적화 제안:')
        
        # 임베딩 데이터 부족 체크
        food_count = Food.objects.count()
        embedding_count = Food.objects.filter(embedding__isnull=False).count()
        
        if embedding_count < food_count * 0.8:
            self.stdout.write(
                self.style.WARNING(
                    f'  - 임베딩 데이터가 부족합니다 ({embedding_count}/{food_count}). '
                    'python manage.py generate_embeddings --limit 1000 실행을 권장합니다.'
                )
            )
        
        # 인덱스 최적화 제안
        self.stdout.write('  - 인덱스 최적화:')
        self.stdout.write('    * Food.name: 음식명 검색 최적화')
        self.stdout.write('    * FoodLog.user+consumed_date: 사용자별 날짜 검색 최적화')
        self.stdout.write('    * FoodLog.user+meal_type: 식사 유형별 검색 최적화')
        
        # 쿼리 최적화 제안
        self.stdout.write('  - 쿼리 최적화:')
        self.stdout.write('    * select_related() 사용으로 N+1 쿼리 방지')
        self.stdout.write('    * aggregate() 사용으로 Python 레벨 계산 최소화')
        self.stdout.write('    * 인덱스 활용한 필터링 최적화')
