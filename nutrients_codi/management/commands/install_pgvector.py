from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'PostgreSQL에 pgvector 확장을 설치합니다'

    def handle(self, *args, **options):
        self.stdout.write('pgvector 확장 설치 중...')
        
        try:
            with connection.cursor() as cursor:
                # pgvector 확장 설치
                cursor.execute('CREATE EXTENSION IF NOT EXISTS vector;')
                self.stdout.write(
                    self.style.SUCCESS('✓ pgvector 확장이 성공적으로 설치되었습니다!')
                )
                
                # 설치 확인
                cursor.execute(
                    "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
                )
                result = cursor.fetchone()
                
                if result:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 설치된 버전: {result[1]}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠ 확장이 설치되었지만 확인할 수 없습니다.')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ pgvector 확장 설치 실패: {e}')
            )
            self.stdout.write(
                self.style.WARNING(
                    '\n수동 설치 방법:\n'
                    '1. PostgreSQL 서버에 pgvector를 설치하세요\n'
                    '2. psql 또는 pgAdmin으로 접속하여 다음 명령 실행:\n'
                    '   CREATE EXTENSION vector;\n'
                )
            )
            raise

