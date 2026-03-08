"""Classifier — derives platform and reward_type from Chaos program metadata."""

from __future__ import annotations

import re

_PLATFORM_PATTERNS: list[tuple[str, str]] = [
    (r"hackerone\.com", "HackerOne"),
    (r"bugcrowd\.com", "Bugcrowd"),
    (r"intigriti\.com", "Intigriti"),
    (r"yeswehack\.com", "YesWeHack"),
]


def classify_platform(url: str) -> str:
    """Derive the bug bounty platform from the program URL.

    Args:
        url: The program URL from the Chaos index.

    Returns:
        One of: "HackerOne", "Bugcrowd", "Intigriti", "YesWeHack", "Other".
    """
    url_lower = url.lower()
    for pattern, platform in _PLATFORM_PATTERNS:
        if re.search(pattern, url_lower):
            return platform
    return "Other"


def classify_reward_type(bounty: bool, url: str) -> str:
    """Derive reward type from the program's bounty flag and URL.

    Derivation rules (in priority order per data-model.md):
      1. bounty=True  → "paid"
      2. bounty=False → "free"  (self-hosted classification deferred to future enhancement)

    Args:
        bounty: Whether the program offers monetary rewards.
        url:    The program URL (reserved for future self-hosted detection).

    Returns:
        One of: "paid", "free", "self-hosted".
    """
    if bounty:
        return "paid"
    return "free"
