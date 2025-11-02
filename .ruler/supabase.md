---
description: PostgreSQL & Django 마이그레이션 관리 가이드
globs: "apps/**/*.py, config/settings.py"
---

# PostgreSQL & Django 마이그레이션 관리 가이드

**개요**: Supabase는 **PostgreSQL 호스팅 전용**으로 사용합니다. Supabase의 클라이언트 라이브러리, RLS, 벡터 검색 등 기능은 **사용하지 않습니다**. 대신 Django ORM과 마이그레이션 시스템으로 스키마를 관리합니다.

---

## 아키텍처 개요

```
┌─────────────────────────────────────┐
│   Django 애플리케이션               │
│   - ORM (models.py)                 │
│   - Migrations (0001_xxx.py)        │
│   - Settings (DATABASE 설정)        │
└─────────────────────────────────────┘
              ↓
     psycopg2 (드라이버)
              ↓
┌─────────────────────────────────────┐
│   Supabase (PostgreSQL)             │
│   - 프로덕션 데이터 저장소          │
│   - RLS 비활성화                    │
│   - Auth 테이블 미사용              │
└─────────────────────────────────────┘
```

---

## 필수 원칙 (MUST)

### 1. 절대 Raw SQL 사용 금지 → Django ORM 최우선

❌ **나쁜 예 (피하기)**
```python
# manage.py 쉘에서 직접 SQL 실행
from django.db import connection
cursor = connection.cursor()
cursor.execute("DROP TABLE dashboard_chartdata CASCADE;")  # 위험!
```

✅ **좋은 예**
```bash
# Django 마이그레이션으로만 스키마 변경
python manage.py makemigrations
python manage.py migrate
```

### 2. 모든 마이그레이션은 역방향(Revert) 가능해야 함

✅ **자동 생성된 마이그레이션 (Django가 역방향 자동 생성)**
```bash
python manage.py makemigrations
# 생성 결과:
# Migrations for 'ingest':
#   0003_add_metadata.py
#     - Add field metadata to excelupload
```

❌ **수동 SQL 마이그레이션 (역방향 작성 어려움)**
```python
# migrations/0003_manual.py
from django.db import migrations

def create_index(apps, schema_editor):
    schema_editor.execute("CREATE INDEX idx_dept_year ON dashboard_chartdata(department, year);")

def drop_index(apps, schema_editor):
    schema_editor.execute("DROP INDEX idx_dept_year;")

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(create_index, drop_index),
    ]
```

### 3. Supabase RLS(Row Level Security) 비활성화

Supabase 콘솔에서 **모든 테이블의 RLS를 비활성화**해야 합니다. Django는 애플리케이션 레벨에서 권한 관리를 수행합니다.

```sql
-- Supabase SQL 에디터에서 실행
ALTER TABLE dashboard_chartdata DISABLE ROW LEVEL SECURITY;
ALTER TABLE ingest_excelupload DISABLE ROW LEVEL SECURITY;
ALTER TABLE ingest_parsinglog DISABLE ROW LEVEL SECURITY;
```

### 4. 마이그레이션 파일명은 의미 있게

```bash
# 좋은 예
0001_initial.py                    # 초기 스키마
0002_create_chartdata_model.py     # 차트 데이터 모델 추가
0003_add_parsing_logs.py           # 파싱 로그 테이블 추가
0004_add_department_index.py       # 인덱스 추가
0005_alter_chartdata_constraints.py # 제약 조건 수정

# 나쁜 예 (의미 불명확)
auto_001.py
fix_bug.py
v2.py
```

### 5. 로컬 개발은 SQLite, 프로덕션은 PostgreSQL

```python
# config/settings.py

import os
from pathlib import Path

if os.getenv('ENVIRONMENT') == 'production':
    # 프로덕션: Supabase PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': '5432',
        }
    }
else:
    # 로컬: SQLite (개발 편의성)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

---

## 마이그레이션 워크플로우

### Step 1: 로컬에서 모델 정의 및 마이그레이션 생성

```python
# apps/ingest/models.py

from django.db import models

class ExcelUpload(models.Model):
    """사용자가 업로드한 엑셀 파일"""
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '대기중'),
            ('success', '성공'),
            ('failed', '실패'),
        ],
        default='pending'
    )

    class Meta:
        db_table = 'ingest_excelupload'
        ordering = ['-uploaded_at']
```

```bash
# 마이그레이션 파일 자동 생성
python manage.py makemigrations ingest
```

### Step 2: 로컬 SQLite에서 테스트

```bash
# 로컬 DB에 마이그레이션 적용
python manage.py migrate

# 스키마 확인
python manage.py showmigrations

# 데이터 조회 테스트
python manage.py shell
>>> from apps.ingest.models import ExcelUpload
>>> ExcelUpload.objects.all()
```

### Step 3: 마이그레이션 파일을 Supabase에 적용

```bash
# 환경 변수 설정 (Supabase 연결 정보)
export ENVIRONMENT=production
export DB_NAME=your_db_name
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_HOST=your-project.supabase.co
export DB_PORT=5432

# Supabase에 마이그레이션 적용
python manage.py migrate --database=default

# 확인
python manage.py showmigrations
```

---

## 권장 패턴 (SHOULD)

### 1. 마이그레이션 파일 구조화

```python
# migrations/0002_create_chartdata.py

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChartData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(max_length=100)),
                ('year', models.IntegerField()),
                ('value', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'dashboard_chartdata',
            },
        ),
        # 인덱스 추가 (조회 성능)
        migrations.AddIndex(
            model_name='chartdata',
            index=models.Index(fields=['department', 'year'], name='idx_dept_year'),
        ),
    ]
