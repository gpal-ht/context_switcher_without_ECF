# Context Switcher — Versioning Policy

Status: App-only foundation (ADR-0010; ECF removed)
Applies to: the Context Switcher application version line.

## 1. One version line

Context Switcher is a standalone application with a single version identity —
`package.json` `version` (e.g. `0.2.0`). ADR-0010 removed the former bundled
ECF/EKB dependency lines; there is no separate dependency version to track.
The application also carries an independent **persistence schema version**
(`WorkspaceState.CurrentSchemaVersion`, ADR-0008/0009) governing the on-disk
workspace file; that is a data-format version, not the product version.

## 2. Semantic versioning

The project version follows Semantic Versioning (`MAJOR.MINOR.PATCH`).

### MAJOR — incompatible / migration-forcing

- Incompatible persisted **data format** with no automatic migration.
- **Architecture model break** requiring migration.
- Removal of a supported user-facing capability.

### MINOR — backward-compatible additions

- New backward-compatible product capabilities.
- New architecture module.
- New tooling or gates that do not break existing usage.

### PATCH — compatible fixes

- Bug fixes, acceptance-test fixes, documentation corrections.
- Additive persistence changes that keep existing workspace files valid
  (ADR-0009 rule: additive optional fields do not bump the schema version).

## 3. Pre-1.0 expectations

While the project is `0.y.z`, the surface is explicitly unstable. Breaking
changes MAY land in MINOR increments, but the categories above still guide the
choice, and every release is recorded in the manifest.

## 4. Where versions are asserted

- Human-readable policy: **this file**.
- Machine-readable identity: `release/release-manifest.json`
  (built by `scripts/build-release-manifest.py`).
- Drift/agreement enforcement: `scripts/validate-release.py` (`npm run release:validate`).

Related: `release/COMPATIBILITY.md`, `release/RELEASE_MANIFEST_SCHEMA.md`.
