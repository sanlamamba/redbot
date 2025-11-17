"""Sentiment analysis and red flag detection for job postings."""
from typing import List, Dict
import re
from .data.red_flags import RED_FLAGS, POSITIVE_INDICATORS, NEGATIVE_INDICATORS


class SentimentAnalyzer:
    """Analyze job posting sentiment and detect red flags."""

    def __init__(self):
        """Initialize sentiment analyzer."""
        # Flatten red flags for quick access
        self.all_red_flags = [
            flag for flags in RED_FLAGS.values() for flag in flags
        ]

        # Compile patterns
        self.red_flag_patterns = [
            re.compile(rf'\b{re.escape(flag)}\b', re.IGNORECASE)
            for flag in self.all_red_flags
        ]

    def analyze(self, text: str) -> Dict:
        """Analyze job posting for sentiment and red flags.

        Args:
            text: Job posting text (title + description)

        Returns:
            Dict with: score, red_flags, warnings, is_suspicious
        """
        if not text:
            return {
                "score": 0.0,
                "red_flags": [],
                "warnings": [],
                "is_suspicious": False
            }

        text_lower = text.lower()

        detected_flags = self._detect_red_flags(text_lower)
        warnings = self._categorize_warnings(detected_flags)
        score = self._calculate_sentiment_score(text_lower, len(detected_flags))
        is_suspicious = len(detected_flags) >= 3 or score < -0.3

        return {
            "score": score,
            "red_flags": detected_flags,
            "warnings": warnings,
            "is_suspicious": is_suspicious
        }

    def _detect_red_flags(self, text: str) -> List[str]:
        """Detect red flags in text."""
        detected = []
        for pattern, flag in zip(self.red_flag_patterns, self.all_red_flags):
            if pattern.search(text):
                detected.append(flag)
        return detected

    def _categorize_warnings(self, detected_flags: List[str]) -> List[str]:
        """Categorize detected red flags into warning types."""
        warnings = set()
        for category, flags in RED_FLAGS.items():
            if any(flag in detected_flags for flag in flags):
                warnings.add(category)
        return list(warnings)

    def _calculate_sentiment_score(self, text: str, red_flag_count: int) -> float:
        """Calculate sentiment score for job posting."""
        score = 0.0

        # Count positive/negative indicators
        positive_count = sum(1 for ind in POSITIVE_INDICATORS if ind in text)
        negative_count = sum(1 for ind in NEGATIVE_INDICATORS if ind in text)

        score += positive_count * 0.1
        score -= negative_count * 0.1
        score -= red_flag_count * 0.2

        return max(-1.0, min(1.0, round(score, 2)))

    def format_warnings(self, analysis: Dict) -> str:
        """Format warnings for display."""
        if not analysis["red_flags"]:
            return ""

        warning_map = {
            "compensation": "⚠️ Compensation concerns",
            "work_life": "⚠️ Work-life balance issues",
            "unrealistic_expectations": "⚠️ Unrealistic expectations",
            "vague_requirements": "⚠️ Vague requirements"
        }

        warnings = [
            warning_map[w] for w in analysis["warnings"]
            if w in warning_map
        ]

        return " | ".join(warnings)

    def get_recommendation(self, analysis: Dict) -> str:
        """Get recommendation based on analysis."""
        if analysis["is_suspicious"]:
            return "⚠️ Review carefully - multiple concerns detected"
        elif analysis["red_flags"]:
            return "⚡ Some concerns detected - proceed with caution"
        elif analysis["score"] > 0.3:
            return "✅ Looks good - positive indicators found"
        return ""
