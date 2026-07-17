---
workflow_id: WF-REASON-0001
name: Engineering Recommendation
version: 0.2.0
status: draft
category: reasoning
owner: engineering_control_framework
entry_state: accepted
successful_exit_state: waiting_for_human_approval
---

# Engineering Recommendation Workflow

This Workflow conforms to `workflows/WORKFLOW_EXECUTION_SPECIFICATION.md`.

It composes existing task specifications. It does not redefine task behavior, and it does not perform engineering reasoning itself.

## Status

```text
Workflow specification status: Complete
Automated execution status:    Not implemented
```

WF-REASON-0001 is structurally complete as a declarative workflow specification: all eighteen tasks resolve, versions are pinned, each task binds to one unique output path, the dependency graph is an explicit acyclic DAG, and the run stops at the human-approval boundary.

It is **not** automatically executable because no workflow runner currently invokes the task graph. These two concerns — specification completeness and runtime-implementation completeness — are tracked separately. The absence of a runner does not downgrade the specification.

---

# Purpose

Transform an accepted engineering Work Request into a validated Engineering Recommendation Report and a complete, auditable reasoning-run record.

The Workflow orders eighteen existing tasks, binds each to a stable runtime output, enforces validation between steps, and stops at the human-approval gate.

Successful completion means the run reaches:

```text
waiting_for_human_approval
```

It never means `approved`, and it never invokes the Engineering Production Engine.

---

# Core Principle

This Workflow coordinates; the tasks reason.

Every conclusion in the run is produced by a task and recorded as a runtime output. The Workflow only decides which task runs next, verifies each output, and carries findings forward.

---

# Entry Conditions

Execution may begin only when:

* an accepted Work Request exists with exactly one primary engineering question
* the Work Request satisfies `work_requests/WORK_REQUEST_SPECIFICATION.md`
* the Orchestration Engine has assigned a Run ID of the form `RUN-REASON-<YYYYMMDD>-<SEQUENCE>`
* bundled ECF and bundled EKB are available (read-only)
* every pinned task version resolves to an existing task specification

The entry state is `accepted`.

---

# Required Inputs

| Input | Type | Source | Required | First consumed by |
|---|---|---|---|---|
| Work Request | work_request | consuming project | yes | TASK-CLASSIFY-0001 |
| Engineering Context Reference | project context | Work Request | yes | TASK-RETRIEVE-0001 |
| Bundled EKB | knowledge base | `vendor/engineering_kb/` | yes | TASK-RETRIEVE-0002 |
| Run ID | identifier | Orchestration Engine | yes | all steps |

A snapshot of the accepted Work Request is stored under `runtime/runs/<RUN_ID>/inputs/`.

---

# Runtime Layout

All outputs use the canonical run root:

```text
runtime/runs/<RUN_ID>/
├── state.yaml          # runtime infrastructure (runtime-owned; not a task output)
├── manifest.yaml       # runtime infrastructure (runtime-owned; not a task output)
├── trace.md            # TASK-TRACE-0001 output
├── completion.yaml     # TASK-TRACE-0003 output
├── inputs/
├── task_outputs/
└── reports/
    └── final-manifest.yaml   # TASK-TRACE-0002 output (immutable snapshot)
```

`state.yaml` and the run-root `manifest.yaml` are runtime-owned infrastructure,
continuously updated by the runtime transaction layer; they are never task
outputs. The task-owned immutable manifest snapshot is `reports/final-manifest.yaml`.

No other runtime root is used by this Workflow.

---

# Task-Version Pinning

Sixteen tasks are pinned to version `0.1.0`; `TASK-TRACE-0002` and `TASK-TRACE-0003` are pinned to `0.2.0` (their output/input contracts changed in the manifest-ownership fix). Each pin matches the current repository state for that task. If any task specification reports a different version at run time, version resolution fails and the Workflow must not execute.

## Migration — manifest ownership (v0.1.0 → v0.2.0)

| | Old (v0.1.0) | New (v0.2.0) |
|---|---|---|
| `TASK-TRACE-0002` output | `manifest.yaml` | `reports/final-manifest.yaml` |
| run-root `manifest.yaml` | task-owned + runtime-owned (conflated) | runtime infrastructure only |
| `TASK-TRACE-0003` manifest input | `manifest.yaml` | `reports/final-manifest.yaml` |

