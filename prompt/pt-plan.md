구현할 페이지: {페이지 이름}

해당 페이지의 기능을 구현하기 위한 최소한의 모듈화 설계를 진행하세요.

반드시 다음 순서를 따라야한다.
1. 유스케이스 문서 내용을 통해 자세한 요구사항을 파악한다.
2. 다음 코드베이스 구조를 참고하여, 재사용 가능한 모듈이 있는지, 따라야 할 코딩 컨벤션이 무엇인지 파악한다.
   - 공통 컴포넌트: `/src/components/shared`
   - 커스텀 훅: `/src/hooks`
   - API 클라이언트: `/src/lib/remote/api-client.ts`
   - 타입 정의: `/src/types`
3. 위 분석 내용을 바탕으로, 구현해야 할 모듈 및 작업위치를 `AGENTS.md`의 코드베이스 구조를 준수하여 설계한다.
완성된 설계를 다음과 같이 구성하여 유스케이스 문서와 같은 경로에 `plan.md`로 저장한다.
- 개요: 모듈 이름, 위치, 간략한 설명을 포함한 목록
- Diagram: mermaid 문법을 사용하여 모듈간 관계를 시각화
- Implementation Plan: 각 모듈의 구체적인 구현 계획. presentation의 경우 qa sheet를, business logic의 경우 unit test를 포함.
