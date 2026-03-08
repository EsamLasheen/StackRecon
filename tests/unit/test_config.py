"""Unit tests for ScanConfig and CLI arg parsing. WRITE FIRST — must FAIL."""

import sys
import pytest


def test_default_values():
    from scanner.src.config import parse_cli_args

    config = parse_cli_args([])
    assert config.workers == 50
    assert config.limit is None
    assert config.connect_timeout == 3
    assert config.read_timeout == 7
    assert config.output == "docs/data/data.json"
    assert config.api_key is None


def test_workers_flag():
    from scanner.src.config import parse_cli_args

    config = parse_cli_args(["--workers", "100"])
    assert config.workers == 100


def test_workers_lower_bound():
    from scanner.src.config import parse_cli_args

    with pytest.raises(SystemExit):
        parse_cli_args(["--workers", "0"])


def test_workers_upper_bound():
    from scanner.src.config import parse_cli_args

    with pytest.raises(SystemExit):
        parse_cli_args(["--workers", "501"])


def test_connect_timeout_lower_bound():
    from scanner.src.config import parse_cli_args

    with pytest.raises(SystemExit):
        parse_cli_args(["--connect-timeout", "0"])


def test_connect_timeout_upper_bound():
    from scanner.src.config import parse_cli_args

    with pytest.raises(SystemExit):
        parse_cli_args(["--connect-timeout", "31"])


def test_limit_flag():
    from scanner.src.config import parse_cli_args

    config = parse_cli_args(["--limit", "10"])
    assert config.limit == 10


def test_api_key_flag():
    from scanner.src.config import parse_cli_args

    config = parse_cli_args(["--api-key", "mykey123"])
    assert config.api_key == "mykey123"


def test_output_flag():
    from scanner.src.config import parse_cli_args

    config = parse_cli_args(["--output", "/tmp/out.json"])
    assert config.output == "/tmp/out.json"
