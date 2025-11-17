"""
Enhanced configuration loader with YAML support.

This module loads configuration from config.yaml and provides backward
compatibility with environment variables and legacy constants.
"""
import yaml
from pathlib import Path
from typing import Any, Optional


class Config:
    """Configuration manager with YAML and environment variable support."""

    def __init__(self, config_file: str = "config.yaml"):
        """Initialize configuration.

        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file = config_file
        self._config = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file."""
        config_path = Path(self.config_file)

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config.yaml: {e}")
                print("Using default configuration")
                self._config = self._get_default_config()
        else:
            print(f"Warning: {self.config_file} not found, using defaults")
            self._config = self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default configuration if YAML file not found.

        Returns:
            Default configuration dictionary
        """
        return {
            "scraping": {
                "check_frequency_seconds": 60,
                "post_limit": 100,
                "age_filter_hours": 24,
            },
            "reddit": {
                "subreddits": [
                    "forhire", "jobbit", "jobopenings", "remotejs",
                    "remotejobs", "remotepython", "remotejava",
                    "RemoteWork", "techjobs",
                ],
                "global_keywords": [
                    "python", "javascript", "java", "c++", "c#",
                    "developer", "software", "react", "angular", "vue",
                    "node", "django", "flask", "machine learning",
                    "aws", "docker", "kubernetes", "devops",
                ],
            },
            "database": {
                "path": "sent_posts.db",
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key.

        Args:
            key: Configuration key (e.g., "scraping.check_frequency_seconds")
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            config.get("scraping.check_frequency_seconds", 60)
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_section(self, section: str) -> dict:
        """Get entire configuration section.

        Args:
            section: Section name

        Returns:
            Section dictionary

        Example:
            scraping_config = config.get_section("scraping")
        """
        return self._config.get(section, {})


# Global configuration instance
_config: Optional[Config] = None


def get_config(key: Optional[str] = None, default: Any = None) -> Any:
    """Get configuration value.

    Args:
        key: Configuration key (None = entire config)
        default: Default value if key not found

    Returns:
        Configuration value or entire config
    """
    global _config
    if _config is None:
        _config = Config()

    if key is None:
        return _config._config

    return _config.get(key, default)


def reload_config():
    """Reload configuration from file."""
    global _config
    _config = Config()


# ===== Legacy Constants (Backward Compatibility) =====
# These are loaded from YAML but exposed as module-level constants
# for backward compatibility with existing code

SUBREDDITS: list = get_config("reddit.subreddits", [])
KEYWORDS: list = get_config("reddit.global_keywords", [])
CHECK_FREQUENCY_SECONDS: int = get_config("scraping.check_frequency_seconds", 60)
POST_LIMIT: int = get_config("scraping.post_limit", 100)
SENT_POSTS_FILE: str = get_config("database.path", "sent_posts.db")
