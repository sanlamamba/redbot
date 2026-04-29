"""Salary parsing patterns — all patterns use named capture groups.

Named groups used across patterns:
  currency  — symbol ($, €, £) or code (USD, EUR …)
  min       — lower bound (or sole value)
  max       — upper bound
  k_min     — literal 'k' after min (×1000 multiplier)
  k_max     — literal 'k' after max (×1000 multiplier)

When k_max is present but k_min is absent in a range pattern the extractor
applies the ×1000 multiplier to min as well, UNLESS min contains a comma
(comma formatting already implies full dollars, e.g. $50,000-70k).
"""

# Shared sub-expressions
_SEP = r'(?:[-–—]|\s+to\s+)'                           # range separator
_SYM = r'[\$€£]'                                         # currency symbol
_COD = r'(?:USD|EUR|GBP|CAD|AUD)'                        # currency code
# Numeric value: comma-formatted OR plain integer/decimal up to 6 digits
_NUM = r'(?:\d{1,3}(?:,\d{3})+|\d{1,6})(?:\.\d+)?'

# Currency symbol → ISO code mapping
CURRENCIES = {
    '$': 'USD',
    '€': 'EUR',
    '£': 'GBP',
    'USD': 'USD',
    'EUR': 'EUR',
    'GBP': 'GBP',
    'CAD': 'CAD',
    'AUD': 'AUD',
}

# Patterns ordered from most to least specific.
SALARY_PATTERNS = [
    # 1. Range with leading currency symbol
    #    $50k-$70k · $80,000-$100,000 · €60-80k · $50k-$80,500
    rf'(?P<currency>{_SYM})(?P<min>{_NUM})(?P<k_min>k)?\s*{_SEP}\s*{_SYM}?(?P<max>{_NUM})(?P<k_max>k)?',

    # 2. Range with trailing currency code
    #    50-70k USD · 60-80k EUR
    rf'(?P<min>{_NUM})(?P<k_min>k)?\s*{_SEP}\s*(?P<max>{_NUM})(?P<k_max>k)?\s*(?P<currency>{_COD})',

    # 3. Single value with currency symbol
    #    $80k · €60,000 · $50.5k
    rf'(?P<currency>{_SYM})(?P<min>{_NUM})(?P<k_min>k)?',

    # 4. Single value with trailing currency code
    #    80k USD · 60000 EUR
    rf'(?P<min>{_NUM})(?P<k_min>k)?\s*(?P<currency>{_COD})',

    # 5. Hourly rate
    #    $40/hr · $40/hour · $40 per hour
    rf'(?P<currency>{_SYM})(?P<min>\d{{1,4}})(?P<k_min>k)?\s*(?:/|per)\s*(?:hr|hour)',

    # 6. Monthly rate
    #    $5000/month · $5k/mo · €3,500/month
    rf'(?P<currency>{_SYM})(?P<min>{_NUM})(?P<k_min>k)?\s*(?:/|per)\s*(?:mo|month)',

    # 7. "Up to" — sets max only
    #    up to $100k · up to $100,000
    rf'up\s+to\s+(?P<currency>{_SYM})(?P<max>{_NUM})(?P<k_max>k)?',

    # 8. "Starting at / starting from" — sets min only
    #    starting at $80k · starting from $60,000
    rf'starting\s+(?:at|from)\s+(?P<currency>{_SYM})(?P<min>{_NUM})(?P<k_min>k)?',
]

# Period keywords: substring → canonical period name
PERIOD_KEYWORDS = {
    'year': 'yearly',
    'yearly': 'yearly',
    'annual': 'yearly',
    'annually': 'yearly',
    ' pa': 'yearly',   # per annum (space-prefixed to avoid "spa")
    'month': 'monthly',
    'monthly': 'monthly',
    '/mo': 'monthly',
    'hour': 'hourly',
    'hourly': 'hourly',
    '/hr': 'hourly',
    'per hr': 'hourly',
}
