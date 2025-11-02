"""Dashboard Tests - Unit and Integration Tests

Tests for dashboard views, services, and utilities following TDD approach.
Follows the specification in docs/rules/tdd.md and docs/spec/003-plan-대시보드-조회.md

Test Coverage:
  - DashboardView: Default filter context
  - ChartDataAPIView: Parameter validation and response
  - get_dashboard_data: Filtering logic
  - to_chartjs: Data transformation
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
import json

from apps.ingest.models import MetricRecord
from apps.dashboard.services import get_dashboard_data, to_chartjs


class MetricRecordTestFixture(TestCase):
    """Fixture for tests - creates sample metric records."""

    def setUp(self):
        """Create test user and sample data."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Create sample metric records
        self.records = [
            MetricRecord.objects.create(
                year=2023,
                department="컴퓨터공학과",
                metric_type="PAPER",
                metric_value=Decimal("10.0000"),
            ),
            MetricRecord.objects.create(
                year=2023,
                department="컴퓨터공학과",
                metric_type="BUDGET",
                metric_value=Decimal("1000.0000"),
            ),
            MetricRecord.objects.create(
                year=2024,
                department="컴퓨터공학과",
                metric_type="PAPER",
                metric_value=Decimal("15.0000"),
            ),
            MetricRecord.objects.create(
                year=2024,
                department="경영학과",
                metric_type="PAPER",
                metric_value=Decimal("8.0000"),
            ),
            MetricRecord.objects.create(
                year=2025,
                department="컴퓨터공학과",
                metric_type="PAPER",
                metric_value=Decimal("20.0000"),
            ),
        ]


class GetDashboardDataTests(MetricRecordTestFixture):
    """Test get_dashboard_data function - data retrieval and filtering."""

    def test_get_all_records_without_filters(self):
        """TC-01: Retrieve all records when no filters applied."""
        records = get_dashboard_data()
        self.assertEqual(len(records), 5)

    def test_get_records_filtered_by_year(self):
        """TC-02: Retrieve records filtered by year."""
        records = get_dashboard_data(year=2023)
        self.assertEqual(len(records), 2)
        for record in records:
            self.assertEqual(record["year"], 2023)

    def test_get_records_filtered_by_department(self):
        """TC-03: Retrieve records filtered by department."""
        records = get_dashboard_data(department="컴퓨터공학과")
        self.assertEqual(len(records), 4)
        for record in records:
            self.assertEqual(record["department"], "컴퓨터공학과")

    def test_get_records_with_combined_filters(self):
        """TC-04: Retrieve records with year and department filters."""
        records = get_dashboard_data(year=2024, department="컴퓨터공학과")
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["year"], 2024)
        self.assertEqual(record["department"], "컴퓨터공학과")
        self.assertEqual(record["metric_type"], "PAPER")

    def test_get_empty_results_for_nonexistent_filter(self):
        """TC-05: Return empty list for non-existent department."""
        records = get_dashboard_data(department="존재하지않는학과")
        self.assertEqual(len(records), 0)

    def test_records_ordered_by_year_and_department(self):
        """TC-06: Verify records are ordered correctly."""
        records = get_dashboard_data()
        self.assertGreaterEqual(records[0]["year"], records[1]["year"])


class ToChartjsTests(MetricRecordTestFixture):
    """Test to_chartjs function - data transformation to Chart.js format."""

    def test_empty_records_returns_empty_chartjs(self):
        """TC-07: Empty records should return empty Chart.js format."""
        result = to_chartjs([])
        self.assertEqual(result["labels"], [])
        self.assertEqual(result["datasets"], [])

    def test_single_metric_type_single_year(self):
        """TC-08: Single metric type across single year."""
        records = get_dashboard_data(year=2023, department="컴퓨터공학과")
        # Filter only PAPER records
        paper_records = [r for r in records if r["metric_type"] == "PAPER"]
        result = to_chartjs(paper_records)

        self.assertIn("2023", result["labels"])
        self.assertEqual(len(result["datasets"]), 1)
        self.assertEqual(result["datasets"][0]["label"], "PAPER")

    def test_multiple_metric_types_multiple_years(self):
        """TC-09: Multiple metric types across multiple years."""
        records = get_dashboard_data(department="컴퓨터공학과")
        result = to_chartjs(records)

        # Should have 3 years: 2023, 2024, 2025
        self.assertEqual(len(result["labels"]), 3)
        self.assertIn("2023", result["labels"])
        self.assertIn("2024", result["labels"])
        self.assertIn("2025", result["labels"])

        # Should have PAPER and BUDGET metric types
        metric_types = [ds["label"] for ds in result["datasets"]]
        self.assertIn("PAPER", metric_types)
        self.assertIn("BUDGET", metric_types)

    def test_chartjs_format_has_required_keys(self):
        """TC-10: Chart.js format contains required keys."""
        records = get_dashboard_data()
        result = to_chartjs(records)

        self.assertIn("labels", result)
        self.assertIn("datasets", result)
        self.assertIsInstance(result["labels"], list)
        self.assertIsInstance(result["datasets"], list)

    def test_dataset_has_required_fields(self):
        """TC-11: Each dataset has label and data fields."""
        records = get_dashboard_data()
        result = to_chartjs(records)

        for dataset in result["datasets"]:
            self.assertIn("label", dataset)
            self.assertIn("data", dataset)
            self.assertIn("backgroundColor", dataset)
            self.assertIsInstance(dataset["data"], list)


