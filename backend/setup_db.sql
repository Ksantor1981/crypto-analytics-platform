-- Create user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'crypto_user') THEN
        CREATE USER crypto_user WITH PASSWORD 'crypto_password';
    END IF;
END
$$;

-- Create database if not exists
SELECT 'CREATE DATABASE crypto_analytics OWNER crypto_user' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'crypto_analytics')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE crypto_analytics TO crypto_user;
GRANT CREATE ON SCHEMA public TO crypto_user;
GRANT USAGE ON SCHEMA public TO crypto_user;

-- Connect to the new database and grant additional privileges
\c crypto_analytics

-- Grant privileges on all tables in public schema
GRANT ALL ON ALL TABLES IN SCHEMA public TO crypto_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO crypto_user;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO crypto_user;

-- Grant default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO crypto_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO crypto_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO crypto_user; 