-- Migration 001: Initial Enhanced Schema
-- Replaces simple sent_posts table with comprehensive job tracking

-- Main job postings table
CREATE TABLE IF NOT EXISTS job_postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    subreddit TEXT,
    author TEXT,
    created_utc INTEGER NOT NULL,
    discovered_at TEXT NOT NULL,

    -- Source tracking
    source TEXT DEFAULT 'reddit' NOT NULL,
    source_id TEXT,

    -- Parsed fields
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT DEFAULT 'USD',
    salary_period TEXT,
    experience_level TEXT,
    company_name TEXT,
    location TEXT,
    is_remote BOOLEAN DEFAULT 0,

    -- Metadata
    matched_keywords TEXT,
    priority_score INTEGER DEFAULT 0,
    duplicate_of INTEGER,

    -- Sentiment analysis
    sentiment_score REAL,
    red_flags TEXT,

    -- Archival
    archived BOOLEAN DEFAULT 0,
    archived_at TEXT,

    FOREIGN KEY (duplicate_of) REFERENCES job_postings(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_postings_url ON job_postings(url);
CREATE INDEX IF NOT EXISTS idx_job_postings_created ON job_postings(created_utc DESC);
CREATE INDEX IF NOT EXISTS idx_job_postings_subreddit ON job_postings(subreddit);
CREATE INDEX IF NOT EXISTS idx_job_postings_source ON job_postings(source, source_id);
CREATE INDEX IF NOT EXISTS idx_job_postings_archived ON job_postings(archived);
CREATE INDEX IF NOT EXISTS idx_job_postings_source_created ON job_postings(source, created_utc DESC);

-- Keep legacy sent_posts table for now (will be migrated)
-- It will be populated from job_postings.url
