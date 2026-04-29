"""Repository for user preferences and saved searches."""
from datetime import datetime
from typing import List, Optional

from utils.logger import logger
from ..models.user_preference import SavedSearch
from .base_repository import BaseRepository


class UserRepository(BaseRepository):
    """CRUD for user_preferences and saved_searches tables."""

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------

    def get_pref(self, user_id: str, guild_id: str, key: str) -> Optional[str]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT pref_value FROM user_preferences "
                    "WHERE user_id=? AND guild_id=? AND pref_key=?",
                    (user_id, guild_id, key),
                ).fetchone()
                return row["pref_value"] if row else None
        except Exception as e:
            logger.error(f"UserRepository.get_pref: {e}")
            return None

    def set_pref(self, user_id: str, guild_id: str, key: str, value: str) -> None:
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO user_preferences "
                    "(user_id, guild_id, pref_key, pref_value) VALUES (?,?,?,?)",
                    (user_id, guild_id, key, value),
                )
        except Exception as e:
            logger.error(f"UserRepository.set_pref: {e}")

    def get_all_prefs(self, user_id: str, guild_id: str) -> dict:
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    "SELECT pref_key, pref_value FROM user_preferences "
                    "WHERE user_id=? AND guild_id=?",
                    (user_id, guild_id),
                ).fetchall()
                return {r["pref_key"]: r["pref_value"] for r in rows}
        except Exception as e:
            logger.error(f"UserRepository.get_all_prefs: {e}")
            return {}

    # ------------------------------------------------------------------
    # Saved searches
    # ------------------------------------------------------------------

    def add_saved_search(self, search: SavedSearch) -> Optional[int]:
        try:
            with self.get_connection() as conn:
                data = search.to_dict()
                cols = ", ".join(data.keys())
                placeholders = ", ".join("?" * len(data))
                cursor = conn.execute(
                    f"INSERT INTO saved_searches ({cols}) VALUES ({placeholders})",
                    list(data.values()),
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"UserRepository.add_saved_search: {e}")
            return None

    def remove_saved_search(self, user_id: str, guild_id: str, name: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM saved_searches WHERE user_id=? AND guild_id=? AND name=?",
                    (user_id, guild_id, name),
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"UserRepository.remove_saved_search: {e}")
            return False

    def get_saved_searches(self, user_id: str, guild_id: str) -> List[SavedSearch]:
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM saved_searches WHERE user_id=? AND guild_id=? "
                    "ORDER BY created_at DESC",
                    (user_id, guild_id),
                ).fetchall()
                return [SavedSearch.from_row(dict(r)) for r in rows]
        except Exception as e:
            logger.error(f"UserRepository.get_saved_searches: {e}")
            return []

    def get_all_saved_searches_for_guild(self, guild_id: str) -> List[SavedSearch]:
        """Return all saved searches across all users in a guild (used for alert matching)."""
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM saved_searches WHERE guild_id=?",
                    (guild_id,),
                ).fetchall()
                return [SavedSearch.from_row(dict(r)) for r in rows]
        except Exception as e:
            logger.error(f"UserRepository.get_all_saved_searches_for_guild: {e}")
            return []

    # ------------------------------------------------------------------
    # Job interactions (save / dismiss / apply)
    # ------------------------------------------------------------------

    def record_interaction(self, user_id: str, job_url: str, action: str) -> None:
        """Record a user interaction (saved, dismissed, applied)."""
        from datetime import datetime
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO user_job_interactions "
                    "(user_id, job_url, action, created_at) VALUES (?,?,?,?)",
                    (user_id, job_url, action, datetime.utcnow().isoformat()),
                )
        except Exception as e:
            logger.error(f"UserRepository.record_interaction: {e}")

    def get_dismissed_urls(self, user_id: str) -> set:
        """Return URLs this user has dismissed (for filtering search results)."""
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    "SELECT job_url FROM user_job_interactions WHERE user_id=? AND action='dismissed'",
                    (user_id,),
                ).fetchall()
                return {r["job_url"] for r in rows}
        except Exception as e:
            logger.error(f"UserRepository.get_dismissed_urls: {e}")
            return set()

    # ------------------------------------------------------------------
    # DM opt-out tracking (stored as preference)
    # ------------------------------------------------------------------

    def mark_dm_disabled(self, user_id: str) -> None:
        """Record that a user has DMs disabled so we don't retry."""
        self.set_pref(user_id, "", "dm_disabled", "1")

    def is_dm_disabled(self, user_id: str) -> bool:
        return self.get_pref(user_id, "", "dm_disabled") == "1"
