-- Migration 004: Remove legacy sent_posts table
-- Deduplication is now handled by DeduplicationService using job_postings.url.
-- The sent_posts table was a leftover from the original single-source design.

DROP TABLE IF EXISTS sent_posts;
