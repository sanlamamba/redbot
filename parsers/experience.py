"""Experience level detection and classification."""
from typing import List, Set
import re


class ExperienceParser:
    """Extract experience level from job postings."""

    # Experience level keywords
    JUNIOR_KEYWORDS = [
        "junior", "jr", "entry level", "entry-level", "graduate",
        "intern", "internship", "0-2 years", "0 - 2 years",
        "early career", "beginner", "trainee", "apprentice",
        "new grad", "recent graduate"
    ]

    MID_KEYWORDS = [
        "mid level", "mid-level", "intermediate", "2-5 years",
        "3+ years", "3-5 years", "experienced", "professional",
        "regular", "standard"
    ]

    SENIOR_KEYWORDS = [
        "senior", "sr", "lead", "principal", "staff",
        "5+ years", "5-10 years", "expert", "advanced",
        "architect", "experienced professional", "veteran"
    ]

    LEAD_KEYWORDS = [
        "lead", "tech lead", "technical lead", "team lead",
        "principal", "staff engineer", "distinguished",
        "fellow", "chief", "head of", "director",
        "vp", "vice president", "cto", "10+ years"
    ]

    # Level icons (emoji)
    LEVEL_ICONS = {
        "junior": "🌱",
        "mid": "🌿",
        "senior": "🌳",
        "lead": "👑",
    }

    def __init__(self):
        """Initialize experience parser."""
        # Compile patterns for efficiency
        self.patterns = {
            "junior": self._compile_keywords(self.JUNIOR_KEYWORDS),
            "mid": self._compile_keywords(self.MID_KEYWORDS),
            "senior": self._compile_keywords(self.SENIOR_KEYWORDS),
            "lead": self._compile_keywords(self.LEAD_KEYWORDS),
        }

    def _compile_keywords(self, keywords: List[str]) -> List[re.Pattern]:
        """Compile keywords into regex patterns.

        Args:
            keywords: List of keyword strings

        Returns:
            List of compiled regex patterns
        """
        patterns = []
        for keyword in keywords:
            # Word boundary to avoid partial matches
            pattern = rf'\b{re.escape(keyword)}\b'
            patterns.append(re.compile(pattern, re.IGNORECASE))
        return patterns

    def parse(self, text: str) -> List[str]:
        """Parse experience levels from text.

        Args:
            text: Text to parse (title + description)

        Returns:
            List of detected experience levels (can be multiple)
        """
        if not text:
            return []

        levels: Set[str] = set()

        # Check for each level (order matters - check lead first, then senior, etc.)
        for level, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    levels.add(level)
                    break  # Found this level, move to next

        # Convert to sorted list (lead > senior > mid > junior)
        level_order = {"lead": 0, "senior": 1, "mid": 2, "junior": 3}
        sorted_levels = sorted(levels, key=lambda x: level_order.get(x, 4))

        return sorted_levels

    def get_primary_level(self, text: str) -> str:
        """Get primary experience level from text.

        Args:
            text: Text to parse

        Returns:
            Primary level ("junior", "mid", "senior", "lead", or "unknown")
        """
        levels = self.parse(text)
        if not levels:
            return "unknown"

        # Return highest level detected
        return levels[0]

    def get_icon(self, level: str) -> str:
        """Get emoji icon for experience level.

        Args:
            level: Experience level

        Returns:
            Emoji icon
        """
        return self.LEVEL_ICONS.get(level, "")

    def format_levels(self, levels: List[str]) -> str:
        """Format experience levels for display.

        Args:
            levels: List of experience levels

        Returns:
            Formatted string with icons
        """
        if not levels:
            return ""

        formatted = []
        for level in levels:
            icon = self.get_icon(level)
            formatted.append(f"{icon} {level.capitalize()}")

        return " / ".join(formatted)

    def is_level_match(self, detected_levels: List[str], preferred_levels: List[str]) -> bool:
        """Check if detected levels match user preferences.

        Args:
            detected_levels: Detected experience levels
            preferred_levels: User's preferred levels

        Returns:
            True if any match
        """
        if not preferred_levels or not detected_levels:
            return True  # No preference or no detection = match

        return any(level in preferred_levels for level in detected_levels)
