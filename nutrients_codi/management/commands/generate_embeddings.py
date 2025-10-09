from django.core.management.base import BaseCommand
from nutrients_codi.models import Food
from nutrients_codi.ai_service import GeminiAIService
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '음식 데이터에 임베딩을 생성합니다 (배치 처리로 최적화)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='처리할 최대 음식 수 (기본값: 전체)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='이미 임베딩이 있는 음식도 다시 생성'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='배치 크기 (기본값: 100)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        batch_size = options['batch_size']
        
        # AI 서비스 초기화
        try:
            ai_service = GeminiAIService()
            self.stdout.write(self.style.SUCCESS('[OK] AI 서비스 초기화 성공'))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] AI 서비스 초기화 실패: {e}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] AI 서비스 초기화 중 예상치 못한 오류: {e}'))
            return
        
        # 임베딩 모델 로드
        ai_service._load_embedding_model()
        
        if not ai_service.embedding_model:
            self.stdout.write(self.style.ERROR('[ERROR] 임베딩 모델이 로드되지 않았습니다.'))
            return
        
        # 임베딩 테스트
        try:
            test_embedding = ai_service.get_embedding("테스트")
            if test_embedding:
                self.stdout.write(self.style.SUCCESS(f'[OK] 임베딩 테스트 성공 (차원: {len(test_embedding)})'))
            else:
                self.stdout.write(self.style.ERROR('[ERROR] 임베딩 테스트 실패'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] 임베딩 테스트 중 오류: {e}'))
            return
        
        # 처리할 음식들 가져오기 (메모리 효율을 위해 only 사용)
        # count() 병목 방지: exists()로 먼저 확인만
        queryset = Food.objects.only('id', 'name', 'embedding')
        
        if not force:
            queryset = queryset.filter(embedding__isnull=True)
        
        # 빠른 체크: 처리할 데이터가 있는지만 확인
        if not queryset.exists():
            self.stdout.write(self.style.WARNING('[INFO] 처리할 음식이 없습니다.'))
            return
        
        if limit:
            queryset = queryset[:limit]
        
        # count() 대신 대략적인 정보만 표시
        self.stdout.write(f'\n[INFO] 임베딩 생성을 시작합니다...')
        self.stdout.write(f'[INFO] 배치 크기: {batch_size}')
        if limit:
            self.stdout.write(f'[INFO] 최대 처리: {limit}개')
        else:
            self.stdout.write(f'[INFO] 전체 데이터 처리 (임베딩 없는 음식만)')
        self.stdout.write(f'[INFO] 진행 상황은 실시간으로 표시됩니다.\n')
        
        success_count = 0
        error_count = 0
        
        # iterator()로 메모리 절약 (14만개도 문제없음!)
        # 배치 단위로 DB에서 가져오기
        import time
        
        # tqdm으로 진행 상황 표시 (total 없이 동적으로)
        with tqdm(desc="임베딩 생성", unit="음식", total=None) as pbar:
            batch = []
            processed = 0
            
            # iterator()로 청크씩 가져오기 (메모리 효율적)
            for food in queryset.iterator(chunk_size=batch_size):
                batch.append(food)
                
                # 배치가 찼을 때 처리
                if len(batch) >= batch_size:
                    # 배치 처리
                    try:
                        # 음식명 추출
                        food_names = [f.name for f in batch]
                        
                        # 임베딩 생성
                        embeddings = ai_service.get_embeddings_batch(food_names)
                        
                        # 임베딩 할당
                        foods_to_update = []
                        for f, emb in zip(batch, embeddings):
                            if emb:
                                f.embedding = emb
                                foods_to_update.append(f)
                                success_count += 1
                            else:
                                error_count += 1
                        
                        # DB 저장 (bulk_update)
                        if foods_to_update:
                            Food.objects.bulk_update(
                                foods_to_update,
                                ['embedding'],
                                batch_size=len(foods_to_update)
                            )
                        
                        processed += len(batch)
                        pbar.update(len(batch))
                        
                        # 진행 상황 출력 (1000개마다)
                        if processed % 1000 == 0:
                            self.stdout.write(
                                f'[PROGRESS] {processed}개 처리 완료 '
                                f'(성공: {success_count}, 실패: {error_count})'
                            )
                        
                    except Exception as e:
                        error_count += len(batch)
                        logger.error(f'배치 처리 오류: {e}')
                        pbar.update(len(batch))
                    
                    # 배치 초기화
                    batch = []
                    
                    # API rate limit 방지 (짧은 대기)
                    time.sleep(0.2)
            
            # 마지막 남은 배치 처리
            if batch:
                try:
                    food_names = [f.name for f in batch]
                    embeddings = ai_service.get_embeddings_batch(food_names)
                    
                    foods_to_update = []
                    for f, emb in zip(batch, embeddings):
                        if emb:
                            f.embedding = emb
                            foods_to_update.append(f)
                            success_count += 1
                        else:
                            error_count += 1
                    
                    if foods_to_update:
                        Food.objects.bulk_update(
                            foods_to_update,
                            ['embedding'],
                            batch_size=len(foods_to_update)
                        )
                    
                    pbar.update(len(batch))
                    
                except Exception as e:
                    error_count += len(batch)
                    logger.error(f'마지막 배치 처리 오류: {e}')
                    pbar.update(len(batch))
        
        # 최종 결과
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'[COMPLETE] 완료: {success_count}개 성공'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'[WARNING] 실패: {error_count}개'))
        self.stdout.write('='*60)