The workflow version is bumped to `0.2.0` and the two changed task versions to `0.2.0`. Historical runs produced under `v0.1.0` remain valid as historical data and are **not** rewritten; new runs use `v0.2.0`. A run planned under one workflow version is evaluated against that version's provenance, so mixing versions within a single run is prevented by version resolution.

---

# Stable Output Bindings

The Workflow is authoritative for these run filenames. Task specifications retain responsibility for output structure and semantics.

| Task ID | Version | Bound primary output |
|---|---|---|
| TASK-CLASSIFY-0001 | 0.1.0 | `task_outputs/engineering-intent.yaml` |
| TASK-CLASSIFY-0002 | 0.1.0 | `task_outputs/engineering-phase.yaml` |
| TASK-RETRIEVE-0001 | 0.1.0 | `task_outputs/engineering-context.yaml` |
| TASK-RETRIEVE-0002 | 0.1.0 | `task_outputs/engineering-knowledge-package.md` |
| TASK-ANALYZE-0001 | 0.1.0 | `task_outputs/engineering-reasoning-context.yaml` |
| TASK-ANALYZE-0002 | 0.1.0 | `task_outputs/engineering-forces.yaml` |
| TASK-ANALYZE-0003 | 0.1.0 | `task_outputs/decision-options.yaml` |
| TASK-ANALYZE-0004 | 0.1.0 | `task_outputs/engineering-alternatives.yaml` |
| TASK-ANALYZE-0005 | 0.1.0 | `task_outputs/engineering-trade-offs.yaml` |
| TASK-ANALYZE-0006 | 0.1.0 | `task_outputs/engineering-risks.yaml` |
| TASK-ANALYZE-0007 | 0.1.0 | `task_outputs/missing-information.yaml` |
| TASK-DECIDE-0001 | 0.1.0 | `task_outputs/engineering-confidence.yaml` |
| TASK-DECIDE-0002 | 0.1.0 | `task_outputs/engineering-recommendation.yaml` |
| TASK-PRODUCE-0001 | 0.1.0 | `reports/engineering-recommendation-report.md` |
| TASK-VALIDATE-0001 | 0.1.0 | `task_outputs/recommendation-report-validation.yaml` |
| TASK-TRACE-0001 | 0.1.0 | `trace.md` |
| TASK-TRACE-0002 | 0.2.0 | `reports/final-manifest.yaml` |
| TASK-TRACE-0003 | 0.2.0 | `completion.yaml` |

No two tasks bind to the same output path. The runtime-owned `state.yaml` and
run-root `manifest.yaml` are infrastructure and are deliberately **not** task
bindings.

---

# Workflow States

```text
requested
accepted
classifying
retrieving
preparing_reasoning_context
analyzing
deciding
producing_report
validating_report
finalizing_trace
waiting_for_human_approval
blocked
failed
cancelled
superseded
```

## Valid Transitions

```text
requested                    → accepted
accepted                     → classifying
classifying                  → retrieving
retrieving                   → preparing_reasoning_context
preparing_reasoning_context  → analyzing
analyzing                    → deciding
deciding                     → producing_report
producing_report             → validating_report
validating_report            → finalizing_trace
finalizing_trace             → waiting_for_human_approval

any active state             → blocked      (recoverable stop: missing/invalid output, blocking finding)
any active state             → failed       (unrecoverable stop: task failure, version-resolution failure)
any active state             → cancelled    (Orchestration Engine cancels)
any active state             → superseded   (a newer run replaces this run)

blocked                      → (resumed active state) on recovery
```

`waiting_for_human_approval`, `failed`, `cancelled`, and `superseded` are terminal for the reasoning Workflow. `blocked` is a held state that may resume after recovery.

---

# Task Graph

Each step lists its sequence number, task, version, upstream dependencies, required inputs, bound output, states, and the gate that must pass before the next step runs. Findings continuation is allowed only where the task contract permits completion with findings.

## Step 1 — Determine Engineering Intent

* Task: TASK-CLASSIFY-0001 @ 0.1.0
* Upstream: none (entry)
* Required inputs: Work Request
* Output: `task_outputs/engineering-intent.yaml`
* State before: `accepted` → sets `classifying`
* State after success: `classifying`
* Failure state: `failed`
* Findings may continue: no blocking findings permitted
* Validation before continue: intent output exists and is valid

