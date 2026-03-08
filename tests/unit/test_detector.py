"""Unit tests for scanner.src.detector — TDD: written before implementation."""

from pathlib import Path

import pytest
import respx
import httpx

from scanner.src.detector import (
    load_signatures,
    detect_offline,
    probe_subdomain,
    detect_all,
)


SIGNATURES_PATH = Path(__file__).parent.parent.parent / "signatures" / "technologies.yaml"


# ---------------------------------------------------------------------------
# load_signatures tests
# ---------------------------------------------------------------------------

def test_load_signatures_returns_list():
    """load_signatures returns a non-empty list of signature dicts."""
    sigs = load_signatures(SIGNATURES_PATH)
    assert isinstance(sigs, list)
    assert len(sigs) > 0


def test_load_signatures_each_has_name():
    """Every signature entry has a non-empty 'name' key."""
    sigs = load_signatures(SIGNATURES_PATH)
    for sig in sigs:
        assert "name" in sig
        assert isinstance(sig["name"], str)
        assert sig["name"]


def test_load_signatures_has_grafana():
    """Grafana must be present in signatures (required by spec)."""
    sigs = load_signatures(SIGNATURES_PATH)
    names = {s["name"] for s in sigs}
    assert "Grafana" in names


def test_load_signatures_at_least_47():
    """Spec requires ≥47 technology signatures."""
    sigs = load_signatures(SIGNATURES_PATH)
    assert len(sigs) >= 47


# ---------------------------------------------------------------------------
# detect_offline tests
# ---------------------------------------------------------------------------

MINIMAL_SIGNATURES = [
    {
        "name": "Grafana",
        "live_probe_required": False,
        "signals": {
            "headers": {"X-Grafana-Id": ".*"},
            "html": ["<title>Grafana</title>"],
            "paths": [],
        },
    },
    {
        "name": "Jenkins",
        "live_probe_required": False,
        "signals": {
            "headers": {},
            "html": ["<title>Dashboard [Jenkins]</title>"],
            "paths": [],
        },
    },
]


def test_detect_offline_matches_html_pattern():
    """HTML pattern match returns technology name."""
    headers = {}
    body = "<html><head><title>Grafana</title></head></html>"
    result = detect_offline(headers=headers, body=body, signatures=MINIMAL_SIGNATURES)
    assert "Grafana" in result


def test_detect_offline_matches_header():
    """Header match returns technology name."""
    headers = {"x-grafana-id": "12345"}
    body = ""
    result = detect_offline(headers=headers, body=body, signatures=MINIMAL_SIGNATURES)
    assert "Grafana" in result


def test_detect_offline_no_match_returns_empty():
    """No matching signals returns empty list."""
    headers = {}
    body = "<html><body>Hello world</body></html>"
    result = detect_offline(headers=headers, body=body, signatures=MINIMAL_SIGNATURES)
    assert result == []


def test_detect_offline_multiple_matches():
    """Multiple signatures can match a single response."""
    headers = {"x-grafana-id": "12345"}
    body = "<title>Dashboard [Jenkins]</title>"
    result = detect_offline(headers=headers, body=body, signatures=MINIMAL_SIGNATURES)
    assert "Grafana" in result
    assert "Jenkins" in result


# ---------------------------------------------------------------------------
# probe_subdomain tests
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_probe_subdomain_returns_detection_on_match():
    """Successful probe with matching signature returns detection dict."""
    sigs = [
        {
            "name": "Grafana",
            "live_probe_required": True,
            "signals": {
                "headers": {"X-Grafana-Id": ".*"},
                "html": [],
                "paths": [],
            },
        }
    ]
    url = "http://grafana.example.com"
    respx.get(url).mock(return_value=httpx.Response(
        200,
        headers={"x-grafana-id": "123"},
        text="<html></html>",
    ))
    result = await probe_subdomain(
        hostname="grafana.example.com",
        signatures=sigs,
        connect_timeout=3,
        read_timeout=7,
    )
    assert result["hostname"] == "grafana.example.com"
    assert "Grafana" in result["technologies"]
    assert result["http_status"] == 200
    assert result["probe_error"] is None


@respx.mock
@pytest.mark.asyncio
async def test_probe_subdomain_timeout_returns_error_record():
    """Timeout returns record with probe_error='timeout' and empty technologies."""
    sigs = []
    url = "http://slow.example.com"
    respx.get(url).mock(side_effect=httpx.TimeoutException("timed out"))
    result = await probe_subdomain(
        hostname="slow.example.com",
        signatures=sigs,
        connect_timeout=3,
        read_timeout=7,
    )
    assert result["probe_error"] == "timeout"
    assert result["technologies"] == []


@respx.mock
@pytest.mark.asyncio
async def test_probe_subdomain_no_match_returns_none():
    """Response with no matching signatures returns None (subdomain omitted)."""
    sigs = [
        {
            "name": "Grafana",
            "live_probe_required": True,
            "signals": {"headers": {"X-Grafana-Id": ".*"}, "html": [], "paths": []},
        }
    ]
    url = "http://plain.example.com"
    respx.get(url).mock(return_value=httpx.Response(200, text="<html>Nothing</html>"))
    result = await probe_subdomain(
        hostname="plain.example.com",
        signatures=sigs,
        connect_timeout=3,
        read_timeout=7,
    )
    assert result is None


# ---------------------------------------------------------------------------
# detect_all tests
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_detect_all_returns_only_detected_subdomains():
    """detect_all only returns subdomains with at least one detection."""
    sigs = [
        {
            "name": "Grafana",
            "live_probe_required": True,
            "signals": {"headers": {"X-Grafana-Id": ".*"}, "html": [], "paths": []},
        }
    ]
    hostnames = ["grafana.example.com", "plain.example.com"]
    respx.get("http://grafana.example.com").mock(
        return_value=httpx.Response(200, headers={"x-grafana-id": "1"}, text="")
    )
    respx.get("http://plain.example.com").mock(
        return_value=httpx.Response(200, text="<html>nothing</html>")
    )
    results = await detect_all(
        hostnames=hostnames,
        signatures=sigs,
        workers=2,
        connect_timeout=3,
        read_timeout=7,
    )
    assert len(results) == 1
    assert results[0]["hostname"] == "grafana.example.com"
