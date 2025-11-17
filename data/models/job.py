"""Job posting data model."""
from dataclasses import dataclass, field, asdict
from typing import Optional, List
import json


@dataclass
class JobPosting:
    """Represents a job posting from any source."""

    # Required fields
    url: str
    title: str
    created_utc: int
    discovered_at: str
    source: str = "reddit"

    # Optional core fields
    id: Optional[int] = None
    description: Optional[str] = None
    subreddit: Optional[str] = None
    author: Optional[str] = None
    source_id: Optional[str] = None

    # Parsed fields
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    salary_period: Optional[str] = None
    experience_level: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool = False

    # Metadata
    matched_keywords: List[str] = field(default_factory=list)
    priority_score: int = 0
    duplicate_of: Optional[int] = None

    # Sentiment analysis
    sentiment_score: Optional[float] = None
    red_flags: List[str] = field(default_factory=list)

    # Archival
    archived: bool = False
    archived_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        data = asdict(self)
        # Convert lists to JSON strings for SQLite
        data['matched_keywords'] = json.dumps(self.matched_keywords) if self.matched_keywords else None
        data['red_flags'] = json.dumps(self.red_flags) if self.red_flags else None
        return data

    @staticmethod
    def from_dict(data: dict) -> 'JobPosting':
        """Create JobPosting from dictionary."""
        # Convert JSON strings back to lists
        if data.get('matched_keywords') and isinstance(data['matched_keywords'], str):
            data['matched_keywords'] = json.loads(data['matched_keywords'])
        if data.get('red_flags') and isinstance(data['red_flags'], str):
            data['red_flags'] = json.loads(data['red_flags'])

        # Handle None values
        data['matched_keywords'] = data.get('matched_keywords') or []
        data['red_flags'] = data.get('red_flags') or []

        return JobPosting(**data)
