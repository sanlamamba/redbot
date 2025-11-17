"""Salary extraction and parsing."""
import re
from typing import Optional
from dataclasses import dataclass
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

        # Extract amounts
        amounts = []
        for g in groups:
            if g and g not in self.currencies and not g.upper() in self.currencies:
                # Clean and parse number
                cleaned = g.replace(',', '').replace('.', '')
                if cleaned.isdigit():
                    amount = int(cleaned)
                    # If ends with 'k', multiply by 1000
                    if 'k' in match.group(0).lower():
                        amount *= 1000
                    amounts.append(amount)

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
            # Assume 40 hours/week, 52 weeks/year
            multiplier = 40 * 52
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

        # Reasonable salary range (10k to 1M annually)
        min_val = salary_info.min or salary_info.max
        max_val = salary_info.max or salary_info.min

        if min_val < 10000 or max_val > 1000000:
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
