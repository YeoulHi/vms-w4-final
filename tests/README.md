# Tests Guide

테스트 환경 설정 및 실행 가이드. Playwright MCP를 활용한 E2E 테스트와 Pytest 기반 단위 테스트를 포함합니다.

## 📋 목차

- [개요](#개요)
- [환경 설정](#환경-설정)
- [테스트 구조](#테스트-구조)
- [단위 테스트 (Unit Tests)](#단위-테스트-unit-tests)
- [E2E 테스트 (Playwright MCP)](#e2e-테스트-playwright-mcp)
- [테스트 실행](#테스트-실행)
- [Best Practices](#best-practices)
- [트러블슈팅](#트러블슈팅)

---

## 개요

본 프로젝트의 테스트 전략은 다층 테스트 피라미드를 따릅니다:

```
┌─────────────────────────────────────┐
│ E2E Test (Playwright MCP)           │
│ - 실제 사용자 시나리오               │
│ - 브라우저 기반 테스트               │
│ 개수: 적음 (3~5개)                  │
│ 속도: 느림 (초~분)                  │
└─────────────────────────────────────┘
         ↑
┌─────────────────────────────────────┐
│ Integration Tests                    │
│ - 다중 모듈 상호작용                 │
│ 개수: 중간 (5~10개)                 │
│ 속도: 중간 (초)                     │
└─────────────────────────────────────┘
         ↑
┌─────────────────────────────────────┐
│ Unit Tests (Pytest)                 │
│ - 함수/메서드 단위                   │
│ 개수: 많음 (20~50개)                │
│ 속도: 빠름 (밀리초)                 │
└─────────────────────────────────────┘
```

---

## 환경 설정

### 1. Python 의존성 설치

```bash
# 기본 의존성 설치
pip install -r requirements-dev.txt

# 설치되는 패키지:
# - pytest: 테스트 러너
# - pytest-django: Django 통합
# - pytest-cov: 커버리지 측정
# - pytest-mock: Mocking 도구
# - factory-boy: 테스트 데이터 생성
```

**Python 버전:**
- Python 3.12+ 권장
- Python 3.13.7 검증됨

### 2. Playwright MCP 설정

Playwright MCP는 **npx를 통해 온디맨드로 실행**됩니다:

```bash
# 방법 1: npm 스크립트
npm run playwright

# 방법 2: npx 직접 실행
npx @playwright/mcp@latest

# 방법 3: Claude에서 직접 사용
# Claude의 MCP 도구로 자동 로드됨
```

**Playwright MCP의 역할:**
- Claude에서 브라우저 자동화 가능
- 실시간 웹 상호작용 테스트
- 스크린샷 및 비디오 캡처
- DOM 검사 및 요소 선택

### 3. Django 설정 확인

```bash
# pytest.ini가 Django 설정을 올바르게 인식하는지 확인
pytest --collect-only

# 출력 예:
# platform win32 -- Python 3.13.7, pytest-8.4.2
# django: version: 5.2.7, settings: config.settings (from ini)
# collected 6 items
```

---

## 테스트 구조

### 디렉토리 레이아웃

```
tests/
├── __init__.py                 # 패키지 표시
├── README.md                   # 본 문서
├── conftest.py                 # 전역 Fixture 정의
├── factories.py                # 테스트 데이터 팩토리
│
├── unit/                       # 단위 테스트
│   ├── __init__.py
│   ├── test_chart_adapter.py   # 차트 데이터 변환 함수 테스트
│   └── test_*.py               # 추가 단위 테스트
│
├── integration/                # 통합 테스트
│   ├── __init__.py
│   ├── test_data_pipeline.py   # CSV 파싱 → DB 저장 → 조회
│   └── test_*.py               # 추가 통합 테스트
│
└── e2e/                        # E2E 테스트 (Playwright MCP)
    ├── __init__.py
    ├── test_login.py           # 로그인 시나리오
    └── test_*.py               # 추가 E2E 테스트
```

### Fixture 및 Factory

#### conftest.py - 전역 Fixture

```python
# 사용 가능한 Fixture:

@pytest.fixture
def authenticated_user(db):
    """인증된 테스트 사용자"""
    return UserFactory(username='testuser', password='testpass123')

@pytest.fixture
def authenticated_client(db, authenticated_user):
    """로그인된 Django 테스트 클라이언트"""
    # HTTP 요청 시뮬레이션용

@pytest.fixture
def sample_users(db):
    """여러 테스트 사용자"""
    return UserFactory.create_batch(5)
```

#### factories.py - 테스트 데이터 생성

```python
# 사용 가능한 Factory:

class UserFactory(factory.django.DjangoModelFactory):
    """User 모델 생성 팩토리"""
    # 사용: user = UserFactory()

class MetricRecordFactory(factory.django.DjangoModelFactory):
    """MetricRecord 모델 생성 팩토리"""
    # 사용: metric = MetricRecordFactory(year=2024)
```

---

## 단위 테스트 (Unit Tests)

### 목적
- 함수/메서드의 정확성 검증
- 비즈니스 로직 테스트
- 엣지 케이스 처리 확인

### 작성 방법

#### 1. 테스트 파일 생성

```python
# tests/unit/test_example.py
import pytest
from decimal import Decimal
from apps.dashboard.utils.chart_adapter import format_chart_data


class TestChartAdapter:
    """차트 데이터 변환 함수 테스트"""

    def test_format_chart_data_with_valid_records(self):
        """정상 데이터를 받았을 때 올바른 형식으로 변환"""
        # Arrange: 테스트 데이터 준비
        records = [
            {'department': 'Computer Science', 'metric_value': Decimal('85.50')},
            {'department': 'Philosophy', 'metric_value': Decimal('62.10')},
        ]

        # Act: 테스트할 함수 실행
        result = format_chart_data(records)

        # Assert: 결과 검증
        assert len(result['labels']) == 2
        assert result['labels'][0] == 'Computer Science'
        assert float(result['data'][0]) == 85.5

    def test_format_chart_data_with_empty_list(self):
        """빈 리스트를 받았을 때 빈 결과 반환"""
        result = format_chart_data([])
        assert result == {"labels": [], "data": []}
```

#### 2. 테스트 패턴 (AAA Pattern)

```python
def test_something(db):
    # Arrange: 테스트 데이터 준비
    user = UserFactory(username='test')
    data = [1, 2, 3]

    # Act: 테스트할 기능 실행
    result = some_function(user, data)

    # Assert: 결과 검증
    assert result is not None
    assert len(result) == 3
```

#### 3. Fixture 사용

```python
def test_with_fixture(authenticated_user):
    """Fixture를 활용한 테스트"""
    assert authenticated_user.is_active
    assert authenticated_user.username == 'testuser'
```

### 단위 테스트 체크리스트

- [ ] 정상 케이스 테스트
- [ ] 빈 입력 처리
- [ ] 기본값 처리
- [ ] 타입 변환 (Decimal → float)
- [ ] 대규모 데이터셋
- [ ] 에러 처리

---

## E2E 테스트 (Playwright MCP)

### 목적
- 실제 사용자 시나리오 검증
- 브라우저 상호작용 테스트
- UI 동작 확인
- 엔드투엔드 흐름 검증

### Playwright MCP 활용

#### 방법 1: Claude Code에서 직접 사용

Claude Code는 Playwright MCP를 자동으로 로드합니다:

```python
# Claude가 자동으로 브라우저 제어 가능
# 예: 페이지 이동, 요소 클릭, 스크린샷 등
```

#### 방법 2: npx로 수동 실행

```bash
# Playwright MCP 서버 시작
npx @playwright/mcp@latest

# 또는 npm 스크립트 사용
npm run playwright
```

#### 방법 3: 테스트 코드에서 사용

```python
# tests/e2e/test_login.py
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db
class TestLoginFlow:
    """사용자 로그인 흐름 E2E 테스트"""

    def test_user_can_login(self, page: Page, live_server):
        """사용자가 로그인 가능한지 검증"""
        # Playwright MCP를 통한 브라우저 제어
        login_url = f"{live_server.url}/login/"
        page.goto(login_url)

        # 요소 선택 및 상호작용
        page.get_by_label("Username").fill("testuser")
        page.get_by_label("Password").fill("testpass123")
        page.get_by_role("button", name="Login").click()

        # 결과 검증
        expect(page).to_have_url(f"{live_server.url}/dashboard/")
```

### Playwright MCP 기능

#### 주요 기능

```python
# 페이지 네비게이션
page.goto(url)                          # URL로 이동
page.go_back()                          # 뒤로 가기
page.reload()                           # 새로고침

# 요소 선택 및 상호작용
page.get_by_label("text").fill("value")  # 텍스트 입력
page.get_by_role("button", name="").click()  # 버튼 클릭
page.get_by_xpath("//div").check()       # 체크박스 선택
page.select_option("#id", "value")       # 드롭다운 선택

# 대기 및 확인
page.wait_for_url(url)                   # URL 변경 대기
page.wait_for_selector(".class")         # 요소 나타나기 대기
page.locator("text=Loading").is_hidden() # 요소 숨김 여부 확인

# 검증 (expect)
expect(page).to_have_url(url)            # URL 검증
expect(page).to_have_title("title")      # 제목 검증
expect(locator).to_be_visible()          # 요소 표시 여부
expect(locator).to_have_text("text")     # 텍스트 내용 검증

# 스크린샷 및 비디오
page.screenshot(path="screenshot.png")   # 스크린샷 저장
# context.tracing.start/stop()          # 비디오 녹화 (옵션)
```

#### 요소 선택 전략

```python
# 추천: 사용자 인터페이스 기반 선택
page.get_by_label("Password")            # 라벨 기반
page.get_by_role("button", name="Login") # 역할 기반
page.get_by_text("Submit")               # 텍스트 기반
page.get_by_placeholder("Enter name")    # 플레이스홀더 기반

# 대체: CSS/XPath 선택 (비추천)
page.locator("#id")                      # CSS ID
page.locator(".class")                   # CSS 클래스
page.get_by_xpath("//div[@class='x']")   # XPath
```

### E2E 테스트 작성 가이드

#### 1. 로그인 시나리오

```python
@pytest.mark.django_db
def test_user_login_flow(page: Page, live_server):
    """사용자 로그인 전체 흐름"""
    # 1. 준비: 테스트 사용자 생성
    user = UserFactory(username='testuser', password='testpass123')

    # 2. 로그인 페이지 접근
    page.goto(f"{live_server.url}/login/")
    expect(page).to_have_title("Login")

    # 3. 로그인 정보 입력
    page.get_by_label("Username").fill("testuser")
    page.get_by_label("Password").fill("testpass123")

    # 4. 로그인 버튼 클릭
    page.get_by_role("button", name="Login").click()

    # 5. 대시보드로 이동 확인
    expect(page).to_have_url(f"{live_server.url}/dashboard/")
    expect(page.locator("h1:has-text('Dashboard')")).to_be_visible()
```

#### 2. 데이터 표시 시나리오

```python
@pytest.mark.django_db
def test_dashboard_displays_metrics(page: Page, live_server):
    """대시보드에서 메트릭 데이터 표시 확인"""
    # 1. 메트릭 데이터 생성
    metrics = MetricRecordFactory.create_batch(3, year=2024)

    # 2. 인증된 사용자로 대시보드 접근
    user = UserFactory(username='testuser', password='testpass123')
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Username").fill("testuser")
    page.get_by_label("Password").fill("testpass123")
    page.get_by_role("button", name="Login").click()

    # 3. 대시보드 페이지 로드 대기
    expect(page).to_have_url(f"{live_server.url}/dashboard/")

    # 4. 차트/메트릭 표시 확인
    expect(page.locator("canvas")).to_be_visible()  # Chart.js 캔버스
```

#### 3. 폼 제출 시나리오

```python
@pytest.mark.django_db
def test_form_submission(page: Page, live_server):
    """폼 제출 및 유효성 검사"""
    page.goto(f"{live_server.url}/some-form/")

    # 폼 필드 입력
    page.get_by_label("Name").fill("John Doe")
    page.get_by_label("Email").fill("john@example.com")

    # 제출
    page.get_by_role("button", name="Submit").click()

    # 성공 확인
    expect(page.locator(".success-message")).to_be_visible()
```

### E2E 테스트 체크리스트

- [ ] 페이지 로드 확인
- [ ] 필수 요소 표시 확인
- [ ] 사용자 입력 처리
- [ ] 폼 제출 및 유효성 검사
- [ ] 페이지 이동/리디렉션
- [ ] 오류 메시지 표시
- [ ] 응답성 테스트 (선택)

---

## 테스트 실행

### 전체 테스트 실행

```bash
# 모든 테스트 실행
pytest -v

# 출력 예:
# tests/unit/test_chart_adapter.py::TestChartAdapter::test_... PASSED
# ====== 6 passed in 0.16s ======
```

### 특정 테스트만 실행

```bash
# 단위 테스트만
pytest tests/unit/ -v

# 통합 테스트만
pytest tests/integration/ -v

# E2E 테스트만
pytest tests/e2e/ -v

# 특정 파일의 테스트
pytest tests/unit/test_chart_adapter.py -v

# 특정 테스트 클래스
pytest tests/unit/test_chart_adapter.py::TestChartAdapter -v

# 특정 테스트 메서드
pytest tests/unit/test_chart_adapter.py::TestChartAdapter::test_format_chart_data_with_valid_records -v
```

### 커버리지 확인

```bash
# 커버리지와 함께 테스트 실행
pytest --cov=apps --cov-report=html

# 출력: htmlcov/index.html 에서 확인

# 커버리지 목표 설정
pytest --cov=apps --cov-fail-under=70
```

### 실시간 모니터링

```bash
# 파일 변경 시 자동으로 테스트 실행
pytest-watch  # 설치: pip install pytest-watch
```

### 병렬 실행 (옵션)

```bash
# pytest-xdist 설치 (다음 분기)
# pip install pytest-xdist

# 병렬 실행
# pytest -n auto
```

---

## Best Practices

### 1. 테스트 이름 규칙

```python
# ✅ 좋은 예
def test_format_chart_data_with_valid_records():
    """무엇을 테스트하는가를 명확하게"""
    pass

def test_login_fails_with_invalid_password():
    """실패 케이스도 포함"""
    pass

# ❌ 나쁜 예
def test_1():
    pass

def test_function():
    pass
```

### 2. 한 가지만 테스트 (단일 책임)

```python
# ❌ 나쁜 예: 여러 개념을 한번에
def test_user_creation_and_login():
    user = UserFactory()
    # 사용자 생성 테스트
    # 로그인 테스트
    pass

# ✅ 좋은 예: 각각 분리
def test_user_creation():
    user = UserFactory()
    assert user.is_active

def test_user_login():
    user = UserFactory(username='testuser', password='pass')
    # 로그인 테스트만
```

### 3. Fixture 활용

```python
# ✅ Fixture 사용 (재사용 가능)
def test_something(authenticated_user):
    assert authenticated_user.is_active

def test_something_else(authenticated_user):
    assert authenticated_user.username == 'testuser'

# ❌ 반복되는 설정 (DRY 위반)
def test_something():
    user = UserFactory(username='testuser', password='testpass123')
    # ...

def test_something_else():
    user = UserFactory(username='testuser', password='testpass123')
    # ...
```

### 4. Mock 사용 (외부 의존성)

```python
# 외부 API 호출을 Mock으로 대체
def test_with_mocked_api(mocker):
    """Mock을 사용한 테스트"""
    mock_response = {'status': 'success'}
    mocker.patch('requests.get', return_value=mock_response)

    # 테스트 로직
    result = some_api_call()
    assert result['status'] == 'success'
```

### 5. Playwright MCP 모범 사례

```python
# ✅ 좋은 예
def test_login(page: Page, live_server):
    # 1. 페이지 이동
    page.goto(f"{live_server.url}/login/")

    # 2. 자동 대기 (MCP가 자동 처리)
    page.get_by_label("Username").fill("test")

    # 3. 명시적 확인
    expect(page).to_have_url(...)

# ❌ 나쁜 예: 임의의 대기
def test_login(page: Page, live_server):
    page.goto(...)
    time.sleep(1)  # 안 좋음
    page.get_by_label("Username").fill("test")
```

---

## 트러블슈팅

### 문제 1: "ModuleNotFoundError: No module named 'pytest'"

**해결책:**
```bash
# 의존성 다시 설치
pip install -r requirements-dev.txt
```

### 문제 2: "Django database backend initialization failed"

**해결책:**
```bash
# Django 마이그레이션 실행
python manage.py migrate

# pytest.ini에서 올바른 DJANGO_SETTINGS_MODULE 확인
# DJANGO_SETTINGS_MODULE = config.settings
```

### 문제 3: "Playwright browser not found"

**해결책:**
```bash
# Playwright 브라우저 설치 (E2E 테스트만 필요)
pip install playwright
playwright install
```

### 문제 4: "Fixture 'authenticated_user' not found"

**해결책:**
```bash
# conftest.py가 tests/ 디렉토리에 있는지 확인
# 또는 __init__.py가 패키지 표시하는지 확인

ls -la tests/
# conftest.py 존재 확인
# tests/__init__.py 존재 확인
```

### 문제 5: "test marked with @pytest.mark.django_db fails"

**해결책:**
```python
# 테스트에서 DB 접근이 필요하면 @pytest.mark.django_db 추가
@pytest.mark.django_db
def test_with_db(db):
    user = UserFactory()
    # DB 접근 테스트
```

### 문제 6: "Playwright MCP connection failed"

**해결책:**
```bash
# MCP 서버 시작 (별도 터미널)
npm run playwright

# 또는 npx 직접 실행
npx @playwright/mcp@latest

# 포트 확인 (기본 8080)
netstat -ano | findstr :8080
```

---

## 추가 리소스

### 공식 문서
- [Pytest 공식 문서](https://docs.pytest.org/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
- [Playwright Python](https://playwright.dev/python/)

### 프로젝트 문서
- `TEST_ENV_PROPOSAL.md` - 기술 스택 상세 분석
- `TESTING_IMPLEMENTATION_SUMMARY.md` - 최종 요약
- `AI_FEEDBACK_PROMPT.md` - 심화 검토 자료

### 팀 리소스
- `conftest.py` - 사용 가능한 모든 Fixture
- `factories.py` - 테스트 데이터 생성기
- 예제 테스트 파일들

---

## 자주 묻는 질문 (FAQ)

### Q1: 단위 테스트와 E2E 테스트의 차이?

**A:**
- **단위 테스트:** 함수 하나를 테스트 (빠름, 간단함)
- **E2E 테스트:** 전체 사용자 흐름을 테스트 (느림, 현실적)

### Q2: Playwright MCP를 항상 실행해야 하나?

**A:** 아니요.
- **단위 테스트:** MCP 불필요
- **E2E 테스트만:** MCP 필요
- Claude Code에서는 자동으로 로드됨

### Q3: 테스트 데이터는 어떻게 관리?

**A:** Factory Boy를 사용합니다:
```python
user = UserFactory()  # 자동 생성
users = UserFactory.create_batch(5)  # 여러 개 생성
metric = MetricRecordFactory(year=2024)  # 커스텀 필드
```

### Q4: 테스트 커버리지 목표는?

**A:**
- **비즈니스 로직:** 70% 이상
- **모델:** 50% (Django ORM은 기본 보장)
- **뷰/API:** 50% (통합 테스트로 커버)
- **전체:** 60% 이상

### Q5: CI/CD에서 테스트를 자동 실행하려면?

**A:** 다음 분기에 GitHub Actions 추가 예정:
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest --cov=apps
```

---

## 다음 단계

### 이번 주 (Week 1)
- [x] 단위 테스트 환경 구축
- [x] 예제 테스트 작성
- [ ] 팀 온보딩

### 다음 주 (Week 2)
- [ ] 추가 단위 테스트 작성
- [ ] 통합 테스트 추가
- [ ] E2E 테스트 확대

### 다음분기 (Week 3+)
- [ ] GitHub Actions CI
- [ ] Playwright 브라우저 캐싱
- [ ] 커버리지 리포트 자동화
- [ ] pytest-xdist 병렬 실행

---

## 문의 및 피드백

테스트 환경에 대한 문의사항은:
- Slack: #testing 채널
- Issues: GitHub Issues
- 문서: 본 README 및 TEST_ENV_PROPOSAL.md

---

**마지막 업데이트:** 2025-10-31
**유지보수:** Claude Code / Development Team
