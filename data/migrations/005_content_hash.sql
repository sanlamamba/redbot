-- Migration 005: Add content_hash column for cross-source deduplication
-- sha256(company|title|source)[:16] lets us detect the same job posted on
-- Reddit, HackerNews, and a career page under different URLs.

ALTER TABLE job_postings ADD COLUMN content_hash TEXT;

CREATE INDEX IF NOT EXISTS idx_job_postings_content_hash
    ON job_postings (content_hash)
    WHERE content_hash IS NOT NULL;
