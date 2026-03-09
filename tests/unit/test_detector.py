"""Unit tests for scanner.src.detector — TDD: written before implementation."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import respx
import httpx

from scanner.src.detector import (
    load_signatures,
    detect_offline,
    probe_subdomain,
    detect_all,
    run_httpx_binary,
    run_nuclei,
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


# ---------------------------------------------------------------------------
# run_httpx_binary tests
# ---------------------------------------------------------------------------

def _make_httpx_line(host, techs):
    return json.dumps({"input": host, "tech": techs, "status-code": 200})


def test_run_httpx_binary_empty_returns_empty():
    """Empty hostname list returns empty list without calling subprocess."""
    result = run_httpx_binary([])
    assert result == []


def test_run_httpx_binary_parses_output():
    """Parses httpx JSON output and strips version numbers."""
    mock_result = MagicMock()
    mock_result.stdout = "\n".join([
        _make_httpx_line("grafana.example.com", ["Grafana:9.0", "Nginx:1.18"]),
        _make_httpx_line("api.example.com", ["Django:4.2"]),
        "",  # blank line should be skipped
    ])
    with patch("scanner.src.detector.subprocess.run", return_value=mock_result):
        results = run_httpx_binary(["grafana.example.com", "api.example.com"])

    assert len(results) == 2
    grafana = next(r for r in results if r["hostname"] == "grafana.example.com")
    assert "Grafana" in grafana["technologies"]
    assert "Nginx" in grafana["technologies"]
    # Version stripped
    assert not any(":" in t for t in grafana["technologies"])


def test_run_httpx_binary_skips_no_tech_lines():
    """Hosts with empty tech list are excluded from results."""
    mock_result = MagicMock()
    mock_result.stdout = json.dumps({"input": "plain.example.com", "tech": [], "status-code": 200})
    with patch("scanner.src.detector.subprocess.run", return_value=mock_result):
        results = run_httpx_binary(["plain.example.com"])
    assert results == []


def test_run_httpx_binary_skips_invalid_json():
    """Lines that are not valid JSON are silently skipped."""
    mock_result = MagicMock()
    mock_result.stdout = "not json\n" + _make_httpx_line("ok.example.com", ["Nginx"])
    with patch("scanner.src.detector.subprocess.run", return_value=mock_result):
        results = run_httpx_binary(["ok.example.com"])
    assert len(results) == 1
    assert results[0]["hostname"] == "ok.example.com"


# ---------------------------------------------------------------------------
# run_nuclei tests
# ---------------------------------------------------------------------------

def _make_nuclei_line(host, template_id, name, severity, matched_at=""):
    return json.dumps({
        "host": host,
        "template-id": template_id,
        "info": {"name": name, "severity": severity, "description": ""},
        "matched-at": matched_at or host,
    })


def test_run_nuclei_empty_returns_empty():
    """Empty hostname list returns empty without subprocess call."""
    result = run_nuclei([])
    assert result == []


def test_run_nuclei_parses_findings():
    """Parses nuclei JSON output into structured finding dicts."""
    mock_result = MagicMock()
    mock_result.stdout = "\n".join([
        _make_nuclei_line("http://grafana.example.com", "grafana-default-login",
                          "Grafana Default Login", "high", "http://grafana.example.com/login"),
        _make_nuclei_line("http://jenkins.example.com", "jenkins-unauth",
                          "Jenkins Unauthenticated Access", "critical"),
    ])
    with patch("scanner.src.detector.subprocess.run", return_value=mock_result):
        findings = run_nuclei(["grafana.example.com", "jenkins.example.com"])

    assert len(findings) == 2
    severities = {f["severity"] for f in findings}
    assert "high" in severities
    assert "critical" in severities


def test_run_nuclei_strips_scheme_from_hostname():
    """Hostname in finding has scheme stripped."""
    mock_result = MagicMock()
    mock_result.stdout = _make_nuclei_line(
        "http://admin.example.com", "exposed-panel", "Exposed Panel", "medium"
    )
    with patch("scanner.src.detector.subprocess.run", return_value=mock_result):
        findings = run_nuclei(["admin.example.com"])

    assert findings[0]["hostname"] == "admin.example.com"


def test_run_nuclei_skips_invalid_json():
    """Invalid JSON lines are silently ignored."""
    mock_result = MagicMock()
    mock_result.stdout = "bad line\n" + _make_nuclei_line(
        "http://ok.example.com", "test-id", "Test", "medium"
    )
    with patch("scanner.src.detector.subprocess.run", return_value=mock_result):
        findings = run_nuclei(["ok.example.com"])
    assert len(findings) == 1
