"""Unit tests for scanner.src.writer — TDD: written before implementation."""

import json
from pathlib import Path

import pytest

from scanner.src.writer import write_atomic


SAMPLE_DATA = {
    "meta": {
        "generated_at": "2026-03-08T12:00:00Z",
        "programs_scanned": 1,
        "programs_failed": 0,
        "total_subdomains_probed": 10,
        "total_detections": 2,
        "scanner_version": "1.0.0",
        "workers_used": 5,
    },
    "programs": [
        {
            "name": "HackerOne",
            "url": "https://hackerone.com/security",
            "platform": "HackerOne",
            "reward_type": "paid",
            "domains": ["hackerone.com"],
            "technologies": ["Grafana"],
            "subdomain_count": 10,
            "detection_count": 2,
            "detections": [
                {
                    "hostname": "grafana.hackerone.com",
                    "technologies": ["Grafana"],
                    "http_status": 200,
                    "probe_error": None,
                }
            ],
        }
    ],
}


def test_write_atomic_creates_file(tmp_path):
    """write_atomic creates a JSON file at the specified path."""
    output = tmp_path / "data.json"
    write_atomic(SAMPLE_DATA, output)
    assert output.exists()


def test_write_atomic_valid_json(tmp_path):
    """The written file contains valid JSON matching input data."""
    output = tmp_path / "data.json"
    write_atomic(SAMPLE_DATA, output)
    with open(output) as f:
        parsed = json.load(f)
    assert parsed["meta"]["programs_scanned"] == 1
    assert parsed["programs"][0]["name"] == "HackerOne"


def test_write_atomic_no_temp_file_left_behind(tmp_path):
    """After successful write, no .tmp file is left in the directory."""
    output = tmp_path / "data.json"
    write_atomic(SAMPLE_DATA, output)
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert tmp_files == []


def test_write_atomic_preserves_existing_on_error(tmp_path):
    """If an error occurs during serialization, existing file is untouched."""
    output = tmp_path / "data.json"
    # Write initial good data
    write_atomic(SAMPLE_DATA, output)
    original_content = output.read_text()

    # Attempt to write un-serializable data (should raise, not corrupt)
    bad_data = {"programs": [object()]}  # object() is not JSON-serializable
    with pytest.raises(Exception):
        write_atomic(bad_data, output)

    # Original file unchanged
    assert output.read_text() == original_content


def test_write_atomic_accepts_path_and_string(tmp_path):
    """write_atomic accepts both Path objects and string paths."""
    output_str = str(tmp_path / "data_str.json")
    write_atomic(SAMPLE_DATA, output_str)
    assert Path(output_str).exists()

    output_path = tmp_path / "data_path.json"
    write_atomic(SAMPLE_DATA, output_path)
    assert output_path.exists()


def test_write_atomic_pretty_printed(tmp_path):
    """Output JSON should be human-readable (indented)."""
    output = tmp_path / "data.json"
    write_atomic(SAMPLE_DATA, output)
    raw = output.read_text()
    assert "\n" in raw  # indented JSON has newlines
