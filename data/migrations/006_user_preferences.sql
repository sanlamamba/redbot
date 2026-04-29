-- Migration 006: User preferences and saved searches

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id  TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    pref_key TEXT NOT NULL,
    pref_value TEXT,
    PRIMARY KEY (user_id, guild_id, pref_key)
);

CREATE TABLE IF NOT EXISTS saved_searches (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          TEXT NOT NULL,
    guild_id         TEXT NOT NULL,
    name             TEXT NOT NULL,
    keywords         TEXT,    -- JSON array of strings
    min_salary       INTEGER,
    experience_levels TEXT,   -- JSON array of strings
    remote_only      INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_saved_searches_user
    ON saved_searches (user_id, guild_id);
