"""Tests for scan diff tracking."""

from scanner.src.differ import compute_diff, load_previous_scan


def test_new_program_detected():
    prev = {"programs": [{"name": "Prog1", "technologies": ["Nginx"], "detections": []}]}
    curr = {
        "programs": [
            {"name": "Prog1", "technologies": ["Nginx"], "detections": []},
            {"name": "Prog2", "technologies": ["Apache"], "detections": []},
        ]
    }
    diff = compute_diff(prev, curr)
    assert "Prog2" in diff["new_programs"]
    assert "Prog1" not in diff["new_programs"]


def test_removed_program_detected():
    prev = {
        "programs": [
            {"name": "Prog1", "technologies": [], "detections": []},
            {"name": "Prog2", "technologies": [], "detections": []},
        ]
    }
    curr = {"programs": [{"name": "Prog1", "technologies": [], "detections": []}]}
    diff = compute_diff(prev, curr)
    assert "Prog2" in diff["removed_programs"]


def test_new_host_detected():
    prev = {
        "programs": [
            {
                "name": "P1",
                "technologies": [],
                "detections": [{"hostname": "a.example.com", "technologies": ["Nginx"]}],
            }
        ]
    }
    curr = {
        "programs": [
            {
                "name": "P1",
                "technologies": [],
                "detections": [
                    {"hostname": "a.example.com", "technologies": ["Nginx"]},
                    {"hostname": "b.example.com", "technologies": ["Apache"]},
                ],
            }
        ]
    }
    diff = compute_diff(prev, curr)
    assert "b.example.com" in diff["new_hosts"]
    assert "a.example.com" not in diff["new_hosts"]


def test_removed_host_detected():
    prev = {
        "programs": [
            {
                "name": "P1",
                "technologies": [],
                "detections": [
                    {"hostname": "a.example.com", "technologies": ["Nginx"]},
                    {"hostname": "b.example.com", "technologies": ["Apache"]},
                ],
            }
        ]
    }
    curr = {
        "programs": [
            {
                "name": "P1",
                "technologies": [],
                "detections": [
                    {"hostname": "a.example.com", "technologies": ["Nginx"]},
                ],
            }
        ]
    }
    diff = compute_diff(prev, curr)
    assert "b.example.com" in diff["removed_hosts"]


def test_new_tech_on_existing_host():
    prev = {
        "programs": [
            {
                "name": "P1",
                "technologies": [],
                "detections": [{"hostname": "a.example.com", "technologies": ["Nginx"]}],
            }
        ]
    }
    curr = {
        "programs": [
            {
                "name": "P1",
                "technologies": [],
                "detections": [{"hostname": "a.example.com", "technologies": ["Nginx", "PHP"]}],
            }
        ]
    }
    diff = compute_diff(prev, curr)
    assert {"hostname": "a.example.com", "tech": "PHP"} in diff["new_techs"]


def test_no_previous_data():
    curr = {
        "programs": [
            {
                "name": "P1",
                "technologies": [],
                "detections": [{"hostname": "a.example.com", "technologies": ["X"]}],
            }
        ]
    }
    diff = compute_diff(None, curr)
    assert diff["new_programs"] == ["P1"]
    assert "a.example.com" in diff["new_hosts"]


def test_identical_scans():
    data = {
        "programs": [
            {
                "name": "P1",
                "technologies": ["X"],
                "detections": [{"hostname": "a.example.com", "technologies": ["X"]}],
            }
        ]
    }
    diff = compute_diff(data, data)
    assert diff["new_programs"] == []
    assert diff["new_hosts"] == []
    assert diff["new_techs"] == []
    assert diff["removed_programs"] == []
    assert diff["removed_hosts"] == []


def test_summary_counts():
    prev = {"programs": [{"name": "P1", "technologies": [], "detections": []}]}
    curr = {
        "programs": [
            {"name": "P1", "technologies": [], "detections": []},
            {
                "name": "P2",
                "technologies": [],
                "detections": [{"hostname": "new.example.com", "technologies": ["Nginx"]}],
            },
        ]
    }
    diff = compute_diff(prev, curr)
    assert diff["summary"]["new_programs"] == 1
    assert diff["summary"]["new_hosts"] == 1


def test_load_previous_scan_missing_file(tmp_path):
    result = load_previous_scan(tmp_path / "nonexistent.json")
    assert result is None


def test_load_previous_scan_valid(tmp_path):
    f = tmp_path / "data.json"
    f.write_text('{"programs": []}')
    result = load_previous_scan(f)
    assert result == {"programs": []}


def test_load_previous_scan_invalid_json(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("not json")
    result = load_previous_scan(f)
    assert result is None
