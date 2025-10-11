"""
Gunicorn 설정 파일 - WORKER TIMEOUT 및 메모리 문제 해결

사용법:
gunicorn -c gunicorn_config.py main_project.wsgi:application
"""

import multiprocessing
import os

# 서버 소켓
bind = "0.0.0.0:8000"
backlog = 2048

# Worker 프로세스
# CPU 코어 수가 아닌 메모리 기반으로 설정
workers = 2  # 메모리 부족 시 2개로 제한
worker_class = "gthread"  # 스레드 기반 (메모리 효율적)
threads = 4  # Worker당 4개 스레드
worker_connections = 1000

# Timeout 설정 (WORKER TIMEOUT 방지)
timeout = 120  # 30초 → 120초로 증가
graceful_timeout = 30
keepalive = 5

# Worker 재시작 (메모리 누수 방지)
max_requests = 1000
max_requests_jitter = 50

# 메모리 최적화
worker_tmp_dir = "/dev/shm"  # RAM 디스크 사용 (Linux)

# 로깅
accesslog = "-"  # stdout
errorlog = "-"  # stderr
loglevel = "warning"  # 불필요한 로그 최소화
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 프로세스 이름
proc_name = "50000ai_gunicorn"

# 보안
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 성능 튜닝
preload_app = False  # 메모리 절약 (각 worker가 독립적으로 로드)

# Hook 함수들
def on_starting(server):
    """서버 시작 시"""
    print("=" * 60)
    print("50000AI Gunicorn Server Starting")
    print(f"Workers: {workers}")
    print(f"Threads per worker: {threads}")
    print(f"Timeout: {timeout}s")
    print("=" * 60)

def worker_int(worker):
    """Worker가 SIGINT 받았을 때"""
    print(f"Worker {worker.pid} received SIGINT")

def worker_abort(worker):
    """Worker가 SIGABRT 받았을 때 (TIMEOUT)"""
    print(f"Worker {worker.pid} TIMEOUT! Aborting...")
    print("이 메시지가 반복되면 최적화 코드 배포를 확인하세요.")

def post_worker_init(worker):
    """Worker 초기화 후"""
    print(f"Worker {worker.pid} initialized")

