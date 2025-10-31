# MVP 테스트 환경 구축 가이드

**작성자:** CTO
**날짜:** 2025-10-31
**목표:** MVP 프로젝트의 안정성 확보 및 신속한 개발 반복을 위한 단위/E2E/통합 테스트 환경 구축

---

## 1. 개요 및 추진 철학

### 1.1 전략

이 문서는 YC 배치 스타트업 초기 단계의 코드 안정성을 확보하면서도 **신속한 개발 속도를 유지**하기 위한 테스트 환경 구축 방안을 제시합니다.

**핵심 원칙:**
- ✅ **빠른 시작:** 1주일 안에 테스트 환경 구성 가능
- ✅ **중간계층 확보:** 단위 테스트(Unit) ↔ E2E 테스트 사이의 **통합 테스트(Integration)**를 중심으로 설계
- ✅ **확장성 제일:** 미래의 비동기 작업(Celery), 외부 API 연동을 대비한 아키텍처 설계
- ✅ **기술 부채 최소화:** Factory Boy, pytest-mock 등 장기 효율성을 위한 최소 투자

### 1.2 기술 스택 선택 근거

| 구분 | 선택 기술 | 이유 |
|------|---------|------|
| **Test Runner** | Pytest + pytest-django | Django의 기본 TestCase보다 간결한 문법과 강력한 Fixture 모델을 제공. 단위/E2E/통합 테스트를 하나의 Runner로 관리하여 팀의 개발 경험 통합 |
| **Unit Testing** | Django TestCase + unittest.mock | Django ORM 테스트에 최적화. 각 테스트마다 자동 트랜잭션 격리로 독립성 보장 |
| **Integration Test** | Django TestCase + pytest | 서비스 레이어의 다중 모듈 상호작용 검증. CSV 파싱 → DB 저장 → API 응답까지의 흐름 테스트 |
| **E2E Testing** | Playwright + pytest-playwright | 최신 브라우저 자동화 도구. 자동 대기 기능으로 Flaky 테스트 최소화. Selenium보다 80% 빠름 |
| **Test Data** | Factory Boy | 테스트마다 복잡한 데이터 설정을 자동화. 50개 이상의 테스트에서 유지보수 시간 월 3~5시간 절감 |
| **Mocking** | pytest-mock | unittest.mock보다 직관적인 API. Fixture와 자연스럽게 통합 |
| **Coverage** | Coverage.py + pytest-cov | 테스트가 검증하는 코드 비율 측정. 점진적인 커버리지 목표 설정 가능 |

---

## 2. 현재 프로젝트 상태 분석

### 2.1 기존 구조
```
project_root/
├── apps/
│   ├── ingest/           # 데이터 입력 담당
│   │   ├── models.py     # (비어있음)
│   │   ├── services.py   # (비어있음) ← 파싱 로직이 들어갈 위치
│   │   ├── views.py      # (비어있음)
│   │   └── tests.py      # (기본 파일)
│   │
│   └── dashboard/        # 데이터 출력 담당
│       ├── models.py     # (비어있음)
│       ├── views.py      # DashboardView 있음
│       ├── utils/
│       │   └── chart_adapter.py  # (비어있음)
│       └── tests.py      # (기본 파일)
│
├── config/
│   ├── settings.py       # ✅ 이미 INSTALLED_APPS 설정됨
│   └── urls.py           # ✅ 기본 경로 설정됨
│
├── templates/
│   ├── base.html
│   ├── dashboard/index.html
│   └── registration/login.html
│
└── requirements.txt      # 많은 의존성 포함 (정리 필요)
```

### 2.2 현재 설정 상태
- ✅ Django 5.2.7, DRF 설치됨
- ✅ 로그인 URL 구성 완료
- ✅ MetricRecord 모델 구현됨
- ✅ DashboardView 구현됨
- ⚠️ 테스트 환경 미구성
- ⚠️ requirements.txt가 과도하게 많은 라이브러리 포함

---

## 3. Phase 1: 기본 환경 구축 (이번 주)

