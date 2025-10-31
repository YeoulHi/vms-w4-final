# 프로젝트 초기 설정 가이드

이 문서는 Vibe Mafia 대시보드 프로젝트를 로컬 환경에서 설정하고 실행하기 위한 가이드입니다.

## 1. 사전 요구사항

-   **Python 3.10 이상**: [Python 공식 웹사이트](https://www.python.org/downloads/)에서 설치할 수 있습니다.
-   **Git**: [Git 공식 웹사이트](https://git-scm.com/downloads/)에서 설치할 수 있습니다.

## 2. 설정 절차

### 1단계: 소스 코드 복제 (Clone)

먼저, Git을 사용하여 프로젝트 소스 코드를 로컬 컴퓨터로 복제합니다.

```bash
git clone https://github.com/your-repository/vibe-mafia-dashboard.git
cd vibe-mafia-dashboard
```

### 2단계: 가상 환경 생성 및 활성화

프로젝트의 의존성을 독립적으로 관리하기 위해 가상 환경을 생성하고 활성화합니다.

**Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3단계: 의존성 설치

`requirements.txt` 파일을 사용하여 프로젝트에 필요한 모든 Python 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

### 4단계: 데이터베이스 마이그레이션

Django 모델을 기반으로 데이터베이스 스키마를 생성합니다.

```bash
python manage.py migrate
```

### 5단계: 관리자 계정 생성

Django Admin 및 대시보드에 로그인하기 위한 관리자(superuser) 계정을 생성합니다.

```bash
python manage.py createsuperuser
```

화면에 표시되는 안내에 따라 사용자 이름, 이메일, 비밀번호를 입력하세요.

### 6단계: 개발 서버 실행

모든 설정이 완료되었습니다. 아래 명령어를 실행하여 Django 개발 서버를 시작합니다.

```bash
python manage.py runserver
```

서버가 정상적으로 실행되면, 웹 브라우저에서 `http://127.0.0.1:8000/` 주소로 접속하여 대시보드를 확인할 수 있습니다.

-   **대시보드 접속**: `http://127.0.0.1:8000/dashboard/`
-   **로그인 페이지**: `http://127.0.0.1:8000/login/`
-   **관리자 페이지**: `http://127.0.0.1:8000/admin/`

