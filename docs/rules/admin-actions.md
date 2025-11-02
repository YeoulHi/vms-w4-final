# Django Admin 액션 규칙

## Admin 파일 업로드 액션 패턴

```python
from django.contrib import admin, messages
from apps.ingest.models import ExcelUpload
from apps.ingest.services import parse_excel_defensively, save_to_db

@admin.action(description="선택된 파일 파싱 및 DB 저장")
def parse_and_save(modeladmin, request, queryset):
    success_count = 0
    for upload in queryset:
        try:
            data, errors = parse_excel_defensively(upload.file.path)

            if errors:
                messages.error(request, f"{upload.file}: {', '.join(errors)}")
                continue

            saved = save_to_db(data)
            upload.parsed_status = 'success'
            upload.save()

            success_count += 1
            messages.success(request, f"{upload.file}: {saved}개 레코드 저장")

        except Exception as e:
            upload.parsed_status = 'failed'
            upload.save()
            messages.error(request, f"{upload.file}: {e}")

    messages.info(request, f"총 {success_count}개 파일 처리 완료")


@admin.register(ExcelUpload)
class ExcelUploadAdmin(admin.ModelAdmin):
    list_display = ['file', 'uploaded_at', 'parsed_status']
    list_filter = ['parsed_status', 'uploaded_at']
    actions = [parse_and_save]

    def get_readonly_fields(self, request):
        return ['parsed_status']
```

## 액션 설계 원칙

1. **한 가지 역할만** (파싱, 저장 등)
2. **에러 처리 필수** (try-except)
3. **사용자 피드백** (messages)
4. **상태 기록** (parsed_status)
5. **로깅** (logger.info/error)

## 자주 사용하는 액션

```python
# 상태 변경
@admin.action(description="상태를 '성공'으로 변경")
def mark_success(modeladmin, request, queryset):
    count = queryset.update(parsed_status='success')
    messages.success(request, f"{count}개 항목 업데이트 완료")

# 데이터 재처리
@admin.action(description="선택된 항목 재파싱")
def reparse(modeladmin, request, queryset):
    queryset.update(parsed_status='pending')
    messages.info(request, "재파싱 대기 중")
```

## Admin 조회 최적화

```python
class ExcelUploadAdmin(admin.ModelAdmin):
    list_select_related = ['user']  # FK 조회 최적화
    list_prefetch_related = ['chartdata_set']  # M2M/역 관계 최적화
    search_fields = ['file']
    date_hierarchy = 'uploaded_at'  # 날짜별 필터링
```
