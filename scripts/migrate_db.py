#!/usr/bin/env python3
"""CLI wrapper around the database migration runner.

Usage:
    python scripts/migrate_db.py [--db sent_posts.db]

Applies all pending SQL migrations from data/migrations/*.sql in order.
Already-applied migrations are skipped (tracked in schema_migrations table).
This script is also called by the Dockerfile as a build-time health check;
at runtime, migrations run automatically via Database.__init__().
"""
import argparse
import sys
from pathlib import Path

# Ensure project root is on path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.migrations.runner import run_migrations


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply pending database migrations")
    parser.add_argument("--db", default="sent_posts.db", help="Database file path")
    args = parser.parse_args()

    print(f"Running migrations on: {args.db}")
    try:
        applied = run_migrations(args.db)
        if applied:
            print(f"✓ Applied {applied} migration(s)")
        else:
            print("✓ Database is already up to date")
        return 0
    except Exception as e:
        print(f"✗ Migration failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