## Step 2 — Determine Engineering Phase

* Task: TASK-CLASSIFY-0002 @ 0.1.0
* Upstream: TASK-CLASSIFY-0001
* Required inputs: Work Request; `engineering-intent.yaml` (optional prioritization)
* Output: `task_outputs/engineering-phase.yaml`
* State before: `classifying`
* State after success: `retrieving`
* Failure state: `failed`
* Findings may continue: no blocking findings permitted
* Validation before continue: phase output exists and is valid

## Step 3 — Retrieve Engineering Context

* Task: TASK-RETRIEVE-0001 @ 0.1.0
* Upstream: TASK-CLASSIFY-0001, TASK-CLASSIFY-0002
* Required inputs: Work Request; Engineering Context Reference; optionally intent and phase
* Output: `task_outputs/engineering-context.yaml`
* State before: `retrieving`
* State after success: `retrieving`
* Failure state: `failed`
* Findings may continue: blocking context contradictions stop the run; non-blocking context findings carry forward
* Validation before continue: context output exists and is valid; no blocking finding

## Step 4 — Generate Engineering Knowledge Package

* Task: TASK-RETRIEVE-0002 @ 0.1.0
* Upstream: TASK-CLASSIFY-0001, TASK-CLASSIFY-0002, TASK-RETRIEVE-0001
* Required inputs: engineering question, intent, phase, `engineering-context.yaml`; bundled EKB
* Output: `task_outputs/engineering-knowledge-package.md`
* State before: `retrieving`
* State after success: `preparing_reasoning_context`
* Failure state: `failed`
* Findings may continue: no blocking findings permitted
* Validation before continue: package exists and validates against its contract; primary Decision Guide present

## Step 5 — Build Engineering Reasoning Context

* Task: TASK-ANALYZE-0001 @ 0.1.0
* Upstream: TASK-CLASSIFY-0001, TASK-CLASSIFY-0002, TASK-RETRIEVE-0001, TASK-RETRIEVE-0002
* Required inputs: `engineering-intent.yaml`, `engineering-phase.yaml`, `engineering-context.yaml`, `engineering-knowledge-package.md`
* Output: `task_outputs/engineering-reasoning-context.yaml`
* State before: `preparing_reasoning_context`
* State after success: `analyzing`
* Failure state: `failed`
* Findings may continue: no blocking findings permitted
* Validation before continue: reasoning context exists and is valid

## Step 6 — Identify Engineering Forces

* Task: TASK-ANALYZE-0002 @ 0.1.0
* Upstream: TASK-ANALYZE-0001
* Required inputs: `engineering-reasoning-context.yaml`
* Output: `task_outputs/engineering-forces.yaml`
* State before: `analyzing`
* State after success: `analyzing`
* Failure state: `failed`
* Findings may continue: non-blocking findings carry forward
* Validation before continue: forces output exists and is valid

## Step 7 — Identify Decision Options

* Task: TASK-ANALYZE-0003 @ 0.1.0
* Upstream: TASK-ANALYZE-0001, TASK-ANALYZE-0002
* Required inputs: `engineering-reasoning-context.yaml`, `engineering-forces.yaml`
* Output: `task_outputs/decision-options.yaml`
* State before: `analyzing`
* State after success: `analyzing`
* Failure state: `failed`
* Findings may continue: non-blocking findings carry forward
* Validation before continue: at least two viable options; output valid

## Step 8 — Generate Engineering Alternatives

* Task: TASK-ANALYZE-0004 @ 0.1.0
* Upstream: TASK-ANALYZE-0001, TASK-ANALYZE-0002, TASK-ANALYZE-0003
* Required inputs: `engineering-reasoning-context.yaml`, `engineering-forces.yaml`, `decision-options.yaml`
* Output: `task_outputs/engineering-alternatives.yaml`
* State before: `analyzing`
* State after success: `analyzing`
* Failure state: `failed`
* Findings may continue: non-blocking findings carry forward
* Validation before continue: at least one viable/experimental alternative; output valid

## Step 9 — Analyze Engineering Trade-offs

