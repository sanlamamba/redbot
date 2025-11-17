"""NLP-based extraction of skills, location, and requirements."""
import re
from typing import List, Dict, Optional
from .data.tech_stack import TECH_STACK


class NLPExtractor:
    """Extract structured information using NLP techniques."""

    LOCATION_PATTERNS = [
        r'(?:location|based in|located in|office in):\s*([A-Z][a-zA-Z\s,]+)',
        r'\b([A-Z][a-zA-Z]+,\s*[A-Z]{2})\b',  # City, ST format
        r'\b(Remote|Hybrid|On-site|Onsite)\b',
    ]

    REMOTE_KEYWORDS = [
        "remote", "work from home", "wfh", "distributed", "anywhere",
        "remote-first", "fully remote", "100% remote", "remote work"
    ]

    def __init__(self):
        """Initialize NLP extractor."""
        self.location_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.LOCATION_PATTERNS
        ]

        self.tech_patterns = {
            tech: re.compile(rf'\b{re.escape(tech)}\b', re.IGNORECASE)
            for tech in TECH_STACK
        }

    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from text."""
        if not text:
            return []

        return [
            tech for tech, pattern in self.tech_patterns.items()
            if pattern.search(text)
        ]

    def extract_location(self, text: str) -> Dict[str, Optional[str]]:
        """Extract location information from text."""
        if not text:
            return {"location": None, "is_remote": False, "work_type": "unknown"}

        text_lower = text.lower()

        is_remote = any(kw in text_lower for kw in self.REMOTE_KEYWORDS)

        # Determine work type
        work_type = "unknown"
        if "hybrid" in text_lower:
            work_type = "hybrid"
        elif is_remote:
            work_type = "remote"
        elif any(kw in text_lower for kw in ["on-site", "onsite", "office"]):
            work_type = "onsite"

        # Extract specific location
        location = None
        for pattern in self.location_patterns:
            match = pattern.search(text)
            if match:
                loc = match.group(1).strip()
                if loc.lower() not in ["remote", "hybrid", "on-site", "onsite"]:
                    location = loc
                    break

        return {"location": location, "is_remote": is_remote, "work_type": work_type}

    def extract_requirements(self, text: str) -> Dict[str, List[str]]:
        """Extract job requirements from text."""
        if not text:
            return {"must_have": [], "nice_to_have": []}

        sections = self._split_into_sections(text)

        requirements_section = self._find_section(
            sections, ["requirements", "required", "qualifications", "must have"]
        )
        preferred_section = self._find_section(
            sections, ["preferred", "nice to have", "bonus", "plus"]
        )

        must_have = self._extract_bullet_points(requirements_section) if requirements_section else []
        nice_to_have = self._extract_bullet_points(preferred_section) if preferred_section else []

        return {"must_have": must_have[:10], "nice_to_have": nice_to_have[:10]}

    def extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name from text."""
        patterns = [
            r'(?:at|@|for)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s+is\s+hiring|\s+seeks|\s+-)',
            r'^([A-Z][A-Za-z0-9\s&]+?)\s+(?:is hiring|seeks|looking for)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                company = match.group(1).strip()
                if len(company) < 50 and not any(
                    word in company.lower()
                    for word in ["we are", "looking for", "hiring", "position"]
                ):
                    return company
        return None

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split text into sections based on headers."""
        sections = {}
        current_section = "main"
        current_content = []

        for line in text.split('\n'):
            if ':' in line or (line.isupper() and len(line) > 3):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line.lower().strip(':').strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _find_section(self, sections: Dict[str, str], keywords: List[str]) -> Optional[str]:
        """Find section matching any of the keywords."""
        for section_name, content in sections.items():
            if any(kw in section_name for kw in keywords):
                return content
        return None

    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points from text."""
        bullet_points = []
        patterns = [
            r'^\s*[-•*]\s+(.+)$',  # - or • bullet
            r'^\s*\d+\.\s+(.+)$',  # 1. numbered
        ]

        for line in text.split('\n'):
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    point = match.group(1).strip()
                    if len(point) > 10:
                        bullet_points.append(point)
                    break

        return bullet_points
