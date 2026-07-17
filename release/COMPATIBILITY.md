# Context Switcher — Compatibility

Status: App-only foundation (ADR-0010; ECF removed)
Companion to the machine-readable `release/release-manifest.json`.

Context Switcher is a standalone .NET application with no external framework
dependency (ADR-0010 removed the former optional ECF integration). A release
records only the application's own identity — there is no bundled dependency
to pin or reconcile.

## What compatibility is recorded

Every release records, in the manifest:

- **Context Switcher** version (`package.json`) and project commit (best-effort).
- **Target** — platform (`Windows`) and stack (`.NET / WinUI 3`).
- **Application projects** — the `src/**/*.csproj` set a release is built from,
  each with a presence flag.
- **Architecture decision baseline** — the `decisions/ADR-*.md` set.

## What the manifest must detect

`scripts/validate-release.py` (`npm run release:validate`) fails the release when:

1. **The package is not private** or has no version (Gate 1).
2. **The on-disk manifest is missing, unparseable, or stale** versus live
   repository state, or its version disagrees with `package.json` (Gate 2).
3. **An application project is absent** from the expected `src/` set (Gate 3).
4. **Packaging boundaries leak** — the `package.json` `files` allowlist, or
   `.gitignore`, would include `runtime/` or `generated/` output (Gate 4).

## Versioning

Context Switcher owns a single SemVer line in `package.json`; see
`release/VERSIONING_POLICY.md`. There is no longer a separate dependency
version to track.

Related: `release/VERSIONING_POLICY.md`, `release/RELEASE_MANIFEST_SCHEMA.md`.
