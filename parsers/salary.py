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
        self.currencies = CURRENCIES
        self.period_keywords = PERIOD_KEYWORDS
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in SALARY_PATTERNS]
        self.min_valid_annual = get_config("parsers.salary.min_valid_annual", 10000)
        self.max_valid_annual = get_config("parsers.salary.max_valid_annual", 1000000)
        self.hours_per_week = get_config("parsers.salary.hours_per_week", 40)

    def parse(self, text: str) -> Optional[SalaryInfo]:
        """Parse salary information from text."""
        if not text:
            return None

        text = text.lower()

        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                salary_info = self._extract_from_match(match, text)
                if salary_info and self._is_valid_salary(salary_info):
                    return salary_info

        return None

    def _extract_from_match(self, match: re.Match, text: str) -> Optional[SalaryInfo]:
        """Extract salary info using named groups from the match."""
        d = match.groupdict()
        salary = SalaryInfo(original_text=match.group(0))

        # --- Currency ---
        raw = d.get('currency')
        if raw:
            salary.currency = self.currencies.get(raw) or self.currencies.get(raw.upper(), 'USD')

        # --- Max amount (patterns 1, 2, 7) ---
        if d.get('max'):
            amount = float(d['max'].replace(',', ''))
            if d.get('k_max'):
                amount *= 1000
            salary.max = int(amount)

        # --- Min amount (patterns 1–6, 8) ---
        if d.get('min'):
            amount = float(d['min'].replace(',', ''))
            if d.get('k_min'):
                amount *= 1000
            elif d.get('k_max') and salary.max and ',' not in d['min']:
                # Shorthand range: trailing k applies to both values.
                # e.g. €60-80k → min=60k, max=80k
                # Not applied when min is comma-formatted ($50,000-70k).
                amount *= 1000
            salary.min = int(amount)

        # Single-value patterns produce only min; treat as exact value (min == max).
        if salary.min and not salary.max:
            salary.max = salary.min

        # --- Period ---
        salary.period = self._detect_period(match.group(0), text)
        if salary.period != 'yearly':
            salary = self._normalize_to_annual(salary)
        else:
            salary.period = 'yearly'

        return salary

    def _detect_period(self, match_text: str, full_text: str) -> str:
        """Detect salary period from the match text and surrounding context."""
        combined = match_text.lower()

        for keyword, period in self.period_keywords.items():
            if keyword in combined:
                return period

        # Check up to 25 chars after the match in the full text
        match_end = full_text.find(match_text.lower()) + len(match_text)
        context = full_text[match_end:match_end + 25]

        for keyword, period in self.period_keywords.items():
            if keyword in context:
                return period

        return 'yearly'

    def _normalize_to_annual(self, salary: SalaryInfo) -> SalaryInfo:
        """Multiply hourly or monthly amounts up to annual equivalents."""
        if salary.period == 'hourly':
            multiplier = self.hours_per_week * 52
        elif salary.period == 'monthly':
            multiplier = 12
        else:
            multiplier = 1

        if salary.min:
            salary.min *= multiplier
        if salary.max:
            salary.max *= multiplier

        salary.period = 'yearly'
        return salary

    def _is_valid_salary(self, salary: SalaryInfo) -> bool:
        """Return True if salary amounts are within configured bounds."""
        if not salary.min and not salary.max:
            return False

        min_val = salary.min or salary.max
        max_val = salary.max or salary.min

        if min_val < self.min_valid_annual or max_val > self.max_valid_annual:
            return False

        if salary.min and salary.max and salary.max < salary.min:
            return False

        return True

    def format_salary(self, salary: SalaryInfo) -> str:
        """Format salary for display."""
        sym = '£' if salary.currency == 'GBP' else '€' if salary.currency == 'EUR' else '$'

        if salary.min and salary.max:
            if salary.min == salary.max:
                return f"{sym}{salary.min:,}/year"
            return f"{sym}{salary.min:,}-{salary.max:,}/year"
        if salary.max:
            return f"Up to {sym}{salary.max:,}/year"
        if salary.min:
            return f"From {sym}{salary.min:,}/year"

        return "Salary not specified"
