"""Base repository with common database operations."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class BaseRepository:
    """Base repository with common database operations."""

    def __init__(self, db_path: str = "sent_posts.db"):
        """Initialize repository.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_file()

    def _ensure_db_file(self):
        """Ensure database file exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
