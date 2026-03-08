"""Extractor — parses subdomain lists from Chaos ZIP archives."""

from __future__ import annotations

import io
import zipfile


def extract_subdomains(zip_bytes: bytes) -> list[str]:
    """Extract unique, non-empty hostnames from a Chaos ZIP archive.

    The ZIP typically contains one or more plaintext files (e.g. everything.txt
    or per-domain files like hackerone.com.txt) with one hostname per line.

    Args:
        zip_bytes: Raw bytes of the ZIP archive.

    Returns:
        Deduplicated list of hostname strings. Empty list if archive is invalid
        or contains no readable text files.
    """
    try:
        buf = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buf, mode="r") as zf:
            hostnames: set[str] = set()
            for name in zf.namelist():
                if not name.endswith(".txt"):
                    continue
                try:
                    content = zf.read(name).decode("utf-8", errors="replace")
                except Exception:
                    continue
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped:
                        hostnames.add(stripped)
            return list(hostnames)
    except zipfile.BadZipFile:
        return []
    except Exception:
        return []
