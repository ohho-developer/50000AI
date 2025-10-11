"""
현재 사용 중인 데이터베이스 정보 확인
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '현재 사용 중인 데이터베이스 정보를 표시합니다.'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('현재 데이터베이스 설정'))
        self.stdout.write('=' * 60)
        
        engine = connection.settings_dict['ENGINE']
        name = connection.settings_dict['NAME']
        host = connection.settings_dict.get('HOST', 'N/A')
        port = connection.settings_dict.get('PORT', 'N/A')
        user = connection.settings_dict.get('USER', 'N/A')
        
        self.stdout.write(f'Engine: {engine}')
        self.stdout.write(f'Name: {name}')
        self.stdout.write(f'Host: {host}')
        self.stdout.write(f'Port: {port}')
        self.stdout.write(f'User: {user}')
        
        # 실제 연결 테스트
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('연결 테스트')
        self.stdout.write('=' * 60)
        
        try:
            with connection.cursor() as cursor:
                if 'postgresql' in engine:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    self.stdout.write(self.style.SUCCESS(f'✓ PostgreSQL 연결 성공'))
                    self.stdout.write(f'  버전: {version}')
                elif 'sqlite' in engine:
                    cursor.execute("SELECT sqlite_version();")
                    version = cursor.fetchone()[0]
                    self.stdout.write(self.style.SUCCESS(f'✓ SQLite 연결 성공'))
                    self.stdout.write(f'  버전: {version}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ 연결 실패: {e}'))
        
        self.stdout.write('=' * 60)

