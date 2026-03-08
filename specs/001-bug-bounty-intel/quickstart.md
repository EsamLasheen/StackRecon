# Quickstart: StackRecon

**Branch**: `001-bug-bounty-intel` | **Date**: 2026-03-08

---

## Prerequisites

- Python 3.11 or later
- Git

---

## 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/stackrecon
cd stackrecon
pip install -r scanner/requirements.txt
```

**Expected `scanner/requirements.txt`**:
```
httpx>=0.25.0
PyYAML>=6.0
aiofiles>=23.0
```

---

## 2. Test the Scanner (10 Programs)

```bash
cd scanner
python main.py --limit 10
```

**Expected output** (stdout):
```
[2026-03-08 12:00:01] [1/10] HackerOne — 423 subdomains, 12 detections
[2026-03-08 12:00:03] [2/10] Bugcrowd — 212 subdomains, 5 detections
...
[2026-03-08 12:01:30] Scan complete: 10 programs, 0 failed, 53 detections total
Output written to: ../docs/data/data.json
```

**Acceptance check**: `docs/data/data.json` exists and is valid JSON:
```bash
python -c "import json; d=json.load(open('../docs/data/data.json')); print(f'{len(d[\"programs\"])} programs')"
# Expected: 10 programs
```

---

## 3. Run a Full Scan

```bash
python main.py
# Uses default: 50 workers, all programs, output to ../docs/data/data.json
```

Estimated runtime: 3–6 hours for the full ~2,847 programs.

**Advanced options**:
```bash
python main.py --workers 100 --connect-timeout 5 --limit 50
python main.py --api-key YOUR_CHAOS_KEY   # uses Chaos REST API instead of GitHub
```

---

## 4. View the Web Interface Locally

Open `docs/index.html` directly in a browser. Because data is loaded via `fetch()`,
you need a local HTTP server to avoid CORS issues:

```bash
cd docs
python -m http.server 8080
# Open http://localhost:8080
```

**Acceptance check**: Page loads, technology filter dropdown is populated, selecting
"Grafana" shows programs with Grafana detections.

---

## 5. Deploy to GitHub Pages

1. Push changes to `main` branch.
2. In repo Settings → Pages → Deploy from branch → `main` → `/docs` folder.
3. Access at `https://YOUR_USERNAME.github.io/stackrecon`

**Acceptance check**: Live site loads within 3 seconds; filters work client-side
without page reload.

---

## Validation Steps (from spec Success Criteria)

| SC | Check | Pass Condition |
|---|---|---|
| SC-001 | Filter by technology | Results visible within 5 s of page load |
| SC-002 | Full scan completion rate | `programs_failed / programs_scanned < 5%` |
| SC-003 | Page load time | Full render < 3 s on broadband |
| SC-004 | Filter response time | Filter update < 500 ms (check DevTools) |
| SC-005 | `--limit 10` runtime | Completes in < 5 minutes |
| SC-006 | Technology coverage | `data.json` contains ≥ 47 distinct technology names |

```bash
# SC-006 validation:
python -c "
import json
from itertools import chain
d = json.load(open('docs/data/data.json'))
techs = set(chain.from_iterable(p['technologies'] for p in d['programs']))
print(f'{len(techs)} distinct technologies: {sorted(techs)[:10]}...')
assert len(techs) >= 47, 'SC-006 FAIL: fewer than 47 technologies detected'
print('SC-006 PASS')
"
```
