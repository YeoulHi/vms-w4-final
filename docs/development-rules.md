# Vibe-Mafia 프로젝트 개발 규칙

이 문서는 "대학교 내부 데이터 시각화 대시보드" MVP 프로젝트의 개발 효율성과 코드 품질 유지를 위한 핵심 규칙을 정의합니다. 모든 개발자는 이 문서를 숙지하고 준수해야 합니다.

---

## 1. 핵심 원칙 (Core Principles)

우리는 YC 스타트업 CTO의 관점에서, 빠르고 효율적으로 MVP를 완성하는 것을 최우선 목표로 합니다.

-   **단순함 (Simplicity):** 1년차 개발자도 쉽게 이해하고 수정할 수 있는 코드를 작성합니다. 복잡한 설계나 과도한 추상화를 지양합니다.
-   **MVP 우선 (MVP First):** "엑셀 업로드 → 차트 시각화" 라는 핵심 기능과 직접적으로 관련 없는 기능은 구현하지 않습니다. 확장성은 문서로만 고려합니다.
-   **오버엔지니어링 금지 (No Over-engineering):** 대용량 트래픽, 완벽한 보안 등 MVP 범위를 넘어서는 최적화 작업을 진행하지 않습니다.
-   **일관성 (Consistency):** 여기서 정의한 아키텍처, 코드 스타일, 커밋 규칙을 따라 프로젝트 전체의 일관성을 유지합니다.

---

## 2. 아키텍처 규칙 (Architecture Rules)

프로젝트는 `2.code-struture.md`에 정의된 구조를 엄격히 따릅니다.

-   **앱 분리:** 기능에 따라 `ingest`(데이터 입력) 앱과 `dashboard`(데이터 출력) 앱으로 명확히 분리합니다.
-   **로직 분리 (Fat Service, Skinny View):**
    -   `views.py`: 요청 파라미터 검증, 서비스 호출, 템플릿/JSON 응답 등 Presentation 역할만 수행합니다.
    -   `services.py`: `pandas` 파싱, ORM 조회/처리 등 핵심 비즈니스 로직을 이 파일에 집중시킵니다.
-   **종속성 분리:** 외부 라이브러리(e.g., Chart.js)에 특화된 데이터 변환 로직은 `utils/chart_adapter.py`와 같은 별도 유틸리티 파일로 분리하여 관리합니다.
-   **불필요한 레이어 금지:** MVP 범위에 맞지 않는 Repository, Interface 등 추가적인 디자인 패턴을 적용하지 않습니다.

---

## 3. 코드 스타일 가이드 (Code Style Guide)

-   **명명 규칙:** 변수, 함수, 클래스명은 Django 및 PEP 8 컨벤션(snake_case, PascalCase)을 따르며, 그 역할이 명확히 드러나도록 작성합니다.
-   **함수 작성:** 함수는 가능한 짧게, 하나의 기능만 수행하도록 작성합니다. (단일 책임 원칙)
-   **ORM 사용:** 모든 DB 쿼리는 `services.py` 내에서 ORM을 통해 수행하는 것을 원칙으로 합니다. View에서 ORM을 직접 호출하지 않습니다.
-   **주석:** "무엇을" 하는 코드인지 설명하는 주석은 지양하고, "왜" 이렇게 작성했는지 설명이 필요할 때만 간결하게 작성합니다.

---

## 4. 데이터베이스 관리 (Database Management)

데이터베이스 스키마의 모든 변경은 Django Migration 시스템을 통해 추적하고 관리합니다.

-   **ORM 우선:** DB 스키마 변경은 `models.py` 파일을 수정하고, `python manage.py makemigrations` 명령어로 마이그레이션 파일을 생성하는 것을 원칙으로 합니다.
-   **Supabase 직접 수정 금지:** Supabase 대시보드에서 테이블을 직접 수정하거나 Raw SQL을 실행하지 않습니다.
-   **공통 필드:** 모든 모델에는 생성/수정 시각을 자동으로 기록하기 위해 `created_at` (`auto_now_add=True`)과 `updated_at` (`auto_now=True`) 필드를 포함합니다.

---

## 5. 커밋 및 버전 관리 (Commit & Version Control)

-   **커밋 메시지:** [Conventional Commits](https://www.conventionalcommits.org/ko/v1.0.0/) 양식을 따릅니다.
    -   `feat`: 새로운 기능 추가
    -   `fix`: 버그 수정
    -   `docs`: 문서 수정
    -   `style`: 코드 포맷팅, 세미콜론 누락 등 (코드 변경 없는 경우)
    -   `refactor`: 코드 리팩토링
    -   `test`: 테스트 코드 추가/수정
-   **커밋 단위:** 하나의 커밋은 논리적으로 관련된 하나의 작업 단위만 포함해야 합니다.
-   **브랜치 (권장):** `main` 브랜치에 직접 커밋하는 대신, `feature/기능명` 브랜치를 생성하여 작업하고 Pull Request를 통해 병합하는 것을 권장합니다.
