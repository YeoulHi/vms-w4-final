"""Django Admin Configuration for Ingest App

Registers models and provides admin interfaces with permission controls.
Follows the specification in docs/4.userflow.md (UserFlow #02)
"""

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import MetricRecord


@admin.register(MetricRecord)
class MetricRecordAdmin(admin.ModelAdmin):
    """Admin interface for MetricRecord model.

    This admin interface allows staff users to manage metric records.
    Only users with is_staff=True can access this interface.

    Attributes:
        list_display: Columns displayed in list view
        list_filter: Filters available in sidebar
        search_fields: Fields available for search
        readonly_fields: Fields that cannot be edited
    """

    list_display = ("year", "department", "metric_type", "metric_value", "updated_at")
    list_filter = ("year", "department", "metric_type")
    search_fields = ("department", "metric_type")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Metric Information",
            {
                "fields": ("year", "department", "metric_type", "metric_value"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def has_add_permission(self, request: object) -> bool:
        """Check if user can add new records.

        In MVP, direct addition through admin is restricted.
        Data should be uploaded via the ingest Excel/CSV upload feature.

        Returns:
            bool: False (upload via files only)
        """
        return False

    def has_change_permission(self, request: object, obj: object = None) -> bool:
        """Check if user can change records.

        Returns:
            bool: True if user is staff, False otherwise
        """
        return request.user.is_staff  # type: ignore

    def has_delete_permission(self, request: object, obj: object = None) -> bool:
        """Check if user can delete records.

        Returns:
            bool: True if user is staff, False otherwise
        """
        return request.user.is_staff  # type: ignore

    def has_view_permission(self, request: object, obj: object = None) -> bool:
        """Check if user can view records.

        Returns:
            bool: True if user is staff, False otherwise
        """
        return request.user.is_staff  # type: ignore

