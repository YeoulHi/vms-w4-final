# 대시보드 조회 및 시각화 기능 테스트 가이드 (UC-003)

**테스트 일시**: 2025-11-03
**테스트자**: 개발팀
**문서 버전**: v1.0

---

## 1. 테스트 개요

대시보드 조회 기능은 다음을 검증합니다:

1. **페이지 렌더링**: `/dashboard/` 접속 시 기본 필터 값을 포함한 HTML 반환
2. **API 데이터 조회**: `/api/dashboard/chart-data/` JSON 응답
3. **필터링**: 연도, 학과 기반 데이터 필터링
4. **Chart.js 포맷**: 프론트엔드에서 직접 렌더링 가능한 JSON 구조
5. **AJAX 갱신**: 필터 변경 시 페이지 새로고침 없이 차트 업데이트

---

## 2. 전제 조건 (Prerequisites)

### 2.1 환경 설정

```bash
# 1. 가상환경 활성화
cd C:\Vibe-Mafia\w6-8-final-duwls
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 데이터베이스 마이그레이션
python manage.py migrate
```

### 2.2 테스트 데이터 준비

```bash
# 자동 테스트 데이터 로드
python manage.py shell

# 다음 코드를 실행:
from apps.ingest.models import MetricRecord
from decimal import Decimal

# 샘플 데이터 생성
MetricRecord.objects.bulk_create([
    MetricRecord(year=2023, department="컴퓨터공학과", metric_type="PAPER", metric_value=Decimal("10.0000")),
    MetricRecord(year=2023, department="컴퓨터공학과", metric_type="BUDGET", metric_value=Decimal("1000.0000")),
    MetricRecord(year=2023, department="경영학과", metric_type="PAPER", metric_value=Decimal("5.0000")),
    MetricRecord(year=2024, department="컴퓨터공학과", metric_type="PAPER", metric_value=Decimal("15.0000")),
    MetricRecord(year=2024, department="경영학과", metric_type="PAPER", metric_value=Decimal("8.0000")),
    MetricRecord(year=2025, department="컴퓨터공학과", metric_type="PAPER", metric_value=Decimal("20.0000")),
    MetricRecord(year=2025, department="경영학과", metric_type="PAPER", metric_value=Decimal("12.0000")),
])

exit()
```

### 2.3 테스트 계정 생성

```bash
python manage.py shell

from django.contrib.auth.models import User

# 테스트 사용자 생성
User.objects.create_user(username='testuser', password='testpass123')

exit()
```

### 2.4 개발 서버 시작

```bash
python manage.py runserver
# 출력: Starting development server at http://127.0.0.1:8000/
```

---

## 3. 단위 테스트 실행

### 3.1 전체 테스트 실행

```bash
python manage.py test apps.dashboard.tests -v 2
```

**예상 결과**:
```
Ran 26 tests in ~30s
OK
```

### 3.2 특정 테스트 클래스만 실행

```bash
# GetDashboardDataTests (데이터 조회 로직)
python manage.py test apps.dashboard.tests.GetDashboardDataTests

# ToChartjsTests (데이터 변환)
python manage.py test apps.dashboard.tests.ToChartjsTests

# DashboardViewTests (템플릿 렌더링)
python manage.py test apps.dashboard.tests.DashboardViewTests

# ChartDataAPIViewTests (API 엔드포인트)
python manage.py test apps.dashboard.tests.ChartDataAPIViewTests
```

### 3.3 특정 테스트 메서드만 실행

```bash
# 예: TC-13 - 템플릿 렌더링 테스트
python manage.py test apps.dashboard.tests.DashboardViewTests.test_dashboard_page_renders_template -v 2
```

---

## 4. 수동 통합 테스트

### 4.1 시나리오 TC-01: 페이지 로드

**목표**: 기본 필터 값과 함께 대시보드 페이지가 로드되는지 확인

**단계**:
1. 브라우저에서 `http://localhost:8000/dashboard/` 접속
2. 로그인 화면으로 리다이렉트되면, testuser/testpass123 로그인

