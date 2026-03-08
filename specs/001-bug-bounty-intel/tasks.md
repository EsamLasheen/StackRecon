---
description: "Task list for StackRecon — Bug Bounty Technology Intelligence"
---

# Tasks: StackRecon — Bug Bounty Technology Intelligence

**Input**: Design documents from `specs/001-bug-bounty-intel/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅ quickstart.md ✅

**Tests**: Included — Constitution Principle II mandates TDD (tests written and failing before implementation). Test tasks are marked within each story phase.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- File paths are relative to repo root

---

## Phase 1: Setup

**Purpose**: Create project scaffold, configs, and fixture data needed before any story work begins.

- [x] T001 Create full directory structure: `scanner/src/`, `docs/css/`, `docs/js/`, `docs/data/`, `signatures/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [x] T002 [P] Create `scanner/requirements.txt` with: `httpx>=0.25.0`, `PyYAML>=6.0`, `aiofiles>=23.0`, `pytest>=7.0`, `pytest-asyncio>=0.23`, `respx>=0.20`, `pytest-cov>=4.0`, `ruff>=0.3`, `black>=24.0`
- [x] T003 [P] Create `pyproject.toml` with `[tool.pytest.ini_options]` (asyncio_mode = "auto", testpaths = ["tests"]), `[tool.ruff]` (line-length = 100, select = ["E","F","I"]), `[tool.black]` (line-length = 100, target-version = ["py311"])
- [x] T004 [P] Create `docs/data/fixture_data.json` — 5-program fixture dataset (HackerOne with Grafana+Jenkins detections, Bugcrowd with WordPress, Intigriti with Keycloak, YesWeHack with Prometheus, one program with zero detections) matching the `data-json-contract.md` schema exactly

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: HTML/CSS shell (blocks US1+US2) and scanner base models/config/signatures (blocks US3). All are blocking — no user story work begins until this phase is complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create `docs/index.html` — HTML5 shell: `<head>` with charset, viewport, title "StackRecon", link to `css/style.css`; `<body>` with `<header>` (site title, subtitle), `<main>` containing `<section id="filter-panel">` (placeholder divs for each filter), `<div id="stats-bar">`, `<div id="results-container">`; `<script>` tags at body end loading `js/filters.js`, `js/components.js`, `js/search.js`, `js/app.js` in that order
- [x] T006 [P] Create `docs/css/style.css` — CSS custom properties in `:root`: `--bg-primary: #0a0e27`, `--bg-secondary: #151b34`, `--bg-tertiary: #1f2847`, `--text-primary: #e4e8f5`, `--text-secondary: #9ca3af`, `--accent-primary: #00ff88`, `--accent-secondary: #00d4ff`, `--accent-danger: #ff3860`, `--border-color: #2d3748`, `--font-mono`, `--font-sans`; dark body base; CSS grid layout (sidebar filters 280px + main results flex-grow); card, badge, input base styles; focus-visible ring using `--accent-primary`; WCAG-compliant contrast for all text/background pairs
- [x] T007 [P] Create `tests/conftest.py` — shared pytest fixtures: `fixture_programs` (list of 3 Program dicts matching data-model.md schema), `fixture_chaos_index` (list of 3 program index dicts with name/url/bounty/swag/domains), `fixture_zip_bytes(subdomains: list[str])` factory that builds an in-memory ZIP with a `everything.txt` file, `fixture_config` (ScanConfig with workers=5, limit=3, connect_timeout=3, read_timeout=7, output="tests/tmp/data.json")
- [x] T008 [P] Write `tests/unit/test_models.py` — **WRITE FIRST, confirm FAIL**: test `Program` dataclass construction with all fields; test `to_dict()` produces keys matching data-json-contract.md (name, url, platform, reward_type, domains, technologies, subdomain_count, detection_count, detections); test `ScanRun.to_dict()` produces meta-schema keys; test JSON round-trip (json.dumps(program.to_dict()) → json.loads → Program.from_dict()); test `platform` enum enforcement
- [x] T009 Create `scanner/src/models.py` — implement `Program`, `Subdomain`, `ScanRun` dataclasses with all fields from `data-model.md`; `to_dict()` → JSON-serializable dict per `data-json-contract.md`; `from_dict()` classmethod; platform enum as string constant (not Python Enum to keep JSON-serializable); run `pytest tests/unit/test_models.py` and confirm **PASS**
- [x] T010 [P] Write `tests/unit/test_config.py` — **WRITE FIRST, confirm FAIL**: test default values (`workers=50`, `limit=None`, `connect_timeout=3`, `read_timeout=7`, `output="docs/data/data.json"`); test `--workers 0` raises SystemExit; test `--workers 501` raises SystemExit; test `--connect-timeout 31` raises SystemExit; test `--limit 10` sets `limit=10`; test `--api-key` sets `api_key` field
- [x] T011 [P] Create `scanner/src/config.py` — `ScanConfig` dataclass with all fields; `parse_cli_args() -> ScanConfig` using argparse with all flags from `cli-contract.md` (`--workers`, `--limit`, `--connect-timeout`, `--read-timeout`, `--output`, `--api-key`); validation: workers 1–500, connect-timeout 1–30; run `pytest tests/unit/test_config.py` and confirm **PASS**
- [x] T012 [P] Create `signatures/technologies.yaml` — 47+ technology signatures in YAML format per `research.md RD-003` structure; MUST include: Grafana, Jenkins, Keycloak, WordPress, GitLab, Jira, Confluence, Kibana, Prometheus, Elasticsearch, Nginx, Apache, Tomcat, Spring Boot, Django, Ruby on Rails, Laravel, Drupal, Magento, Shopify, Cloudflare, Fastly, AWS ALB, Traefik, HAProxy, HashiCorp Vault, Consul, Nomad, etcd, RabbitMQ, Redis (HTTP API), MinIO, Portainer, Rancher, ArgoCD, GoCD, TeamCity, Bamboo, SonarQube, Nexus Repository, Harbor, Gitea, Gogs, Bitbucket Server, phpMyAdmin, Roundcube; each signature has: `id`, `name`, `category`, `live_probe_required` (bool), `min_confidence_threshold` (float), `signals.headers[]`, `signals.html[]`, `signals.paths[]`; at least 7 must have `live_probe_required: true` (Grafana, Jenkins, Keycloak, Kibana, Prometheus, Elasticsearch, GitLab)

