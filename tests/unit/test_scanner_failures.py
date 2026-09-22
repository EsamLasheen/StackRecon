"""Exercise process failures without contacting live targets."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from scanner.src.detector import run_httpx_binary, run_nuclei, run_nuclei_info


@pytest.fixture
def controlled_binary(tmp_path, monkeypatch):
    import os

    fixture = {
        "input": "host.example",
        "host": "host.example",
        "tech": ["Nginx"],
        "template-id": "fixture",
        "info": {"name": "Fixture", "severity": "info"},
    }
    script = (
        "#!/usr/bin/env python3\nimport os, sys\n"
        f"print({json.dumps(json.dumps(fixture))}, flush=True)\n"
        "sys.exit(int(os.environ['STUB_EXIT']))\n"
    )
    for name in ("httpx", "nuclei"):
        binary = tmp_path / name
        binary.write_text(script)
        binary.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])


def test_httpx_rejects_partial_output_on_nonzero_exit(controlled_binary, monkeypatch):
    monkeypatch.setenv("STUB_EXIT", "2")
    with pytest.raises(subprocess.CalledProcessError):
        run_httpx_binary(["host.example"])


@pytest.mark.parametrize("runner", [run_nuclei, run_nuclei_info])
def test_nuclei_rejects_partial_output_on_nonzero_exit(runner, controlled_binary, monkeypatch):
    monkeypatch.setenv("STUB_EXIT", "2")
    with pytest.raises(RuntimeError, match="exit=2"):
        runner(["host.example"], strict=True)


@pytest.mark.parametrize("runner", [run_nuclei, run_nuclei_info])
def test_normal_eof_does_not_kill_successful_process(runner, controlled_binary, monkeypatch):
    monkeypatch.setenv("STUB_EXIT", "0")
    assert runner(["host.example"], strict=True)[0]["hostname"] == "host.example"


@pytest.mark.parametrize("runner", [run_nuclei, run_nuclei_info])
def test_deadline_rejects_partial_findings(runner):
    process = MagicMock()
    process.stdout = iter([json.dumps({"host": "host.example", "info": {}}) + "\n"])
    process.wait.return_value = -9
    with (
        patch("scanner.src.detector.subprocess.Popen", return_value=process),
        patch("time.monotonic", side_effect=[0, 0, 10000]),
    ):
        with pytest.raises(RuntimeError, match="timed_out=True"):
            runner(["host.example"], strict=True)
    process.kill.assert_called_once()
