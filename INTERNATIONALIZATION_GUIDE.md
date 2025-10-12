# 다국어(국제화) 설정 가이드

## 현재 상태

브라우저 언어에 따라 자동으로 한국어/영어가 전환되는 시스템이 구현되었습니다.

### 구현 방식

1. **서버 사이드 번역 (Django i18n)**
   - `LocaleMiddleware`가 브라우저의 `Accept-Language` 헤더를 자동 감지
   - 번역 파일: `locale/en/LC_MESSAGES/django.po`, `django.mo`
   - 메인 홈페이지(`templates/main_project/home.html`)에 적용

2. **클라이언트 사이드 번역 (JavaScript)**
   - `nutrients_codi`, `recipe_ai` 앱은 JavaScript로 번역 처리
   - 브라우저 언어(`navigator.language`)를 감지하여 실시간 변환

## 테스트 방법

### 1. 브라우저 언어 변경 테스트

#### Chrome
1. 설정(Settings) → 언어(Languages)
2. "기본 언어(Preferred languages)" 섹션에서 English를 맨 위로 이동
3. 브라우저 재시작
4. http://localhost:8000 접속하여 영어로 표시되는지 확인

#### Firefox
1. 설정(Settings) → 일반(General) → 언어(Language)
2. "Choose your preferred language" 에서 English를 맨 위로 이동
3. 브라우저 재시작
4. http://localhost:8000 접속하여 영어로 표시되는지 확인

### 2. curl을 통한 테스트

```bash
# 한국어 요청
curl -H "Accept-Language: ko" http://localhost:8000/

# 영어 요청
curl -H "Accept-Language: en" http://localhost:8000/
```

### 3. Django 개발 서버 실행

```bash
python manage.py runserver
```

## 번역된 텍스트 예시

| 한국어 | 영어 |
|--------|------|
| 프로필 | Profile |
| 로그아웃 | Logout |
| 로그인 | Login |
| 시작하기 | Get Started |
| AI로 더 스마트한 삶을 설계하세요 | Smarter Living with AI - Design Your Life |
| 뉴트리언트코디 | Nutrients-Codi |
| AI 요리 추천 | AI Recipe Recommendation |

## 추가 번역 추가 방법

### 1. 템플릿에 번역 태그 추가

```django
{% load i18n %}

<!-- 간단한 텍스트 -->
<h1>{% trans "안녕하세요" %}</h1>

<!-- HTML 포함된 텍스트 -->
<p>{% blocktrans %}환영합니다 <strong>사용자</strong>님{% endblocktrans %}</p>
```

### 2. 번역 파일 수정

`locale/en/LC_MESSAGES/django.po` 파일에 새로운 번역 추가:

```po
msgid "안녕하세요"
msgstr "Hello"
```

### 3. 번역 파일 컴파일

```bash
# polib 사용 (gettext 없이)
pip install polib
python -c "import polib; po = polib.pofile('locale/en/LC_MESSAGES/django.po'); po.save_as_mofile('locale/en/LC_MESSAGES/django.mo')"

# 또는 gettext 설치 후
python manage.py compilemessages
```

### 4. 서버 재시작

```bash
python manage.py runserver
```

## 주의사항

1. **브라우저 캐시**: 번역이 즉시 반영되지 않으면 브라우저 캐시를 지우세요 (Ctrl+Shift+Delete)
2. **서버 재시작**: .mo 파일 변경 후에는 Django 서버를 재시작해야 합니다
3. **하이브리드 방식**: 현재 메인 페이지는 Django i18n, 앱 내부 페이지는 JavaScript로 번역됩니다

## 문제 해결

### 번역이 표시되지 않을 때

1. `.mo` 파일이 생성되었는지 확인:
   ```bash
   ls locale/en/LC_MESSAGES/django.mo
   ```

2. `LocaleMiddleware`가 활성화되었는지 확인:
   ```python
   # main_project/settings/base.py
   MIDDLEWARE = [
       ...
       'django.middleware.locale.LocaleMiddleware',
       ...
   ]
   ```

3. 브라우저의 `Accept-Language` 헤더 확인:
   - Chrome DevTools → Network → 요청 헤더 확인

## 향후 개선 사항

1. 모든 템플릿에 Django i18n 적용
2. Python 코드(views.py, forms.py)에 gettext 적용
3. 관리자 페이지 번역
4. 추가 언어 지원 (일본어, 중국어 등)

