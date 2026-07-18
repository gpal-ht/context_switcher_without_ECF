# ADR-0020: MSIX Packaging

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: MSIX
packaging", 2026-07-17)

**Related Work:** ADR-0001 (WinUI 3), ADR-0011 (WinUI 3 GUI shell / VS-MSBuild
build path).

## Context

The WinUI 3 app has run **unpackaged** (`WindowsPackageType=None`, launched as a
plain exe via `scripts/build-gui.ps1`). To be installable like a real Windows
application it needs an **MSIX** package. This slice adds MSIX packaging while
keeping the fast unpackaged dev-run intact.

Feasibility was confirmed in this environment: `makeappx.exe`/`signtool.exe`
ship with `Microsoft.Windows.SDK.BuildTools` (pulled transitively by
`Microsoft.WindowsAppSDK`), the Visual Studio AppxPackage MSBuild targets are
present, and `New-SelfSignedCertificate` is available.

## Decision

### Single-project MSIX, dual-mode build

Keep one app project that builds **either** way:

- **Unpackaged (default)** — `WindowsPackageType=None`; `scripts/build-gui.ps1`
  produces a directly runnable exe (unchanged).
- **Packaged** — `scripts/package-msix.ps1` passes `BuildMsix=true`, which
  leaves `WindowsPackageType` unset so the project builds a packaged MSIX.

`WindowsPackageType` is therefore conditional on `BuildMsix`; `EnableMsixTooling`
is on. A `Package.appxmanifest` and placeholder `Assets/` (generated logos) live
in the app project.

### Build unsigned, then sign with signtool

MSBuild's in-build signing (`AppxPackageSigningEnabled` +
`PackageCertificateKeyFile`) fails to import a password-protected `.pfx`
(APPX0105). So the script builds the package **unsigned**, then signs the
`.msix` with **`signtool`** (from the SDK build tools), which handles the
password reliably.

### Self-signed development certificate; nothing secret committed

Signing uses a **self-signed development certificate** (`CN=ContextSwitcher
Dev`, matching the manifest `Publisher`) generated on demand into the
**gitignored** `.local/certs/` directory. The private key (`.pfx`), the public
`.cer`, all `AppPackages/` output, and any `*.msix`/`*.pfx`/`*.cer` are
**never committed** (`.gitignore`). The `.pfx` password is a throwaway dev
constant, not a secret.

The resulting MSIX is a **sideload / development** package: installable after
importing the dev `.cer` into Trusted People (the script prints the commands,
or `-Install` does it). This is honest about its scope.

## Consequences

- The app can be built into an installable MSIX with one command
  (`scripts/package-msix.ps1`), and installed for real testing.
- The unpackaged dev-run and the offline pure-BCL acceptance gate are
  unaffected (the packaged build is a separate, opt-in path; the acceptance
  suite does not build the GUI).
- Producing MSIX requires Visual Studio + the SDK build tools (already required
  for the GUI) and network to restore packages — same prerequisites as ADR-0011.

## Non-goals (this slice)

Store submission / Partner Center identity and **production code-signing** (a
real certificate) — a self-signed dev cert is not trusted by other machines
without importing it; a Store or EV/OV identity is required for distribution and
is out of scope. Also out: MSIX bundles, auto-update (App Installer / `.appinstaller`),
CI packaging, and real branded app icons (current assets are placeholders).