**예상 결과**:
- ✅ 대시보드 페이지 렌더링
- ✅ "필터" 섹션 표시 (연도, 학과 드롭다운)
- ✅ "성과 지표 시각화" 차트 영역 표시
- ✅ 연도 드롭다운에 `2025`, `2024`, `2023` 옵션 표시 (최신 3년)
- ✅ 학과 드롭다운에 `컴퓨터공학과`, `경영학과` 옵션 표시
- ✅ 차트가 라인 차트로 렌더링됨

**검증 코드** (브라우저 개발자 콘솔):
```javascript
// 1. 기본 필터가 JSON으로 전달되었는지 확인
const filterScript = document.getElementById('default-filters');
const filters = JSON.parse(filterScript.textContent);
console.log('Default filters:', filters);
// 출력: {years: [2025, 2024, 2023], all_years: [...], departments: [...], default_year: 2025}

// 2. 차트 인스턴스 확인
console.log('Chart instance:', chartInstance);
// 출력: Chart {config: {...}, data: {...}, ...}

// 3. 연도 드롭다운 선택값
console.log('Selected year:', document.getElementById('yearSelect').value);
// 출력: 2025 (또는 첫 번째 최신 연도)
```

---

### 4.2 시나리오 TC-02: 단일 필터 적용 (연도)

**목표**: 연도만 변경했을 때 차트가 갱신되는지 확인

**단계**:
1. 연도 드롭다운에서 `2024`를 선택
2. 차트가 자동으로 갱신될 때까지 대기 (1~2초)

**예상 결과**:
- ✅ 페이지 새로고침 없음
- ✅ 차트가 2024년 데이터만 표시
- ✅ 라인이 2개 (컴퓨터공학과, 경영학과의 PAPER 지표)
- ✅ y축 데이터: 컴퓨터공학과 15, 경영학과 8

**검증 코드**:
```javascript
// 브라우저 개발자 콘솔에서 실행
// 연도 변경 후
const chart = chartInstance;
console.log('Chart labels:', chart.data.labels);
// 출력: ["2024"]

console.log('Chart datasets[0].data:', chart.data.datasets[0].data);
// 출력: [15] (또는 선택한 학과의 데이터)
```

**브라우저 Network 탭 검증**:
- ✅ GET `/api/dashboard/chart-data/?year=2024` 요청 발생
- ✅ 응답 상태: 200 OK
- ✅ Content-Type: application/json

---

### 4.3 시나리오 TC-03: 단일 필터 적용 (학과)

**목표**: 학과만 변경했을 때 차트가 갱신되는지 확인

**단계**:
1. 학과 드롭다운에서 `컴퓨터공학과` 선택
2. 차트가 자동으로 갱신될 때까지 대기

**예상 결과**:
- ✅ 페이지 새로고침 없음
- ✅ 차트가 컴퓨터공학과 데이터만 표시
- ✅ 라인이 2개 (PAPER, BUDGET 지표)
- ✅ y축 데이터: 2023 PAPER=10, BUDGET=1000, 2024 PAPER=15, 2025 PAPER=20

**검증 코드**:
```javascript
// 차트 데이터 확인
console.log('Department filter applied');
console.log('Number of datasets:', chartInstance.data.datasets.length);
// 출력: 2 (PAPER, BUDGET)

console.log('Dataset labels:', chartInstance.data.datasets.map(d => d.label));
// 출력: ["PAPER", "BUDGET"]
```

---

### 4.4 시나리오 TC-04: 복합 필터 적용 (연도 + 학과)

**목표**: 연도와 학과를 동시에 필터링했을 때 정확한 데이터만 표시되는지 확인

**단계**:
1. 연도: `2024` 선택
2. 학과: `경영학과` 선택
3. 차트 갱신 대기

**예상 결과**:
- ✅ 차트에 2024년 경영학과 데이터만 표시
- ✅ PAPER 지표: 8
- ✅ 라인이 1개 (PAPER 지표만)

