# Reddit Job Scraper - Architecture Documentation

## 🏗️ Project Structure

```
redbot/
├── main.py                     # Application entry point
├── config.yaml                 # Configuration file
├── requirements.txt            # Python dependencies
│
├── core/                       # Core business logic
│   ├── __init__.py            # Exports: JobProcessor, get_job_processor
│   └── job_processor.py       # Orchestrates all parsers (130 lines)
│
├── sources/                    # Job sources (Reddit, Discord, etc.)
│   ├── __init__.py            # Exports: RedditStream, DiscordBot
│   ├── reddit.py              # Reddit job scraper (105 lines)
│   └── discord.py             # Discord bot integration (164 lines)
│
├── parsers/                    # Content parsers
│   ├── __init__.py            # Exports all parsers
│   ├── salary.py              # Salary detection (287 lines)
│   ├── experience.py          # Experience level detection (140 lines)
│   ├── sentiment.py           # Sentiment analysis (112 lines)
│   ├── nlp.py                 # NLP extraction (154 lines)
│   └── data/                  # Parser constants
│       ├── red_flags.py       # Red flag keywords (62 lines)
│       └── tech_stack.py      # Technology keywords (49 lines)
│
├── data/                       # Data layer
│   ├── database.py            # Database facade (118 lines)
│   ├── models/                # Data models
│   │   ├── __init__.py        # Exports all models
│   │   ├── job.py             # JobPosting model (79 lines)
│   │   ├── user.py            # User models (71 lines)
│   │   └── analytics.py       # Analytics models (43 lines)
│   ├── repositories/          # Repository pattern
│   │   ├── __init__.py        # Exports repositories
│   │   ├── base_repository.py # Base repository (32 lines)
│   │   ├── job_repository.py  # Job data access (124 lines)
│   │   └── user_repository.py # User data access (171 lines)
│   └── migrations/            # SQL migrations
│       ├── 001_initial_schema.sql
│       ├── 002_user_profiles.sql
│       └── 003_analytics.sql
│
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── logger.py              # Logging system (130 lines)
│   ├── config.py              # Configuration loader (148 lines)
│   ├── constants.py           # Environment constants
│   ├── health.py              # Health monitoring (200 lines)
│   ├── rate_limiter.py        # Rate limiting (150 lines)
│   └── retry.py               # Retry logic (180 lines)
│
├── scripts/                    # Utility scripts
│   └── migrate_db.py          # Database migration runner
│
└── tests/                      # Test suite
    ├── __init__.py
    └── test_parsers.py        # Parser tests (16 passing)
```

## 📦 Module Organization

### Core Principles

1. **Single Responsibility** - Each module has one clear purpose
2. **Separation of Concerns** - Business logic, data access, and parsing are separate
3. **Repository Pattern** - Clean data access layer
4. **Dependency Injection** - Loose coupling between components
5. **Clean Imports** - All packages export their public API via `__init__.py`

### Module Breakdown

#### Sources (`sources/`)
**Purpose**: Job sources and external integrations
- `reddit.py` - Scrapes Reddit with age filtering and job processing
- `discord.py` - Sends rich embeds to Discord with all parsed data

#### Core (`core/`)
**Purpose**: Business logic orchestration
- `job_processor.py` - Integrates all parsers, processes jobs end-to-end

#### Parsers (`parsers/`)
**Purpose**: Extract structured data from unstructured text
- `salary.py` - Detects and normalizes salaries (16 test cases ✓)
- `experience.py` - Classifies experience levels (Junior/Mid/Senior/Lead)
- `sentiment.py` - Analyzes sentiment and detects 60+ red flags
- `nlp.py` - Extracts skills, location, and requirements
- `data/` - Parser constants (red flags, tech stack)

#### Data (`data/`)
**Purpose**: Data models and persistence
- `database.py` - Facade for all repositories
- `models/` - Data classes with serialization
- `repositories/` - Data access with repository pattern
- `migrations/` - SQL schema migrations