class DashboardViewTests(MetricRecordTestFixture):
    """Test DashboardView - template rendering and context."""

    def setUp(self):
        """Initialize test client and authenticate."""
        super().setUp()
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

    def test_dashboard_page_requires_authentication(self):
        """TC-12: Dashboard page requires login."""
        client = Client()
        response = client.get("/dashboard/")
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_page_renders_template(self):
        """TC-13: Dashboard page renders with correct template."""
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")

    def test_dashboard_context_has_default_filters(self):
        """TC-14: Dashboard context includes default_filters."""
        response = self.client.get("/dashboard/")
        self.assertIn("default_filters", response.context)

    def test_default_filters_contain_required_keys(self):
        """TC-15: default_filters contains years and departments."""
        response = self.client.get("/dashboard/")
        default_filters = response.context["default_filters"]

        self.assertIn("years", default_filters)
        self.assertIn("departments", default_filters)
        self.assertIn("default_year", default_filters)

    def test_default_filters_latest_three_years(self):
        """TC-16: default_filters.years contains latest 3 years."""
        response = self.client.get("/dashboard/")
        default_filters = response.context["default_filters"]
        years = default_filters["years"]

        # Should have up to 3 years
        self.assertLessEqual(len(years), 3)
        # Years should be sorted descending
        self.assertEqual(years, sorted(years, reverse=True))

    def test_default_filters_all_departments(self):
        """TC-17: default_filters.departments contains all departments."""
        response = self.client.get("/dashboard/")
        default_filters = response.context["default_filters"]
        departments = default_filters["departments"]

        # Should include both departments
        self.assertIn("컴퓨터공학과", departments)
        self.assertIn("경영학과", departments)


class ChartDataAPIViewTests(MetricRecordTestFixture):
    """Test ChartDataAPIView - API endpoint for chart data."""

    def setUp(self):
        """Initialize test client and authenticate."""
        super().setUp()
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

    def test_api_endpoint_requires_authentication(self):
        """TC-18: API endpoint requires login."""
        client = Client()
        response = client.get("/api/dashboard/chart-data/")
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_api_returns_json(self):
        """TC-19: API returns JSON response."""
        response = self.client.get("/api/dashboard/chart-data/")
        self.assertEqual(response["Content-Type"], "application/json")

    def test_api_returns_chartjs_format(self):
        """TC-20: API response is Chart.js compatible."""
        response = self.client.get("/api/dashboard/chart-data/")
        data = response.json()

        self.assertIn("labels", data)
        self.assertIn("datasets", data)

    def test_api_with_year_filter(self):
        """TC-21: API responds to year parameter."""
        response = self.client.get("/api/dashboard/chart-data/?year=2023")
        data = response.json()

        self.assertIn("labels", data)
        self.assertIn("2023", data["labels"])

    def test_api_with_department_filter(self):
        """TC-22: API responds to department parameter."""
        response = self.client.get(
            "/api/dashboard/chart-data/?department=컴퓨터공학과"
        )
        self.assertEqual(response.status_code, 200)

    def test_api_with_both_filters(self):
        """TC-23: API responds to combined filters."""
        response = self.client.get(
            "/api/dashboard/chart-data/?year=2024&department=컴퓨터공학과"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("labels", data)

    def test_api_invalid_year_returns_400(self):
        """TC-24: Invalid year parameter returns 400."""
        response = self.client.get("/api/dashboard/chart-data/?year=invalid")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["error"], "invalid_parameter")

    def test_api_empty_filters_returns_all_data(self):
        """TC-25: Empty filters return all data."""
        response = self.client.get("/api/dashboard/chart-data/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data["labels"]), 0)

    def test_api_nonexistent_department_returns_empty(self):
        """TC-26: Non-existent department returns empty chart."""
        response = self.client.get(
            "/api/dashboard/chart-data/?department=존재하지않는학과"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["labels"], [])
        self.assertEqual(data["datasets"], [])

