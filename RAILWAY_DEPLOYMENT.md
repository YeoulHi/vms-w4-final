# Railway + Supabase 배포 가이드

## 사전 준비사항

### 1. Supabase 설정 확인
이미 `.env.local`에 Supabase 정보가 설정되어 있습니다:
- DB_HOST: `zzyovbiajuotsjttpqns.supabase.co`
- DB_NAME: `postgres`
- DB_USER: `postgres`
- DB_PASSWORD: `mNks7peUSQlm2nFA`
- DB_PORT: `5432`

### 2. Supabase RLS 비활성화
1. Supabase 대시보드 접속: https://supabase.com/dashboard
2. 프로젝트 선택
3. SQL Editor 열기
4. `supabase-setup.sql` 파일의 내용을 복사하여 실행

```sql
-- 또는 간단하게 모든 테이블의 RLS 비활성화
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        EXECUTE 'ALTER TABLE ' || quote_ident(r.tablename) || ' DISABLE ROW LEVEL SECURITY';
    END LOOP;
END $$;
```

---

## Railway 배포 단계

### 1. Railway 계정 생성 및 프로젝트 연결

1. **Railway 계정 생성**
   - https://railway.app 접속
   - GitHub 계정으로 로그인

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - `w6-8-final-duwls` 저장소 선택

### 2. Railway 환경 변수 설정

Railway 대시보드에서 **Variables** 탭을 열고 다음 환경 변수를 추가하세요:

#### 필수 환경 변수

```bash
# Django 기본 설정
SECRET_KEY=<강력한-랜덤-키를-생성하세요>
DEBUG=False
ALLOWED_HOSTS=*.railway.app,yourdomain.com
DJANGO_SETTINGS_MODULE=config.settings

# Supabase PostgreSQL 연결
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=mNks7peUSQlm2nFA
DB_HOST=zzyovbiajuotsjttpqns.supabase.co
DB_PORT=5432

# SQLite 사용 안함 (프로덕션)
USE_SQLITE=false
```

#### SECRET_KEY 생성 방법

Python으로 강력한 SECRET_KEY 생성:

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

또는 온라인 생성기:
- https://djecrety.ir/

### 3. Railway 설정 파일 확인

프로젝트에 이미 생성된 파일들:

✅ `Procfile` - Railway가 앱을 시작하는 방법 정의
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
```

✅ `runtime.txt` - Python 버전 지정
```
python-3.13
```

✅ `railway.toml` - Railway 빌드 설정

✅ `requirements-prod.txt` - 배포용 의존성 목록

### 4. 배포 실행

1. **코드 푸시**
   ```bash
   git add .
   git commit -m "feat: Railway 배포 설정 추가"
   git push origin master
   ```

2. **Railway 자동 배포**
   - Railway가 자동으로 빌드 시작
   - 빌드 로그 확인 (Deployments 탭)
   - 마이그레이션 자동 실행 (Procfile의 release 명령)

3. **배포 확인**
   - Railway 대시보드에서 "View Logs" 클릭
   - 에러 없이 완료되면 성공

---

## 배포 후 작업

### 1. 슈퍼유저 생성

Railway CLI로 접속하여 슈퍼유저 생성:

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 연결
railway link

# 슈퍼유저 생성
railway run python manage.py createsuperuser
```

또는 Railway 대시보드에서:
- Settings → Deploy → Custom Start Command에서 일회성으로 실행

### 2. 정적 파일 확인

배포 후 자동으로 `collectstatic`이 실행됩니다.

확인 방법:
- `https://your-app.railway.app/admin` 접속
- CSS가 정상적으로 로드되는지 확인

### 3. 데이터베이스 마이그레이션 확인

Railway 로그에서 다음 메시지 확인:
```
Running migrations:
  Applying dashboard.0001_initial... OK
  Applying ingest.0001_initial... OK
```

### 4. 앱 URL 확인

- Railway 대시보드에서 "Deployments" 탭
- 생성된 URL 확인 (예: `https://w6-8-final-duwls-production.up.railway.app`)

