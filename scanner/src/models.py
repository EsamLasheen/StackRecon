"""Data models for StackRecon scanner output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Subdomain:
    """A single hostname with detected technologies."""

    hostname: str
    technologies: list[str]
    http_status: int | None
    probe_error: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "hostname": self.hostname,
            "technologies": self.technologies,
            "http_status": self.http_status,
            "probe_error": self.probe_error,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Subdomain:
        return cls(
            hostname=d["hostname"],
            technologies=d["technologies"],
            http_status=d.get("http_status"),
            probe_error=d.get("probe_error"),
        )


@dataclass
class Program:
    """A single bug bounty program with scan results."""

    name: str
    url: str
    platform: str  # "HackerOne"|"Bugcrowd"|"Intigriti"|"YesWeHack"|"Other"
    reward_type: str  # "paid"|"free"|"self-hosted"
    domains: list[str]
    technologies: list[str]
    subdomain_count: int
    detection_count: int
    detections: list[Subdomain]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "platform": self.platform,
            "reward_type": self.reward_type,
            "domains": self.domains,
            "technologies": self.technologies,
            "subdomain_count": self.subdomain_count,
            "detection_count": self.detection_count,
            "detections": [s.to_dict() for s in self.detections],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Program:
        return cls(
            name=d["name"],
            url=d["url"],
            platform=d["platform"],
            reward_type=d["reward_type"],
            domains=d["domains"],
            technologies=d["technologies"],
            subdomain_count=d["subdomain_count"],
            detection_count=d["detection_count"],
            detections=[Subdomain.from_dict(s) for s in d.get("detections", [])],
        )


@dataclass
class ScanRun:
    """Metadata for a completed scan run (embedded in output JSON under 'meta')."""

    generated_at: str
    programs_scanned: int
    programs_failed: int
    total_subdomains_probed: int
    total_detections: int
    scanner_version: str
    workers_used: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "programs_scanned": self.programs_scanned,
            "programs_failed": self.programs_failed,
            "total_subdomains_probed": self.total_subdomains_probed,
            "total_detections": self.total_detections,
            "scanner_version": self.scanner_version,
            "workers_used": self.workers_used,
        }
