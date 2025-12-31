-- Initialize database with required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create a simple test to verify extensions are loaded
SELECT 'uuid-ossp extension loaded' AS status WHERE EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp');
SELECT 'vector extension loaded' AS status WHERE EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');
