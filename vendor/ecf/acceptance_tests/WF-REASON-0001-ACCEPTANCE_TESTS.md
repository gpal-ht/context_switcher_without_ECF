# WF-REASON-0001 — Acceptance Tests

# Purpose

These acceptance tests validate the structural and execution-contract correctness of the Engineering Recommendation Workflow:

```text
workflows/reasoning/WF-REASON-0001-engineering-recommendation.md
```

They validate contracts and flow structure. They do not validate the correctness of any specific engineering recommendation.

Each test is observable and repeatable against the repository and against a run's runtime outputs. No test requires or inspects private model chain-of-thought.

---

# Scope

* In scope: task reachability, version compatibility, input/output continuity, output-filename stability, runtime-root consistency, failure propagation, cascading validation failure, human-approval boundary, trace completeness, resumption, observable-evidence-only, and a full reference-scenario structural pass.
* Out of scope: whether the final architectural recommendation is correct.

---

# Reference Data

## Expected task sequence (18)

```text
1  TASK-CLASSIFY-0001
2  TASK-CLASSIFY-0002
3  TASK-RETRIEVE-0001
4  TASK-RETRIEVE-0002
5  TASK-ANALYZE-0001
6  TASK-ANALYZE-0002
7  TASK-ANALYZE-0003
8  TASK-ANALYZE-0004
9  TASK-ANALYZE-0005
10 TASK-ANALYZE-0006
11 TASK-ANALYZE-0007
12 TASK-DECIDE-0001
13 TASK-DECIDE-0002
14 TASK-PRODUCE-0001
15 TASK-VALIDATE-0001
16 TASK-TRACE-0001
17 TASK-TRACE-0002
18 TASK-TRACE-0003
```

## Expected output bindings

```text
task_outputs/engineering-intent.yaml
task_outputs/engineering-phase.yaml
task_outputs/engineering-context.yaml
task_outputs/engineering-knowledge-package.md
task_outputs/engineering-reasoning-context.yaml
task_outputs/engineering-forces.yaml
task_outputs/decision-options.yaml
task_outputs/engineering-alternatives.yaml
task_outputs/engineering-trade-offs.yaml
task_outputs/engineering-risks.yaml
task_outputs/missing-information.yaml
task_outputs/engineering-confidence.yaml
task_outputs/engineering-recommendation.yaml
reports/engineering-recommendation-report.md
task_outputs/recommendation-report-validation.yaml
trace.md
reports/final-manifest.yaml
completion.yaml
```

---

# WAT-REASON-0001 — Complete Task Reachability

**Given** the Workflow specification,

**when** every referenced Task ID is resolved against `tasks/`,

**then** each of the 18 Task IDs must resolve to exactly one task specification file, and no referenced Task ID may be unresolved or ambiguous.

**Pass criteria:** 18/18 Task IDs resolve to exactly one file each.

---

# WAT-REASON-0002 — Version Compatibility

**Given** the Workflow pins every task to `0.1.0`,

**when** each pinned version is compared to the version declared in the corresponding task specification,

**then** every pinned version must match the task file.

**Pass criteria:** 18/18 versions match. Any mismatch fails this test and must be reported, not silently changed.

---

# WAT-REASON-0003 — Input/Output Continuity

**Given** the task graph,

**when** each step's required inputs are compared to upstream bound outputs,

**then** every required downstream input must map to an existing upstream output, and no runtime output may be orphaned except the terminal completion result.

**Pass criteria:** every non-entry step's inputs resolve to an upstream producer; `completion.yaml` is the only output with no downstream consumer.

---

# WAT-REASON-0004 — Stable Filenames

**Given** the output bindings,

**when** the bound outputs are enumerated,

**then** every task must have exactly one workflow-bound primary output filename, and no two tasks may bind to the same path.

**Pass criteria:** 18 bindings, 18 unique paths, no duplicates.

---

# WAT-REASON-0005 — Runtime-Root Consistency

**Given** every runtime path referenced by the Workflow,

**when** the paths are inspected,

**then** every path must resolve under:

```text
runtime/runs/<RUN_ID>/
```

