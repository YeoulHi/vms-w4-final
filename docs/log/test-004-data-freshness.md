# 테스트 가이드: UC-004 데이터 반영 정책

## 개요

UC-004 데이터 반영 정책은 "업로드 후 대시보드에 데이터가 즉시 반영되는가"를 검증합니다.

**핵심 원칙:**
- ✅ 엑셀 업로드는 **동기 처리** (비동기 작업 없음)
- ✅ 대시보드 API는 **캐시 없이** 항상 최신 DB 조회
- ✅ 부분 성공(Partial Commit) 시에도 성공한 행만 반영

---

## 환경 준비

### 1. 로컬 개발 DB 설정 확인

```bash
# SQLite 기본값 확인
python manage.py showmigrations ingest
```

출력 예:
```
ingest
 [X] 0001_initial
 [X] 0002_add_compound_index
```

### 2. Admin 계정 생성 (미존재 시)

```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@test.local
# Password: testpass123
```

### 3. 테스트 데이터 샘플 파일

다음 경로의 샘플 파일들을 사용합니다:

- `sample/tc-01-vaild.csv` → 정상 업로드 (3행)
- `sample/tc-02-upsert.csv` → UPSERT 테스트
- `sample/test-invalid.txt` → 확장자 오류 테스트
- `sample/test-missing-value.csv` → 누락값 오류 테스트
- `sample/test-high-failure.csv` → 고실패율(≥20%) 테스트

---

## TC-01: 정상 업로드 후 즉시 조회

**목표:** 업로드 완료 직후, 대시보드가 새로운 데이터를 즉시 반영하는가?

### 단계 1: Admin 로그인 및 업로드

```bash
# 개발 서버 시작
python manage.py runserver
```

1. 브라우저: `http://localhost:8000/admin/`
2. 계정 로그인
3. [Ingest] → [MetricRecords] → [Upload] 클릭
4. `sample/tc-01-vaild.csv` 선택 및 업로드

**예상 결과:**
```
Upload complete: Total 3 rows: 3 success, 0 failed
```

### 단계 2: 대시보드 즉시 확인

```bash
# 다른 터미널에서 API 테스트
curl -b "sessionid=<ADMIN_SESSION>" \
  "http://localhost:8000/api/dashboard/chart-data/"
```

또는 브라우저: `http://localhost:8000/dashboard/`

**예상 결과:**
```json
{
  "labels": ["2023", "2024"],
  "datasets": [
    {
      "label": "PAPER",
      "data": [10, 15],
      "backgroundColor": "#4A90E2"
    }
  ]
}
```

**검증:**
- ✅ 업로드된 3개 행의 데이터가 모두 포함됨
- ✅ `metric_value` 합계가 일치
- ✅ 응답 시간 < 500ms

---

## TC-02: UPSERT 동작 확인

**목표:** 같은 키(year, department, metric_type)로 재업로드 시, 데이터가 업데이트되는가?

### 단계 1: 초기 데이터 조회

```bash
curl "http://localhost:8000/api/dashboard/chart-data/?year=2023&department=computer-science"
```

기록: `PAPER` 값 = **10**

### 단계 2: 같은 키로 다른 값 업로드

`tc-02-upsert.csv` 내용:
```
year,department,metric_type,value
2023,computer-science,PAPER,25
```

Admin에서 업로드

### 단계 3: 데이터 재조회

```bash
curl "http://localhost:8000/api/dashboard/chart-data/?year=2023&department=computer-science"
```

**예상 결과:**
- `PAPER` 값 = **25** (업데이트됨)
- DB 레코드 수는 변함없음 (INSERT 아닌 UPDATE)

**검증 쿼리:**
```bash
python manage.py shell

from apps.ingest.models import MetricRecord
records = MetricRecord.objects.filter(
    year=2023,
    department="computer-science",
    metric_type="PAPER"
)
assert records.count() == 1  # 1개만 존재
assert records.first().metric_value == 25
```

---

## TC-03: 부분 실패 후 데이터 반영

**목표:** 업로드 중 일부 행 실패 시, 성공한 행만 DB에 반영되는가?

### 단계 1: 부분 실패 파일 업로드

`test-partical-fail.csv` (3행 중 1행 실패):
```
year,department,metric_type,value
2024,electronics,PAPER,50
2024,invalid-dept,PAPER,  (빈 값)
2024,philosophy,BUDGET,100
```

Admin에서 업로드

