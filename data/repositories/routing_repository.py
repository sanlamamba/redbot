"""Repository for channel routing rules."""
from typing import List, Optional
from utils.logger import logger
from .base_repository import BaseRepository


class RoutingRule:
    __slots__ = ("id", "guild_id", "channel_id", "rule_type", "rule_value", "priority")

    def __init__(self, guild_id, channel_id, rule_type, rule_value, priority=0, id=None):
        self.id = id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.rule_type = rule_type
        self.rule_value = rule_value
        self.priority = priority

    @staticmethod
    def from_row(row) -> "RoutingRule":
        return RoutingRule(
            id=row["id"],
            guild_id=row["guild_id"],
            channel_id=row["channel_id"],
            rule_type=row["rule_type"],
            rule_value=row["rule_value"],
            priority=row["priority"],
        )


class RoutingRepository(BaseRepository):
    def add_rule(self, rule: RoutingRule) -> Optional[int]:
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO channel_routes (guild_id, channel_id, rule_type, rule_value, priority) "
                    "VALUES (?,?,?,?,?)",
                    (rule.guild_id, rule.channel_id, rule.rule_type, rule.rule_value, rule.priority),
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"RoutingRepository.add_rule: {e}")
            return None

    def remove_rule(self, rule_id: int, guild_id: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM channel_routes WHERE id=? AND guild_id=?",
                    (rule_id, guild_id),
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"RoutingRepository.remove_rule: {e}")
            return False

    def get_rules(self, guild_id: str) -> List[RoutingRule]:
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM channel_routes WHERE guild_id=? ORDER BY priority DESC",
                    (guild_id,),
                ).fetchall()
                return [RoutingRule.from_row(dict(r)) for r in rows]
        except Exception as e:
            logger.error(f"RoutingRepository.get_rules: {e}")
            return []
