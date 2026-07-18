# ADR-0023: .appinstaller for Auto-Update

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: .appinstaller
for auto-update", 2026-07-17)

**Related Work:** ADR-0020 (MSIX packaging), ADR-0022 (exe icon);
`docs/product/PRODUCT_PRINCIPLES.md` (Human in Control).

## Context

ADR-0020 produces a signed MSIX, but installing an updated version means
re-running the installer by hand. Windows **App Installer** supports an
`.appinstaller` file: a small XML manifest that points at a hosted MSIX and
declares update behavior, so installed apps check for and apply updates
automatically. This slice generates that file.

The honest constraint (like the dev-signing scope of ADR-0020): auto-update
**requires the `.appinstaller` and the `.msix` to be hosted at a stable
HTTP(S) URL**. There is no hosting in scope here, so the generated file carries
a **placeholder base URL** the operator replaces with their real location.

## Decision

### Generate the .appinstaller from the package identity

Extend `scripts/package-msix.ps1` to emit `ContextSwitcher.appinstaller`
alongside the signed MSIX, built from the **manifest identity** (Name,
Publisher, Version, architecture) and the MSIX filename so it never drifts from
the package. A `-AppInstallerBaseUrl` parameter (default a clearly-fake
placeholder) sets where the files will be hosted; both the `.appinstaller`
`Uri` and the `MainPackage` `Uri` are derived from it.

It is a build artifact (written into the gitignored `AppPackages/` output);
the **script is the source of truth**. `*.appinstaller` is gitignored.

### Update behavior — prompt, don't force (Human in Control)

`UpdateSettings` uses `OnLaunch` with `HoursBetweenUpdateChecks="0"` (check
each launch) and `ShowPrompt="true"`, plus an `AutomaticBackgroundTask` for
periodic background checks. Updates are **offered**, not forced;
`UpdateBlocksActivation` is left false so a failed check never stops the app
from launching. This matches the product's Human-in-Control principle.

The `.appinstaller` itself is not signed, but the MSIX it references must be
signed by a trusted certificate (the dev cert requires importing the `.cer`,
per ADR-0020) — a machine won't auto-install an untrusted package.

## Consequences

- Once the operator hosts the `.appinstaller`, `.msix`, and `.cer` at the
  configured URL and bumps the version, installed apps pick up updates with a
  prompt — no manual reinstall.
- Package identity and the auto-update file stay in sync (both derive from the
  manifest); one command produces both.

## Non-goals (this slice)

Actual hosting/CDN, a real (non-placeholder) URL, production code-signing, MSIX
bundles/multi-arch, and delta updates — deployment concerns out of scope. This
delivers the generated, correctly-formed `.appinstaller` and its update policy.
