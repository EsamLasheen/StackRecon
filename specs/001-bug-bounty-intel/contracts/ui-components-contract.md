# Contract: Frontend UI Components

**Type**: UI Contract | **Branch**: `001-bug-bounty-intel` | **Date**: 2026-03-08

---

## Component Inventory

All shared UI patterns MUST be implemented as reusable JS functions in `docs/js/components.js`.
Ad-hoc one-off HTML patterns are prohibited (per Constitution III).

### 1. `ProgramCard(program, activeTech)`

Renders a single program entry in the results list.

**Inputs**:
- `program` — Program object from `data.json`
- `activeTech` — currently active technology filter string | null

**Outputs**: Returns an HTMLElement (div).

**Visual contract**:
- Left border accent: `--accent-primary` (neon green)
- Shows: program name, platform badge, reward type badge, subdomain count, technology badges
- If `activeTech` set: highlight the matching technology badge in `--accent-secondary`
- On hover: border color transitions to `--accent-secondary`
- On click: expands to show `detections` list filtered to `activeTech` (if set) or all detections

### 2. `TechBadge(techName, active)`

Renders a technology name pill/tag.

**Inputs**: `techName` string, `active` boolean

**Visual contract**:
- Inactive: background `--bg-tertiary`, border `--accent-primary`, text `--accent-primary`
- Active: background `--accent-primary`, text `--bg-primary` (inverted)
- Font: monospace
- Size: small (0.85em)

### 3. `PlatformBadge(platform)`

Renders a platform label (HackerOne, Bugcrowd, etc.).

**Visual contract**: `--text-secondary` color; no border; uppercase small caps.

### 4. `RewardBadge(rewardType)`

Renders the reward type indicator.

**Visual contract**:
- `paid` → `--accent-primary` (green)
- `free` → `--accent-secondary` (cyan)
- `self-hosted` → `--text-secondary` (grey)

### 5. `LoadingSpinner(message)`

Shown while `data.json` is being fetched. Covers the results area.

**Contract**: MUST be visible within 100 ms of page load (before fetch completes).
MUST disappear and be replaced by results within 500 ms of fetch completing.

### 6. `EmptyState(message)`

Shown when filter combination matches zero programs.

**Contract**: Clear, human-readable message. MUST include a "Clear filters" button.

### 7. `ErrorBanner(message)`

Shown when `data.json` fails to load (network error, malformed JSON).

**Contract**: `--accent-danger` background; human-readable error text; "Retry" button.
MUST be dismissible.

---

## Filter State Machine

```
Initial: all filters null → all programs shown
↓ User selects technology filter
Active tech filter → programs filtered by tech
↓ User selects platform filter (AND)
Active tech + platform filters → intersection result
↓ User clears tech filter
Active platform filter only → programs filtered by platform only
↓ User clears all filters
Back to initial state → all programs shown
```

**Rule**: Clearing one filter does not clear others.
**Rule**: Filter state MUST be reflected in the URL hash for shareability.
  Format: `#tech=Grafana&platform=HackerOne&reward=paid`

---

## Accessibility Contract (WCAG 2.1 AA)

- All interactive elements (buttons, inputs, filter options) MUST have visible focus indicators.
- Color is NEVER the sole means of conveying information (badges also use text labels).
- Contrast ratio ≥ 4.5:1 for all body text against background.
- Contrast ratio ≥ 3:1 for large text and UI components.
- All images/icons MUST have `alt` text or `aria-hidden="true"` if decorative.
- Filter inputs MUST have visible `<label>` elements.
- Program cards MUST be keyboard-navigable (Tab order follows DOM order).

---

## Performance Contract

- Filter update (any single filter change) → results re-rendered within **500 ms**.
- Text search (name input) → debounced 200 ms; results appear within 500 ms of debounce.
- Initial page load → `LoadingSpinner` visible within 100 ms; results within 3 s on broadband.
- Results list renders first 50 programs immediately; additional programs rendered on scroll.
