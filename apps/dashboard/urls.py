"""Dashboard URL Configuration

Routes for dashboard page and chart data API endpoints.
Follows the specification in docs/3.prd.md and docs/spec/003-spec-대시보드-조회.md

URL Patterns:
    - GET /dashboard/ → DashboardView (template rendering)
    - GET /api/dashboard/chart-data/ → ChartDataAPIView (JSON API)
"""

from django.urls import path

from .views import DashboardView, ChartDataAPIView

app_name = "dashboard"

# Main view patterns - accessible at /dashboard/
page_patterns = [
    path("", DashboardView.as_view(), name="index"),
]

# API patterns - accessible at /api/dashboard/
api_patterns = [
    path("chart-data/", ChartDataAPIView.as_view(), name="chart-data-api"),
]

urlpatterns = page_patterns + api_patterns
