"""Fetcher — downloads Chaos index and program ZIP files."""

from __future__ import annotations

import httpx

CHAOS_GITHUB_URL = (
    "https://raw.githubusercontent.com/projectdiscovery/"
    "public-bugbounty-programs/main/dist/data.json"
)


class SourceUnavailableError(Exception):
    """Raised when the Chaos source cannot be reached."""


async def fetch_chaos_index(
    api_key: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Fetch the public Chaos program index and return a list of program dicts.

    Args:
        api_key: Optional Chaos REST API key. When provided, uses the REST API.
                 When None, fetches from the public GitHub raw URL.
        limit:   If set, return at most this many programs.

    Raises:
        SourceUnavailableError: If the source is unreachable or returns a non-200 response.
    """
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(CHAOS_GITHUB_URL, headers=headers)
            if resp.status_code != 200:
                raise SourceUnavailableError(f"Chaos source returned HTTP {resp.status_code}")
            data = resp.json()
    except httpx.HTTPError as exc:
        raise SourceUnavailableError(f"Chaos source unreachable: {exc}") from exc

    # The public GitHub JSON is a list of program dicts.
    programs: list[dict] = data if isinstance(data, list) else data.get("programs", [])

    if limit is not None:
        programs = programs[:limit]

    return programs


async def download_zip(url: str, timeout: int = 30) -> bytes | None:
    """Download a program's subdomain ZIP file.

    Args:
        url:     Full URL to the ZIP archive.
        timeout: Request timeout in seconds.

    Returns:
        Raw ZIP bytes on success, None if the file is unavailable or timed out.
    """
    try:
        async with httpx.AsyncClient(timeout=float(timeout)) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            return resp.content
    except (httpx.HTTPError, httpx.TimeoutException):
        return None