### 3.1 Step 1: 의존성 정리 및 추가

**목표:** 테스트 환경에 필요한 라이브러리를 명확하게 분리

#### 현재 requirements.txt 정리
```bash
# 현재 requirements.txt를 새 파일로 정리
pip install pipdeptree  # 의존성 트리 확인
pipdeptree
```

기존 requirements.txt에서 **최소 필수 항목**만 유지:
```
Django==5.2.7
djangorestframework==3.16.1
pandas==2.3.3
python-dotenv==1.1.1
psycopg2-binary==2.9.11
```

#### requirements-dev.txt 생성
```
# Development & Testing dependencies
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
pytest-mock==3.12.0
factory-boy==3.3.0
playwright==1.40.0
pytest-playwright==0.4.4
```

#### 설치 명령어
```bash
# 개발 환경 설정 (처음 1회)
pip install -r requirements.txt
pip install -r requirements-dev.txt
playwright install  # Playwright 브라우저 설치 (약 5분)

# CI 환경에서는 requirements-dev.txt만 설치 가능
```

### 3.2 Step 2: pytest 설정

#### pytest.ini 생성 (프로젝트 루트)
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts = -v --tb=short -ra
testpaths = tests/
```

**설명:**
- `DJANGO_SETTINGS_MODULE`: Django 설정 파일 경로
- `addopts`:
  - `-v`: 자세한 출력 (테스트 이름 표시)
  - `--tb=short`: 스택트레이스를 간결하게 표시
  - `-ra`: 테스트 실패 요약 출력
- `testpaths`: 테스트 파일을 찾을 디렉토리

### 3.3 Step 3: 테스트 디렉토리 구조 생성

```
tests/
├── __init__.py               # Python 패키지 표시
├── conftest.py               # 전역 Fixture 정의
├── factories.py              # Factory Boy 모델 정의
│
├── unit/                     # 단위 테스트
│   ├── __init__.py
│   ├── test_chart_adapter.py # dashboard.utils.chart_adapter 테스트
│   └── test_ingest_services.py  # ingest.services 테스트
│
├── integration/              # 통합 테스트
│   ├── __init__.py
│   └── test_data_pipeline.py # CSV 파싱 → DB 저장 → API 응답 전체 흐름
│
└── e2e/                      # E2E 테스트
    ├── __init__.py
    └── test_user_flows.py    # 사용자 시나리오 (로그인, 대시보드 접근)
```

#### 디렉토리 생성 명령어
```bash
mkdir -p tests/unit tests/integration tests/e2e
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py tests/e2e/__init__.py
touch tests/conftest.py tests/factories.py
```

---

## 4. Phase 2: 핵심 테스트 자산 구현 (다음 주)

### 4.1 factories.py: 테스트 데이터 생성기

**파일:** `tests/factories.py`

```python
import factory
from django.contrib.auth.models import User
from apps.ingest.models import MetricRecord


class UserFactory(factory.django.DjangoModelFactory):
    """테스트용 사용자 생성 팩토리"""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """비밀번호 설정 (평문으로 저장, 테스트용)"""
        password = extracted or 'testpass123'
        obj.set_password(password)
        if create:
            obj.save()


class MetricRecordFactory(factory.django.DjangoModelFactory):
    """테스트용 성과 지표 레코드 생성"""

    class Meta:
        model = MetricRecord

    year = factory.Faker('year', min_value=2020, max_value=2025)
    department = factory.Faker('word')  # 임시: 실제는 선택지 제한 필요
    metric_type = factory.Faker('word')
    metric_value = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
```

**사용 예시:**
```python
def test_something(db):
    # 사용자 1명 생성
    user = UserFactory()
    assert user.username.startswith('user_')

    # 사용자 3명 생성
    users = UserFactory.create_batch(3)
    assert len(users) == 3

    # 메트릭 레코드 생성
    metric = MetricRecordFactory(year=2024, department='CS')
    assert metric.year == 2024
