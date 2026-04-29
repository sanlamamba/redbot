"""Tests for DeduplicationService URL + content-hash logic."""
import pytest
from unittest.mock import MagicMock
from core.dedup import DeduplicationService
from data.models.job import JobPosting


def _make_db(existing_urls=(), existing_hashes=()):
    """Return a mock Database whose jobs repo returns the given seed data."""
    db = MagicMock()
    rows = [(url, h) for url, h in zip(existing_urls, existing_hashes)]
    conn_ctx = MagicMock()
    conn_ctx.__enter__ = MagicMock(return_value=MagicMock(
        execute=MagicMock(return_value=MagicMock(fetchall=MagicMock(return_value=rows)))
    ))
    conn_ctx.__exit__ = MagicMock(return_value=False)
    db.jobs.get_connection = MagicMock(return_value=conn_ctx)
    return db


def _job(url="https://example.com/1", content_hash=None) -> JobPosting:
    return JobPosting(
        url=url,
        title="Dev",
        created_utc=1_700_000_000,
        discovered_at="2024-01-01T00:00:00",
        source="reddit",
        content_hash=content_hash,
    )


class TestDeduplicationService:
    def test_new_job_not_duplicate(self):
        svc = DeduplicationService(_make_db())
        assert not svc.is_duplicate(_job())

    def test_url_already_in_db_is_duplicate(self):
        url = "https://example.com/seen"
        svc = DeduplicationService(_make_db(existing_urls=[url], existing_hashes=[None]))
        assert svc.is_duplicate(_job(url=url))

    def test_hash_already_in_db_is_duplicate(self):
        h = "abc123def456abcd"
        svc = DeduplicationService(_make_db(existing_urls=["https://other.com"], existing_hashes=[h]))
        assert svc.is_duplicate(_job(url="https://new.com", content_hash=h))

    def test_mark_seen_prevents_future_duplicate(self):
        svc = DeduplicationService(_make_db())
        job = _job(url="https://example.com/new", content_hash="aaabbbcccdddeeee")
        assert not svc.is_duplicate(job)
        svc.mark_seen(job)
        assert svc.is_duplicate(job)

    def test_mark_seen_also_caches_hash(self):
        svc = DeduplicationService(_make_db())
        job = _job(url="https://example.com/a", content_hash="hashval")
        svc.mark_seen(job)
        # Different URL, same hash → duplicate
        job2 = _job(url="https://example.com/b", content_hash="hashval")
        assert svc.is_duplicate(job2)

    def test_no_content_hash_only_url_checked(self):
        svc = DeduplicationService(_make_db())
        job = _job(url="https://example.com/unique", content_hash=None)
        assert not svc.is_duplicate(job)

    def test_cache_size(self):
        urls = ["https://a.com", "https://b.com"]
        svc = DeduplicationService(_make_db(existing_urls=urls, existing_hashes=[None, None]))
        assert svc.cache_size() == 2
