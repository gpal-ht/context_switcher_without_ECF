# ADR-0010: Remove ECF Integration

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "start the ECF-cleanup pass";
scope confirmed as "remove ECF + backend abstraction only, keep an app-only
release/governance harness", 2026-07-17)

**Supersedes:** ADR-0006 (Release and Bundling Strategy), ADR-0007 (Optional
ECF Integration Behind an Engineering-Backend Boundary)

**Related Work:** ADR-0008 (Work Engine Implementation Foundation),
ADR-0009 (Work Session Lifecycle)

## Context

This repository was forked from the ECF-consumer `context_switcher` to
become a standalone, releasable Context Switcher application. ECF (the
Engineering Control Framework) was a design/governance integration, made
optional behind a stable engineering-backend boundary in ADR-0007. With the
product now developing on its own (project registry ADR-0008, work sessions
ADR-0009) and targeting an app-store release, the ECF integration — the
bundled `vendor/ecf` tree, the consumer wrapper scripts, the backend
selection abstraction, and the ECF governance artifacts — is dead weight:
it is never exercised by the application, it is large, and it complicates
the build, packaging, and documentation.

Because ADR-0007 isolated ECF behind a narrow boundary (an allowlisted
backend registry, adapter scripts, and a dependency-boundary test proving no
product code references `vendor/ecf`), removal is a clean vertical
extraction rather than scattered surgery — the boundary was designed to make
exactly this possible.

## Decision

Remove ECF from this repository entirely and collapse the now-single-mode
backend abstraction. The application (`src/`) is unaffected: it never
depended on ECF.

### Removed

- **Bundled framework:** the entire `vendor/ecf/` tree.
- **ECF adapter scripts:** `scripts/bundle-ecf.ps1`,
  `scripts/initialize-ecf-run.ps1`, `scripts/plan-ecf-workflow.ps1`,
  `scripts/run-ecf-task.ps1`.
- **ECF acceptance tests:** `check_vendor_integrity.sh`,
  `check_bundle_integrity.sh`, `check_consumer_integration.sh`.
- **Engineering-backend abstraction** (only `ecf` justified two modes):
  `config/engineering-backend.yaml`, `scripts/engineering_backend.py`,
  `scripts/lib/Resolve-EngineeringBackend.ps1`,
  `acceptance_tests/lib/backend.sh`,
  `acceptance_tests/check_backend_boundary.sh`,
  `docs/engineering/ENGINEERING_BACKENDS.md`.
- **ECF governance artifacts:** `work_requests/` and its check
  `acceptance_tests/check_work_requests.sh`; `PROJECT_ECF_ADOPTION_REPORT.md`;
  `PLATFORM_RELEASE_0.2.0.md`.

### Simplified

- **`acceptance_tests/run_all.sh`** drops backend resolution and the ECF
  suite; it runs the product/architecture checks directly
  (`check_engineering_context`, `check_architecture_consistency`,
  `check_ignore_boundaries`, `check_product_tests`).
- **Release tooling** (`scripts/build-release-manifest.py`,
  `scripts/validate-release.py`, `release/`) becomes **app-only**: it records
  project identity, packaging boundaries, and the ADR/decision baseline. All
  bundled-ECF/EKB identity, capability, and backend fields are gone. The
  manifest is retained (the owner chose to keep an app-only release harness),
  not removed.
- **`package.json`** drops the ECF/backend scripts and the `vendor/ecf/`,
  `config/`, and `work_requests/` package entries.

### Kept

- The application (`src/`) and its gate (`check_product_tests.sh`).
- Product and architecture documentation, and the non-ECF governance checks
  (`check_engineering_context`, `check_architecture_consistency`,
  `check_ignore_boundaries`).
- Decision history: ADR-0001..0005, ADR-0008, ADR-0009, and — as **history,
  marked Superseded** — ADR-0006 and ADR-0007. ADRs are immutable records;
  they are annotated, not deleted.

## Consequences

- The repository is materially smaller and builds/packages as a pure .NET
  application with no vendored framework and no network/ECF assumptions.
- There is a single, implicit operating mode; no backend configuration
  exists or is consulted. The `CONTEXT_SWITCHER_ENGINEERING_BACKEND`
  variable and `engineering_backend` config key are retired.
- The dependency-boundary guarantee (no product code touches `vendor/ecf`)
  is now trivially satisfied because `vendor/ecf` no longer exists; the
  boundary test that enforced it is removed with the abstraction it guarded.
- Re-introducing an engineering integration later would be a fresh design
  (a new ADR), not a revival of this boundary.
- ADR-0006/0007 remain readable for the rationale of why ECF was bundled and
  then made optional, even though neither policy is active here.
