# 대학교 내부 데이터 시각화 대시보드 - 개발 규칙

## 프로젝트 개요

- **목표**: Ecount 엑셀 파일 → 파싱 → DB 저장 → 차트 시각화 MVP
- **사용자 수준**: 1년차 개발자 학습 프로젝트
- **우선순위**: 최소 복잡도 > 유지보수 > 확장성(문서화만)
- **배포**: Django 동기 처리 (Celery 비동기는 기술부채로 문서화만)

---

## 핵심 기술 스택

```
Backend:      Django 5.x + Django REST Framework (DRF)
Database:     PostgreSQL on Supabase (마이그레이션 관리)
Parser:       pandas (방어적 파싱)
Frontend:     Django Template + Bootstrap 5 + Chart.js
Authentication: Django Session (기본 인증)
```

---

## 아키텍처 (App-based)

```
project_root/
├── apps/
│   ├── ingest/                    # 데이터 입력 담당
│   │   ├── models.py              # 업로드 파일, 파싱 결과 모델
│   │   ├── admin.py               # Admin 액션: 파일 업로드, 파싱, Upsert
│   │   ├── services.py            # pandas 파싱 로직 (방어적 파싱)
│   │   ├── serializers.py         # DRF 시리얼라이저 (유효성 검사)
│   │   └── views.py               # 필요시 API 뷰
│   │
│   └── dashboard/                 # 데이터 출력 담당
│       ├── models.py              # 차트 데이터 모델 (읽기용)
│       ├── views.py               # Django View (템플릿 렌더링)
│       ├── api_views.py           # DRF ViewSet (/api/dashboard/chart-data/)
│       ├── serializers.py         # 응답 시리얼라이저
│       ├── templates/
│       │   └── dashboard.html     # Chart.js 차트 렌더링
│       └── filters.py             # 학과별, 연도별 필터링 로직
│
├── config/                        # Django 프로젝트 설정
│   ├── settings.py               # 환경별 설정, 미들웨어, 앱 등록
│   ├── urls.py                   # URL 라우팅
│   └── wsgi.py                   # WSGI 진입점
│
├── static/                        # CSS, JS (Bootstrap, Chart.js)
├── manage.py                      # Django 관리 명령
└── requirements.txt               # Python 의존성
```

---

## 필수 원칙 (MUST)

### 1. 엑셀 파싱은 반드시 방어적으로
```python
# apps/ingest/services.py

def parse_excel_defensively(file_path: str) -> tuple[dict, list[str]]:
    """
    방어적 파싱: 필수 컬럼, 타입 캐스팅, 에러 로깅

    Returns:
        (parsed_data, error_messages)
    """
    required_columns = ['학과', '연도', '지표값']
    df = pd.read_excel(file_path)

    errors = []

    # 1. 필수 컬럼 검증
    missing = set(required_columns) - set(df.columns)
    if missing:
        errors.append(f"필수 컬럼 누락: {missing}")
        return {}, errors

    # 2. 빈 행 제거
    df = df.dropna(how='all')

    # 3. 타입 캐스팅 (에러 처리)
    try:
        df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
        df['지표값'] = pd.to_numeric(df['지표값'], errors='coerce')
    except Exception as e:
        errors.append(f"타입 캐스팅 오류: {str(e)}")
        return {}, errors

    # 4. 데이터 유효성 검사
    if df['지표값'].isna().any():
        errors.append("유효하지 않은 지표값 존재")

    if errors:
        return {}, errors

    return df.to_dict('records'), []
```

### 2. Django Admin으로 파일 업로드 및 Upsert
```python
# apps/ingest/admin.py

@admin.action(description="선택된 파일 파싱 및 DB 저장")
def parse_and_save(modeladmin, request, queryset):
    for upload in queryset:
        try:
            data, errors = parse_excel_defensively(upload.file.path)
            if errors:
                messages.error(request, f"파싱 실패: {errors}")
                continue

            # Upsert (학과, 연도 기준)
            for row in data:
                obj, created = ChartData.objects.update_or_create(
                    department=row['학과'],
                    year=row['연도'],
                    defaults={'value': row['지표값']}
                )
            messages.success(request, f"{len(data)}개 레코드 저장 완료")
        except Exception as e:
            messages.error(request, f"오류: {str(e)}")
```

