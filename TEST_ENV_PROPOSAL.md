# 단위/E2E 테스트 환경 구축 제안서

**작성자:** CTO
**날짜:** 2025-10-31
**대상:** 팀 리드, 개발팀
**목표:** MVP 안정성 확보 + 신속한 개발 반복을 위한 테스트 환경 구축

---

## 📋 Executive Summary (2분 읽기)

### 제안 내용

본 문서는 **Pytest + Playwright 기반의 통합 테스트 환경**을 MVP 단계에서 구축하는 방안을 제시합니다.

| 항목 | 내용 |
|------|------|
| **추진 기간** | 1주 (Phase 1: 환경 구축) + 1주 (Phase 2: 핵심 테스트) |
| **투자 비용** | 개발 시간 2~3일 (팀 전체 초기 학습 30분) |
| **기대 효과** | 회귀 버그 80% 감소, 배포 자신감 향상, 리팩토링 안정성 |
| **사용 기술** | Pytest, Playwright, Factory Boy, pytest-django |

### 핵심 의사결정

**왜 Pytest인가?**
- Django의 기본 TestCase보다 간결한 문법 (assert vs assertEqual)
- Pytest의 Fixture 모델로 테스트 간 중복 코드 제거
- 단위/E2E/통합 테스트를 **하나의 Runner로 통일** → 팀의 개발 경험 단순화

**왜 Playwright인가?**
- Selenium 대비 80% 빠른 실행 속도
- 자동 대기(Auto-wait) 기능으로 Flaky 테스트 최소화
- 최신 브라우저 아키텍처 활용 → 안정적

**왜 Factory Boy를 처음부터 도입하는가?**
- 지금은 불필요해 보이지만, 테스트가 50개를 넘으면 필수
- 초기 30분 투자로 향후 월 3~5시간 절감
- 기술 부채 방지: "나중에 추가하기"는 구조 변경을 요구함

### 예상 타임라인

```
이번 주(Week 1):      환경 구축 (의존성, pytest 설정, 디렉토리 구조)
다음주(Week 2):       핵심 테스트 작성 (단위 2개, 통합 2개, E2E 3개)
2주 이후(Week 3+):    CI/CD 자동화, 커버리지 관리 (별도 문서)
```

---

## ✅ 장점

1. **신속한 도입** (1주일 내)
   - 기존 Django 프로젝트에 최소 설정으로 즉시 적용
   - 팀원이 하루 안에 테스트 작성 가능

2. **기술 스택 통일**
   - Pytest 하나로 단위/통합/E2E 테스트 모두 관리
   - 팀의 정신적 부담 감소 (여러 도구 학습 불필요)

3. **확장성 및 미래 대비**
   - Factory Boy의 규칙 기반 설계로 모델 추가 시 테스트 데이터 자동 확장
   - Pytest의 Fixture는 나중에 데이터베이스, API Mock 추가 시 기반이 됨

4. **비용 효율성**
   - 모두 오픈소스 (비용 0)
   - 로컬 + CI 환경에서 즉시 실행 (별도 인프라 불필요)

5. **개발 생산성 향상**
   - 초기 투자 2~3일 → 향후 월 10시간 절감 (3개월 ROI)
   - 리팩토링 시 회귀 위험 감소

---

## ⚠️ 예상되는 한계점

| 한계 | 영향 | 완화 방법 |
|------|------|---------|
| **SQLite vs PostgreSQL 불일치** | 테스트는 SQLite, 프로덕션은 PostgreSQL로 실행되는 쿼리 동작이 다를 수 있음 | 다음 분기: Docker 기반 PostgreSQL 테스트 환경 도입 |
| **브라우저 바이너리 관리** | CI 환경에서 Playwright 브라우저 설치 시간 (5분) | GitHub Actions 캐싱 전략 (다음 분기) |
| **E2E 테스트 속도** | 10개 E2E 테스트 = 약 3~5분 소요 | 단위/통합 테스트 우선 실행, E2E는 병렬화 (pytest-xdist, 다음 분기) |
| **초기 학습곡선** | Pytest Fixture, Factory Boy 문법 학습 필요 | 팀 온보딩 30분, 문서 제공 |

