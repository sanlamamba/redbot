"""Database migration runner.

Scans data/migrations/*.sql in lexicographic order and applies any that
haven't been recorded in the schema_migrations table yet.  Each migration
runs inside its own transaction so a failure leaves the database in the last
known-good state.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from utils.logger import logger

_MIGRATIONS_DIR = Path(__file__).parent
_BOOTSTRAP = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def run_migrations(db_path: str) -> int:
    """Apply all pending migrations.  Returns the count of migrations applied."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_BOOTSTRAP)
        conn.commit()

        applied = {
            row[0]
            for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
        }

        sql_files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
        count = 0
        for path in sql_files:
            version = path.stem  # e.g. "001_initial_schema"
            if version in applied:
                continue
            logger.info(f"Applying migration: {version}")
            try:
                sql = path.read_text()
                conn.executescript(sql)          # executescript auto-commits
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
                )
                conn.commit()
                count += 1
            except Exception as e:
                conn.rollback()
                logger.error(f"Migration {version} failed: {e}")
                raise

        if count:
            logger.info(f"Migrations: applied {count} new migration(s)")
        else:
            logger.debug("Migrations: database is up to date")

        return count
    finally:
        conn.close()
