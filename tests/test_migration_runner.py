"""Tests for the database migration runner."""
import sqlite3
import tempfile
import os
import pytest
from data.migrations.runner import run_migrations


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


class TestMigrationRunner:
    def test_creates_schema_migrations_table(self, db_path):
        run_migrations(db_path)
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchone()
        conn.close()
        assert row is not None

    def test_applies_migrations_only_once(self, db_path):
        first = run_migrations(db_path)
        second = run_migrations(db_path)
        assert second == 0  # nothing new to apply

    def test_first_run_applies_all_sql_files(self, db_path):
        from pathlib import Path
        sql_files = list((Path(__file__).parent.parent / "data" / "migrations").glob("*.sql"))
        count = run_migrations(db_path)
        assert count == len(sql_files)

    def test_applied_migrations_recorded(self, db_path):
        run_migrations(db_path)
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
        conn.close()
        assert len(rows) > 0
        versions = [r[0] for r in rows]
        assert "001_initial_schema" in versions