```

### 4.2 conftest.py: 전역 Fixture 정의

**파일:** `tests/conftest.py`

```python
import pytest
from django.test import Client
from tests.factories import UserFactory, MetricRecordFactory


@pytest.fixture
def authenticated_user(db):
    """인증된 사용자 객체 반환"""
    user = UserFactory(username='testuser', password='testpass123')
    return user


@pytest.fixture
def authenticated_client(db, authenticated_user):
    """인증된 Django 테스트 클라이언트 반환

    Usage:
        def test_dashboard(authenticated_client):
            response = authenticated_client.get('/dashboard/')
            assert response.status_code == 200
    """
    client = Client()
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def sample_metric_records(db):
    """샘플 메트릭 레코드 생성

    Usage:
        def test_with_metrics(sample_metric_records):
            assert MetricRecord.objects.count() == 5
    """
    return MetricRecordFactory.create_batch(
        5,
        year=2024,
        department='Computer Science'
    )
```

**Fixture 사용 패턴:**
```python
# Fixture 매개변수로 주입
def test_login_required(db):
    """단순히 db 접근만 필요"""
    ...

def test_with_user(authenticated_user):
    """인증된 사용자 필요"""
    assert authenticated_user.is_active

def test_with_client(authenticated_client):
    """HTTP 요청 필요"""
    response = authenticated_client.get('/dashboard/')
    assert response.status_code == 200

def test_with_metrics(sample_metric_records):
    """샘플 데이터 필요"""
    assert len(sample_metric_records) == 5
```

---

## 5. Phase 3: 테스트 작성 및 예제

### 5.1 단위 테스트 예제

**파일:** `tests/unit/test_chart_adapter.py`

```python
import pytest
from decimal import Decimal
from apps.dashboard.utils.chart_adapter import format_chart_data


class TestChartAdapter:
    """차트 데이터 형식 변환 함수 테스트"""

    def test_format_chart_data_with_valid_records(self):
        """정상적인 레코드를 받았을 때 올바른 형식으로 변환"""
        # Arrange
        records = [
            {'department': 'Computer Science', 'value': Decimal('85.50')},
            {'department': 'Philosophy', 'value': Decimal('62.10')},
        ]

        # Act
        result = format_chart_data(records)

        # Assert
        assert 'labels' in result
        assert 'data' in result
        assert len(result['labels']) == 2
        assert result['labels'][0] == 'Computer Science'
        assert float(result['data'][0]) == 85.50

    def test_format_chart_data_with_empty_list(self):
        """빈 리스트를 받았을 때 빈 결과 반환"""
        # Act
        result = format_chart_data([])

        # Assert
        assert result == {'labels': [], 'data': []}

    def test_format_chart_data_with_missing_fields(self):
        """필드가 누락되었을 때 기본값 사용"""
        # Arrange
        records = [{'value': Decimal('100')}]  # 'department' 필드 누락

        # Act
        result = format_chart_data(records)

        # Assert
        assert result['labels'][0] == 'N/A'
        assert float(result['data'][0]) == 100.0
```

**앞서 구현 필요:** `apps/dashboard/utils/chart_adapter.py`

```python
from decimal import Decimal
from typing import List, Dict, Any


def format_chart_data(records: List[Dict[str, Any]]) -> Dict[str, List]:
    """
    주어진 레코드 리스트를 차트 라이브러리가 요구하는 형식으로 변환합니다.

    Args:
        records: {'department': str, 'value': Decimal} 형태의 딕셔너리 리스트

    Returns:
        {'labels': [...], 'data': [...]} 형태의 차트 데이터

    Example:
        >>> records = [{'department': 'CS', 'value': 85}]
        >>> format_chart_data(records)
        {'labels': ['CS'], 'data': [85]}
    """
    if not records:
        return {"labels": [], "data": []}

    labels = [str(r.get("department", "N/A")) for r in records]
    data = [float(r.get("value", 0)) for r in records]

    return {"labels": labels, "data": data}
