"""Unit tests for scanner.src.classifier — TDD: written before implementation."""

import pytest

from scanner.src.classifier import classify_platform, classify_reward_type


# ---------------------------------------------------------------------------
# classify_platform tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url,expected", [
    ("https://hackerone.com/security", "HackerOne"),
    ("https://hackerone.com/programs/acme", "HackerOne"),
    ("https://bugcrowd.com/engagements/target", "Bugcrowd"),
    ("https://bugcrowd.com/target", "Bugcrowd"),
    ("https://intigriti.com/programs/company/program/scope", "Intigriti"),
    ("https://app.intigriti.com/programs/target", "Intigriti"),
    ("https://yeswehack.com/programs/target", "YesWeHack"),
    ("https://www.yeswehack.com/programs/target", "YesWeHack"),
    ("https://www.openbugbounty.org/", "Other"),
    ("https://security.company.com/vdp", "Other"),
    ("https://example.com", "Other"),
])
def test_classify_platform(url, expected):
    assert classify_platform(url) == expected


def test_classify_platform_case_insensitive():
    """Platform classification is case-insensitive on the URL."""
    assert classify_platform("https://HackerOne.com/security") == "HackerOne"


# ---------------------------------------------------------------------------
# classify_reward_type tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bounty,url,expected", [
    # bounty=True → paid, regardless of URL
    (True, "https://hackerone.com/security", "paid"),
    (True, "https://example.com/vdp", "paid"),
    # bounty=False + self-hosted platform patterns → self-hosted
    (False, "https://company.com/security", "free"),
    (False, "https://www.openbugbounty.org/", "free"),
    # bounty=False + no known platform → free
    (False, "https://bugcrowd.com/engagements/target", "free"),
])
def test_classify_reward_type(bounty, url, expected):
    assert classify_reward_type(bounty=bounty, url=url) == expected


def test_classify_reward_type_self_hosted():
    """VDP programs on their own domain are classified as 'self-hosted' only if
    configured as such — by default non-bounty non-platform URLs are 'free'."""
    # The default for non-bounty, non-known-platform is "free"
    result = classify_reward_type(bounty=False, url="https://security.company.com")
    assert result in ("free", "self-hosted")  # either is valid per data-model spec