with task outputs under `task_outputs/`, reports (incl. the immutable `final-manifest.yaml`) under `reports/`, task-owned `trace.md` and `completion.yaml` at the run root, and the runtime-owned infrastructure `state.yaml` and `manifest.yaml` at the run root.

**Pass criteria:** no occurrence of `runtime/work_requests/` or `runtime/reasoning_runs/` as a run root in the Workflow specification.

---

# WAT-REASON-0006 — Failure Propagation

**Given** a run in which any task returns `failed`, produces no primary output, or emits a blocking finding,

**when** the Workflow evaluates the step gate,

**then** the run must transition to `blocked` or `failed`, and no downstream reasoning task may run.

**Pass criteria:** downstream steps do not execute after a failed or blocked step; `state.yaml` records the stop.

---

# WAT-REASON-0007 — Cascading Validation Failure

**Given** a run in which TASK-VALIDATE-0001 returns a `failed` report validation result,

**when** the Workflow evaluates the report-validation gate,

**then** the run must reach `blocked` or `failed` and must never reach `waiting_for_human_approval`.

**Pass criteria:** a failed report validation cannot produce a successful exit state.

---

# WAT-REASON-0008 — Human Approval Boundary

**Given** a completed run,

**when** the terminal state and actions are inspected,

**then** the Workflow must terminate at `waiting_for_human_approval`, must not grant approval, and must not invoke the Engineering Production Engine or modify any canonical artifact.

**Pass criteria:** `completion.yaml` records `approval_granted: false` and `production_engine_invoked: false`; final state is `waiting_for_human_approval`.

---

# WAT-REASON-0009 — Trace Completeness

**Given** a run approaching its successful exit state,

**when** the completeness gate is evaluated,

**then** `state.yaml` (runtime infrastructure), `trace.md`, `reports/final-manifest.yaml`, and `completion.yaml` must all exist before the run may reach `waiting_for_human_approval`.

**Pass criteria:** all four artifacts exist; absence of any one prevents the successful exit state. The task-owned final manifest is `reports/final-manifest.yaml`; the run-root `manifest.yaml` is runtime infrastructure.

---

# WAT-REASON-0010 — Resumption

**Given** a partially completed run with valid outputs for steps 1..N and no output for step N+1,

**when** the Orchestration Engine determines the next runnable task from `state.yaml`, `manifest.yaml`, per-task status, and output existence and validity,

**then** it must select step N+1 (the first incomplete task in graph order) and must not rerun any valid completed task.

**Pass criteria:** the first incomplete/invalid task is selected; completed valid tasks are not rerun unless inputs, output validity, or pinned version changed, or the run was explicitly restarted.

---

# WAT-REASON-0011 — No Private Chain-of-Thought

**Given** the Workflow and its composed tasks,

**when** their evidence and rationale requirements are inspected,

**then** the Workflow and every task must require observable evidence and rationale only, and none may request or expose private model chain-of-thought.

**Pass criteria:** every trace and rationale requirement is satisfiable with observable evidence; no step requires hidden reasoning.

---

# WAT-REASON-0012 — Reference Scenario

**Given** the engineering question:

```text
Should Repository Integration become a first-class subsystem within Context Switcher?
```

carried by an accepted Work Request,

**when** WF-REASON-0001 executes end to end,

**then** the Workflow must resolve all 18 tasks, produce all 18 bound outputs, reach a validated Engineering Recommendation Report, and exit at `waiting_for_human_approval`.

**Pass criteria:** 18 outputs produced under `runtime/runs/<RUN_ID>/`; `recommendation-report-validation.yaml` records `passed` or `passed_with_findings`; `completion.yaml` sets `waiting_for_human_approval`.

This test validates contracts and flow structure, not the correctness of the final architectural recommendation.

---

# Structural Validation Summary

A Workflow passes structural acceptance when WAT-REASON-0001 through WAT-REASON-0011 pass, and WAT-REASON-0012 confirms an end-to-end structural traversal reaches the successful exit state.

These tests are prose-executable today (verifiable by inspection and by simple repository queries) and are intended to be automated by a future workflow runner.

---

# Guiding Principle

Prove that the plan is well-formed before trusting any run it produces: every task real, every version pinned, every output bound and continuous, every failure path honored, and the human-approval gate intact.
