# Context Switcher — Compatibility

Status: Draft foundation (v0.2.0)
Companion to the machine-readable `release/release-manifest.json`.

## Engineering backend (ADR-0007)

Every release records its **engineering backend** (`standalone` or `ecf`) and
a truthful capability matrix in the manifest. **ECF is optional**: standalone
releases claim no ECF/EKB identity, provenance, or acceptance level
(`"claimed": false` in every ECF section), and the ECF identity gates below
apply only to `ecf`-mode releases.

**ECF adapter compatibility policy** — selecting the `ecf` backend validates,
before any operation:

1. `vendor/ecf/` exists (availability);
2. `vendor/ecf/ecf-version.yaml` declares a `schema_version` on the supported
   **`0.1` line** (the compatibility anchor; the supported line is a single
   constant in `scripts/engineering_backend.py`);
3. `vendor/ecf/VERSION` carries a valid 40-hex `source_commit` (identity);
4. the required bundled capabilities are present.

An incompatible or missing bundle is a hard, named configuration failure —
never a silent fallback to standalone. ECF currently publishes no formally
versioned integration contract beyond `schema_version`; the required-
capability list is the de-facto contract, isolated in
`scripts/engineering_backend.py` and guarded by
`acceptance_tests/check_backend_boundary.sh` and `check_bundle_integrity.sh`
against silent drift.

## What compatibility is recorded

Every release records, in the manifest:

- **Context Switcher** version (`package.json`) and project commit (best-effort).
- **Bundled ECF** package/version/commit (`vendor/ecf/ecf-version.yaml` +
  `vendor/ecf/VERSION`) and bundle strategy.
- **Nested EKB** package/version/commit (`vendor/ecf/vendor/engineering_kb/VERSION`),
  plus the EKB identity as recorded inside the ECF `VERSION` (`ekb_*`).
- **Architecture decision baseline** — the `decisions/ADR-*.md` set.
- **Accepted Work Request baseline** — the `work_requests/WR-*.md` set.
- **Workflow compatibility** — the reasoning workflow the consumer targets
  (`WF-REASON-0001`).
- **Runtime-schema compatibility** — presence of the bundled `runtime_schemas/`
  contracts among the required capabilities.
- **Consumer-script compatibility** — the shipped `scripts/*.ps1` wrappers.

## What the manifest must detect

`scripts/validate-release.py` (`npm run release:validate`) fails the release when:

1. **Bundled ECF and nested EKB metadata disagree** — ECF `VERSION.ekb_commit`
   differs from the nested EKB `VERSION.source_commit` (Gate 4).
2. **The package version drifts** — `package.json` version differs from the manifest
   project version, or the on-disk manifest is stale versus live state (Gates 1–2).
3. **Required bundled capabilities are absent** — any capability in the required set
   (mirrored from `check_bundle_integrity.sh`) is missing (Gate 5).

It additionally enforces machine-path-free ECF identity, nested-EKB validity,
consumer-script presence, packaging boundaries, and honest acceptance level.

## Bundled ECF strategy (trade-off detail)

The decision is recorded canonically in
[`ADR-0006 — Release and Bundling Strategy`](../decisions/ADR-0006-release-and-bundling-strategy.md).
This section retains the detailed trade-off table it references; it does not
re-decide the policy.

**Decision (per ADR-0006): Option A — the self-contained bundle is included in
the Context Switcher release artifact.**

| | Option A — include bundle (chosen) | Option B — fetch ECF separately |
|---|---|---|
| Offline verifiable | Yes — bundle ships with the release | No — needs a fetch/resolve step |
| Artifact size | Larger (full `vendor/ecf/` tree) | Smaller |
| Reproducibility | High — pinned tree travels with the release | Depends on external availability |
| Coupling | Bundle refresh is coupled to the release | Decoupled dependency lifecycle |
| Complexity now | Low — matches current repo shape | Higher — new resolution contract |

**Rationale:** the repository is already self-contained and offline-verifiable, and
`vendor/` is governed as read-only via `scripts/bundle-ecf.ps1`. Option A preserves
that guarantee with no new machinery. Option B (a fetched dependency artifact) is a
deliberate future step and would warrant a superseding ADR. Full rationale,
alternatives, and review triggers: see ADR-0006.

## Current pins (informational; authoritative values live in the manifest)

- **ECF:** canonical `v0.1` (`ecf-version.yaml`); bundle `v0.1-local`, commit
  recorded in `vendor/ecf/VERSION` `source_commit`.
- **EKB:** `v0.1-local`, commit recorded in the nested EKB `VERSION` and mirrored in
  ECF `VERSION.ekb_commit` (must match).
- **Acceptance level:** single live task proven; full workflow not yet proven.

> Note: narrative documents (e.g. `PROJECT_ECF_ADOPTION_REPORT.md`) may cite an
> older commit than the live bundle. The manifest and validator read metadata, not
> prose, so such prose drift never affects a release decision — but it is worth
> reconciling as an open finding.

Related: `release/VERSIONING_POLICY.md`, `release/RELEASE_MANIFEST_SCHEMA.md`.
