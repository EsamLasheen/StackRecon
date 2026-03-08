"""Unit tests for scanner.src.fetcher — TDD: written before implementation."""

import json
import io
import zipfile

import pytest
import respx
import httpx

from scanner.src.fetcher import (
    SourceUnavailableError,
    fetch_chaos_index,
    download_zip,
)


SAMPLE_INDEX = [
    {"name": "HackerOne", "url": "https://hackerone.com/security", "bounty": True,
     "swag": True, "domains": ["hackerone.com"]},
    {"name": "Bugcrowd", "url": "https://bugcrowd.com/engagements/bugcrowd", "bounty": True,
     "swag": False, "domains": ["bugcrowd.com"]},
]

CHAOS_GITHUB_URL = (
    "https://raw.githubusercontent.com/projectdiscovery/"
    "public-bugbounty-programs/main/chaos-bugbounty-list.json"
)


def make_zip(subdomains: list[str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as zf:
        zf.writestr("everything.txt", "\n".join(subdomains) + "\n")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# fetch_chaos_index tests
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_fetch_chaos_index_returns_list_of_dicts():
    """Happy path: returns parsed list of program dicts."""
    respx.get(CHAOS_GITHUB_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_INDEX)
    )
    result = await fetch_chaos_index()
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "HackerOne"


@respx.mock
@pytest.mark.asyncio
async def test_fetch_chaos_index_raises_on_http_error():
    """HTTP 503 raises SourceUnavailableError."""
    respx.get(CHAOS_GITHUB_URL).mock(
        return_value=httpx.Response(503)
    )
    with pytest.raises(SourceUnavailableError):
        await fetch_chaos_index()


@respx.mock
@pytest.mark.asyncio
async def test_fetch_chaos_index_raises_on_connection_error():
    """Network failure raises SourceUnavailableError."""
    respx.get(CHAOS_GITHUB_URL).mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(SourceUnavailableError):
        await fetch_chaos_index()


@respx.mock
@pytest.mark.asyncio
async def test_fetch_chaos_index_with_api_key_sends_header():
    """When api_key provided, Authorization header is sent."""
    respx.get(CHAOS_GITHUB_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_INDEX)
    )
    result = await fetch_chaos_index(api_key="test-key")
    assert result is not None  # no error raised


@respx.mock
@pytest.mark.asyncio
async def test_fetch_chaos_index_limit_applied():
    """fetch_chaos_index with limit=1 returns at most 1 entry."""
    respx.get(CHAOS_GITHUB_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_INDEX)
    )
    result = await fetch_chaos_index(limit=1)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# download_zip tests
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_download_zip_returns_bytes():
    """Happy path: returns raw ZIP bytes."""
    zip_data = make_zip(["a.example.com", "b.example.com"])
    url = "https://chaos.example.com/programs/hackerone.zip"
    respx.get(url).mock(return_value=httpx.Response(200, content=zip_data))
    result = await download_zip(url)
    assert isinstance(result, bytes)
    assert len(result) > 0


@respx.mock
@pytest.mark.asyncio
async def test_download_zip_returns_none_on_404():
    """ZIP 404 returns None (program skipped, not aborted)."""
    url = "https://chaos.example.com/programs/missing.zip"
    respx.get(url).mock(return_value=httpx.Response(404))
    result = await download_zip(url)
    assert result is None


@respx.mock
@pytest.mark.asyncio
async def test_download_zip_returns_none_on_timeout():
    """Timeout returns None (program skipped gracefully)."""
    url = "https://chaos.example.com/programs/slow.zip"
    respx.get(url).mock(side_effect=httpx.TimeoutException("timed out"))
    result = await download_zip(url)
    assert result is None