```

### 5.2 통합 테스트 예제 (가장 중요!)

**파일:** `tests/integration/test_data_pipeline.py`

```python
import pytest
import io
import csv
from decimal import Decimal
from django.test import TestCase
from apps.ingest.services import parse_and_store_metrics
from apps.ingest.models import MetricRecord
from apps.dashboard.utils.chart_adapter import format_chart_data


@pytest.mark.django_db
class TestDataPipeline:
    """CSV 파싱부터 차트 표시까지의 전체 데이터 흐름 검증"""

    def test_csv_parsing_to_chart_display_flow(self):
        """
        실제 시나리오: CSV 파일 → 데이터 파싱 → DB 저장 → 차트 형식 변환

        이 테스트는 다음을 검증합니다:
        1. CSV가 올바르게 파싱되는가?
        2. 파싱된 데이터가 DB에 저장되는가?
        3. DB에서 조회한 데이터를 차트 형식으로 변환할 수 있는가?
        """
        # Arrange: CSV 파일 시뮬레이션
        csv_content = """year,department,metric_type,metric_value
2024,Computer Science,paper_count,15
2024,Computer Science,graduation_rate,85.5
2024,Philosophy,paper_count,5
2024,Philosophy,graduation_rate,62.1
"""
        csv_file = io.StringIO(csv_content)

        # Act 1: CSV 파싱 및 DB 저장
        record_count = parse_and_store_metrics(csv_file)

        # Assert 1: 레코드 저장 확인
        assert record_count == 4
        assert MetricRecord.objects.count() == 4

        # Act 2: DB에서 조회 및 차트 형식 변환
        metrics = MetricRecord.objects.filter(year=2024).values('department', 'metric_value')
        chart_data = format_chart_data(list(metrics))

        # Assert 2: 차트 형식 검증
        assert len(chart_data['labels']) > 0
        assert len(chart_data['data']) == len(chart_data['labels'])
        assert 'Computer Science' in chart_data['labels']

    def test_duplicate_metric_records_are_updated(self):
        """
        동일한 (year, department, metric_type)의 레코드는 업데이트되어야 함
        (UPSERT 패턴 검증)
        """
        # Arrange
        csv_content = """year,department,metric_type,metric_value
2024,Computer Science,paper_count,15
2024,Computer Science,paper_count,20
"""
        csv_file = io.StringIO(csv_content)

        # Act
        record_count = parse_and_store_metrics(csv_file)

        # Assert: 2개가 아니라 1개의 레코드로 업데이트되어야 함
        assert record_count == 2  # 파싱된 개수
        assert MetricRecord.objects.count() == 1  # 실제 DB 레코드 개수

        record = MetricRecord.objects.first()
        assert record.metric_value == Decimal('20')  # 최신 값으로 업데이트됨
```

**앞서 구현 필요:** `apps/ingest/services.py`

```python
import csv
import io
from decimal import Decimal
from typing import Union, IO
from django.core.exceptions import ValidationError
from apps.ingest.models import MetricRecord


def parse_and_store_metrics(csv_file: Union[str, IO]) -> int:
    """
    CSV 파일을 파싱하여 MetricRecord 테이블에 저장합니다.
    (UPSERT 패턴: 동일한 year, department, metric_type는 업데이트)

    Args:
        csv_file: 파일 경로(str) 또는 파일 객체(IO)

    Returns:
        처리된 레코드 개수

    Raises:
        ValidationError: 파일 형식이 잘못되었을 때
    """
    if isinstance(csv_file, str):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = list(reader)
    else:
        reader = csv.DictReader(csv_file)
        records = list(reader)

    if not records:
        raise ValidationError("CSV 파일이 비어있습니다.")

    created_count = 0

    for row in records:
        try:
            metric, created = MetricRecord.objects.update_or_create(
                year=int(row['year']),
                department=row['department'],
                metric_type=row['metric_type'],
                defaults={
                    'metric_value': Decimal(row['metric_value'])
                }
            )
            created_count += 1
        except (KeyError, ValueError, TypeError) as e:
            raise ValidationError(f"CSV 파일의 행을 파싱할 수 없습니다: {row}\n오류: {e}")

    return created_count
