"""Filter scraped jobs by the Japanese level chosen on the search form."""

from __future__ import annotations

import re
from typing import Optional

# Highest requirement a choice can satisfy. Jobs with no stated level stay at 0.
_CHOICE_RANK = {
    "no japanese": 0,
    "daily conversation level": 2,
    "intermediate": 3,
    "business level": 4,
    "native": 5,
}

# First match wins.
_JOB_PATTERNS = (
    (re.compile(r"not required|no japanese|\bnone\b"), 0),
    (re.compile(r"native|fluent|\bn1\b"), 5),
    (re.compile(r"business"), 4),
    (re.compile(r"intermediate|\bn2\b"), 3),
    (re.compile(r"conversational|daily|\bn3\b|\bn4\b|\bn5\b|basic"), 2),
)


def job_requirement_rank(level: Optional[str]) -> int:
    """Rank a scraped Japanese requirement. Unknown text counts as no stated requirement."""
    if not level or not level.strip():
        return 0
    text = level.strip().lower()
    for pattern, rank in _JOB_PATTERNS:
        if pattern.search(text):
            return rank
    return 0


def job_fits_japanese_level(job_level: Optional[str], selected: str) -> bool:
    """True when the listing does not ask for more Japanese than the user selected."""
    ceiling = _CHOICE_RANK.get(selected.strip().lower())
    if ceiling is None:
        return True
    return job_requirement_rank(job_level) <= ceiling
