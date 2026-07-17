# ADR-0015: Focus Trends Insights

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: focus trends
insights", 2026-07-17)

**Related Work:** ADR-0009 (Work Session Lifecycle), ADR-0012 (Timer-Driven
Switching — planned durations), ADR-0013 (Overrun), ADR-0014 (cross-project);
`docs/architecture/DOMAIN_MODEL.md` ("Insight" — a higher-level observation
derived from historical work: focus trends, estimation accuracy); README
Phase 4 (Productivity Intelligence).

## Context

The app has accumulated the raw material for insight — closed sessions with
durations, planned durations (ADR-0012), outcomes, and per-project scoping —
but presents only individual records. The DOMAIN_MODEL's "Insight" concept and
the roadmap's Phase 4 call for **derived observations**: how much focused work
is happening, how it trends, and how well time is being estimated. This slice
introduces the first insight — **focus trends** — computed from existing data.

## Decision

### A pure, derived insights value (domain)

Add `FocusInsights`, a computed summary over **closed** sessions for a scope
(one project or the whole workspace):

- `SessionCount`, `TotalFocus`, `AverageFocus`;
- `OutcomeCounts` (per `SessionOutcome`) and a derived `CompletionRate`;
- **Estimation accuracy** for timed sessions: `TimedCount`, `OverranCount`,
  `AverageOverrun` (signed — positive means sessions tended to run over);
- **Week-over-week trend**: `RecentFocus` (last 7 days) vs `PriorFocus`
  (the 7 days before that).

`WorkSessionService.ComputeInsights(projectNameOrId = null)` computes it —
`null` = all projects; a reference = that project (via the shared
`ProjectLookup`, ADR-0014). It reads state once and is a **pure function of
the stored sessions plus the injected clock** (the clock drives the 7-day
windows), so it is fully deterministic and unit-tested. No new persisted
state; nothing is written.

### Surfaces

- **CLI:** `insights [--project <name|id>]` prints the focus-trends report
  (totals, average, outcome breakdown, estimation accuracy, this-week vs
  last-week). Default scope is the whole workspace.
- **GUI:** a read-only **Focus trends** panel (workspace scope) that
  recomputes on refresh, showing the same figures phrased for people.

## Consequences

- Users get a first productivity insight from data they already recorded,
  reinforcing the value of wrapping up sessions and setting focus timers.
- Insight logic lives in one tested, pure method; both surfaces render it.
- No persistence, schema, or migration impact — this is derived and read-only.

## Non-goals (this slice)

Per-day charts or visualizations, configurable windows, recurring-blocker
text mining, cross-session goal tracking, and GUI scope/time filters — later
slices. This slice establishes the insight computation and a first, honest
presentation of focus trends.
