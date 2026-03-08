# Contract: Scanner CLI Interface

**Type**: CLI Tool | **Branch**: `001-bug-bounty-intel` | **Date**: 2026-03-08

---

## Command Signature

```
python main.py [OPTIONS]
```

## Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--workers N` | int | 50 | Concurrent HTTP probe workers (1–500) |
| `--limit N` | int | (all) | Process at most N programs (≥1) |
| `--connect-timeout S` | int | 3 | TCP connect timeout in seconds (1–30) |
| `--read-timeout S` | int | 7 | HTTP read timeout in seconds (1–60) |
| `--output PATH` | str | `docs/data/data.json` | Output JSON file path |
| `--api-key KEY` | str | (none) | Chaos API key; omit to use public GitHub source |

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Scan completed successfully; `data.json` written |
| `1` | Chaos/GitHub source unreachable at startup; `data.json` unchanged |
| `2` | Invalid CLI arguments |
| `3` | Output path unwritable (disk full, permissions); `data.json` unchanged |

## Standard Output (during scan)

Progress messages written to stdout; one line per completed program:
```
[2026-03-08 12:00:01] [1/2847] HackerOne — 423 subdomains, 12 detections
[2026-03-08 12:00:02] [2/2847] Bugcrowd — 212 subdomains, 5 detections
```

## Standard Error

Errors and warnings written to stderr; does NOT terminate execution (except
source-unreachable which triggers immediate exit):
```
[WARN] hackerone.com: ZIP unavailable (HTTP 404) — skipping
[WARN] api.target.com: probe timeout after 10s — skipping
[ERROR] Chaos source unreachable: Connection refused — aborting
```

## Invariants

- MUST NOT modify or delete an existing `data.json` unless a new scan completes fully.
- MUST exit with code 1 and print to stderr if Chaos/GitHub source is unreachable.
- MUST process programs in the order returned by the index (stable ordering).
- MUST respect `--limit N` exactly; process N programs and stop.
- MUST NOT make exploitative or intrusive HTTP requests (only GET, no auth attempts).
