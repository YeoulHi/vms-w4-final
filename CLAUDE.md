# 프로젝트 개요: 대학교 내부 데이터 시각화 대시보드

## 1. 핵심 목표 (The One Thing)
- Ecount에서 추출한 엑셀(Excel) 파일을 업로드하면, 웹 대시보드에서 주요 성과 지표를 차트로 시각화하여 보여주는 MVP(최소 기능 제품)를 개발한다.

## 2. 주요 기능 (Core Features)
- **관리자 (Admin):** Django Admin 페이지를 통해 엑셀/CSV 파일을 업로드하고, 시스템은 이를 파싱하여 데이터베이스에 저장(Upsert)한다.
- **내부 직원 (User):** 웹 페이지에 로그인하여, 학과별/연도별 성과 지표가 시각화된 차트를 조회하고 필터링한다.

## 3. 기술 스택 (Tech Stack)
- **Backend:** Django 5.x, Django REST Framework
- **Database:** PostgreSQL (on Supabase)
- **Parser:** pandas
- **Frontend:** Django Template, Bootstrap, Chart.js

## 4. 코드베이스 구조 (Code Structure)
- `project_root/`
  - `apps/ingest/`: 데이터 **입력** 담당. (엑셀 파싱, DB 저장 로직)
  - `apps/dashboard/`: 데이터 **출력** 담당. (대시보드 뷰, 차트 데이터 API)
  - `config/`: Django 프로젝트 설정

## 5. 개발 원칙 (Development Principles)
- **단순성:** 1년차 개발자도 쉽게 이해할 수 있는 간단한 구조와 코드를 유지한다.
- **MVP 우선:** 핵심 기능(업로드, 조회, 시각화)에만 집중하고, 오버엔지니어링을 지양한다.
- **동기 처리:** 모든 데이터 처리는 비동기 작업 없이 간단한 동기 방식으로 구현한다.
