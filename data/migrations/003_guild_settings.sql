-- Migration 003: Per-guild settings
-- Adds guild_id dimension to bot_settings so each Discord server has
-- its own independent configuration (e.g. separate job_channel_id).

-- Rename old table to preserve any existing data
ALTER TABLE bot_settings RENAME TO bot_settings_legacy;

-- New table with guild_id in the primary key
CREATE TABLE IF NOT EXISTS bot_settings (
    guild_id TEXT NOT NULL DEFAULT '',
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT,
    PRIMARY KEY (guild_id, key)
);

-- Migrate existing rows (guild_id = '' means "global / unscoped")
INSERT OR IGNORE INTO bot_settings (guild_id, key, value, updated_at, updated_by)
SELECT '', key, value, updated_at, updated_by
FROM bot_settings_legacy
WHERE value != '';

DROP TABLE bot_settings_legacy;
