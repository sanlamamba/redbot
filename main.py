import asyncpraw
import discord
import asyncio
from datetime import datetime
import os
import csv
from dotenv import load_dotenv
import config
from loguru import logger

# Load environment variables
load_dotenv()

# ============ CONFIGURATION CONSTANTS ============
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

SUBREDDITS = config.SUBREDDITS
KEYWORDS = config.KEYWORDS

CHECK_FREQUENCY_SECONDS = config.CHECK_FREQUENCY_SECONDS
POST_LIMIT = config.POST_LIMIT
SENT_POSTS_FILE = config.SENT_POSTS_FILE

MULTI_SUBREDDIT_QUERY = "+".join(SUBREDDITS)

# ============ END CONFIGURATION ============

# Initialize logger with formatting
logger.add("reddit_jobs.log", rotation="500 MB", level="INFO",
           format="{time} {level} {message}", colorize=True)

def load_sent_posts():
    sent_posts = set()
    if os.path.exists(SENT_POSTS_FILE):
        try:
            with open(SENT_POSTS_FILE, mode="r", newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row:
                        sent_posts.add(row[0])
            logger.info(f"Loaded {len(sent_posts)} sent posts from CSV.")
        except Exception as e:
            logger.error(f"Error loading sent posts from CSV: {e}")
    return sent_posts

def save_sent_post(url):
    try:
        with open(SENT_POSTS_FILE, mode="a", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([url, datetime.utcnow().isoformat()])
        logger.info(f"Saved post URL to CSV: {url}")
    except Exception as e:
        logger.error(f"Error saving sent post to CSV: {e}")

class RedditStream:
    def __init__(self):
        self.reddit = asyncpraw.Reddit(client_id=REDDIT_CLIENT_ID,
                                       client_secret=REDDIT_CLIENT_SECRET,
                                       user_agent=REDDIT_USER_AGENT)
        self.sent_posts = load_sent_posts()

    async def get_submissions(self):
        subreddit = await self.reddit.subreddit(MULTI_SUBREDDIT_QUERY)
        submissions = []
        async for submission in subreddit.new(limit=POST_LIMIT):
            post_title = submission.title.lower()
            post_text = submission.selftext.lower()
            post_url = submission.url

            if any(keyword in post_title or keyword in post_text for keyword in KEYWORDS) and "for hire" not in post_title:
                if post_url not in self.sent_posts:  
                    submissions.append(submission)

        logger.info(f"Found {len(submissions)} new posts in the subreddits.")
        return submissions

class DiscordBot(discord.Client):
    def __init__(self, reddit_stream: RedditStream, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reddit_stream = reddit_stream

    async def bulk_delete(self):
        channel = self.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            try:
                deleted = await channel.purge(limit=100, check=lambda m: m.author == self.user)
                logger.info(f"Bulk deleted {len(deleted)} old messages from the bot.")
            except Exception as e:
                logger.error(f"Error in bulk delete: {e}")

    async def send_to_discord(self, submission):
        channel = self.get_channel(DISCORD_CHANNEL_ID)
        if channel is None:
            logger.error(f"Failed to get Discord channel with ID: {DISCORD_CHANNEL_ID}")
            return

        description = submission.selftext[:200] + '...' if submission.selftext else "No description provided"
        embed = discord.Embed(
            title=submission.title[:256], 
            url=submission.url,
            description=description,
            color=discord.Color.blue(),
            timestamp=datetime.utcfromtimestamp(submission.created_utc)
        )
        embed.set_author(name=submission.author.name)
        embed.add_field(name="Subreddit", value=submission.subreddit.display_name, inline=True)
        embed.set_footer(text="Posted at")

        try:
            await channel.send(embed=embed)
            logger.info(f"Sent post: {submission.title}")
            save_sent_post(submission.url)
            self.reddit_stream.sent_posts.add(submission.url)
        except Exception as e:
            logger.error(f"Error sending message to Discord: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')

        await asyncio.gather(
            self.bulk_delete(),
            self.start_scraping_jobs()
        )

    async def start_scraping_jobs(self):
        logger.info("Starting the Reddit job scraping process...")
        while not self.is_closed():
            try:
                submissions = await self.reddit_stream.get_submissions()
                logger.info(f"Scraping completed. Found {len(submissions)} matching posts.")
                for submission in submissions:
                    await self.send_to_discord(submission)
            except Exception as e:
                logger.error(f"Error checking Reddit: {e}")
            await asyncio.sleep(CHECK_FREQUENCY_SECONDS)

async def main():
    reddit_stream = RedditStream()
    discord_bot = DiscordBot(reddit_stream, activity=discord.Game(name="Reddit Jobs"), intents=discord.Intents.default())

    await discord_bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
