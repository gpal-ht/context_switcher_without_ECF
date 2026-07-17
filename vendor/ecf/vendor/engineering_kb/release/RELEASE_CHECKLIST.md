# EKB Release Checklist

A release is ready when every box is checked. All checks are mechanical unless
marked *(manual)*.

## Identity & Version
- [ ] `package.json` version is valid semver.
- [ ] `package.json` version == `VERSION` == manifest `package_version`.
- [ ] Canonical version source is `package.json:version`.
- [ ] `package.json` is `"private": true` with no `publishConfig`.

## Content
- [ ] `npm run pack:check` lists only canonical content.
- [ ] No forbidden files in the pack (`.git`, `.claude`, `__pycache__`, `*.pyc`,
      `generated/`, `*.tmp`, `*.temp`, `*.log`, `*.tgz`).
- [ ] Required canonical directories present (`engine/`, `knowledge_model/`,
      `standards/`, `decision_guides/`, `concepts/`, `migrations/`, `release/`).

## Manifest
- [ ] `release/release-manifest.json` regenerated for the current commit.
- [ ] Manifest complete (all required keys).
- [ ] `git_commit` equals current `HEAD`.
- [ ] `publish_status` is `not_published`; `git_tag` is `null`.
- [ ] `content_digest` present.

## Quality Gates
- [ ] `npm test` passes.
- [ ] `npm run validate` passes.
- [ ] `npm run integrity` passes.
- [ ] `npm run completeness` passes.
- [ ] Coverage and centrality reports are byte-deterministic across two runs.

## Pre-Publish Blockers *(manual — must be resolved before any publish)*
- [ ] A `LICENSE` file exists and a license has been chosen.
- [ ] A decision to drop `"private": true` has been explicitly authorized.
- [ ] Downstream ECF bundle-refresh requirements (see `COMPATIBILITY.md`) handled.

## One-shot
```
npm run release:manifest && npm run release:validate && npm run pack:check
```
