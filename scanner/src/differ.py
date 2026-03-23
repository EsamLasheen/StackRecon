"""Differ — computes changes between consecutive scan runs."""

from __future__ import annotations

import json
from pathlib import Path


def compute_diff(
    previous: dict | None,
    current: dict,
) -> dict:
    """Compare two scan outputs and return what's new.

    Args:
        previous: Previous scan data dict (or None if first scan).
        current:  Current scan data dict.

    Returns:
        Dict with keys: new_programs, new_hosts, new_techs,
        removed_programs, removed_hosts, summary.
    """
    curr_programs = current.get("programs", [])

    if previous is None:
        all_programs = [p["name"] for p in curr_programs]
        all_hosts = []
        for p in curr_programs:
            for d in p.get("detections", []):
                all_hosts.append(d["hostname"])
        return {
            "new_programs": all_programs,
            "removed_programs": [],
            "new_hosts": all_hosts,
            "removed_hosts": [],
            "new_techs": [],
            "summary": {
                "new_programs": len(all_programs),
                "new_hosts": len(all_hosts),
                "new_techs": 0,
                "removed_programs": 0,
                "removed_hosts": 0,
            },
        }

    prev_programs_set = {p["name"] for p in previous.get("programs", [])}
    curr_programs_set = {p["name"] for p in curr_programs}

    new_programs = sorted(curr_programs_set - prev_programs_set)
    removed_programs = sorted(prev_programs_set - curr_programs_set)

    # Build host -> tech sets for previous and current
    prev_host_techs: dict[str, set[str]] = {}
    for p in previous.get("programs", []):
        for d in p.get("detections", []):
            h = d["hostname"]
            if h not in prev_host_techs:
                prev_host_techs[h] = set()
            prev_host_techs[h].update(d.get("technologies", []))

    curr_host_techs: dict[str, set[str]] = {}
    for p in curr_programs:
        for d in p.get("detections", []):
            h = d["hostname"]
            if h not in curr_host_techs:
                curr_host_techs[h] = set()
            curr_host_techs[h].update(d.get("technologies", []))

    new_hosts = sorted(set(curr_host_techs.keys()) - set(prev_host_techs.keys()))
    removed_hosts = sorted(set(prev_host_techs.keys()) - set(curr_host_techs.keys()))

    # New techs on existing hosts
    new_techs = []
    for h in sorted(curr_host_techs):
        if h in prev_host_techs:
            added = curr_host_techs[h] - prev_host_techs[h]
            for t in sorted(added):
                new_techs.append({"hostname": h, "tech": t})

    return {
        "new_programs": new_programs,
        "removed_programs": removed_programs,
        "new_hosts": new_hosts,
        "removed_hosts": removed_hosts,
        "new_techs": new_techs,
        "summary": {
            "new_programs": len(new_programs),
            "new_hosts": len(new_hosts),
            "new_techs": len(new_techs),
            "removed_programs": len(removed_programs),
            "removed_hosts": len(removed_hosts),
        },
    }


def load_previous_scan(path: str | Path) -> dict | None:
    """Load previous scan data from disk, or return None if not found."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
