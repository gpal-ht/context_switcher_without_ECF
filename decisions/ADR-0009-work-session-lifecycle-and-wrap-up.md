# ADR-0009: Work Session Lifecycle and Wrap-Up

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "Let's start the work sessions
and wrap-up slice", 2026-07-17)

**Related Work:** docs/features/project_context_switch.md (MVP requirements
"a current work session", "wrap-up form", "session history");
docs/architecture/WORK_SESSION_MODEL.md; docs/architecture/DOMAIN_MODEL.md;
ADR-0008 (Work Engine Implementation Foundation)

## Context

The project registry (ADR-0008) delivered the first two MVP requirements
(a project list and an active project). The next vertical slice is the core
of the product's value proposition — recording a **work session** and its
**wrap-up**, so the app can answer the MVP questions: what was I working on,
what did I finish, what is still open, what should future-me know, what is
next. This ADR fixes the session lifecycle, the wrap-up shape, and the
persistence-evolution rule; it follows the ADR-0008 conventions (pure-BCL,
standalone-first, interim CLI harness, store port).

## Decision

### Session lifecycle (single-user, one open session)

- A **work session** belongs to one project and has: id, project id,
  optional objective (the "session intention" of WORK_SESSION_MODEL.md),
  start time, optional end time, and — once ended — a wrap-up. A session is
  *open* until it is ended.
- **At most one open session exists across the workspace.** This models the
  product's central discipline: you are either in a focused session or you
  are not. `StartSession` fails if one is already open.
- `StartSession` starts a session on the **active project** (ADR-0008). It
  fails clearly if there is no active project. Starting does not change the
  active project.
- `EndSession` ends the single open session with a **required outcome** and
  an **optional wrap-up**; it fails if no session is open.
- Session operations are scoped to the **active project** for this slice
  (start on it; history and resume brief for it). Per-project history for
  arbitrary projects is a deliberate follow-up, kept out to bound review.

### Wrap-up: outcome required, reflection optional (calm, not punitive)

- WORK_SESSION_MODEL.md states every session ends with **exactly one
  outcome**, so `SessionOutcome` is **required** at end. The nine canonical
  outcomes are modeled verbatim: Completed, PartiallyCompleted, Blocked,
  Replanned, Superseded, Cancelled, Interrupted, ResearchCompleted,
  DecisionReached.
- The reflective wrap-up fields — completed work, unfinished work, blockers,
  future-self notes, next action (DOMAIN_MODEL.md "Wrap-Up") — are **all
  optional** free text. This honors the UX principle that the form must feel
  calm and be quick to complete (open questions #2/#4 in the feature doc are
  resolved this way for the MVP; revisit with usage evidence). Text is
  trimmed and length-capped.

### Resume brief

- `GetResumeBrief` for the active project returns the most recent **closed**
  session's wrap-up (previous outcome, unfinished work, blockers,
  future-self notes, next action) — the DOMAIN_MODEL.md "Resume Brief",
  initial form. Null when the project has no completed session yet. No AI
  (out of scope, MVP non-goal).

### Persistence — additive within the schema version line

- `WorkspaceState` gains a `sessions` list. This is a **purely additive,
  backward-compatible** change: a `0.1.0` file written by the registry slice
  (no `sessions` key) still loads — the field defaults to empty — and files
  this build writes remain readable by the registry-only build (the unknown
  key is ignored). Therefore `schema_version` **stays `0.1.0`**.
- Rule established here: **additive optional fields do not bump the schema
  version; a version bump plus a migration step is reserved for breaking
  shape changes** (renames, removals, semantic changes). The store's
  exact-version rejection and the corrupt-store safety (ADR-0008) are
  unchanged. This keeps existing user data valid with no migration code
  while preserving the versioned-migration seam for when it is truly needed.

### Failure model and boundaries

- Reuses ADR-0008 typed exceptions (`ValidationException`,
  `NotFoundException`, `StoreCorruptException`) and CLI exit-code mapping
  (2/3/4). Session logic lives in a new `WorkSessionService` in the Work
  Engine, sharing the `IWorkspaceStore` port; the CLI stays a thin harness.
  No ECF involvement — this is pure standalone product behavior.

## Consequences

- The end-to-end MVP flow becomes demonstrable: start a session on the
  active project → end it with a wrap-up and outcome → switch project →
  read the resume brief → start the next session.
- No persistence migration is required; existing workspaces keep working.
- Arbitrary-project history, timers/auto-switch, and AI-assisted wrap-ups
  remain future slices (MVP non-goals or later requirements).
- The "outcome required / reflection optional" and "additive-schema" calls
  are recorded here so they are revisited deliberately, not by accident.
