# ADR-0022: Application Icon for the Executable and Window

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: .ico for the
exe window", 2026-07-17)

**Related Work:** ADR-0021 (branded icons), ADR-0020 (MSIX packaging),
ADR-0011 (WinUI 3 GUI shell).

## Context

ADR-0021 branded the MSIX **package** assets (tiles, Start, Store, splash). But
the raw executable — used by the unpackaged dev-run and shown in Explorer, the
taskbar, and the WinUI window titlebar — still carried the **default .NET
icon**. This slice gives the exe and its window the brand icon.

## Decision

### One reproducible `.ico`, embedded in the exe

Extend `scripts/generate-assets.ps1` to emit `Assets/app.ico` — a multi-size
icon (16/24/32/48/64/128/256) rendered from the **same brand mark** as the PNG
assets, packed as a PNG-compressed ICO. The brand stays defined in one script.

The app project sets `<ApplicationIcon>Assets\app.ico</ApplicationIcon>`, which
embeds the icon as the exe's Win32 resource. Windows then uses it for the exe
file icon and the taskbar.

### Explicit titlebar icon for certainty

WinUI 3 does not always adopt the exe icon for the window titlebar, so the
window also calls `AppWindow.SetIcon(<app.ico>)` at startup. The `.ico` is
copied next to the exe for this; the call is guarded (a missing file is
non-fatal, and `ApplicationIcon` still covers the exe/taskbar).

## Consequences

- The unpackaged exe and its window show the Context Switcher brand everywhere
  Windows renders an app icon.
- Branding remains single-sourced in `generate-assets.ps1`; `app.ico` is a
  committed generated artifact (built without running the script).
- No behavior, persistence, or architecture change; MSIX and unpackaged builds
  are unaffected apart from the embedded icon.

## Non-goals (this slice)

Per-monitor icon variants, light/dark titlebar icons, and a hand-designed logo
— later polish.
