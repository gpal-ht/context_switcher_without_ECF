# ADR-0026: Harden Persistence — Concurrency and Schema Migration

**Status:** Accepted

**Date:** 2026-07-18

**Approved by:** Project Owner (directive: "build all four slices at once",
2026-07-18)

**Related Work:** ADR-0008 (Work Engine foundation, `IWorkspaceStore` port and
atomic JSON file adapter), ADR-0009 (work-session lifecycle, additive-field
schema policy); `docs/product/PRODUCT_PRINCIPLES.md` (data is the user's).

## Context

`JsonFileWorkspaceStore` (ADR-0008) persists the whole `WorkspaceState` to a
single `workspace.json` with an atomic temp-file-then-`Move` write, and every
service mutation is a load → mutate → save round trip. Two gaps remained:

1. **Concurrency.** The load and save are separate calls with the mutation in
   between (in `ProjectRegistry` / `WorkSessionService`), and nothing guards
   that window across processes or threads. Two writers can each load the same
   state, mutate, and save — the second silently discards the first under
   last-writer-wins. The app can plausibly run more than once (a second launch,
   a background task), so this is a real lost-update risk, not a theoretical one.

2. **Schema migration.** Version handling was a bare string (in)equality check:
   *any* version other than the exact current one — older or newer — was treated
   as corruption and rejected. There was no forward path for an older file and
   no structure for future migrations to slot into.

## Decision

### 1. A guarded read-modify-write primitive on the store port

Add `WorkspaceState Update(Func<WorkspaceState, WorkspaceState> mutate)` to
`IWorkspaceStore`. It performs load → mutate → save as one critical section. In
`JsonFileWorkspaceStore` that section is protected by a **sibling lock file**
(`workspace.json.lock`) opened with `FileShare.None`: the OS grants that handle
to exactly one holder at a time, across both processes and threads on the
machine. Acquisition uses a **bounded exponential backoff** (2 ms → 25 ms) up to
a configurable timeout (default 10 s); on timeout it throws the new domain
exception `StoreLockedException` rather than hanging. The write itself stays the
existing atomic temp-then-move, so a concurrent reader never sees a torn file.

`Load` and `Save` are unchanged and remain lock-free: atomic replace already
makes a plain read see either the whole old file or the whole new one, and the
existing single-process behavior and every existing test are preserved. The
`InMemoryWorkspaceStore` test seam implements `Update` with a simple monitor
lock. Services are **not** rewired to `Update` in this slice (out of scope, see
Non-goals); the guarded primitive is the foundation for that follow-up.

### 2. Explicit, extensible schema migration

Introduce `WorkspaceMigrator`. On load it parses the file's `schema_version`
semantically (via `System.Version`) and compares it to
`WorkspaceState.CurrentSchemaVersion`:

- **equal** — loaded as-is;
- **older or blank/absent** — run an ordered migration pipeline (empty today:
  0.1.0 is the first schema, so this is a no-op re-stamp) and stamp the current
  version **in memory only**; loading never rewrites the file, so the upgrade is
  persisted on the next save;
- **newer** — rejected with a clear `StoreCorruptException` naming both versions,
  so a build never silently drops fields it does not understand;
- **unparseable** — rejected as corrupt.

Future breaking shape changes bump `CurrentSchemaVersion` and append a step to
`WorkspaceMigrator.Migrations`. Additive optional fields still stay on the
current version (ADR-0009), so older files keep loading without a migration.

## Consequences

Positive:

- Concurrent updates through `Update` no longer lose data; a contended writer
  fails fast with an actionable `StoreLockedException` instead of hanging.
- Because the guard is an OS file handle, a crashed holder's lock is released by
  the OS on process exit — there is no stale-lock sentinel to clean up and no
  deadlock after a crash. The leftover empty `.lock` file is harmless.
- Migration is explicit and structured; older files upgrade cleanly and newer
  files fail loudly and safely, never mutating user data on read.

Negative / honest limits of file-lock concurrency on Windows:

- The lock is **cooperative**: it only protects code paths that go through
  `Update`. Direct `Load`/`Save` (and anything editing `workspace.json` outside
  the app) still race under last-writer-wins. Until the services are migrated to
  `Update`, their existing mutations are not yet serialized.
- `FileShare.None` is a **single-machine** guarantee. It is reliable for the
  local `%LOCALAPPDATA%` data home this app uses; it is not a distributed lock
  and should not be relied on over a network share, where SMB caching/oplocks
  make exclusivity unreliable.
- Exclusivity is enforced per **logon session** semantics of the file system,
  which fits a single-user desktop app; it is not a cross-user or cross-session
  coordination mechanism.
- Under heavy contention a writer can exhaust the timeout and must retry; the
  primitive surfaces that rather than blocking indefinitely.

## Non-goals (this slice)

Rewiring `ProjectRegistry` / `WorkSessionService` to route their mutations
through `Update` (a mechanical follow-up now that the primitive exists);
cross-machine or networked coordination; a real (non-no-op) migration step;
changing the on-disk shape. This slice delivers the guarded `Update` primitive,
the `StoreLockedException` failure mode, and the explicit migration framework,
with deterministic tests, keeping every existing file loadable.