**Checkpoint**: Foundation ready — US1+US2 (frontend) and US3 (scanner) can now proceed in parallel

---

## Phase 3: User Story 1 — Technology Filter UI (Priority: P1) 🎯 MVP

**Goal**: A user can load the site, see all programs with their technology badges, and filter by technology to find relevant targets.

**Independent Test**: Serve `docs/` via `python -m http.server 8080`, open `http://localhost:8080`, select "Grafana" from the technology dropdown — only the programs with Grafana detections from `fixture_data.json` appear.

- [x] T013 [P] [US1] Create `docs/js/components.js` — implement `LoadingSpinner(message)` returns `<div class="loading-spinner">` with animated indicator and message text; `EmptyState(message, onClearFilters)` returns `<div class="empty-state">` with message and "Clear filters" `<button>` wired to `onClearFilters`; `ErrorBanner(message, onRetry)` returns `<div class="error-banner" role="alert">` with `--accent-danger` styling, message, and "Retry" button
- [x] T014 [P] [US1] Create `docs/js/filters.js` — `buildTechIndex(programs)` iterates programs and returns `Map<string, Set<number>>` (tech name → Set of program indices); `getAllTechnologies(programs)` returns sorted `string[]` of all distinct technology names across all programs; `filterByTech(techIndex, techName)` returns `Set<number>` of matching program indices; `intersect(setA, setB)` returns new `Set` containing only elements in both; all functions exported on `window.stackrecon.filters`
- [x] T015 [US1] Create `docs/js/app.js` — `async fetchData()`: show `LoadingSpinner` on `#results-container`, `fetch('./data/fixture_data.json')` (replace with `'./data/data.json'` once scanner produces it), parse JSON, hide spinner, call `buildIndices(data.programs)`, call `renderResults(allPrograms, null)`; on fetch failure (network error or non-200): replace spinner with `ErrorBanner("Failed to load program data.", () => fetchData())`; expose `window.stackrecon = { programs: [], indices: {}, activeFilters: {} }`; call `fetchData()` on `DOMContentLoaded`
- [x] T016 [US1] Extend `docs/js/components.js` — add `ProgramCard(program, activeTech)`: returns `<div class="program-card">` containing `<h3>` (program name), `<div class="card-meta">` (subdomain_count, detection_count), `<div class="tech-badges">` (one `TechBadge` per technology in `program.technologies`); if `activeTech` set, highlight matching badge with `active=true`; card has `data-program-name` attr; on click expands `<ul class="detections-list">` showing hostnames with detected techs (filtered to `activeTech` if set)
- [x] T017 [US1] Extend `docs/js/components.js` — add `TechBadge(techName, active)`: returns `<span class="badge tech-badge" data-tech="[techName]">`; `active=false` → outlined style (border `--accent-primary`, color `--accent-primary`); `active=true` → filled style (background `--accent-primary`, color `--bg-primary`); font: `--font-mono`
- [x] T018 [US1] Extend `docs/index.html` — in `#filter-panel`: add `<label for="tech-filter">Technology</label>` + `<select id="tech-filter"><option value="">All technologies</option></select>` (options populated by JS); add `<div id="stats-bar" role="status" aria-live="polite">` showing "Showing N of N programs"; add `<div id="results-container" role="main">`
- [x] T019 [US1] Extend `docs/js/app.js` — `renderResults(programs, activeTech)`: clear `#results-container`, append `ProgramCard(p, activeTech)` for each program, update `#stats-bar` text; `initTechFilter()`: call `getAllTechnologies(programs)`, populate `#tech-filter` select options, wire `onchange` → `filterByTech(techIndex, value)` → `renderResults(matchingPrograms, value)`; on zero results show `EmptyState("No programs found running [tech]. Try another.", clearAllFilters)`; call `initTechFilter()` after `fetchData()` resolves

