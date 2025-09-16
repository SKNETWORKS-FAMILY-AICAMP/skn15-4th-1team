-- Database initialization script
-- PostgreSQL Docker 컨테이너가 POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD로 자동 생성

-- 추가 권한 설정 (기본 사용자는 이미 생성됨)
-- PostgreSQL 컨테이너는 자동으로 슈퍼유저 권한을 가진 사용자를 생성하므로
-- 별도의 권한 설정이 필요하지 않음

-- 확장 모듈 설치 (필요시)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 기본 설정 완료 메시지
SELECT 'Database initialization completed successfully' as status;