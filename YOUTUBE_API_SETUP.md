# YouTube Data API v3 설정 가이드

## 1. Google Cloud Console 접속

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다.
2. Google 계정으로 로그인합니다.

## 2. 프로젝트 생성

1. 상단의 프로젝트 선택 드롭다운을 클릭합니다.
2. "새 프로젝트"를 클릭합니다.
3. 프로젝트 이름을 입력합니다 (예: "50000AI-Recipe").
4. "만들기" 버튼을 클릭합니다.

## 3. YouTube Data API v3 활성화

1. 좌측 메뉴에서 "API 및 서비스" > "라이브러리"를 클릭합니다.
2. 검색창에 "YouTube Data API v3"를 입력합니다.
3. "YouTube Data API v3"를 선택합니다.
4. "사용" 버튼을 클릭합니다.

## 4. API 키 생성

1. 좌측 메뉴에서 "API 및 서비스" > "사용자 인증 정보"를 클릭합니다.
2. 상단의 "+ 사용자 인증 정보 만들기"를 클릭합니다.
3. "API 키"를 선택합니다.
4. API 키가 생성되면 복사하여 안전한 곳에 저장합니다.

## 5. API 키 제한 설정 (권장)

보안을 위해 API 키에 제한을 설정하는 것을 권장합니다:

1. 생성된 API 키 옆의 편집 아이콘을 클릭합니다.
2. "애플리케이션 제한사항"에서 적절한 제한을 선택합니다:
   - **HTTP 리퍼러**: 웹 애플리케이션의 경우
   - **IP 주소**: 서버 애플리케이션의 경우
3. "API 제한사항"에서 "키 제한"을 선택합니다.
4. "YouTube Data API v3"만 선택합니다.
5. "저장" 버튼을 클릭합니다.

## 6. 환경 변수 설정

### Windows (개발 환경)

프로젝트 루트에 `.env` 파일을 생성하거나 수정:

```
YOUTUBE_API_KEY=여기에_발급받은_API_키를_입력하세요
```

### Linux/Mac (프로덕션 환경)

```bash
export YOUTUBE_API_KEY="여기에_발급받은_API_키를_입력하세요"
```

또는 `.env` 파일에 추가:

```
YOUTUBE_API_KEY=여기에_발급받은_API_키를_입력하세요
```

## 7. 설정 확인

Django 프로젝트에서 다음 명령어로 확인:

```bash
python manage.py shell
```

```python
from django.conf import settings
print(settings.YOUTUBE_API_KEY)
```

API 키가 출력되면 설정이 완료된 것입니다.

## 8. 할당량 관리

YouTube Data API v3는 일일 할당량이 있습니다:

- **기본 할당량**: 하루 10,000 단위
- **검색 요청**: 100 단위/요청
- **비디오 정보 조회**: 1 단위/요청

### 할당량 확인

1. Google Cloud Console의 "API 및 서비스" > "할당량"에서 확인할 수 있습니다.
2. 필요시 할당량 증가를 신청할 수 있습니다.

## 9. 주의사항

⚠️ **중요**: API 키는 절대로 공개 저장소(GitHub 등)에 커밋하지 마세요!

- `.env` 파일을 `.gitignore`에 추가하세요
- 환경 변수로 관리하세요
- 프로덕션 환경에서는 보안 관리 서비스 사용을 권장합니다

## 10. 비용

YouTube Data API v3는 기본적으로 무료이지만, 할당량을 초과하면 추가 비용이 발생할 수 있습니다. 자세한 내용은 [Google Cloud 가격 정책](https://cloud.google.com/youtube/v3/getting-started#quota)을 참조하세요.

## 문제 해결

### "API key not valid" 오류

1. API 키가 올바르게 입력되었는지 확인
2. YouTube Data API v3가 활성화되었는지 확인
3. API 키 제한 설정이 올바른지 확인

### "quotaExceeded" 오류

1. 일일 할당량을 초과한 경우입니다
2. 다음 날까지 기다리거나 할당량 증가를 신청하세요

### 자막을 찾을 수 없는 경우

일부 YouTube 영상은 자막이 없거나 자막이 비활성화되어 있을 수 있습니다. 이는 정상적인 상황이며, 앱에서 적절한 에러 메시지를 표시합니다.

