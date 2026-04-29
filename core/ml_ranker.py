"""TF-IDF based relevance ranker — no external ML dependencies required.

Workflow:
  1. Collect jobs a user has 'saved' or 'applied' as positive signal.
  2. Build a TF-IDF corpus from those job titles + descriptions.
  3. Score new jobs by cosine similarity to the user's interest profile.

The ranker is per-user and ephemeral (not persisted between restarts),
rebuilt on demand from the interaction table.  Once a user has at least
MIN_INTERACTIONS positive interactions the ranker activates; below that
threshold all jobs receive a neutral score of 0.5.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from data.models.job import JobPosting

MIN_INTERACTIONS = 5  # require this many liked jobs before ranking kicks in


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9#+]{2,}", text.lower())


class _TFIDF:
    """Minimal TF-IDF implementation over a small corpus."""

    def __init__(self, docs: List[str]):
        self._n = len(docs)
        tokens_per_doc = [_tokenize(d) for d in docs]

        # IDF: log((N+1)/(df+1)) + 1  (smoothed)
        df: Counter[str] = Counter()
        for tokens in tokens_per_doc:
            df.update(set(tokens))
        self._idf: Dict[str, float] = {
            t: math.log((self._n + 1) / (c + 1)) + 1 for t, c in df.items()
        }

        # Build and L2-normalise document vectors
        self._vecs = [self._vectorise(tokens) for tokens in tokens_per_doc]

    def _vectorise(self, tokens: List[str]) -> Dict[str, float]:
        tf = Counter(tokens)
        total = max(len(tokens), 1)
        vec: Dict[str, float] = {}
        for t, c in tf.items():
            if t in self._idf:
                vec[t] = (c / total) * self._idf[t]
        # L2 normalise
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def profile_vector(self) -> Dict[str, float]:
        """Return the centroid of all document vectors (user interest profile)."""
        merged: Dict[str, float] = {}
        for vec in self._vecs:
            for t, v in vec.items():
                merged[t] = merged.get(t, 0) + v
        n = max(self._n, 1)
        norm = math.sqrt(sum((v / n) ** 2 for v in merged.values())) or 1.0
        return {t: (v / n) / norm for t, v in merged.items()}

    def score_doc(self, profile: Dict[str, float], text: str) -> float:
        """Cosine similarity between `text` and the profile vector (0-1)."""
        tokens = _tokenize(text)
        vec = self._vectorise(tokens)
        dot = sum(profile.get(t, 0) * v for t, v in vec.items())
        return min(1.0, max(0.0, dot))


class MLRanker:
    """Per-user relevance scorer backed by interaction history."""

    def __init__(self):
        self._profiles: Dict[str, Optional[Dict[str, float]]] = {}

    def build_profile(self, user_id: str, positive_texts: List[str]) -> None:
        """Train the user profile from a list of liked job texts."""
        if len(positive_texts) < MIN_INTERACTIONS:
            self._profiles[user_id] = None  # not enough data
            return
        tfidf = _TFIDF(positive_texts)
        self._profiles[user_id] = tfidf.profile_vector()

    def score(self, user_id: str, job: "JobPosting") -> float:
        """Return a relevance score 0.0–1.0 for this job (0.5 = unknown)."""
        profile = self._profiles.get(user_id)
        if profile is None:
            return 0.5
        text = f"{job.title} {job.description or ''}"
        tfidf = _TFIDF([text])  # single-doc used only to vectorise
        return tfidf.score_doc(profile, text)

    def has_profile(self, user_id: str) -> bool:
        return user_id in self._profiles and self._profiles[user_id] is not None


# ------------------------------------------------------------------
# Module-level helper — load a profile from the DB on demand
# ------------------------------------------------------------------

def load_profile_from_db(ranker: MLRanker, user_id: str, db) -> None:
    """Populate a user's ranker profile from their saved/applied interactions."""
    try:
        with db.users.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT jp.title, jp.description
                FROM user_job_interactions uji
                JOIN job_postings jp ON uji.job_url = jp.url
                WHERE uji.user_id = ? AND uji.action IN ('saved','applied')
                """,
                (user_id,),
            ).fetchall()
    except Exception:
        return

    texts = [f"{r['title']} {r['description'] or ''}" for r in rows]
    ranker.build_profile(user_id, texts)


# Global singleton — shared across the bot process
_ranker: Optional[MLRanker] = None


def get_ranker() -> MLRanker:
    global _ranker
    if _ranker is None:
        _ranker = MLRanker()
    return _ranker
