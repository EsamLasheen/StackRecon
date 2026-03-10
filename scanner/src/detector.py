"""Detector — loads YAML signatures and detects technologies in HTTP responses."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import tempfile
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
# httpx binary detection (primary path — Wappalyzer fingerprints, 1400+ techs)
# ---------------------------------------------------------------------------


def run_httpx_binary(
    hostnames: list[str],
    threads: int = 50,
    timeout: int = 10,
) -> list[dict[str, Any]]:
    """Run the projectdiscovery/httpx binary with Wappalyzer tech detection.

    Requires the `httpx` binary to be installed and on PATH.

    Args:
        hostnames: Bare hostnames to probe (no scheme).
        threads:   Concurrent worker threads.
        timeout:   Per-request timeout in seconds.

    Returns:
        List of detection dicts for hosts where at least one tech was detected.
        Each dict has: hostname, technologies, http_status, probe_error.
    """
    if not hostnames:
        return []

    tmpfile = Path(tempfile.mktemp(suffix=".txt"))
    try:
        tmpfile.write_text("\n".join(hostnames) + "\n", encoding="utf-8")

        result = subprocess.run(
            [
                "httpx",
                "-l",
                str(tmpfile),
                "-tech-detect",
                "-json",
                "-silent",
                "-no-color",
                "-t",
                str(threads),
                "-timeout",
                str(timeout),
                "-retries",
                "0",  # no retries — failed hosts counted once, not twice
                "-follow-redirects",
            ],
            capture_output=True,
            text=True,
            timeout=14400,  # 4-hour hard cap (scan should finish in <30 min)
        )

        detections: list[dict[str, Any]] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                techs = data.get("tech", [])
                if not techs:
                    continue
                # Strip version numbers: "Nginx:1.18.0" -> "Nginx"
                clean_techs = [t.split(":")[0] for t in techs]
                # Prefer 'input' field (original hostname); fall back to parsed url
                host = data.get("input", data.get("url", ""))
                if "://" in host:
                    host = host.split("://", 1)[1].split("/")[0]
                detections.append(
                    {
                        "hostname": host,
                        "technologies": clean_techs,
                        "http_status": data.get("status-code"),
                        "probe_error": None,
                    }
                )
            except json.JSONDecodeError:
                continue

        return detections
    finally:
        tmpfile.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Nuclei misconfiguration / exposure scanner
# ---------------------------------------------------------------------------


def run_nuclei(
    hostnames: list[str],
    concurrency: int = 50,
    rate_limit: int = 150,
    timeout: int = 10,
) -> list[dict[str, Any]]:
    """Run nuclei with misconfiguration/exposure/default-login templates.

    Args:
        hostnames: Bare hostnames (no scheme) to scan.
        concurrency: Parallel template executions.
        rate_limit: Max requests per second.
        timeout: Per-request timeout in seconds.

    Returns:
        List of finding dicts: hostname, template_id, name, severity, matched_at, description.
    """
    if not hostnames:
        return []

    tmpfile = Path(tempfile.mktemp(suffix=".txt"))
    try:
        # nuclei accepts bare hostnames directly
        tmpfile.write_text("\n".join(hostnames) + "\n", encoding="utf-8")

        cmd = [
            "nuclei",
            "-l",
            str(tmpfile),
            "-tags",
            "panel,exposure,misconfig,default-login",
            "-severity",
            "critical,high,medium",
            "-j",  # JSON output (short flag)
            "-silent",
            "-no-color",
            "-c",
            str(concurrency),
            "-bs",
            str(concurrency),  # bulk-size: hosts per template in parallel
            "-timeout",
            str(timeout),
            "-rl",
            str(rate_limit),
            "-no-interactsh",
            "-exclude-tags",
            "dos,intrusive,fuzz,ssrf",
        ]

        # Stream stdout line-by-line via Popen so findings are captured
        # even if nuclei is killed on timeout.
        import time as _time

        deadline = _time.monotonic() + 5400  # 90-min hard cap
        findings: list[dict[str, Any]] = []

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        try:
            for line in proc.stdout:  # type: ignore[union-attr]
                if _time.monotonic() > deadline:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    host = data.get("host", data.get("matched-at", ""))
                    if "://" in host:
                        host = host.split("://", 1)[1].split("/")[0].split(":")[0]

                    info = data.get("info", {})
                    findings.append(
                        {
                            "hostname": host,
                            "template_id": data.get("template-id", ""),
                            "name": info.get("name", ""),
                            "severity": info.get("severity", "info").lower(),
                            "matched_at": data.get("matched-at", ""),
                            "description": info.get("description", ""),
                        }
                    )
                except json.JSONDecodeError:
                    continue
        finally:
            proc.kill()
            proc.wait()

        return findings
    finally:
        tmpfile.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Live HTTP probe (legacy / test fallback)
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
# Batch detection with worker pool (legacy / test fallback)
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
