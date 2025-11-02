"""Dashboard Views - Template rendering and API endpoints

This module provides views for the dashboard page and chart data API.
Follows the specification in docs/4.userflow.md and docs/5.dataflow.md
"""

from typing import Any, Dict

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import get_dashboard_data, to_chartjs


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard page view - displays chart data visualization.

    This view renders the main dashboard template with default filter values.
    Only authenticated users can access this view.

    Attributes:
        template_name: Path to the dashboard template
        login_url: URL to redirect unauthenticated users (default: /login/)
    """

    template_name = "dashboard/index.html"
    login_url = "login"
    redirect_field_name = "next"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add default filter values to template context.

        According to docs/4.userflow.md and docs/spec/003, the backend must
        provide default filter values (최신 3개년, 전체 학과) through the template context.

        Returns:
            dict: Context with default_filters containing years and departments
        """
        context = super().get_context_data(**kwargs)

        try:
            # Get all unique years from database, sorted descending
            from apps.ingest.models import MetricRecord

            all_years = (
                MetricRecord.objects.values_list("year", flat=True).distinct().order_by("-year")
            )
            all_years_list = list(all_years)

            # Get latest 3 years
            latest_three_years = all_years_list[:3] if all_years_list else []

            # Get all departments
            all_departments = (
                MetricRecord.objects.values_list("department", flat=True).distinct().order_by("department")
            )

            # Build default_filters context for frontend
            context["default_filters"] = {
                "years": latest_three_years,
                "all_years": all_years_list,
                "departments": list(all_departments),
                "default_year": latest_three_years[0] if latest_three_years else None,
            }
        except Exception as e:
            # Handle database errors gracefully
            context["default_filters"] = {
                "years": [],
                "all_years": [],
                "departments": [],
                "default_year": None,
            }

        return context


class ChartDataAPIView(APIView):
    """API endpoint for retrieving chart data.

    Provides JSON response with chart data based on filter parameters.
    Only authenticated users can access this endpoint.

    URL: GET /api/dashboard/chart-data/?year=YYYY&department=DEPT_NAME
    """

    def dispatch(self, request, *args, **kwargs):
        """Check authentication before processing request."""
        if not request.user.is_authenticated:
            return Response(
                {"error": "unauthorized", "message": "인증이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: Any) -> Response:
        """Handle GET request for chart data.

        Query Parameters:
            year (optional): Filter by year (int)
            department (optional): Filter by department name (str)

        Returns:
            Response: Chart.js compatible JSON or error response
                - 200: Successful response with chart data
                - 400: Invalid parameters
                - 401: Unauthorized (handled by @login_required decorator)
        """
        try:
            # Extract and validate query parameters
            year_param = request.GET.get("year")
            department_param = request.GET.get("department")

            year = None
            if year_param is not None and year_param != "":
                try:
                    year = int(year_param)
                except (ValueError, TypeError):
                    return Response(
                        {"error": "invalid_parameter"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            department = department_param if department_param and department_param != "" else None

            # Retrieve and transform data
            records = get_dashboard_data(year=year, department=department)
            chart_data = to_chartjs(records)

            return Response(chart_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the error in production
            return Response(
                {"error": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
