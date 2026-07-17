# EKB Compatibility Contract

This document declares, in EKB-owned terms, the identity a consumer (e.g. ECF)
should pin. **It does not modify ECF or any consumer.**

## What Consumers Should Pin

| Pin | Source | Meaning |
|---|---|---|
| **Package version** | `package.json:version` (mirrored in `VERSION`, manifest) | Release identity (`0.2.0`). |
| **Git commit** | the `v0.2.0` tag commit (`git rev-list -n1 v0.2.0`) | Exact released repository state a consumer bundles/pins. The manifest's `git_commit` is the best-effort *source* commit (its base); the authoritative released commit is the tag commit, recorded in the platform compatibility table. |
| **Knowledge Object schema version** | `release-manifest.json:compatibility.knowledge_object_schema_version` (`1.0`) | Structure of Knowledge Objects (metadata + relationships). |
| **Package contract version** | `release-manifest.json:compatibility.package_contract_version` (`1.0`) | Engineering Knowledge Package structure (`artifacts/ENGINEERING_KNOWLEDGE_PACKAGE_CONTRACT.md`). |

Pinning `(package_version, git_commit)` is sufficient for an exact, reproducible
consumption. The two schema versions let a consumer reason about compatibility
across releases without re-reading every object.

## Current Compatibility Declarations (0.2.0)

- **Canonical Decision Guide type:** `decision_guide` (artifact identity). The
  value `engineering_decision` is rejected — see
  `migrations/MIGRATION-0002-decision-guide-type-final.md`.
- **Relationship model:** `foundations/KNOWLEDGE_RELATIONSHIP_MODEL.md`, codes
  `REL001`–`REL007`.
- **Knowledge Object schema version:** `1.0`.
- **Package contract version:** `1.0`.
- **Engine generator version:** `0.2.0`.

## Downstream Bundle-Refresh Requirements

Before the next cross-repository experiment, any ECF bundle, runner, or bundled
EKB copy that pinned an **earlier** DG type value must refresh to
`type: decision_guide`:

- pinned `engineering_decision` (from the superseded `MIGRATION-0001`) → refresh;
- pinned the older accidental `decision_guide` → already aligned.

No consumer has pinned the type yet, so this is the cheapest alignment point.
**This batch performs no bundle refresh** — it only declares the requirement.

## Stability Notes (0.x line)

While the major version is `0`, breaking changes may ship in minor releases but
are always accompanied by a numbered migration under `migrations/` and a note
here. See `release/VERSIONING_POLICY.md`.
