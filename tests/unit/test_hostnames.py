"""Tests for _hostnames_for_program subdomain generation."""

from scanner.main import _hostnames_for_program


def test_minimum_prefix_count():
    """We must generate at least 70 unique prefixes."""
    entry = {"domains": ["example.com"]}
    hostnames = _hostnames_for_program(entry)
    assert len(hostnames) >= 70


def test_security_critical_prefixes_present():
    """All high-value security subdomains must be included."""
    entry = {"domains": ["example.com"]}
    hostnames = _hostnames_for_program(entry)
    must_have = [
        "example.com",
        "admin.example.com",
        "jenkins.example.com",
        "grafana.example.com",
        "sonarqube.example.com",
        "phpmyadmin.example.com",
        "elasticsearch.example.com",
        "prometheus.example.com",
        "traefik.example.com",
        "mailhog.example.com",
        "swagger.example.com",
        "debug.example.com",
        "backup.example.com",
        "internal.example.com",
        "vpn.example.com",
        "git.example.com",
        "ci.example.com",
        "cd.example.com",
        "uat.example.com",
        "sandbox.example.com",
    ]
    for h in must_have:
        assert h in hostnames, f"Missing critical prefix: {h}"


def test_deduplication():
    """Duplicate hostnames should be removed."""
    entry = {"domains": ["example.com", "example.com"]}
    hostnames = _hostnames_for_program(entry)
    assert len(hostnames) == len(set(hostnames))


def test_fallback_to_url():
    """When no domains provided, extract host from URL."""
    entry = {"url": "https://www.example.com/security"}
    hostnames = _hostnames_for_program(entry)
    assert "www.example.com" in hostnames
