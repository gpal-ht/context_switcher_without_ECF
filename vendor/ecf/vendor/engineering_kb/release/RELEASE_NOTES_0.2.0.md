# Engineering Knowledge Base — Release Notes 0.2.0

Package: `@gpal-ht/engineering-kb`
Version: `0.2.0`
Tag: `v0.2.0`
Private: `true` — not published to any registry.
Publish status: `not_published`.

## Theme

Operational AI engineering platform foundation — the **Knowledge Plane**:
governed, machine-validated engineering knowledge that downstream planes (ECF
control, Context Switcher project adoption) pin exactly.

## Highlights

- **Canonical Decision Guide ontology.** `decision_guide` is the single
  canonical artifact type (the superseded `engineering_decision` value is
  rejected — see `migrations/MIGRATION-0002-decision-guide-type-final.md`).
- **Graph validation and retrieval.** The dependency-free Python engine
  (`engine/ekb.py`) enforces type-prefix integrity, relationship-model
  correctness (`REL001`–`REL007`), and scoped, guide-bounded retrieval closures.
- **Sufficiency validation.** Required/optional knowledge-object completeness is
  checked, including cohesion ablation and second-level completeness.
- **Deterministic reports.** `coverage` and `centrality` reports are
  byte-deterministic across runs (verified by the release validator).
- **Release-control foundation.** `package.json` + `VERSION` version mirror,
  a machine-readable release manifest, and mechanical `release:manifest` /
  `release:validate` gates — no publication is performed.

## Verification (all gates pass for this release)

- `npm test` → engine test suite: **40 passed, 0 failed**.
- `python engine/ekb.py validate | integrity | completeness` → pass.
- `python engine/ekb.py coverage | centrality` → deterministic.
- `npm run release:manifest` → regenerates `release/release-manifest.json`.
- `npm run release:validate` → all release gates pass.
- `npm pack --dry-run` → package contains only the canonical content allowlist;
  no `__pycache__`, `.git`, `.claude`, `generated/`, bytecode, logs, or tarballs.

## Release-manifest identity model (non-recursive)

Per the Critical Release-Manifest Rule, the committed manifest does **not** assert
its own containing commit. Release-content identity is `content_digest` (a sha256
over canonical content, excluding the manifest itself); `git_commit` is the
best-effort *source* commit (a committed ancestor of HEAD). The authoritative
**tag → commit** binding is recorded in the platform compatibility table
(`context_switcher/PLATFORM_RELEASE_0.2.0.md`) and resolvable via
`git rev-list -n1 v0.2.0`. See `release/RELEASE_MANIFEST_SCHEMA.md`.

## License decision

This repository has **no LICENSE file** and no `license` field. No license is
invented here. The package therefore remains **`private: true`** and **public
publication is blocked** until a license is chosen. This does not block the
private `v0.2.0` Git release/tag, which is owner-controlled and unpublished.

## Known limitations / notes

- `0.x` line: breaking changes may ship in minor releases, always with a numbered
  `migrations/` entry and a COMPATIBILITY note.
- No npm publication and no GitHub Release are created by this batch.
