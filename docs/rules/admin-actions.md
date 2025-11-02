# Django Admin 액션 규칙

## 파일 업로드 커스텀 URL + View

```python
class MetricRecordAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        return [
            path("upload/", self.admin_site.admin_view(self.upload_excel),
                 name="ingest_metricrecord_upload"),
        ] + urls

    def upload_excel(self, request):
        if request.method == "POST":
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    file_obj = request.FILES["file"]
                    success_count, failure_count, message = parse_and_save_excel(file_obj)
                    messages.success(request, f"Upload complete: {message}")
                    return HttpResponseRedirect(reverse("admin:ingest_metricrecord_changelist"))
                except ValidationError as e:
                    messages.error(request, f"Upload failed: {str(e)}")
        else:
            form = ExcelUploadForm()

        return TemplateResponse(request, "admin/ingest/upload.html", {"form": form})
```

## 파일 업로드 Form (DB 테이블 없음)

```python
class ExcelUploadForm(forms.Form):
    """DB 테이블 생성 안 하는 폼"""
    file = forms.FileField(
        label="Excel/CSV File",
        widget=forms.FileInput(attrs={"accept": ".xlsx,.xls,.csv"})
    )

    def clean_file(self):
        file = self.cleaned_data["file"]
        allowed = {'.xlsx', '.xls', '.csv'}
        if not any(file.name.lower().endswith(ext) for ext in allowed):
            raise ValidationError("File format not allowed")
        return file
```

## 권한 제어

```python
def has_add_permission(self, request):
    return False  # 직접 추가 비활성화 (Upload만 사용)

def has_change_permission(self, request, obj=None):
    return request.user.is_staff  # Staff만 수정 가능
```
