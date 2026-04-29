"""Abstract base class for all job sources."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

from data.models.job import JobPosting


class BaseSource(ABC):
    """Every job source must implement this interface.

    The scraping loop in DiscordBot.start_scraping_jobs() iterates over a
    list of BaseSource instances and calls get_submissions() on each one.
    Sources that fail repeatedly are backed off exponentially (handled by
    the scraping loop, not here).
    """

    #: Human-readable name shown in logs and !stats output.
    name: str = "unknown"

    #: Whether this source should be polled. Sources can set this False
    #: to temporarily disable themselves without being removed from the list.
    enabled: bool = True

    @abstractmethod
    async def get_submissions(self) -> List[JobPosting]:
        """Fetch new job postings from this source.

        Returns:
            List of JobPosting objects that have not yet been seen.
            The caller (DiscordBot) handles deduplication, so sources
            may return jobs they have already returned in previous cycles
            if they have no local memory — dedup will suppress them.
        """

    async def health_check(self) -> bool:
        """Return True if the source is reachable and healthy.

        The default implementation always returns True (no-op check).
        Override in sources that can cheaply verify connectivity.
        """
        return True
