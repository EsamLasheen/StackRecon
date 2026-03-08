# Feature Specification: StackRecon — Bug Bounty Technology Intelligence

**Feature Branch**: `001-bug-bounty-intel`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: StackRecon — Bug Bounty Technology Intelligence

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Discover Technology Targets by Tech Stack (Priority: P1)

As a bug hunter, I want to search all public bug bounty programs and filter by the
technology running on their subdomains, so I can quickly find targets that match
my expertise (e.g., "show me all programs running Grafana").

**Why this priority**: This is the core value proposition of StackRecon. Without
technology-based filtering, the tool provides no differentiation from existing
program lists.

**Independent Test**: A user visits the live site, selects "Grafana" from the
technology filter, and immediately sees a list of programs and subdomains confirmed
to be running Grafana — without needing any other feature to be present.

**Acceptance Scenarios**:

1. **Given** a user opens the StackRecon web interface,
   **When** they select a technology from the technology filter (e.g., "Jenkins"),
   **Then** only programs with at least one subdomain detected as running Jenkins are shown.

2. **Given** a technology filter is active,
   **When** a user clicks on a program entry,
   **Then** they see all subdomains of that program running the selected technology.

3. **Given** no technology filter is applied,
   **When** the user loads the page,
   **Then** all scanned programs are shown with their detected technology badges.

4. **Given** a technology has zero detections across all scanned programs,
   **When** a user selects it from the filter,
   **Then** a clear "No results" message is shown rather than an empty page.

---

### User Story 2 — Filter Programs by Platform, Reward Type, and Name (Priority: P2)

As a bug hunter, I want to further narrow down programs by platform (e.g., HackerOne,
Bugcrowd), reward type (Paid / Free / Self-Hosted), and program name, so I can match
targets to my preferred workflow.

**Why this priority**: Technology filtering alone may return too many results. Additional
filters make the tool practical for professional use.

**Independent Test**: A user opens the interface, types a company name in the search
box, selects "Paid" reward type, and sees a filtered list — independent of any
technology filter being active.

**Acceptance Scenarios**:

1. **Given** a user types a partial company name in the search field,
   **When** the input is at least 2 characters,
   **Then** the program list updates in real-time to show only matching programs.

2. **Given** a user selects the "Paid" reward type filter,
   **When** the filter is applied,
   **Then** only programs classified as paid bug bounty programs are shown.

3. **Given** a user selects a platform filter (e.g., "HackerOne"),
   **When** the filter is applied,
   **Then** only programs hosted on that platform are shown.

4. **Given** multiple filters are active simultaneously (technology + platform + reward type),
   **When** the user views the results,
   **Then** only programs matching ALL active filters are shown (AND logic).

---

### User Story 3 — Run the Scanner to Refresh Program and Subdomain Data (Priority: P3)

As a maintainer, I want to run the StackRecon scanner from the command line to fetch
the latest program list from Chaos ProjectDiscovery, download and extract subdomain
ZIP files, and detect technologies across all subdomains, so the web interface stays
up-to-date.

**Why this priority**: Data freshness is essential for the tool's value, but this is a
maintainer workflow. It can be executed separately from the UI.

**Independent Test**: The scanner runs with `python main.py --limit 10`, successfully
downloads 10 programs' subdomain data, detects technologies, and writes output data
that the web interface can consume — independently of the UI being deployed.

**Acceptance Scenarios**:

1. **Given** the scanner is invoked with `python main.py`,
   **When** it runs,
   **Then** it fetches the full program list from Chaos ProjectDiscovery without manual
   configuration.

2. **Given** the scanner has fetched the program list,
   **When** it processes each program,
   **Then** it downloads the subdomain ZIP file, extracts it, and probes each subdomain
   for technology signals.

3. **Given** a `--limit N` flag is passed,
   **When** the scanner runs,
   **Then** it processes exactly N programs and exits successfully.

4. **Given** a program's ZIP file is unavailable or a subdomain probe times out,
   **When** the scanner encounters the error,
   **Then** it logs the failure, skips that entry, and continues without crashing.

5. **Given** the scanner completes a run,
   **When** it finishes,
   **Then** the output data is written in a format the web interface can directly consume.

---

### Edge Cases

- Chaos ProjectDiscovery source unavailable at scan start: the scanner MUST abort
  immediately with a clear, human-readable error message and exit with a non-zero code.
  The existing output JSON file MUST remain untouched so the UI continues to serve the
  last good dataset.
- How does the system handle subdomains that are unreachable or return non-standard HTTP responses?
- How does the UI behave when the data file is empty or malformed?
- What happens if two programs share the same name but are on different platforms?
- Subdomains that redirect to third-party services: the scanner follows the redirect
  chain (up to a configurable hop limit) and applies technology signatures to the final
  response. If the final destination is outside the program's scope, the detection is
  still recorded but flagged as "redirect target."

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The scanner MUST automatically retrieve the full list of public bug bounty
  programs from Chaos ProjectDiscovery without user-supplied configuration.
- **FR-002**: The scanner MUST download and extract subdomain ZIP files for each program
  in the fetched list.
- **FR-003**: The scanner MUST classify each subdomain against at least 47 technology
  signatures (e.g., Grafana, WordPress, Jenkins, Keycloak) using a hybrid detection
  approach: subdomain lists from Chaos ZIP files form the base dataset; live HTTP probing
  (single GET request, headers and body analysis only) is performed for a configurable
  subset of high-value technologies. No intrusive or exploit-like requests are permitted.