**예상 결과 메시지:**
```
Upload complete: Total 3 rows: 2 success, 1 failed
Row 3: Value conversion failed
```

### 단계 2: 성공한 데이터만 조회 확인

```bash
curl "http://localhost:8000/api/dashboard/chart-data/?year=2024"
```

**예상 결과:**
```json
{
  "labels": ["2024"],
  "datasets": [
    { "label": "PAPER", "data": [50], ... },
    { "label": "BUDGET", "data": [100], ... }
  ]
}
```

**검증:**
- ✅ 성공한 2개 행만 포함
- ✅ 실패한 행은 제외
- ✅ 실패율 < 20%이므로 업로드 완료

---

## TC-04: 고실패율(≥20%) 거부

**목표:** 실패율이 20% 이상이면 업로드 전체 거부되는가?

### 단계 1: 고실패율 파일 업로드

`test-high-failure.csv` (4행 중 3행 실패):
```
year,department,metric_type,value
2025,computer-science,PAPER,100
2025,invalid,UNKNOWN,  (실패)
2025,invalid,UNKNOWN,  (실패)
2025,invalid,UNKNOWN,  (실패)
```

Admin에서 업로드

**예상 결과:**
```
Upload failed: Failure rate is 75.0%. Please review the file.
```

### 단계 2: DB 확인

```bash
# 2025년 데이터가 추가되지 않았는지 확인
curl "http://localhost:8000/api/dashboard/chart-data/?year=2025"
```

**예상 결과:**
```json
{ "labels": [], "datasets": [] }  또는 이전 데이터만 표시
```

**검증:**
- ✅ DB에 부분적 커밋 없음
- ✅ 모든 행이 원자적으로 처리됨

---

## TC-05: 캐시 없음 확인 (Real-time Freshness)

**목표:** API 호출마다 DB에서 최신 데이터를 읽는가? (캐싱 안 함)

### 단계 1: 초기 API 호출

```bash
curl "http://localhost:8000/api/dashboard/chart-data/?department=computer-science"
```

응답 기록: `updated_at` 타임스탬프 확인 (예: `2025-11-03T10:30:00Z`)

### 단계 2: 신규 업로드 수행

다른 관리자가 새로운 데이터 추가 업로드 (동일 학과)

### 단계 3: 즉시 재 API 호출

```bash
curl "http://localhost:8000/api/dashboard/chart-data/?department=computer-science"
```

**예상 결과:**
- ✅ 새로운 데이터 포함
- ✅ 응답 JSON이 변경됨
- ✅ 캐시 헤더 없음 (또는 `Cache-Control: no-cache`)

**검증 방법:**
```bash
# HTTP 헤더 확인 (캐시 정책 없음)
curl -i "http://localhost:8000/api/dashboard/chart-data/" | grep -i cache-control
# 출력: (없거나 no-cache 만 표시)
```

---

## TC-06: 파일 형식 자동 감지 및 변환

**목표:** 다양한 엑셀 형식을 자동 감지하고 표준 형식으로 변환하는가?

### 단계 1: 한글 KPI 형식 (department_kpi.csv)

```csv
평가년도,단과대학,학과,졸업생 취업률 (%),전임교원 수 (명),초빙교원 수 (명),연간 기술이전 수입액 (억원),국제학술대회 개최 횟수
2023,공과대학,컴퓨터공학과,87.5,25,5,150,8
```

업로드 후 확인:

```bash
curl "http://localhost:8000/api/dashboard/chart-data/?year=2023&department=computer-science"
```

**예상 결과:**
- ✅ 5개 metric_type 자동 생성
  - `EMPLOYMENT_RATE`: 87.5
  - `FULL_TIME_FACULTY`: 25
  - `VISITING_FACULTY`: 5
  - `TECH_TRANSFER_REVENUE`: 150
  - `INTERNATIONAL_CONFERENCE`: 8

### 단계 2: 논문 목록 형식 (publication_list.csv)

```csv
논문ID,게재일,단과대학,학과,논문제목,
P001,2023-03-15,공과대학,컴퓨터공학과,AI 기반 시스템,
P002,2023-06-20,공과대학,컴퓨터공학과,클라우드 아키텍처,
```

업로드 후:

```bash
curl "http://localhost:8000/api/dashboard/chart-data/?year=2023&department=computer-science"
```

**예상 결과:**
- ✅ `PUBLICATION` metric 생성
- ✅ 값 = 2 (2023년 컴퓨터공학과 논문 수)