* Task: TASK-ANALYZE-0005 @ 0.1.0
* Upstream: TASK-ANALYZE-0001, TASK-ANALYZE-0002, TASK-ANALYZE-0003, TASK-ANALYZE-0004
* Required inputs: `engineering-reasoning-context.yaml`, `engineering-forces.yaml`, `decision-options.yaml`, `engineering-alternatives.yaml`
* Output: `task_outputs/engineering-trade-offs.yaml`
* State before: `analyzing`
* State after success: `analyzing`
* Failure state: `failed`
* Findings may continue: non-blocking findings carry forward
* Validation before continue: trade-off output exists and is valid

## Step 10 — Identify Engineering Risks

* Task: TASK-ANALYZE-0006 @ 0.1.0
* Upstream: TASK-ANALYZE-0001, TASK-ANALYZE-0004, TASK-ANALYZE-0005
* Required inputs: `engineering-reasoning-context.yaml`, `engineering-alternatives.yaml`, `engineering-trade-offs.yaml`
* Output: `task_outputs/engineering-risks.yaml`
* State before: `analyzing`
* State after success: `analyzing`
* Failure state: `failed`
* Findings may continue: non-blocking findings carry forward
* Validation before continue: risk output exists and is valid

## Step 11 — Identify Missing Information

* Task: TASK-ANALYZE-0007 @ 0.1.0
* Upstream: TASK-ANALYZE-0001, TASK-ANALYZE-0002, TASK-ANALYZE-0003, TASK-ANALYZE-0004, TASK-ANALYZE-0005, TASK-ANALYZE-0006
* Required inputs: all prior reasoning outputs
* Output: `task_outputs/missing-information.yaml`
* State before: `analyzing`
* State after success: `deciding`
* Failure state: `failed`
* Findings may continue: an open blocker is recorded and carried forward; it constrains the recommendation but does not by itself stop the run
* Validation before continue: missing-information output exists and is valid; blocking summary present

## Step 12 — Assess Engineering Confidence

* Task: TASK-DECIDE-0001 @ 0.1.0
* Upstream: TASK-ANALYZE-0001, TASK-ANALYZE-0002, TASK-ANALYZE-0003, TASK-ANALYZE-0004, TASK-ANALYZE-0005, TASK-ANALYZE-0006, TASK-ANALYZE-0007
* Required inputs: reasoning context, forces, options, alternatives, trade-offs, risks, missing-information
* Output: `task_outputs/engineering-confidence.yaml`
* State before: `deciding`
* State after success: `deciding`
* Failure state: `failed`
* Findings may continue: non-blocking findings carry forward
* Validation before continue: five dimensions plus Overall narrative present; not averaged

## Step 13 — Generate Engineering Recommendation

* Task: TASK-DECIDE-0002 @ 0.1.0
* Upstream: TASK-ANALYZE-0001, TASK-ANALYZE-0002, TASK-ANALYZE-0003, TASK-ANALYZE-0004, TASK-ANALYZE-0005, TASK-ANALYZE-0006, TASK-ANALYZE-0007, TASK-DECIDE-0001
* Required inputs: all reasoning outputs plus `engineering-confidence.yaml`
* Output: `task_outputs/engineering-recommendation.yaml`
* State before: `deciding`
* State after success: `producing_report`
* Failure state: `failed`
* Findings may continue: non-blocking findings carry forward
* Validation before continue: exactly one primary recommendation; blocking-gap rule respected; approval not granted

## Step 14 — Generate Engineering Recommendation Report

* Task: TASK-PRODUCE-0001 @ 0.1.0
* Upstream: TASK-ANALYZE-0001, TASK-ANALYZE-0002, TASK-ANALYZE-0003, TASK-ANALYZE-0004, TASK-ANALYZE-0005, TASK-ANALYZE-0006, TASK-ANALYZE-0007, TASK-DECIDE-0001, TASK-DECIDE-0002
* Required inputs: reasoning outputs, confidence, recommendation
* Output: `reports/engineering-recommendation-report.md`
* State before: `producing_report`
* State after success: `validating_report`
* Failure state: `failed`
* Findings may continue: no blocking findings permitted
* Validation before continue: report self-check passes; all required sections present; marked pending human approval

## Step 15 — Validate Engineering Recommendation Report

