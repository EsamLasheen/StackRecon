"""CLI argument parsing and ScanConfig for StackRecon scanner."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass
class ScanConfig:
    """Runtime configuration derived from CLI arguments."""

    workers: int = 50
    limit: int | None = None
    connect_timeout: int = 3
    read_timeout: int = 7
    output: str = "docs/data/data.json"
    api_key: str | None = None
    templates: str | None = None
    progress: str | None = None


def _validate_range(
    parser: argparse.ArgumentParser, value: int, lo: int, hi: int, name: str
) -> int:
    if not (lo <= value <= hi):
        parser.error(f"--{name} must be between {lo} and {hi}, got {value}")
    return value


def parse_cli_args(args: list[str] | None = None) -> ScanConfig:
    """Parse command-line arguments and return a ScanConfig.

    Args:
        args: Argument list (defaults to sys.argv[1:] when None).
    """
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="StackRecon — Bug Bounty Technology Intelligence Scanner",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=50,
        metavar="N",
        help="Concurrent HTTP probe workers (1–500, default: 50)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process at most N programs (default: all)",
    )
    parser.add_argument(
        "--connect-timeout",
        type=int,
        default=3,
        metavar="S",
        dest="connect_timeout",
        help="TCP connect timeout in seconds (1–30, default: 3)",
    )
    parser.add_argument(
        "--read-timeout",
        type=int,
        default=7,
        metavar="S",
        dest="read_timeout",
        help="HTTP read timeout in seconds (1–60, default: 7)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/data/data.json",
        metavar="PATH",
        help="Output JSON file path (default: docs/data/data.json)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        metavar="KEY",
        dest="api_key",
        help="Chaos API key (omit to use public GitHub source)",
    )
    parser.add_argument(
        "--templates",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to custom nuclei templates directory (default: nuclei built-in)",
    )
    parser.add_argument(
        "--progress",
        type=str,
        default=None,
        metavar="PATH",
        dest="progress",
        help="Path to write live progress JSON (e.g. docs/data/progress.json)",
    )

    parsed = parser.parse_args(args)

    _validate_range(parser, parsed.workers, 1, 500, "workers")
    _validate_range(parser, parsed.connect_timeout, 1, 30, "connect-timeout")
    _validate_range(parser, parsed.read_timeout, 1, 60, "read-timeout")
    if parsed.limit is not None and parsed.limit < 1:
        parser.error("--limit must be ≥ 1")

    return ScanConfig(
        workers=parsed.workers,
        limit=parsed.limit,
        connect_timeout=parsed.connect_timeout,
        read_timeout=parsed.read_timeout,
        output=parsed.output,
        api_key=parsed.api_key,
        templates=parsed.templates,
        progress=parsed.progress,
    )
