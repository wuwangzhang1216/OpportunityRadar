"""Initialize database tables directly using psycopg2 (sync driver)."""

import os
import sys

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "opportunity_radar")


def get_connection():
    """Get a connection to the database."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def init_extensions(conn):
    """Initialize required PostgreSQL extensions."""
    cursor = conn.cursor()

    # Enable pgvector extension
    print("Enabling pgvector extension...")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Enable uuid-ossp for UUID generation
    print("Enabling uuid-ossp extension...")
    cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    conn.commit()
    cursor.close()
    print("Extensions enabled successfully!")


def create_tables(conn):
    """Create all application tables."""
    cursor = conn.cursor()

    # Create tables in order (respecting foreign key dependencies)
    tables_sql = """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email VARCHAR(255) NOT NULL UNIQUE,
        hashed_password VARCHAR(255) NOT NULL,
        full_name VARCHAR(255),
        is_active BOOLEAN DEFAULT true,
        is_superuser BOOLEAN DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Profiles table
    CREATE TABLE IF NOT EXISTS profiles (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
        display_name VARCHAR(255),
        bio TEXT,
        tech_stack JSONB DEFAULT '[]'::jsonb,
        experience_level VARCHAR(50),
        availability_hours_per_week INTEGER,
        timezone VARCHAR(100),
        preferred_team_size_min INTEGER DEFAULT 1,
        preferred_team_size_max INTEGER DEFAULT 5,
        goals JSONB DEFAULT '[]'::jsonb,
        interests JSONB DEFAULT '[]'::jsonb,
        location_country VARCHAR(100),
        location_region VARCHAR(100),
        student_status VARCHAR(50),
        university VARCHAR(255),
        github_url VARCHAR(500),
        linkedin_url VARCHAR(500),
        portfolio_url VARCHAR(500),
        embedding vector(1536),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Hosts table (Devpost, MLH, etc.)
    CREATE TABLE IF NOT EXISTS hosts (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name VARCHAR(255) NOT NULL UNIQUE,
        slug VARCHAR(255) NOT NULL UNIQUE,
        website_url VARCHAR(500),
        logo_url VARCHAR(500),
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Opportunities table (hackathons, grants)
    CREATE TABLE IF NOT EXISTS opportunities (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        host_id UUID REFERENCES hosts(id) ON DELETE SET NULL,
        external_id VARCHAR(255),
        title VARCHAR(500) NOT NULL,
        slug VARCHAR(500),
        description TEXT,
        short_description TEXT,
        opportunity_type VARCHAR(50) DEFAULT 'hackathon',
        format VARCHAR(50),
        location_type VARCHAR(50),
        location_city VARCHAR(255),
        location_country VARCHAR(100),
        website_url VARCHAR(500),
        registration_url VARCHAR(500),
        logo_url VARCHAR(500),
        banner_url VARCHAR(500),
        themes JSONB DEFAULT '[]'::jsonb,
        technologies JSONB DEFAULT '[]'::jsonb,
        sponsors JSONB DEFAULT '[]'::jsonb,
        judges JSONB DEFAULT '[]'::jsonb,
        total_prize_value DECIMAL(15, 2),
        currency VARCHAR(10) DEFAULT 'USD',
        participant_count INTEGER,
        team_size_min INTEGER,
        team_size_max INTEGER,
        is_featured BOOLEAN DEFAULT false,
        is_active BOOLEAN DEFAULT true,
        source_url VARCHAR(500),
        raw_data JSONB,
        embedding vector(1536),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(host_id, external_id)
    );

    -- Batches/Seasons table
    CREATE TABLE IF NOT EXISTS batches (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
        name VARCHAR(255),
        batch_number INTEGER,
        year INTEGER,
        season VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Timelines table
    CREATE TABLE IF NOT EXISTS timelines (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
        batch_id UUID REFERENCES batches(id) ON DELETE SET NULL,
        event_type VARCHAR(100) NOT NULL,
        event_name VARCHAR(255),
        start_time TIMESTAMP WITH TIME ZONE,
        end_time TIMESTAMP WITH TIME ZONE,
        timezone VARCHAR(100),
        description TEXT,
        is_deadline BOOLEAN DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Prizes table
    CREATE TABLE IF NOT EXISTS prizes (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
        batch_id UUID REFERENCES batches(id) ON DELETE SET NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        prize_type VARCHAR(100),
        value DECIMAL(15, 2),
        currency VARCHAR(10) DEFAULT 'USD',
        quantity INTEGER DEFAULT 1,
        sponsor VARCHAR(255),
        rank INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Requirements table (DSL format)
    CREATE TABLE IF NOT EXISTS requirements (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
        requirement_type VARCHAR(100) NOT NULL,
        description TEXT,
        dsl_rule JSONB,
        is_mandatory BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Matches table
    CREATE TABLE IF NOT EXISTS matches (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
        overall_score DECIMAL(5, 4),
        semantic_score DECIMAL(5, 4),
        rule_score DECIMAL(5, 4),
        time_score DECIMAL(5, 4),
        team_score DECIMAL(5, 4),
        score_breakdown JSONB,
        eligibility_status VARCHAR(50),
        eligibility_issues JSONB DEFAULT '[]'::jsonb,
        fix_suggestions JSONB DEFAULT '[]'::jsonb,
        is_bookmarked BOOLEAN DEFAULT false,
        is_dismissed BOOLEAN DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, opportunity_id)
    );

    -- Pipelines table (user tracking)
    CREATE TABLE IF NOT EXISTS pipelines (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
        match_id UUID REFERENCES matches(id) ON DELETE SET NULL,
        status VARCHAR(50) DEFAULT 'interested',
        notes TEXT,
        team_members JSONB DEFAULT '[]'::jsonb,
        project_idea TEXT,
        submission_url VARCHAR(500),
        reminder_enabled BOOLEAN DEFAULT true,
        last_reminder_sent TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, opportunity_id)
    );

    -- Materials table (AI-generated content)
    CREATE TABLE IF NOT EXISTS materials (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
        pipeline_id UUID REFERENCES pipelines(id) ON DELETE SET NULL,
        material_type VARCHAR(100) NOT NULL,
        title VARCHAR(500),
        content TEXT NOT NULL,
        metadata JSONB DEFAULT '{}'::jsonb,
        prompt_used TEXT,
        model_used VARCHAR(100),
        is_favorite BOOLEAN DEFAULT false,
        version INTEGER DEFAULT 1,
        parent_id UUID REFERENCES materials(id) ON DELETE SET NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes for better query performance
    CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
    CREATE INDEX IF NOT EXISTS idx_opportunities_host_id ON opportunities(host_id);
    CREATE INDEX IF NOT EXISTS idx_opportunities_type ON opportunities(opportunity_type);
    CREATE INDEX IF NOT EXISTS idx_opportunities_active ON opportunities(is_active);
    CREATE INDEX IF NOT EXISTS idx_batches_opportunity_id ON batches(opportunity_id);
    CREATE INDEX IF NOT EXISTS idx_timelines_opportunity_id ON timelines(opportunity_id);
    CREATE INDEX IF NOT EXISTS idx_prizes_opportunity_id ON prizes(opportunity_id);
    CREATE INDEX IF NOT EXISTS idx_requirements_opportunity_id ON requirements(opportunity_id);
    CREATE INDEX IF NOT EXISTS idx_matches_user_id ON matches(user_id);
    CREATE INDEX IF NOT EXISTS idx_matches_opportunity_id ON matches(opportunity_id);
    CREATE INDEX IF NOT EXISTS idx_matches_score ON matches(overall_score DESC);
    CREATE INDEX IF NOT EXISTS idx_pipelines_user_id ON pipelines(user_id);
    CREATE INDEX IF NOT EXISTS idx_pipelines_status ON pipelines(status);
    CREATE INDEX IF NOT EXISTS idx_materials_user_id ON materials(user_id);
    CREATE INDEX IF NOT EXISTS idx_materials_type ON materials(material_type);

    -- Create vector indexes for semantic search (HNSW)
    CREATE INDEX IF NOT EXISTS idx_profiles_embedding ON profiles USING hnsw (embedding vector_cosine_ops);
    CREATE INDEX IF NOT EXISTS idx_opportunities_embedding ON opportunities USING hnsw (embedding vector_cosine_ops);
    """

    print("Creating tables...")
    cursor.execute(tables_sql)
    conn.commit()
    cursor.close()
    print("All tables created successfully!")


def seed_hosts(conn):
    """Seed initial host data."""
    cursor = conn.cursor()

    hosts = [
        ("Devpost", "devpost", "https://devpost.com", "Platform for hackathons and coding challenges"),
        ("MLH", "mlh", "https://mlh.io", "Major League Hacking - Student hackathon league"),
        ("Kaggle", "kaggle", "https://kaggle.com", "Data science competitions platform"),
        ("HackerEarth", "hackerearth", "https://hackerearth.com", "Developer assessment and hackathon platform"),
    ]

    print("Seeding hosts...")
    for name, slug, url, desc in hosts:
        cursor.execute("""
            INSERT INTO hosts (name, slug, website_url, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (slug) DO NOTHING
        """, (name, slug, url, desc))

    conn.commit()
    cursor.close()
    print("Hosts seeded successfully!")


def main():
    """Main function to initialize the database."""
    print("=" * 50)
    print("OpportunityRadar Database Initialization")
    print("=" * 50)

    try:
        # Connect to database
        print(f"\nConnecting to database at {DB_HOST}:{DB_PORT}...")
        conn = get_connection()
        print("Connected successfully!")

        # Initialize extensions
        init_extensions(conn)

        # Create tables
        create_tables(conn)

        # Seed initial data
        seed_hosts(conn)

        # Close connection
        conn.close()

        print("\n" + "=" * 50)
        print("Database initialization completed successfully!")
        print("=" * 50)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
