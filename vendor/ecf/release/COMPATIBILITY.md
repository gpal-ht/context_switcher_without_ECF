# ECF Compatibility Contract (0.2.0)

Declares, in ECF-owned terms, the identity a consumer (e.g. Context Switcher)
should pin, and the exact upstream Knowledge-Plane dependency ECF pins.

## What a consumer should pin

| Pin | Source | Value (0.2.0) |
|---|---|---|
| **ECF package version** | `package.json:version` (mirrored in `VERSION`, manifest) | `0.2.0` |
| **ECF released commit** | the `v0.2.0` tag commit (`git rev-list -n1 v0.2.0`) | recorded in the platform compatibility table |
| **Workflow** | `release-manifest.json:compatibility.workflow` | `WF-REASON-0001` @ `0.2.0` |
| **Nested EKB** | `release-manifest.json:bundled_ekb` | `0.2.0` @ `ce160741b767c4f108c6483fb94d13a2cc934e3a` (tag `v0.2.0`), ontology `decision_guide` |

The manifest's `git_commit` is the best-effort *source* commit; the authoritative
released commit is the tag commit.

## Upstream pin (Knowledge Plane)

ECF bundles EKB read-only under `vendor/engineering_kb/`, refreshed **only** via
`scripts/bundle-engineering-kb.ps1`. The `0.2.0` release pins:

- EKB package version `0.2.0`
- EKB source commit `ce160741b767c4f108c6483fb94d13a2cc934e3a` (tag `v0.2.0`)
- EKB ontology `decision_guide`

No EKB development artifacts (`.claude/`, caches, bytecode) are bundled.

## Framework vs package version

`ecf-version.yaml` records the ECF **framework** identity used by the planner for
provenance; it is intentionally independent of the release **package** version in
`package.json`. Do not bump one as a proxy for the other.

## Stability

While the major version is `0`, breaking changes may ship in minor releases; the
control-plane suites (`npm test`) and the workflow validator gate every release.
