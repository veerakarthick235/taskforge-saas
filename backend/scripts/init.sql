-- TaskForge Database Initialization
-- This script runs on first container start

-- Create a restricted application role (no BYPASSRLS)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'taskforge_app') THEN
        CREATE ROLE taskforge_app WITH LOGIN PASSWORD 'taskforge_app_secret';
    END IF;
END
$$;

-- Grant privileges
GRANT CONNECT ON DATABASE taskforge TO taskforge_app;
GRANT USAGE ON SCHEMA public TO taskforge_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO taskforge_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO taskforge_app;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- trigram index for ILIKE search
