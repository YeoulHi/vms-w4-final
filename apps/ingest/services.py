"""Ingest Service - Excel/CSV parsing and data persistence

This module handles Excel/CSV file parsing, data normalization, and database UPSERT.
Implements the core logic for UserFlow #02 (Admin Excel Upload).
"""

from typing import List, Dict, Any, Tuple, Optional
from decimal import Decimal

# Lazy import: pandas는 함수 내부에서 import (Django admin 로드 시 무거운 의존성 방지)
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import MetricRecord


ALLOWED_DEPARTMENTS = {
    # 영문 매핑
    "computer-science": "computer-science",
    "electronics": "electronics",
    "korean-literature": "korean-literature",
    "philosophy": "philosophy",
    "industrial-engineering": "industrial-engineering",
    "education": "education",
    # 한글 매핑
    "컴퓨터공학과": "computer-science",
    "전자공학과": "electronics",
    "국어국문학과": "korean-literature",
    "철학과": "philosophy",
    "산업공학과": "industrial-engineering",
    "교육학과": "education",
}

ALLOWED_METRICS = {
    # 기본 지표
    "paper": "PAPER",
    "budget": "BUDGET",
    "student": "STUDENT",
    "project": "PROJECT",
    "PAPER": "PAPER",
    "BUDGET": "BUDGET",
    "STUDENT": "STUDENT",
    "PROJECT": "PROJECT",
    # department_kpi 지표
    "employment_rate": "EMPLOYMENT_RATE",
    "full_time_faculty": "FULL_TIME_FACULTY",
    "visiting_faculty": "VISITING_FACULTY",
    "tech_transfer_revenue": "TECH_TRANSFER_REVENUE",
    "international_conference": "INTERNATIONAL_CONFERENCE",
    "EMPLOYMENT_RATE": "EMPLOYMENT_RATE",
    "FULL_TIME_FACULTY": "FULL_TIME_FACULTY",
    "VISITING_FACULTY": "VISITING_FACULTY",
    "TECH_TRANSFER_REVENUE": "TECH_TRANSFER_REVENUE",
    "INTERNATIONAL_CONFERENCE": "INTERNATIONAL_CONFERENCE",
    # publication_list 지표
    "publication": "PUBLICATION",
    "PUBLICATION": "PUBLICATION",
    # research_project 지표
    "research_budget": "RESEARCH_BUDGET",
    "RESEARCH_BUDGET": "RESEARCH_BUDGET",
    # student_roster 지표
    "student_count": "STUDENT_COUNT",
    "STUDENT_COUNT": "STUDENT_COUNT",
}

ALLOWED_FILE_EXTENSIONS = {".xlsx", ".xls", ".csv"}
REQUIRED_COLUMNS = {"year", "department", "metric_type", "value"}
FAILURE_THRESHOLD_PERCENTAGE = 20

# 한글 컬럼명 → metric_type 매핑
KOREAN_COLUMN_MAPPING = {
    "졸업생 취업률 (%)": "EMPLOYMENT_RATE",
    "전임교원 수 (명)": "FULL_TIME_FACULTY",
    "초빙교원 수 (명)": "VISITING_FACULTY",
    "연간 기술이전 수입액 (억원)": "TECH_TRANSFER_REVENUE",
    "국제학술대회 개최 횟수": "INTERNATIONAL_CONFERENCE",
}