* Task: TASK-VALIDATE-0001 @ 0.1.0
* Upstream: TASK-PRODUCE-0001, TASK-ANALYZE-0001, TASK-ANALYZE-0002, TASK-ANALYZE-0003, TASK-ANALYZE-0004, TASK-ANALYZE-0005, TASK-ANALYZE-0006, TASK-ANALYZE-0007, TASK-DECIDE-0001, TASK-DECIDE-0002
* Required inputs: `reports/engineering-recommendation-report.md`, reasoning outputs (for cross-check)
* Output: `task_outputs/recommendation-report-validation.yaml`
* State before: `validating_report`
* State after success: `finalizing_trace`
* Failure state: `blocked` (a `failed` report result holds the run for regeneration)
* Findings may continue: only `passed` or `passed_with_findings` may continue; a `failed` report result moves the run to `blocked`
* Validation before continue: validation result recorded; report eligible for human approval

## Step 16 — Generate Reasoning Trace

* Task: TASK-TRACE-0001 @ 0.1.0
* Upstream: TASK-VALIDATE-0001
* Required inputs: the workflow-managed run-output registry (all recorded task outputs), the report, and the validation result
* Output: `trace.md`
* State before: `finalizing_trace`
* State after success: `finalizing_trace`
* Failure state: `failed`
* Findings may continue: no blocking findings permitted
* Validation before continue: trace exists with all contract-required sections

## Step 17 — Generate Reasoning Manifest

* Task: TASK-TRACE-0002 @ 0.2.0
* Upstream: TASK-TRACE-0001
* Required inputs: the reasoning trace (`trace.md`), the runtime execution manifest (`manifest.yaml`, read as a source), plus task records, report path, and validation result from the workflow-managed run-output registry, and run metadata
* Output: `reports/final-manifest.yaml` (immutable task-owned snapshot; the runtime `manifest.yaml` is not written by this task)
* State before: `finalizing_trace`
* State after success: `finalizing_trace`
* Failure state: `failed`
* Findings may continue: no blocking findings permitted
* Validation before continue: final manifest is valid YAML; all tasks, paths, findings, and validation result present

## Step 18 — Finalize Reasoning Run

* Task: TASK-TRACE-0003 @ 0.2.0
* Upstream: TASK-VALIDATE-0001, TASK-TRACE-0001, TASK-TRACE-0002
* Required inputs: `final-manifest.yaml`, `trace.md`, `recommendation-report-validation.yaml`, report
* Output: `completion.yaml`
* State before: `finalizing_trace`
* State after success: `waiting_for_human_approval` when the completion result sets `waiting_for_human_approval`
* Failure state: `blocked` when the completion result sets `blocked`; `failed` when it sets `failed`
* Findings may continue: open non-blocking findings are carried into `waiting_for_human_approval`
* Validation before continue: single final status set; approval not granted; production not invoked

---

# Environment Dependencies

This block is the **authoritative** declaration of which environment identities
each task's provenance must pin. The planner reads EKB-required status from here
(and from task specifications), never from the provenance record being validated,
so a record cannot omit EKB fields to bypass an EKB check.

* Every task requires **ECF** identity.
* Only `TASK-RETRIEVE-0002` requires **EKB** identity: it is the single task that
  reads the bundled Engineering Knowledge Base directly and derives its output
  (the Engineering Knowledge Package) from it. Downstream tasks receive EKB
  changes transitively through the fingerprint of the knowledge-package input,
  so they require ECF only.

```yaml
environment_dependencies:
  default:
    ecf: required
    ekb: not_required
  TASK-RETRIEVE-0002:
    ecf: required
    ekb: required
```

---

# Machine-Readable Dependency Graph

This block is the authoritative, machine-readable dependency graph for the run. Each `depends_on` list contains explicit Task IDs only (no prose, no ranges). It agrees with the per-step `Upstream` lines above; if they ever diverge, this block governs.

