"""StackRecon — Bug Bounty Technology Intelligence Scanner."""

from __future__ import annotations

import asyncio
import datetime
import sys
from pathlib import Path

from scanner.src.classifier import classify_platform, classify_reward_type
from scanner.src.config import parse_cli_args
from scanner.src.detector import detect_all, load_signatures
from scanner.src.extractor import extract_subdomains
from scanner.src.fetcher import SourceUnavailableError, download_zip, fetch_chaos_index
from scanner.src.writer import write_atomic

SIGNATURES_PATH = Path(__file__).parent.parent / "signatures" / "technologies.yaml"
SCANNER_VERSION = "1.0.0"


async def run(config) -> int:
    """Main async scan pipeline.

    Returns:
        Exit code: 0=success, 1=source unavailable, 3=disk error.
    """
    # Load signatures once
    try:
        signatures = load_signatures(SIGNATURES_PATH)
    except Exception as exc:
        print(f"[ERROR] Failed to load signatures: {exc}", file=sys.stderr)
        return 1

    # Fetch Chaos index
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
        zip_url = entry.get("program_url", "")

        platform = classify_platform(url)
        reward_type = classify_reward_type(bounty=bounty, url=url)

        # Download ZIP
        zip_bytes: bytes | None = None
        if zip_url:
            zip_bytes = await download_zip(zip_url)
        if zip_bytes is None:
            print(f"[WARN] {name}: ZIP unavailable — skipping", file=sys.stderr)
            programs_failed += 1
            continue

        # Extract subdomains
        subdomains = extract_subdomains(zip_bytes)
        subdomain_count = len(subdomains)
        total_probed += subdomain_count

        # Detect technologies
        detections = await detect_all(
            hostnames=subdomains,
            signatures=signatures,
            workers=config.workers,
            connect_timeout=config.connect_timeout,
            read_timeout=config.read_timeout,
        )

        detection_count = len(detections)
        total_detections += detection_count

        # Aggregate technology names
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
        print(f"[{ts}] [{idx}/{total}] {name} — {subdomain_count} subdomains, {detection_count} detections")  # noqa: E501

    # Build output
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
