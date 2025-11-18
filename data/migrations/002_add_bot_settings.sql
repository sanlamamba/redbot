-- Migration 002: Add bot settings table
-- Stores bot configuration that can be changed via commands

CREATE TABLE IF NOT EXISTS bot_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT
);

-- Insert default channel (will be overridden by !setchannel command)
INSERT OR IGNORE INTO bot_settings (key, value, updated_at)
VALUES ('job_channel_id', '', datetime('now'));