```

### 5.3 E2E 테스트 예제

**파일:** `tests/e2e/test_user_flows.py`

```python
import pytest
from django.test import Client
from playwright.sync_api import Page, expect
from tests.factories import UserFactory


@pytest.mark.django_db
def test_login_page_loads(live_server):
    """로그인 페이지가 올바르게 로드되는지 검증"""
    client = Client()
    response = client.get('/login/')

    assert response.status_code == 200
    assert b'Login' in response.content
    assert b'username' in response.content
    assert b'password' in response.content


@pytest.mark.django_db
def test_user_can_login_and_access_dashboard(page: Page, live_server):
    """
    사용자가 로그인하여 대시보드에 접근할 수 있는지 검증

    Playwright를 사용한 실제 사용자 흐름:
    1. 로그인 페이지 접근
    2. 사용자명/비밀번호 입력
    3. 로그인 버튼 클릭
    4. 대시보드 페이지로 리디렉션 확인
    5. 대시보드 콘텐츠 표시 확인
    """
    # Arrange: 테스트 사용자 생성
    user = UserFactory(username='testuser', password='testpass123')

    # Act: 로그인 페이지로 이동
    login_url = f"{live_server.url}/login/"
    page.goto(login_url)

    # 사용자명 입력
    page.get_by_label("Username").fill("testuser")

    # 비밀번호 입력
    page.get_by_label("Password").fill("testpass123")

    # 로그인 버튼 클릭
    page.get_by_role("button", name="Login").click()

    # Assert: 대시보드로 리디렉션되었는지 확인
    expect(page).to_have_url(f"{live_server.url}/dashboard/")

    # 대시보드 콘텐츠 확인
    welcome_message = page.locator("text=Dashboard")
    expect(welcome_message).to_be_visible()

    welcome_user = page.locator("text=Welcome, testuser!")
    expect(welcome_user).to_be_visible()


@pytest.mark.django_db
def test_login_failure_with_wrong_password(page: Page, live_server):
    """
    잘못된 비밀번호로 로그인 시도 시 오류 메시지 표시
    """
    # Arrange
    user = UserFactory(username='testuser', password='testpass123')

    # Act
    login_url = f"{live_server.url}/login/"
    page.goto(login_url)

    page.get_by_label("Username").fill("testuser")
    page.get_by_label("Password").fill("wrongpassword")
    page.get_by_role("button", name="Login").click()

    # Assert: 오류 메시지가 표시되고 로그인 페이지에 남아있음
    error_message = page.locator("text=didn't match")
    expect(error_message).to_be_visible()

    # URL이 여전히 로그인 페이지임을 확인
    expect(page).to_have_url(f"{live_server.url}/login/")


@pytest.mark.django_db
def test_unauthenticated_user_redirected_to_login(page: Page, live_server):
    """
    인증되지 않은 사용자가 대시보드에 접근하면 로그인 페이지로 리디렉션
    """
    dashboard_url = f"{live_server.url}/dashboard/"
    page.goto(dashboard_url)

    # 로그인 페이지로 리디렉션되어야 함
    expect(page).to_have_url(f"{live_server.url}/login/")
```

---

## 6. 테스트 실행 가이드

### 6.1 기본 실행 명령어

```bash
# 모든 테스트 실행
pytest

# 특정 디렉토리의 테스트만 실행
pytest tests/unit/          # 단위 테스트만
pytest tests/integration/   # 통합 테스트만
pytest tests/e2e/          # E2E 테스트만

# 특정 파일의 테스트 실행
pytest tests/unit/test_chart_adapter.py

# 특정 테스트 클래스/함수 실행
pytest tests/unit/test_chart_adapter.py::TestChartAdapter::test_format_chart_data_with_valid_records

# verbose 모드 (테스트 이름 자세히 표시)
pytest -v