- **FR-004**: The scanner MUST classify each program into one of: Paid, Free, or
  Self-Hosted reward types.
- **FR-005**: The scanner MUST support a `--limit N` flag to process only N programs.
- **FR-014**: The scanner MUST use a configurable concurrent worker pool for subdomain
  probing, with a default of 50 workers. The concurrency level MUST be tunable via a
  `--workers N` CLI flag without requiring code changes.
- **FR-006**: The scanner MUST continue processing remaining programs when an individual
  program or subdomain fails — failures MUST be logged but MUST NOT halt execution.
- **FR-015**: If the Chaos ProjectDiscovery source is unreachable at scan startup, the
  scanner MUST abort immediately with a human-readable error and a non-zero exit code.
  The existing output JSON file MUST NOT be modified or deleted in this case.
- **FR-016**: The scanner MUST write scan output to a temporary file during execution
  and atomically rename it to `data.json` only upon full successful completion. An
  interrupted or failed scan MUST NOT corrupt or replace the previously valid `data.json`.
- **FR-007**: The scanner MUST produce a single JSON file containing a top-level array
  of programs, each with nested subdomain hostnames and detected technologies, that the
  web interface loads directly via a `fetch()` call with no server-side processing.
- **FR-008**: The web interface MUST allow users to filter programs by detected technology.
- **FR-009**: The web interface MUST allow users to filter programs by platform,
  reward type, and program name (text search).
- **FR-010**: The web interface MUST support combining multiple filters simultaneously
  using AND logic.
- **FR-011**: The web interface MUST be deployable as a static site on GitHub Pages with
  no server-side runtime required.
- **FR-012**: The web interface MUST display a dark-themed UI consistent with security
  tooling aesthetics.
- **FR-013**: Filter and search interactions MUST update displayed results without a
  full page reload.

### Key Entities

- **Program**: A public bug bounty program. Attributes: name, platform, reward type
  (Paid/Free/Self-Hosted), subdomain count, detected technologies.
- **Subdomain**: A hostname associated with a program. Attributes: hostname, HTTP status,
  detected technologies.
- **Technology**: A named technology signature. Attributes: name, detection signal,
  count of subdomains detected across all programs.
- **Scan Run**: A single scanner execution. Attributes: timestamp, programs processed,
  programs failed, total subdomains probed.
- **Output File**: A single `data.json` file produced after each scan. Structure: top-level
  array of Program objects, each containing a `subdomains` array (with detected technologies
  per host) and a `technologies` summary array. Consumed by the UI via a direct `fetch()` call.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can identify all programs running a specific technology within
  5 seconds of arriving at the web interface.
- **SC-002**: The scanner successfully processes at least 95% of available programs in
  a full run without manual intervention.
- **SC-003**: The web interface loads and renders the full program list in under 3 seconds
  on a standard broadband connection.
- **SC-004**: Applying any filter combination returns updated results within 500 ms
  with no network request required.
- **SC-005**: The scanner's `--limit 10` test mode completes in under 5 minutes on a
  standard developer machine.
- **SC-006**: Technology detection covers at least 47 distinct technologies across
  the scanned program set.

## Clarifications

### Session 2026-03-08

- Q: What is the output format of the structured file the scanner produces for UI consumption? → A: Single JSON file — programs array with subdomains and detected technologies nested per program entry.
- Q: How does the scanner detect technologies — live HTTP probing, offline ZIP analysis, or hybrid? → A: Hybrid — Chaos ZIP subdomain data is the base; live HTTP probing (single GET, headers + body) is performed for a configurable subset of high-value technologies.
- Q: What concurrency model does the scanner use for subdomain probing? → A: Configurable concurrent worker pool with a conservative default (e.g., 50 workers), tunable via a CLI flag (e.g., `--workers N`).
- Q: What happens when the Chaos ProjectDiscovery source is unavailable at scan start? → A: Abort immediately with a clear error message; the existing output file is left intact and unchanged so the UI continues to serve the last good dataset.
- Q: How is the output JSON file written — atomic or incremental? → A: Written to a temporary file during the scan; atomically renamed to `data.json` only on full successful completion, ensuring the UI always serves a fully-valid dataset.

## Assumptions

- The Chaos ProjectDiscovery source provides a machine-readable index of programs and
  subdomain ZIP URLs; no authentication is required.
- Technology detection uses a hybrid approach: Chaos ZIP subdomain lists provide the
  base dataset (no live requests needed for subdomain enumeration); live HTTP probing
  (single GET per subdomain, headers and body only) is performed for a configurable
  subset of high-value technologies. No exploit-like or intrusive requests are ever made.
- Which technologies require live probing vs offline-only classification is maintainer-
  configurable; the default set targets technologies with clear HTTP response fingerprints
  (e.g., Grafana, Jenkins, Keycloak) where offline data is insufficient.
- The GitHub Pages deployment assumes a static build step converting scanner output
  into web-consumable format (e.g., embedded or fetched JSON).
- Program platform classification (HackerOne, Bugcrowd, etc.) is deterministic from
  the Chaos data source and does not require additional scraping.
- The scanner is run by a single maintainer on demand; no scheduling infrastructure
  is in scope for this feature.