**Checkpoint**: US1 complete — technology filter works with fixture data; independently testable without scanner

---

## Phase 4: User Story 2 — Platform, Reward, and Name Filters (Priority: P2)

**Goal**: Users can combine technology filter with platform, reward type, and name search using AND logic; filter state is URL-shareable.

**Independent Test**: Open site, type "hacker" in name search, select "Paid" reward, see only HackerOne-matching paid programs — without technology filter being active.

- [x] T020 [P] [US2] Extend `docs/js/components.js` — add `PlatformBadge(platform)`: returns `<span class="badge platform-badge">` with `--text-secondary` color, uppercase small caps, no border; add `RewardBadge(rewardType)`: returns `<span class="badge reward-badge">`; `paid` → color `--accent-primary`; `free` → color `--accent-secondary`; `self-hosted` → color `--text-secondary`; integrate both into `ProgramCard` render (add to `<div class="card-meta">`)
- [x] T021 [P] [US2] Create `docs/js/search.js` — `debounce(fn, delayMs)` returns debounced wrapper; `nameSearch(allPrograms, query, minChars = 2)` returns filtered `number[]` of program indices where `program.name.toLowerCase().includes(query.toLowerCase())` (returns all indices if `query.length < minChars`); `readFiltersFromHash()` parses `window.location.hash` (format `#tech=Grafana&platform=HackerOne&reward=paid&name=foo`) → `{tech, platform, reward, name}` object (missing keys = empty string); `writeFiltersToHash(filters)` updates `window.location.hash` from filter object; export on `window.stackrecon.search`
- [x] T022 [US2] Extend `docs/js/filters.js` — add `buildPlatformIndex(programs)` → `Map<string, Set<number>>`; `buildRewardIndex(programs)` → `Map<string, Set<number>>`; add `applyAllFilters(state)`: takes `{techIndex, platformIndex, rewardIndex, programs, activeFilters}`, applies AND intersection across all non-empty active filters (tech → platform → reward → name), returns `number[]` of matching program indices; update `buildIndices()` call in `app.js` to also build platform and reward indices
- [x] T023 [US2] Extend `docs/index.html` — in `#filter-panel` add (each with `<label>`): `<select id="platform-filter">` (options: All, HackerOne, Bugcrowd, Intigriti, YesWeHack, Other); `<select id="reward-filter">` (options: All, Paid, Free, Self-Hosted); `<input type="text" id="name-search" placeholder="Search programs...">` with debounce; add `<button id="clear-filters">Clear all filters</button>`; ensure all inputs have explicit `<label for="...">` per WCAG
- [x] T024 [US2] Update `docs/js/components.js` `ProgramCard` — PlatformBadge and RewardBadge already integrated in T020; verify `ProgramCard` uses `program.platform` and `program.reward_type` fields correctly; ensure card shows platform badge and reward badge in `<div class="card-meta">` alongside subdomain count
- [x] T025 [US2] Extend `docs/js/app.js` — wire `#platform-filter` onchange, `#reward-filter` onchange, `#name-search` oninput (debounced 200ms) → all call `applyAllFilters(state)` then `renderResults(matchingPrograms, state.activeFilters.tech)`; update `#stats-bar` count; wire `#clear-filters` button to reset all `<select>` to index 0, clear name input, set `activeFilters = {}`, call `renderResults(allPrograms, null)`, call `writeFiltersToHash({})`; on page load call `readFiltersFromHash()` and restore filter state before first render

