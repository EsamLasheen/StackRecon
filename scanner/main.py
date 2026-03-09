"""StackRecon — Bug Bounty Technology Intelligence Scanner."""

from __future__ import annotations

import asyncio
import datetime
import sys
from urllib.parse import urlparse

from scanner.src.classifier import classify_platform, classify_reward_type
from scanner.src.config import parse_cli_args
from scanner.src.detector import run_httpx_binary, run_nuclei
from scanner.src.fetcher import SourceUnavailableError, fetch_chaos_index
from scanner.src.writer import write_atomic

SCANNER_VERSION = "3.0.0"

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0, "none": -1}


def _hostnames_for_program(entry: dict) -> list[str]:
    """Build hostnames to probe from a Chaos program entry."""
    hostnames: list[str] = []
    domains = entry.get("domains", [])

    if not domains:
        url = entry.get("url", "")
        if url:
            host = urlparse(url).hostname or ""
            if host:
                domains = [host]

    prefixes = [
        # Root + common web
        "",
        "www",
        "www2",
        "web",
        "m",
        # APIs & apps
        "api",
        "api2",
        "app",
        "apps",
        "application",
        # Auth & identity
        "auth",
        "login",
        "sso",
        "oauth",
        "id",
        "identity",
        "accounts",
        "account",
        # Admin & management
        "admin",
        "administrator",
        "manage",
        "management",
        "dashboard",
        "console",
        "panel",
        "portal",
        "cp",
        "control",
        # Dev & testing environments
        "dev",
        "develop",
        "development",
        "staging",
        "stage",
        "stg",
        "test",
        "testing",
        "uat",
        "qa",
        "beta",
        "sandbox",
        "preprod",
        "demo",
        # DevOps & CI/CD
        "jenkins",
        "ci",
        "cd",
        "build",
        "deploy",
        "cicd",
        "pipeline",
        "gitlab",
        "git",
        "svn",
        "code",
        "bitbucket",
        "grafana",
        "prometheus",
        "metrics",
        "telemetry",
        "apm",
        "monitor",
        "kibana",
        "elk",
        "elastic",
        "splunk",
        "logs",
        "logging",
        # Infrastructure tools
        "jira",
        "confluence",
        "wiki",
        "docs",
        "documentation",
        "vault",
        "consul",
        "nomad",
        "rancher",
        "portainer",
        "k8s",
        "kubernetes",
        "docker",
        "harbor",
        "registry",
        "artifactory",
        "nexus",
        "sonar",
        "rabbitmq",
        "kafka",
        "queue",
        "minio",
        "storage",
        # Remote access
        "vpn",
        "remote",
        "citrix",
        "rdp",
        # Support & comms
        "support",
        "help",
        "helpdesk",
        "kb",
        "status",
        "health",
        # Email
        "mail",
        "webmail",
        "smtp",
        # Content & CDN
        "blog",
        "news",
        "media",
        "cdn",
        "static",
        "assets",
        "files",
        # Commerce
        "shop",
        "store",
        "pay",
        "payment",
        "checkout",
        # Internal
        "internal",
        "intranet",
        "corp",
        # Infra shortcuts
        "db",
        "database",
        "cache",
        "redis",
        "search",
    ]

    for domain in domains:
        domain = domain.strip().lower()
        if not domain:
            continue
        for prefix in prefixes:
            hostname = f"{prefix}.{domain}" if prefix else domain
            hostnames.append(hostname)

    return list(dict.fromkeys(hostnames))


