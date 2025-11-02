"""Django Admin Configuration for Ingest App

Registers models and provides admin interfaces with permission controls.
Implements Excel/CSV upload functionality (UserFlow #02).
"""

from typing import Any
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse, path
from django.template.response import TemplateResponse

from .models import MetricRecord
from .services import parse_and_save_excel


class ExcelUploadForm(forms.Form):
    """Form for Excel/CSV file upload"""

    file = forms.FileField(
        label="Excel/CSV File",
        help_text="Allowed formats: .xlsx, .xls, .csv",
        widget=forms.FileInput(attrs={"accept": ".xlsx,.xls,.csv"}),
    )

    def clean_file(self) -> Any:
        """Validate file extension"""
        file = self.cleaned_data["file"]
        filename = file.name.lower()

        allowed_extensions = {".xlsx", ".xls", ".csv"}
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise ValidationError(
                f"File format not allowed. Allowed: {', '.join(allowed_extensions)}"
            )

        return file


@admin.register(MetricRecord)
class MetricRecordAdmin(admin.ModelAdmin):
    """Admin interface for MetricRecord model"""

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
        """Direct addition is disabled - use Excel upload instead"""
        return False

    def has_change_permission(self, request: object, obj: object = None) -> bool:
        """Only staff can edit"""
        return request.user.is_staff  # type: ignore

    def has_delete_permission(self, request: object, obj: object = None) -> bool:
        """Only staff can delete"""
        return request.user.is_staff  # type: ignore

    def has_view_permission(self, request: object, obj: object = None) -> bool:
        """Only staff can view"""
        return request.user.is_staff  # type: ignore

    def get_urls(self) -> list:
        """Add custom URL for Excel upload"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "upload/",
                self.admin_site.admin_view(self.upload_excel),
                name="ingest_metricrecord_upload",
            ),
        ]
        return custom_urls + urls

    def upload_excel(self, request: Any) -> TemplateResponse:
        """Handle Excel file upload"""
        if request.method == "POST":
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    file_obj = request.FILES["file"]
                    success_count, failure_count, summary_message = parse_and_save_excel(file_obj)

                    messages.success(
                        request,
                        f"Upload complete: {summary_message}",
                    )

                    return HttpResponseRedirect(
                        reverse("admin:ingest_metricrecord_changelist")
                    )

                except ValidationError as e:
                    messages.error(request, f"Upload failed: {str(e)}")
                except Exception as e:
                    messages.error(request, f"Unexpected error: {str(e)}")
        else:
            form = ExcelUploadForm()

        context = {
            "title": "Upload Excel Data",
            "form": form,
            "opts": self.model._meta,
            "site_header": self.admin_site.site_header,
            "site_title": self.admin_site.site_title,
        }

        return TemplateResponse(request, "admin/ingest/upload.html", context)
