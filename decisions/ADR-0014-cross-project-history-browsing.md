# ADR-0014: Cross-Project History Browsing

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: cross-project
history browsing", 2026-07-17)

**Related Work:** ADR-0009 (Work Session Lifecycle — deferred cross-project
history), ADR-0013 (Session History View), ADR-0008 (Work Engine).

## Context

Session history is currently scoped to the **active project**
(`ListSessionsForActiveProject`, CLI `session list`/`show`, and the GUI history
pane). ADR-0009 and ADR-0013 both deferred browsing an *arbitrary* project's
history. That deferral is the gap this slice closes: you should be able to look
at another project's past sessions **without switching to it** — switching the
active project is a deliberate context change (and is blocked for archived
projects), so it is the wrong tool for a quick look back.

## Decision

### A project-scoped history query (service)

Add `WorkSessionService.ListSessions(projectNameOrId)` — resolve the named/id'd
project and return its sessions, most recent first. It does **not** change the
active project. `ListSessionsForActiveProject` remains for the common case.

### Share project resolution (small refactor)

The name/id resolution logic (`Resolve`/`FindByName`) previously lived
privately in `ProjectRegistry`. With a genuine second consumer, it moves to an
internal `ProjectLookup` helper used by both `ProjectRegistry` and
`WorkSessionService`, so the two cannot drift on resolution semantics
(case-insensitive name, exact id, the same `NotFound`/`Validation` messages).
`ProjectRegistry` behavior is unchanged — it just delegates.

### CLI

`session list` and `session show` gain an optional `--project <name|id>`:
- `session list [--project <p>]` — omit for the active project.
- `session show <n> [--project <p>]` — inspect the n-th session of any project.

The active project remains the default so existing usage is unchanged.

### GUI

The history section gains a **"History for" project selector** (a ComboBox of
all projects, defaulting to the active project). Choosing a project loads its
sessions into the same selectable list + detail pane — **without** changing the
active project or the session controls (which stay bound to the active project).
The chosen history project is preserved across refreshes while it still exists.

## Consequences

- Any project's history is reviewable from either surface without disturbing the
  active-project context or an in-progress session.
- Resolution logic is defined once (`ProjectLookup`); `ProjectRegistry` and
  `WorkSessionService` share it.
- No persistence or schema change — this is a read/query and presentation
  capability over existing data.

## Non-goals (this slice)

Cross-project resume brief, search/filter across projects, aggregate/rollup
stats, and editing history remain out (later slices). Session start/end still
operate only on the active project.
