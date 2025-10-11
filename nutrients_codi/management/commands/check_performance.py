"""
성능 테스트 및 벤치마크
"""

import time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from nutrients_codi.models import FoodLog
from nutrients_codi.utils_optimized import get_today_nutrition_cached
from datetime import date


class Command(BaseCommand):
    help = '최적화된 쿼리 성능을 테스트합니다.'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('성능 테스트')
        self.stdout.write('=' * 60)
        
        # 테스트할 사용자 찾기
        users = User.objects.filter(food_logs__isnull=False).distinct()[:3]
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('테스트할 사용자가 없습니다.'))
            return
        
        self.stdout.write(f'\n테스트 사용자: {users.count()}명')
        
        for user in users:
            self.stdout.write(f'\n[사용자: {user.username}]')
            
            # 1. 캐시 없이 조회 (첫 번째 호출)
            start = time.time()
            result1 = get_today_nutrition_cached(user, use_cache=False)
            time1 = time.time() - start
            
            self.stdout.write(f'  캐시 없음: {time1*1000:.2f}ms')
            self.stdout.write(f'    칼로리: {result1.get("total_calories", 0):.1f}kcal')
            
            # 2. 캐시 있이 조회 (두 번째 호출)
            start = time.time()
            result2 = get_today_nutrition_cached(user, use_cache=True)
            time2 = time.time() - start
            
            self.stdout.write(f'  캐시 사용: {time2*1000:.2f}ms')
            
            if time1 > 0:
                speedup = time1 / time2 if time2 > 0 else float('inf')
                self.stdout.write(
                    self.style.SUCCESS(f'  성능 향상: {speedup:.1f}배 빠름')
                )
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('테스트 완료!'))
        self.stdout.write('=' * 60)

