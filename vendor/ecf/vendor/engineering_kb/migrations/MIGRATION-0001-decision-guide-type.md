# MIGRATION-0001 — Decision Guide Type Canonicalization

> **SUPERSEDED by [MIGRATION-0002](MIGRATION-0002-decision-guide-type-final.md).**
> This migration standardized the DG type on `engineering_decision`. A subsequent
> ontology review (`reviews/ONTOLOGY_REVIEW.md`) found that value names the
> object's *purpose* rather than its *identity*. The canonical type is now
> **`decision_guide`**. This document is retained as accurate history of the
> intermediate step; do not act on its "New (canonical)" value — see 0002.

## Summary

The Knowledge Object `type` value for a Decision Guide is standardized to
`engineering_decision`. The value `decision_guide` is a **rejected legacy alias**.

## Old vs New Representation

| | Value |
|---|---|
| **Old (legacy, rejected)** | `type: decision_guide` |
| **New (canonical)** | `type: engineering_decision` |

The human-readable class name remains "Decision Guide" and the stable ID prefix
remains `DG-`. Only the machine `type` field is affected.

## Why `engineering_decision` Was Chosen

Repository evidence, not preference:

- `knowledge_model/KNOWLEDGE_OBJECT_STANDARD.md` — the authoritative object
  standard — specifies `type: engineering_decision` for a Decision Guide, both in
  the minimum-metadata example and the "Object Types" section.
- `standards/DECISION_GUIDE_STANDARD.md` scopes itself to
  `type: engineering_decision`.
- The only occurrences of `decision_guide` were the source object (already
  migrated), permissive aliases in the engine, test fixtures, and one gitignored
  generated package.

Two authoritative standards prescribe `engineering_decision`; the alias was an
accidental inconsistency, so **Option A (one canonical type)** was chosen.
Option B (a separate `object_class` field) was explicitly rejected — there is no
second concept to preserve, only an accident.

## Affected Files

| File | Change |
|---|---|
| `decision_guides/architecture/should_introduce_another_subsystem.md` | `type` set to `engineering_decision` (done in the prior batch) |
| `engine/ekb.py` | `engineering_decision` is the only canonical decision type; `decision_guide` is a rejected legacy alias that fails validation; retrieval, ordering, labels, and scoping use the canonical value |
| `engine/test_engine.py` | fixtures use `engineering_decision`; a test asserts the legacy value is rejected |
| `knowledge_model/KNOWLEDGE_OBJECT_STANDARD.md` | note added declaring `decision_guide` a rejected legacy alias |
| `generated/packages/EKP-ARCH-0001-subsystem-decision.md` | stale (embeds `decision_guide`); gitignored, non-canonical; flagged by `ekb.py packages`, to be regenerated — **not** hand-edited |

## Validation Behavior After Migration

- A Knowledge Object with `type: decision_guide` now **fails** validation:
  `legacy type 'decision_guide' — migrate to 'engineering_decision'`.
- Two `type:` keys in one object's front matter now **fail**:
  `duplicate/conflicting front-matter key 'type'`.
- `ekb.py packages` flags any generated package embedding the legacy token.

## Downstream Impact on ECF Bundles

- ECF and any bundled EKB copies inside other repositories were **not** modified
  by this batch (out of ownership).
- **Action required before the next cross-repository experiment:** any ECF bundle
  that pinned or matched `type: decision_guide` must be refreshed to
  `engineering_decision`. Until refreshed, a bundle filtering on the old string
  will not match the migrated Decision Guide.

## Compatibility Expectations

- **Not** backward-compatible at the `type`-string level: consumers matching the
  literal `decision_guide` must update. This is intentional — the legacy value is
  rejected, not silently accepted, so the inconsistency cannot silently return.
- An old *generated package* can still be **read** by a human, but it fails the
  staleness check and must not be treated as current.
