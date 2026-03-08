# StackRecon Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-08

## Active Technologies

- Python 3.11+ (scanner) · HTML5/CSS3/ES2022 (frontend, no build step) + httpx ≥ 0.25 (async HTTP probing) · PyYAML ≥ 6.0 (signature DB) · aiofiles ≥ 23.0 (async file I/O) · no frontend dependencies (Vanilla JS) (001-bug-bounty-intel)

## Project Structure

```text
scanner/src/        # Python CLI scanner modules
signatures/         # technologies.yaml signature database
docs/               # GitHub Pages static frontend (index.html, css/, js/, data/)
tests/              # pytest: unit/, integration/, contract/
specs/              # Feature specs and plans
```

## Commands

```bash
# Run scanner (test mode)
cd scanner && python main.py --limit 10

# Run tests
cd scanner && pytest --cov=src tests/

# Lint + format
ruff check scanner/src && black --check scanner/src

# Serve frontend locally
cd docs && python -m http.server 8080
```

## Code Style

- Python: black formatting, ruff linting, type hints on all public functions
- JS: ES2022, no build step, no npm — Vanilla JS only
- YAML: 2-space indent, no trailing whitespace

## Recent Changes

- 001-bug-bounty-intel: Added Python 3.11+ (scanner) · HTML5/CSS3/ES2022 (frontend, no build step) + httpx ≥ 0.25 (async HTTP probing) · PyYAML ≥ 6.0 (signature DB) · aiofiles ≥ 23.0 (async file I/O) · no frontend dependencies (Vanilla JS)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
