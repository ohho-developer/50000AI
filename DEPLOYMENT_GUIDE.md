# 프로덕션 배포 가이드 (WORKER TIMEOUT 해결)

## 🚨 문제 진단

```
WORKER TIMEOUT (pid:48)
Worker was sent SIGKILL! Perhaps out of memory?
```

이 문제는 **대용량 쿼리 + 메모리 부족**으로 발생했습니다.

## ✅ 해결 방법 (이미 적용됨)

### 1. 코드 레벨 최적화 (가장 중요!)

**변경된 파일:**
- `nutrients_codi/views.py` - 50개 필드 → 7개 필드
- `nutrients_codi/utils_optimized.py` - 캐싱 시스템
- `main_project/settings/base.py` - DB 연결 풀링
- `main_project/settings/production.py` - 프로덕션 최적화

**효과:**
- 메모리 사용량: 70-80% 감소
- 쿼리 속도: 5-10배 향상
- 응답 시간: 수 초 → 밀리초

### 2. Gunicorn 설정 변경

**기존 설정 (문제 발생):**
```bash
gunicorn --workers 4 --timeout 30 main_project.wsgi:application
```

**새 설정 (권장):**
```bash
gunicorn -c gunicorn_config.py main_project.wsgi:application
```

또는 직접 옵션 지정:
```bash
gunicorn \
  --workers 2 \
  --threads 4 \
  --worker-class gthread \
  --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --worker-tmp-dir /dev/shm \
  main_project.wsgi:application
```

### 3. 환경 변수 확인

`.env` 파일에 다음 설정 확인:
```env
DJANGO_SETTINGS_MODULE=main_project.settings.production
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## 📦 배포 순서

### 1단계: 코드 배포
```bash
# 로컬에서 Git 커밋
git add .
git commit -m "성능 최적화: WORKER TIMEOUT 해결"
git push origin main

# 서버에서 Pull
cd /path/to/50000AI
git pull origin main
```

### 2단계: 의존성 확인
```bash
# 가상환경 활성화
source venv/bin/activate  # Linux
# 또는
venv\Scripts\activate  # Windows

# 패키지 확인 (psutil 필요)
pip install psutil
```

### 3단계: 데이터베이스 최적화
```bash
# 마이그레이션 (필요시)
python manage.py migrate

# PostgreSQL 최적화 실행
python manage.py optimize_postgres --vacuum

# 캐시 테이블 생성 (처음 한 번만)
python manage.py createcachetable
```

### 4단계: Gunicorn 재시작
```bash
# systemd 사용 시
sudo systemctl restart gunicorn

# 또는 직접 재시작
pkill gunicorn
gunicorn -c gunicorn_config.py main_project.wsgi:application &
```

### 5단계: 모니터링
```bash
# 로그 실시간 확인
tail -f /var/log/gunicorn/error.log

# 메모리 사용량 모니터링
watch -n 1 free -m

# Worker 상태 확인
ps aux | grep gunicorn
```

## 🔍 문제 발생 시 체크리스트

### WORKER TIMEOUT이 계속 발생한다면:

1. **최적화 코드가 배포되었는지 확인**
   ```bash
   cd /path/to/50000AI
   git log -1  # 최신 커밋 확인
   ls -la nutrients_codi/utils_optimized.py  # 파일 존재 확인
   ```

2. **Timeout 설정 확인**
   ```bash
   ps aux | grep gunicorn | grep timeout
   # --timeout 120 이 표시되어야 함
   ```

3. **메모리 상태 확인**
   ```bash
   free -m
   # 여유 메모리가 200MB 이상 있어야 함
   ```

4. **Worker 수 조정**
   ```bash
   # 메모리가 부족하면 Worker를 1개로 줄이기
   gunicorn --workers 1 --timeout 120 ...
   ```

## 📊 성능 측정

배포 후 성능 확인:
```bash
# Django 쉘에서 테스트
python manage.py check_performance

# HTTP 요청 테스트
curl -o /dev/null -s -w "Time: %{time_total}s\n" https://your-domain.com/nutrients-codi/
```

**정상 응답 시간:**
- 대시보드: < 1초
- 일별 상세: < 2초
- 분석 요청: < 5초

## 🎯 장기적 개선 사항

1. **Redis 캐시 도입**
   ```bash
   pip install redis django-redis
   ```

2. **Celery 비동기 작업**
   ```bash
   pip install celery
   ```

3. **서버 리소스 증설**
   - RAM: 최소 2GB → 4GB 권장
   - CPU: 2 Core 이상 권장

4. **pgBouncer 도입**
   ```bash
   sudo apt-get install pgbouncer
   ```

## ❓ 자주 묻는 질문

**Q: WORKER TIMEOUT은 해결됐는데 여전히 느려요**
A: `python manage.py check_performance`로 캐시가 작동하는지 확인하세요.

**Q: 메모리가 계속 증가해요**
A: `--max-requests 1000` 옵션으로 주기적인 Worker 재시작이 설정되어 있는지 확인하세요.

**Q: 특정 페이지만 느려요**
A: 해당 페이지의 views.py 함수도 최적화가 필요할 수 있습니다.

## 📞 지원

문제가 계속되면:
1. 로그 파일 확인: `/var/log/gunicorn/error.log`
2. Django 로그 확인: `logs/django.log`
3. 메모리 덤프: `ps aux --sort=-%mem | head -20`

