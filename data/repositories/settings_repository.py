"""Repository for bot settings storage."""

from datetime import datetime
from typing import Optional
from .base_repository import BaseRepository
from utils.logger import logger


class SettingsRepository(BaseRepository):
    """Handle bot settings storage and retrieval."""

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value by key.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM bot_settings WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            return row[0] if row else default

    def set(self, key: str, value: str, updated_by: Optional[str] = None) -> bool:
        """Set a setting value.

        Args:
            key: Setting key
            value: Setting value
            updated_by: User who updated the setting

        Returns:
            True if successful
        """
        try:
            with self.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO bot_settings (key, value, updated_at, updated_by)
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, value, datetime.utcnow().isoformat(), updated_by)
                )
            return True
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """Get a setting value as integer.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value as int or default
        """
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def delete(self, key: str) -> bool:
        """Delete a setting.

        Args:
            key: Setting key

        Returns:
            True if successful
        """
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM bot_settings WHERE key = ?", (key,))
            return True
        except Exception as e:
            logger.error(f"Error deleting {key}: {e}")
            return False

    def get_all(self) -> dict:
        """Get all settings as a dictionary.

        Returns:
            Dictionary of all settings
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM bot_settings")
            return {row[0]: row[1] for row in cursor.fetchall()}
