# Context Switcher — Release Checklist

Status: Draft foundation (v0.2.0)
Use one copy of this checklist per release candidate.

## Release gates

A release candidate is eligible only when **all** gates below are satisfied.

- [ ] **1. Acceptance tests pass.** `npm test` is all-PASS (7 checks).
- [ ] **2. Bundle-integrity self-test passes.** `npm run test:bundle:selftest`.
- [ ] **3. Consumer integration passes offline.** `npm run test:consumer` (fixture
      executor; live Claude not invoked).
- [ ] **4. No runtime/generated output packaged.** `npm run release:pack` shows no
      `runtime/`, `generated/`, `.claude/`, `bin/`, `obj/`, bytecode, or secrets.
- [ ] **5. Bundled ECF identity complete.** `source_commit` is a 40-hex commit and
      `source` carries no machine path (`release:validate` Gate 3).
- [ ] **6. Nested EKB identity matches.** ECF `VERSION.ekb_commit` == nested EKB
      `VERSION.source_commit` (`release:validate` Gate 4).
- [ ] **7. Version sources agree.** `package.json` version == manifest project
      version; manifest is not stale (`release:validate` Gates 1–2).
- [ ] **8. No vendor modifications outside the bundler.** `check_vendor_integrity.sh`
      (optionally `STRICT=1`) reports no project edits under `vendor/`.
- [ ] **9. No live Claude invocation.** Confirmed by the offline-only pipeline.
- [ ] **10. Package dry-run reviewed.** `npm run release:pack` content inspected and
      approved.

## Current acceptance level (record honestly)

```
single live task proven
full workflow not yet proven
```

The full 18-task WF-REASON-0001 workflow is **not yet** a release requirement. Do
not claim full-workflow proof until it has actually been executed end-to-end.

## Run record

| Field | Value |
|---|---|
| Candidate version | _e.g. 0.2.0-rc.1_ |
| Project commit | _`git rev-parse HEAD`_ |
| ECF pin | _version / commit_ |
| EKB pin | _version / commit_ |
| `npm test` | _PASS / FAIL_ |
| `npm run test:bundle:selftest` | _PASS / FAIL_ |
| `npm run release:validate` | _PASS / FAIL_ |
| `npm run release:pack` reviewed | _yes / no_ |
| Notes / open findings | _link PROJECT_ECF_ADOPTION_REPORT.md findings_ |

## Out of scope for this foundation

`npm publish`, `npm version`, git tags, GitHub releases, commits, and pushes are
performed by the project owner outside this checklist.

Related: `release/RELEASE_PROCESS.md`, `release/COMPATIBILITY.md`.
