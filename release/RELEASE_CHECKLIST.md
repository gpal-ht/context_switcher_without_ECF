# Context Switcher — Release Checklist

Status: App-only foundation (ADR-0010; ECF removed)
Use one copy of this checklist per release candidate.

## Release gates

A release candidate is eligible only when **all** gates below are satisfied.

- [ ] **1. Acceptance tests pass.** `npm test` is all-PASS.
- [ ] **2. Product build + tests pass.** `npm run app:test` (Work Engine +
      CLI build; deterministic product suite).
- [ ] **3. No runtime/generated output packaged.** `npm run release:pack` shows no
      `runtime/`, `generated/`, `.claude/`, `bin/`, `obj/`, bytecode, or secrets.
- [ ] **4. Application projects present.** `release:validate` Gate 3.
- [ ] **5. Version sources agree.** `package.json` version == manifest project
      version; manifest is not stale (`release:validate` Gates 1–2).
- [ ] **6. Packaging boundaries clean.** `files` allowlist and `.gitignore`
      exclude `runtime/`/`generated/` (`release:validate` Gate 4).
- [ ] **7. Package dry-run reviewed.** `npm run release:pack` content inspected and
      approved.

## Run record

| Field | Value |
|---|---|
| Candidate version | _e.g. 0.3.0-rc.1_ |
| Project commit | _`git rev-parse HEAD`_ |
| `npm run app:test` | _PASS / FAIL_ |
| `npm test` | _PASS / FAIL_ |
| `npm run release:validate` | _PASS / FAIL_ |
| `npm run release:pack` reviewed | _yes / no_ |
| Notes / open findings | _link_ |

## Out of scope for this foundation

`npm publish`, `npm version`, git tags, GitHub releases, commits, and pushes are
performed by the project owner outside this checklist.

Related: `release/RELEASE_PROCESS.md`, `release/COMPATIBILITY.md`.
