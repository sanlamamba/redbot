"""Database utility functions for saving and loading sent posts using SQLite."""

import sqlite3
from datetime import datetime
from .config import SENT_POSTS_FILE
from .bprint import bprint as bp


def create_connection():
    """Create a database connection to the SQLite database."""
    if not SENT_POSTS_FILE:
        bp.error("No database file specified.")
        return None
    conn = sqlite3.connect(SENT_POSTS_FILE)
    return conn


def initialize_database():
    """Initialize the database and create the sent_posts table if it doesn't exist."""
    with create_connection() as conn:
        if conn is None:
            return
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_posts (
                url TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL
            )
            """
        )
        conn.commit()


def load_sent_posts() -> set:
    """Load sent posts from the SQLite database.

    Returns:
        set: A set of sent post URLs.
    """
    sent_posts = set()
    initialize_database()

    try:
        with create_connection() as conn:
            if conn is None:
                return sent_posts
            cursor = conn.cursor()
            cursor.execute("SELECT url FROM sent_posts")
            sent_posts = {row[0] for row in cursor.fetchall()}
        bp.success(f"Loaded {len(sent_posts)} sent posts from the database.")
    except Exception as e:
        bp.error(f"Error loading sent posts from the database: {e}")

    return sent_posts


def save_sent_post(url: str) -> None:
    """Save the given post URL to the SQLite database with the current UTC timestamp.

    Args:
        url (str): The URL of the post to be saved.
    """
    if not isinstance(url, str):
        bp.error("Provided URL is not a string.")
        return

    initialize_database()

    try:
        with create_connection() as conn:
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO sent_posts (url, timestamp) VALUES (?, ?)",
                (url, datetime.utcnow().isoformat()),
            )
            conn.commit()
        bp.info(f"Saved post URL to database: {url}")
    except Exception as e:
        bp.error(f"Error saving sent post to database: {e}")


def purge_sent_posts() -> None:
    """Purge all sent posts from the SQLite database."""
    initialize_database()

    try:
        with create_connection() as conn:
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sent_posts")
            conn.commit()
        bp.info("Purged all sent posts from the database.")
    except Exception as e:
        bp.error(f"Error purging sent posts from the database: {e}")
