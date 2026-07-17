# TASK_PROVENANCE_SCHEMA.md

# Purpose

This document defines the **Task Provenance Record**: the machine-readable
evidence a runner writes after a task executes successfully, and the read-only
planner reads to decide whether a completed output is still valid.

A provenance record answers: *for exactly which inputs, versions, and dependency
state was this output produced?* If any of those change, the output is stale.

The record is a runtime artifact. It is generated, non-canonical, and written
**only by the future execution runner** — never by the planner and never by the
validator.

---

# Location

```text
runtime/runs/<RUN_ID>/provenance/<TASK_ID>.yaml
```

One record per task, named by Task ID. Its presence in a run's `provenance/`
directory signals that the run uses provenance; see *Planner Enforcement*.

---

# Core Principle

Validity is determined by **content fingerprints and explicit versions**, not by
filesystem modification times. Every input and the output are pinned by SHA-256.
Task, workflow, ECF, and (when applicable) EKB versions are pinned explicitly.

---

# Structure

A record is a flat, YAML-compatible document with these fields:

```yaml
schema_version: 1

run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001

workflow_id: WF-REASON-0001
workflow_version: 0.1.0

task_id: TASK-ANALYZE-0002
task_version: 0.1.0

inputs:
  - name: engineering_reasoning_context
    path: task_outputs/engineering-reasoning-context.yaml
    sha256: 9f2c...e1
  # zero or more inputs; each with a logical name, a run-relative path, and a hash

output:
  path: task_outputs/engineering-forces.yaml
  sha256: 4b81...a0

ecf_version: v0.1
ecf_commit: 9e88a8b7eab0

# ekb_* present ONLY for tasks that consume the bundled Engineering Knowledge Base
ekb_version: v0.1-local
ekb_commit: 5334e693c56a7cf5de3b9e628a0bc57a384808b9

executor:
  type: ai
  provider: anthropic
  tool: claude-code

generated_at: 2026-07-10T10:05:00+05:30
```

## Required fields

* `schema_version`
* `run_id`, `work_request_id`
* `workflow_id`, `workflow_version`
* `task_id`, `task_version`
* `inputs` (possibly empty for entry tasks): each `{name, path, sha256}`
* `output`: `{path, sha256}`
* `ecf_version`, `ecf_commit`
* `executor`
* `generated_at`

## Conditional fields

* `ekb_version`, `ekb_commit` — present **only** for tasks that consume the
  bundled EKB (e.g. `TASK-RETRIEVE-0002`). When present, the planner compares
  them; when absent, the planner performs no EKB comparison for that task.

---

# Field semantics

| Field | Meaning |
|-------|---------|
| `sha256` | lowercase hex SHA-256 of the file's bytes, per `tools/artifact_fingerprint` |
| `path` | resolved relative to the run root `runtime/runs/<RUN_ID>/`, then the repo root |
| `*_version` | the pinned semantic version at production time |
| `*_commit` | the source commit at production time (ECF repo / EKB bundle) |
| `generated_at` | ISO-8601 timestamp; informational only, **never** a validity signal |

---

# Provenance Mode (explicit, never inferred)

Provenance policy is **explicit configuration**, never inferred from directory
existence. Every runtime run declares its mode in `state.yaml` (or `manifest.yaml`):

```yaml
provenance:
  mode: required        # required | legacy
  schema_version: "0.1.0"
```

* `required` — every completed task must have a valid provenance record.
* `legacy` — output existence may stand in for completion, but the planner emits
  a WARNING and marks output validity `unknown` (unverified).

Rules:

* New runs use `required`.
* **Missing provenance configuration is an invalid runtime configuration** — the
  planner fails (exit 2) and never silently enters legacy mode.
* An unrecognized mode value is an invalid runtime configuration.
* The presence or absence of a `provenance/` directory **never** determines policy.

---

# Authoritative Environment Dependencies

Whether a task requires **EKB** identity is decided by the **workflow/task
contract**, not by the provenance record being validated. The workflow declares:

```yaml
environment_dependencies:
  default:
    ecf: required
    ekb: not_required
  TASK-RETRIEVE-0002:
    ecf: required
    ekb: required
```

