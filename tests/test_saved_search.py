"""Tests for SavedSearch.matches() filtering logic."""
import pytest
from data.models.user_preference import SavedSearch
from data.models.job import JobPosting


def _search(**kw) -> SavedSearch:
    defaults = dict(user_id="u1", guild_id="g1", name="test",
                    keywords=[], min_salary=None, experience_levels=[],
                    remote_only=False, created_at="2024-01-01")
    defaults.update(kw)
    return SavedSearch(**defaults)


def _job(**kw) -> JobPosting:
    defaults = dict(
        url="https://example.com/1",
        title="Senior Python Developer",
        description="Work with Python and Django on a remote team",
        created_utc=1_700_000_000,
        discovered_at="2024-01-01T00:00:00",
        source="reddit",
        salary_min=120_000,
        experience_level="senior",
        is_remote=True,
    )
    defaults.update(kw)
    return JobPosting(**defaults)


class TestSavedSearchMatches:
    def test_no_filters_matches_everything(self):
        assert _search().matches(_job())

    def test_keyword_in_title(self):
        s = _search(keywords=["python"])
        assert s.matches(_job(title="Python Engineer"))

    def test_keyword_in_description(self):
        s = _search(keywords=["django"])
        assert s.matches(_job(title="Backend Dev", description="Uses Django"))

    def test_keyword_no_match(self):
        s = _search(keywords=["java"])
        assert not s.matches(_job(title="Python Dev", description="Python only"))

    def test_multiple_keywords_any_match(self):
        s = _search(keywords=["rust", "python"])
        assert s.matches(_job(title="Python Developer"))

    def test_min_salary_pass(self):
        s = _search(min_salary=100_000)
        assert s.matches(_job(salary_min=120_000))

    def test_min_salary_fail(self):
        s = _search(min_salary=150_000)
        assert not s.matches(_job(salary_min=120_000))

    def test_min_salary_no_salary_on_job_skipped(self):
        # job with no salary data is not filtered out by salary filter
        s = _search(min_salary=100_000)
        assert s.matches(_job(salary_min=None))

    def test_experience_level_match(self):
        s = _search(experience_levels=["senior"])
        assert s.matches(_job(experience_level="senior"))

    def test_experience_level_multi_match(self):
        s = _search(experience_levels=["lead", "senior"])
        assert s.matches(_job(experience_level="senior, lead"))

    def test_experience_level_no_match(self):
        s = _search(experience_levels=["junior"])
        assert not s.matches(_job(experience_level="senior"))

    def test_experience_level_no_level_on_job_skipped(self):
        s = _search(experience_levels=["senior"])
        assert s.matches(_job(experience_level=None))

    def test_remote_only_pass(self):
        s = _search(remote_only=True)
        assert s.matches(_job(is_remote=True))

    def test_remote_only_fail(self):
        s = _search(remote_only=True)
        assert not s.matches(_job(is_remote=False))

    def test_remote_only_false_matches_onsite(self):
        s = _search(remote_only=False)
        assert s.matches(_job(is_remote=False))

    def test_all_filters_combined_pass(self):
        s = _search(keywords=["python"], min_salary=100_000,
                    experience_levels=["senior"], remote_only=True)
        assert s.matches(_job())

    def test_all_filters_combined_one_fail(self):
        s = _search(keywords=["python"], min_salary=100_000,
                    experience_levels=["senior"], remote_only=True)
        assert not s.matches(_job(is_remote=False))
