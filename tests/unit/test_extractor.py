"""Unit tests for scanner.src.extractor — TDD: written before implementation."""

import io
import zipfile

import pytest

from scanner.src.extractor import extract_subdomains


def make_zip(files: dict[str, str]) -> bytes:
    """Create a ZIP archive with the given {filename: content} mapping."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# extract_subdomains tests
# ---------------------------------------------------------------------------

def test_extract_subdomains_single_file():
    """Standard everything.txt with 3 subdomains returns 3-item list."""
    zip_bytes = make_zip({"everything.txt": "a.example.com\nb.example.com\nc.example.com\n"})
    result = extract_subdomains(zip_bytes)
    assert sorted(result) == ["a.example.com", "b.example.com", "c.example.com"]


def test_extract_subdomains_strips_whitespace():
    """Lines with leading/trailing whitespace are stripped."""
    zip_bytes = make_zip({"everything.txt": "  a.example.com  \n  b.example.com\n"})
    result = extract_subdomains(zip_bytes)
    assert "a.example.com" in result
    assert "b.example.com" in result


def test_extract_subdomains_skips_empty_lines():
    """Empty lines in the text file are not included."""
    zip_bytes = make_zip({"everything.txt": "a.example.com\n\nb.example.com\n\n"})
    result = extract_subdomains(zip_bytes)
    assert len(result) == 2


def test_extract_subdomains_deduplicates():
    """Duplicate hostnames are deduplicated."""
    zip_bytes = make_zip({"everything.txt": "a.example.com\na.example.com\nb.example.com\n"})
    result = extract_subdomains(zip_bytes)
    assert result.count("a.example.com") == 1
    assert len(result) == 2


def test_extract_subdomains_empty_zip_returns_empty_list():
    """A ZIP with an empty text file returns an empty list."""
    zip_bytes = make_zip({"everything.txt": ""})
    result = extract_subdomains(zip_bytes)
    assert result == []


def test_extract_subdomains_multiple_txt_files():
    """When ZIP has multiple .txt files, all hostnames are merged."""
    zip_bytes = make_zip({
        "hackerone.com.txt": "a.hackerone.com\n",
        "hackerone.net.txt": "b.hackerone.net\n",
    })
    result = extract_subdomains(zip_bytes)
    assert "a.hackerone.com" in result
    assert "b.hackerone.net" in result


def test_extract_subdomains_invalid_zip_returns_empty():
    """Corrupt/invalid ZIP bytes return empty list (no crash)."""
    result = extract_subdomains(b"not a zip file at all")
    assert result == []