**Checkpoint**: US2 complete — all 4 filters combinable; URL hash preserves state; "Clear all filters" resets correctly

---

## Phase 5: User Story 3 — CLI Scanner (Priority: P3)

**Goal**: Maintainer runs `python main.py --limit 10` and gets a valid `data.json` the UI can consume.

**Independent Test**: `cd scanner && python main.py --limit 10` completes in < 5 min, exits 0, produces `docs/data/data.json` that passes `python -c "import json; d=json.load(open('../docs/data/data.json')); assert len(d['programs'])==10"`

### Tests for US3 (TDD — write these FIRST, confirm FAIL before implementing) ⚠️

- [x] T026 [P] [US3] Write `tests/unit/test_fetcher.py` — **WRITE FIRST, confirm FAIL**: test `fetch_program_index(config)` with `respx.mock` returning fixture chaos index JSON → asserts list of program dicts returned; test raises `SourceUnavailableError` on `httpx.ConnectError`; test raises `SourceUnavailableError` on non-200 response; test `download_zip(url, config)` returns `bytes` on 200; test `download_zip` logs warning and returns `None` on 404
- [x] T027 [P] [US3] Write `tests/unit/test_extractor.py` — **WRITE FIRST, confirm FAIL**: test `extract_subdomains(zip_bytes, "program")` with `fixture_zip_bytes(["a.example.com","b.example.com"])` → returns `["a.example.com","b.example.com"]`; test with multi-file ZIP (two .txt files) merges and deduplicates; test with malformed bytes returns `[]` and does not raise; test hostnames are stripped of whitespace and empty lines removed
- [x] T028 [P] [US3] Write `tests/unit/test_classifier.py` — **WRITE FIRST, confirm FAIL**: test `derive_platform({"url":"https://hackerone.com/..."})` → `"HackerOne"`; test Bugcrowd, Intigriti, YesWeHack URL patterns; test unknown URL → `"Other"`; test `derive_reward_type({"bounty": True})` → `"paid"`; test `{"bounty": False, "url": "...hackerone..."}` → `"free"`; test self-hosted URL patterns → `"self-hosted"`
- [x] T029 [P] [US3] Write `tests/unit/test_detector.py` — **WRITE FIRST, confirm FAIL**: test `load_signatures("signatures/technologies.yaml")` returns list with ≥ 47 items, each having `id`, `name`, `live_probe_required`; test `detect_offline(headers={}, body="<title>Grafana</title>", signature=grafana_sig)` → confidence ≥ 0.60; test confidence below threshold returns no detection; test `probe_subdomain` with `respx.mock` returning 200 + Grafana body → detections include "Grafana"; test `probe_subdomain` on `httpx.TimeoutException` → returns ProbeResult with `probe_error="timeout"`
- [x] T030 [P] [US3] Write `tests/unit/test_writer.py` — **WRITE FIRST, confirm FAIL**: test `write_atomic(data_dict, tmp_path/"data.json")` creates valid JSON file; test content matches data_dict on round-trip; test when rename fails (mock `os.rename` to raise `OSError`) → existing `data.json` untouched, `SystemExit(3)` raised; test no temp file remains after success; test `write_atomic` with large dict (stress-test JSON validity)
- [x] T031 [US3] Write `tests/integration/test_pipeline.py` — **WRITE FIRST, confirm FAIL**: end-to-end test using `fixture_config` + `fixture_chaos_index` + `fixture_zip_bytes`; mock Chaos HTTP with `respx`; mock subdomain probe responses with Grafana body for one subdomain; call `asyncio.run(main_pipeline(config))`; assert `data.json` file exists; assert `json.load(data.json)["programs"]` has 3 entries; assert `meta.programs_scanned == 3`; assert HackerOne entry has `"Grafana"` in technologies; assert `meta.total_detections >= 1`
- [x] T032 [US3] Write `tests/contract/test_chaos_source.py` — schema contract test marked `@pytest.mark.network`: fetch `https://raw.githubusercontent.com/projectdiscovery/public-bugbounty-programs/main/chaos-bugbounty-list.json`; assert response 200; assert top-level is a list; assert first 5 entries each have: `"name"` (str), `"url"` (str), `"bounty"` (bool), `"swag"` (bool), `"domains"` (list with ≥1 str element); add `@pytest.mark.skip(reason="requires network")` decorator so CI skips by default