---

## 🎯 다음 단계 (상세 내용은 아래)

### Phase 1: 기본 환경 구축 (이번 주)
- [ ] `requirements-dev.txt` 생성 (Pytest, Playwright, Factory Boy)
- [ ] `pytest.ini` 설정
- [ ] `tests/` 디렉토리 구조 생성 (`unit/`, `integration/`, `e2e/`)
- [ ] `conftest.py` 및 `factories.py` 작성
- [ ] 테스트 1개 실행 확인

### Phase 2: 핵심 테스트 작성 (다음 주)
- [ ] 단위 테스트 예제 1개 작성 (`tests/unit/test_chart_adapter.py`)
- [ ] E2E 테스트 예제 1개 작성 (`tests/e2e/test_login.py`)
- [ ] 전체 테스트 성공 확인

### Phase 3: 통합 및 최적화 (다음 다음주)
- [ ] GitHub Actions CI 파이프라인
- [ ] 커버리지 리포트
- [ ] 병렬 실행 (pytest-xdist)

---

## 📊 기술 스택 선택 근거 (상세)

### 1. Test Runner: Pytest vs Django TestCase

#### Pytest 선택 이유

**비교 대상: Django의 기본 TestCase**

```python
# Django TestCase (기존)
class UserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='test')

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'test')

# Pytest (제안)
@pytest.mark.django_db
def test_user_creation(db):
    user = UserFactory()
    assert user.username.startswith('user_')
```

**Pytest의 장점:**
1. **간결한 문법**
   - `assertEqual()` → `assert` (더 직관적)
   - 테스트당 2~3줄 코드 절감

2. **강력한 Fixture 모델**
   - `setUp()`은 매 테스트마다 호출되지만, Pytest Fixture는 필요할 때만 생성
   - 테스트 간 공유 리소스 관리 용이
   - 재사용성 높음 (여러 테스트에서 동일 Fixture 사용)

3. **풍부한 플러그인 생태계**
   - `pytest-django`: Django 통합
   - `pytest-cov`: 커버리지 측정
   - `pytest-xdist`: 병렬 실행
   - `pytest-mock`: Mocking 간소화

4. **단일 Runner로 모든 테스트 관리**
   - 단위, 통합, E2E 모두 `pytest` 명령어로 실행
   - 개발팀이 학습해야 할 도구 1개 (vs 여러 도구)

**비용-효과 분석:**
- 학습곡선: Django TestCase 사용자 → Pytest 전환 약 1시간
- 초기 투자: 2~3일
- 향후 절감: 테스트 코드 작성 시 월 3~5시간 (코드 중복 제거)

---

### 2. Test Data: Factory Boy

#### 선택 이유

**현재 상황:**
```python
# 수동으로 테스트 데이터 생성 (나쁜 예)
def test_user_login(db):
    user = User.objects.create_user(username='testuser', password='pass123')
    # 30개 테스트마다 이 코드 반복 = 중복 300줄
```

**Factory Boy 사용:**
```python
# factories.py
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f'user_{n}')

# 테스트에서 사용
def test_user_login(db):
    user = UserFactory()  # 한 줄, 자동 생성
```

