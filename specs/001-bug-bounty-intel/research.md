# Research: StackRecon — Bug Bounty Technology Intelligence

**Branch**: `001-bug-bounty-intel` | **Phase**: 0 | **Date**: 2026-03-08

---

## RD-001: Chaos ProjectDiscovery Data Source

**Decision**: Use the `projectdiscovery/public-bugbounty-programs` GitHub repository
as the primary data source (no auth required), with optional Chaos API as a secondary
source for real-time updates.

**Rationale**: The GitHub repo (`chaos-bugbounty-list.json`) is publicly accessible
without authentication and is the source used by the majority of community tools. The
Chaos REST API (`chaos-data.projectdiscovery.io`) requires an API key (CHAOS_API_KEY
/ PDCP_API_KEY) and enforces a rate limit of 60 requests/minute.

**Spec assumption update**: The original assumption "no authentication required" holds
when using the GitHub source. If the Chaos REST API is used, a key is required.

**Index URL (public, no auth)**:
```
https://raw.githubusercontent.com/projectdiscovery/public-bugbounty-programs/main/chaos-bugbounty-list.json
```

**Index schema per program entry**:
```json
{
  "name": "HackerOne",
  "url": "https://hackerone.com/security",
  "bounty": true,
  "swag": true,
  "domains": ["hackerone.com", "hackerone.net"]
}
```

**ZIP subdomain format**: Plain-text files inside the ZIP archive, one hostname per line.
Files named after the domain (e.g., `hackerone.com.txt`) or `everything.txt`.

**Platforms covered**: HackerOne, Bugcrowd, Intigriti, YesWeHack, and community-
submitted VDP programs.

**Rate limit handling**: When using the public GitHub source, standard HTTP client
behaviour is sufficient. If switching to the Chaos REST API, implement exponential
backoff on 429 responses.

**Alternatives considered**:
- Chaos REST API directly — rejected as default due to auth requirement; supported
  as an opt-in via `--api-key` flag.

---

## RD-002: Python HTTP Scanning Library & Concurrency Model

**Decision**: asyncio + httpx ≥ 0.25 with a Semaphore-based worker pool (default 50).

**Rationale**:

| Factor | asyncio + httpx | ThreadPoolExecutor + requests |
|---|---|---|
| Memory at 50 workers | ~2–5 MB | ~100–400 MB |
| 1M requests feasibility | ✅ Single process | ⚠ Requires multi-process |
| GIL contention | None (cooperative) | High |
| Unified sync/async API | ✅ httpx | ✗ |
| Timeout granularity | connect + total | (connect, read) tuple |

**Concurrency pattern**:
```python
sem = asyncio.Semaphore(config.workers)   # caps active probes
limits = httpx.Limits(max_connections=config.workers,
                      max_keepalive_connections=config.workers // 2)
async with httpx.AsyncClient(limits=limits) as client:
    tasks = [bounded_probe(client, sem, sd) for sd in subdomains]
    await asyncio.gather(*tasks)
```

**Timeout values**:
- Connect: 3 s (DNS + TCP; dead hosts fail fast)
- Total: 10 s (hard ceiling; prevents indefinite hangs)

**User-Agent**: `StackRecon/1.0 (subdomain tech scanner; +https://github.com/YOUR_USERNAME/stackrecon)`

**Error categories & handling**:
- `TimeoutError` → log + skip; retry once with backoff
- `ConnectError` / DNS failure → log + skip; no retry
- SSL error → log + skip (certificate issues are common in bug bounty scope)
- HTTP 4xx/5xx → valid response; analyze headers/body for fingerprints
- Never crash on per-subdomain errors; crash only on: source unavailable, disk full.

**Estimated throughput at 50 workers**: ~50–100 subdomains/second → full 1.2M run
takes approximately 3–6 hours. The `--limit N` flag makes development runs feasible.

**Alternatives considered**:
- aiohttp — good but async-only; httpx offers cleaner API.
- requests + ThreadPoolExecutor — GIL contention makes it impractical at 1M scale.

---

## RD-003: Technology Fingerprinting

