지금까지 정리한 데이터플로우, 스키마를 종합하여 최종 완성본으로 응답하라.

1.  PostgreSQL 기반의 데이터베이스 스키마를 `/docs/database.md` 경로에 생성하라.
2.  스키마를 실제 데이터베이스에 반영하기 위한 Supabase 마이그레이션 SQL 파일을 `/supabase/migrations/` 경로에 `000N_[description].sql` 형식으로 생성하라.

- 반드시 유저플로우와 기능 명세에 명시적으로 포함된 데이터만 포함한다.
- 모든 테이블에 `updated_at` 자동 갱신 트리거와 RLS 비활성화 설정을 포함해야 한다.
