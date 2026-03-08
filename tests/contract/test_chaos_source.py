"""
Contract tests for the Chaos ProjectDiscovery public GitHub source.
These tests make real network requests and are skipped in CI.

Run manually with:
    python3 -m pytest tests/contract/ -m network -v
"""

import pytest

from scanner.src.fetcher import fetch_chaos_index, SourceUnavailableError


pytestmark = pytest.mark.network


@pytest.mark.asyncio
async def test_chaos_source_reachable():
    """Chaos public GitHub source returns a non-empty list of programs."""
    programs = await fetch_chaos_index(limit=5)
    assert isinstance(programs, list)
    assert len(programs) > 0


@pytest.mark.asyncio
async def test_chaos_index_entry_schema():
    """Each entry from Chaos source has required fields: name, url, bounty, domains."""
    programs = await fetch_chaos_index(limit=10)
    required_keys = {"name", "url", "bounty", "domains"}
    for entry in programs:
        missing = required_keys - set(entry.keys())
        assert not missing, f"Entry missing keys: {missing}. Entry: {entry}"


@pytest.mark.asyncio
async def test_chaos_index_has_many_programs():
    """Chaos source should contain at least 100 programs for a meaningful scan."""
    programs = await fetch_chaos_index()
    assert len(programs) >= 100, f"Expected ≥100 programs, got {len(programs)}"