**Factory Boy의 장점:**
1. **DRY 원칙** (Don't Repeat Yourself)
   - 테스트 데이터 정의 1번
   - 모든 테스트에서 재사용

2. **자동 필드 생성**
   - Faker 라이브러리 통합
   - 랜덤 데이터로 엣지 케이스 발견

3. **관계 객체 자동 생성**
   - User와 Profile의 관계가 있다면, `UserFactory`에서 자동 생성
   - N+1 쿼리 문제 조기 발견

4. **테스트 가독성 향상**
   - 의도가 명확함 (`UserFactory` = 사용자 테스트)
   - 테스트 데이터 관리 중앙화

**비용-효과:**
- 초기 투자: 팩토리 정의 1시간
- 향후 절감: 테스트 50개 이상 시 월 3~5시간
- **다음 분기에 추가하려면?** → 기존 테스트 300줄을 Fixture로 변환 필요 (매우 어려움)

---

### 3. E2E 테스트: Playwright

#### 선택 이유

**비교 대상: Selenium, Cypress**

| 항목 | Selenium | Playwright | Cypress |
|------|----------|-----------|---------|
| **실행 속도** | 느림 (상대값 1.0) | 빠름 (상대값 0.2) | 중간 (상대값 0.3) |
| **Flaky 테스트** | 많음 | 거의 없음 (Auto-wait) | 중간 |
| **Python 지원** | 있음 | 있음 | 없음 (JavaScript만) |
| **브라우저 지원** | Chrome, Firefox, Safari | Chrome, Firefox, Safari, Edge | Chrome 기반 |
| **모바일 테스트** | 어려움 | 지원 | 미지원 |
| **학습곡선** | 중간 | 낮음 | 높음 (JavaScript 필수) |

**Playwright 선택 근거:**

1. **가장 빠른 E2E 테스트 속도**
   - 내부적으로 DevTools Protocol 사용
   - Selenium의 WebDriver 대비 80% 빠름
   - E2E 테스트 10개 = 5분 vs Selenium 25분

2. **Auto-wait 기능** (Flaky 테스트 최소화)
   ```python
   # Selenium (Flaky - 타이밍 이슈 자주 발생)
   element = driver.find_element(By.ID, 'submit')
   time.sleep(1)  # 임의로 대기 (불안정)
   element.click()

   # Playwright (안정적)
   page.locator('#submit').click()  # 자동으로 요소가 클릭 가능할 때까지 대기
   ```

3. **Python 생태계 완벽 지원**
   - 백엔드 팀이 JavaScript 학습 불필요
   - Pytest와 완벽 통합

4. **최신 기술 선택** (미래 지향)
   - Google, Microsoft 등 주요 기업이 Playwright 지원
   - Selenium은 legacy 기술로 전환 중

**비용-효과:**
- Selenium 경험자 → Playwright 전환: 2~3시간 (문법이 유사)
- E2E 테스트 속도 향상으로 CI/CD 피드백 루프 단축

---

### 4. 테스트 구조: Unit + Integration + E2E

#### 왜 3가지 모두 필요한가?

```
┌─────────────────────────────────────────────┐
│ E2E Test (UI 포함 전체 흐름)                    │
│ 실행 시간: 초~분, 속도: 느림                      │
│ "사용자 관점에서 기능이 동작하는가?"                   │
└─────────────────────────────────────────────┘
         ↑
┌─────────────────────────────────────────────┐
│ Integration Test (다중 모듈 상호작용)              │
│ 실행 시간: 밀리초, 속도: 중간                      │
│ "CSV 파싱 → DB 저장 → API 응답이 일관성 있는가?"     │
└─────────────────────────────────────────────┘
         ↑
┌─────────────────────────────────────────────┐
│ Unit Test (함수/메서드 1개)                      │
│ 실행 시간: 밀리초, 속도: 빠름                      │
│ "format_chart_data() 함수가 올바른 값을 반환하는가?" │
└─────────────────────────────────────────────┘
```

**각 테스트 유형의 역할:**

| 테스트 | 범위 | 목적 | 개수 |
|--------|------|------|------|
| **Unit** | 함수/메서드 1개 | 비즈니스 로직 정확성 | 많음 (30~50개) |
| **Integration** | 다중 모듈 상호작용 | 모듈 간 데이터 흐름 검증 | 중간 (5~10개) |
| **E2E** | 전체 사용자 시나리오 | 실제 사용 가능 여부 | 적음 (3~5개) |

**예시: CSV 업로드 기능**

```
1. Unit Test:
   ✓ format_chart_data([...]) → {'labels': [...], 'data': [...]} 반환?

2. Integration Test:
   ✓ CSV 파싱 → DB 저장 → 조회 시 올바른 데이터?
   ✓ 중복 데이터는 업데이트되는가? (UPSERT)

3. E2E Test:
   ✓ 관리자가 CSV 업로드 → 일반 사용자가 대시보드에서 확인 가능?
```

**비용-효과:**
- Unit + Integration: 빠른 피드백 루프 (1초 이내)
- E2E: 느리지만 실제 사용성 검증 (필수지만 개수 제한)

---

## 📦 구현 계획 (상세)

### Phase 1: 기본 환경 구축 (1주일)

#### Step 1.1: 의존성 파일 생성

**파일: `requirements-dev.txt`**
```
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
pytest-mock==3.12.0
factory-boy==3.3.0
playwright==1.40.0
pytest-playwright==0.4.4
```

**설치 명령어:**
```bash
pip install -r requirements-dev.txt
playwright install  # 브라우저 바이너리 (약 5분)
```

#### Step 1.2: Pytest 설정

**파일: `pytest.ini`**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts = -v --tb=short -ra
testpaths = tests/
```

#### Step 1.3: 디렉토리 구조

```
tests/
├── __init__.py
├── conftest.py          # 전역 Fixture
├── factories.py         # 테스트 데이터 팩토리
├── unit/               # 단위 테스트
│   └── test_chart_adapter.py
├── integration/        # 통합 테스트
│   └── test_data_pipeline.py
└── e2e/               # E2E 테스트
    └── test_login.py
```

#### Step 1.4: 핵심 파일 작성

**파일: `tests/conftest.py`** (Fixture 중앙 관리)
```python
import pytest
from django.test import Client
from tests.factories import UserFactory

@pytest.fixture
def authenticated_user(db):
    """인증된 사용자"""
    return UserFactory(username='testuser', password='testpass123')

@pytest.fixture
def authenticated_client(db, authenticated_user):
    """로그인된 테스트 클라이언트"""
    client = Client()
    client.login(username='testuser', password='testpass123')
    return client
```

**파일: `tests/factories.py`** (테스트 데이터 생성)
```python
import factory
from django.contrib.auth.models import User
from apps.ingest.models import MetricRecord

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f'user_{n}')

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or 'testpass123')
        if create:
            obj.save()

class MetricRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MetricRecord
    year = 2024
    department = factory.Faker('word')
    metric_type = factory.Faker('word')
    metric_value = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
```

---

### Phase 2: 핵심 테스트 작성 (1주일)

#### Step 2.1: 단위 테스트 예제

**파일: `tests/unit/test_chart_adapter.py`**

먼저 구현할 함수:
```python
# apps/dashboard/utils/chart_adapter.py
def format_chart_data(records: list[dict]) -> dict:
    """레코드를 Chart.js 형식으로 변환"""
    if not records:
        return {"labels": [], "data": []}

    labels = [str(r.get("department", "N/A")) for r in records]
    data = [float(r.get("value", 0)) for r in records]

    return {"labels": labels, "data": data}
```

테스트 코드:
```python
import pytest
from apps.dashboard.utils.chart_adapter import format_chart_data

class TestChartAdapter:
    def test_format_chart_data_with_valid_records(self):
        """정상 데이터를 받았을 때 올바른 형식으로 변환"""
        # Arrange
        records = [
            {'department': 'Computer Science', 'value': 85.5},
            {'department': 'Philosophy', 'value': 62.1},
        ]

        # Act
        result = format_chart_data(records)

        # Assert
        assert len(result['labels']) == 2
        assert result['labels'][0] == 'Computer Science'
        assert float(result['data'][0]) == 85.5

    def test_format_chart_data_with_empty_list(self):
        """빈 리스트를 받았을 때 빈 결과 반환"""
        result = format_chart_data([])
        assert result == {"labels": [], "data": []}
