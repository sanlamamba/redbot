"""Red flag keywords for job posting analysis."""

RED_FLAGS = {
    "compensation": [
        "unpaid", "no salary", "work for equity", "exposure",
        "sweat equity", "deferred compensation", "commission only",
        "potential to earn", "unlimited earning potential"
    ],
    "work_life": [
        "unlimited overtime", "long hours expected", "nights and weekends",
        "must be available 24/7", "on call 24/7", "no work life balance",
        "hustle culture", "grind", "sacrifice", "all hands on deck"
    ],
    "company_culture": [
        "family atmosphere", "we're like a family", "pizza parties",
        "fun work environment", "ping pong table", "beer on tap",
        "casual fridays", "work hard play hard", "fast paced startup"
    ],
    "unrealistic_expectations": [
        "wear many hats", "many hats", "jack of all trades",
        "unicorn", "rockstar", "ninja", "guru", "wizard",
        "10x engineer", "full stack ninja", "growth hacker",
        "passionate only", "must be passionate", "must love",
        "obsessed with", "eat sleep code"
    ],
    "vague_requirements": [
        "self starter", "self-starter", "motivated individual",
        "go getter", "proactive", "takes initiative",
        "figure it out", "hit the ground running",
        "little to no guidance"
    ],
    "demanding": [
        "perfectionist", "attention to detail required",
        "no room for error", "zero mistakes", "flawless execution",
        "elite performance", "only the best", "top talent only"
    ]
}

POSITIVE_INDICATORS = [
    "competitive salary", "401k", "health insurance", "benefits",
    "remote", "flexible hours", "work life balance", "pto", "vacation",
    "professional development", "training", "growth opportunities",
    "collaborative", "supportive", "mentorship"
]

NEGATIVE_INDICATORS = [
    "urgent", "immediately available", "asap", "immediate start",
    "tight deadline", "aggressive timeline", "pressure", "stress"
]