#### Utils (`utils/`)
**Purpose**: Cross-cutting concerns
- `logger.py` - Structured logging with rotation
- `config.py` - YAML configuration loader
- `health.py` - Health monitoring and alerts
- `rate_limiter.py` - API rate limiting
- `retry.py` - Exponential backoff retry logic

## 🔄 Data Flow

```
Reddit API
    ↓
RedditStream (sources/reddit.py)
    ├─ Filters by keywords
    ├─ Applies age filter
    └─ Creates JobPosting objects
    ↓
JobProcessor (core/job_processor.py)
    ├─ SalaryParser → Extracts salary
    ├─ ExperienceParser → Detects level
    ├─ SentimentAnalyzer → Finds red flags
    └─ NLPExtractor → Extracts skills/location
    ↓
JobPosting (enriched with parsed data)
    ↓
DiscordBot (sources/discord.py)
    ├─ Creates rich embed
    ├─ Color codes by priority
    └─ Sends to Discord channel
    ↓
Database (data/repositories/)
    └─ Stores job posting
```

## 💡 Design Patterns Used

### 1. Repository Pattern
**Location**: `data/repositories/`
**Purpose**: Abstracts data access, makes testing easy
```python
db = get_database()
job = db.jobs.get_by_url(url)
db.jobs.save(job)
```

### 2. Facade Pattern
**Location**: `data/database.py`
**Purpose**: Provides simple interface to complex subsystems
```python
db = Database()
db.jobs  # JobRepository
db.users # UserRepository
```

### 3. Strategy Pattern
**Location**: `parsers/`
**Purpose**: Interchangeable parsing algorithms
```python
processor.salary_parser.parse(text)
processor.experience_parser.parse(text)
```

### 4. Singleton Pattern
**Location**: `utils/logger.py`, `data/database.py`
**Purpose**: Single instance of shared resources
```python
logger = setup_logger()  # Single instance
db = get_database()      # Single instance
```

## 🎯 Key Improvements Over Original

| Aspect | Before | After |
|--------|--------|-------|
| **Module Count** | 12 files | 30+ focused files |
| **Avg File Size** | 200-400 lines | 100-200 lines |
| **Parsers** | Monolithic | Modular with data separation |
| **Database** | Single 400+ line file | Repository pattern (4 files) |
| **Data** | Hardcoded in code | Separate data files |
| **Imports** | Messy, direct imports | Clean via `__init__.py` |
| **Naming** | `components/` | `sources/` (clearer) |
| **Logging** | Custom bprint | Professional loguru |
| **Tests** | 16 tests | 16 tests (maintained) |

## 📈 Code Metrics

- **Total Lines**: ~2,500 lines
- **Test Coverage**: Parsers fully tested
- **Avg Module Size**: 120 lines
- **Max Module Size**: 287 lines (salary.py - comprehensive)
- **Min Module Size**: 32 lines (base_repository.py)

## 🔧 Maintenance Guidelines

### Adding a New Parser
1. Create `parsers/new_parser.py`
2. Add exports to `parsers/__init__.py`
3. Integrate in `core/job_processor.py`
4. Write tests in `tests/test_parsers.py`

### Adding a New Job Source
1. Create `sources/new_source.py`
2. Inherit from base class or follow RedditStream pattern
3. Add exports to `sources/__init__.py`
4. Update `main.py` to include new source

### Adding Database Tables
1. Create migration in `data/migrations/`
2. Update models in `data/models/`
3. Add repository methods in appropriate repository
4. Run `python scripts/migrate_db.py`

## 🚀 Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python scripts/migrate_db.py

# Start the bot
python main.py
```

## 🧪 Running Tests

```bash
# Run all tests
python tests/test_parsers.py

# With pytest (if installed)
pytest tests/ -v
```

---

**This architecture follows SOLID principles and clean code practices for maintainability and scalability.**