# 코드 커버리지 확인
pytest --cov=apps --cov-report=html  # HTML 리포트 생성
# htmlcov/index.html 에서 확인

# 특정 커버리지 레벨 이상일 때만 성공
pytest --cov=apps --cov-fail-under=70  # 70% 이상 커버리지 필요
```

### 6.2 CI/CD에서 자주 사용할 명령어

```bash
# 빠른 테스트 (단위 + 통합만, E2E 제외)
pytest tests/unit/ tests/integration/ -v

# 모든 테스트 + 커버리지 리포트
pytest --cov=apps --cov-report=term-missing

# 병렬 실행 (pytest-xdist 설치 필요, 다음 분기)
pytest -n auto

# 테스트 실패 시 첫 번째 실패에서 멈춤
pytest -x

# 마지막 실패한 테스트만 실행
pytest --lf
```

---

## 7. 테스트 작성 Best Practices

### 7.1 Arrange-Act-Assert (AAA) 패턴

```python
def test_something(db):
    # Arrange: 테스트 데이터 준비
    user = UserFactory(username='test')

    # Act: 테스트할 기능 실행
    result = some_function(user)

    # Assert: 결과 검증
    assert result is not None
```

### 7.2 테스트 이름 규칙

```python
# ❌ 나쁜 예
def test_1():
    pass

def test_user():
    pass

# ✅ 좋은 예
def test_format_chart_data_with_valid_records():
    """무엇을 테스트하는가를 명확히 표현"""
    pass

def test_login_failure_with_wrong_password():
    """실패 케이스도 포함"""
    pass
```

### 7.3 한 가지만 테스트 (단일 책임 원칙)

```python
# ❌ 나쁜 예: 여러 개념을 한번에 테스트
def test_user_login_and_dashboard_access(page: Page, live_server):
    # 로그인 + 대시보드 + 데이터 표시 등 모든 것을 테스트
    pass

# ✅ 좋은 예: 각각 분리
def test_user_can_login(page: Page, live_server):
    # 로그인만 테스트
    pass

def test_dashboard_is_accessible_to_authenticated_users(authenticated_client):
    # 접근 권한만 테스트
    pass
```

### 7.4 Mock 사용 예시

```python
from unittest.mock import patch, MagicMock
import pytest

@pytest.mark.django_db
def test_parse_large_csv_file(mocker):
    """외부 파일 시스템 호출을 Mock으로 대체"""
    # Mock 설정
    mock_file = mocker.patch('builtins.open', create=True)
    mock_file.return_value.__enter__.return_value.readlines.return_value = [
        "year,department,metric_type,metric_value\n",
        "2024,CS,paper_count,15\n"
    ]

    # 테스트 실행
    result = parse_and_store_metrics('fake_file.csv')

    # 검증
    assert result == 1
    mock_file.assert_called_once_with('fake_file.csv', 'r', encoding='utf-8')
```

---

## 8. 장기 계획 (Next Quarter)

### 8.1 다음 분기 우선순위 (별도 백로그로 관리)

**높음 (1-2주):**
- [ ] GitHub Actions CI 파이프라인 구축
  - 매 push마다 자동으로 pytest 실행
  - 커버리지 리포트 생성
- [ ] Playwright 브라우저 캐싱
  - CI 환경에서 브라우저 재설치 시간 단축

**중간 (3-4주):**
- [ ] pytest-xdist를 이용한 병렬 테스트 실행
  - E2E 테스트 실행 시간 단축 (10분 → 3분)
- [ ] 데이터베이스 테스트 PostgreSQL로 변경
  - `pytest-postgresql` 도입
  - 프로덕션 환경과 동일한 DB로 테스트

**낮음 (다음 월):**
- [ ] 외부 API 호출 Mock 라이브러리 (responses, vcr.py)
- [ ] 비동기 작업 테스트 (Celery, pytest-asyncio)
- [ ] 성능 테스트 (locust, pytest-benchmark)

### 8.2 기술 부채 관리

```markdown
# 테스트 관련 기술 부채 추적

