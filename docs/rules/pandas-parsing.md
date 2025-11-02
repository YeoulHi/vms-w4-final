# Pandas 방어적 파싱 규칙

## 필수 검증 순서

1. **필수 컬럼 확인** → 누락되면 즉시 실패
2. **데이터 타입 변환** → coerce 사용 (NaN 생성)
3. **범위 검증** → 유효한 값 범위 확인
4. **중복 제거** → unique_together 기준 중복 확인

## 기본 패턴

```python
def parse_excel(file_path: str) -> tuple[list[dict], list[str]]:
    """반환: (데이터, 에러 메시지 리스트)"""
    errors = []

    # 1. 파일 로드
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        return [], [f"파일 읽기 실패: {e}"]

    # 2. 필수 컬럼 확인
    required = ['column1', 'column2']
    missing = set(required) - set(df.columns)
    if missing:
        return [], [f"필수 컬럼 누락: {missing}"]

    # 3. 데이터 타입 변환 (에러 처리)
    df['numeric_col'] = pd.to_numeric(df['numeric_col'], errors='coerce')

    # 4. 검증 (에러 수집)
    if df['numeric_col'].isna().any():
        errors.append("numeric_col에 유효하지 않은 값 존재")

    if errors:
        return [], errors

    return df.to_dict('records'), []
```

## 에러 로깅

```python
import logging

logger = logging.getLogger(__name__)

try:
    data, errors = parse_excel(file_path)
    if errors:
        logger.warning(f"파싱 부분 실패: {errors}")
except Exception as e:
    logger.error(f"파싱 완전 실패: {e}", exc_info=True)
```

## Upsert 패턴 (Django)

```python
# unique_together 기준으로 update_or_create
for row in parsed_data:
    obj, created = Model.objects.update_or_create(
        unique_field1=row['col1'],
        unique_field2=row['col2'],
        defaults={'field3': row['col3']}
    )
```
