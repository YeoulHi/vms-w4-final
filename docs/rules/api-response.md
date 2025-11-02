# DRF API 응답 포맷 규칙

## 통일된 응답 포맷

### 성공 응답 (200, 201)

```json
{
    "success": true,
    "data": {},
    "error": null
}
```

### 에러 응답 (400, 500 등)

```json
{
    "success": false,
    "data": null,
    "error": {
        "message": "에러 메시지",
        "code": "ERROR_CODE"
    }
}
```

## DRF View 구현

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class BaseAPIView(APIView):
    """응답 포맷 통일"""

    def success_response(self, data, status_code=200):
        return Response(
            {"success": True, "data": data, "error": None},
            status=status_code
        )

    def error_response(self, message, code, status_code=400):
        return Response(
            {
                "success": False,
                "data": None,
                "error": {"message": message, "code": code}
            },
            status=status_code
        )

class ChartDataView(BaseAPIView):
    def get(self, request):
        try:
            data = fetch_chart_data()
            return self.success_response(data)
        except Exception as e:
            return self.error_response(str(e), "CHART_ERROR", 500)
```

## Serializer 검증 에러

```python
from rest_framework import serializers

class ChartDataSerializer(serializers.Serializer):
    department = serializers.CharField()
    year = serializers.IntegerField()

    def validate_year(self, value):
        if not (1900 <= value <= 2100):
            raise serializers.ValidationError("유효한 연도 아님")
        return value

# View에서
serializer = ChartDataSerializer(data=request.data)
if not serializer.is_valid():
    return error_response(
        str(serializer.errors),
        "VALIDATION_ERROR",
        400
    )
```

## API URL 패턴

```
/api/dashboard/chart-data/     # 차트 데이터 조회 (GET, 필터 가능)
/api/dashboard/chart-data/?department=CS&year=2023
```