### 3. DRF API는 Chart.js 포맷으로 응답
```python
# apps/dashboard/api_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class ChartDataAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        /api/dashboard/chart-data/

        Query Params:
        - department: 학과명 (선택)
        - year: 연도 (선택)

        Response:
        {
            "success": true,
            "data": {
                "labels": ["Q1", "Q2", "Q3", "Q4"],
                "datasets": [
                    {
                        "label": "학과A",
                        "data": [10, 20, 15, 25],
                        "backgroundColor": "rgba(75, 192, 192, 0.5)"
                    }
                ]
            }
        }
        """
        department = request.query_params.get('department')
        year = request.query_params.get('year')

        queryset = ChartData.objects.all()

        if department:
            queryset = queryset.filter(department=department)
        if year:
            queryset = queryset.filter(year=year)

        # 학과별로 그룹화해서 Chart.js 포맷으로 변환
        data = self._format_for_chartjs(queryset)

        return Response({
            "success": True,
            "data": data
        })

    def _format_for_chartjs(self, queryset):
        # 데이터 그룹화 및 포맷팅 로직
        pass
```

### 4. DRF 응답 포맷 통일
```python
# apps/dashboard/serializers.py

from rest_framework import serializers

class ChartDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartData
        fields = ['id', 'department', 'year', 'value', 'created_at']
        read_only_fields = ['created_at']

    def validate_year(self, value):
        if not (1900 <= value <= 2100):
            raise serializers.ValidationError("유효한 연도가 아닙니다.")
        return value

    def validate_value(self, value):
        if value < 0:
            raise serializers.ValidationError("값은 0 이상이어야 합니다.")
        return value
```

### 5. Django ORM 최적화
```python
# 나쁜 예: N+1 쿼리
for data in ChartData.objects.all():
    print(data.department.name)  # 각 루프마다 추가 쿼리

# 좋은 예: select_related
queryset = ChartData.objects.select_related('department').all()
for data in queryset:
    print(data.department.name)  # 추가 쿼리 없음
```

### 6. 모든 코드는 PEP 8 준수
```python
# 좋은 예
def calculate_metrics(data: list[dict]) -> dict:
    """학과별 지표 계산 (명확한 docstring)"""
    result = {}
    for item in data:
        dept = item['department']
        if dept not in result:
            result[dept] = []
        result[dept].append(item['value'])
    return result

# 나쁜 예 (피하기)
def calc(d):
    r={}
    for i in d:
        dp=i['d'];r.setdefault(dp,[]).append(i['v'])
    return r
```

### 7. 에러 처리는 명시적으로
```python
# 좋은 예: 구체적인 예외 처리
try:
    parsed_data, errors = parse_excel_defensively(file_path)
except FileNotFoundError:
    logger.error(f"파일 없음: {file_path}")
    raise
except Exception as e:
    logger.error(f"예상치 못한 오류: {str(e)}", exc_info=True)
    raise

# 나쁜 예 (피하기)
try:
    ...
except:  # 모든 예외를 무시
    pass
```

---

## 권장 패턴 (SHOULD)

### 1. 의존성 주입 (DI) - 테스트 용이성
```python
# 좋은 예
def ingest_data(parser: ExcelParser, storage: DataStorage) -> bool:
    """주입된 의존성으로 테스트 가능"""
    data = parser.parse(file_path)
    return storage.save(data)

# 테스트
def test_ingest():
    mock_parser = MockExcelParser()
    mock_storage = MockDataStorage()
    assert ingest_data(mock_parser, mock_storage)
```

### 2. 복잡한 비즈니스 로직은 Service 계층으로
```python
# apps/ingest/services.py
class ExcelIngestService:
    """엑셀 파싱 및 DB 저장 로직 중앙화"""

    def ingest(self, file_path: str) -> dict:
        parsed_data, errors = self.parse(file_path)
        if errors:
            return {"success": False, "errors": errors}

        saved_count = self.save_to_db(parsed_data)
        return {"success": True, "saved_count": saved_count}

    def parse(self, file_path: str) -> tuple[list, list]:
        # 파싱 로직
        pass

    def save_to_db(self, data: list) -> int:
        # Upsert 로직
        pass
```

