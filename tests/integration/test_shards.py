"""Offline recovery checks: preserve all programs and reject incomplete publication."""

import copy
import json
from pathlib import Path

import pytest

from scanner import main, shards
from scanner.src.config import ScanConfig, parse_cli_args


@pytest.fixture
def index_path(tmp_path):
    # Shared hosts and duplicate display names must not lose/duplicate coverage.
    index = [
        {"name": "One", "url": "https://one.example", "domains": ["one.example", "shared.example"]},
        {"name": "Two", "url": "https://two.example", "domains": ["two.example", "shared.example"]},
        {"name": "One", "url": "https://other.example", "domains": ["other.example"]},
    ]
    path = tmp_path / "scan-index.json"
    path.write_text(json.dumps(index))
    return path


@pytest.fixture
def fake_scanners(monkeypatch):
    def httpx(hostnames, **kwargs):
        return [
            {
                "hostname": h,
                "technologies": ["Nginx", "HSTS"],
                "http_status": 200,
                "probe_error": None,
            }
            for h in hostnames
        ], list(hostnames)

    def nuclei(hostnames, **kwargs):
        return [
            {
                "hostname": h,
                "template_id": "test",
                "name": "Test",
                "severity": "high",
                "matched_at": f"https://{h}/private",
                "description": "Controlled fixture",
            }
            for h in hostnames
            if h.startswith("www.")
        ]

    def info(hostnames, **kwargs):
        return [
            {
                "hostname": h,
                "template_id": "test-info",
                "name": "Tech",
                "severity": "info",
                "matched_at": f"https://{h}",
                "description": "Controlled fixture",
            }
            for h in hostnames
            if h.startswith("api.")
        ]

    monkeypatch.setattr(main, "run_httpx_binary", httpx)
    monkeypatch.setattr(main, "run_nuclei", nuclei)
    monkeypatch.setattr(main, "run_nuclei_info", info)


async def scan(index_path, output, shard_index=0, shard_count=1):
    config = ScanConfig(
        program_index=str(index_path),
        output=str(output),
        workers=75,
        shard_index=shard_index,
        shard_count=shard_count,
        strict=True,
    )
    assert await main.run(config) == 0
    return json.loads(output.with_name("data-full.json").read_text())


@pytest.fixture
async def completed_reports(index_path, tmp_path, fake_scanners):
    return [
        await scan(index_path, tmp_path / "parts" / f"scan-shard-{i}" / "data.json", i, 16)
        for i in range(16)
    ]


def normalize(programs):
    result = copy.deepcopy(programs)
    for program in result:
        for field in ("detections", "vulnerabilities", "info_findings"):
            program[field].sort(key=lambda item: json.dumps(item, sort_keys=True))
    return result


async def test_shards_equal_complete_single_scan(index_path, tmp_path, completed_reports):
    baseline = await scan(index_path, tmp_path / "baseline" / "data.json")
    merged = shards.merge_reports(index_path, completed_reports, 16)
    assert normalize(merged["programs"]) == normalize(baseline["programs"])
    for key in (
        "programs_scanned",
        "programs_failed",
        "total_subdomains_probed",
        "total_detections",
        "total_vuln_findings",
        "total_info_findings",
    ):
        assert merged["meta"][key] == baseline["meta"][key]
    assert merged["meta"]["shards_completed"] == 16


def test_all_802_programs_partitioned_once():
    index = [
        {"name": f"Program {i}", "domains": [f"p{i}.example", "shared.example"]} for i in range(802)
    ]
    hosts = shards.index_hosts(index)
    partitions = [hosts[i::16] for i in range(16)]
    flattened = [h for part in partitions for h in part]
    assert len(flattened) == len(set(flattened)) == len(hosts)
    assert set(flattened) == set(hosts)
    assert max(map(len, partitions)) - min(map(len, partitions)) <= 1


@pytest.mark.parametrize(
    "damage", ["missing", "duplicate", "snapshot", "incomplete", "program", "hosts"]
)
def test_incomplete_merge_cannot_overwrite_baseline(
    index_path, tmp_path, completed_reports, damage
):
    reports = copy.deepcopy(completed_reports)
    if damage == "missing":
        reports.pop()
    elif damage == "duplicate":
        reports[-1] = reports[0]
    elif damage == "snapshot":
        reports[0]["meta"]["shard"]["index_sha256"] = "wrong"
    elif damage == "incomplete":
        reports[0]["meta"]["shard"]["complete"] = False
    elif damage == "program":
        reports[0]["programs"].pop()
    elif damage == "hosts":
        reports[0]["meta"]["total_subdomains_probed"] -= 1
    directory = tmp_path / "damaged"
    for i, report in enumerate(reports):
        path = directory / str(i) / "data-full.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(report))
    output, progress = tmp_path / "public.json", tmp_path / "progress.json"
    output.write_text('{"last_complete": true}')
    progress.write_text('{"status": "idle"}')
    with pytest.raises(ValueError):
        shards.publish(index_path, directory, 16, output, progress)
    assert output.read_text() == '{"last_complete": true}'
    assert progress.read_text() == '{"status": "idle"}'
    assert not output.with_name("public-full.json").exists()


def test_publish_merges_before_diff_and_strips_private_findings(
    index_path, tmp_path, completed_reports
):
    output = tmp_path / "published" / "data.json"
    progress = output.with_name("progress.json")
    output.parent.mkdir()
    # Existing programs must not appear removed just because they reside in a different shard.
    previous = {
        "programs": [
            {"name": p["name"], "detections": []} for p in completed_reports[0]["programs"]
        ]
    }
    output.write_text(json.dumps(previous))
    shards.publish(index_path, tmp_path / "parts", 16, output, progress)
    public = json.loads(output.read_text())
    full = json.loads(output.with_name("data-full.json").read_text())
    assert public["diff"]["removed_programs"] == []
    assert public["meta"]["programs_scanned"] == 3
    assert all("vulnerabilities" not in p for p in public["programs"])
    assert any(p["vulnerabilities"] for p in full["programs"])
    assert json.loads(progress.read_text())["status"] == "idle"


async def test_nuclei_failure_prevents_shard_report(
    index_path, tmp_path, fake_scanners, monkeypatch
):
    def fail(**kwargs):
        raise RuntimeError("controlled scanner failure")

    monkeypatch.setattr(main, "run_nuclei", fail)
    output = tmp_path / "failed" / "data.json"
    with pytest.raises(RuntimeError, match="controlled"):
        await scan(index_path, output, 0, 16)
    assert not output.exists()
    assert not output.with_name("data-full.json").exists()


@pytest.mark.parametrize(
    "args",
    [
        ["--shard-count", "16"],
        ["--shard-index", "16", "--shard-count", "16"],
        ["--program-index", "index.json", "--limit", "1"],
    ],
)
def test_invalid_sharding_configuration_rejected(args):
    with pytest.raises(SystemExit):
        parse_cli_args(args)
