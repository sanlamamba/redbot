"""Database facade — convenient access to repositories."""

from typing import Optional

from utils.logger import logger
from .migrations.runner import run_migrations
from .repositories import JobRepository
from .repositories.settings_repository import SettingsRepository
from .repositories.user_repository import UserRepository
from .repositories.routing_repository import RoutingRepository


class Database:
    """Facade providing access to all repositories."""

    def __init__(self, db_path: str = "sent_posts.db"):
        self.db_path = db_path
        run_migrations(db_path)  # apply any pending SQL migrations before opening repos
        self.jobs = JobRepository(db_path)
        self.settings = SettingsRepository(db_path)
        self.users = UserRepository(db_path)
        self.routes = RoutingRepository(db_path)


# Global singleton
_db_instance: Optional[Database] = None


def get_database(db_path: str = "sent_posts.db") -> Database:
    """Return the global Database instance, creating it on first call."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance
