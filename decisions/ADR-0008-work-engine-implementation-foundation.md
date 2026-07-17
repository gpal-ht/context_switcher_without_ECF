# ADR-0008: Work Engine Implementation Foundation

**Status:** Accepted

**Date:** 2026-07-16

**Approved by:** Project Owner (directive to resume product development,
standalone-first, 2026-07-16)

**Related Work:** MVP_SCOPE.md; docs/features/project_context_switch.md;
ADR-0001 (WinUI 3), ADR-0002 (Modular Platform), ADR-0004 (Event-Driven),
ADR-0005 (Canonical Subsystems), ADR-0007 (Optional ECF)

## Context

Product implementation is beginning with the first vertical slice of the
project-to-project context switch feature: the **project registry with
active-project selection** (feature doc MVP requirements "a list of
projects" and "an active project"). The repository previously contained no
application code, so this slice sets the initial implementation
conventions. Two hard constraints shape them:

1. **Offline toolchain.** Development environments may not access the
   network. The NuGet cache is empty, so no external package — including
   Windows App SDK/WinUI 3 and xunit — can be restored. Only the installed
   .NET SDK (currently 10.0.x) is available.
2. **Standalone-first.** Product code must run and be verified with no ECF
   present (ADR-0007) and must never reference `vendor/ecf`.

## Decision

### Source layout and module boundaries

```text
src/
  Directory.Build.props                     shared compiler settings
  Work/ContextSwitcher.Work/                Work Engine module (class library)
  Work/ContextSwitcher.Work.Tests/          deterministic test runner (console)
  App/ContextSwitcher.Cli/                  interim command-line harness
```

- Modules follow ADR-0002/ADR-0005: the Work Engine owns work-lifecycle
  state; future subsystems get sibling module directories.
- Namespace root: `ContextSwitcher.<Subsystem>`.

### Pure-BCL policy (network-restricted environments)

Product projects declare **no PackageReference** while the offline
constraint stands. Consequences accepted deliberately:

- **Tests:** a minimal in-repo test framework (`[Test]` attribute +
  reflection runner, non-zero exit on failure) substitutes for xunit. It is
  an honest, deterministic gate — not a mock of one. Migrate to a standard
  framework when package restore becomes available.
- **CLI parsing, JSON:** hand-rolled argument handling and
  `System.Text.Json` (in-box).

### Interim CLI harness — WinUI 3 remains the product UI

ADR-0001 stands: the product UI is WinUI 3. Windows App SDK cannot be
restored offline, so the observable surface for early slices is
`ContextSwitcher.Cli`, a thin harness over Work Engine services. It must
stay thin: command parsing + service calls + text output only. Business
rules live in the module, so the future WinUI shell binds to the same
services. The CLI is a development/product harness, not a committed
second product surface.

### Persistence — versioned JSON file behind a store port

- Port: `IWorkspaceStore` (Context Switcher-owned; adapters:
  `JsonFileWorkspaceStore` for production, `InMemoryWorkspaceStore` for
  tests). Storage technology is intentionally replaceable; the
  architecture docs prescribe none.
- Location: `%LOCALAPPDATA%\ContextSwitcher\workspace.json`, overridable
  with the `CONTEXT_SWITCHER_DATA_HOME` environment variable (directory).
- Format: single JSON document with a top-level `schema_version` (starts
  at `0.1.0`); unknown versions are a clear read error, reserving the
  migration path.
- Writes are **atomic** (write temp file, then move over the target).
- A corrupted or unreadable store is a **hard, named failure**
  (`StoreCorruptException`); the application never silently resets or
  overwrites user data.

### Domain conventions for this slice

- `Project` carries exactly the feature-doc required data: id (GUID),
  name, description, status, created, updated (UTC, `DateTimeOffset`).
- `status` values start minimal: `active | archived` (the feature doc
  names the field but not its values; extend deliberately later).
- Names are required, trimmed, ≤ 200 characters, and unique
  case-insensitively across the workspace.
- Invariants: at most one active project; an archived project cannot be
  the active project; the active project cannot be archived.
- Failure model: typed exceptions (`ValidationException`,
  `NotFoundException`, `StoreCorruptException`) mapped to distinct CLI
  exit codes; messages are user-readable and never leak stack traces.

### Event-driven design deferred

ADR-0004 (event-driven application design) is not implemented in this
slice: there is no event consumer yet, and abstractions without consumers
are prohibited by the working agreement. Introduce events when the first
real consumer (e.g., the wrap-up flow or UI notifications) arrives.

### Verification

`acceptance_tests/check_product_tests.sh` builds `src/` and runs the Work
Engine test suite; it joins the **standalone** acceptance suite (required
gate). The .NET SDK is now required toolchain for the standalone gate —
its absence is a clear FAIL, not a silent skip. The dependency-boundary
test additionally scans `*.cs` so product code can never reference
`vendor/ecf`.

## Consequences

- Product development proceeds offline, standalone-first, with
  deterministic verification and no new dependencies.
- The WinUI 3 shell is a future slice gated on package availability; until
  then the CLI harness exposes Work Engine behavior.
- The in-repo test framework and JSON store are deliberate, replaceable
  stopgaps recorded here so they are revisited rather than fossilized.
