# Multi-Source Job Scraper Bot

A Discord bot that monitors multiple sources (Reddit, HackerNews, company pages) for job postings and automatically forwards them to Discord with intelligent parsing and analysis.

## Features

### Phase 1: Foundation & Infrastructure
- **Multi-source job tracking** - SQLite database with comprehensive schema
- **User profiles & preferences** - Personalized job filtering and notifications
- **Advanced analytics** - Track job interactions, keyword trends, and statistics
- **Professional logging** - Structured logging with rotation and retention (loguru)
- **Health monitoring** - Heartbeat monitoring with alerts
- **Rate limiting** - Token bucket algorithm for API calls
- **Smart retry logic** - Exponential backoff with jitter

### Phase 2: Intelligent Parsing
- **Salary detection** - 16 regex patterns supporting USD, EUR, GBP, CAD, AUD
- **Experience level detection** - Classifies as Junior/Mid/Senior/Lead
- **Sentiment analysis** - Detects 60+ red flags across 6 categories
- **NLP extraction** - Extracts skills, location, and requirements
- **Tech stack detection** - Identifies 100+ technologies
- **Rich Discord embeds** - Color-coded by priority with all parsed data
- **Age filtering** - Only shows recent posts (configurable hours)
- **Duplicate detection** - Prevents spam from reposted jobs

### Phase 3: Analytics & Commands
- **!stats** - Show today's job statistics (total, avg salary, top keywords, remote %)
- **!search** - Search jobs by keyword across title, description, and skills
- **!trends** - View market trends (salary by level, top keywords, active subreddits)
- **!export** - Export jobs to CSV with all parsed data
- **Interactive Discord bot** - Responds to text commands with rich embeds

### Phase 4: Multi-Source Expansion (NEW!)
- **HackerNews integration** - Monthly "Who is hiring?" threads via HN API
- **Company monitoring** - Track specific company career pages for new postings
- **Multi-source architecture** - Unified processing pipeline for all sources
- **Docker deployment** - Containerized for easy deployment anywhere
- **Persistent storage** - Full job data saved to database for historical analysis

## Architecture

This project follows clean architecture principles with clear separation of concerns:

```
sources/     - Job sources (Reddit, Discord)
core/        - Business logic orchestration
parsers/     - Content parsers (salary, experience, sentiment, NLP)
data/        - Data models, repositories, and migrations
utils/       - Cross-cutting concerns (logging, config, health, rate limiting)
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Discord Commands

The bot supports **both** text commands (`!command`) and slash commands (`/command`).

### Text Commands (Traditional)

- **`!help`** - Show all available commands
- **`!stats`** - Today's statistics (last 24 hours)
- **`!search <keyword>`** - Search recent jobs (e.g., `!search python`)
- **`!trends salary`** - Salary trends by experience level (last 30 days)
- **`!trends keywords`** - Most in-demand skills (last 30 days)
- **`!trends subreddits`** - Most active subreddits (last 30 days)
- **`!export`** - Export last 100 jobs to CSV file
- **`!setchannel [#channel]`** - 🔧 **[Admin]** Set job posting channel
- **`!getchannel`** - Show current job posting channel

### Slash Commands (Modern)

All commands are also available as slash commands with autocomplete:

- **`/help`** - Show all available commands
- **`/stats`** - Today's job statistics
- **`/search <keyword>`** - Search with autocomplete
- **`/trends <type>`** - Select from: salary, keywords, subreddits
- **`/export`** - Export to CSV
- **`/setchannel [#channel]`** - 🔧 **[Admin]** Set channel with autocomplete
- **`/getchannel`** - Show current channel

> **Tip**: Slash commands provide autocomplete, validation, and better UX!

## Quick Start

> **📘 For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

### Prerequisites
- Python 3.11+ (or Docker)
- Reddit API credentials
- Discord bot token (with **message content intent** enabled)

### Pre-Flight Check

Before deployment, validate your setup:
```bash
python scripts/validate_setup.py
```

### Option A: Docker (Recommended)

1. Clone and configure:
```bash
git clone <repository-url>
cd redbot
cp .env.example .env  # Edit with your credentials
```

2. Enable sources in `config.yaml`:
```yaml
platforms:
  hackernews:
    enabled: true  # Monitor HackerNews
  company_monitor:
    enabled: true  # Monitor company pages
    companies:
      - name: "Shopify"
        url: "https://www.shopify.com/careers"
      - name: "Stripe"
        url: "https://stripe.com/jobs"
```

3. Run with Docker:
```bash
docker-compose up -d
docker-compose logs -f  # View logs
```

4. Set job posting channel in Discord:
```
!setchannel #jobs-channel
```
Or set `DISCORD_CHANNEL_ID` in `.env` before starting the bot.

### Option B: Local Python

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_user_agent
DISCORD_TOKEN=your_discord_token
# DISCORD_CHANNEL_ID=your_channel_id  # Optional: or use !setchannel command
```

3. Run migrations and start:
```bash
python scripts/migrate_db.py
python main.py
```

4. In Discord, set the job posting channel:
```
!setchannel #jobs-channel
```

## Configuration

Edit `config.yaml` to customize:

- **Scraping**: Subreddits, keywords, age filter, check frequency
- **Platforms**: Enable/disable HackerNews, company monitoring
  - **HackerNews**: Automatically finds latest "Who is hiring?" thread
  - **Companies**: Add company names and career page URLs to monitor
- **Parsers**: Salary ranges, red flags, tech stack
- **Analytics**: Retention periods, tracking settings
- **Logging**: Log levels, rotation, retention

### Multi-Source Setup

```yaml
platforms:
  hackernews:
    enabled: true
    check_frequency_hours: 6  # Check every 6 hours

  company_monitor:
    enabled: true
    companies:
      - name: "Company Name"
        url: "https://company.com/careers"
```

See `config.yaml` for full configuration options.

## Project Structure

```
redbot/
├── main.py                  # Application entry point
├── config.yaml              # Configuration file
├── requirements.txt         # Python dependencies
│
├── sources/                 # Job sources
│   ├── reddit.py           # Reddit job scraper (105 lines)
│   ├── discord.py          # Discord bot integration (190 lines)
│   └── commands/           # Discord command handlers
│       ├── __init__.py     # Command router (54 lines)
│       ├── stats.py        # Statistics command (65 lines)
│       ├── search.py       # Search command (54 lines)
│       ├── trends.py       # Trends analysis (119 lines)
│       └── export.py       # CSV export (56 lines)
│
├── core/                    # Business logic
│   └── job_processor.py    # Orchestrates all parsers (130 lines)
│
├── parsers/                 # Content parsers
│   ├── salary.py           # Salary detection (287 lines, 16 tests ✓)
│   ├── experience.py       # Experience level detection (140 lines)
│   ├── sentiment.py        # Sentiment analysis (112 lines)
│   ├── nlp.py              # NLP extraction (154 lines)
│   └── data/               # Parser constants
│       ├── red_flags.py    # Red flag keywords
│       └── tech_stack.py   # Technology keywords
│
├── data/                    # Data layer
│   ├── database.py         # Database facade (118 lines)
│   ├── models/             # Data models (job, user, analytics)
│   ├── repositories/       # Repository pattern for data access
│   └── migrations/         # SQL schema migrations
│
├── utils/                   # Utilities
│   ├── logger.py           # Logging system (130 lines)
│   ├── config.py           # Configuration loader (148 lines)
│   ├── health.py           # Health monitoring (200 lines)
│   ├── rate_limiter.py     # Rate limiting (150 lines)
│   └── retry.py            # Retry logic (180 lines)
│
└── tests/                   # Test suite
    └── test_parsers.py     # Parser tests (16 passing)
```

## Testing

Run the test suite:
```bash
python tests/test_parsers.py
```

Or with pytest:
```bash
pytest tests/ -v
```

Current coverage: 16/16 salary parser tests passing

## Utility Scripts

### Reset Bot (Leave All Servers)

Remove the bot from all servers:
```bash
# Show which servers the bot is in
python scripts/reset_bot.py --show

# Leave all servers (with confirmation)
python scripts/reset_bot.py

# Force leave all servers (no confirmation)
python scripts/reset_bot.py --force
```

**Use cases:**
- Clean up test servers
- Reset bot to initial state
- Remove from unwanted servers

### Validate Setup

Check configuration before deploying:
```bash
python scripts/validate_setup.py
```

Checks:
- Environment variables (Reddit, Discord credentials)
- Config file validity
- Database connectivity
- Python dependencies
- Channel configuration

## Design Patterns

- **Repository Pattern** - Clean data access layer
- **Facade Pattern** - Simplified database interface
- **Strategy Pattern** - Interchangeable parsers
- **Singleton Pattern** - Shared resources (logger, database)

## Code Metrics

- **Total Lines**: ~2,500
- **Modules**: 30+ focused files
- **Avg Module Size**: 120 lines
- **Max Module Size**: 287 lines (salary.py)
- **Test Coverage**: Parsers fully tested

## Maintenance

### Adding a New Parser
1. Create `parsers/new_parser.py`
2. Add exports to `parsers/__init__.py`
3. Integrate in `core/job_processor.py`
4. Write tests in `tests/test_parsers.py`

### Adding a New Job Source
1. Create `sources/new_source.py`
2. Follow RedditStream pattern
3. Add exports to `sources/__init__.py`
4. Update `main.py`

### Adding Database Tables
1. Create migration in `data/migrations/`
2. Update models in `data/models/`
3. Add repository methods
4. Run `python scripts/migrate_db.py`

## License

MIT

## Author

San Lamamba P. (2024)
