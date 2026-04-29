"""Salary extraction and parsing."""
import re
from typing import Optional
from dataclasses import dataclass
from utils.config import get_config
from .data.salary_patterns import CURRENCIES, SALARY_PATTERNS, PERIOD_KEYWORDS


@dataclass
class SalaryInfo:
    """Parsed salary information."""

    min: Optional[int] = None
    max: Optional[int] = None
    currency: str = "USD"
    period: Optional[str] = None  # yearly, monthly, hourly
    original_text: str = ""


class SalaryParser:
    """Extract salary information from job postings."""

    def __init__(self):
        """Initialize salary parser."""
        self.currencies = CURRENCIES
        self.period_keywords = PERIOD_KEYWORDS
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in SALARY_PATTERNS]
        self.min_valid_annual = get_config("parsers.salary.min_valid_annual", 10000)
        self.max_valid_annual = get_config("parsers.salary.max_valid_annual", 1000000)
        self.hours_per_week = get_config("parsers.salary.hours_per_week", 40)

    def parse(self, text: str) -> Optional[SalaryInfo]:
        """Parse salary information from text.

        Args:
            text: Text to parse (title + description)

        Returns:
            SalaryInfo if salary found, None otherwise
        """
        if not text:
            return None

        # Clean text
        text = text.lower()

        # Try each pattern
        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                salary_info = self._extract_from_match(match, text)
                if salary_info and self._is_valid_salary(salary_info):
                    return salary_info

        return None

    def _extract_from_match(self, match: re.Match, text: str) -> Optional[SalaryInfo]:
        """Extract salary info from regex match.

        Args:
            match: Regex match object
            text: Original text for context

        Returns:
            SalaryInfo if valid, None otherwise
        """
        groups = match.groups()
        salary_info = SalaryInfo(original_text=match.group(0))

        # Determine currency
        currency_symbol = groups[0] if groups[0] in self.currencies else None
        if currency_symbol:
            salary_info.currency = self.currencies[currency_symbol]
        else:
            # Check for currency code in groups
            for g in groups:
                if g and g.upper() in self.currencies:
                    salary_info.currency = g.upper()
                    break

        # Extract amounts — use 1-based group indices for per-token k-suffix detection
        match_str = match.group(0).lower()
        amounts = []

        # Detect a trailing 'k' that applies to all numbers in a shorthand range
        # (e.g. "€60-80k" or "50-70k USD" where the k is shared, not per-token).
        # Find where the last numeric group ends in the match string.
        last_num_end = 0
        for group_idx, g in enumerate(groups, start=1):
            if g and g not in self.currencies and g.upper() not in self.currencies:
                last_num_end = max(last_num_end, match.end(group_idx) - match.start())
        # A trailing 'k' exists if the next non-space character after all numbers is 'k'.
        has_trailing_k = False
        for ch in match_str[last_num_end:]:
            if ch == 'k':
                has_trailing_k = True
                break
            if ch.isdigit():
                break  # another digit before k — not a shared trailing k

        for group_idx, g in enumerate(groups, start=1):
            if not g:
                continue
            if g in self.currencies or g.upper() in self.currencies:
                continue
            # Strip commas (thousand separators only) — preserve decimal points
            cleaned = g.replace(',', '')
            try:
                amount = float(cleaned)
            except ValueError:
                continue
            # Per-token: check if the character immediately after this group is 'k'
            pos_after = match.end(group_idx) - match.start()
            has_own_k = pos_after < len(match_str) and match_str[pos_after] == 'k'
            # Apply ×1000 if: this token has its own k, OR a trailing k is shared
            # and the token is not comma-formatted (comma means already full dollars).
            if has_own_k or (has_trailing_k and ',' not in g):
                amount *= 1000
            amounts.append(int(amount))

        if len(amounts) == 1:
            # Single value
            if 'up to' in text:
                salary_info.max = amounts[0]
            elif 'starting' in text or 'from' in text:
                salary_info.min = amounts[0]
            else:
                # Ambiguous, use as both min and max
                salary_info.min = amounts[0]
                salary_info.max = amounts[0]
        elif len(amounts) >= 2:
            # Range
            salary_info.min = min(amounts)
            salary_info.max = max(amounts)

        # Detect period
        salary_info.period = self._detect_period(match.group(0), text)

        # Normalize to annual if not yearly
        if salary_info.period and salary_info.period != 'yearly':
            salary_info = self._normalize_to_annual(salary_info)
        else:
            salary_info.period = 'yearly'

        return salary_info

    def _detect_period(self, match_text: str, full_text: str) -> str:
        """Detect salary period from context.

        Args:
            match_text: Matched salary text
            full_text: Full text for context

        Returns:
            Period string (yearly, monthly, hourly)
        """
        # Check match text first
        for keyword, period in self.period_keywords.items():
            if keyword in match_text:
                return period

        # Check surrounding context (20 chars after match)
        match_end = full_text.find(match_text) + len(match_text)
        context = full_text[match_end:match_end + 20]

        for keyword, period in self.period_keywords.items():
            if keyword in context:
                return period

        # Default to yearly
        return 'yearly'

    def _normalize_to_annual(self, salary_info: SalaryInfo) -> SalaryInfo:
        """Normalize salary to annual amount.

        Args:
            salary_info: SalaryInfo with period

        Returns:
            Normalized SalaryInfo
        """
        multiplier = 1

        if salary_info.period == 'hourly':
            multiplier = self.hours_per_week * 52
        elif salary_info.period == 'monthly':
            multiplier = 12

        if salary_info.min:
            salary_info.min *= multiplier
        if salary_info.max:
            salary_info.max *= multiplier

        salary_info.period = 'yearly'
        return salary_info

    def _is_valid_salary(self, salary_info: SalaryInfo) -> bool:
        """Validate extracted salary.

        Args:
            salary_info: SalaryInfo to validate

        Returns:
            True if valid
        """
        # Must have at least min or max
        if not salary_info.min and not salary_info.max:
            return False

        # Reasonable salary range (configurable bounds)
        min_val = salary_info.min or salary_info.max
        max_val = salary_info.max or salary_info.min

        if min_val < self.min_valid_annual or max_val > self.max_valid_annual:
            return False

        # Max must be >= min
        if salary_info.min and salary_info.max:
            if salary_info.max < salary_info.min:
                return False

        return True

    def format_salary(self, salary_info: SalaryInfo) -> str:
        """Format salary for display.

        Args:
            salary_info: SalaryInfo to format

        Returns:
            Formatted string
        """
        currency_symbol = '£' if salary_info.currency == 'GBP' else \
                         '€' if salary_info.currency == 'EUR' else '$'

        if salary_info.min and salary_info.max:
            if salary_info.min == salary_info.max:
                return f"{currency_symbol}{salary_info.min:,}/year"
            else:
                return f"{currency_symbol}{salary_info.min:,}-{salary_info.max:,}/year"
        elif salary_info.max:
            return f"Up to {currency_symbol}{salary_info.max:,}/year"
        elif salary_info.min:
            return f"From {currency_symbol}{salary_info.min:,}/year"

        return "Salary not specified"
