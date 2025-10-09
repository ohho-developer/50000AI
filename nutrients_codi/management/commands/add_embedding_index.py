from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'embedding 필드에 NULL 체크 최적화를 위한 부분 인덱스를 추가합니다'

    def handle(self, *args, **options):
        self.stdout.write('[INFO] embedding 필드 인덱스 추가 중...')
        
        try:
            with connection.cursor() as cursor:
                # embedding이 NULL인 행에 대한 부분 인덱스 생성
                # 이렇게 하면 embedding__isnull=True 필터가 엄청 빨라집니다!
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS nutrients_codi_food_embedding_null_idx 
                    ON nutrients_codi_food (id) 
                    WHERE embedding IS NULL;
                """)
                
                self.stdout.write(
                    self.style.SUCCESS('[OK] embedding NULL 인덱스 생성 완료!')
                )
                
                # 인덱스 확인
                cursor.execute("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'nutrients_codi_food' 
                    AND indexname LIKE '%embedding%';
                """)
                
                results = cursor.fetchall()
                if results:
                    self.stdout.write('[INFO] 생성된 인덱스:')
                    for idx_name, idx_def in results:
                        self.stdout.write(f'  - {idx_name}')
                
                # 통계 업데이트
                cursor.execute("ANALYZE nutrients_codi_food;")
                self.stdout.write(self.style.SUCCESS('[OK] 테이블 통계 업데이트 완료!'))
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'[ERROR] 인덱스 추가 실패: {e}')
            )
            raise
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n[COMPLETE] 최적화 완료! '
                'embedding__isnull=True 필터가 이제 훨씬 빨라집니다.'
            )
        )

