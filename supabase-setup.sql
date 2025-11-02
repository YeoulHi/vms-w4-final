-- Supabase RLS 비활성화 스크립트
-- Supabase SQL Editor에서 실행하세요

-- Django가 관리하는 모든 테이블의 RLS 비활성화
-- 중요: Django 애플리케이션 레벨에서 권한 관리를 수행합니다

-- Django 시스템 테이블
ALTER TABLE IF EXISTS django_migrations DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS django_session DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS django_admin_log DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS django_content_type DISABLE ROW LEVEL SECURITY;

-- Auth 테이블
ALTER TABLE IF EXISTS auth_user DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS auth_group DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS auth_permission DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS auth_user_groups DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS auth_user_user_permissions DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS auth_group_permissions DISABLE ROW LEVEL SECURITY;

-- Dashboard 앱 테이블 (마이그레이션 후 생성될 테이블)
ALTER TABLE IF EXISTS dashboard_chartdata DISABLE ROW LEVEL SECURITY;

-- Ingest 앱 테이블 (마이그레이션 후 생성될 테이블)
ALTER TABLE IF EXISTS ingest_excelupload DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS ingest_parsinglog DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS ingest_metricrecord DISABLE ROW LEVEL SECURITY;

-- 참고: 마이그레이션 실행 후 새로운 테이블이 생성되면
-- 다시 이 스크립트를 실행하거나 아래 쿼리로 모든 테이블을 한번에 처리하세요

-- 모든 public 스키마 테이블의 RLS 비활성화 (선택사항)
-- DO $$
-- DECLARE
--     r RECORD;
-- BEGIN
--     FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
--     LOOP
--         EXECUTE 'ALTER TABLE ' || quote_ident(r.tablename) || ' DISABLE ROW LEVEL SECURITY';
--     END LOOP;
-- END $$;
