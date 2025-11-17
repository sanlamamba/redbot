"""Database facade - provides backward compatibility and convenient access to repositories."""
from typing import Optional, Set

from .repositories import JobRepository


class Database:
    """Database facade providing convenient access to job repository."""

    def __init__(self, db_path: str = "sent_posts.db"):
        """Initialize database with job repository.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.jobs = JobRepository(db_path)

    def initialize_database(self):
        """Initialize database with legacy sent_posts table.

        New schema is applied via migrations.
        """
        with self.jobs.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sent_posts (
                    url TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL
                )
                """
            )

    # ===== Legacy Functions (Backward Compatibility) =====

    def load_sent_posts(self) -> Set[str]:
        """Load sent posts from database (legacy support).

        Returns:
            Set of sent post URLs
        """
        self.initialize_database()
        sent_posts = set()

        try:
            with self.jobs.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT url FROM sent_posts")
                sent_posts = {row[0] for row in cursor.fetchall()}
        except Exception as e:
            print(f"Error loading sent posts: {e}")

        return sent_posts

    def save_sent_post(self, url: str) -> None:
        """Save sent post URL with timestamp (legacy support).

        Args:
            url: Post URL to save
        """
        if not isinstance(url, str):
            return

        self.initialize_database()

        try:
            from datetime import datetime
            with self.jobs.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO sent_posts (url, timestamp) VALUES (?, ?)",
                    (url, datetime.utcnow().isoformat()),
                )
        except Exception as e:
            print(f"Error saving sent post: {e}")


# Global database instance
_db_instance: Optional[Database] = None


def get_database(db_path: str = "sent_posts.db") -> Database:
    """Get global database instance.

    Args:
        db_path: Path to database file

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance


# Legacy functions for backward compatibility
def create_connection():
    """Legacy: Create database connection."""
    return get_database().jobs.get_connection()


def initialize_database():
    """Legacy: Initialize database."""
    get_database().initialize_database()


def load_sent_posts() -> set:
    """Legacy: Load sent posts."""
    return get_database().load_sent_posts()


def save_sent_post(url: str):
    """Legacy: Save sent post."""
    get_database().save_sent_post(url)
