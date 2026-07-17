# EKB Release Process

npm is used here as a **packaging and release-control interface only**. The EKB
ships Markdown knowledge and a dependency-free Python engine; there is **no
JavaScript runtime dependency** and no `node_modules`.

## Toolchain

- **Python 3.9+** — runs the engine, tests, and release scripts. (Not expressible
  as an npm `engines` field; validated by running the suite.)
- **npm** — the release interface (`npm test`, `npm run release:*`, `npm pack`).
- **git** — the manifest records the current commit.

## Commands

| Command | Purpose |
|---|---|
| `npm test` | Canonical EKB test suite (`python engine/test_engine.py`). |
| `npm run validate` | Standard + relationship-policy validation. |
| `npm run integrity` | Full graph integrity. |
| `npm run completeness` | Decision Guide completeness. |
| `npm run release:manifest` | (Re)generate `release/release-manifest.json`. |
| `npm run release:validate` | Run all 12 mechanical release checks. |
| `npm run pack:check` | `npm pack --dry-run --json` — inspect exact contents. |

## Standard Release Flow (no publish)

1. Ensure the working tree is committed (the manifest records `HEAD`).
2. `npm run release:manifest` — regenerate the manifest for the current commit.
3. `npm run release:validate` — must pass all 12 checks.
4. `npm run pack:check` — confirm the file list contains only canonical content.
5. Review `release/release-manifest.json` (`publish_status: not_published`).

## Publishing (NOT part of this batch — blocked)

Publishing is intentionally impossible today:

- `package.json` has `"private": true`.
- **No `LICENSE` exists** — a license MUST be chosen before any publish.
- No `npm login`, `npm publish`, Git tag, or GitHub release is performed by any
  script here.

Before a future publish, a separate, explicitly-authorized batch must: add a
`LICENSE`, decide whether to drop `private`, set the version, create the Git tag,
and run `npm publish` — none of which happens here.

## Version Bump (manual, not automated here)

`npm version` is **not** run by this foundation. To bump: edit `package.json`
`version`, mirror it in `VERSION`, regenerate the manifest, and validate. The
validator fails on any drift.
