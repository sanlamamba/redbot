"""
Module Name: config_loader
Description: This module loads configuration settings for the Reddit bot,
including API credentials, subreddit information, keywords, and other
parameters necessary for the bot's operation.
"""

import os
from dotenv import load_dotenv
from .config import (
    SUBREDDITS as subReddits,
    KEYWORDS as keywords,
    CHECK_FREQUENCY_SECONDS as checkFrequencySeconds,
    POST_LIMIT as postLimit,
    SENT_POSTS_FILE as sendPostsFile,
)

# Load environment variables from .env file
load_dotenv()

# Load environment variables
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# Configuration constants
SUBREDDITS = subReddits
KEYWORDS = keywords
CHECK_FREQUENCY_SECONDS = checkFrequencySeconds
POST_LIMIT = postLimit
SENT_POSTS_FILE = sendPostsFile

# Multi-subreddit query string
MULTI_SUBREDDIT_QUERY = "+".join(SUBREDDITS)
