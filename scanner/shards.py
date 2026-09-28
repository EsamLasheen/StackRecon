"""Freeze the complete program index and publish only complete shard sets."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
from pathlib import Path

from scanner.main import SEVERITY_ORDER, _hostnames_for_program, _now
from scanner.src.differ import compute_diff, load_previous_scan
from scanner.src.fetcher import fetch_chaos_index
from scanner.src.writer import write_atomic


def index_hosts(index: list[dict]) -> list[str]:
    if not index:
        raise ValueError("Empty program index")
    hosts: dict[str, None] = {}
    for entry in index:
        program_hosts = _hostnames_for_program(entry)
        if not program_hosts:
            raise ValueError(f"Program has no scannable hostnames: {entry.get('name')}")
        hosts.update(dict.fromkeys(program_hosts))
    return list(hosts)


def merge_reports(index_path: Path, reports: list[dict], count: int) -> dict:
    """Validate coverage before merging; no partial report can pass this gate."""
    index_bytes = index_path.read_bytes()
    index = json.loads(index_bytes)
    hosts = index_hosts(index)
    digest = hashlib.sha256(index_bytes).hexdigest()
    if count < 1 or len(reports) != count:
        raise ValueError("Missing or extra shard reports")
    by_id = {}
    identities = [(p.get("name", "unknown"), p.get("url", ""), p.get("domains", [])) for p in index]
    for report in reports:
        meta = report["meta"]
        shard = meta.get("shard", {})
        shard_id = shard.get("index")
        if (
            type(shard_id) is not int
            or not 0 <= shard_id < count
            or shard_id in by_id
            or shard.get("count") != count
            or shard.get("index_sha256") != digest
            or shard.get("complete") is not True
            or meta.get("programs_failed") != 0
            or meta.get("programs_scanned") != len(index)
        ):
            raise ValueError("Incomplete, duplicate, or incompatible shard")
        assigned = set(hosts[shard_id::count])
        if meta["total_subdomains_probed"] != len(assigned):
            raise ValueError("Shard hostname coverage mismatch")
        programs = report["programs"]
        if [(p["name"], p["url"], p["domains"]) for p in programs] != identities:
            raise ValueError("Shard program coverage mismatch")
        for program, entry in zip(programs, index):
            if program["subdomain_count"] != len(_hostnames_for_program(entry)):
                raise ValueError("Shard program hostname count mismatch")
            for key in ("detections", "vulnerabilities", "info_findings"):
                if any(item["hostname"] not in assigned for item in program[key]):
                    raise ValueError("Shard contains a result assigned to another shard")
        by_id[shard_id] = report

    ordered = [by_id[i] for i in range(count)]
    merged = copy.deepcopy(ordered[0])
    for i, program in enumerate(merged["programs"]):
        parts = [report["programs"][i] for report in ordered]
        program["technologies"] = sorted({t for p in parts for t in p["technologies"]})
        for key in ("detections", "vulnerabilities", "info_findings"):
            program[key] = [item for p in parts for item in p[key]]
        for key in (
            "detection_count",
            "critical_count",
            "high_count",
            "medium_count",
            "low_count",
            "info_count",
        ):
            program[key] = sum(p[key] for p in parts)
        program["severity"] = max((p["severity"] for p in parts), key=SEVERITY_ORDER.__getitem__)
    for key in (
        "total_subdomains_probed",
        "total_detections",
        "total_vuln_findings",
        "total_info_findings",
    ):
        merged["meta"][key] = sum(r["meta"][key] for r in ordered)
    merged["meta"].pop("shard")
    merged["meta"]["shards_completed"] = count
    merged["meta"]["index_sha256"] = digest
    merged["meta"]["generated_at"] = _now()
    merged["meta"]["started_at"] = min(r["meta"]["shard"]["started_at"] for r in ordered)
    return merged


def publish(index_path: Path, directory: Path, count: int, output: Path, progress: Path) -> None:
    reports = [json.loads(p.read_text()) for p in sorted(directory.glob("*/data-full.json"))]
    merged = merge_reports(index_path, reports, count)
    diff = compute_diff(load_previous_scan(output), merged)
    merged["diff"] = diff
    merged["meta"]["diff"] = diff["summary"]
    # Preserve the full report separately; commit only the existing public schema.
    write_atomic(merged, output.with_name(output.stem + "-full.json"))
    for program in merged["programs"]:
        program.pop("vulnerabilities")
    write_atomic(merged, output)
    meta = merged["meta"]
    write_atomic(
        {
            "status": "idle",
            "phase": "done",
            "phase_label": "Scan complete",
            "phase_number": 4,
            "total_phases": 4,
            "started_at": meta["started_at"],
            "updated_at": meta["generated_at"],
            "last_scan": meta["generated_at"],
            "programs_loaded": meta["programs_scanned"],
            "hostnames_total": meta["total_subdomains_probed"],
            "detections_so_far": meta["total_detections"],
            "vuln_findings": meta["total_vuln_findings"],
        },
        progress,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--index", type=Path, required=True)
    merge = sub.add_parser("merge")
    merge.add_argument("--index", type=Path, required=True)
    merge.add_argument("--count", type=int, required=True)
    merge.add_argument("--directory", type=Path, required=True)
    merge.add_argument("--output", type=Path, required=True)
    merge.add_argument("--progress", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        index = asyncio.run(fetch_chaos_index())
        hosts = index_hosts(index)
        write_atomic(index, args.index)
        print(f"Frozen index: {len(index)} programs, {len(hosts)} unique hostnames")
    else:
        publish(args.index, args.directory, args.count, args.output, args.progress)


if __name__ == "__main__":
    main()
