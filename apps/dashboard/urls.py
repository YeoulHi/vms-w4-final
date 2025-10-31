"""Dashboard URL Configuration

Routes for dashboard page and chart data API endpoints.
Follows the specification in docs/3.prd.md
"""

from django.urls import path

from .views import DashboardView, ChartDataAPIView

app_name = "dashboard"

urlpatterns = [
    path("", DashboardView.as_view(), name="index"),
    path("api/chart-data/", ChartDataAPIView.as_view(), name="chart-data-api"),
]