### Implementation for US3 (make tests pass)

- [x] T033 [P] [US3] Implement `scanner/src/fetcher.py` — define `SourceUnavailableError(Exception)`; `async fetch_program_index(config: ScanConfig) -> list[dict]`: use `httpx.AsyncClient` with 10s timeout; if `config.api_key` set use Chaos REST API URL with `Authorization: Bearer {key}` header; else use GitHub raw URL; raise `SourceUnavailableError` on `ConnectError` or status != 200; `async download_zip(url: str, config: ScanConfig) -> bytes | None`: GET with 30s timeout; return `response.content` on 200; log `[WARN]` and return `None` on non-200; run `pytest tests/unit/test_fetcher.py` → **PASS**
- [x] T034 [P] [US3] Implement `scanner/src/extractor.py` — `extract_subdomains(zip_bytes: bytes, program_name: str) -> list[str]`: `zipfile.ZipFile(io.BytesIO(zip_bytes))`; read all `.txt` member files; split by newline; strip whitespace; filter empty strings; deduplicate with `set()`; sort; return list; on `zipfile.BadZipFile` or any exception: log `[WARN] {program_name}: malformed ZIP — skipping subdomain extraction`; return `[]`; run `pytest tests/unit/test_extractor.py` → **PASS**
- [x] T035 [P] [US3] Implement `scanner/src/classifier.py` — `derive_platform(program: dict) -> str`: map URL host patterns to platform strings (hackerone.com → "HackerOne", bugcrowd.com → "Bugcrowd", intigriti.com → "Intigriti", yeswehack.com → "YesWeHack"); default "Other"; `derive_reward_type(program: dict) -> str`: `bounty == True` → "paid"; `bounty == False` and URL matches known platform → "free"; URL matches self-hosted pattern list → "self-hosted"; default "free"; run `pytest tests/unit/test_classifier.py` → **PASS**
- [x] T036 [US3] Implement `scanner/src/detector.py` — `load_signatures(yaml_path: str) -> list[TechSignature]`: `yaml.safe_load()`, compile all regex patterns at load time (fail fast on invalid regex); `TechSignature` dataclass with id, name, live_probe_required, min_confidence_threshold, compiled signals; `detect_offline(headers: dict, body: str, sig: TechSignature) -> float`: apply header patterns + HTML patterns; return max matched confidence or 0.0; `async probe_subdomain(client, sem, hostname, live_sigs, config) -> ProbeResult`: acquire semaphore; `client.get(f"http://{hostname}", timeout=httpx.Timeout(config.read_timeout, connect=config.connect_timeout), follow_redirects=True, max_redirects=5)`; classify exceptions into ErrorCategory; `async detect_all(subdomains, signatures, config) -> dict[str, list[str]]`: partition signatures by live_probe_required; run offline detection first; run live probing via `asyncio.gather(*[probe(...) for sd in live_candidates])` with semaphore; merge results; run `pytest tests/unit/test_detector.py` → **PASS**
- [x] T037 [US3] Implement `scanner/src/writer.py` — `write_atomic(data: dict, output_path: str)`: compute `tmp_path = output_path + ".tmp"`; `json.dumps(data, indent=2)` to tmp file; `os.rename(tmp_path, output_path)` (atomic on same filesystem); on `OSError`: log `[ERROR] write failed: {e} — output file unchanged`; `sys.exit(3)`; ensure tmp file cleaned up on error via try/finally; run `pytest tests/unit/test_writer.py` → **PASS**
- [x] T038 [US3] Implement `scanner/main.py` — `async main_pipeline(config: ScanConfig)`: `fetch_program_index(config)` (catch `SourceUnavailableError` → `print(f"[ERROR] ...", file=sys.stderr)` → `sys.exit(1)`); slice programs to `config.limit`; for each program: `download_zip()` (skip if None, increment `programs_failed`); `extract_subdomains()`; `detect_all(subdomains, signatures, config)`; `classify`; build `Program` dataclass; `print(f"[{timestamp}] [{i}/{total}] {name} — {n} subdomains, {detections} detections")`; `write_atomic(output_dict, config.output)` after loop; handle `KeyboardInterrupt`: print `[WARN] Scan interrupted — output file unchanged`, exit 0; `if __name__ == "__main__": asyncio.run(main_pipeline(parse_cli_args()))`
- [x] T039 [US3] Run all unit tests and verify coverage: `cd scanner && pytest ../tests/unit/ --cov=src --cov-report=term-missing` — confirm all tests PASS and coverage ≥ 80% on all modules
- [x] T040 [US3] Run integration test: `pytest tests/integration/test_pipeline.py -v` — confirm end-to-end pipeline PASS with fixture data; inspect produced `data.json` to confirm schema matches `data-json-contract.md`
- [x] T041 [US3] Run scanner acceptance test (SC-005): `cd scanner && time python main.py --limit 10 --output ../docs/data/data.json` — confirm exits 0, completes in < 5 min; run `python -c "import json; d=json.load(open('../docs/data/data.json')); assert len(d['programs'])==10; print('OK')"` to confirm valid output
- [x] T042 [US3] Run SC-006 validation from `quickstart.md`: `python -c "import json; from itertools import chain; d=json.load(open('docs/data/data.json')); techs=set(chain.from_iterable(p['technologies'] for p in d['programs'])); assert len(techs)>=47, f'Only {len(techs)} technologies'; print(f'SC-006 PASS: {len(techs)} technologies')"` against full-scan output (or --limit 100 run)

