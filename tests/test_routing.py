"""Tests for RoutingEngine."""
import pytest
from core.routing import RoutingEngine
from data.repositories.routing_repository import RoutingRule
from data.models.job import JobPosting


def _job(**kw) -> JobPosting:
    defaults = dict(
        url="https://example.com/job/1",
        title="Senior Python Developer",
        created_utc=1_700_000_000,
        discovered_at="2024-01-01T00:00:00",
        source="reddit",
        subreddit="forhire",
        is_remote=False,
        experience_level=None,
        description="",
    )
    defaults.update(kw)
    return JobPosting(**defaults)


def _rule(channel_id: str, rule_type: str, rule_value: str, priority: int = 0) -> RoutingRule:
    return RoutingRule(
        guild_id="123",
        channel_id=channel_id,
        rule_type=rule_type,
        rule_value=rule_value,
        priority=priority,
    )


engine = RoutingEngine()


class TestRoutingEngine:
    def test_no_rules_returns_default(self):
        job = _job()
        result = engine.resolve(job, [], default_channel_id=999)
        assert result == [999]

    def test_no_rules_no_default_returns_empty(self):
        assert engine.resolve(_job(), [], default_channel_id=None) == []

    def test_keyword_match(self):
        rule = _rule("111", "keyword", "python")
        result = engine.resolve(_job(title="Python Developer"), [rule], default_channel_id=999)
        assert 111 in result

    def test_keyword_no_match_falls_back(self):
        rule = _rule("111", "keyword", "java")
        result = engine.resolve(_job(title="Python Developer"), [rule], default_channel_id=999)
        assert result == [999]

    def test_keyword_in_description(self):
        rule = _rule("222", "keyword", "django")
        job = _job(title="Backend Dev", description="experience with Django required")
        assert 222 in engine.resolve(job, [rule], default_channel_id=0)

    def test_subreddit_match(self):
        rule = _rule("333", "subreddit", "remotepython")
        job = _job(subreddit="remotepython")
        assert 333 in engine.resolve(job, [rule], default_channel_id=999)

    def test_source_match(self):
        rule = _rule("444", "source", "hackernews")
        job = _job(source="hackernews")
        assert 444 in engine.resolve(job, [rule], default_channel_id=999)

    def test_experience_match(self):
        rule = _rule("555", "experience", "senior")
        job = _job(experience_level="senior, lead")
        assert 555 in engine.resolve(job, [rule], default_channel_id=999)

    def test_experience_no_match(self):
        rule = _rule("555", "experience", "senior")
        job = _job(experience_level="junior")
        assert 555 not in engine.resolve(job, [rule], default_channel_id=999)

    def test_remote_match(self):
        rule = _rule("666", "remote", "")
        assert 666 in engine.resolve(_job(is_remote=True), [rule], default_channel_id=0)

    def test_remote_no_match(self):
        rule = _rule("666", "remote", "")
        assert 666 not in engine.resolve(_job(is_remote=False), [rule], default_channel_id=0)

    def test_fanout_multiple_rules(self):
        rules = [
            _rule("100", "keyword", "python"),
            _rule("200", "source", "reddit"),
        ]
        result = engine.resolve(_job(title="Python dev", source="reddit"), rules, 999)
        assert 100 in result
        assert 200 in result
        assert 999 not in result  # default not added when rules matched

    def test_no_duplicate_channel_ids(self):
        rules = [_rule("100", "keyword", "python")] * 3
        result = engine.resolve(_job(title="Python"), rules, default_channel_id=0)
        assert result.count(100) == 1

    def test_unknown_rule_type_ignored(self):
        rule = _rule("777", "zodiac", "scorpio")
        result = engine.resolve(_job(), [rule], default_channel_id=888)
        assert result == [888]
