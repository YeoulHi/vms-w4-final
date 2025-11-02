# 파일 형식 및 매핑 규칙

## 지원 파일 형식

| 파일명 | 형식 | 변환 | 메트릭 |
|--------|------|------|--------|
| standard.csv | 표준 (year, dept, metric, value) | 그대로 | 모든 타입 |
| department_kpi.csv | 한글 와이드 | Melt | KPI 5개 |
| publication_list.csv | 논문 목록 | Groupby | PUBLICATION |
| research_project.csv | 연구비 현황 | Sum | RESEARCH_BUDGET |
| student_roster.csv | 학생 명단 | Count | STUDENT_COUNT |

## 형식 감지

```python
def _detect_file_format(df) -> str:
    cols = set(df.columns)

    # 표준 형식
    if {"year", "department", "metric_type", "value"}.issubset(cols):
        return "standard"

    # 한글 와이드
    if {"평가년도", "단과대학", "학과"}.issubset(cols):
        return "korean_wide"

    # 논문
    if {"논문ID", "게재일"}.issubset(cols):
        return "publication_list"

    # 연구비
    if {"집행ID", "집행금액"}.issubset(cols):
        return "research_project"

    # 학생
    if {"학번", "학적상태"}.issubset(cols):
        return "student_roster"

    return "unknown"
```

## 부서명 정규화

```python
ALLOWED_DEPARTMENTS = {
    # 한글
    "컴퓨터공학과": "computer-science",
    "전자공학과": "electronics",
    "국어국문학과": "korean-literature",
    "철학과": "philosophy",
    "산업공학과": "industrial-engineering",
    "교육학과": "education",
    # 영문 (통과)
    "computer-science": "computer-science",
    "electronics": "electronics",
    # ...
}
```

## 지표명 정규화

```python
ALLOWED_METRICS = {
    # 한글 → 영문
    "졸업생 취업률 (%)": "EMPLOYMENT_RATE",
    "전임교원 수 (명)": "FULL_TIME_FACULTY",
    "초빙교원 수 (명)": "VISITING_FACULTY",
    "연간 기술이전 수입액 (억원)": "TECH_TRANSFER_REVENUE",
    "국제학술대회 개최 횟수": "INTERNATIONAL_CONFERENCE",
    # 집계 지표
    "PUBLICATION": "PUBLICATION",
    "RESEARCH_BUDGET": "RESEARCH_BUDGET",
    "STUDENT_COUNT": "STUDENT_COUNT",
    # 기본 지표 (대소문자 무시)
    "paper": "PAPER",
    "PAPER": "PAPER",
    "budget": "BUDGET",
    "BUDGET": "BUDGET",
    # ...
}
```

## 변환 패턴

### 와이드 → 롱 (Melt)
```python
df.melt(id_vars=["year", "dept"],
        value_vars=metric_columns,
        var_name="metric_column",
        value_name="value")
```

### 집계 (Groupby)
```python
df.groupby(["year", "department"]).size()  # 논문 수
df.groupby(["year", "department"])["amount"].sum()  # 연구비
```
