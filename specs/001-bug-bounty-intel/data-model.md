# Data Model: StackRecon — Bug Bounty Technology Intelligence

**Branch**: `001-bug-bounty-intel` | **Phase**: 1 | **Date**: 2026-03-08

---

## Entities

### Program

Represents a single public bug bounty or VDP program from Chaos ProjectDiscovery.

| Field | Type | Constraints | Source |
|---|---|---|---|
| `name` | string | Non-empty, unique within dataset | Chaos index |
| `url` | string | Valid HTTP/HTTPS URL | Chaos index |
| `platform` | string | Enum: `HackerOne`, `Bugcrowd`, `Intigriti`, `YesWeHack`, `Other` | Derived from `url` |
| `reward_type` | string | Enum: `paid`, `free`, `self-hosted` | Derived from `bounty` flag + URL pattern |
| `domains` | string[] | ≥1 root domain per program | Chaos index |
| `technologies` | string[] | Distinct detected technology names; may be empty | Derived by detector |
| `subdomain_count` | integer | ≥0; count of all subdomains in ZIP | Derived after extraction |
| `detection_count` | integer | ≥0; count of subdomains with ≥1 tech detected | Derived after detection |

**Uniqueness**: `name` is the primary identifier within a scan run. Programs with
identical names on different platforms are disambiguated by appending platform suffix.

**Reward type derivation rules** (in priority order):
1. `bounty: true` → `paid`
2. `bounty: false` AND URL contains known self-hosted platform pattern → `self-hosted`
3. `bounty: false` AND URL is a company page (no known platform) → `free`

---

### Subdomain

A single hostname associated with a Program. Only subdomains with at least one
detected technology are persisted in the output file.

| Field | Type | Constraints | Source |
|---|---|---|---|
| `hostname` | string | Valid FQDN; non-empty | Chaos ZIP extraction |
| `technologies` | string[] | ≥1 tech name; subdomains with zero detections omitted | Detector output |
| `http_status` | integer \| null | HTTP status code from live probe; `null` if probe skipped or failed | Live probe |
| `probe_error` | string \| null | Error category (`timeout`, `dns_failed`, `ssl_error`, `connection_refused`, `unknown`) if probe failed; `null` on success | Live probe |

---

### Technology

A named technology signature that the detector can identify. Defined in
`signatures/technologies.yaml`.

| Field | Type | Constraints |
|---|---|---|
| `id` | string | Lowercase slug; unique across all signatures (e.g., `grafana`) |
| `name` | string | Display name (e.g., `Grafana`) |
| `category` | string | One of: `Monitoring/Analytics`, `CI/CD`, `Identity/Auth`, `CMS`, `DevOps/VCS`, `Project Management`, `Collaboration`, `Search/Data`, `Visualization`, `Web Server`, `Framework`, `Other` |
| `live_probe_required` | boolean | If `true`, scanner MUST make a live HTTP request to detect this tech |
| `min_confidence_threshold` | float | 0.0–1.0; detections below this are discarded |
| `signals` | object | Header, HTML, path-based detection rules (see research.md RD-003) |
| `version_patterns` | object[] | Optional; regex to extract version string |

---

### ScanRun

Metadata produced after a complete scanner execution. Embedded in the output
JSON under the `meta` key.

| Field | Type | Constraints |
|---|---|---|
| `generated_at` | string | ISO 8601 UTC timestamp |
| `programs_scanned` | integer | Count of programs successfully processed |
| `programs_failed` | integer | Count of programs skipped due to errors |
| `total_subdomains_probed` | integer | Count of unique hostnames probed via HTTP |
| `total_detections` | integer | Count of (subdomain, technology) pairs detected |
| `scanner_version` | string | SemVer string of the scanner |
| `workers_used` | integer | Concurrency setting used for this run |

---

### OutputFile (`data.json`)

The complete output artifact written atomically by the scanner and consumed
directly by the web frontend.

```json
{
  "meta": {
    "generated_at": "2026-03-08T12:00:00Z",
    "programs_scanned": 2835,
    "programs_failed": 12,
    "total_subdomains_probed": 1200000,
    "total_detections": 48312,
    "scanner_version": "1.0.0",
    "workers_used": 50
  },
  "programs": [
    {
      "name": "HackerOne",
      "url": "https://hackerone.com/security",
      "platform": "HackerOne",
      "reward_type": "paid",
      "domains": ["hackerone.com", "hackerone.net"],
      "technologies": ["Grafana", "Jenkins"],
      "subdomain_count": 423,
      "detection_count": 12,
      "detections": [
        {
          "hostname": "grafana.hackerone.com",
          "technologies": ["Grafana"],
          "http_status": 200,
          "probe_error": null
        },
        {
          "hostname": "ci.hackerone.com",
          "technologies": ["Jenkins"],
          "http_status": 200,
          "probe_error": null
        }
      ]
    }
  ]
}
```

**Write constraints**:
- The file is written to a temporary path during scan execution.
- It is atomically renamed to `data.json` only upon full successful completion.
- If the scanner aborts mid-run, the existing `data.json` is left unchanged.

---

## Entity Relationships

```
ScanRun (1) ──── meta section of OutputFile
Program (1) ──── (*) Subdomain         [one program has many subdomains]
Subdomain (*) ── (*) Technology        [one subdomain may match many technologies]
Technology (1) ── signature YAML        [one signature file defines all technologies]
OutputFile (1) ── (n) Programs          [one file contains all programs in a scan run]
```

---

## State Transitions (Scanner Pipeline)

```
[FETCHING INDEX]
  Chaos source reachable?
    No  → ABORT (non-zero exit; data.json untouched)
    Yes → [DOWNLOADING ZIPs]

[DOWNLOADING ZIPs]
  Per program: ZIP available?
    No  → log error, increment programs_failed, skip to next program
    Yes → [EXTRACTING SUBDOMAINS]

[EXTRACTING SUBDOMAINS]
  Per program: parse plaintext file(s) from ZIP
    → [DETECTING TECHNOLOGIES]

[DETECTING TECHNOLOGIES]
  Per subdomain:
    Offline signatures matched?     → tag subdomain with detected techs
    Live probe required + probed?
      Success                       → tag subdomain with detected techs
      Timeout                       → log, probe_error = "timeout", skip
      DNS/SSL/Connection error      → log, probe_error = <category>, skip
    No detections                   → subdomain OMITTED from output
    → [AGGREGATING]

[AGGREGATING]
  Per program: collect detected subdomains, derive technologies summary
    → [WRITING]

[WRITING]
  All programs processed?
    Write to temp file → atomic rename to data.json → EXIT 0
  Disk error during write?
    Log error → EXIT non-zero (data.json untouched if rename not yet done)
```

---

## ScanConfig (CLI + Runtime)

Represents all runtime configuration for a scan, injected via CLI flags.

| Flag | Default | Validation |
|---|---|---|
| `--workers N` | 50 | 1 ≤ N ≤ 500 |
| `--limit N` | None (all programs) | N ≥ 1 |
| `--connect-timeout S` | 3 | 1 ≤ S ≤ 30 |
| `--read-timeout S` | 7 | 1 ≤ S ≤ 60 |
| `--output PATH` | `docs/data/data.json` | Parent directory must exist |
| `--api-key KEY` | None (uses public GitHub source) | Optional |
