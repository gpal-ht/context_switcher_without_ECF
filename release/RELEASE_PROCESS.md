# Context Switcher — Release Process

Status: App-only foundation (ADR-0010; ECF removed)
Scope: how to cut a Context Switcher release artifact **offline**, with full
identity/packaging validation, without publishing.

Context Switcher is a standalone .NET application with no bundled dependency
(ADR-0010). Release metadata describes only the application itself.

## Ownership

- **Application code:** `src/` (Work Engine + interim CLI harness).
- **Release metadata + gates:** `package.json`, `release/`,
  `scripts/build-release-manifest.py`, `scripts/validate-release.py`.

## Procedure

1. **Confirm the working tree is clean** and on the intended branch (`git status`).
2. **Set the project version** in `package.json` per `release/VERSIONING_POLICY.md`.
   (Edit the field directly; do not run `npm version` in this foundation.)
3. **Build and test the application** — `npm run app:test` (builds the Work
   Engine and CLI and runs the deterministic product suite). Must be all-PASS.
4. **Rebuild the manifest** — `npm run release:manifest`
   (writes `release/release-manifest.json`).
5. **Run the offline acceptance suite** — `npm test` (engineering context,
   architecture consistency, ignore boundaries, product build/tests). All-PASS.
6. **Validate release gates** — `npm run release:validate` (identity,
   application projects present, packaging boundaries, manifest freshness).
7. **Review packaged content** — `npm run release:pack` (`npm pack --dry-run --json`)
   and confirm no `runtime/`, `generated/`, `.claude/`, bytecode, or secrets appear.
8. **Update `release/RELEASE_CHECKLIST.md`** with the run's results.
9. **Hand off to the project owner** for any tag/commit/publish decision (out of
   scope here).

## Command summary

```bash
npm run app:test          # build + deterministic product tests
npm test                  # full offline acceptance suite
npm run release:manifest  # (re)build release/release-manifest.json
npm run release:validate  # enforce identity/application/packaging gates
npm run release:pack      # npm pack --dry-run --json (content review)
```

## Prerequisites

- **.NET SDK** on PATH (builds and tests the application).
- **Git Bash** on PATH (npm scripts shell out to `bash` for the acceptance suite).
- **Python 3** on PATH (manifest + validation tools).
- **Node/npm** for the script runner and `npm pack`.

Related: `release/RELEASE_CHECKLIST.md`, `release/COMPATIBILITY.md`.