def parse_and_save_excel(file_obj: Any) -> Tuple[int, int, str]:
    """
    Parse and save Excel/CSV file to database.

    Args:
        file_obj: Django UploadedFile object

    Returns:
        Tuple[int, int, str]: (success_count, failure_count, summary_message)

    Raises:
        ValidationError: If file validation fails
    """
    import pandas as pd  # Lazy import: 함수 호출 시점에만 로드

    try:
        filename = file_obj.name.lower()
        if not any(filename.endswith(ext) for ext in ALLOWED_FILE_EXTENSIONS):
            raise ValidationError(
                f"File format not allowed. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
            )

        if filename.endswith(".csv"):
            df = pd.read_csv(file_obj)
        else:
            df = pd.read_excel(file_obj)

        # 파일 형식 감지
        file_format = _detect_file_format(df)

        if file_format == "standard":
            _validate_columns(df)
        elif file_format == "department_kpi":
            df = _transform_korean_format(df)
        elif file_format == "publication_list":
            df = _transform_publication_list(df)
        elif file_format == "research_project":
            df = _transform_research_project(df)
        elif file_format == "student_roster":
            df = _transform_student_roster(df)
        else:
            raise ValidationError("Unknown file format. Please check the file structure.")

        results = _process_rows(df)

        total_rows = len(df)
        success_count = results["success_count"]
        failure_count = results["failure_count"]
        failure_rate = (failure_count / total_rows * 100) if total_rows > 0 else 0

        if failure_rate >= FAILURE_THRESHOLD_PERCENTAGE:
            raise ValidationError(
                f"Failure rate is {failure_rate:.1f}%. Please review the file."
            )

        summary_message = _generate_summary_message(total_rows, success_count, failure_count)

        return success_count, failure_count, summary_message

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Error processing file: {str(e)}")


def _validate_columns(df: "pd.DataFrame") -> None:
    """
    Validate that all required columns exist.

    Args:
        df: pandas DataFrame to validate

    Raises:
        ValidationError: If any required column is missing
    """
    df_columns_lower = {col.lower() for col in df.columns}
    missing_columns = REQUIRED_COLUMNS - df_columns_lower

    if missing_columns:
        raise ValidationError(
            f"Missing required columns: {', '.join(sorted(missing_columns))}"
        )


def _process_rows(df: "pd.DataFrame") -> Dict[str, int]:
    """
    Process each row: normalize, validate, and upsert to database.

    Args:
        df: pandas DataFrame with validated columns

    Returns:
        dict: {"success_count": int, "failure_count": int}
    """
    import pandas as pd  # Lazy import

    success_count = 0
    failure_count = 0
    failures = []

    df.columns = df.columns.str.lower()

    with transaction.atomic():
        for row_num, row in df.iterrows():
            try:
                normalized_row = _normalize_row(row)
                _upsert_metric_record(normalized_row)
                success_count += 1
            except Exception as e:
                failure_count += 1
                failures.append(f"Row {row_num + 2}: {str(e)}")

    if failures:
        print("\n[Excel Upload Failures]")
        for failure_msg in failures:
            print(f"  {failure_msg}")

    return {"success_count": success_count, "failure_count": failure_count, "failures": failures}


def _normalize_row(row: pd.Series) -> Dict[str, Any]:
    """
    Normalize row data: clean strings, cast types, apply domain mappings.

    Args:
        row: pandas Series representing a single row

    Returns:
        dict: Normalized row data

    Raises:
        ValueError: If required field is invalid
    """
    year_raw = row.get("year")
    department_raw = row.get("department")
    metric_type_raw = row.get("metric_type")
    value_raw = row.get("value")

    try:
        year = int(year_raw) if pd.notna(year_raw) else None
        if year is None or year < 1900 or year > 2100:
            raise ValueError(f"Invalid year: {year_raw}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Year conversion failed: {year_raw}")

    department_str = (str(department_raw) if pd.notna(department_raw) else "").strip()
    if not department_str:
        raise ValueError("Department is required")
    department = ALLOWED_DEPARTMENTS.get(department_str, department_str)

    metric_type_str = (str(metric_type_raw) if pd.notna(metric_type_raw) else "").strip()
    if not metric_type_str:
        raise ValueError("Metric type is required")
    metric_type = ALLOWED_METRICS.get(metric_type_str, metric_type_str)

    try:
        metric_value = Decimal(str(value_raw)) if pd.notna(value_raw) else None
        if metric_value is None:
            raise ValueError("Metric value is required")
    except Exception as e:
        raise ValueError(f"Value conversion failed: {value_raw}")

    return {
        "year": year,
        "department": department,
        "metric_type": metric_type,
        "metric_value": metric_value,
    }


