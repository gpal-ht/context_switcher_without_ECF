# ADR-0011: WinUI 3 GUI Shell

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the WinUI 3 GUI shell",
2026-07-17, after authorizing the WinUI 3 dependency/network exception)

**Related Work:** ADR-0001 (Use WinUI 3), ADR-0008 (Work Engine Foundation),
ADR-0009 (Work Session Lifecycle)

## Context

ADR-0008 recorded that WinUI 3 could not be built in the offline development
environment (the Windows App SDK is a NuGet dependency with no cached copy),
so the observable surface was an interim CLI harness over the Work Engine.
That constraint is now lifted: the owner authorized a scoped network
exception for NuGet, the Windows App SDK restores, and — critically —
Visual Studio 2022 (v18) is installed locally, providing the MSIX/PRI
MSBuild tasks that the bare .NET SDK lacks. WinUI 3 apps therefore build and
run here. This ADR affirms ADR-0001 (WinUI 3 remains the product UI) and
records how the GUI shell is structured and built.

## Decision

### The GUI is a thin presentation layer over the Work Engine

The shell adds no business logic. It binds to the existing, tested
application services — `ProjectRegistry` and `WorkSessionService`
(`ContextSwitcher.Work`) — through view-models. The services already proved
UI-agnostic under the CLI; the WinUI shell is a second presentation over the
same seam. Persistence, invariants, and the failure model are unchanged
(ADR-0008/0009).

```
ContextSwitcher.Work  (services + domain, net10.0, pure BCL)
        ▲                         ▲
        │ project reference       │ project reference
ContextSwitcher.Cli          ContextSwitcher.App (WinUI 3, net10.0-windows)
  (interim harness)            ViewModels (INotifyPropertyChanged) → XAML views
```

### Project shape

- New project `src/App/ContextSwitcher.App` — WinUI 3, unpackaged
  (`WindowsPackageType=None`) so it launches as a plain `.exe` with no MSIX
  deployment. TFM `net10.0-windows10.0.19041.0`; references
  `Microsoft.WindowsAppSDK`.
- MVVM: `INotifyPropertyChanged` view-models (`ShellViewModel`,
  `ProjectViewModel`) mediate between XAML and the services. Views are
  code-light; commands call service methods and refresh observable state.
- The CLI (`ContextSwitcher.Cli`) remains as a scriptable/testable surface;
  it is not removed. Both surfaces share the same services.

### Build path — Visual Studio MSBuild, not `dotnet build`

WinUI 3's resource (PRI) generation needs `Microsoft.Build.Packaging.Pri.Tasks.dll`,
which ships with Visual Studio, not the .NET SDK. `dotnet build` looks only
in the SDK and fails. Therefore the GUI is built with the installed VS
MSBuild via `scripts/build-gui.ps1`, which:
1. locates VS MSBuild (vswhere, or a configured path),
2. restores, then builds (separately — a combined `-t:Restore,Build`
   evaluates XAML targets with stale imports and fails).

The pure-BCL projects (Work library, tests, CLI) continue to build/test with
`dotnet build` and remain the required acceptance gate. The GUI build is a
separate, VS-dependent step and is **not** added to the default `dotnet`
acceptance suite (so the offline/pure-BCL gate stays intact for anyone
without VS).

### Data location

The GUI uses the same `JsonFileWorkspaceStore` and honors
`CONTEXT_SWITCHER_DATA_HOME`, so CLI and GUI operate on one workspace file.

## Consequences

- Context Switcher now has a real, runnable WinUI 3 window that exercises the
  full project + work-session flow against live persisted state.
- Building the GUI requires Visual Studio (for the PRI/MSIX MSBuild tasks)
  and network access to restore the Windows App SDK — both now available and
  recorded as project prerequisites for GUI work. The core app (services,
  CLI, tests) still builds offline with the .NET SDK alone.
- ADR-0008's "interim CLI, WinUI blocked" note is superseded in practice by
  this ADR; the CLI is retained as a secondary surface, not the only one.
- Safety (CLAUDE.md): the shell is an ordinary desktop window — no
  always-on-top lock, no blocking of Task Manager/Alt-Tab, a normal close
  button; interruptive behaviors (timers) are out of scope for this slice.

## Non-goals (this slice)

Timer-driven switching, notifications/tray, packaging/MSIX installer,
theming polish, and accessibility automation testing are later slices. This
ADR covers the runnable shell and its build path only.
