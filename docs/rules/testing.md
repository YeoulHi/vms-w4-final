# Django 테스트 규칙

## Excel Upload 테스트 체크리스트

```python
# TC-01: 정상 업로드
def test_valid_upload():
    """3개 행 정상 저장"""
    success, failure, msg = parse_and_save_excel(file_obj)
    assert success == 3 and failure == 0

# TC-02: UPSERT
def test_upsert_no_duplicate():
    """같은 키(year, dept, metric_type) → 1개만 존재"""
    assert MetricRecord.objects.filter(year=2025, department="computer-science", metric_type="PAPER").count() == 1

# TC-03: 확장자 검증
def test_invalid_extension():
    """.txt 파일 거부"""
    form = ExcelUploadForm(files={"file": TextFile})
    assert not form.is_valid()

# TC-04: 컬럼 검증
def test_missing_column():
    """value 컬럼 누락 → ValidationError"""
    with pytest.raises(ValidationError):
        parse_and_save_excel(file_without_value)

# TC-05: 부분 실패 (33.3%)
def test_partial_failure():
    """1개 실패, 2개 성공 → 거부"""
    with pytest.raises(ValidationError) as exc:
        parse_and_save_excel(file_with_1_invalid)
    assert "33.3%" in str(exc.value)

# TC-06: 고실패율 (75%)
def test_high_failure_rate():
    """3개 실패, 1개 성공 → 거부"""
    with pytest.raises(ValidationError) as exc:
        parse_and_save_excel(file_with_3_invalid)
    assert "75.0%" in str(exc.value)

# TC-07/08: 정규화
def test_normalization():
    """Computer-Science, PAPER → computer-science, PAPER"""
    success, failure, _ = parse_and_save_excel(mixed_case_file)
    assert MetricRecord.objects.filter(department="computer-science", metric_type="PAPER").count() == 1
```

## 파일 형식 변환 테스트

```python
# 한글 와이드 → 롱 변환
def test_korean_wide_format():
    """12행 × 5지표 = 60행"""
    df = _transform_korean_format(korean_kpi_df)
    assert len(df) == 60

# 논문 목록 집계
def test_publication_groupby():
    """학과별 논문 수 집계"""
    df = _transform_publication_list(publication_df)
    assert df['metric_type'].unique()[0] == "PUBLICATION"
```
