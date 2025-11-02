다음 PRD 문서를 개선하기 위해 날카롭게 지적하라

- 사용자의 맥락
- Tech-Stack
- 클라이언트 요구사항 Docs
- Code-Structure
- PRD 

--- 

시니어 엔지니어로서 {{PROMPT}}를 개발자 관점에서 간결하고 단호하게 비판하라.
고정 맥락: 최소 복잡도·유지보수 우선(확장성=문서화), Django5+DRF+pandas(방어적 파싱)+Chart.js, Supabase(Postgres만), 세션 인증, 동기 MVP, 한 페이지(막대·라인·파이), /api/dashboard/chart-data=Chart.js JSON.
출력: 목표 1문장 요약 → 레드플래그 Top10 [Critical/Major/Minor](근거·영향 각 1줄) → 맥락 위배 전부 적발.
누락 명세와 수용 기준: 엑셀 입력·파싱/DB·API·보안·테스트의 누락을 지적하고, 측정 가능한 수용 기준 3–5개 제시.
개선: ≤10줄 재작성안과 후속 질문 3–5개를 제시하되, SPA/React·JWT/OAuth·Celery/비동기·Redis·Supabase 기능 남용 등 복잡도 증가는 즉시 차단.

