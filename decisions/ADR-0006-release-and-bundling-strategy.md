# ADR-0006: Release and Bundling Strategy

**Status:** Superseded by [ADR-0010](ADR-0010-remove-ecf-integration.md)
(ECF removed from this repository, 2026-07-17). Retained as history: this
records the original ECF/EKB bundling and release policy. With ECF gone, the
release tooling is app-only and no longer bundles any dependency.

**Date:** 2026-07-13

**Approved by:** Project Owner

**Related Work:** Context Switcher Release Foundation (v0.2.0)

## Context

Context Switcher consumes the Engineering Control Framework (ECF), which itself
bundles the Engineering Knowledge Base (EKB). The v0.2.0 release foundation
introduced `package.json`, a release manifest, release documentation, and offline
validation tooling. Those artifacts encoded several significant, hard-to-reverse
choices — how versions are sourced, how dependencies are bundled, whether the
package is published, and what a "release" actually requires — but no single
decision record made them canonical. Without an ADR, the policy lives scattered
across `release/*.md` and the tooling, inviting drift and silent redefinition.

This ADR fixes those choices in one place so the release docs and tooling can
**reference** the policy instead of each restating (and potentially contradicting)
it. It is needed now, at the foundation stage, before any release is cut.

## Decision

### Version source — each repository owns its own semantic version

- Every repository (Context Switcher, ECF, EKB) owns its **own** SemVer line.
- For Context Switcher, the **canonical version source is `package.json`**.
- `VERSION` files (`vendor/ecf/VERSION`, the nested EKB `VERSION`) are **release
  metadata** describing bundled-dependency identity — they are **not** the project's
  version, and the project version is never a proxy for ECF/EKB versioning.

### Bundle strategy — nested, explicit, offline

The dependency composition is nested and self-contained:

```
Engineering KB (EKB)
        ↓ bundled into
Engineering Control Framework (ECF)
        ↓ bundled into
Context Switcher
```

- **No runtime downloads.** A release artifact carries everything it needs.
- **No npm dependency installation.** The package declares no runtime npm
  dependencies; there is no `package-lock.json`.
- **Bundle refreshes are explicit engineering changes**, performed only via
  `scripts/bundle-ecf.ps1` (never by hand-editing `vendor/`), and are visible in
  version-control history and in the release manifest's ECF/EKB pins.

### Package publication — private, owner-gated

Current state and policy:

```
private
not published
no git tags
no GitHub Release
owner approval required
```

npm provides release **metadata and validation**, not public distribution. No
tooling in this repository performs `npm publish`, `npm version`, tag creation,
GitHub releases, commits, or pushes.

### Runtime — never packaged

The following are runtime/generated output and must **never** be packaged or
committed:

```
runtime/
generated/
experiment logs
transactions
locks
staging
scratch
```

Enforced by the `package.json` `files` allowlist, `.gitignore`, and
`release:validate` packaging gates.

### Compatibility — exact pins, no floating

- Context Switcher owns its own version and **pins the exact ECF identity**
  (source + 40-hex commit).
- ECF **pins the exact bundled EKB identity** (source + 40-hex commit), and the
  EKB commit recorded in the ECF `VERSION` **must match** the nested EKB `VERSION`.
- **No floating compatibility** (no ranges, no "latest") anywhere in the chain.

### Release gates — a release is more than passing unit tests

An approved release requires **all** of:

```
Acceptance tests       (npm test)
Bundle integrity       (npm run test:bundle / :selftest)
Consumer integration   (offline, fixture executor)
Release validation     (npm run release:validate)
Pack dry-run           (npm run release:pack, content reviewed)
Owner approval
```

Passing unit tests alone is **not** a release.

### Release event — a tag means an approved release

A **git tag represents an approved release**, not merely a version bump. Tagging
(and any publication) is an explicit owner action taken only after every gate above
is green.

## Alternatives Considered

### Bundling: A — include the bundle (chosen) vs B — fetch ECF separately

- **A (chosen).** Pros: offline-verifiable; reproducible; matches the current
  read-only `vendor/` governance; no new machinery. Cons: larger artifact; bundle
  refresh coupled to the release lifecycle.
- **B.** Pros: smaller artifact; decoupled dependency lifecycle. Cons: requires a
  fetch/resolve contract and network availability; weakens offline reproducibility.
  Deferred; adopting it later would warrant its own ADR.

### Versioning: per-repository SemVer (chosen) vs single shared version

- **Per-repo (chosen).** Pros: each component evolves independently; dependency
  identity is explicit via pins. Cons: three version lines to track (mitigated by
  the release manifest).
- **Single shared version.** Pros: one number. Cons: forces project bumps for
  dependency changes (and vice versa); conflates unrelated lifecycles — the exact
  anti-pattern the version-source rule forbids.

### Publication: private/owner-gated (chosen) vs public npm

- **Private (chosen).** Pros: no accidental distribution; owner controls every
  release event. Cons: no public consumption (not a goal now).
- **Public npm.** Pros: distributable. Cons: premature — the application has not
  started implementation; nothing to distribute.

## Compatibility

- The compatibility chain is **exact-pin only**: Context Switcher → ECF commit →
  EKB commit, with ECF↔EKB commit agreement asserted at validation time.
- Changing any pin is a **bundle refresh** (explicit engineering change), reflected
  in `release/release-manifest.json` and gated by `release:validate`.
- Interoperability with a given ECF/EKB is defined solely by the recorded commits,
  never by version ranges.

## Review Triggers

Revisit this decision if:

- a fetched-dependency model (Option B) becomes necessary (size, decoupling, or
  multi-consumer reuse);
- Context Switcher needs public distribution (promotion off `private`);
- the release must be automated end-to-end (CI-driven publish/tag), which would
  change the "owner-gated" posture;
- the ECF/EKB bundling topology changes (e.g., EKB consumed directly rather than
  through ECF).

## Superseded Decisions

None. This ADR is **additive** and supersedes no prior decision. It formalizes as
canonical policy the release/bundling choices previously described informally in
`release/COMPATIBILITY.md` and `release/RELEASE_PROCESS.md`; those documents now
**reference** this ADR rather than restating the policy. ADR-0002/0004/0005 (the
subsystem model) are unaffected.

## References

- `package.json` — canonical project version + packaging allowlist + release scripts.
- `release/VERSIONING_POLICY.md` — SemVer rules for the project line.
- `release/RELEASE_PROCESS.md` — the offline release procedure.
- `release/RELEASE_CHECKLIST.md` — the release gates as a checklist.
- `release/COMPATIBILITY.md` — recorded compatibility + bundle-strategy trade-off.
- `release/RELEASE_MANIFEST_SCHEMA.md` / `release/release-manifest.json` — machine-readable identity.
- `scripts/build-release-manifest.py`, `scripts/validate-release.py` — manifest + gate enforcement.
- `vendor/BUNDLE_RULES.md`, `scripts/bundle-ecf.ps1` — read-only vendor governance + the only bundle-refresh path.
- `acceptance_tests/` — acceptance, bundle-integrity, and offline consumer-integration checks.
