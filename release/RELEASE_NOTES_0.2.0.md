# Context Switcher — Release Notes 0.2.0

Package: `@gpal-ht/context-switcher`
Version: `0.2.0`
Tag: `v0.2.0`
Private: `true` — not published to any registry.
Publish status: `not_published`.

## Theme

Operational AI engineering platform foundation — the **Project Plane**: a
concrete project adopting the Control Plane (ECF) over the Knowledge Plane (EKB),
with governed work-request adoption, offline consumer verification, and release
engineering.

## Highlights

- **Canonical six-subsystem architecture.** Reconciled and recorded in
  `ADR-0005 — Canonical Subsystem Model`.
- **Project Work Request governance.** A Work Request catalog with `WR-0001`
  (repository integration subsystem) and `WR-0002`, governing how project work is
  adopted.
- **ECF adoption and bundling.** ECF is vendored offline under `vendor/ecf/`,
  refreshed only via `scripts/bundle-ecf.ps1`, and pinned exactly (see below).
  Strategy recorded in `ADR-0006 — Release and Bundling Strategy`.
- **Portable consumer wrappers.** `initialize-ecf-run.ps1`, `plan-ecf-workflow.ps1`,
  and `run-ecf-task.ps1` with Git Bash/PowerShell path conversion and
  fixture-path portability, plus fail-fast diagnostics.
- **Offline end-to-end consumer verification.** The offline pipeline
  (canonical initializer → planner → fixture runner → planner) is exercised by
  `check_consumer_integration.sh`; live Claude is never invoked and no vendor
  mutation occurs.
- **First successful real Claude-backed `TASK-CLASSIFY-0001` execution.** Proven
  as single-task execution (recorded honestly in the manifest acceptance level).
- **Release foundation.** Offline release manifest + validator, seven acceptance
  checks, `.gitignore` hardening, and a compatibility manifest.

## Exact dependency pins

| Dependency | Version | Tag | Commit |
|---|---|---|---|
| ECF (`@gpal-ht/ecf`) | `0.2.0` | `v0.2.0` | `eb15e18c34fe0fb4292e896962845dae51fe6da7` |
| Nested EKB (`@gpal-ht/engineering-kb`) | `0.2.0` | `v0.2.0` | `ce160741b767c4f108c6483fb94d13a2cc934e3a` |

Top-level `vendor/ecf/VERSION` `ekb_commit` matches nested
`vendor/ecf/vendor/engineering_kb/VERSION` `source_commit` (`ce16074…`). The
project version is independent of the ECF/EKB versions (not a proxy bump).

## Runtime evidence

Experiment 0006 and later real-run evidence are retained only under ignored
runtime storage (`runtime/`), never committed. This release embeds no run
directories, transaction journals, provenance files, or experiment logs.

## Verification (all gates pass for this release)

- `npm test` (7 acceptance checks) → ALL PASSED.
- Bundle self-test → 12 passed.
- Offline consumer integration → 0 failures (fixture executor; no live Claude).
- `npm run release:manifest` / `release:validate` → gates pass (0 failures).
- `npm run release:pack` → 391 files, no bytecode, `.claude/`, runtime, or
  generated output.

## Release-manifest identity model (non-recursive)

The manifest records the project `commit` as best-effort provenance
(`commit_policy: best_effort`) and excludes it from the drift comparison, so the
committed manifest never asserts its own containing commit. Release identity is
the exact ECF/EKB pins and bundled capabilities; the tag→commit binding is
recorded in `PLATFORM_RELEASE_0.2.0.md` and resolvable via `git rev-list -n1 v0.2.0`.

## Known limitations

- The full `WF-REASON-0001` workflow has **not yet completed end to end**.
- Automated multi-task orchestration is **intentionally absent** — tasks are
  driven one at a time through the canonical runner in this release.
- No npm publication and no GitHub Release are created by this batch.
