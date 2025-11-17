"""Salary parsing patterns and constants."""

# Currency symbols and codes
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

# Salary regex patterns (ordered by specificity)
SALARY_PATTERNS = [
    # Range with currency: $50k-$70k, $50K-70K, $80,000-$100,000
    r'([\$€£])(\d{1,3}[,.]?\d{0,3})k?\s*[-–—to]\s*\1?(\d{1,3}[,.]?\d{0,3})k?',

    # Range without repeated currency: $50-70k, €60-80k
    r'([\$€£])(\d{1,3})\s*[-–—to]\s*(\d{1,3})k',

    # Range with currency code: 50-70k USD, 60-80k EUR
    r'(\d{1,3}[,.]?\d{0,3})k?\s*[-–—to]\s*(\d{1,3}[,.]?\d{0,3})k?\s*(USD|EUR|GBP|CAD|AUD)',

    # Single value with currency: $80k, €60,000
    r'([\$€£])(\d{1,3}[,.]?\d{0,3})k?',

    # Single value with currency code: 80k USD, 60000 EUR
    r'(\d{1,3}[,.]?\d{0,3})k?\s*(USD|EUR|GBP|CAD|AUD)',

    # Hourly rate: $40/hr, $40/hour, $40 per hour
    r'([\$€£])(\d{1,3})\s*(?:/|per)\s*(?:hr|hour)',

    # Monthly rate: $5000/month, $5k/mo
    r'([\$€£])(\d{1,3}[,.]?\d{0,3})k?\s*(?:/|per)\s*(?:mo|month)',

    # "Up to" patterns: up to $100k, up to $100,000
    r'up\s+to\s+([\$€£])(\d{1,3}[,.]?\d{0,3})k?',

    # "Starting at" patterns: starting at $80k
    r'starting\s+(?:at|from)\s+([\$€£])(\d{1,3}[,.]?\d{0,3})k?',
]

# Period keywords
PERIOD_KEYWORDS = {
    'year': 'yearly',
    'yearly': 'yearly',
    'annual': 'yearly',
    'annually': 'yearly',
    'pa': 'yearly',  # per annum
    'month': 'monthly',
    'monthly': 'monthly',
    'mo': 'monthly',
    'hour': 'hourly',
    'hourly': 'hourly',
    'hr': 'hourly',
}
