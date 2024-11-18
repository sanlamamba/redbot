"""Database utility functions for saving and loading sent posts."""

import os
import csv
from datetime import datetime
from .constants import SENT_POSTS_FILE
from .bprint import bprint as bp


def load_sent_posts() -> set:
    """Load sent posts from a CSV file.

    Returns:
        set: A set of sent post URLs.
    """
    sent_posts = set()

    if not os.path.exists(SENT_POSTS_FILE):
        bp.error("No sent posts CSV file found.")
        return sent_posts

    try:
        with open(SENT_POSTS_FILE, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            sent_posts = {row[0] for row in reader if row}  # Using set comprehension
        bp.success(f"Loaded {len(sent_posts)} sent posts from CSV.")
    except Exception as e:
        bp.error(f"Error loading sent posts from CSV: {e}")

    return sent_posts


def save_sent_post(url: str) -> None:
    """Save the given post URL to a CSV file with the current UTC timestamp.

    Args:
        url (str): The URL of the post to be saved.

    Returns:
        None

    Raises:
        Exception: If there is an error while writing to the CSV file.
    """
    if not isinstance(url, str):
        bp.error("Provided URL is not a string.")
        return

    try:
        with open(SENT_POSTS_FILE, mode="a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([url, datetime.utcnow().isoformat()])
        bp.info(f"Saved post URL to CSV: {url}")
    except (FileNotFoundError, IOError) as e:
        bp.error(f"Error saving sent post to CSV: {e}")