@transaction.atomic
def _upsert_metric_record(normalized_row: Dict[str, Any]) -> None:
    """
    Insert or update a single metric record in the database.

    Args:
        normalized_row: Normalized row dict

    Raises:
        Exception: If database operation fails
    """
    MetricRecord.objects.update_or_create(
        year=normalized_row["year"],
        department=normalized_row["department"],
        metric_type=normalized_row["metric_type"],
        defaults={"metric_value": normalized_row["metric_value"]},
    )


def _generate_summary_message(total_rows: int, success_count: int, failure_count: int) -> str:
    """
    Generate user-friendly summary message.

    Args:
        total_rows: Total number of rows processed
        success_count: Number of successful saves
        failure_count: Number of failures

    Returns:
        str: Summary message
    """
    return f"Total {total_rows} rows: {success_count} success, {failure_count} failed"


def _detect_file_format(df: "pd.DataFrame") -> str:
    """
    파일 형식 감지: 표준 형식, department_kpi, publication_list, research_project, student_roster

    Args:
        df: pandas DataFrame

    Returns:
        str: 파일 형식 종류
    """
    columns_set = set(df.columns)
    columns_lower = {col.lower() for col in df.columns}

    # 1. 표준 형식 체크
    required_english = {"year", "department", "metric_type", "value"}
    if required_english.issubset(columns_lower):
        return "standard"

    # 2. department_kpi 형식 체크
    if {"평가년도", "단과대학", "학과"}.issubset(columns_set):
        if "졸업생 취업률 (%)" in columns_set:
            return "department_kpi"

    # 3. publication_list 형식 체크
    if {"논문ID", "게재일", "단과대학", "학과", "논문제목"}.issubset(columns_set):
        return "publication_list"

    # 4. research_project_data 형식 체크
    if {"집행ID", "과제번호", "과제명", "연구책임자", "소속학과"}.issubset(columns_set):
        return "research_project"

    # 5. student_roster 형식 체크
    if {"학번", "이름", "단과대학", "학과", "학년"}.issubset(columns_set):
        return "student_roster"

    return "unknown"


def _is_korean_format(df: "pd.DataFrame") -> bool:
    """
    감지: 한글 형식 파일인지 확인 (호환성 유지)

    Args:
        df: pandas DataFrame

    Returns:
        bool: 한글 형식이면 True, 영문 형식이면 False
    """
    file_format = _detect_file_format(df)
    return file_format != "standard"


def _transform_korean_format(df: "pd.DataFrame") -> "pd.DataFrame":
    """
    한글 형식 DataFrame을 표준 형식으로 변환 (department_kpi.csv)

    한글 형식:
        평가년도, 단과대학, 학과, 졸업생 취업률 (%), 전임교원 수 (명), ...

    표준 형식:
        year, department, metric_type, value

    Args:
        df: 한글 형식 DataFrame

    Returns:
        "pd.DataFrame": 표준 형식으로 변환된 DataFrame (Melt 형태)
    """
    # 컬럼 이름 매핑
    column_rename = {
        "평가년도": "year",
        "단과대학": "college",
        "학과": "department",
    }

    df_renamed = df.rename(columns=column_rename)

    # 지표 컬럼들 (한글 → metric_type)
    metric_columns = list(KOREAN_COLUMN_MAPPING.keys())

    # ID 컬럼들 (year, college, department)
    id_vars = ["year", "college", "department"]

    # Melt: 와이드 형식 → 롱 형식
    df_melted = df_renamed.melt(
        id_vars=id_vars,
        value_vars=metric_columns,
        var_name="metric_column",
        value_name="value"
    )

    # 한글 컬럼명 → metric_type 변환
    df_melted["metric_type"] = df_melted["metric_column"].map(KOREAN_COLUMN_MAPPING)

    # 부서명 정규화 (한글 → 영문)
    df_melted["department"] = df_melted["department"].map(
        lambda x: ALLOWED_DEPARTMENTS.get(x, x)
    )

    # 최종 컬럼 선택
    df_result = df_melted[["year", "department", "metric_type", "value"]].copy()

    # year를 정수로 변환
    df_result["year"] = df_result["year"].astype(int)

    return df_result


