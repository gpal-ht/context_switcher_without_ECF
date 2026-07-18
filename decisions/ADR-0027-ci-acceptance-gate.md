# ADR-0027: CI Acceptance Gate

**Status:** Accepted

**Date:** 2026-07-18

**Approved by:** Project Owner (directive: "build all four slices at once",
2026-07-18)

**Related Work:** ADR-0008 (offline pure-BCL Work Engine + reflection test
runner), ADR-0010 (standalone .NET app; ECF removed), ADR-0020 (MSIX
packaging, Windows-only); `acceptance_tests/run_all.sh`.

## Context

The repository ships an offline acceptance suite (`acceptance_tests/run_all.sh`)
that runs four checks — engineering context, architecture consistency, ignore
boundaries, and product build + tests. The product-tests check builds the
pure-BCL Work library and CLI harness with `dotnet` and runs the in-repo
`[Test]` reflection runner (ADR-0008: no NuGet restore, no network). Until now
this gate ran only when a contributor remembered to run it locally, so nothing
mechanically protected `develop` from a regression landing on the trunk.

The suite is cross-platform: it is bash plus `dotnet` over the `net10.0` Work
Engine, CLI, and test projects, with no Windows-only assumptions (the checks
use `git`, `grep`, and `wc`). The WinUI GUI (`ContextSwitcher.App`,
`net10.0-windows`) and MSIX packaging (ADR-0020) require Windows + Visual
Studio MSBuild and are **not** part of this suite.

## Decision

### Add a GitHub Actions workflow that runs the acceptance suite

Add `.github/workflows/acceptance.yml`. It triggers on `push` (to `develop` and
to `feature/**`, `chore/**`, `ci/**` branches) and on `pull_request` targeting
`develop`, so both feature-branch work and every PR into the trunk are gated.

The job runs on `ubuntu-latest` because the suite is pure bash + .NET with no
Windows dependency; Linux is faster and cheaper than a Windows runner and is
sufficient for the cross-platform Work Engine, CLI, and offline test runner.
Steps are minimal: `actions/checkout@v4`, `actions/setup-dotnet@v4` pinned to
the .NET **10** SDK (`10.0.x`, matching `src/Directory.Build.props`
`TargetFramework net10.0`; there is no `global.json` to match), then a single
`bash acceptance_tests/run_all.sh`. The suite is invoked directly rather than
through `npm test` — the npm script is only a thin wrapper around the same bash
entry point, so no Node setup is needed. `run_all.sh` exits non-zero on any
failing check, which fails the job.

## Consequences

- Every push and every PR into `develop` mechanically runs the four-check
  acceptance suite; a regression in the Work Engine, CLI, architecture docs, or
  ignore boundaries turns the trunk gate red instead of merging silently.
- CI stays fast and dependency-free: no NuGet restore, no secrets, no Node, no
  network beyond the SDK setup, consistent with the offline pure-BCL policy.
- The .NET SDK version lives in the workflow (pinned `10.0.x`) alongside
  `src/Directory.Build.props`; a future framework bump touches both.

## Non-goals (this slice)

The WinUI GUI build and MSIX/`.appinstaller` packaging (ADR-0020, ADR-0023) —
they need Windows, Visual Studio MSBuild, and signing material and are out of
scope for this gate. Also out of scope: deployment/publishing, release
validation, code-signing, branch-protection rule configuration on GitHub, and
any secrets. This slice delivers the CI job that runs the existing offline
acceptance suite and nothing more.
