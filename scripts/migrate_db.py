#!/usr/bin/env python3
"""Database migration script.

Applies all SQL migrations in order from data/migrations/ directory.
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent


def run_migrations(db_path: str = "sent_posts.db"):
    """Run all pending migrations.

    Args:
        db_path: Path to database file
    """
    project_root = get_project_root()
    migrations_dir = project_root / "data" / "migrations"

    if not migrations_dir.exists():
        print(f"Error: Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get migration files sorted by name
        migration_files = sorted(migrations_dir.glob("*.sql"))

        if not migration_files:
            print("No migration files found.")
            return

        print(f"Found {len(migration_files)} migration file(s)")
        print("-" * 50)

        # Apply each migration
        for migration_file in migration_files:
            print(f"Applying: {migration_file.name}")

            # Read SQL file
            with open(migration_file, 'r') as f:
                sql_content = f.read()

            # Execute SQL
            try:
                cursor.executescript(sql_content)
                conn.commit()
                print(f"✓ Success: {migration_file.name}")
            except sqlite3.Error as e:
                print(f"✗ Error applying {migration_file.name}: {e}")
                conn.rollback()
                # Continue with other migrations

        print("-" * 50)
        print("Migration complete!")

        # Show current schema version
        try:
            cursor.execute("SELECT MAX(version) FROM schema_version")
            version = cursor.fetchone()[0]
            if version:
                print(f"Current schema version: {version}")
        except sqlite3.Error:
            print("Schema version table not found")

    finally:
        conn.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "--db",
        default="sent_posts.db",
        help="Database file path (default: sent_posts.db)"
    )
    args = parser.parse_args()

    print(f"Running migrations on database: {args.db}")
    run_migrations(args.db)


if __name__ == "__main__":
    main()