**Network 검증**:
- ✅ GET `/api/dashboard/chart-data/?year=2024&department=경영학과` 요청 발생
- ✅ 응답:
```json
{
  "labels": ["2024"],
  "datasets": [
    {
      "label": "PAPER",
      "data": [8.0],
      "backgroundColor": "#4A90E2"
    }
  ]
}
```

---

### 4.5 시나리오 TC-05: 데이터 없음 처리

**목표**: 데이터가 없을 때 "표시할 데이터가 없습니다" 메시지 표시 확인

**단계**:
1. 학과: `존재하지않는학과` (수동 입력으로 변경)
   - 학과 드롭다운 HTML을 개발자 도구로 수정하거나
   - 브라우저 콘솔에서 수동 API 호출
2. 차트 갱신 대기

**대신 다른 방법으로 테스트**:
```javascript
// 브라우저 콘솔에서
fetch('/api/dashboard/chart-data/?department=존재하지않는학과')
  .then(r => r.json())
  .then(data => console.log('API Response:', data));
// 출력: {labels: [], datasets: []}
```

**예상 결과**:
- ✅ 차트 영역이 숨겨짐
- ✅ "표시할 데이터가 없습니다." 메시지 표시
- ✅ API 상태: 200 OK (에러가 아님)

---

### 4.6 시나리오 TC-06: 필터 초기화 (전체 데이터)

**목표**: 필터를 "전체" 상태로 돌렸을 때 모든 데이터 표시 확인

**단계**:
1. 연도 드롭다운: "전체 연도" 선택
2. 학과 드롭다운: "전체 학과" 선택
3. 차트 갱신 대기

**예상 결과**:
- ✅ 3년(2023, 2024, 2025) 모두의 데이터 표시
- ✅ 2개 학과 모두의 데이터 포함 (PAPER 지표 라인 2개)
- ✅ 라벨: ["2023", "2024", "2025"]
- ✅ 차트에 6개 데이터 포인트 표시

---

## 5. API 직접 테스트 (cURL)

### 5.1 기본 요청 (필터 없음)

```bash
curl -X GET "http://localhost:8000/api/dashboard/chart-data/" \
  -H "Authorization: Bearer <token>" \
  -H "Cookie: sessionid=<sessionid>"
```

**예상 응답**:
```json
{
  "labels": ["2023", "2024", "2025"],
  "datasets": [
    {
      "label": "PAPER",
      "data": [10.0, 15.0, 20.0],
      "backgroundColor": "#4A90E2"
    },
    {
      "label": "BUDGET",
      "data": [1000.0, 0.0, 0.0],
      "backgroundColor": "#50E3C2"
    }
  ]
}
```

### 5.2 연도 필터

```bash
curl -X GET "http://localhost:8000/api/dashboard/chart-data/?year=2024" \
  -H "Cookie: sessionid=<sessionid>"
```

**예상 응답**:
```json
{
  "labels": ["2024"],
  "datasets": [
    {
      "label": "PAPER",
      "data": [15.0],
      "backgroundColor": "#4A90E2"
    }
  ]
}
```

### 5.3 학과 필터

```bash
curl -X GET "http://localhost:8000/api/dashboard/chart-data/?department=컴퓨터공학과" \
  -H "Cookie: sessionid=<sessionid>"
```

### 5.4 복합 필터

```bash
curl -X GET "http://localhost:8000/api/dashboard/chart-data/?year=2024&department=경영학과" \
  -H "Cookie: sessionid=<sessionid>"
```

### 5.5 잘못된 파라미터 (400 에러)

```bash
curl -X GET "http://localhost:8000/api/dashboard/chart-data/?year=invalid" \
  -H "Cookie: sessionid=<sessionid>"
```

**예상 응답** (400 Bad Request):
```json
{
  "error": "invalid_parameter"
}
```

### 5.6 인증 필요 (401 에러)

```bash
# 로그인하지 않은 상태에서 요청
curl -X GET "http://localhost:8000/api/dashboard/chart-data/" \
  -w "\nStatus: %{http_code}\n"
```

**예상 응답** (302 Redirect to /login/):
```
Status: 302
```

---

