from django.core.management.base import BaseCommand
from nutrients_codi.models import Food
from nutrients_codi.ai_service import GeminiAIService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '음식 데이터에 로컬 임베딩을 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='처리할 최대 음식 수 (기본값: 100)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='이미 임베딩이 있는 음식도 다시 생성'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        
        # AI 서비스 초기화
        try:
            ai_service = GeminiAIService()
        except ValueError as e:
            self.stdout.write(
                self.style.ERROR(f'AI 서비스 초기화 실패: {e}')
            )
            return
        
        if not ai_service.embedding_model:
            self.stdout.write(
                self.style.ERROR('임베딩 모델이 로드되지 않았습니다.')
            )
            return
        
        # 처리할 음식들 가져오기
        if force:
            foods = Food.objects.all()[:limit]
        else:
            foods = Food.objects.filter(embedding__isnull=True)[:limit]
        
        total_count = foods.count()
        self.stdout.write(f'총 {total_count}개 음식의 임베딩을 생성합니다...')
        
        success_count = 0
        error_count = 0
        
        for i, food in enumerate(foods, 1):
            try:
                self.stdout.write(f'처리 중: {i}/{total_count} - {food.name}')
                
                # 임베딩 생성
                embedding = ai_service.get_embedding(food.name)
                
                if embedding:
                    # 데이터베이스에 저장
                    food.embedding = embedding
                    food.save()
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'[OK] {food.name} 임베딩 생성 완료')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'[FAIL] {food.name} 임베딩 생성 실패')
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'[ERROR] {food.name} 처리 중 오류: {str(e)}')
                )
                logger.error(f'임베딩 생성 오류 - {food.name}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'완료: {success_count}개 성공, {error_count}개 실패'
            )
        )