```yaml
depends_on:
  TASK-CLASSIFY-0001: []
  TASK-CLASSIFY-0002:
    - TASK-CLASSIFY-0001
  TASK-RETRIEVE-0001:
    - TASK-CLASSIFY-0001
    - TASK-CLASSIFY-0002
  TASK-RETRIEVE-0002:
    - TASK-CLASSIFY-0001
    - TASK-CLASSIFY-0002
    - TASK-RETRIEVE-0001
  TASK-ANALYZE-0001:
    - TASK-CLASSIFY-0001
    - TASK-CLASSIFY-0002
    - TASK-RETRIEVE-0001
    - TASK-RETRIEVE-0002
  TASK-ANALYZE-0002:
    - TASK-ANALYZE-0001
  TASK-ANALYZE-0003:
    - TASK-ANALYZE-0001
    - TASK-ANALYZE-0002
  TASK-ANALYZE-0004:
    - TASK-ANALYZE-0001
    - TASK-ANALYZE-0002
    - TASK-ANALYZE-0003
  TASK-ANALYZE-0005:
    - TASK-ANALYZE-0001
    - TASK-ANALYZE-0002
    - TASK-ANALYZE-0003
    - TASK-ANALYZE-0004
  TASK-ANALYZE-0006:
    - TASK-ANALYZE-0001
    - TASK-ANALYZE-0004
    - TASK-ANALYZE-0005
  TASK-ANALYZE-0007:
    - TASK-ANALYZE-0001
    - TASK-ANALYZE-0002
    - TASK-ANALYZE-0003
    - TASK-ANALYZE-0004
    - TASK-ANALYZE-0005
    - TASK-ANALYZE-0006
  TASK-DECIDE-0001:
    - TASK-ANALYZE-0001
    - TASK-ANALYZE-0002
    - TASK-ANALYZE-0003
    - TASK-ANALYZE-0004
    - TASK-ANALYZE-0005
    - TASK-ANALYZE-0006
    - TASK-ANALYZE-0007
  TASK-DECIDE-0002:
    - TASK-ANALYZE-0001
    - TASK-ANALYZE-0002
    - TASK-ANALYZE-0003
    - TASK-ANALYZE-0004
    - TASK-ANALYZE-0005
    - TASK-ANALYZE-0006
    - TASK-ANALYZE-0007
    - TASK-DECIDE-0001
  TASK-PRODUCE-0001:
    - TASK-ANALYZE-0001
    - TASK-ANALYZE-0002
    - TASK-ANALYZE-0003
    - TASK-ANALYZE-0004
    - TASK-ANALYZE-0005
    - TASK-ANALYZE-0006
    - TASK-ANALYZE-0007
    - TASK-DECIDE-0001
    - TASK-DECIDE-0002
  TASK-VALIDATE-0001:
    - TASK-PRODUCE-0001
    - TASK-ANALYZE-0001
    - TASK-ANALYZE-0002
    - TASK-ANALYZE-0003
    - TASK-ANALYZE-0004
    - TASK-ANALYZE-0005
    - TASK-ANALYZE-0006
    - TASK-ANALYZE-0007
    - TASK-DECIDE-0001
    - TASK-DECIDE-0002
  TASK-TRACE-0001:
    - TASK-VALIDATE-0001
  TASK-TRACE-0002:
    - TASK-TRACE-0001
  TASK-TRACE-0003:
    - TASK-VALIDATE-0001
    - TASK-TRACE-0001
    - TASK-TRACE-0002
```

Edges are **direct and causal**, not the transitive closure. Each list names only the tasks whose primary output the task directly consumes, or whose completion is an immediate gate. Transitive reachability (for example, that the trace ultimately depends on classification) is computed by tooling from these edges, not hand-listed here.

The traceability tasks consume the **workflow-managed run-output registry** (the recorded task outputs and their bound paths, indexed by the manifest) rather than a producer edge per task. Their direct edges are therefore small:

* `TASK-TRACE-0001` (trace) depends only on `TASK-VALIDATE-0001` — the report-validation gate that must complete before the run can be traced. It reads every task output through the run-output registry, so it needs no per-producer edges.
* `TASK-TRACE-0002` (final manifest) depends only on `TASK-TRACE-0001` — it needs the trace path/existence. It reads the runtime execution manifest and the run-output registry as sources and writes the immutable snapshot `reports/final-manifest.yaml`; those producer edges would be redundant.
* `TASK-TRACE-0003` (finalize) depends directly on `TASK-VALIDATE-0001`, `TASK-TRACE-0001`, and `TASK-TRACE-0002` — the validation result, trace, and the immutable final manifest snapshot it verifies before setting the final run status.

