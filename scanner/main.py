"""StackRecon — Bug Bounty Technology Intelligence Scanner."""

from __future__ import annotations

import asyncio
import datetime
import sys
from urllib.parse import urlparse

from scanner.src.classifier import classify_platform, classify_reward_type
from scanner.src.config import parse_cli_args
from scanner.src.detector import run_httpx_binary
from scanner.src.fetcher import SourceUnavailableError, fetch_chaos_index
from scanner.src.writer import write_atomic

SCANNER_VERSION = "2.0.0"


def _hostnames_for_program(entry: dict) -> list[str]:
    """Build a list of hostnames to probe from a Chaos program entry.

    Tries domains list first; falls back to parsing the program URL host.
    Generates common subdomain prefixes for each root domain.
    """
    hostnames: list[str] = []
    domains = entry.get("domains", [])

    # If no domains, extract from url
    if not domains:
        url = entry.get("url", "")
        if url:
            host = urlparse(url).hostname or ""
            if host:
                domains = [host]

    prefixes = [
        "",
        "www",
        "api",
        "app",
        "admin",
        "portal",
        "dev",
        "staging",
        "grafana",
        "jenkins",
        "gitlab",
        "jira",
        "confluence",
        "monitor",
    ]

    for domain in domains:
        domain = domain.strip().lower()
        if not domain:
            continue
        for prefix in prefixes:
            hostname = f"{prefix}.{domain}" if prefix else domain
            hostnames.append(hostname)

    return list(dict.fromkeys(hostnames))  # deduplicate, preserve order


async def run(config) -> int:
    """Main async scan pipeline.

    Returns:
        Exit code: 0=success, 1=source unavailable, 3=disk error.
    """
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

    # Build hostname → detection lookup
    detection_map: dict[str, dict] = {d["hostname"]: d for d in raw_detections}
    total_detections = len(raw_detections)

    print(f"httpx finished — {total_detections} hosts with detections.")

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