async def run(config) -> int:
    """Main async scan pipeline."""
    print("Fetching Chaos program index…")
    try:
        index = await fetch_chaos_index(api_key=config.api_key, limit=config.limit)
    except SourceUnavailableError as exc:
        print(f"[ERROR] {exc} — aborting", file=sys.stderr)
        return 1

    total = len(index)
    print(f"Loaded {total} programs.")

    # Build per-program metadata and collect all unique hostnames
    program_meta: list[dict] = []
    all_hostnames: list[str] = []
    seen: set[str] = set()

    for entry in index:
        name = entry.get("name", "unknown")
        url = entry.get("url", "")
        bounty = entry.get("bounty", False)
        domains = entry.get("domains", [])

        if not domains and not url:
            program_meta.append(None)  # type: ignore[arg-type]
            continue

        platform = classify_platform(url)
        reward_type = classify_reward_type(bounty=bounty, url=url)
        hostnames = _hostnames_for_program(entry)

        program_meta.append(
            {
                "name": name,
                "url": url,
                "platform": platform,
                "reward_type": reward_type,
                "domains": domains,
                "hostnames": hostnames,
            }
        )

        for h in hostnames:
            if h not in seen:
                all_hostnames.append(h)
                seen.add(h)

    total_probed = len(all_hostnames)
    print(
        f"Running httpx tech-detect on {total_probed} unique hostnames "
        f"({config.workers} threads)…"
    )

    raw_detections = run_httpx_binary(
        hostnames=all_hostnames,
        threads=config.workers,
        timeout=config.connect_timeout + config.read_timeout,
    )

    detection_map: dict[str, dict] = {d["hostname"]: d for d in raw_detections}
    total_detections = len(raw_detections)
    print(f"httpx finished — {total_detections} hosts with tech detections.")

    # Run nuclei only on hosts that responded (much smaller set)
    detected_hosts = list(detection_map.keys())
    print(f"Running nuclei misconfig/exposure scan on {len(detected_hosts)} live hosts…")
    nuclei_findings = run_nuclei(
        hostnames=detected_hosts,
        concurrency=config.workers,
        rate_limit=200,
        timeout=10,
    )
    print(f"Nuclei finished — {len(nuclei_findings)} findings.")

    # Build nuclei lookup: hostname -> list of findings
    nuclei_map: dict[str, list[dict]] = {}
    for f in nuclei_findings:
        h = f["hostname"]
        if h not in nuclei_map:
            nuclei_map[h] = []
        nuclei_map[h].append(f)

    total_vuln_findings = len(nuclei_findings)

    # Assemble per-program output
    programs_out: list[dict] = []
    programs_failed = 0

    for meta in program_meta:
        if meta is None:
            programs_failed += 1
            continue

        prog_detections = [detection_map[h] for h in meta["hostnames"] if h in detection_map]

        tech_set: set[str] = set()
        for det in prog_detections:
            tech_set.update(det.get("technologies", []))

        detections_out = [
            {
                "hostname": d["hostname"],
                "technologies": d["technologies"],
                "http_status": d.get("http_status"),
                "probe_error": d.get("probe_error"),
            }
            for d in prog_detections
        ]

        # Gather nuclei findings for this program's hosts
        prog_vulns: list[dict] = []
        for h in meta["hostnames"]:
            if h in nuclei_map:
                prog_vulns.extend(nuclei_map[h])

        # Compute highest severity
        highest_severity = "none"
        if prog_vulns:
            highest_severity = max(
                prog_vulns,
                key=lambda v: SEVERITY_ORDER.get(v.get("severity", "info"), 0),
            )["severity"]

        programs_out.append(
            {
                "name": meta["name"],
                "url": meta["url"],
                "platform": meta["platform"],
                "reward_type": meta["reward_type"],
                "domains": meta["domains"],
                "technologies": sorted(tech_set),
                "subdomain_count": len(meta["hostnames"]),
                "detection_count": len(prog_detections),
                "detections": detections_out,
                "severity": highest_severity,
                "critical_count": sum(1 for v in prog_vulns if v["severity"] == "critical"),
                "high_count": sum(1 for v in prog_vulns if v["severity"] == "high"),
                "medium_count": sum(1 for v in prog_vulns if v["severity"] == "medium"),
                "vulnerabilities": prog_vulns,
            }
        )

    data = {
        "meta": {
            "generated_at": (
                datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            ),
            "programs_scanned": len(programs_out),
            "programs_failed": programs_failed,
            "total_subdomains_probed": total_probed,
            "total_detections": total_detections,
            "total_vuln_findings": total_vuln_findings,
            "scanner_version": SCANNER_VERSION,
            "workers_used": config.workers,
        },
        "programs": programs_out,
    }

    try:
        write_atomic(data, config.output)
    except OSError as exc:
        print(f"[ERROR] Failed to write output: {exc}", file=sys.stderr)
        return 3

    print(f"\nDone. {len(programs_out)} programs written to {config.output}")
    return 0


def main() -> None:
    config = parse_cli_args()
    exit_code = asyncio.run(run(config))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
