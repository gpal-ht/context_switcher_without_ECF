# ECF Release Process (0.2.0 foundation)

How to cut an ECF Control-Plane release artifact **offline**, with full identity
and dependency-pin validation, without publishing.

## Principles

- **Offline.** No release step invokes live Claude. Validation runs the
  control-plane suites and mechanical gates only.
- **Read-only over vendor.** `vendor/engineering_kb/` is refreshed ONLY by
  `scripts/bundle-engineering-kb.ps1`. The release process never hand-edits the
  bundle.
- **Metadata over prose.** Identity is read from `package.json` / `VERSION` /
  `ecf-version.yaml` / the bundle `VERSION` stamp, never from narrative docs.
- **No implicit publication.** `npm publish`, GitHub Releases, tags, and pushes
  are owner-controlled; this foundation performs none implicitly.

## Gates (all must pass before tagging)

1. `npm test` — 226 control-plane tests (per-tool isolation).
2. Workflow validation — `WF-REASON-0001` passes all 21 rules.
3. `npm run release:manifest` — regenerate `release/release-manifest.json`.
4. `npm run release:validate` — identity, EKB pin, packaging, non-recursive
   manifest model.
5. `npm pack --dry-run --json` — package content review (no bytecode, `.claude/`,
   runtime, or generated output).

## Order

1. Ensure upstream EKB `v0.2.0` is tagged and pushed.
2. Refresh the EKB bundle to the EKB tag commit.
3. Run all gates.
4. Commit logical batches; create the annotated `v0.2.0` tag on the release
   commit; push branch then tag; verify the remote.

The tag → commit binding is recorded in the platform compatibility table.
