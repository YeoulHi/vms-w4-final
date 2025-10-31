# 1. 데이터플로우 (최종)

1.  **Admin 업로드 (유저플로우 #2)**
    *   Django Admin `/admin/ingest/exceldata/add/`에서 엑셀/CSV 업로드
    *   `ingest/services.py`가 pandas로 파싱
    *   각 행에 대해
        1.  `normalize_department(raw_department)`로 학과명을 통일
        2.  `normalize_metric_type(raw_metric)`으로 시스템 정의 값으로 변환
        3.  `INSERT ... ON CONFLICT (year, department, metric_type) DO UPDATE` 실행
    *   트랜잭션 커밋 시점에 DB는 최신 상태가 된다

2.  **대시보드 조회 (유저플로우 #3)**
    *   `/dashboard/` 접근 시 템플릿이 기본 필터(최신 연도, 전체 학과)를 내려준다
    *   프런트가 `/api/dashboard/chart-data/?year=...&department=...` 호출
    *   API가 `metric_records`에서 해당 조건으로 SELECT
    *   결과를 `to_chartjs()`로 변환해 반환

3.  **신선도 (유저플로우 #4)**
    *   업로드가 커밋된 이후의 SELECT는 모두 최신 데이터
    *   별도 캐시 없음
    *   사용자가 재접속/새로고침/필터 재적용할 때마다 최신 반영
    *   partial commit 시엔 성공 레코드만 노출

4.  **인증 (유저플로우 #1)**
    *   Django 기본 `auth_user`에서 로그인
    *   `is_staff = true`만 업로드 URL 접근 가능
    *   DB 스키마 추가 없음

---

## 2. 데이터베이스 스키마 (PostgreSQL, 최종본)

```sql
-- 1. 도메인 테이블
CREATE TABLE metric_records (
    id              BIGSERIAL PRIMARY KEY,
    year            INTEGER NOT NULL,
    department      VARCHAR(100) NOT NULL,
    metric_type     VARCHAR(50)  NOT NULL,
    metric_value    NUMERIC(18,4) NOT NULL,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_metric_records_business
        UNIQUE (year, department, metric_type)
);

-- 2. 조회 패턴에 맞춘 고정 인덱스
-- PRD가 연도 + 학과 조회를 기본으로 하므로 단일 인덱스 대신 복합 인덱스를 기본값으로 둔다.
CREATE INDEX idx_metric_records_year_department
    ON metric_records (year, department);
```

### 2.1 `updated_at` 자동 갱신 보강

Django 모델의 `auto_now=True` 또는 아래의 DB 트리거 중 하나를 사용하여 데이터 신선도를 100% 보장합니다.

**방법 A — Django 모델에서:**

```python
class MetricRecord(models.Model):
    # ...
    updated_at = models.DateTimeField(auto_now=True)  # <- 여기서 강제
```

**방법 B — DB trigger로:**

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_metric_records_updated_at
BEFORE UPDATE ON metric_records
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
```

---

## 3. 앱 레이어에서의 정규화 책임 명시

DB에 마스터 테이블을 두지 않는 대신, 업로드 시점에 `ingest/services.py`에서 문자열을 정리하여 데이터 일관성을 유지합니다.

```python
# apps/ingest/services.py (개념 스케치)

ALLOWED_DEPARTMENTS = {
    "컴퓨터공학과": "컴퓨터공학과",
    "컴퓨터 공학과": "컴퓨터공학과",
    "컴공과": "컴퓨터공학과",
}

ALLOWED_METRICS = {
    "논문": "PAPER",
    "논문수": "PAPER",
    "예산": "BUDGET",
    "학생수": "STUDENT",
}

def normalize_department(raw: str) -> str:
    raw = (raw or "").strip()
    return ALLOWED_DEPARTMENTS.get(raw, raw)  # 모르는 건 그대로 저장

def normalize_metric_type(raw: str) -> str:
    raw = (raw or "").strip()
    return ALLOWED_METRICS.get(raw, raw)
```

---

## 4. 문서에만 남기는 metric_type 도메인

DB에 ENUM을 만들지 않았으므로, 시스템이 사용하는 `metric_type`의 종류는 아래와 같이 문서로 정의합니다.

```markdown
# metric_type 도메인 (MVP)

- PAPER    : 논문 수
- BUDGET   : 예산
- STUDENT  : 재학생/학생 수
- PROJECT  : 연구/과제 실적

※ 위 목록은 대시보드에서 시각화 대상으로 삼는 시스템 정의 값입니다.
※ 엑셀에 이 값과 다른 문자열이 오면 ingest 단계에서 가능한 값으로 치환하고, 치환 불가하면 원문 그대로 저장합니다.
```

---

## 5. 최종 요약

*   **테이블 수**: 도메인 1개(`metric_records`), 나머지는 Django 기본 테이블 사용
*   **키 구조**: PK = id, 비즈니스 유니크 키 = (year, department, metric_type)
*   **인덱스**: (year, department) 복합 인덱스 1개 고정
*   **업데이트 타임**: 모델 `auto_now=True` 또는 DB trigger로 항상 갱신
*   **정규화 위치**: DB가 아닌 `ingest/services.py`에서 문자열 정규화
*   **확장성**: 마스터/로그/캐시 테이블은 문서에만 명시하고, MVP에서는 구현하지 않음
*   **출처 일치**: 클라이언트 요구사항, PRD, 코드 구조, 유저플로우 등 모든 문서의 내용을 최종 반영한 버전입니다.