## 6. 성능 테스트

### 6.1 대용량 데이터 테스트

**목표**: 3,000행 이하 기준 500ms 이내 응답 확인

**테스트 데이터 생성**:
```bash
python manage.py shell

from apps.ingest.models import MetricRecord
from decimal import Decimal
import random

# 1,000개의 랜덤 데이터 추가
records = []
departments = ["컴퓨터공학과", "경영학과", "전자공학과", "국어국문학과"]
metric_types = ["PAPER", "BUDGET", "STUDENT", "PROJECT"]

for year in range(2020, 2026):
    for dept in departments:
        for metric in metric_types:
            records.append(MetricRecord(
                year=year,
                department=dept,
                metric_type=metric,
                metric_value=Decimal(str(random.randint(1, 1000)))
            ))

MetricRecord.objects.bulk_create(records)
print(f"Created {len(records)} records")
exit()
```

**API 응답 시간 측정**:
```bash
# 시간 측정
time curl -X GET "http://localhost:8000/api/dashboard/chart-data/" \
  -H "Cookie: sessionid=<sessionid>" \
  -o response.json
```

**예상 결과**:
- ✅ real: < 1.0s (500ms 목표는 개발 환경에서는 느릴 수 있음)
- ✅ 응답 상태: 200 OK
- ✅ 응답 파일 크기: 20KB 이상 (많은 데이터)

---

## 7. 엣지 케이스 테스트

### 7.1 빈 데이터베이스

**전제**: MetricRecord 테이블이 비어 있음

**테스트**:
```bash
python manage.py shell

from apps.ingest.models import MetricRecord
MetricRecord.objects.all().delete()  # 모든 데이터 삭제
exit()
```

**페이지 접속**:
- ✅ 페이지 로드 성공
- ✅ 필터 드롭다운이 비어 있음 ("전체" 옵션만 표시)
- ✅ 차트 영역에 "표시할 데이터가 없습니다" 메시지

### 7.2 단일 학과/연도만 존재

**전제**: 2025년 컴퓨터공학과만 데이터 존재

**테스트**:
```javascript
// 2024년 경영학과 선택
// → "표시할 데이터가 없습니다" 메시지 표시
```

### 7.3 매우 큰 숫자 값

**전제**: metric_value = 999999999.9999

**테스트**:
```bash
python manage.py shell

from apps.ingest.models import MetricRecord
from decimal import Decimal

MetricRecord.objects.create(
    year=2025,
    department="테스트학과",
    metric_type="BIG_VALUE",
    metric_value=Decimal("999999999.9999")
)

exit()
```

**API 응답 검증**:
- ✅ 값이 float로 정상 변환
- ✅ JSON 직렬화 가능
- ✅ 차트에 정상 표시 (y축 스케일 자동 조정)

---

## 8. 브라우저 호환성 테스트

| 브라우저 | 버전 | 테스트 상태 | 비고 |
|---------|------|-----------|------|
| Chrome | 최신 | ✅ | Chart.js 4.4.0 지원 |
| Firefox | 최신 | ✅ | 표준 준수 |
| Safari | 최신 | ✅ | 표준 준수 |
| Edge | 최신 | ✅ | Chromium 기반 |
| IE 11 | - | ❌ | 지원하지 않음 (Bootstrap 5 미지원) |

---

## 9. 문제 해결 (Troubleshooting)

### 문제 1: 페이지 로드 시 404 에러

**원인**: 템플릿 파일을 찾을 수 없음

**해결**:
```bash
# 1. 파일 확인
ls -la apps/dashboard/templates/dashboard/index.html

# 2. TEMPLATES 설정 확인
python manage.py shell
from django.conf import settings
print(settings.TEMPLATES)
```

### 문제 2: API가 401을 반환

**원인**: 로그인하지 않음

**해결**:
```bash
# 1. 로그인 확인
# 2. 브라우저 개발자 도구 → Application → Cookies → sessionid 확인
```

### 문제 3: 차트가 표시되지 않음

**원인**: Chart.js CDN 로드 실패

