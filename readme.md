# Reddit-Discord Job Scraper Bot

This project is a Python-based bot that scrapes job postings from multiple Reddit communities and sends relevant posts to a Discord channel. The bot is designed to be run continuously on an AWS EC2 instance or any server, with logging, duplicate post prevention, and configurable settings through environment variables and configuration files.

## Features

- **Scrapes Multiple Subreddits:** The bot scrapes job postings from specific subreddits (e.g., `forhire`, `jobopenings`, `remotejobs`) to find relevant job posts.
- **Keyword Filtering:** Uses keywords related to coding and development jobs to filter posts and avoid irrelevant content.
- **Prevents Duplicate Posts:** The bot tracks previously sent URLs to prevent posting the same job multiple times.
- **Bulk Deletes Discord Messages:** Deletes old messages in the Discord channel to keep the conversation relevant.
- **Configurable:** The bot uses environment variables and a configuration file to easily modify settings, such as subreddits, keywords, and post-check frequency.
- **Logging:** The bot logs its operations, including post-scraping activities, sending messages, and error handling, with options for adjusting log verbosity.

## Prerequisites

Before running the bot, make sure you have the following:

- **Python 3.7+**
- **Pipenv** or `pip` for managing dependencies
- A **Reddit** account and API keys for access (client ID, client secret)
- A **Discord** bot token and channel ID where job postings will be sent

## Setup

### 1. Clone the repository

[[[bash
git clone https://github.com/your-username/reddit-discord-job-scraper-bot.git
cd reddit-discord-job-scraper-bot
]]]

### 2. Install dependencies

[[[bash
pip install -r requirements.txt
]]]

### 3. Configure environment variables

Create a `.env` file in the project root with the following content:

[[[bash
REDDIT_CLIENT_ID=<your_reddit_client_id>
REDDIT_CLIENT_SECRET=<your_reddit_client_secret>
REDDIT_USER_AGENT=<your_reddit_user_agent>
DISCORD_TOKEN=<your_discord_token>
DISCORD_CHANNEL_ID=<your_discord_channel_id>
]]]

### 4. Configure additional settings in `config.py`

Modify `config.py` to adjust subreddit lists, keywords, and other options:

[[[python
SUBREDDITS = ['forhire', 'jobbit', 'jobopenings', 'remotejs', 'remotejobs']
KEYWORDS = ['python', 'javascript', 'java', 'developer', 'software']
CHECK_FREQUENCY_SECONDS = 60
POST_LIMIT = 20
SENT_POSTS_FILE = 'sent_posts.csv'
]]]

### 5. Run the bot

To start the bot, simply run:

[[[bash
python main.py
]]]

### 6. Deploy on AWS EC2

1. **Launch an EC2 instance**: Choose a t2.micro or higher instance with Ubuntu 20.04.
2. **Set up the environment**:
   - SSH into the instance.
   - Install Python and Git.
   - Clone this repository.
   - Install dependencies.
3. **Run the bot**: Use a process manager like `pm2` or `nohup` to ensure the bot continues running in the background.

Example using `nohup`:

[[[bash
nohup python main.py &
]]]

