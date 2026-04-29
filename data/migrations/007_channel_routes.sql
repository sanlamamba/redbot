-- Migration 007: Per-guild channel routing rules

CREATE TABLE IF NOT EXISTS channel_routes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    TEXT NOT NULL,
    channel_id  TEXT NOT NULL,
    rule_type   TEXT NOT NULL,  -- keyword | subreddit | source | experience | remote
    rule_value  TEXT NOT NULL,
    priority    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_channel_routes_guild
    ON channel_routes (guild_id, priority DESC);
