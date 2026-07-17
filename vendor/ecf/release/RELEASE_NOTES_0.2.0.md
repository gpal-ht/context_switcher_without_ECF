# Engineering Control Framework — Release Notes 0.2.0

Package: `@gpal-ht/ecf`
Version: `0.2.0`
Tag: `v0.2.0`
Private: `true` — not published to any registry.
Publish status: `not_published`.

## Theme

Operational AI engineering platform foundation — the **Control Plane**: a
declarative, validated model for executing engineering-reasoning workflows over
an exactly-pinned Knowledge Plane (bundled EKB `v0.2.0`).

## Highlights

- **Controlled workflow execution.** `WF-REASON-0001` (version `0.2.0`) is a
  declarative 18-task DAG that passes all **21** workflow-validator rules
  (`WF001`–`WF021`); execution stops at the human-approval boundary.
- **Planner and stale detection.** The workflow planner resolves the ready set
  from runtime state and separates provenance dimensions (own output, EKB
  authority, ECF version) so changed upstream marks dependents stale.
- **Atomic runtime transactions.** Crash-consistent runtime state with staging,
  promotion, and hash/revision verification.
- **Recovery and provenance.** Crash scenarios are detected and classified;
  provenance is recorded and compared, never inferred from directory presence.
- **Run initialization.** A canonical run initializer with Windows-safe
  promotion hardening (non-transient errors are not retried; no partial final
  run on exhaustion).
- **Claude-backed `TASK-CLASSIFY-0001` executor.** A real Claude-backed task
  adapter; the framework achieved its **first successful real Claude-backed task
  execution** with it.
- **Executor-independent output validation.** Task output contracts are enforced
  before commit, independent of which executor produced the output.
- **Manifest ownership correction.** Runtime-owned `state.yaml` / mutable
  `manifest.yaml` are separated from the immutable `reports/final-manifest.yaml`;
  `TASK-TRACE-0002` binds the final manifest, `TASK-TRACE-0003` consumes it.
  `TASK-TRACE-0002` and `TASK-TRACE-0003` are versioned `0.2.0`.

## Bundled dependency (exact pin)

- **Engineering Knowledge Base** `@gpal-ht/engineering-kb` `0.2.0`
  - source commit `ce160741b767c4f108c6483fb94d13a2cc934e3a` (tag `v0.2.0`)
  - ontology: `decision_guide`
  - refreshed only via `scripts/bundle-engineering-kb.ps1`; no EKB development
    artifacts (`.claude/`, caches, bytecode) are bundled.

## Verification (all gates pass for this release)

- `npm test` → 6 canonical control-plane suites, per-tool isolation:
  **226 passed** (workflow_validator 29, workflow_planner 37, run_initializer 42,
  runtime_state 31, task_runner 77, artifact_fingerprint 10).
- Workflow validation → `WF-REASON-0001`: **21/21 rules pass**.
- `npm run release:manifest` / `release:validate` → all gates pass.
- `npm pack --dry-run` → package contains every consumer entrypoint and no
  bytecode, `.claude/`, runtime run, or generated output.

## Release-manifest identity model (non-recursive)

Per the Critical Release-Manifest Rule the committed manifest does not assert its
own containing commit. Release-content identity is `content_digest` (sha256 over
canonical content, manifest excluded); `git_commit` is the best-effort source
commit (a committed ancestor of HEAD). The tag→commit binding is recorded in the
platform compatibility table and resolvable via `git rev-list -n1 v0.2.0`.

## Known limitations

- The complete 18-task `WF-REASON-0001` workflow has **not yet been executed end
  to end**.
- Only `TASK-CLASSIFY-0001` currently has a **live Claude task adapter**; the
  other tasks are declarative specifications without live adapters.
- No live Claude invocation occurs during release validation (offline gates
  only). No npm publication and no GitHub Release are created by this batch.
