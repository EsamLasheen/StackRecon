<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0 [Initial ratification]

Added sections:
- I. Code Quality (new)
- II. Testing Standards (new)
- III. User Experience Consistency (new)
- IV. Performance Requirements (new)
- Quality Gates
- Development Workflow
- Governance

Removed sections: N/A (initial version)

Templates requiring updates:
- ✅ .specify/templates/plan-template.md — Constitution Check gates align with these 4 principles
- ✅ .specify/templates/spec-template.md — Success Criteria section already captures measurable outcomes
- ✅ .specify/templates/tasks-template.md — Polish phase covers perf, security, and docs per principle IV
- ✅ .specify/memory/constitution.md — This file

Follow-up TODOs:
- TODO(TECH_STACK): No language/framework detected yet. Constitution uses tech-agnostic language.
  Update Performance Requirements thresholds once stack is confirmed.
-->

# StackRecon Constitution

## Core Principles

### I. Code Quality (NON-NEGOTIABLE)

All code MUST meet the following standards before merging:

- **Readability**: Every function or method MUST have a single, well-defined responsibility.
  Files exceeding 400 lines MUST be split unless a documented exception exists.
- **No dead code**: Unused variables, imports, functions, and commented-out blocks MUST
  be removed. Code is not preserved "just in case."
- **Consistent style**: A linter and formatter MUST be configured and enforced in CI.
  No PR may introduce linting violations.
- **Meaningful naming**: Variable, function, and class names MUST convey intent without
  requiring inline comments to decode them.
- **Minimal complexity**: Cyclomatic complexity above 10 per function MUST be justified
  or refactored. Prefer flat, readable control flow over clever nesting.

**Rationale**: Readable, well-structured code reduces onboarding time, minimizes bugs,
and enables confident refactoring. Complexity is a liability, not an asset.

### II. Testing Standards (NON-NEGOTIABLE)

All features MUST be shipped with tests. The following rules are mandatory:

- **Test-first discipline**: Tests MUST be written before implementation begins.
  Tests MUST fail (red) before implementation makes them pass (green).
- **Coverage floor**: Unit test coverage MUST not drop below 80% for new code.
  Coverage regressions block merges.
- **Test pyramid**: Features MUST include unit tests. Integration tests MUST cover
  every user-facing workflow. Contract tests MUST cover all external API boundaries.
- **Isolation**: Unit tests MUST NOT rely on external services, databases, or network.
  Use mocks, fakes, or stubs at system boundaries.
- **Test quality**: Flaky tests MUST be fixed or deleted — never skipped indefinitely.
  A skipped test is a debt that MUST carry a linked issue.

**Rationale**: Tests are the primary mechanism for validating behaviour and enabling
safe refactoring. Untested code is a correctness risk and a maintenance burden.

### III. User Experience Consistency

All user-facing interfaces MUST follow these rules:

- **Uniform error messages**: Error messages MUST be human-readable, actionable, and
  consistent in tone and format across the entire application.
- **Predictable behaviour**: Similar actions MUST produce similar outcomes. Surprise
  behaviour MUST be treated as a bug.
- **Feedback on every action**: Every user action that takes longer than 300 ms MUST
  provide visible feedback (loading indicator, progress bar, or status message).
- **Accessible by default**: UI components MUST meet WCAG 2.1 AA accessibility
  standards. Accessibility is not optional or deferred.
- **Documented UX contracts**: Any shared UI pattern (buttons, forms, modals, toasts)
  MUST be implemented via a reusable component. Ad-hoc one-offs are prohibited.

**Rationale**: Consistency builds user trust and reduces cognitive load. Accessibility
ensures the product is usable by everyone, not just the majority.

### IV. Performance Requirements

All features MUST satisfy baseline performance targets before shipping:

- **Response time**: API endpoints MUST respond within 200 ms at p95 under expected
  load. Page loads MUST complete within 2 s on a standard connection.
- **No performance regression**: New code MUST not degrade existing benchmark baselines
  by more than 10%. Performance tests MUST run in CI.
- **Resource efficiency**: Features MUST not introduce unbounded memory growth or
  O(n²) complexity against user-controlled input sizes.
- **Lazy loading**: Large data sets MUST be paginated or lazily loaded. Fetching
  unbounded result sets is prohibited.
- **Profiling before optimisation**: Optimisations MUST be backed by profiling data.
  Speculative optimisations that increase complexity are prohibited.

**Rationale**: Performance is a feature. Slow software erodes user trust and
increases infrastructure cost. Regression prevention is cheaper than post-hoc fixes.

## Quality Gates

The following gates MUST pass before any feature branch is merged to main:

- [ ] All tests pass (unit, integration, contract)
- [ ] Coverage floor maintained (≥ 80% on new code)
- [ ] No linting or formatting violations
- [ ] No new dead code or unused imports
- [ ] Performance benchmarks show no regression > 10%
- [ ] UX review completed for any user-facing change
- [ ] Accessibility check passed for new UI components
- [ ] Constitution Check completed in `plan.md`

## Development Workflow

1. **Spec first**: Every feature begins with a `spec.md` capturing user stories and
   acceptance criteria. No implementation starts without an approved spec.
2. **Plan before code**: A `plan.md` MUST be produced before implementation, including
   a Constitution Check gate.
3. **Test before implement**: Tests are written and confirmed failing before
   implementation begins (see Principle II).
4. **Incremental delivery**: Features MUST be deliverable in independently testable
   user-story slices. Big-bang releases are prohibited.
5. **Review before merge**: All code MUST be reviewed by at least one peer. The
   author is responsible for ensuring all quality gates pass before requesting review.

## Governance

This constitution supersedes all informal conventions, verbal agreements, and
prior practices. Amendments require:

1. A written proposal documenting the change and its rationale.
2. Agreement from at least one other contributor (or project lead on solo projects).
3. A version bump following semantic versioning:
   - **MAJOR**: Removal or redefinition of an existing principle.
   - **MINOR**: Addition of a new principle or section.
   - **PATCH**: Clarification, wording improvement, or non-semantic refinement.
4. `LAST_AMENDED_DATE` updated on every change.

All PRs and code reviews MUST verify compliance with this constitution.
Complexity violations MUST be documented in the `Complexity Tracking` table
of the relevant `plan.md` before being permitted.

**Version**: 1.0.0 | **Ratified**: 2026-03-08 | **Last Amended**: 2026-03-08
