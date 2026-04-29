"""Channel routing engine — maps a job posting to one or more channel IDs."""
from typing import List, Optional

from data.models.job import JobPosting
from data.repositories.routing_repository import RoutingRule
from utils.logger import logger


class RoutingEngine:
    """Evaluate routing rules against a job and return target channel IDs.

    Rules are evaluated in priority order (highest first).  The engine
    supports fanout: a single job can be routed to multiple channels if
    more than one rule matches.  Falls back to `default_channel_id` when
    no rule matches.
    """

    def resolve(
        self,
        job: JobPosting,
        rules: List[RoutingRule],
        default_channel_id: Optional[int],
    ) -> List[int]:
        matched: list[int] = []

        for rule in rules:
            if self._rule_matches(rule, job):
                try:
                    channel_id = int(rule.channel_id)
                    if channel_id not in matched:
                        matched.append(channel_id)
                except ValueError:
                    logger.warning(f"RoutingEngine: invalid channel_id '{rule.channel_id}'")

        if not matched and default_channel_id:
            matched = [default_channel_id]

        return matched

    # ------------------------------------------------------------------

    def _rule_matches(self, rule: RoutingRule, job: JobPosting) -> bool:
        rt = rule.rule_type.lower()
        rv = rule.rule_value.lower()

        if rt == "keyword":
            text = f"{job.title} {job.description or ''}".lower()
            return rv in text

        if rt == "subreddit":
            return (job.subreddit or "").lower() == rv

        if rt == "source":
            return job.source.lower() == rv

        if rt == "experience":
            if not job.experience_level:
                return False
            levels = {lvl.strip().lower() for lvl in job.experience_level.split(",")}
            return rv in levels

        if rt == "remote":
            return job.is_remote

        logger.warning(f"RoutingEngine: unknown rule_type '{rule.rule_type}'")
        return False