```

**실행:**
```bash
pytest tests/unit/test_chart_adapter.py -v
```

---

#### Step 2.2: E2E 테스트 예제

**파일: `tests/e2e/test_login.py`**

```python
import pytest
from playwright.sync_api import Page, expect
from tests.factories import UserFactory

@pytest.mark.django_db
def test_user_can_login_and_see_welcome_message(page: Page, live_server):
    """사용자가 로그인하여 대시보드에 접근할 수 있는가?"""

    # Arrange: 테스트 사용자 생성
    user = UserFactory(username='testuser', password='testpass123')

    # Act: 로그인 페이지로 이동
    login_url = f"{live_server.url}/login/"
    page.goto(login_url)

    # 사용자명/비밀번호 입력
    page.get_by_label("Username").fill("testuser")
    page.get_by_label("Password").fill("testpass123")

    # 로그인 버튼 클릭
    page.get_by_role("button", name="Login").click()

    # Assert: 대시보드로 이동했는지 확인
    expect(page).to_have_url(f"{live_server.url}/dashboard/")

    # 환영 메시지 확인
    welcome = page.locator("text=Welcome, testuser!")
    expect(welcome).to_be_visible()
```

**실행:**
```bash
pytest tests/e2e/test_login.py -v
```

---

### Phase 3: CI/CD 및 최적화 (다음 분기)

- [ ] GitHub Actions 워크플로우 생성
- [ ] Playwright 브라우저 캐싱
- [ ] 테스트 병렬 실행 (pytest-xdist)
- [ ] 커버리지 리포트 (pytest-cov)
- [ ] PostgreSQL 테스트 환경 (pytest-postgresql)

---

## 📝 추가 자료

### 테스트 실행 명령어 (팀용)

```bash
# 모든 테스트 실행
pytest

# 단위 테스트만
pytest tests/unit/

# E2E 테스트만
pytest tests/e2e/

# 커버리지 리포트
pytest --cov=apps

# 특정 테스트만
pytest tests/unit/test_chart_adapter.py::TestChartAdapter::test_format_chart_data_with_valid_records
```

### 프로젝트 상황에 맞춘 설정

**현재 프로젝트 상태:**
- Django 5.2.7 ✅
- DRF 설치됨 ✅
- MetricRecord 모델 구현됨 ✅
- DashboardView 구현됨 ✅
- **테스트 환경 미구성 ← 본 제안서의 목표**

**설정 파일 상태:**
- `config/settings.py`: INSTALLED_APPS에 'apps.dashboard', 'apps.ingest' 등록됨 ✅
- `config/urls.py`: 로그인/로그아웃 URL 이미 설정됨 ✅
- 템플릿: base.html, login.html, dashboard/index.html 모두 있음 ✅

**따라서:**
- `pytest.ini` 1개 추가하면 즉시 테스트 가능
- 기존 구조 변경 최소화

---

## 🎬 Action Items

### 이번 주 (Week 1)
- [ ] 팀 미팅에서 제안서 검토 (30분)
- [ ] `requirements-dev.txt` 생성 및 설치 (15분)
- [ ] `pytest.ini`, `conftest.py`, `factories.py` 작성 (1시간)
- [ ] 디렉토리 구조 생성 (10분)
- [ ] 팀원 온보딩: Pytest/Factory Boy 기본 사용법 (30분)

### 다음주 (Week 2)
- [ ] Unit Test 예제 `test_chart_adapter.py` 작성 (2시간)
- [ ] E2E Test 예제 `test_login.py` 작성 (2시간)
- [ ] 모든 테스트 성공 확인 (30분)
- [ ] 팀 코드 리뷰 (1시간)

### 기대 결과
- 테스트 작성 능력 갖춘 개발팀
- 향후 모든 새 기능은 테스트와 함께 개발
- 버그 심각도 감소, 배포 자신감 향상

---

