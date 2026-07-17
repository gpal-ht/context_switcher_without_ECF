# Coordinated Platform Release 0.2.0

Operational AI engineering platform foundation: governed knowledge, controlled
execution, project adoption, and release engineering. Three coordinated,
**private** Git releases. Nothing is published to npm; no GitHub Releases exist.

```text
Knowledge Plane:
  engineering_kb   v0.2.0
Control Plane:
  ecf              v0.2.0   (pins EKB v0.2.0 exact commit)
Project Plane:
  context_switcher v0.2.0   (pins ECF v0.2.0 exact commit; nested EKB v0.2.0 exact commit)

Release status:
  private Git releases
  npm packages not published
  GitHub Releases not created
```

## Exact final commits and tags

| Component | Version | Tag | Commit | Pins |
|---|---|---|---|---|
| Engineering Knowledge Base (`@gpal-ht/engineering-kb`) | `0.2.0` | `v0.2.0` | `ce160741b767c4f108c6483fb94d13a2cc934e3a` | — |
| Engineering Control Framework (`@gpal-ht/ecf`) | `0.2.0` | `v0.2.0` | `eb15e18c34fe0fb4292e896962845dae51fe6da7` | EKB `ce160741b767c4f108c6483fb94d13a2cc934e3a` |
| Context Switcher (`@gpal-ht/context-switcher`) | `0.2.0` | `v0.2.0` | see note | ECF `eb15e18c34fe0fb4292e896962845dae51fe6da7` (nested EKB `ce160741b767c4f108c6483fb94d13a2cc934e3a`) |

**Context Switcher commit note (non-recursive attestation):** this document is
committed *inside* the Context Switcher release commit, so it cannot embed its own
containing commit without a self-reference loop. The Context Switcher `v0.2.0`
commit is the tip of `release/0.2.0` at tag time and is resolvable with
`git rev-list -n1 v0.2.0` in this repository. It is reported exactly in the
coordinated release result and verifiable against the remote tag.

## Dependency chain (verified)

```text
context_switcher v0.2.0
  pins ecf v0.2.0  @ eb15e18c34fe0fb4292e896962845dae51fe6da7
    which bundles engineering_kb v0.2.0 @ ce160741b767c4f108c6483fb94d13a2cc934e3a
context_switcher's nested EKB @ ce160741b767c4f108c6483fb94d13a2cc934e3a
  == ecf's bundled EKB @ ce160741b767c4f108c6483fb94d13a2cc934e3a   (identity match)
```

## Release-manifest identity model

All three repositories use a **non-recursive** manifest model (Critical
Release-Manifest Rule): the committed manifest never asserts its own containing
commit. Release-content identity is a content digest / exact upstream pins;
`git_commit` (or `project.commit`) is best-effort source provenance excluded from
equality/drift checks. The authoritative tag→commit binding is this attestation.

## What was NOT done

- `npm publish` — NOT PERFORMED.
- GitHub Releases — NOT CREATED.
- No force-push, no tag rewriting, no history rewriting after tags were pushed.
- No live Claude workflow execution during release validation.