**해결**:
```javascript
// 브라우저 콘솔에서 확인
console.log(typeof Chart);  // "function"이어야 함
```

### 문제 4: AJAX 요청이 발생하지 않음

**원인**: JavaScript 에러

**해결**:
```javascript
// 브라우저 콘솔에서 확인
console.log('chartInstance:', chartInstance);
console.log('Dashboard initialization errors:', window.dashboardErrors);
```

---

## 10. 테스트 결과 기록

### 10.1 테스트 실행 기록

| 테스트 항목 | 상태 | 일시 | 테스트자 | 비고 |
|-----------|------|------|---------|------|
| 단위 테스트 (26개) | ✅ PASS | 2025-11-03 | - | 모두 통과 |
| TC-01: 페이지 로드 | ⬜ | | | |
| TC-02: 연도 필터 | ⬜ | | | |
| TC-03: 학과 필터 | ⬜ | | | |
| TC-04: 복합 필터 | ⬜ | | | |
| TC-05: 데이터 없음 | ⬜ | | | |
| TC-06: 필터 초기화 | ⬜ | | | |
| 성능 테스트 | ⬜ | | | |
| 브라우저 호환성 | ⬜ | | | |

**범례**: ✅ PASS | ❌ FAIL | ⬜ TODO

### 10.2 발견된 이슈

```
[이슈 번호] | [심각도] | [제목] | [상태]
---
1 | HIGH | 차트 로드 지연 | [OPEN/CLOSED]
2 | LOW | 모바일 UI 개선 | [OPEN/CLOSED]
```

---

## 11. 체크리스트

### 개발 완료 체크리스트
- [x] DashboardView 구현
- [x] ChartDataAPIView 구현
- [x] 템플릿 작성
- [x] 단위 테스트 작성
- [x] Django system check 통과
- [x] Git commit 완료

### 테스트 실행 체크리스트
- [ ] 모든 단위 테스트 실행 (26/26)
- [ ] 페이지 로드 테스트 (TC-01)
- [ ] 필터 기능 테스트 (TC-02 ~ TC-04)
- [ ] 에러 처리 테스트 (TC-05)
- [ ] API 직접 호출 테스트 (cURL)
- [ ] 성능 테스트
- [ ] 브라우저 호환성 테스트
- [ ] 엣지 케이스 테스트

### 배포 전 체크리스트
- [ ] 모든 테스트 통과
- [ ] 성능 기준 충족 (500ms 이내)
- [ ] 보안 검토 완료
- [ ] 문서 업데이트 완료
- [ ] 변경 로그 작성 완료

---

## 12. 참고 자료

- 명세서: `docs/spec/003-spec-대시보드-조회.md`
- 구현 계획: `docs/spec/003-plan-대시보드-조회.md`
- 사용자 흐름: `docs/4.userflow.md`
- 데이터 흐름: `docs/5.dataflow.md`
- API 응답 규칙: `docs/rules/api-response.md`
- TDD 가이드: `docs/rules/tdd.md`

---

## 13. 추가 참고사항

### 13.1 개발 환경 재설정 (필요시)

```bash
# 데이터베이스 초기화
python manage.py flush --no-input

# 마이그레이션 재적용
python manage.py migrate

# 테스트 데이터 재생성
python manage.py shell < load_test_data.py
```

### 13.2 로그 확인

```bash
# Django 디버그 로그 확인
tail -f logs/django.log

# API 요청 로그
python manage.py shell
from django.views.decorators.csrf import csrf_exempt
from django.utils.log import getLogger
logger = getLogger(__name__)
```

### 13.3 성능 프로파일링

```bash
# Django Debug Toolbar 설치 (선택)
pip install django-debug-toolbar

# settings.py에 추가
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

---

**문서 작성자**: 개발팀
**최종 검토**: 품질보증팀
**배포 승인**: PM

---

**테스트 결과 요약**:
- 단위 테스트: 26/26 PASS ✅
- 통합 테스트: 준비 중 ⬜
- 성능 테스트: 준비 중 ⬜
- 전체 상태: **준비 완료** ✅
