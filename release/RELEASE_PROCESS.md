# Context Switcher — Release Process

Status: Draft foundation (v0.2.0)
Scope: how to cut a Context Switcher release artifact **offline**, with full
identity/compatibility validation, without publishing.

**Canonical policy:** [`ADR-0006 — Release and Bundling Strategy`](../decisions/ADR-0006-release-and-bundling-strategy.md).
This document is the operational procedure; it does not restate the policy. In
particular ADR-0006 governs version source, the nested bundle strategy (offline,
no downloads/installs), private/owner-gated publication, the never-package runtime
list, exact-pin compatibility, the release gates, and what a git tag means.

Operational reminders that follow directly from ADR-0006: every step is **offline**
(the consumer integration test uses the fixture executor); `vendor/` is refreshed
**only** via `scripts/bundle-ecf.ps1`; identity is read from metadata
(`VERSION` / `ecf-version.yaml` / `package.json`), never from prose.

## Roles / ownership

- **Run initialization, planner, runner, schemas:** canonical ECF (`vendor/ecf/…`).
- **Consumer wrappers:** `scripts/*.ps1` (thin adapters only).
- **Release metadata + gates:** `package.json`, `release/`, `scripts/build-release-manifest.py`,
  `scripts/validate-release.py`.

## Procedure

1. **Confirm the working tree is clean** and on the intended branch (`git status`).
2. **Refresh the ECF bundle if required** — `pwsh scripts/bundle-ecf.ps1` (only when a
   dependency refresh is intended; otherwise skip). Never hand-edit `vendor/`.
3. **Set the project version** in `package.json` per `release/VERSIONING_POLICY.md`.
   (Edit the field directly; do not run `npm version` in this foundation.)
4. **Rebuild the manifest** — `npm run release:manifest`
   (writes `release/release-manifest.json`).
5. **Run the offline acceptance suite** — `npm test`
   (engineering context, work requests, architecture consistency, vendor + bundle
   integrity, ignore boundaries, consumer integration). Must be all-PASS.
6. **Run the bundle self-test** — `npm run test:bundle:selftest`.
7. **Validate release gates** — `npm run release:validate` (identity, ECF↔EKB
   agreement, capability presence, packaging boundaries, manifest freshness).
8. **Review packaged content** — `npm run release:pack` (`npm pack --dry-run --json`)
   and confirm no `runtime/`, `generated/`, `.claude/`, bytecode, or secrets appear.
9. **Update `release/RELEASE_CHECKLIST.md`** with the run's results and record the
   current acceptance level honestly.
10. **Hand off to the project owner** for any tag/commit/publish decision (out of
    scope here).

## Command summary

```bash
npm test                     # full offline acceptance suite (no live Claude)
npm run test:bundle:selftest # bundle-integrity parser/validator self-test
npm run test:consumer        # offline consumer integration only
npm run release:manifest     # (re)build release/release-manifest.json
npm run release:validate     # enforce identity/compatibility/packaging gates
npm run release:pack         # npm pack --dry-run --json (content review)
```

## Prerequisites

- **Git Bash** on PATH (npm scripts shell out to `bash` for the acceptance suite,
  mirroring `acceptance_tests/run_all.ps1`).
- **Python 3** on PATH (manifest + validation tools; the consumer wrappers own
  their own Python discovery).
- **Node/npm** for the script runner and `npm pack`.

Related: `release/RELEASE_CHECKLIST.md`, `release/COMPATIBILITY.md`.
