# Implementation Plan: StackRecon — Bug Bounty Technology Intelligence

**Branch**: `001-bug-bounty-intel` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-bug-bounty-intel/spec.md`

## Summary

StackRecon is a two-component system: (1) a Python CLI scanner that fetches all public
bug bounty programs from Chaos ProjectDiscovery, extracts subdomain lists from ZIP files,
detects 47+ technologies via a hybrid offline/live-probe approach, and writes results
atomically to `data.json`; and (2) a GitHub Pages static site that loads `data.json`
and provides client-side filtering by technology, platform, reward type, and program name.

## Technical Context

**Language/Version**: Python 3.11+ (scanner) · HTML5/CSS3/ES2022 (frontend, no build step)
**Primary Dependencies**: httpx ≥ 0.25 (async HTTP probing) · PyYAML ≥ 6.0 (signature DB) · aiofiles ≥ 23.0 (async file I/O) · no frontend dependencies (Vanilla JS)
**Storage**: `docs/data/data.json` (flat file, atomic write) · `signatures/technologies.yaml` (static config)
**Testing**: pytest + pytest-asyncio (scanner unit + integration) · contract tests against live Chaos source
**Target Platform**: Linux/macOS (scanner) · GitHub Pages static hosting (frontend, `/docs` folder)
**Project Type**: CLI tool (scanner) + static web app (frontend)
**Performance Goals**: UI filter < 500 ms · page load < 3 s on broadband · `--limit 10` < 5 min
**Constraints**: No server runtime for frontend · default 50 workers · atomic output write · 3 s connect / 7 s read timeout defaults
**Scale/Scope**: ~2,847 programs · ~1.2M subdomains · 47+ technologies · ~5–15 MB output JSON (uncompressed)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Code Quality ✅

- Scanner split into modules with single responsibility: `fetcher`, `extractor`,
  `detector`, `classifier`, `writer`, `models`, `config`. No module expected to exceed
  400 lines.
- Linting (ruff) and formatting (black) configured in CI from day one.
- Meaningful module and function names; no abbreviation-only identifiers.
- `detector.py` pattern matching uses compiled regex (no re-compilation per call).
  Cyclomatic complexity of the probe loop capped by Semaphore + `asyncio.gather`.

### II. Testing Standards ✅

- TDD: tests written and confirmed failing before each module is implemented.
- 80% coverage floor enforced via `pytest --cov` in CI.
- Test pyramid:
  - **Unit**: `detector`, `classifier`, `writer`, `models` — mocked HTTP, mocked ZIP
  - **Integration**: full scanner pipeline on 3-program fixture data
  - **Contract**: Chaos index format validation against live source
- Unit tests use no network; all HTTP stubbed via `respx` (httpx mock library).

### III. User Experience Consistency ✅

- All scanner CLI errors use the format `[ERROR] <context>: <reason> — <action>`.
- All scanner warnings use `[WARN] <context>: <reason> — <action>`.
- Frontend: CSS custom properties define all colors; dark theme consistent throughout.
- Loading spinner visible within 100 ms of page load (per UI contract).
- Filter "No results" empty state with "Clear filters" CTA.
- Error banner with "Retry" button when `data.json` fails to load.
- WCAG 2.1 AA: contrast ≥ 4.5:1; all interactive elements keyboard-navigable.

### IV. Performance Requirements ✅

- Client-side filtering uses pre-built inverted indices (Map → O(1) lookup); 2,847
  items filter in < 10 ms; well within 500 ms target.
- `data.json` estimated 5–15 MB uncompressed, < 2 MB gzipped via GitHub Pages CDN;
  page loads within 3 s on 10 Mbps connection.
- Scanner: no O(n²) complexity; subdomain probing is bounded by Semaphore(workers).
- No unbounded memory growth: programs streamed and written progressively to temp
  file during scan (not accumulated in memory until write time).

**Violations requiring justification**: None. Design is fully compliant.

## Project Structure

### Documentation (this feature)

```text
specs/001-bug-bounty-intel/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── cli-contract.md
│   ├── data-json-contract.md
│   └── ui-components-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
scanner/
├── main.py                  # CLI entry point; argparse → ScanConfig → orchestrator
├── requirements.txt         # httpx, PyYAML, aiofiles
└── src/
    ├── __init__.py
    ├── config.py            # ScanConfig dataclass + CLI arg parsing
    ├── models.py            # Program, Subdomain, Technology, ScanRun dataclasses
    ├── fetcher.py           # Fetch Chaos index JSON + download/cache program ZIPs
    ├── extractor.py         # Extract subdomain lists from ZIP archives
    ├── detector.py          # Hybrid technology detection engine (offline + live probe)
    ├── classifier.py        # Derive platform + reward_type from program metadata
    └── writer.py            # Atomic JSON writer (temp file → rename)

signatures/
└── technologies.yaml        # 47+ technology signature definitions

tests/
├── conftest.py              # Shared fixtures (mock Chaos index, fixture ZIPs, respx mocks)
├── unit/
│   ├── test_config.py       # CLI arg parsing, validation
│   ├── test_models.py       # Dataclass construction, serialisation
│   ├── test_fetcher.py      # Chaos fetch logic (mocked HTTP)
│   ├── test_extractor.py    # ZIP extraction (in-memory fixture ZIPs)
│   ├── test_detector.py     # Signature matching against fixture responses
│   ├── test_classifier.py   # reward_type + platform derivation rules
│   └── test_writer.py       # Atomic write, abort-safety, JSON validity
├── integration/
│   └── test_pipeline.py     # End-to-end scan of 3-program fixture; validates data.json
└── contract/
    └── test_chaos_source.py # Verify Chaos index JSON matches expected schema (live)

docs/
├── index.html               # Single-page app shell
├── css/
│   └── style.css            # CSS custom properties, dark theme, layout
├── js/
│   ├── app.js               # Entry point: fetch data.json, build indices, wire events
│   ├── filters.js           # Inverted index build + filter/intersection logic
│   ├── components.js        # ProgramCard, TechBadge, PlatformBadge, RewardBadge,
│   │                        #   LoadingSpinner, EmptyState, ErrorBanner
│   └── search.js            # Name search with debounce
└── data/
    └── .gitkeep             # data.json written here by scanner; gitignored if large
```

**Structure Decision**: Mixed layout — separate `scanner/` for Python CLI and `docs/`
for GitHub Pages static site. No shared runtime between them; `data.json` is the only
interface. This avoids a monorepo build-step while keeping both components in one repo.

## Complexity Tracking

> No violations — all constitution gates pass. Table intentionally empty.
