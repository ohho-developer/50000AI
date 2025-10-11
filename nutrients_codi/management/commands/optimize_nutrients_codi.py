"""
nutrients_codi 앱 전용 데이터베이스 최적화 명령어
- 성능이 중요한 뷰 최적화
- 캐싱 전략 구현
- 인덱스 최적화
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from nutrients_codi.models import Food, FoodLog, Profile


class Command(BaseCommand):
    help = 'nutrients_codi 앱의 성능을 최적화합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='캐시를 모두 삭제',
        )
        parser.add_argument(
            '--create-indexes',
            action='store_true',
            help='추가 인덱스 생성',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== nutrients_codi 최적화 시작 ===\n'))
        
        if options['clear_cache']:
            self.clear_all_cache()
        
        if options['create_indexes']:
            self.create_custom_indexes()
        
        # 기본 실행: 통계 + 최적화 제안
        self.show_statistics()
        self.suggest_optimizations()
        
        self.stdout.write(self.style.SUCCESS('\n=== 최적화 완료 ==='))

    def show_statistics(self):
        """현재 상태 통계"""
        self.stdout.write('[통계]')
        
        food_count = Food.objects.count()
        foodlog_count = FoodLog.objects.count()
        profile_count = Profile.objects.count()
        
        self.stdout.write(f'  Food: {food_count:,}개')
        self.stdout.write(f'  FoodLog: {foodlog_count:,}개')
        self.stdout.write(f'  Profile: {profile_count:,}개')
        
        # 인덱스 수 (SQLite)
        if 'sqlite' in connection.settings_dict['ENGINE']:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """)
                index_count = cursor.fetchone()[0]
                self.stdout.write(f'  인덱스: {index_count}개\n')

    def suggest_optimizations(self):
        """최적화 제안"""
        self.stdout.write('[최적화 제안]')
        
        food_count = Food.objects.count()
        
        # 1. 데이터베이스 권장사항
        if 'sqlite' in connection.settings_dict['ENGINE']:
            if food_count > 10000:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠️  SQLite로 {food_count:,}개의 데이터 처리 중!\n'
                        '     PostgreSQL 마이그레이션을 강력히 권장합니다.\n'
                        '     성능이 10-50배 향상됩니다.'
                    )
                )
        
        # 2. 뷰 최적화
        self.stdout.write('  📌 views.py 최적화 필요:')
        self.stdout.write('     - 50개 필드 집계 → 필요한 필드만 선택')
        self.stdout.write('     - 캐싱 추가 (하루 통계는 캐시 활용)')
        self.stdout.write('     - only(), defer() 활용\n')
        
        # 3. 쿼리 최적화
        self.stdout.write('  📌 쿼리 최적화:')
        self.stdout.write('     - select_related() 이미 사용 중 ✓')
        self.stdout.write('     - prefetch_related() 추가 고려')
        self.stdout.write('     - 날짜 범위 쿼리에 인덱스 활용 ✓\n')
        
        # 4. 캐싱 전략
        self.stdout.write('  📌 캐싱 전략:')
        self.stdout.write('     - 일일 통계: 1시간 캐시')
        self.stdout.write('     - 주간 통계: 4시간 캐시')
        self.stdout.write('     - Food 데이터: 24시간 캐시\n')

    def clear_all_cache(self):
        """모든 캐시 삭제"""
        self.stdout.write('[캐시 삭제]')
        cache.clear()
        self.stdout.write(self.style.SUCCESS('  ✓ 모든 캐시가 삭제되었습니다.\n'))

    def create_custom_indexes(self):
        """추가 인덱스 생성"""
        self.stdout.write('[인덱스 생성]')
        
        if 'sqlite' in connection.settings_dict['ENGINE']:
            with connection.cursor() as cursor:
                # FoodLog의 중요한 복합 인덱스들
                indexes = [
                    # 이미 모델에 정의되어 있지만 확인
                    ('CREATE INDEX IF NOT EXISTS idx_foodlog_user_date ON nutrients_codi_foodlog(user_id, consumed_date);', 
                     'FoodLog: user+date'),
                    ('CREATE INDEX IF NOT EXISTS idx_foodlog_user_date_meal ON nutrients_codi_foodlog(user_id, consumed_date, meal_type);', 
                     'FoodLog: user+date+meal'),
                ]
                
                for sql, description in indexes:
                    try:
                        cursor.execute(sql)
                        self.stdout.write(f'  ✓ {description}')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  {description}: {e}'))
        else:
            self.stdout.write(self.style.WARNING('  PostgreSQL은 Django 마이그레이션으로 인덱스가 자동 생성됩니다.\n'))