```

### 2. 필드별 제약 조건 명확히

```python
# apps/dashboard/models.py

class ChartData(models.Model):
    department = models.CharField(
        max_length=100,
        null=False,
        blank=False,  # Admin에서 입력 필수
        db_index=True  # 조회 최적화
    )
    year = models.IntegerField(
        null=False,
        blank=False,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)]
    )
    value = models.FloatField(
        null=False,
        blank=False,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_chartdata'
        # 학과+연도 조합은 unique
        unique_together = [['department', 'year']]
        indexes = [
            models.Index(fields=['department', 'year']),
            models.Index(fields=['year']),
        ]
        ordering = ['-year', 'department']
```

### 3. 데이터 마이그레이션 (시드 데이터 추가)

```python
# migrations/0003_add_initial_data.py

from django.db import migrations

def add_initial_data(apps, schema_editor):
    """초기 데이터 추가"""
    ChartData = apps.get_model('dashboard', 'ChartData')
    ChartData.objects.bulk_create([
        ChartData(department='컴퓨터과학과', year=2023, value=100),
        ChartData(department='경영학과', year=2023, value=85),
    ])

def delete_initial_data(apps, schema_editor):
    """초기 데이터 삭제 (롤백 시)"""
    ChartData = apps.get_model('dashboard', 'ChartData')
    ChartData.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_create_chartdata'),
    ]

    operations = [
        migrations.RunPython(add_initial_data, delete_initial_data),
    ]
```

### 4. 대용량 데이터는 배치로 처리

```python
# apps/ingest/services.py

def save_to_db_in_batches(data: list[dict], batch_size=1000):
    """대용량 데이터를 배치로 Upsert"""
    from django.db.models import F

    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]

        # bulk_create + update 조합
        objects = [
            ChartData(
                department=row['department'],
                year=row['year'],
                value=row['value']
            )
            for row in batch
        ]

        ChartData.objects.bulk_create(
            objects,
            update_conflicts=['value'],
            update_fields=['value'],
            unique_fields=['department', 'year']
        )
```

---

## 주의사항 (CAUTION)

### ❌ 피해야 할 패턴

1. **프로덕션 DB에서 직접 SQL 실행**
   - Supabase 콘솔의 SQL 에디터 사용 금지
   - 항상 Django 마이그레이션 사용

2. **마이그레이션 파일 수동 편집**
   ```python
   # 피하기
   # migrations/0001_initial.py를 손수 작성하기
   ```

3. **Supabase 기능 활용 (RLS, Realtime, Storage 등)**
   - PostgreSQL 호스팅 전용
   - Supabase Python 클라이언트 import 금지

4. **마이그레이션 순서 무시**
   ```bash
   # 피하기
   python manage.py migrate 0001_initial
   python manage.py migrate 0003_skip_0002  # 건너뛰기 금지!
   ```

---

## 트러블슈팅

### 문제: "django.db.utils.ProgrammingError: column already exists"

**원인**: 마이그레이션 파일이 이미 실행되었는데 다시 적용

**해결**:
```bash
# 현재 마이그레이션 상태 확인
python manage.py showmigrations

# 마이그레이션 기록 확인
python manage.py showmigrations --list

# 필요시 특정 마이그레이션으로 되돌리기 (개발 환경만)
python manage.py migrate dashboard 0001
```

### 문제: "role 'postgres' does not exist" (Supabase 연결 실패)

**원인**: 환경 변수 누락 또는 잘못된 자격증명

**해결**:
```bash
# .env 파일 확인
cat .env.local

# Supabase 콘솔에서 DB 자격증명 다시 확인
# Settings → Database → Connection String 복사

# 연결 테스트
python manage.py dbshell
```

### 문제: 마이그레이션 순환 의존성

**원인**: 두 마이그레이션이 서로를 의존

**해결**: 마이그레이션 파일의 `dependencies` 순서 재정렬
```python
# migrations/0003_bad.py
class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0002_chartdata'),
    ]
    # ✅ 올바른 의존성
```

---

## PostgreSQL 최적화 팁

### 1. 인덱스 전략

```python
# 자주 조회되는 필드에 인덱스 추가
class ChartData(models.Model):
    department = models.CharField(max_length=100, db_index=True)
    year = models.IntegerField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['department', 'year']),  # 복합 인덱스
        ]
```

### 2. 쿼리 최적화

```python
# N+1 쿼리 문제 해결
queryset = ChartData.objects.select_related('department').all()
# 또는
queryset = ChartData.objects.prefetch_related('related_field').all()
```

### 3. 대용량 조회는 `.only()` / `.defer()` 사용

```python
# 필요한 필드만 조회
queryset = ChartData.objects.only('department', 'year', 'value')

# 또는 특정 필드 제외
queryset = ChartData.objects.defer('large_text_field')
```

---

## 환경 설정 체크리스트

- [ ] `.env.local`에 `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` 설정
- [ ] `requirements.txt`에 `psycopg2-binary` 포함
- [ ] 로컬에서 `python manage.py migrate` 성공
- [ ] Supabase RLS 모두 비활성화
- [ ] `settings.py`의 `DATABASES` 설정 환경별 구분
- [ ] `.env.local`는 `.gitignore`에 포함
- [ ] 프로덕션 배포 전 마이그레이션 테스트 완료

---

## 참고 자료

- [Django 공식 문서: Migrations](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [Supabase 문서: Connecting to Database](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [PostgreSQL 최적화 가이드](https://wiki.postgresql.org/wiki/Performance_Optimization)