def _transform_publication_list(df: "pd.DataFrame") -> "pd.DataFrame":
    """
    publication_list.csv를 표준 형식으로 변환

    입력: 논문ID, 게재일, 단과대학, 학과, 논문제목, ...
    출력: year, department, metric_type, value (각 학과별 논문 수)

    Args:
        df: 논문 목록 DataFrame

    Returns:
        "pd.DataFrame": 표준 형식으로 변환된 DataFrame
    """
    # 게재일에서 연도 추출
    df["year"] = pd.to_datetime(df["게재일"], errors="coerce").dt.year.astype(int)

    # 부서명 정규화
    df["department"] = df["학과"].map(lambda x: ALLOWED_DEPARTMENTS.get(x, x))

    # 학과별, 연도별 논문 수 집계
    df_grouped = df.groupby(["year", "department"]).size().reset_index(name="value")

    # metric_type 추가
    df_grouped["metric_type"] = "PUBLICATION"

    # 최종 컬럼 선택
    df_result = df_grouped[["year", "department", "metric_type", "value"]].copy()

    return df_result


def _transform_research_project(df: "pd.DataFrame") -> "pd.DataFrame":
    """
    research_project_data.csv를 표준 형식으로 변환

    입력: 집행ID, 과제번호, 과제명, 연구책임자, 소속학과, 집행일자, 집행금액, ...
    출력: year, department, metric_type, value (연도별 연구비)

    Args:
        df: 연구 과제 DataFrame

    Returns:
        "pd.DataFrame": 표준 형식으로 변환된 DataFrame
    """
    # 집행일자에서 연도 추출
    df["year"] = pd.to_datetime(df["집행일자"], errors="coerce").dt.year.astype(int)

    # 부서명 정규화
    df["department"] = df["소속학과"].map(lambda x: ALLOWED_DEPARTMENTS.get(x, x))

    # 집행금액을 숫자로 변환
    df["execution_amount"] = pd.to_numeric(df["집행금액"], errors="coerce")

    # 학과별, 연도별 연구비 합계
    df_grouped = df.groupby(["year", "department"])["execution_amount"].sum().reset_index(name="value")

    # metric_type 추가
    df_grouped["metric_type"] = "RESEARCH_BUDGET"

    # 최종 컬럼 선택
    df_result = df_grouped[["year", "department", "metric_type", "value"]].copy()

    return df_result


def _transform_student_roster(df: "pd.DataFrame") -> "pd.DataFrame":
    """
    student_roster.csv를 표준 형식으로 변환

    입력: 학번, 이름, 단과대학, 학과, 학년, 입학년도, 학적상태, ...
    출력: year, department, metric_type, value (연도별 학생 수)

    Args:
        df: 학생 명단 DataFrame

    Returns:
        "pd.DataFrame": 표준 형식으로 변환된 DataFrame
    """
    # 입학년도를 연도로 사용
    df["year"] = df["입학년도"].astype(int)

    # 부서명 정규화
    df["department"] = df["학과"].map(lambda x: ALLOWED_DEPARTMENTS.get(x, x))

    # 학적상태가 '재학'인 학생만 카운트
    df_active = df[df["학적상태"] == "재학"].copy()

    # 학과별, 연도별 학생 수 집계
    df_grouped = df_active.groupby(["year", "department"]).size().reset_index(name="value")

    # metric_type 추가
    df_grouped["metric_type"] = "STUDENT_COUNT"

    # 최종 컬럼 선택
    df_result = df_grouped[["year", "department", "metric_type", "value"]].copy()

    return df_result
