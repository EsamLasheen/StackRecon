"""Shared pytest fixtures for StackRecon scanner tests."""

import io
import json
import zipfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixture: raw Chaos index entries (list of program dicts from Chaos source)
# ---------------------------------------------------------------------------

FIXTURE_CHAOS_INDEX = [
    {
        "name": "HackerOne",
        "url": "https://hackerone.com/security",
        "bounty": True,
        "swag": True,
        "domains": ["hackerone.com", "hackerone.net"],
    },
    {
        "name": "Bugcrowd",
        "url": "https://bugcrowd.com/engagements/bugcrowd",
        "bounty": True,
        "swag": False,
        "domains": ["bugcrowd.com"],
    },
    {
        "name": "OpenBugBounty",
        "url": "https://www.openbugbounty.org/",
        "bounty": False,
        "swag": False,
        "domains": ["openbugbounty.org"],
    },
]


@pytest.fixture
def fixture_chaos_index():
    """Return a list of 3 program dicts matching the Chaos index schema."""
    return FIXTURE_CHAOS_INDEX.copy()


# ---------------------------------------------------------------------------
# Fixture: ScanConfig with safe test defaults
# ---------------------------------------------------------------------------

@pytest.fixture
def fixture_config(tmp_path):
    """Return a ScanConfig suitable for tests (no real network, small limits)."""
    from scanner.src.config import ScanConfig

    return ScanConfig(
        workers=5,
        limit=3,
        connect_timeout=3,
        read_timeout=7,
        output=str(tmp_path / "data.json"),
        api_key=None,
    )


# ---------------------------------------------------------------------------
# Fixture factory: in-memory ZIP containing subdomain list
# ---------------------------------------------------------------------------

def make_zip_bytes(subdomains: list[str], filename: str = "everything.txt") -> bytes:
    """Create an in-memory ZIP archive with a single plaintext subdomain file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        content = "\n".join(subdomains) + "\n"
        zf.writestr(filename, content)
    return buf.getvalue()


@pytest.fixture
def fixture_zip_bytes():
    """Factory fixture: call with a list of subdomains to get ZIP bytes."""
    return make_zip_bytes


# ---------------------------------------------------------------------------
# Fixture: expected Program dicts (output schema)
# ---------------------------------------------------------------------------

FIXTURE_PROGRAMS = [
    {
        "name": "HackerOne",
        "url": "https://hackerone.com/security",
        "platform": "HackerOne",
        "reward_type": "paid",
        "domains": ["hackerone.com", "hackerone.net"],
        "technologies": ["Grafana"],
        "subdomain_count": 2,
        "detection_count": 1,
        "detections": [
            {
                "hostname": "grafana.hackerone.com",
                "technologies": ["Grafana"],
                "http_status": 200,
                "probe_error": None,
            }
        ],
    },
    {
        "name": "Bugcrowd",
        "url": "https://bugcrowd.com/engagements/bugcrowd",
        "platform": "Bugcrowd",
        "reward_type": "paid",
        "domains": ["bugcrowd.com"],
        "technologies": [],
        "subdomain_count": 1,
        "detection_count": 0,
        "detections": [],
    },
    {
        "name": "OpenBugBounty",
        "url": "https://www.openbugbounty.org/",
        "platform": "Other",
        "reward_type": "free",
        "domains": ["openbugbounty.org"],
        "technologies": [],
        "subdomain_count": 1,
        "detection_count": 0,
        "detections": [],
    },
]


@pytest.fixture
def fixture_programs():
    """Return list of 3 program output dicts matching data-json-contract.md."""
    return [p.copy() for p in FIXTURE_PROGRAMS]
