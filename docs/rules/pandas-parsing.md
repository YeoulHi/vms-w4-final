# Pandas 방어적 파싱 규칙

## 검증 순서
1. 필수 컬럼 확인
2. 데이터 타입 변환 (errors='coerce')
3. 범위 검증
4. 중복 확인

## 기본 패턴
```python
def parse_and_save_excel(file_obj) -> Tuple[int, int, str]:
    """반환: (성공수, 실패수, 메시지)"""
    df = pd.read_excel(file_obj) if file_obj.name.endswith(('.xlsx', '.xls')) else pd.read_csv(file_obj)

    # 형식 감지
    file_format = _detect_file_format(df)

    # 표준 형식 검증
    if file_format == "standard":
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(missing)}")

    # 포맷별 변환
    if file_format == "korean_wide":
        df = _transform_korean_format(df)
    elif file_format == "publication_list":
        df = _transform_publication_list(df)

    # 행별 처리 (부분 실패 허용)
    success_count = failure_count = 0
    for row in df.iterrows():
        try:
            normalized = _normalize_row(row)
            _upsert_record(normalized)
            success_count += 1
        except Exception:
            failure_count += 1

    # 실패율 검증 (≥20% 거부)
    failure_rate = (failure_count / len(df) * 100) if len(df) > 0 else 0
    if failure_rate >= 20:
        raise ValidationError(f"Failure rate is {failure_rate:.1f}%")

    return success_count, failure_count, f"Total {len(df)} rows: {success_count} success, {failure_count} failed"
```

## UPSERT
```python
MetricRecord.objects.update_or_create(
    year=row['year'],
    department=row['department'],
    metric_type=row['metric_type'],
    defaults={'metric_value': row['value']}
)
```
