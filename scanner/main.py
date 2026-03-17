"""StackRecon — Bug Bounty Technology Intelligence Scanner."""

from __future__ import annotations

import asyncio
import datetime
import sys
from urllib.parse import urlparse

from scanner.src.classifier import classify_platform, classify_reward_type
from scanner.src.config import parse_cli_args
from scanner.src.detector import run_httpx_binary, run_nuclei, run_nuclei_info
from scanner.src.fetcher import SourceUnavailableError, fetch_chaos_index
from scanner.src.writer import write_atomic

SCANNER_VERSION = "4.0.0"

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0, "none": -1}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _write_progress(path: str | None, payload: dict) -> None:
    """Write progress.json atomically; silently ignore failures."""
    if not path:
        return
    payload["updated_at"] = _now()
    try:
        write_atomic(payload, path)
    except Exception:
        pass


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

    # Focused on subdomains most likely to expose security-relevant services.
    # Deliberately concise — 800+ programs × many domains × prefixes = huge scan.
    prefixes = [
        # Root + common web
        "",
        "www",
        "api",
        "app",
        # Auth & admin (highest nuclei hit rate)
        "admin",
        "portal",
        "auth",
        "sso",
        "login",
        # Environments often misconfigured
        "dev",
        "staging",
        "test",
        "beta",
        # DevOps tools — primary targets for misconfigs
        "jenkins",
        "gitlab",
        "grafana",
        "kibana",
        "jira",
        "confluence",
        "vault",
        "monitor",
        # Infrastructure
        "k8s",
        "docker",
        "registry",
        "status",
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
    started_at = _now()
    progress_path = config.progress

    _write_progress(progress_path, {
        "status": "scanning",
        "phase": "chaos",
        "phase_label": "Fetching bug bounty program index…",
        "phase_number": 1,
        "total_phases": 4,
        "started_at": started_at,
        "programs_loaded": 0,
        "hostnames_total": 0,
        "detections_so_far": 0,
        "vuln_findings": 0,
    })

    print("Fetching Chaos program index…")
    try:
        index = await fetch_chaos_index(api_key=config.api_key, limit=config.limit)
    except SourceUnavailableError as exc:
        print(f"[ERROR] {exc} — aborting", file=sys.stderr)
        _write_progress(progress_path, {
            "status": "error",
            "phase": "chaos",
            "phase_label": f"Failed to fetch program index: {exc}",
            "phase_number": 1,
            "total_phases": 4,
            "started_at": started_at,
            "programs_loaded": 0,
            "hostnames_total": 0,
            "detections_so_far": 0,
            "vuln_findings": 0,
        })
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

    _write_progress(progress_path, {
        "status": "scanning",
        "phase": "httpx",
        "phase_label": f"Tech detection — probing {total_probed:,} subdomains",
        "phase_number": 2,
        "total_phases": 4,
        "started_at": started_at,
        "programs_loaded": total,
        "hostnames_total": total_probed,
        "detections_so_far": 0,
        "vuln_findings": 0,
    })

    raw_detections = run_httpx_binary(
        hostnames=all_hostnames,
        threads=config.workers,
        timeout=config.connect_timeout + config.read_timeout,
    )

    detection_map: dict[str, dict] = {d["hostname"]: d for d in raw_detections}
    total_detections = len(raw_detections)
    print(f"httpx finished — {total_detections} hosts with tech detections.")

    # Run nuclei on hosts that responded (much smaller set)
    detected_hosts = list(detection_map.keys())

    # 1) Vuln scan — real reportable bugs (private only)
    print(f"Running nuclei vuln scan on {len(detected_hosts)} live hosts…")

    _write_progress(progress_path, {
        "status": "scanning",
        "phase": "nuclei_vuln",
        "phase_label": f"Vulnerability scan — {len(detected_hosts):,} live hosts",
        "phase_number": 3,
        "total_phases": 4,
        "started_at": started_at,
        "programs_loaded": total,
        "hostnames_total": total_probed,
        "detections_so_far": total_detections,
        "vuln_findings": 0,
    })

    nuclei_findings = run_nuclei(
        hostnames=detected_hosts,
        concurrency=config.workers,
        rate_limit=200,
        timeout=10,
        templates_path=config.templates,
    )
    print(f"Nuclei vulns — {len(nuclei_findings)} findings.")

    # 2) Info scan — WAF/tech/cloud detection (public site)
    print(f"Running nuclei info scan on {len(detected_hosts)} live hosts…")

    _write_progress(progress_path, {
        "status": "scanning",
        "phase": "nuclei_info",
        "phase_label": "Info scan — WAF & tech fingerprinting",
        "phase_number": 4,
        "total_phases": 4,
        "started_at": started_at,
        "programs_loaded": total,
        "hostnames_total": total_probed,
        "detections_so_far": total_detections,
        "vuln_findings": len(nuclei_findings),
    })

    nuclei_info = run_nuclei_info(
        hostnames=detected_hosts,
        concurrency=config.workers,
        rate_limit=200,
        timeout=10,
    )
    print(f"Nuclei info — {len(nuclei_info)} detections.")

    # Build nuclei lookups: hostname -> list of findings
    nuclei_map: dict[str, list[dict]] = {}
    for f in nuclei_findings:
        h = f["hostname"]
        if h not in nuclei_map:
            nuclei_map[h] = []
        nuclei_map[h].append(f)

    nuclei_info_map: dict[str, list[dict]] = {}
    for f in nuclei_info:
        h = f["hostname"]
        if h not in nuclei_info_map:
            nuclei_info_map[h] = []
        nuclei_info_map[h].append(f)

    total_vuln_findings = len(nuclei_findings)
    total_info_findings = len(nuclei_info)

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

        # Gather nuclei vuln findings (private — reportable bugs)
        prog_vulns: list[dict] = []
        for h in meta["hostnames"]:
            if h in nuclei_map:
                prog_vulns.extend(nuclei_map[h])

        # Gather nuclei info findings (public — WAF/tech/cloud detection)
        prog_info: list[dict] = []
        for h in meta["hostnames"]:
            if h in nuclei_info_map:
                prog_info.extend(nuclei_info_map[h])

        # Compute highest severity from vuln findings
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
                "low_count": sum(1 for v in prog_vulns if v["severity"] == "low"),
                "info_count": len(prog_info),
                "vulnerabilities": prog_vulns,
                "info_findings": prog_info,
            }
        )

    generated_at = _now()
    data = {
        "meta": {
            "generated_at": generated_at,
            "programs_scanned": len(programs_out),
            "programs_failed": programs_failed,
            "total_subdomains_probed": total_probed,
            "total_detections": total_detections,
            "total_vuln_findings": total_vuln_findings,
            "total_info_findings": total_info_findings,
            "scanner_version": SCANNER_VERSION,
            "workers_used": config.workers,
        },
        "programs": programs_out,
    }

    # Write full private report (includes matched_at URLs, vuln details)
    private_path = config.output.replace(".json", "-full.json")
    try:
        write_atomic(data, private_path)
        print(f"Full report (private): {private_path}")
    except OSError as exc:
        print(f"[WARN] Failed to write private report: {exc}", file=sys.stderr)

    # Strip vuln details for public data.json — keep info findings (safe)
    for prog in programs_out:
        prog.pop("vulnerabilities", None)
        # Keep info_findings (WAF/tech detection — safe to show publicly)
        # Keep severity + counts (safe aggregate stats)

    try:
        write_atomic(data, config.output)
    except OSError as exc:
        print(f"[ERROR] Failed to write output: {exc}", file=sys.stderr)
        return 3

    # Mark scan complete in progress.json
    _write_progress(progress_path, {
        "status": "idle",
        "phase": "done",
        "phase_label": "Scan complete",
        "phase_number": 4,
        "total_phases": 4,
        "started_at": started_at,
        "last_scan": generated_at,
        "programs_loaded": total,
        "hostnames_total": total_probed,
        "detections_so_far": total_detections,
        "vuln_findings": total_vuln_findings,
    })

    print(f"Public report: {config.output}")
    print(f"\nDone. {len(programs_out)} programs written.")
    return 0


def main() -> None:
    config = parse_cli_args()
    exit_code = asyncio.run(run(config))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
