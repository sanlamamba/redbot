"""Tests for the pure-Python TF-IDF MLRanker."""
import pytest
from core.ml_ranker import MLRanker, _TFIDF, _tokenize, MIN_INTERACTIONS
from data.models.job import JobPosting


def _job(title="", description="") -> JobPosting:
    return JobPosting(
        url="https://example.com",
        title=title,
        description=description,
        created_utc=1_700_000_000,
        discovered_at="2024-01-01T00:00:00",
        source="reddit",
    )


class TestTokenize:
    def test_basic(self):
        assert "python" in _tokenize("Python Developer")
        assert "c#" in _tokenize("C# Engineer")

    def test_strips_single_char_tokens(self):
        result = _tokenize("a i ok")
        assert "a" not in result
        assert "i" not in result
        assert "ok" in result

    def test_lowercases(self):
        assert _tokenize("Django")[0] == "django"


class TestTFIDF:
    def test_profile_vector_nonzero(self):
        docs = ["python django flask", "javascript react node"]
        tfidf = _TFIDF(docs)
        profile = tfidf.profile_vector()
        assert len(profile) > 0
        assert all(v > 0 for v in profile.values())

    def test_similar_doc_scores_high(self):
        docs = ["python django flask", "python fastapi uvicorn"]
        tfidf = _TFIDF(docs)
        profile = tfidf.profile_vector()
        score = tfidf.score_doc(profile, "python developer flask experience")
        assert score > 0.1

    def test_unrelated_doc_scores_lower(self):
        docs = ["python django flask"] * 5
        tfidf = _TFIDF(docs)
        profile = tfidf.profile_vector()
        py_score = tfidf.score_doc(profile, "python web developer")
        java_score = tfidf.score_doc(profile, "java spring boot microservices")
        assert py_score > java_score


class TestMLRanker:
    def test_below_min_interactions_returns_neutral(self):
        ranker = MLRanker()
        ranker.build_profile("u1", ["python dev"] * (MIN_INTERACTIONS - 1))
        assert not ranker.has_profile("u1")
        assert ranker.score("u1", _job("anything")) == 0.5

    def test_at_min_interactions_activates(self):
        ranker = MLRanker()
        ranker.build_profile("u2", ["python dev"] * MIN_INTERACTIONS)
        assert ranker.has_profile("u2")

    def test_relevant_job_scores_above_irrelevant(self):
        ranker = MLRanker()
        positive_docs = [
            "python backend developer django",
            "python senior engineer fastapi",
            "python fullstack developer flask aws",
            "python developer remote",
            "python software engineer startup",
        ]
        ranker.build_profile("u3", positive_docs)
        py_job = _job("Python Backend Engineer", "We use Django and FastAPI")
        java_job = _job("Java Spring Developer", "Microservices with Spring Boot")
        assert ranker.score("u3", py_job) > ranker.score("u3", java_job)

    def test_unknown_user_returns_neutral(self):
        ranker = MLRanker()
        assert ranker.score("nobody", _job("some job")) == 0.5

    def test_score_bounded_zero_to_one(self):
        ranker = MLRanker()
        ranker.build_profile("u4", ["python"] * MIN_INTERACTIONS)
        score = ranker.score("u4", _job("python python python python"))
        assert 0.0 <= score <= 1.0
