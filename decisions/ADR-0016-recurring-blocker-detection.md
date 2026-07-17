# ADR-0016: Recurring Blocker Detection

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: recurring
blocker detection", 2026-07-17)

**Related Work:** ADR-0009 (Wrap-Up — the Blockers field), ADR-0014
(cross-project / ProjectLookup), ADR-0015 (Focus Trends Insights);
`docs/architecture/DOMAIN_MODEL.md` ("Insight" — recurring blockers; "Blocker"
— something preventing progress, visible until resolved).

## Context

Sessions capture a free-text **Blockers** field at wrap-up (ADR-0009), but the
same obstacle recorded across many sessions is currently invisible — you would
have to read every session to notice a pattern. The DOMAIN_MODEL calls out
"recurring blockers" as an Insight. This slice surfaces blockers that come up
repeatedly so they can be addressed rather than re-hit.

## Decision

### A derived detector over the Blockers text (domain)

Add `RecurringBlocker` (representative text, occurrence `Count`, `LastSeenUtc`)
and `WorkSessionService.DetectRecurringBlockers(projectNameOrId = null,
minOccurrences = 2)`:

- considers **closed** sessions whose wrap-up `Blockers` field is non-empty,
  scoped to one project (via the shared `ProjectLookup`) or the whole
  workspace (`null`);
- treats each session's Blockers field as **one** blocker entry;
- groups entries by a **normalized key** — lowercased, whitespace-collapsed —
  so "Waiting on API" and "waiting on  api " count together;
- keeps groups seen in **`minOccurrences` or more** sessions (default 2 —
  "recurring" means at least twice; values below 1 are clamped to 1);
- returns them most-frequent first (ties broken by most-recently-seen), each
  displayed with the most recent original wording.

It is a **pure function of the stored sessions** (the clock is not needed);
it reads state and writes nothing. No new persisted state.

### Surfaces

- **CLI:** `blockers [--project <name|id>] [--min <n>]` — lists the recurring
  blockers with their counts and when each was last seen. Default scope is the
  whole workspace, default threshold 2.
- **GUI:** a read-only **Recurring blockers** panel (workspace scope) listing
  the top recurring blockers with counts, or "None detected yet." The left
  column is wrapped in a scroll viewer so the growing insight panels never
  clip.

## Consequences

- Repeated obstacles become visible across a project or the whole workspace,
  turning the Blockers field from a per-session note into an actionable signal.
- Detection lives in one tested, pure method; both surfaces render it.
- No persistence, schema, or migration impact — derived and read-only.

## Non-goals (this slice)

Splitting a multi-line Blockers field into several blockers, fuzzy/semantic
matching (only exact-after-normalization grouping), resolution tracking
(marking a blocker resolved), per-blocker drill-down, and time-window
filtering — all later slices. This slice establishes exact-match recurring
detection and a first honest presentation.
