"""Detector — loads YAML signatures and detects technologies in HTTP responses."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

import httpx
import yaml

# ---------------------------------------------------------------------------
# Signature loading
# ---------------------------------------------------------------------------


def load_signatures(path: str | Path) -> list[dict[str, Any]]:
    """Load technology signatures from a YAML file.

    Args:
        path: Path to technologies.yaml.

    Returns:
        List of signature dicts, each with at least a 'name' key.
    """
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("technologies", [])


# ---------------------------------------------------------------------------
# Offline detection (header + HTML body matching)
# ---------------------------------------------------------------------------


def detect_offline(
    headers: dict[str, str],
    body: str,
    signatures: list[dict[str, Any]],
) -> list[str]:
    """Detect technologies from HTTP headers and response body without live probing.

    Supports two header signal formats:
      - YAML list format: [{"name": "Server", "pattern": "(?i)grafana", ...}]
      - Dict format (tests): {"X-Grafana-Id": ".*"}

    Args:
        headers:    HTTP response headers (any case; matched case-insensitively).
        body:       HTTP response body as a string.
        signatures: List of signature dicts from load_signatures().

    Returns:
        List of detected technology display names.
    """
    detected: list[str] = []
    headers_lower = {k.lower(): v for k, v in headers.items()}

    for sig in signatures:
        name = sig.get("name", "")
        signals = sig.get("signals", {})
        matched = False

        raw_headers = signals.get("headers", [])

        if isinstance(raw_headers, dict):
            # Dict-style: {"HeaderName": "pattern"}
            for header_name, pattern in raw_headers.items():
                if header_name.lower() in headers_lower:
                    if re.search(pattern, headers_lower[header_name.lower()], re.IGNORECASE):
                        matched = True
                        break
        elif isinstance(raw_headers, list):
            # List-of-dicts style from YAML: [{"name": "...", "pattern": "..."}]
            for header_sig in raw_headers:
                if not isinstance(header_sig, dict):
                    continue
                header_name = header_sig.get("name", "").lower()
                pattern = header_sig.get("pattern", "")
                if header_name in headers_lower:
                    if re.search(pattern, headers_lower[header_name], re.IGNORECASE):
                        matched = True
                        break

        if matched:
            detected.append(name)
            continue

        # HTML signals — supports both string patterns and dict format
        for html_sig in signals.get("html", []):
            if isinstance(html_sig, str):
                # Plain string: literal substring match
                if html_sig in body:
                    matched = True
                    break
            elif isinstance(html_sig, dict):
                pattern = html_sig.get("pattern", "")
                if pattern and re.search(pattern, body, re.IGNORECASE):
                    matched = True
                    break

        if matched:
            detected.append(name)

    return detected


# ---------------------------------------------------------------------------
# Live HTTP probe
# ---------------------------------------------------------------------------


async def probe_subdomain(
    hostname: str,
    signatures: list[dict[str, Any]],
    connect_timeout: int = 3,
    read_timeout: int = 7,
) -> dict[str, Any] | None:
    """Probe a single subdomain via HTTP and detect technologies.

    Tries HTTP first; does not follow HTTPS upgrade (respects timeout budget).

    Args:
        hostname:        Bare hostname (no scheme).
        signatures:      Signatures to match against.
        connect_timeout: TCP connect timeout in seconds.
        read_timeout:    HTTP read timeout in seconds.

    Returns:
        Detection dict if at least one technology detected or a probe error occurred
        for live_probe_required signatures; None if no relevant detections.
    """
    url = f"http://{hostname}"
    timeout = httpx.Timeout(
        connect=float(connect_timeout), read=float(read_timeout), write=5.0, pool=5.0
    )

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            verify=False,
        ) as client:
            resp = await client.get(url)
    except httpx.TimeoutException:
        return {
            "hostname": hostname,
            "technologies": [],
            "http_status": None,
            "probe_error": "timeout",
        }
    except httpx.ConnectError:
        return {
            "hostname": hostname,
            "technologies": [],
            "http_status": None,
            "probe_error": "connection_refused",
        }
    except httpx.HTTPStatusError:
        return {
            "hostname": hostname,
            "technologies": [],
            "http_status": None,
            "probe_error": "unknown",
        }
    except Exception:
        return {
            "hostname": hostname,
            "technologies": [],
            "http_status": None,
            "probe_error": "unknown",
        }

    headers = dict(resp.headers)
    body = resp.text

    techs = detect_offline(headers=headers, body=body, signatures=signatures)

    if not techs:
        return None

    return {
        "hostname": hostname,
        "technologies": techs,
        "http_status": resp.status_code,
        "probe_error": None,
    }


# ---------------------------------------------------------------------------
# Batch detection with worker pool
# ---------------------------------------------------------------------------


async def detect_all(
    hostnames: list[str],
    signatures: list[dict[str, Any]],
    workers: int = 50,
    connect_timeout: int = 3,
    read_timeout: int = 7,
) -> list[dict[str, Any]]:
    """Probe all hostnames concurrently and return only subdomains with detections.

    Args:
        hostnames:       List of bare hostnames to probe.
        signatures:      Technology signatures to match.
        workers:         Maximum concurrent HTTP requests.
        connect_timeout: Per-request TCP connect timeout.
        read_timeout:    Per-request HTTP read timeout.

    Returns:
        List of detection dicts (only entries with ≥1 detected technology).
    """
    semaphore = asyncio.Semaphore(workers)

    async def _probe(hostname: str) -> dict[str, Any] | None:
        async with semaphore:
            return await probe_subdomain(
                hostname=hostname,
                signatures=signatures,
                connect_timeout=connect_timeout,
                read_timeout=read_timeout,
            )

    tasks = [_probe(h) for h in hostnames]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    return [r for r in results if r is not None and r.get("technologies")]
