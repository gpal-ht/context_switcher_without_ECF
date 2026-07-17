# Context Switcher — Versioning Policy

Status: Draft foundation (v0.2.0)
Applies to: the **Context Switcher project** version line only.

## 1. Three independent version lines

Context Switcher records three distinct identities. They are **never** conflated.

| Line | Source of truth | Example |
|---|---|---|
| **Context Switcher (project)** | `package.json` `version` | `0.2.0` |
| **Bundled ECF** | `vendor/ecf/ecf-version.yaml` (canonical) + `vendor/ecf/VERSION` (bundle pin/commit) | `v0.1` / `v0.1-local` @ `7fd39af…` |
| **Bundled EKB** | `vendor/ecf/vendor/engineering_kb/VERSION` | `v0.1-local` @ `6084948…` |

**Rule:** Do **not** use a Context Switcher version bump as a substitute for ECF or
EKB versioning. ECF/EKB identities change only when the bundle is refreshed
(`scripts/bundle-ecf.ps1`); the project version changes only for project reasons
below. All three are recorded together in `release/release-manifest.json`.

## 2. Semantic versioning for the project line

The Context Switcher project version follows Semantic Versioning (`MAJOR.MINOR.PATCH`).

### MAJOR — incompatible / migration-forcing

- Incompatible project **data format** (persisted state, work-session, knowledge store).
- Incompatible **bundle / adoption contract** (how the project consumes ECF).
- **Architecture model break** requiring migration (e.g. a canonical-subsystem change
  that invalidates existing artifacts).
- **Removal** of a supported consumer workflow.

### MINOR — backward-compatible additions

- New backward-compatible project capabilities.
- New Work Request / workflow integration.
- New architecture module.
- New consumer automation (scripts, gates) that does not break existing usage.

### PATCH — compatible fixes

- Acceptance-test fixes.
- Wrapper / path fixes.
- Bundle **metadata** corrections.
- Documentation corrections.
- Dependency **refresh that preserves compatibility** (e.g. an ECF bundle refresh
  with no contract change — the project PATCH records that the refresh happened;
  the ECF/EKB commit fields carry the actual dependency identity).

## 3. Pre-1.0 expectations

While the project is `0.y.z` and implementation has not started (see `README.md`),
the surface is explicitly unstable. Breaking changes MAY land in MINOR increments,
but the categories above still guide the choice, and every release is recorded in
the manifest with its full ECF/EKB pin.

## 4. Where versions are asserted

- Human-readable policy: **this file**.
- Machine-readable identity: `release/release-manifest.json`
  (built by `scripts/build-release-manifest.py`).
- Drift/agreement enforcement: `scripts/validate-release.py` (`npm run release:validate`).

Related: `release/COMPATIBILITY.md`, `release/RELEASE_MANIFEST_SCHEMA.md`.
