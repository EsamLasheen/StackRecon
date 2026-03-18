"""Integration tests for the full scanner pipeline — TDD: written before implementation."""

import io
import json
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import respx
import httpx

from scanner.src.config import ScanConfig
from scanner.src.fetcher import fetch_chaos_index
from scanner.src.extractor import extract_subdomains
from scanner.src.classifier import classify_platform, classify_reward_type
from scanner.src.writer import write_atomic


CHAOS_GITHUB_URL = (
    "https://raw.githubusercontent.com/projectdiscovery/"
    "public-bugbounty-programs/main/dist/data.json"
)

SAMPLE_INDEX = [
    {
        "name": "HackerOne",
        "url": "https://hackerone.com/security",
        "bounty": True,
        "swag": True,
        "domains": ["hackerone.com"],
        "program_url": "https://chaos.example.com/programs/hackerone.zip",
    },
    {
        "name": "OpenBugBounty",
        "url": "https://www.openbugbounty.org/",
        "bounty": False,
        "swag": False,
        "domains": ["openbugbounty.org"],
        "program_url": "https://chaos.example.com/programs/openbugbounty.zip",
    },
]


def make_zip(subdomains: list[str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as zf:
        zf.writestr("everything.txt", "\n".join(subdomains) + "\n")
    return buf.getvalue()


@respx.mock
@pytest.mark.asyncio
async def test_pipeline_fetch_extract_classify(tmp_path):
    """
    End-to-end: fetch index → extract subdomains → classify programs.
    Asserts correct platform and reward_type derived from Chaos data.
    """
    respx.get(CHAOS_GITHUB_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_INDEX)
    )

    programs = await fetch_chaos_index(limit=2)
    assert len(programs) == 2

    for entry in programs:
        platform = classify_platform(entry["url"])
        reward = classify_reward_type(bounty=entry["bounty"], url=entry["url"])
        assert platform in ("HackerOne", "Bugcrowd", "Intigriti", "YesWeHack", "Other")
        assert reward in ("paid", "free", "self-hosted")

    h1 = next(p for p in programs if p["name"] == "HackerOne")
    assert classify_platform(h1["url"]) == "HackerOne"
    assert classify_reward_type(bounty=h1["bounty"], url=h1["url"]) == "paid"

    obb = next(p for p in programs if p["name"] == "OpenBugBounty")
    assert classify_platform(obb["url"]) == "Other"
    assert classify_reward_type(bounty=obb["bounty"], url=obb["url"]) == "free"


def test_extract_classify_write_full_cycle(tmp_path):
    """
    Extract subdomains from ZIP, build program dict, write atomically.
    Validates the written JSON matches the expected schema.
    """
    zip_bytes = make_zip(["grafana.hackerone.com", "api.hackerone.com"])
    subdomains = extract_subdomains(zip_bytes)
    assert len(subdomains) == 2

    platform = classify_platform("https://hackerone.com/security")
    reward = classify_reward_type(bounty=True, url="https://hackerone.com/security")

    data = {
        "meta": {
            "generated_at": "2026-03-08T12:00:00Z",
            "programs_scanned": 1,
            "programs_failed": 0,
            "total_subdomains_probed": 2,
            "total_detections": 0,
            "scanner_version": "1.0.0",
            "workers_used": 5,
        },
        "programs": [
            {
                "name": "HackerOne",
                "url": "https://hackerone.com/security",
                "platform": platform,
                "reward_type": reward,
                "domains": ["hackerone.com"],
                "technologies": [],
                "subdomain_count": len(subdomains),
                "detection_count": 0,
                "detections": [],
            }
        ],
    }

    output = tmp_path / "data.json"
    write_atomic(data, output)

    parsed = json.loads(output.read_text())
    assert parsed["programs"][0]["platform"] == "HackerOne"
    assert parsed["programs"][0]["reward_type"] == "paid"
    assert parsed["programs"][0]["subdomain_count"] == 2


@respx.mock
@pytest.mark.asyncio
async def test_pipeline_limit_respected(tmp_path):
    """With limit=1, only 1 program from the index is processed."""
    respx.get(CHAOS_GITHUB_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_INDEX)
    )
    programs = await fetch_chaos_index(limit=1)
    assert len(programs) == 1
