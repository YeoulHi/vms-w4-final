"""Ingest Service - Excel/CSV parsing and data persistence

This module handles Excel/CSV file parsing, data normalization, and database UPSERT.
Implements the core logic for UserFlow #02 (Admin Excel Upload).
"""

from typing import List, Dict, Any, Tuple, Optional
from decimal import Decimal

import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import MetricRecord


ALLOWED_DEPARTMENTS = {
    "computer-science": "computer-science",
    "electronics": "electronics",
}

ALLOWED_METRICS = {
    "paper": "PAPER",
    "budget": "BUDGET",
    "student": "STUDENT",
    "project": "PROJECT",
    "PAPER": "PAPER",
    "BUDGET": "BUDGET",
    "STUDENT": "STUDENT",
    "PROJECT": "PROJECT",
}

ALLOWED_FILE_EXTENSIONS = {".xlsx", ".xls", ".csv"}
REQUIRED_COLUMNS = {"year", "department", "metric_type", "value"}
FAILURE_THRESHOLD_PERCENTAGE = 20


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

        _validate_columns(df)

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


def _validate_columns(df: pd.DataFrame) -> None:
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


def _process_rows(df: pd.DataFrame) -> Dict[str, int]:
    """
    Process each row: normalize, validate, and upsert to database.

    Args:
        df: pandas DataFrame with validated columns

    Returns:
        dict: {"success_count": int, "failure_count": int}
    """
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
