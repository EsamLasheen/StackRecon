# Contract: data.json Output Format

**Type**: File Format | **Branch**: `001-bug-bounty-intel` | **Date**: 2026-03-08

---

## File Location

```
docs/data/data.json
```

Written atomically (temp file → rename). Never partially written.

---

## Top-Level Schema

```json
{
  "meta": { ... },
  "programs": [ ... ]
}
```

## `meta` Object

```json
{
  "generated_at":          "2026-03-08T12:00:00Z",   // ISO 8601 UTC
  "programs_scanned":      2835,                       // integer ≥ 0
  "programs_failed":       12,                         // integer ≥ 0
  "total_subdomains_probed": 1200000,                  // integer ≥ 0
  "total_detections":      48312,                      // integer ≥ 0
  "scanner_version":       "1.0.0",                    // SemVer string
  "workers_used":          50                          // integer ≥ 1
}
```

## `programs` Array

Each element:
```json
{
  "name":            "HackerOne",                      // string, non-empty
  "url":             "https://hackerone.com/security", // valid HTTP/HTTPS URL
  "platform":        "HackerOne",                      // see Enum below
  "reward_type":     "paid",                           // "paid"|"free"|"self-hosted"
  "domains":         ["hackerone.com", "hackerone.net"],// string[], ≥1 element
  "technologies":    ["Grafana", "Jenkins"],            // string[], may be empty []
  "subdomain_count": 423,                              // integer ≥ 0
  "detection_count": 12,                              // integer ≥ 0
  "detections": [
    {
      "hostname":     "grafana.hackerone.com",         // valid FQDN
      "technologies": ["Grafana"],                     // string[], ≥1 element
      "http_status":  200,                             // integer | null
      "probe_error":  null                             // string | null (see Enum)
    }
  ]
}
```

## Enums

**`platform`**: `"HackerOne"` | `"Bugcrowd"` | `"Intigriti"` | `"YesWeHack"` | `"Other"`

**`reward_type`**: `"paid"` | `"free"` | `"self-hosted"`

**`probe_error`**: `null` (success) | `"timeout"` | `"dns_failed"` | `"ssl_error"` |
`"connection_refused"` | `"unknown"`

---

## Invariants

- Programs with `detection_count: 0` ARE included (program appears in list, no detections).
- Subdomains with ZERO technology detections are OMITTED from `detections` array.
- `technologies` array at program level = distinct union of all technologies across `detections`.
- `programs_scanned + programs_failed` = total programs in Chaos index (or `--limit N`).
- File MUST be valid JSON; invalid JSON is a scanner bug.
- Array ordering: programs in Chaos index order; detections alphabetical by hostname.

---

## Consumption by Frontend

The frontend loads this file via:
```javascript
const response = await fetch('./data/data.json');
const { meta, programs } = await response.json();
```

GitHub Pages serves this file with automatic gzip compression.
Expected uncompressed size: 5–15 MB. Expected gzipped size: 0.5–2 MB.
