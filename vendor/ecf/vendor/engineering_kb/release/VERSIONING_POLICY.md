# EKB Versioning Policy

The Engineering Knowledge Base is versioned with **Semantic Versioning 2.0.0**
(`MAJOR.MINOR.PATCH`). The current release line is **0.2.0**.

While the major version is `0`, the contract is still stabilizing; breaking
changes may occur in minor releases but must always be documented as a migration.

## Canonical Version Source

`package.json` `version` is the single canonical version. `VERSION` is a mirror
and the release manifest carries a copy; all three must agree. Drift is a
release-validation failure (`scripts/validate-release.py`, check 3).

## What Counts as MAJOR

A change that can break an existing consumer (ECF, a bundle, a conforming
Knowledge Object) without a migration:

- breaking a Knowledge Object schema (removing/renaming a required field);
- removing or renaming a canonical `type` value (e.g. removing `decision_guide`);
- an incompatible change to the relationship model (removing a relationship,
  changing an inverse requirement in a way that invalidates conforming objects);
- an incompatible change to the Engineering Knowledge Package contract;
- removing or renaming a stable validation code (`REL001`–`REL007`) that consumers
  match on.

## What Counts as MINOR

Backward-compatible additions:

- new Decision Guides or other Knowledge Objects;
- new backward-compatible object types;
- new validation rules that do **not** invalidate previously conforming objects
  without a migration;
- new reports or new engine commands;
- new optional metadata fields.

## What Counts as PATCH

Corrections that preserve the contract:

- typo and metadata fixes;
- validator bug fixes that keep the same contract and codes;
- report-generation correctness fixes;
- documentation clarifications.

## How Ontology Migrations Are Versioned

An ontology change to a canonical `type` value (as recorded in `migrations/`) is
a **breaking change** and is therefore **MAJOR** once the contract is stable
(≥ 1.0.0). During the `0.x` line it may ship in a **MINOR** release, but it must:

1. be accompanied by a numbered migration note under `migrations/`;
2. reject the old value in the engine (never silently accept it);
3. declare a downstream bundle-refresh requirement in the migration note and in
   `release/COMPATIBILITY.md`.

Example: the `engineering_decision` → `decision_guide` correction is recorded in
`migrations/MIGRATION-0002-decision-guide-type-final.md` and superseded
`MIGRATION-0001`. Because no consumer had pinned the value and the line is still
`0.x`, it was handled within the `0.2.0` line with a mandatory bundle-refresh note.

## Pre-Release / Build Metadata

Pre-release identifiers (`-rc.1`) and build metadata (`+<sha>`) are permitted by
the validator's semver check but are not used in this line yet.
