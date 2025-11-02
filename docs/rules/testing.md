# Django 테스트 규칙

## 테스트 파일 구조

```
tests/
├── __init__.py
├── conftest.py              # pytest 설정
├── ingest/
│   ├── test_services.py     # 파싱 로직
│   └── test_admin.py        # Admin 액션
└── dashboard/
    ├── test_api.py          # API 뷰
    └── test_models.py       # 모델 로직
```

## 기본 테스트 패턴

```python
import pytest
from django.test import TestCase
from apps.ingest.services import parse_excel_defensively

# Unit Test
def test_parse_excel_missing_column():
    """필수 컬럼 누락 시 에러 반환"""
    data, errors = parse_excel_defensively("invalid.xlsx")
    assert len(errors) > 0
    assert data == []

def test_parse_excel_valid():
    """유효한 엑셀 파싱"""
    data, errors = parse_excel_defensively("valid.xlsx")
    assert len(errors) == 0
    assert len(data) > 0

# Integration Test (Django TestCase)
class ChartDataAPITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """한 번만 실행 (빠름)"""
        cls.user = User.objects.create_user('test', 'test@test.com', 'pass')

    def setUp(self):
        """매 테스트마다 실행"""
        self.client.login(username='test', password='pass')

    def test_chart_data_api_authenticated(self):
        """인증된 사용자만 조회 가능"""
        response = self.client.get('/api/dashboard/chart-data/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_chart_data_api_unauthenticated(self):
        """미인증 사용자 거부"""
        self.client.logout()
        response = self.client.get('/api/dashboard/chart-data/')
        self.assertEqual(response.status_code, 403)
```

## 테스트 실행

```bash
# 전체 테스트
pytest

# 특정 파일만
pytest tests/ingest/test_services.py

# 특정 테스트만
pytest tests/ingest/test_services.py::test_parse_excel_valid

# 커버리지 확인
pytest --cov=apps
```

## Mock 패턴

```python
from unittest.mock import patch, MagicMock

def test_parse_with_mock_file():
    """파일 시스템 없이 테스트"""
    with patch('builtins.open', MagicMock()):
        result = parse_excel("fake.xlsx")
        assert result is not None
```

## 빠른 테스트 팁

- `setUpTestData()`: 공유 데이터 (1회)
- `setUp()`: 각 테스트마다 실행
- `--reuse-db`: 테스트 DB 재사용 (빠름)
- 필요한 데이터만 생성 (최소한)
