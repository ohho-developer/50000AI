# 📧 이메일 전송 문제 해결 가이드

## 현재 상황
- 터미널에는 이메일 내용이 출력됨
- 실제로 이메일이 도착하지 않음
- Gmail SMTP 사용 중

## 🔍 문제 원인

### 1. Gmail 보안 정책 변경 (가장 가능성 높음)
2024년 5월부터 Gmail은 "보안 수준이 낮은 앱"을 차단합니다.
**해결책: 앱 비밀번호 사용**

### 2. 2단계 인증 필수
Gmail 계정에 2단계 인증이 켜져있으면 일반 비밀번호로는 SMTP 사용 불가

### 3. SMTP 설정 오류
포트, TLS 설정 등이 잘못되었을 수 있음

---

## ✅ 해결 방법

### 방법 1: Gmail 앱 비밀번호 사용 (추천) ⭐

#### 1단계: Google 계정에서 2단계 인증 활성화
1. https://myaccount.google.com/security 접속
2. "2단계 인증" 클릭하여 활성화

#### 2단계: 앱 비밀번호 생성
1. https://myaccount.google.com/apppasswords 접속
2. "앱 선택" → "기타(맞춤 이름)" 선택
3. "50000AI Django" 입력
4. "생성" 클릭
5. **16자리 비밀번호 복사** (예: `abcd efgh ijkl mnop`)

#### 3단계: .env 파일 수정
```env
EMAIL_HOST_PASSWORD=abcdefghijklmnop  # 16자리 (공백 없이)
```

#### 4단계: 서버 재시작
```bash
# 서버 종료 후 재시작
python manage.py runserver
```

---

### 방법 2: Gmail 설정 확인

#### Gmail 계정 설정 확인:
1. IMAP 액세스 활성화 확인
   - Gmail 설정 → 전달 및 POP/IMAP
   - "IMAP 사용" 체크

2. "보안 수준이 낮은 앱의 액세스" (구버전 계정)
   - https://myaccount.google.com/lesssecureapps
   - "사용" 으로 변경 (2024년 이후 대부분 불가능)

---

### 방법 3: 다른 이메일 서비스 사용

#### A. SendGrid (무료 플랜: 100통/일)
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = '여기에_SendGrid_API_키'
```

#### B. Mailgun (무료 플랜: 5,000통/월)
```python
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'postmaster@your-domain.mailgun.org'
EMAIL_HOST_PASSWORD = '여기에_Mailgun_비밀번호'
```

#### C. AWS SES (저렴)
```python
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_ACCESS_KEY_ID = '여기에_AWS_키'
AWS_SECRET_ACCESS_KEY = '여기에_AWS_시크릿'
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'
```

---

### 방법 4: 개발 중에는 Console Backend 사용

개발 환경에서 실제 이메일이 필요 없다면:

```python
# settings.py 또는 development.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

이메일이 터미널에만 출력되고 실제로 전송되지 않음 (개발용)

---

## 🧪 테스트 방법

### Django Shell에서 테스트:
```python
python manage.py shell

from django.core.mail import send_mail
send_mail(
    '테스트',
    '테스트 메시지',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)
```

에러가 발생하면 정확한 에러 메시지를 확인할 수 있습니다.

---

## 📌 현재 설정 확인

```bash
# .env 파일 확인
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=여기에_앱비밀번호_16자리
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

---

## ⚠️ 주의사항

1. **앱 비밀번호에는 공백이 없어야 함**
   - 잘못: `abcd efgh ijkl mnop`
   - 올바름: `abcdefghijklmnop`

2. **2단계 인증이 꺼져있으면 앱 비밀번호 메뉴가 안 보임**

3. **Gmail은 하루 500통 제한이 있음**

4. **스팸 폴더 확인**
   - 첫 이메일은 스팸으로 분류될 수 있음

---

## 🚀 빠른 해결 체크리스트

- [ ] Gmail 2단계 인증 활성화
- [ ] 앱 비밀번호 생성 (16자리)
- [ ] .env 파일에 앱 비밀번호 입력 (공백 없이)
- [ ] 서버 재시작
- [ ] 테스트 이메일 전송
- [ ] 스팸 폴더 확인

---

## 💡 추천 솔루션

**단기 (즉시 해결):**
→ Gmail 앱 비밀번호 사용

**장기 (프로덕션):**
→ SendGrid 또는 AWS SES 사용 (안정성, 전송률 높음)

**개발 환경:**
→ Console Backend 사용 (실제 전송 불필요)

