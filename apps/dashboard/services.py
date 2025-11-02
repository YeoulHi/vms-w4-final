"""Dashboard Service - Data retrieval and transformation

This module handles dashboard data retrieval and transformation to Chart.js format.
Follows the specification in docs/5.dataflow.md and docs/spec/003.

Example:
    from apps.dashboard.services import get_dashboard_data, to_chartjs

    data = get_dashboard_data(year=2024, department="컴퓨터공학")
    chart_json = to_chartjs(data)
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal

from apps.ingest.models import MetricRecord


def get_dashboard_data(
    year: Optional[int] = None, department: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve metric records from database based on filters.

    Args:
        year: Optional year filter (if None, includes all years)
        department: Optional department filter (if None, includes all departments)

    Returns:
        List of dictionaries with metric data: [
            {'year': int, 'department': str, 'metric_type': str, 'metric_value': Decimal}
        ]
    """
    queryset = MetricRecord.objects.all()

    if year is not None:
        queryset = queryset.filter(year=year)

    if department is not None and department != "":
        queryset = queryset.filter(department=department)

    records = queryset.values("year", "department", "metric_type", "metric_value").order_by(
        "year", "department", "metric_type"
    )

    return list(records)


def to_chartjs(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert metric records to Chart.js compatible format.

    This function transforms database records into a format that Chart.js
    can directly render. It groups data by metric_type and creates datasets.

    Args:
        records: List of dictionaries from get_dashboard_data()

    Returns:
        dict: Chart.js compatible JSON with structure:
            {
                'labels': ['2023', '2024', '2025'],
                'datasets': [
                    {
                        'label': 'Papers',
                        'data': [10, 15, 20],
                        'backgroundColor': '#4A90E2'
                    }
                ]
            }
    """
    if not records:
        return {"labels": [], "datasets": []}

    # Extract unique years and sort them
    years = sorted(set(record.get("year") for record in records if record.get("year")))
    labels = [str(year) for year in years]

    if not labels:
        return {"labels": [], "datasets": []}

    # Group by metric_type and year
    datasets_map: Dict[str, Dict[str, Any]] = {}

    for record in records:
        metric_type = record.get("metric_type", "Unknown")
        year = record.get("year")
        value = record.get("metric_value", 0)

        if metric_type not in datasets_map:
            datasets_map[metric_type] = {
                "label": metric_type,
                "data": [0] * len(labels),  # Initialize with zeros
                "backgroundColor": _get_color_for_metric(metric_type),
            }

        # Find index of the year in labels and set the value
        year_index = labels.index(str(year))
        datasets_map[metric_type]["data"][year_index] = float(value)

    datasets = list(datasets_map.values())

    return {"labels": labels, "datasets": datasets}


def _get_color_for_metric(metric_type: str) -> str:
    """Get a color for a given metric type.

    Args:
        metric_type: The type of metric (e.g., 'PAPER', 'BUDGET', 'STUDENT')

    Returns:
        str: Hex color code for the metric type
    """
    color_map = {
        "PAPER": "#4A90E2",  # Blue
        "BUDGET": "#50E3C2",  # Teal
        "STUDENT": "#F5A623",  # Orange
        "PROJECT": "#BD10E0",  # Purple
    }
    return color_map.get(metric_type, "#999999")  # Default gray
