-- Migration 008: User interactions with job postings (save, dismiss, apply)

CREATE TABLE IF NOT EXISTS user_job_interactions (
    user_id     TEXT NOT NULL,
    job_url     TEXT NOT NULL,
    action      TEXT NOT NULL,  -- saved | dismissed | applied
    created_at  TEXT NOT NULL,
    PRIMARY KEY (user_id, job_url, action)
);

CREATE INDEX IF NOT EXISTS idx_uj_interactions_user
    ON user_job_interactions (user_id, action);
