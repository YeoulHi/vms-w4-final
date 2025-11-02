QA 테스트 계획 프롬프트
목표

제공된 유스케이스와 계획 문서를 기반으로, 구현 없이 검증 가능한 QA 테스트 계획과 체크리스트, 수용기준(Exit Criteria)을 산출한다.
프로젝트 규칙 및 아키텍처 제약(Hono+Next.js, React Query, Supabase, Naver SDK)을 준수하는지 검증한다.
입력

필수 문서 경로
유스케이스: docs/[USECASE_ID]/spec.md
관련 계획: docs/[USECASE_ID]/plan.md (있다면)
공통 기준: docs/prd.md, docs/userflow.md, docs/database.md
운영 규칙: .ruler/*.md(Hono/응답 규칙, Naver SDK, Supabase)
대상 기능/페이지/엔드포인트 식별자
페이지/컴포넌트: [PAGE_OR_COMPONENT_NAME]
API: [HTTP_METHOD] /api/[...path]
상태 훅/스토어: [store or hook id]
제약

기능 구현 금지. 오직 테스트 계획·체크리스트·시나리오·수용기준 산출만 수행한다.
프런트는 Client Component, 서버 상태는 React Query, HTTP는 @/lib/remote/api-client 경유 원칙을 준수한다.
Hono 앱은 .basePath('/api'), 응답 헬퍼는 success(data, status)/failure(status, code, message) 순서를 따라야 한다.
Naver Maps SDK는 ncpKeyId 파라미터, 필요한 경우 submodules=geocoder를 포함해야 한다.
Supabase 마이그레이션은 idempotent, updated_at 트리거, 인덱스 전략, RLS 비활성 원칙을 따른다.
산출물 형식

아래 템플릿을 그대로 채워서 산출한다. 항목이 불명확하면 “미확정: 질문 필요”로 남긴다.