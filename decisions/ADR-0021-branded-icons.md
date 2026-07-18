# ADR-0021: Branded Application Icons

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: real branded
icons", 2026-07-17)

**Related Work:** ADR-0020 (MSIX packaging — the placeholder assets this
replaces).

## Context

ADR-0020 shipped placeholder assets (flat blue squares with "CS" text) so the
MSIX would build. This slice replaces them with a deliberate, consistent
**brand mark** and the full icon set a real WinUI app ships (base logos, scale
variants, and target-size taskbar icons).

There is no designer or design tool in scope, and the environment has no SVG
rasterizer. So the icons are **code-generated** with GDI+ (`System.Drawing`)
from a defined mark, at every required size.

## Decision

### The mark

Context Switcher is about moving between work contexts, so the mark is **two
overlapping rounded "context" panels** (layered cards) in white on a diagonal
brand gradient (indigo `#2B2D7A` → teal `#1CA0B8`), with a thin indigo keyline
separating the front panel from the back. It is simple, reads as
"multiple contexts," and stays legible down to 16 px.

### Reproducible generation

`scripts/generate-assets.ps1` renders the entire asset set into
`src/App/ContextSwitcher.App/Assets/`. The **script is the source of truth**;
the PNGs are committed generated artifacts (so the app packages without running
the script, and the brand can be regenerated deterministically). The set:

- `Square44x44Logo` (+ `scale-200`, + `targetsize-16/24/32/48/256` for crisp
  taskbar/Start icons),
- `Square71x71Logo`, `Square150x150Logo`, `Square310x310Logo` (+ `scale-200`
  where impactful),
- `Wide310x150Logo` (+ `scale-200`),
- `StoreLogo` (+ `scale-200`),
- `SplashScreen` (mark + wordmark on the brand gradient, + `scale-200`).

All icons are **plated** (they carry the gradient background), so they always
contrast on light or dark shells without needing separate unplated/mono
variants. The manifest's optional lock-screen badge (which requires a
white/transparent asset) is dropped rather than shipped half-done.

## Consequences

- The app presents a coherent brand across tiles, taskbar, Start, splash, and
  the Store logo, at all scales.
- Re-branding is a one-file change (`generate-assets.ps1`) plus a regenerate.
- No architecture, persistence, or behavior change; the MSIX build and the
  unpackaged dev-run are unaffected apart from the new images.

## Non-goals (this slice)

A professionally designed logo, an `.ico` for the unpackaged exe window, dark/
light unplated taskbar variants, and animated/adaptive icons — later polish.
This delivers a real, consistent, code-generated brand replacing the
placeholders.
