"""User preference and saved search data models."""
from dataclasses import dataclass, field
from typing import List, Optional
import json


@dataclass
class SavedSearch:
    """A user-defined saved search filter."""

    user_id: str
    guild_id: str
    name: str
    keywords: List[str] = field(default_factory=list)
    min_salary: Optional[int] = None
    experience_levels: List[str] = field(default_factory=list)
    remote_only: bool = False
    created_at: str = ""
    id: Optional[int] = None

    def matches(self, job) -> bool:
        """Return True if job satisfies all filter criteria."""
        text = f"{job.title} {job.description or ''}".lower()

        if self.keywords:
            if not any(kw.lower() in text for kw in self.keywords):
                return False

        if self.min_salary and job.salary_min:
            if job.salary_min < self.min_salary:
                return False

        if self.experience_levels and job.experience_level:
            job_levels = {lvl.strip().lower() for lvl in job.experience_level.split(",")}
            wanted = {lvl.lower() for lvl in self.experience_levels}
            if not job_levels & wanted:
                return False

        if self.remote_only and not job.is_remote:
            return False

        return True

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "name": self.name,
            "keywords": json.dumps(self.keywords),
            "min_salary": self.min_salary,
            "experience_levels": json.dumps(self.experience_levels),
            "remote_only": int(self.remote_only),
            "created_at": self.created_at,
        }

    @staticmethod
    def from_row(row: dict) -> "SavedSearch":
        return SavedSearch(
            id=row["id"],
            user_id=row["user_id"],
            guild_id=row["guild_id"],
            name=row["name"],
            keywords=json.loads(row["keywords"] or "[]"),
            min_salary=row["min_salary"],
            experience_levels=json.loads(row["experience_levels"] or "[]"),
            remote_only=bool(row["remote_only"]),
            created_at=row["created_at"],
        )