Consequently a record cannot omit its `ekb_*` fields to bypass an EKB check:
when the contract marks a task EKB-required and the record lacks EKB identity,
the output is stale (`ekb_provenance_missing`). Every task requires **ECF**
identity. For `WF-REASON-0001`, the only EKB-required task is `TASK-RETRIEVE-0002`
(it reads the bundled EKB directly and derives the Knowledge Package from it);
all downstream tasks receive EKB changes transitively through the fingerprint of
that package as an input.

---

# Canonical Version Identity

ECF version identity is read **only** from the machine-readable root file
`ecf-version.yaml` (never from README prose). EKB identity is read from
`vendor/engineering_kb/VERSION`.

Conservative v0.1 failure behavior:

* If the required current **ECF** identity cannot be resolved, that is a **planner
  configuration error** (not staleness).
* If a task is EKB-required and the current **EKB** identity cannot be resolved,
  that is a **planner configuration error**.
* Git **commit** resolution is **best-effort** (`commit_policy: best_effort` in
  `ecf-version.yaml`): when the current or recorded commit is unavailable the
  planner falls back to version-only comparison; when both are present and differ
  the output is stale. Version is always compared.

---

# Planner Enforcement

The planner is read-only and treats provenance conservatively (v0.1):

1. Provenance policy comes from the explicit run mode (above).
2. In `required` mode, for each task the planner considers completed (bound
   output exists or the manifest records a successful terminal status), it loads
   `provenance/<TASK_ID>.yaml` and re-verifies:
   - the provenance record exists and parses;
   - `task_id` and `task_version` match the workflow;
   - `workflow_id` and `workflow_version` match;
   - every declared input re-hashes to its recorded `sha256`;
   - the output re-hashes to its recorded `sha256`;
   - `ecf_version` (and best-effort `ecf_commit`) match the current environment;
   - `ekb_version`/`ekb_commit` match when the **contract** requires EKB.
3. A completed task keeps output validity `valid` only if **all** required checks
   pass. Otherwise its output validity is `stale`, `missing`, or `malformed`.
4. A completed task whose own output is valid but whose direct dependency needs
   rerun gets planned action `rerun` (cascade).
5. A not-yet-run task does not get planned action `run` while a required upstream
   task needs rerun.

Treated as **stale** in v0.1: missing provenance, malformed provenance, changed
input hash, changed output hash, changed task version, changed workflow version,
changed ECF version/commit, changed EKB version/commit (when the contract
requires EKB), and a stale direct dependency. Semantic compatibility ranges are
**not** implemented.

---

# Separated State Dimensions

The planner represents each task with three **independent** dimensions (never a
single competing state):

* `execution_state`: `not_started | running | completed | failed | cancelled | superseded`
* `output_validity`: `not_applicable | unknown | valid | stale | missing | malformed`
* `planned_action`: `none | run | rerun | wait | blocked | stop`

`STALE` and `RERUN REQUIRED` are **derived presentation labels**, not lifecycle
states. Example: a task that ran but whose input changed is
`execution_state: completed`, `output_validity: stale`, `planned_action: rerun`.

---

# Parser Limitations

The planner parses a **constrained subset** of YAML with the standard library
(no PyYAML):

* flat top-level `key: value` scalars;
* a single `inputs:` list of `{name, path, sha256}` items;
* a single `output:` block with `path` and `sha256`;
* a single `executor:` block of scalars.

It does **not** support: anchors/aliases, multi-document files, block scalars
(`|`, `>`), flow mappings, nested lists, or comments mid-value. A record that
does not fit this subset is treated as **malformed** (hence stale) — the safe,
conservative outcome. The future runner should emit records within this subset.

---

# Boundaries

* The planner never creates, repairs, updates, or deletes provenance.
* Provenance is written by the runner **after** successful task execution,
  atomically (see `execution/EXECUTION_TRACE_CONTRACT.md`).
* Modification times are never the primary validity check.

---

# Guiding Principle

An output is valid only for the exact inputs and versions it was produced from.
Provenance makes that statement checkable, and staleness makes re-execution
decisions explicit rather than assumed.
