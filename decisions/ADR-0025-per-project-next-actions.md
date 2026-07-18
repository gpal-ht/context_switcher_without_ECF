# ADR-0025: Per-Project Next-Actions (Open Work Items)

**Status:** Accepted

**Date:** 2026-07-18

**Approved by:** Project Owner (directive: "build all four slices at once",
2026-07-18)

**Related Work:** ADR-0008 (Work Engine, pure-BCL, domain errors), ADR-0009
(work-session history + additive schema), ADR-0014 (shared `ProjectLookup`
resolution), ADR-0019 (what-to-work-on-next); `ResumeBrief`;
`docs/product/PRODUCT_PRINCIPLES.md` (Human in Control).

## Context

The resume brief already replays the *last session's* free-text "next action"
hint, but there is no durable, per-project list of the concrete things that
remain unfinished. A user returning to a project cannot see, at a glance, the
open work items they left behind — they are buried inside individual session
wrap-ups. This slice adds a lightweight, explicit **next-actions** list per
project so "what remains unfinished" is a first-class, resumable fact.

## Decision

### Domain model — an immutable `NextAction` record

`NextAction` (id, projectId, text, createdUtc, `Status` {Open, Done},
completedUtc?) mirrors the `WorkSession`/`Project` record idiom: `required`
init-only members, a `[JsonIgnore]`-derived `IsOpen`, and a static
`NormalizeText` guard (blank → `ValidationException`, 1000-char cap). Completion
is recorded immutably by producing a `Done` value with a `completedUtc`.

### Additive persistence

`WorkspaceState` gains a `List<NextAction> NextActions` collection. It is
**additive on schema 0.1.0** (ADR-0009): a file written before the field
existed has no `next_actions` key and deserializes to an empty list, with no
schema-version bump. Writes remain atomic via `JsonFileWorkspaceStore`.

### Service — `NextActionService`, deterministic and clock-injected

A dedicated service alongside `WorkSessionService`, sharing the same
`IWorkspaceStore` and injected clock:

- `AddNextAction(projectRef, text)` — resolves the project via the shared
  `ProjectLookup` (blank → validation, unknown → not-found).
- `CompleteNextAction(id)` — idempotent; accepts a full id or any unambiguous
  prefix (unknown → not-found, ambiguous → validation).
- `ListOpenNextActionsForActiveProject()` and `ListNextActions(projectRef)`.

`GetResumeBriefForActiveProject` is extended (additively) to attach the active
project's **open** next-actions to the `ResumeBrief`.

### CLI noun — `todo`, deliberately distinct from `next`

There is already a `next` command (ADR-0019, *what project to work on next*).
To avoid overloading that noun, next-actions use **`todo`**:

- `todo add [--project <name|id>] <text>` (defaults to the active project)
- `todo done <id>` (id or short prefix)
- `todo list [--project <name|id>] [--all]` (**open-only by default**)

Exit codes follow the existing contract (0 ok, 2 validation/usage, 3 not-found).
Open next-actions are also surfaced by `resume`.

## Consequences

- Returning to a project shows its open work items directly, not just the last
  session's parting note — the two are complementary and both appear on resume.
- Old workspace files keep loading unchanged (additive field); no migration.
- The `todo` noun keeps the CLI unambiguous next to `next`; ids are shown
  abbreviated for ergonomics and accepted as prefixes on completion.

## Non-goals (this slice)

Due dates, priorities/ordering, reordering, editing text, deleting actions,
sub-tasks, cross-project rollups, and any AI ranking. Completion is one-way
(no reopen) for now. The WinUI binding is best-effort and does not gate the
offline build. These can follow if the primitive proves useful.
