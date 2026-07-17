# ADR-0018: Personalized Planning Recommendations

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: personalized
planning recommendations", 2026-07-17)

**Related Work:** ADR-0009 (Wrap-Up / next action), ADR-0012 (planned
durations), ADR-0016 (recurring blockers), ADR-0017 (estimation accuracy);
`docs/architecture/DOMAIN_MODEL.md` ("AI Recommendation" — supports
decision-making, never modifies user data automatically);
`docs/product/PRODUCT_PRINCIPLES.md` (Human in Control); README Phase 4.

## Context

The app now records enough history (session durations, wrap-up next actions,
recurring blockers) to help the user **plan the next session** rather than just
review the past. Roadmap Phase 4 calls for "personalized planning
recommendations."

The product principles bound how: **Human in Control**, and (DOMAIN_MODEL)
recommendations "never modify user data automatically" and "exist to support
decision-making." This app also has **no external AI provider** in scope. So
the recommendations here are **deterministic, data-driven suggestions from the
user's own history** — honest heuristics, not an LLM — presented read-only for
the user to accept or ignore. Nothing is auto-applied.

## Decision

### A read-only recommendation for the next session (service)

Add `PlanningRecommendation` (scope, `SuggestedFocus` + `SuggestedFocusReason`,
`PendingNextAction`, `TopBlocker`) and
`WorkSessionService.RecommendPlanning(projectNameOrId = null)`.

Unlike the workspace-wide insights, planning is about the **next session**, so
the default scope is the **active project** (`null` → active; a reference →
that project). It composes existing, tested signals:

- **Suggested focus** — the median actual duration of the project's most recent
  (up to 5) closed sessions, rounded to the nearest 5 minutes (floor 5).
  Requires at least 2 closed sessions; otherwise no number is suggested and the
  reason says so. Median (not mean) is used so a single outlier session does
  not skew the suggestion.
- **Pending next action** — the `NextAction` from the most recent closed
  session that recorded one (the thing you said you'd do next).
- **Top blocker** — the project's most frequent recurring blocker
  (`DetectRecurringBlockers`, ADR-0016), if any, as a heads-up.

Pure over the stored sessions; reads state, **writes nothing** and applies
nothing.

### Surfaces

- **CLI:** `recommend [--project <name|id>]` — prints the suggested focus (with
  its basis), any pending next action, and any recurring blocker to watch.
- **GUI:** a read-only **"For your next session"** panel in the active-project
  column. It is advisory only — the user still sets the timer / starts the
  session themselves; nothing is pre-filled or auto-started.

## Consequences

- The app moves from reflection to gentle, personalized planning help while
  keeping the human in control — no auto-apply, no external AI.
- Built entirely from existing data and prior insight methods; no persistence,
  schema, or migration impact.

## Non-goals (this slice)

Auto-filling the timer or auto-starting sessions, cross-project "what should I
work on next" ranking, LLM-generated advice, goal/deadline planning, and
confidence intervals — later slices (some require an AI provider, explicitly
out of scope here). This slice delivers honest, data-derived suggestions the
user chooses to act on.