Because `TASK-VALIDATE-0001` transitively depends on every reasoning and production task, the reduced edges preserve the same valid topological order: nothing can run before its real prerequisites.

---

# Validation Gates

* **Per-step output gate** — after every step, the bound primary output must exist and pass the task's declared validation before the next step runs.
* **Report-validation gate** — Step 15 must yield `passed` or `passed_with_findings` before Step 16.
* **Completeness gate** — before `waiting_for_human_approval`, `state.yaml` (runtime infrastructure), `trace.md`, `reports/final-manifest.yaml`, and `completion.yaml` must all exist, and the completion result must set `waiting_for_human_approval`.

---

# Findings Behavior

* A `blocker` finding from any task stops the Workflow at `blocked`.
* Non-blocking findings continue only where the step above marks continuation permitted.
* An open missing-information blocker does not stop the run at Step 11; it constrains Step 13 to a `defer` or `gather_additional_evidence` outcome and is disclosed in the report and completion result.
* All open findings are carried forward into the manifest and completion result and remain visible at the approval gate.

---

# Failure Propagation

The Workflow stops forward execution and transitions to `blocked` or `failed` when:

* a task fails
* a required primary output is missing
* a task output fails validation
* a blocking finding exists
* the recommendation report fails validation (→ `blocked`)
* trace or manifest generation fails (→ `failed`)
* task-version resolution fails (→ `failed`)

On any stop, `state.yaml` is persisted and a failure or block record is written. Downstream reasoning tasks do not run.

---

# Human Approval Boundary

Successful completion of this Workflow means:

```text
waiting_for_human_approval
```

It does not mean:

```text
approved
```

The Workflow must not grant approval, invoke production, modify canonical project artifacts, create ADRs, update architecture documents, or write source code. Any post-approval action is coordinated separately by the Orchestration Engine after a human decides.

---

# Resumption

Given a partially completed run, the Orchestration Engine determines the next runnable task using `state.yaml`, `manifest.yaml`, per-task status, existence of each bound output, and each output's validation status.

Resumption selects the first incomplete or invalid task in graph order and continues. A completed task is not rerun unless its inputs changed, its output is invalid, its pinned version changed, or the run was explicitly restarted.

---

# Cancellation, Suspension, Supersession

* **Cancellation** sets `cancelled`, preserves outputs and trace, records the reason.
* **Suspension** preserves `state.yaml` and completed outputs; the run is resumable.
* **Supersession** records the superseding Run ID; the superseded run is retained for audit.

---

# Workflow Outputs

A complete run produces:

* all eighteen task outputs under `task_outputs/` and `reports/`
* the Engineering Recommendation Report (`reports/engineering-recommendation-report.md`)
* the validated report result (`task_outputs/recommendation-report-validation.yaml`)
* the reasoning trace (`trace.md`)
* the final reasoning manifest snapshot (`reports/final-manifest.yaml`)
* the completion result (`completion.yaml`)
* a persisted runtime `state.yaml` and `manifest.yaml` (runtime infrastructure)
* final state: `waiting_for_human_approval`

---

# Permission Boundaries

Allowed:

* read the accepted Work Request and referenced project context
* read bundled ECF and bundled EKB (read-only)
* invoke the eighteen pinned tasks in graph order
* write runtime outputs under `runtime/runs/<RUN_ID>/`
* persist workflow state

Prohibited:

* modify `vendor/engineering_kb/`
* modify canonical project artifacts, ADRs, architecture documents, or source code
* modify task specifications during a run
* invoke the Engineering Production Engine
* grant human approval
* access sibling repositories or external sources without authorization

---

# Trace and Manifest Requirements

The trace (`trace.md`), the final manifest snapshot (`reports/final-manifest.yaml`), and completion result (`completion.yaml`) — plus the runtime-owned infrastructure `state.yaml` and `manifest.yaml` — must all exist before the run may reach `waiting_for_human_approval`. All conform to `execution/EXECUTION_TRACE_CONTRACT.md` and record observable evidence only, never private chain-of-thought.

---

# Guiding Principle

Turn an accepted Work Request into a validated recommendation and a complete audit trail by running the existing tasks in order, verifying every output, and stopping at the human-approval gate.

Order the work. Bind the evidence. Do not reason, and do not approve.