---

## TC-07: 필터링 검증

**목표:** 연도, 학과 필터가 정확히 작동하는가?

### 단계 1: 연도 필터

```bash
# 2023년만
curl "http://localhost:8000/api/dashboard/chart-data/?year=2023"

# 2024년만
curl "http://localhost:8000/api/dashboard/chart-data/?year=2024"
```

**검증:** labels에 해당 연도만 포함

### 단계 2: 학과 필터

```bash
# 컴퓨터공학과만
curl "http://localhost:8000/api/dashboard/chart-data/?department=computer-science"
```

**검증:** 모든 데이터의 department = "computer-science"

### 단계 3: 복합 필터

```bash
# 2023년 + 컴퓨터공학과
curl "http://localhost:8000/api/dashboard/chart-data/?year=2023&department=computer-science"
```

**검증:** 두 조건 모두 만족하는 데이터만 포함

---

## TC-08: 에러 처리

### 8-1: 잘못된 확장자

파일: `test-invalid.txt`

**예상 결과:**
```
Upload failed: File format not allowed. Allowed: {'.xlsx', '.xls', '.csv'}
```

### 8-2: 필수 컬럼 누락

파일 내용:
```
year,department,invalid_column
2023,computer-science,100
```

**예상 결과:**
```
Upload failed: Missing required columns: metric_type, value
```

### 8-3: 잘못된 연도 값

```csv
year,department,metric_type,value
invalid_year,computer-science,PAPER,100
```

**예상 결과:**
```
Total 1 rows: 0 success, 1 failed
Row 2: Year conversion failed: invalid_year
```

### 8-4: 잘못된 파라미터 (API)

```bash
curl "http://localhost:8000/api/dashboard/chart-data/?year=notanumber"
```

**예상 결과:**
```json
{ "error": "invalid_parameter" }
```

HTTP Status: `400 Bad Request`

---

## 성능 검증

### 단계 1: 대용량 데이터 업로드

5,000행 CSV 파일 생성 후 업로드:

```bash
# 처리 시간 측정
time python manage.py shell << 'EOF'
from apps.ingest.services import parse_and_save_excel
from django.core.files.uploadedfile import SimpleUploadedFile

with open('sample/large_5000rows.csv', 'rb') as f:
    file_obj = SimpleUploadedFile("test.csv", f.read())
    result = parse_and_save_excel(file_obj)
    print(result)
EOF
```

**예상 결과:**
- ✅ 처리 시간 < 3초 (5,000행 기준)
- ✅ 메모리 누수 없음

### 단계 2: API 응답 시간

```bash
# 3,000행 데이터 조회 (응답 시간 측정)
time curl "http://localhost:8000/api/dashboard/chart-data/" > /dev/null
```

**예상 결과:**
- ✅ 응답 시간 < 500ms

---

## 마이그레이션 검증

### 마이그레이션 파일 확인

```bash
ls -la apps/ingest/migrations/
```

**예상 결과:**
```
0001_initial.py          ✅
0002_add_compound_index.py  ✅
```

### 인덱스 생성 확인

```bash
python manage.py shell

from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'ingest_metricrecord'
        AND indexname LIKE 'idx%'
    """)
    print(cursor.fetchall())
```

**예상 결과:**
```
[('idx_metric_records_year_department',)]
```

---

## 요약 체크리스트

- [ ] TC-01: 정상 업로드 후 즉시 조회 ✅
- [ ] TC-02: UPSERT 동작 확인 ✅
- [ ] TC-03: 부분 실패 후 성공 행만 반영 ✅
- [ ] TC-04: 고실패율 거부 ✅
- [ ] TC-05: 캐시 없음 확인 ✅
- [ ] TC-06: 파일 형식 자동 감지 ✅
- [ ] TC-07: 필터링 검증 ✅
- [ ] TC-08: 에러 처리 ✅
- [ ] 성능 검증 (< 3초, < 500ms) ✅
- [ ] 마이그레이션 적용 ✅

---

## 참조 문서

- `docs/spec/004-spec-데이터-반영-정책.md`: UC-004 명세
- `docs/spec/004-plan-데이터-반영-정책.md`: 구현 계획
- `docs/5.dataflow.md`: 데이터 흐름 및 DB 스키마
- `docs/rules/pandas-parsing.md`: 파싱 규칙
- `docs/rules/admin-actions.md`: Admin 액션 규칙
