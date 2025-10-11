"""
PostgreSQL 전용 최적화 명령어
- VACUUM ANALYZE 실행
- 인덱스 상태 확인
- 쿼리 성능 분석
"""

from django.core.management.base import BaseCommand
from django.db import connection
from nutrients_codi.models import Food, FoodLog, Profile


class Command(BaseCommand):
    help = 'PostgreSQL 데이터베이스를 최적화합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='VACUUM ANALYZE 실행',
        )
        parser.add_argument(
            '--reindex',
            action='store_true',
            help='인덱스 재생성',
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('PostgreSQL 최적화')
        self.stdout.write('=' * 60)
        
        # 현재 상태 확인
        self.show_statistics()
        
        if options['vacuum']:
            self.vacuum_analyze()
        
        if options['reindex']:
            self.reindex_tables()
        
        # 기본 실행: 인덱스 사용률 확인 + 제안
        self.check_index_usage()
        self.suggest_optimizations()
        
        self.stdout.write('=' * 60)

    def show_statistics(self):
        """테이블 통계"""
        self.stdout.write('\n[테이블 통계]')
        
        food_count = Food.objects.count()
        foodlog_count = FoodLog.objects.count()
        profile_count = Profile.objects.count()
        
        self.stdout.write(f'  Food: {food_count:,}개')
        self.stdout.write(f'  FoodLog: {foodlog_count:,}개')
        self.stdout.write(f'  Profile: {profile_count:,}개')

    def check_index_usage(self):
        """인덱스 사용률 확인"""
        self.stdout.write('\n[인덱스 사용률]')
        
        with connection.cursor() as cursor:
            try:
                # 인덱스 크기 및 사용 통계
                cursor.execute("""
                    SELECT 
                        schemaname,
                        relname as tablename,
                        indexrelname as indexname,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                        idx_scan as scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    WHERE schemaname = 'public'
                    AND relname LIKE 'nutrients_codi%'
                    ORDER BY idx_scan DESC
                    LIMIT 15;
                """)
                
                results = cursor.fetchall()
                
                if results:
                    self.stdout.write(f'  상위 15개 인덱스:')
                    for row in results:
                        schema, table, index, size, scans, reads, fetches = row
                        table_short = table.replace('nutrients_codi_', '')
                        self.stdout.write(
                            f'    {table_short}.{index}: '
                            f'{size}, {scans:,} scans'
                        )
                else:
                    self.stdout.write('  인덱스 통계를 가져올 수 없습니다.')
                    
            except Exception as e:
                self.stdout.write(f'  오류: {e}')

    def vacuum_analyze(self):
        """VACUUM ANALYZE 실행"""
        self.stdout.write('\n[VACUUM ANALYZE 실행]')
        
        tables = [
            'nutrients_codi_food',
            'nutrients_codi_foodlog',
            'nutrients_codi_profile',
            'nutrients_codi_communitypost',
            'nutrients_codi_communitycomment'
        ]
        
        with connection.cursor() as cursor:
            for table in tables:
                try:
                    self.stdout.write(f'  {table}... ', ending='')
                    cursor.execute(f'VACUUM ANALYZE {table};')
                    self.stdout.write('OK')
                except Exception as e:
                    self.stdout.write(f'ERROR: {e}')

    def reindex_tables(self):
        """인덱스 재생성"""
        self.stdout.write('\n[인덱스 재생성]')
        
        tables = [
            'nutrients_codi_food',
            'nutrients_codi_foodlog',
        ]
        
        with connection.cursor() as cursor:
            for table in tables:
                try:
                    self.stdout.write(f'  {table}... ', ending='')
                    cursor.execute(f'REINDEX TABLE {table};')
                    self.stdout.write('OK')
                except Exception as e:
                    self.stdout.write(f'ERROR: {e}')

    def suggest_optimizations(self):
        """최적화 제안"""
        self.stdout.write('\n[최적화 제안]')
        
        self.stdout.write('  1. 정기적 VACUUM ANALYZE')
        self.stdout.write('     python manage.py optimize_postgres --vacuum')
        self.stdout.write('')
        self.stdout.write('  2. 캐시 활용 (이미 적용됨)')
        self.stdout.write('     - 오늘 영양소: 1시간 캐시')
        self.stdout.write('     - 과거 데이터: 24시간 캐시')
        self.stdout.write('')
        self.stdout.write('  3. 연결 풀 설정 확인')
        self.stdout.write('     settings.py에 CONN_MAX_AGE 설정 권장')
        self.stdout.write('')
        self.stdout.write('  4. pgvector 인덱스 확인')
        self.stdout.write('     HNSW 인덱스가 생성되어 있는지 확인')

