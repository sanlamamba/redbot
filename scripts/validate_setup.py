#!/usr/bin/env python3
"""
Validation script to check if the bot is properly configured before deployment.
Run this before starting the bot to catch configuration issues early.
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check_mark(passed: bool) -> str:
    """Return checkmark or X based on pass/fail."""
    return f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"

def validate_env_file() -> bool:
    """Check if .env file exists and has required variables."""
    print("\n1. Checking environment configuration...")

    env_path = Path(".env")
    if not env_path.exists():
        print(f"  {RED}✗{RESET} .env file not found")
        print(f"    → Copy .env.example to .env and fill in your credentials")
        return False

    print(f"  {GREEN}✓{RESET} .env file exists")

    # Check for required variables
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
        "DISCORD_TOKEN",
        "DISCORD_CHANNEL_ID"
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith("your_"):
            missing.append(var)
            print(f"  {RED}✗{RESET} {var} not configured")
        else:
            print(f"  {GREEN}✓{RESET} {var} configured")

    if missing:
        print(f"\n  {YELLOW}Missing variables:{RESET} {', '.join(missing)}")
        return False

    return True

def validate_config_file() -> bool:
    """Check if config.yaml exists and is valid."""
    print("\n2. Checking config.yaml...")

    config_path = Path("config.yaml")
    if not config_path.exists():
        print(f"  {RED}✗{RESET} config.yaml not found")
        return False

    print(f"  {GREEN}✓{RESET} config.yaml exists")

    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check platform settings
        platforms = config.get("platforms", {})
        enabled_platforms = []

        if platforms.get("hackernews", {}).get("enabled"):
            enabled_platforms.append("HackerNews")
        if platforms.get("company_monitor", {}).get("enabled"):
            enabled_platforms.append("Company Monitor")

        print(f"  {GREEN}✓{RESET} Config is valid YAML")

        if enabled_platforms:
            print(f"  {GREEN}✓{RESET} Additional platforms: {', '.join(enabled_platforms)}")
        else:
            print(f"  {YELLOW}ℹ{RESET} Only Reddit enabled (HackerNews and Company Monitor disabled)")

        return True
    except Exception as e:
        print(f"  {RED}✗{RESET} Config parsing error: {e}")
        return False

def validate_database() -> bool:
    """Check if database can be initialized."""
    print("\n3. Checking database setup...")

    db_path = Path("sent_posts.db")

    try:
        # Try to import database module
        sys.path.insert(0, str(Path.cwd()))
        from data.database import get_database

        db = get_database()
        print(f"  {GREEN}✓{RESET} Database module loads successfully")

        if db_path.exists():
            print(f"  {GREEN}✓{RESET} Database file exists: {db_path}")
        else:
            print(f"  {YELLOW}ℹ{RESET} Database will be created on first run")

        return True
    except Exception as e:
        print(f"  {RED}✗{RESET} Database error: {e}")
        return False

def validate_dependencies() -> bool:
    """Check if all required packages are installed."""
    print("\n4. Checking Python dependencies...")

    required_packages = {
        "asyncpraw": "Reddit API client",
        "discord": "Discord bot framework",
        "aiohttp": "HTTP client for HackerNews/companies",
        "yaml": "Config file parsing",
        "loguru": "Logging system",
        "dotenv": "Environment variables"
    }

    missing = []
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"  {GREEN}✓{RESET} {package:12} - {description}")
        except ImportError:
            print(f"  {RED}✗{RESET} {package:12} - {description} (NOT INSTALLED)")
            missing.append(package)

    if missing:
        print(f"\n  {YELLOW}Run:{RESET} pip install -r requirements.txt")
        return False

    return True

def main():
    """Run all validation checks."""
    print(f"\n{'='*60}")
    print(f"  Multi-Source Job Scraper Bot - Setup Validation")
    print(f"{'='*60}")

    checks = [
        validate_dependencies(),
        validate_env_file(),
        validate_config_file(),
        validate_database()
    ]

    print(f"\n{'='*60}")
    if all(checks):
        print(f"{GREEN}✓ All checks passed! Ready to deploy.{RESET}")
        print(f"\n  Start with: python main.py")
        print(f"  Or Docker:  docker-compose up -d")
        print(f"{'='*60}\n")
        return 0
    else:
        print(f"{RED}✗ Some checks failed. Fix the issues above.{RESET}")
        print(f"{'='*60}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
