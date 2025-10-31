* 사용자는 **1년차 개발자 수준의 기능 구현 연습**을 진행 중이다.
* 프로젝트 주제는 **“대학교 내부용 데이터 시각화 대시보드”**이며,
  핵심 목표는 **엑셀(Ecount 추출 데이터) → 파싱 → DB 저장 → 차트 시각화**의 전체 흐름 구현이다.
* **최소 복잡도와 유지보수 용이성**을 우선으로 하며, **확장성은 문서로만 고려**한다.
* 인증은 **Django 기본 세션 인증만 사용**, Supabase는 **PostgreSQL 호스팅용으로만 사용**한다.
* **Chart.js**를 사용하여 막대/라인/파이 차트를 한 페이지에서 렌더링하며,
  `/api/dashboard/chart-data/`는 **Chart.js 포맷(JSON)** 으로 응답한다.
* **엑셀 파싱은 pandas**로 수행하며, 필수 컬럼 검증·타입 캐스팅·에러 로깅 등 **방어적 파싱**을 적용한다.
* 현재는 **동기 처리(MVP)** 구조지만, 기술 부채로서 **비동기(Celery)** 전환 가능성을 문서화한다.
* UI는 Django Template 기반, 배포는 선택적으로 Railway를 사용한다.

**사용 기술 스택**
`Django 5.x + DRF + pandas + Chart.js + Supabase(Postgres only) + Railway(optional)`
