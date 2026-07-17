# ADR-0019: "What Should I Work On Next" Suggestion

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: what should
I work on next", 2026-07-17)

**Related Work:** ADR-0008 (project registry), ADR-0009 (Wrap-Up / next
action), ADR-0016 (recurring blockers), ADR-0018 (planning recommendations —
per-project); `docs/product/PRODUCT_PRINCIPLES.md` (Human in Control);
`docs/features/project_context_switch.md` ("next project selection").

## Context

ADR-0018 recommends how to plan the next session **on a given project**. The
complementary question is **which project** to pick up next — the feature
doc's "next project selection" and a natural close to the context-switch loop
(wrap up A → what next?). This slice ranks the user's projects and suggests
where to go, from recorded history. Same principles apply: a **deterministic,
transparent, non-authoritative** suggestion (no external AI); the user still
switches projects themselves — nothing is auto-selected.

## Decision

### A ranked, cross-project suggestion (service)

Add `NextProjectSuggestion` (project name, `IsActive`, `LastWorkedUtc`,
`PendingNextAction`, `Reason`) and
`WorkSessionService.SuggestNextProject()` → the **non-archived** projects,
ranked best-first by a transparent rule:

1. projects with a **pending next action** first — you have a clear,
   low-friction entry point (you already wrote down what to do);
2. then **most recently worked** first — resume with momentum;
3. then by name, for stable ordering.

Per project it reports the last-worked time, the pending next action (the most
recent session that recorded one), and a plain-language reason
("You left off with a clear next step." / "Recently active." / "Not started
yet."). Archived projects are excluded; the active project is flagged, not
privileged.

Pure over the stored projects/sessions; reads state, **writes and selects
nothing**.

### Surfaces

- **CLI:** `next` — the ranked list with each project's reason, pending next
  action, and last-worked time, plus a reminder to switch manually.
- **GUI:** a read-only **"What to work on next"** panel near the project list,
  listing the top suggestions. Advisory only — switching stays a manual action.

## Consequences

- Closes the context-switch loop: after wrapping up, the app helps choose the
  next project without deciding for the user.
- Reuses existing data (projects, sessions, wrap-up next actions); no
  persistence, schema, or migration impact.
- The ranking rule is simple and explained per-project, so a suggestion is
  never a black box.

## Non-goals (this slice)

Deadlines/priority fields, weighting by blockers or staleness thresholds,
"nudge me about neglected projects," and any auto-switch — later slices. This
delivers a transparent ranked suggestion the user acts on.
