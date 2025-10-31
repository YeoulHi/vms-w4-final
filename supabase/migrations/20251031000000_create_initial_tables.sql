-- 1. 도메인 테이블 생성
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

-- 2. 조회 성능을 위한 복합 인덱스 생성
-- PRD의 주요 조회 패턴(연도 + 학과)에 맞춰 생성합니다.
CREATE INDEX idx_metric_records_year_department
    ON metric_records (year, department);

-- 3. updated_at 자동 갱신을 위한 트리거 함수 생성
-- 레코드가 업데이트될 때마다 updated_at 필드를 현재 시간으로 자동 설정합니다.
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. 테이블에 트리거 적용
CREATE TRIGGER trg_metric_records_updated_at
BEFORE UPDATE ON metric_records
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- 5. 테이블 및 인덱스에 대한 주석 추가 (가독성 및 유지보수성 향상)
COMMENT ON TABLE metric_records IS 'Ecount에서 추출된 각 학과의 연도별 성과 지표를 저장하는 테이블';
COMMENT ON COLUMN metric_records.year IS '성과 지표의 해당 연도';
COMMENT ON COLUMN metric_records.department IS '성과 지표의 해당 학과';
COMMENT ON COLUMN metric_records.metric_type IS '성과 지표의 종류 (예: PAPER, BUDGET)';
COMMENT ON COLUMN metric_records.metric_value IS '성과 지표의 값';
COMMENT ON INDEX idx_metric_records_year_department IS '대시보드에서 연도와 학과로 데이터를 필터링하는 성능을 향상시키기 위한 인덱스';
