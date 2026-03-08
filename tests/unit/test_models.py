"""Unit tests for scanner data models. WRITE FIRST — must FAIL before implementation."""

import json
import pytest


def test_program_construction():
    from scanner.src.models import Program

    p = Program(
        name="HackerOne",
        url="https://hackerone.com/security",
        platform="HackerOne",
        reward_type="paid",
        domains=["hackerone.com"],
        technologies=["Grafana"],
        subdomain_count=10,
        detection_count=1,
        detections=[],
    )
    assert p.name == "HackerOne"
    assert p.platform == "HackerOne"
    assert p.reward_type == "paid"


def test_program_to_dict_keys():
    from scanner.src.models import Program

    p = Program(
        name="Test",
        url="https://example.com",
        platform="Other",
        reward_type="free",
        domains=["example.com"],
        technologies=[],
        subdomain_count=0,
        detection_count=0,
        detections=[],
    )
    d = p.to_dict()
    required_keys = {
        "name", "url", "platform", "reward_type", "domains",
        "technologies", "subdomain_count", "detection_count", "detections",
    }
    assert required_keys.issubset(d.keys())


def test_program_json_round_trip():
    from scanner.src.models import Program

    p = Program(
        name="RoundTrip",
        url="https://rt.example.com",
        platform="HackerOne",
        reward_type="paid",
        domains=["rt.example.com"],
        technologies=["Jenkins"],
        subdomain_count=5,
        detection_count=1,
        detections=[],
    )
    serialized = json.dumps(p.to_dict())
    parsed = json.loads(serialized)
    restored = Program.from_dict(parsed)
    assert restored.name == p.name
    assert restored.technologies == p.technologies


def test_subdomain_construction():
    from scanner.src.models import Subdomain

    s = Subdomain(
        hostname="api.example.com",
        technologies=["Grafana"],
        http_status=200,
        probe_error=None,
    )
    assert s.hostname == "api.example.com"
    assert s.http_status == 200
    assert s.probe_error is None


def test_subdomain_to_dict():
    from scanner.src.models import Subdomain

    s = Subdomain(
        hostname="ci.example.com",
        technologies=["Jenkins"],
        http_status=200,
        probe_error=None,
    )
    d = s.to_dict()
    assert d["hostname"] == "ci.example.com"
    assert d["technologies"] == ["Jenkins"]
    assert d["http_status"] == 200
    assert d["probe_error"] is None


def test_scan_run_to_dict():
    from scanner.src.models import ScanRun

    sr = ScanRun(
        generated_at="2026-03-08T12:00:00Z",
        programs_scanned=10,
        programs_failed=2,
        total_subdomains_probed=1000,
        total_detections=50,
        scanner_version="1.0.0",
        workers_used=50,
    )
    d = sr.to_dict()
    assert d["programs_scanned"] == 10
    assert d["scanner_version"] == "1.0.0"
    required = {
        "generated_at", "programs_scanned", "programs_failed",
        "total_subdomains_probed", "total_detections", "scanner_version", "workers_used",
    }
    assert required.issubset(d.keys())


def test_platform_values_are_strings():
    from scanner.src.models import Program

    p = Program(
        name="X",
        url="https://x.com",
        platform="HackerOne",
        reward_type="paid",
        domains=["x.com"],
        technologies=[],
        subdomain_count=0,
        detection_count=0,
        detections=[],
    )
    # platform must be a plain string (not an Enum), for JSON serialization
    assert isinstance(p.platform, str)
    assert isinstance(p.reward_type, str)