**Decision**: YAML-based signature database (`signatures/technologies.yaml`), loaded
at startup, regex-compiled in memory. Hybrid detection modes: offline (ZIP subdomain
lists only) and live HTTP (single GET per subdomain for configured technologies).

**Signature structure** (reference: Wappalyzer format, simplified):
```yaml
- id: "grafana"
  name: "Grafana"
  category: "Monitoring/Analytics"
  live_probe_required: false
  signals:
    headers:
      - name: "Server"
        pattern: "(?i)grafana"
        confidence: 0.95
    html:
      - selector: "title"
        pattern: "^Grafana"
        confidence: 0.95
      - type: "meta"
        name: "application-name"
        value: "Grafana"
        confidence: 0.90
    paths:
      - path: "/api/health"
        patterns: ["version"]
        confidence: 0.80
  version_patterns:
    - header: "Server"
      regex: "grafana/([\\d.]+)"
  min_confidence_threshold: 0.60
```

**Detection signals ranked by reliability**:
1. Dedicated headers (X-Jenkins, X-Elastic-Product): 95–99% confidence
2. `<title>` tag exact/regex match: 90–95%
3. `<meta name="generator">` tag: 95–99% when present
4. HTML body patterns (form IDs, class names, JS paths): 75–90%
5. Known URL path responses (e.g., `/metrics`, `/api/v1/query`): 80–95%
6. Generic `Server` / `X-Powered-By` headers: 80–95%

**Technologies requiring live probing** (cannot be reliably detected from subdomain
lists alone): Jenkins, Keycloak, Prometheus, Grafana, Kibana, Elasticsearch, GitLab.

**Technologies detectable offline** (from Chaos ZIP metadata/DNS records): WordPress
(common in static data), generic CDN providers.

**Reference databases**: Wappalyzer (MIT), WhatWeb (GPL-2.0), Nuclei Templates (MIT).
Signatures will be written from scratch referencing these; no code copied.

**Alternatives considered**:
- Python classes per technology — rejected; harder to maintain and contribute to.
- Wappalyzer JSON format directly — too complex; YAML subset is sufficient for 47 techs.

---

## RD-004: Frontend Data Architecture

**Decision**: Single `data.json` file (scanner output) for datasets ≤ 15 MB
(uncompressed); split into `data/index.json` + `data/programs-NNN.json` chunks
for larger datasets. GitHub Pages serves gzip automatically (85–90% reduction).

**Estimated output size**: Only subdomains with at least one technology detection
are included in the JSON (not all 1.2M). Estimate ~45k detection entries at ~150
bytes each → ~7 MB uncompressed → ~1 MB gzipped. Single file is sufficient.

**Client-side filtering** (target: <500 ms):
```javascript
// Built once after data loads — O(n) build, O(1) lookup
const techIndex = new Map();  // tech name → [program indices]
const platformIndex = new Map();
const rewardIndex = new Map();

// Filter: AND intersection of active filter sets
function filterPrograms(filters) {
  let result = null;
  if (filters.technology) result = intersect(result, techIndex.get(filters.technology));
  if (filters.platform)   result = intersect(result, platformIndex.get(filters.platform));
  if (filters.reward)     result = intersect(result, rewardIndex.get(filters.reward));
  if (filters.name)       result = nameSearch(result, filters.name);
  return (result ? [...result] : allIndices).map(i => programs[i]);
}
```

**UI design**: CSS custom properties, deep-blue backgrounds (#0a0e27, #151b34),
neon accent (#00ff88 green, #00d4ff cyan), monospace data font. WCAG 2.1 AA compliant
(contrast ratio ≥ 4.5:1 for all text).

**GitHub Pages deployment**: `/docs` folder — native support, no GitHub Actions
required. Scanner writes output to `docs/data/data.json`.

**Alternatives considered**:
- Chunked JSON files (5–20 files, parallel load) — reserved for if dataset grows
  beyond 15 MB; not needed at current estimated size.
- Build step (webpack, Vite) — rejected; no build step is a hard constraint for
  GitHub Pages without CI.