**Checkpoint**: US3 complete — scanner produces valid data.json; all unit, integration tests pass; SC-005 confirmed

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Accessibility, CI, final validation, and deployment readiness.

- [x] T043 [P] WCAG accessibility pass on `docs/index.html` + `docs/css/style.css`: add `role="main"` to results section; add `role="status" aria-live="polite"` to `#stats-bar`; add `aria-label` to icon-only buttons; verify all `<select>` and `<input>` have matching `<label for="...">`; use DevTools contrast checker to confirm ≥ 4.5:1 on all text/background pairs; add `:focus-visible` outline to all interactive elements using `--accent-primary` color
- [x] T044 [P] Create `.github/workflows/ci.yml` — trigger on `push` to any branch + `pull_request` to `main`; job `lint-and-test`: `runs-on: ubuntu-latest`; steps: checkout, `pip install -r scanner/requirements.txt`; `ruff check scanner/src`; `black --check scanner/src`; `pytest tests/unit/ tests/integration/ --cov=scanner/src --cov-fail-under=80 -v`; skip contract tests (add `-m "not network"` marker); upload coverage report as artifact
- [ ] T045 Run full quickstart.md validation: serve `docs/` via `python -m http.server 8080`, open browser DevTools, load page, measure DOMContentLoaded (SC-003: < 3 s); apply tech filter, measure response time (SC-004: < 500 ms); verify SC-001 (find tech targets < 5 s); verify SC-002 from scan run stats (programs_failed / programs_scanned < 5%)
- [x] T046 [P] Update `docs/index.html` — add `<meta name="description">`, `<meta property="og:title">`, `<link rel="icon">`; add `<footer>` with GitHub repo link and `<span id="last-updated">` (populated by `app.js` from `meta.generated_at` in data.json); ensure `<main>`, `<header>`, `<footer>` landmark elements present for screen reader navigation
- [x] T047 [P] Replace `fixture_data.json` reference in `docs/js/app.js` with `./data/data.json` — update `fetchData()` to fetch `./data/data.json`; test locally with scanner-produced data; confirm fixture file path was only a dev convenience and production path is correct

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundation (Phase 2)**: Depends on Setup — BLOCKS all user stories
  - T005–T006 (HTML/CSS) block US1 and US2
  - T007–T012 (models, config, fixtures, signatures) block US3