## 현재 (MVP 단계)
- SQLite 인메모리 DB 사용
- Django TestCase의 자동 트랜잭션 격리 활용
- E2E 테스트의 전체 브라우저 스택 테스트

## 위험 요소
- [ ] PostgreSQL의 배열 타입, JSONB 차이 미테스트
- [ ] 실제 파일 시스템 I/O 테스트 부족
- [ ] 외부 API 의존성 미처리

## 해결 기한
- DB 테스트: 기능이 PostgreSQL에 의존하는 시점
- API 테스트: 외부 서비스 연동 시점
```

---

## 9. FAQ

### Q1: "단위 테스트와 통합 테스트가 정확히 어떻게 다른가요?"

**A:** 다음과 같이 구분합니다:

| 구분 | 범위 | 예시 | 속도 |
|------|------|------|------|
| **Unit** | 함수/메서드 1개 | `format_chart_data()` 함수만 테스트 | 빠름 (밀리초) |
| **Integration** | 여러 모듈의 상호작용 | CSV 파싱 + DB 저장 + 차트 변환 전체 | 중간 (초) |
| **E2E** | 전체 사용자 시나리오 | 로그인 → 대시보드 접근 → 데이터 확인 | 느림 (초~분) |

### Q2: "테스트 커버리지는 몇 %를 목표로 해야 하나요?"

**A:** MVP 단계에서는 다음을 권장합니다:

- **비즈니스 로직 (services.py, utils/):** 70~80% (필수)
- **모델:** 50% (기본 CRUD는 Django가 보장)
- **뷰/API:** 50% (통합 테스트로 커버)
- **전체:** 60% 이상

### Q3: "테스트 작성이 개발을 느리게 하지 않을까요?"

**A:** 초기 2주는 3~5% 느릴 수 있지만:

- **3주차부터:** 회귀 버그 감소로 수정 시간 절감
- **2개월차:** 누적 개발 속도가 테스트 없는 팀보다 30% 빠름
- **6개월차:** 대규모 리팩토링 시 테스트가 있는 팀이 10배 빠름

---

## 10. 체크리스트

### Phase 1 완료 기준 (이번 주)
- [ ] `requirements-dev.txt` 생성 및 설치
- [ ] `pytest.ini` 생성
- [ ] `tests/` 디렉토리 구조 생성
- [ ] `tests/conftest.py` 작성
- [ ] `tests/factories.py` 작성
- [ ] `pytest` 기본 실행 확인 (`pytest --co` 명령어로 테스트 발견 확인)

### Phase 2 완료 기준 (다음 주)
- [ ] `apps/dashboard/utils/chart_adapter.py` 구현
- [ ] `apps/ingest/services.py` 구현
- [ ] `tests/unit/test_chart_adapter.py` 작성 (3개 테스트 이상)
- [ ] `tests/integration/test_data_pipeline.py` 작성 (2개 테스트 이상)
- [ ] `tests/e2e/test_user_flows.py` 작성 (3개 테스트 이상)
- [ ] 전체 테스트 성공 확인 (`pytest -v`)
- [ ] 커버리지 60% 이상 달성 (`pytest --cov=apps`)

### Phase 3 (그 다음주)
- [ ] `apps/ingest/views.py`에서 CSV 업로드 엔드포인트 구현
- [ ] E2E 테스트 확장: "CSV 업로드 → 대시보드 반영" 시나리오
- [ ] GitHub Actions 워크플로우 초안 작성

---

## 11. 참고 자료

- [Pytest 공식 문서](https://docs.pytest.org/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
- [Playwright Python](https://playwright.dev/python/)
- [Django Testing](https://docs.djangoproject.com/en/5.2/topics/testing/)

---

## 12. 문서 이력

| 버전 | 날짜 | 변경사항 |
|------|------|---------|
| v1.0 | 2025-10-31 | 초기 문서 작성 (Phase 1, 2, 3 계획) |

---

**질문이나 피드백:** 팀 Slack #tech-strategy 채널에서 논의

