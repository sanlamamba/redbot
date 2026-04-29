"""Repository for per-guild bot settings storage."""

from datetime import datetime
from typing import Optional
from .base_repository import BaseRepository
from utils.logger import logger

_GLOBAL = ""  # sentinel for guild-agnostic settings


class SettingsRepository(BaseRepository):
    """Store and retrieve bot settings keyed by (guild_id, key)."""

    def get(self, key: str, default: Optional[str] = None,
            guild_id: str = _GLOBAL) -> Optional[str]:
        """Get a setting value.

        Args:
            key: Setting key
            default: Value to return when key is absent
            guild_id: Discord guild snowflake string (empty = global)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT value FROM bot_settings WHERE guild_id = ? AND key = ?",
                    (guild_id, key)
                )
                row = cursor.fetchone()
                return row[0] if row else default
        except Exception as e:
            logger.error(f"Error reading setting {key}: {e}")
            return default

    def set(self, key: str, value: str, updated_by: Optional[str] = None,
            guild_id: str = _GLOBAL) -> bool:
        """Set a setting value.

        Args:
            key: Setting key
            value: Setting value
            updated_by: User who changed the setting
            guild_id: Discord guild snowflake string (empty = global)
        """
        try:
            with self.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO bot_settings
                        (guild_id, key, value, updated_at, updated_by)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (guild_id, key, value, datetime.utcnow().isoformat(), updated_by)
                )
            return True
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False

    def get_int(self, key: str, default: Optional[int] = None,
                guild_id: str = _GLOBAL) -> Optional[int]:
        """Get a setting value as integer."""
        value = self.get(key, guild_id=guild_id)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def delete(self, key: str, guild_id: str = _GLOBAL) -> bool:
        """Delete a setting."""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "DELETE FROM bot_settings WHERE guild_id = ? AND key = ?",
                    (guild_id, key)
                )
            return True
        except Exception as e:
            logger.error(f"Error deleting {key}: {e}")
            return False

    def get_all(self, guild_id: str = _GLOBAL) -> dict:
        """Get all settings for a guild as a dictionary."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT key, value FROM bot_settings WHERE guild_id = ?",
                    (guild_id,)
                )
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Error reading all settings: {e}")
            return {}
