-- Initialize PostgreSQL database for OpportunityRadar
-- This script runs automatically when the container starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Grant permissions (if needed)
GRANT ALL PRIVILEGES ON DATABASE opportunity_radar TO postgres;
