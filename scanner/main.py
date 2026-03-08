"""StackRecon — Bug Bounty Technology Intelligence Scanner."""

from __future__ import annotations

import asyncio
import datetime
import sys
from pathlib import Path
from urllib.parse import urlparse

from scanner.src.classifier import classify_platform, classify_reward_type
from scanner.src.config import parse_cli_args
from scanner.src.detector import detect_all, load_signatures
from scanner.src.fetcher import SourceUnavailableError, fetch_chaos_index
from scanner.src.writer import write_atomic

SIGNATURES_PATH = Path(__file__).parent.parent / "signatures" / "technologies.yaml"
SCANNER_VERSION = "1.0.0"


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

    prefixes = ["", "www", "api", "app", "admin", "portal", "dev", "staging",
                "grafana", "jenkins", "gitlab", "jira", "confluence", "monitor"]

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
    try:
        signatures = load_signatures(SIGNATURES_PATH)
    except Exception as exc:
        print(f"[ERROR] Failed to load signatures: {exc}", file=sys.stderr)
        return 1

    print("Fetching Chaos program index…")
    try:
        index = await fetch_chaos_index(api_key=config.api_key, limit=config.limit)
    except SourceUnavailableError as exc:
        print(f"[ERROR] {exc} — aborting", file=sys.stderr)
        return 1

    total = len(index)
    print(f"Processing {total} programs with {config.workers} workers…")

    programs_out: list[dict] = []
    programs_failed = 0
    total_probed = 0
    total_detections = 0

    for idx, entry in enumerate(index, start=1):
        name = entry.get("name", f"program-{idx}")
        url = entry.get("url", "")
        bounty = entry.get("bounty", False)
        domains = entry.get("domains", [])

        # Skip programs with no domains and no url
        if not domains and not url:
            programs_failed += 1
            continue

        platform = classify_platform(url)
        reward_type = classify_reward_type(bounty=bounty, url=url)

        hostnames = _hostnames_for_program(entry)
        subdomain_count = len(hostnames)
        total_probed += subdomain_count

        detections = await detect_all(
            hostnames=hostnames,
            signatures=signatures,
            workers=config.workers,
            connect_timeout=config.connect_timeout,
            read_timeout=config.read_timeout,
        )

        detection_count = len(detections)
        total_detections += detection_count

        tech_set: set[str] = set()
        for det in detections:
            tech_set.update(det.get("technologies", []))

        detections_out = [
            {
                "hostname": d["hostname"],
                "technologies": d["technologies"],
                "http_status": d.get("http_status"),
                "probe_error": d.get("probe_error"),
            }
            for d in detections
        ]

        programs_out.append({
            "name": name,
            "url": url,
            "platform": platform,
            "reward_type": reward_type,
            "domains": domains,
            "technologies": sorted(tech_set),
            "subdomain_count": subdomain_count,
            "detection_count": detection_count,
            "detections": detections_out,
        })

        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        print(  # noqa: E501
            f"[{ts}] [{idx}/{total}] {name} — "
            f"{subdomain_count} probed, {detection_count} detections"
        )

    data = {
        "meta": {
            "generated_at": (
                datetime.datetime.now(datetime.timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
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