---

## 커스텀 도메인 연결 (선택사항)

### 1. Railway에 도메인 추가
1. Railway 대시보드 → Settings → Domains
2. "Custom Domain" 클릭
3. 도메인 입력 (예: `dashboard.yourdomain.com`)

### 2. DNS 설정
Railway가 제공하는 DNS 레코드를 도메인 관리 페이지에 추가:
- CNAME 레코드: `dashboard` → `your-app.up.railway.app`

### 3. ALLOWED_HOSTS 업데이트
Railway 환경 변수에서:
```
ALLOWED_HOSTS=*.railway.app,dashboard.yourdomain.com
```

---

## 로컬에서 프로덕션 DB 테스트 (선택사항)

로컬에서 Supabase DB에 연결하여 테스트:

```bash
# .env.local 수정
USE_SQLITE=false

# 마이그레이션 실행
python manage.py migrate

# 개발 서버 실행
python manage.py runserver

# 슈퍼유저 생성
python manage.py createsuperuser
```

**주의**: 프로덕션 DB를 로컬에서 테스트할 때는 데이터를 신중하게 다루세요!

---

## 배포 체크리스트

배포 전:
- [ ] `.env.local` 파일이 `.gitignore`에 포함됨
- [ ] `requirements-prod.txt` 의존성 확인
- [ ] `SECRET_KEY` 강력한 값으로 생성
- [ ] Supabase RLS 비활성화 완료

Railway 설정:
- [ ] 모든 환경 변수 설정 완료
- [ ] `DEBUG=False` 확인
- [ ] `ALLOWED_HOSTS`에 Railway 도메인 포함
- [ ] `USE_SQLITE=false` 설정

배포 후:
- [ ] 빌드 로그 에러 없음
- [ ] 마이그레이션 성공
- [ ] 정적 파일 로딩 확인
- [ ] `/admin` 접속 가능
- [ ] 슈퍼유저 생성 완료

---

## 트러블슈팅

### 문제: "ModuleNotFoundError: No module named 'gunicorn'"

**해결**: `requirements-prod.txt`를 `requirements.txt`로 복사 또는 Railway 설정에서 참조 변경

```bash
cp requirements-prod.txt requirements.txt
git add requirements.txt
git commit -m "fix: requirements.txt 업데이트"
git push
```

### 문제: "ALLOWED_HOSTS 에러"

**해결**: Railway 환경 변수에 Railway 도메인 추가

```
ALLOWED_HOSTS=*.railway.app
```

### 문제: "정적 파일이 로드되지 않음"

**해결**:
1. Whitenoise 설치 확인 (`requirements-prod.txt`)
2. `MIDDLEWARE`에 `WhiteNoiseMiddleware` 있는지 확인
3. Railway 로그에서 `collectstatic` 실행 확인

### 문제: "Database connection error"

**해결**:
1. Supabase DB 자격증명 확인
2. Railway 환경 변수 재확인
3. Supabase 대시보드에서 DB 접속 가능 여부 확인

---

## 유용한 Railway CLI 명령어

```bash
# 로그 실시간 확인
railway logs

# 환경 변수 확인
railway variables

# Django 쉘 실행
railway run python manage.py shell

# 마이그레이션 다시 실행
railway run python manage.py migrate

# 정적 파일 다시 수집
railway run python manage.py collectstatic --noinput
```

---

## 참고 자료

- [Railway 공식 문서](https://docs.railway.app/)
- [Django 배포 가이드](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Supabase PostgreSQL 연결](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Whitenoise 문서](https://whitenoise.readthedocs.io/)

---

## 다음 단계

배포 성공 후:
1. 모니터링 설정 (Railway 대시보드 활용)
2. 백업 전략 수립 (Supabase 자동 백업 확인)
3. CI/CD 파이프라인 구축 (GitHub Actions)
4. 성능 최적화 (Django 쿼리 최적화, 캐싱)
