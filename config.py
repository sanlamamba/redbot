# config.py

SUBREDDITS = [
    'forhire',          # Freelance/contract gigs
    'jobbit',           # Programming job postings
    'jobopenings',      # General job postings
    'remotejs',         # Remote JavaScript jobs
    'remotejobs',       # Remote tech jobs in general
    'remotepython',     # Remote Python jobs
    'remotejava',       # Remote Java jobs
    'webdev',           # Web development and opportunities
    'RemoteWork',       # Remote work across different fields
    'gamedev',          # Game development job listings
    'technology',       # Broader tech industry opportunities
    'techjobs',         # General tech job postings
]

# Keywords for filtering coding-related jobs
KEYWORDS = [
    'python', 'javascript', 'java', 'c++', 'c#', 'developer', 'software',
    'programmer', 'coding', 'backend', 'frontend', 'fullstack', 'web developer',
    'react', 'angular', 'vue', 'node', 'machine learning', 'ai', 'artificial intelligence',
    'devops', 'cloud', 'aws', 'azure', 'docker', 'kubernetes', 'engineer',
    'programming', 'data scientist', 'data analyst', 'golang', 'ruby', 'php',
    'remote', 'work from home', 'full-stack developer', 'backend engineer',
    'senior developer', 'lead developer', 'tech lead', 'software engineer',
    'remote developer', 'remote engineer', 'remote programmer', 'remote software',
    'wordpress', 'shopify', 'magento', 'laravel', 'django', 'flask', 'rails', 'sql', 'nosql',
]

CHECK_FREQUENCY_SECONDS = 60  # Default: 1 minute

POST_LIMIT = 100

SENT_POSTS_FILE = "sent_posts.csv"