### 3. 마이그레이션 구조화
```bash
# Django 마이그레이션 파일명
0001_initial.py          # 초기 스키마
0002_add_department.py   # 필드 추가
0003_create_chart_data.py  # 차트 데이터 테이블
```

### 4. 로깅 설정
```python
# config/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/ingest.log',
        },
    },
    'loggers': {
        'apps.ingest': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

---

## 금지 패턴 (MUST NOT)

❌ **비동기 처리 (Celery, async/await)** → MVP는 동기만 사용
❌ **Supabase 기능 남용** → PostgreSQL 호스팅용으로만 사용
❌ **JWT/OAuth 인증** → Django 세션 인증만 사용
❌ **캐싱 (Redis)** → 필요시 기술부채로 문서화만
❌ **마이크로서비스 아키텍처** → 단일 Django 앱으로 유지
❌ **ORM 없이 Raw SQL** → Django ORM 최우선
❌ **하드코딩된 설정값** → 환경 변수 사용 (.env)

---

## 코드 스타일 가이드라인

### Python/Django
- **타입 힌팅**: `def get_data(dept_id: int) -> list[ChartData]:`
- **Docstring**: Google 스타일 (함수 목적, 파라미터, 반환값)
- **함수 순서**: 높은 수준의 함수 먼저, 유틸 함수는 아래
- **Early Return**: 조건문을 최소화
  ```python
  # 좋은 예
  if not user.is_authenticated:
      return None

  # 나쁜 예
  if user.is_authenticated:
      return user.profile
  else:
      return None
  ```

### HTML/Template
- **Bootstrap 클래스**: 인라인 스타일 피하기
- **차트 컨테이너**: `<canvas id="chartX"></canvas>` 고유 ID 사용
- **CSRF 토큰**: 모든 POST 폼에 `{% csrf_token %}` 포함

### API 응답
```json
{
    "success": true,
    "data": {},
    "error": null,
    "code": "OK"
}
```

---

## 성능 고려사항

1. **데이터베이스 쿼리**
   - 항상 `select_related()` / `prefetch_related()` 사용
   - `only()` / `defer()`로 필요한 필드만 조회

2. **대용량 엑셀 파싱**
   - pandas `chunksize` 옵션 활용
   - 메모리 부하 시 배치 처리 (100개씩)

3. **템플릿 렌더링**
   - Chart.js 데이터는 API로 분리 제공
   - 초기 페이지 로드 시간 최소화

---

## 테스트 전략

### Unit Test (pytest)
```python
# tests/ingest/test_services.py
def test_parse_excel_defensively_missing_column():
    """필수 컬럼 누락 시 에러 반환"""
    with pytest.raises(ValidationError):
        parse_excel_defensively("invalid.xlsx")

def test_parse_excel_defensively_valid():
    """유효한 파일은 정상 파싱"""
    data, errors = parse_excel_defensively("valid.xlsx")
    assert len(errors) == 0
    assert len(data) > 0
```

### Integration Test
```python
# tests/ingest/test_admin_actions.py
def test_parse_and_save_action(admin_user):
    """Admin 파싱 액션 통합 테스트"""
    upload = ExcelUpload.objects.create(...)
    parse_and_save(None, None, ExcelUpload.objects.filter(id=upload.id))
    assert ChartData.objects.count() > 0
```

---

## 주요 의존성

```
Django==5.0
djangorestframework==3.14
pandas==2.0
psycopg2-binary==2.9  # PostgreSQL 드라이버
python-dotenv==1.0    # 환경 변수
pytest==7.4
pytest-django==4.5
```

---

## 배포 고려사항

1. **로컬 개발**: `python manage.py runserver`
2. **Supabase 마이그레이션**: Django migrations 사용
3. **정적 파일**: `python manage.py collectstatic`
4. **환경 변수**: `.env` 파일로 관리 (절대 커밋 금지)

---

## 추가 질문 시 확인사항

- [ ] 파일 업로드 크기 제한?
- [ ] 차트 갱신 주기?
- [ ] 사용자 권한별 데이터 필터링?
- [ ] 에러 알림 방식 (이메일, 대시보드)?
- [ ] 감사 로그(Audit Log) 필요?
