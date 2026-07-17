# ADR-0013: Session History View

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: session
history view", 2026-07-17)

**Related Work:** ADR-0009 (Work Session Lifecycle), ADR-0011 (WinUI 3 GUI
Shell), ADR-0012 (Timer-Driven Switching); `docs/features/project_context_switch.md`
(MVP requirement "session history").

## Context

Sessions are recorded with a rich wrap-up (outcome, completed/unfinished
work, blockers, future-self notes, next action) and, since ADR-0012, a
planned focus duration. But that detail is effectively **write-only** in the
app: `session list` (CLI) and the GUI history pane show only a one-line
summary per session. There is no way to review a past session's full
reflection — which is the whole point of preserving context. This slice adds
a **detail view** over the existing history so a completed session can be
inspected, including how its actual time compared to its plan.

## Decision

### A derived planned-vs-actual measure (domain)

Add `WorkSession.Overrun` — the signed difference between a **closed** timed
session's actual `Duration` and its `PlannedDuration` (positive = ran over,
negative = finished early). Null for untimed or still-open sessions. This is
a pure derived property (not persisted), unit-tested with the clock-injection
pattern; it integrates the timer (ADR-0012) into history without new state.

### Inspecting a session

- **CLI:** `session show <n>` prints the full detail of the n-th most-recent
  session for the active project (1 = most recent): project, objective,
  start/end (UTC), duration, planned duration and over/under, outcome, and
  every wrap-up field that is present. `n` is validated against the history
  length. `session list` remains the summary index.
- **GUI:** the history list becomes **selectable**; selecting an entry shows
  a read-only detail pane with the same information, phrased for people
  ("ran 5m over" / "finished 3m early"). No editing of past sessions in this
  slice — history is a record, not a form.

### Scope stays on the active project

History remains scoped to the **active project** (ADR-0009). Browsing an
arbitrary project's history without switching to it is still a deliberate
follow-up; this slice deepens (detail) rather than widens (cross-project) the
view, to stay reviewable.

## Consequences

- A recorded wrap-up can now be read back, in both surfaces, making the
  captured context actually useful on return.
- Planned-vs-actual surfaces naturally in history, closing the loop with the
  focus timer.
- No persistence change (Overrun is derived); no schema bump; existing data
  displays unchanged.

## Non-goals (this slice)

Editing or deleting past sessions, cross-project history browsing, search/
filter, export, and aggregate stats (focus trends, estimation accuracy) —
all later slices.