- **US1 (Phase 3)**: Depends on T005, T006 — independent of US3
- **US2 (Phase 4)**: Depends on US1 complete (builds on US1 UI foundation)
- **US3 (Phase 5)**: Depends on T007–T012 — independent of US1/US2
- **Polish (Phase 6)**: Depends on all stories complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundation — no dependency on US2 or US3
- **US2 (P2)**: Depends on US1 complete (adds to US1's UI components and JS modules)
- **US3 (P3)**: Can start after Foundation — fully independent of US1 and US2

### Within US3 (TDD Order)

- Write tests (T026–T032) → confirm all FAIL
- Implement modules (T033–T038) in order: fetcher/extractor/classifier [P] → detector → writer → main
- Run unit tests (T039) → integration test (T040) → acceptance (T041–T042)

### Parallel Opportunities

**Phase 1**: T002, T003, T004 all parallel after T001
**Phase 2**: T006, T007, T008, T010, T012 parallel after T005; T009 depends on T008 FAIL; T011 depends on T010 FAIL
**Phase 3**: T013, T014 parallel; T015 depends on both; T016, T017 parallel; T018, T019 extend existing files sequentially
**Phase 4**: T020, T021 parallel; T022, T024 parallel after T020; T023, T025 extend existing files
**Phase 5 (tests)**: T026, T027, T028, T029, T030 all parallel; T031 after T026–T030 written
**Phase 5 (impl)**: T033, T034, T035 parallel; T036 after T033, T035, T012; T037 after T036; T038 after all
**Phase 6**: T043, T044, T046, T047 parallel; T045 after all stories

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 (Setup)
2. Complete Phase 2 Foundation (T005, T006 for frontend only)
3. Complete Phase 3 (US1 — technology filter)
4. **STOP and VALIDATE**: Load `docs/index.html` locally, select "Grafana", confirm filtering works with fixture data
5. Demo at `http://localhost:8080`

### Incremental Delivery

1. Setup + Foundation → scaffold ready
2. US1 complete → tech filter site works (MVP!) with fixture data
3. US2 complete → multi-filter site works → deploy to GitHub Pages
4. US3 complete → real scanner produces `data.json` → update deployed site with live data
5. Polish → CI, accessibility, production-ready

### Parallel Team Strategy

With multiple contributors:
- **Contributor A**: US1 + US2 (frontend, no Python required)
- **Contributor B**: US3 (Python scanner, no frontend required)
- Both unblocked after Phase 2 Foundation

---

## Notes

- `[P]` tasks involve different files with no blocking dependencies — safe to run concurrently
- `[Story]` label maps each task to its user story for independent delivery tracking
- US3 TDD tasks: tests **must** fail before implementation begins (Constitution Principle II)
- `fixture_data.json` (T004) enables US1/US2 to be fully developed without the scanner
- Replace `fixture_data.json` reference in `app.js` with `data.json` in T047 (final Polish)
- Contract test (T032) is marked `@pytest.mark.network` — skip in CI, run manually before release
- Commit after each checkpoint (end of Phase 3, 4, 5) at minimum
