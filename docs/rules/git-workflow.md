# Git Workflow 규칙

## 커밋 메시지 규칙

### 형식

```
<type>: <subject>

<body> (선택)

<footer> (선택)
```

### Type (필수)

- `feat:` 새 기능
- `fix:` 버그 수정
- `refactor:` 코드 구조 개선 (기능 변경 없음)
- `docs:` 문서 수정
- `test:` 테스트 추가/수정
- `chore:` 설정, 의존성 업데이트

### 예제

```
feat: Add chart data API endpoint

- Implement GET /api/dashboard/chart-data/
- Add department/year filtering
- Return Chart.js compatible JSON

Closes #12
```

## 브랜치 전략

```
main (프로덕션)
 └── develop (개발)
      ├── feature/excel-parsing
      ├── feature/chart-api
      └── fix/login-bug
```

## 커밋 빈도

- **작은 기능**: 1-2 커밋
- **큰 기능**: 기능별로 5-10 커밋
- **리팩토링**: 논리적 단위로 나누기
- **테스트**: 기능 커밋과 함께 포함

## Pull Request 체크리스트

- [ ] 테스트 통과
- [ ] 코드 스타일 준수 (PEP 8)
- [ ] 관련 문서 업데이트
- [ ] 커밋 메시지 명확함

## 금지 사항

❌ `git push -f` (강제 푸시)
❌ `git rebase -i main` (메인 브랜치 리베이스)
❌ 큰 바이너리 파일 커밋 (.xlsx, .zip 등)
❌ 환경 변수 파일 커밋 (.env, .env.local)
