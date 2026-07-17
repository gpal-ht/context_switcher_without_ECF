---

task_id: TASK-TRACE-0002
name: Generate Reasoning Manifest
version: 0.2.0
status: draft
category: traceability
owner: engineering_control_framework
idempotent: true
determinism: deterministic
------------------------

# Purpose

Produce the machine-readable **Final Reasoning Run Manifest** — an immutable,
task-owned snapshot that summarizes the entire reasoning run.

The final manifest is the structured index of the run: its identity, dependency versions, executor, every task and its status, every runtime input and output, findings, validation result, and the paths to the recommendation report and the trace.

It consumes the run records — including the runtime execution manifest as a read-only source — and produces one Final Reasoning Run Manifest.

The task does not perform reasoning, change any task result, or approve anything. It records the observable state of the run in YAML.

---

# Ownership: runtime manifest vs. final manifest

Two distinct manifests exist and must not be conflated:

* **Runtime execution manifest** — `runtime/runs/<RUN_ID>/manifest.yaml`. This is
  **runtime infrastructure**, owned and continuously mutated by the runtime
  transaction layer (`tools/runtime_state`); it is revision-coupled with
  `state.yaml`. This task reads it as a **read-only source** and must never write
  or mutate it.
* **Final reasoning run manifest** — `reports/final-manifest.yaml`. This is the
  **task-owned, immutable output** of `TASK-TRACE-0002`. It is generated only when
  this task executes, receives a task provenance record, and is never mutated by
  the runtime transaction layer.

---

# Core Principle

The final manifest is a faithful, machine-readable snapshot.

Every entry must correspond to an actual task result, input, output, or finding produced by the run.

The final manifest must never assert a status, output, or result that the run did not produce, and generating it must never rewrite runtime control state.

---

# Inputs

## Required Input: Reasoning Run Records

The recorded results of every task in the run:

```text
TASK-ANALYZE-0001 .. TASK-ANALYZE-0007
TASK-DECIDE-0001, TASK-DECIDE-0002
TASK-PRODUCE-0001
TASK-VALIDATE-0001
TASK-TRACE-0001
```

## Required Input: Engineering Recommendation Report

Produced by:

```text
TASK-PRODUCE-0001
```

## Required Input: Report Validation Result

Produced by:

```text
TASK-VALIDATE-0001
```

## Required Input: Reasoning Trace

Produced by:

```text
TASK-TRACE-0001
```

## Required Input: Run Metadata

Run ID, Work Request ID, ECF version, EKB version, and executor metadata, consistent with:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

## Required Input: Runtime Execution Manifest (read-only source)

The runtime-owned execution manifest:

```text
runtime/runs/<RUN_ID>/manifest.yaml
```

It is read only, as a source of recorded task/output/status facts. This task must
not write or mutate it.

## Required Input: Parent Execution Run

A valid reasoning Run ID.

---

# Preconditions

Execution may begin only when:

* every reasoning task from `TASK-ANALYZE-0001` through `TASK-VALIDATE-0001` has a recorded result
* the Reasoning Trace exists and its path is known
* the Engineering Recommendation Report exists and its path is known
* the Report Validation Result exists
* run metadata is available
* the parent reasoning Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task must conform to the Output Manifest and run-metadata requirements of:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

It records identifiers and paths rather than reproducing artifact content.

---

# Required Manifest Fields

The manifest must include, at minimum:

* Run ID
* Work Request ID
* ECF version
* EKB version
* executor metadata
* every task ID and version
* every task status
* every runtime input
* every runtime output
* findings
* validation result
* recommendation-report path
* trace path
* next required action

Task status values must be drawn from the allowed task-execution status values.

Run status must be drawn from the allowed run status values.

---

# Execution Rules

1. Read the recorded result of every task in the run.
2. Read the report, validation result, and trace locations.
3. Assemble run identity and dependency versions from run metadata.
4. Record executor metadata.
5. For each task, record its ID, version, status, inputs, and outputs.
6. Aggregate findings from every task, preserving IDs and classifications.
7. Record the report path and the trace path.
8. Record the validation result and whether the report is eligible for human approval.
9. Derive the next required action from the recommendation and the validation gate.
10. Ensure every referenced path exists in the run records.
11. Emit the final manifest as machine-readable YAML at the task-owned path.
12. Register the final manifest location for the finalization task.

The task must not:

* perform reasoning or change conclusions
* invent a task status, output, or finding
* approve anything
* modify any prior output, report, or trace
* write or mutate runtime control state (`state.yaml` or the runtime `manifest.yaml`)

---

# Primary Output

The primary output is the **Final Reasoning Run Manifest**, an immutable
task-owned snapshot.

Stable path:

```text
runtime/runs/<RUN_ID>/reports/final-manifest.yaml
```

This is distinct from the runtime execution manifest at
`runtime/runs/<RUN_ID>/manifest.yaml`, which remains runtime-owned and is never
written by this task.

Example:

```yaml
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
run_type: reasoning
run_status: completed_with_findings

ecf_version: v0.1-local
ekb_version: v0.1-local

executor:
  type: ai
  provider: anthropic
  tool: claude-code

tasks:
  - id: TASK-ANALYZE-0001
    version: 0.1.0
    status: completed
    inputs:
      - intent-result.yaml
      - phase-result.yaml
      - context-result.yaml
      - engineering-knowledge-package.md
    outputs:
      - engineering-reasoning-context.yaml
  - id: TASK-ANALYZE-0002
    version: 0.1.0
    status: completed
    inputs: [engineering-reasoning-context.yaml]
    outputs: [engineering-forces.yaml]
  - id: TASK-ANALYZE-0003
    version: 0.1.0
    status: completed
    inputs: [engineering-reasoning-context.yaml, engineering-forces.yaml]
    outputs: [decision-options.yaml]
  - id: TASK-ANALYZE-0004
    version: 0.1.0
    status: completed
    inputs: [engineering-forces.yaml, decision-options.yaml]
    outputs: [engineering-alternatives.yaml]
  - id: TASK-ANALYZE-0005
    version: 0.1.0
    status: completed
    inputs: [engineering-alternatives.yaml, engineering-forces.yaml]
    outputs: [engineering-trade-offs.yaml]
  - id: TASK-ANALYZE-0006
    version: 0.1.0
    status: completed
    inputs: [engineering-alternatives.yaml, engineering-trade-offs.yaml]
    outputs: [engineering-risks.yaml]
  - id: TASK-ANALYZE-0007
    version: 0.1.0
    status: completed_with_findings
    inputs: [engineering-trade-offs.yaml, engineering-risks.yaml]
    outputs: [missing-information.yaml]
  - id: TASK-DECIDE-0001
    version: 0.1.0
    status: completed
    inputs: [missing-information.yaml, engineering-risks.yaml]
    outputs: [engineering-confidence.yaml]
  - id: TASK-DECIDE-0002
    version: 0.1.0
    status: completed
    inputs: [engineering-confidence.yaml, missing-information.yaml]
    outputs: [engineering-recommendation.yaml]
  - id: TASK-PRODUCE-0001
    version: 0.1.0
    status: completed
    inputs: [engineering-recommendation.yaml, engineering-confidence.yaml]
    outputs: [recommendation-report.md]
  - id: TASK-VALIDATE-0001
    version: 0.1.0
    status: completed
    inputs: [recommendation-report.md]
    outputs: [recommendation-report-validation.yaml]
  - id: TASK-TRACE-0001
    version: 0.1.0
    status: completed
    inputs: [recommendation-report.md, recommendation-report-validation.yaml]
    outputs: [trace.md]

findings:
  - id: FIND-TRADE-0001
    classification: minor
    status: open
  - id: MISS-0001
    classification: blocker
    status: open

validation:
  report_validation_result: passed
  eligible_for_human_approval: true

recommendation_report_path: runtime/runs/RUN-REASON-20260710-0001/reports/recommendation-report.md
trace_path: runtime/runs/RUN-REASON-20260710-0001/trace.md

next_required_action: request_human_approval

manifest_validation:
  result: passed
  tasks_recorded: 12
  all_paths_exist: true
```

The output is:

* generated
* runtime
* non-canonical
* machine-readable
* immutable once written (task-owned; provenance-tracked)
* read-only for downstream tasks
* consumed by the finalization task

---

# Secondary Outputs

The task may produce:

* manifest-assembly findings
* missing-path findings
* status-inconsistency findings

Secondary outputs must not replace the Reasoning Run Manifest.

---

# Validation

The task passes validation only when:

* the manifest is valid YAML
* Run ID, Work Request ID, ECF version, and EKB version are present
* executor metadata is present
* every task in the run appears with an ID, version, and status
* every task status is an allowed task-execution status
* runtime inputs and outputs are recorded for each task
* findings are aggregated with IDs and classifications
* the validation result is recorded
* the recommendation-report path and trace path are present and exist
* the next required action is present
* no status, output, or finding is invented
* task status is recorded

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* every task is represented in the manifest
* report path, trace path, findings, and validation result are recorded
* the next required action is set
* manifest validation succeeds
* the final manifest is written to `reports/final-manifest.yaml`
* the final manifest location is available to the finalization task

---

# Failure Conditions

The task must fail when:

* a task result required for the manifest is missing
* the report, validation result, or trace path cannot be resolved
* run metadata is unavailable
* a referenced path does not exist
* the manifest cannot be emitted as valid YAML

The task must not fabricate a task result to complete the manifest.

---

# Failure Output

```yaml
task_id: TASK-TRACE-0002
task_version: 0.2.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: manifest_inputs_incomplete
  description: >
    The Reasoning Trace path could not be resolved, so the manifest cannot
    record a valid trace_path.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/trace.md
  partial_output_available: false
  recovery_action: >
    Generate the Reasoning Trace, then regenerate the manifest.
```

---

# Trace Requirements

This task must be recorded with:

* Task ID and version
* Run ID
* inputs consumed
* tasks enumerated
* findings aggregated
* manifest output location
* final status

The record must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

It must not expose private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly against the same run records must produce the same Reasoning Run Manifest.

---

# Determinism

Expected level:

```text
Deterministic
```

The same run records must produce the same manifest.

Any nondeterminism in the manifest is a defect.

---

# Executor Requirements

The executor requires:

* read access to every task result in the run
* read access to the report, validation result, and trace
* read access to run metadata
* read access to the runtime execution manifest (`manifest.yaml`) as a source
* read access to bundled ECF, including the trace contract
* permission to write the Final Reasoning Run Manifest under `reports/`

It requires no permission to write or mutate runtime control state
(`state.yaml`, runtime `manifest.yaml`). No network access is required.

---

# Permission Boundaries

Allowed:

* read task results, report, validation result, and trace
* read the runtime execution manifest (`manifest.yaml`) as a source
* read bundled ECF
* write the Final Reasoning Run Manifest at `reports/final-manifest.yaml`

Prohibited:

* perform reasoning or change conclusions
* invent task statuses, outputs, or findings
* modify runtime control state (`state.yaml` or the runtime `manifest.yaml`)
* modify canonical project artifacts
* modify bundled dependencies
* modify prior outputs, the report, or the trace
* approve anything
* execute production work
* access external sources without authorization

---

# Security and Privacy

The task must:

* record identifiers and paths, not sensitive content
* exclude secrets, keys, and tokens
* avoid unnecessary personal data
* preserve repository boundaries

---

# Accessibility

Although the manifest is machine-readable, it must:

* use clear, self-describing field names
* avoid encoding meaning in ordering alone
* remain parseable and human-inspectable
* expand uncommon abbreviations in accompanying documentation

---

# Metrics

Recommended metrics:

* manifest-generation success rate
* path-integrity rate
* status-consistency rate
* finding-aggregation completeness
* human correction rate

Metrics exist to improve traceability quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Complete Run

Given recorded results for every task, plus the report, validation result, and trace,

when `TASK-TRACE-0002` executes,

then it must produce a valid YAML manifest listing every task ID, version, and status, all runtime inputs and outputs, findings, the validation result, the report path, the trace path, and the next required action.

## Scenario 2 — Missing Path

Given an unresolved trace path,

when the task executes,

then it must fail with `manifest_inputs_incomplete`.

## Scenario 3 — No Invented Status

Given a task that failed,

when the manifest is generated,

then that task must be recorded with its actual failed status, not a fabricated completed status.

## Scenario 4 — Findings Aggregated

Given open findings across tasks,

when the manifest is generated,

then every finding must appear with its ID and classification.

## Scenario 5 — Machine Readable

Given a generated manifest,

when it is parsed by a YAML reader,

then it must parse without error and expose every required field.

---

# Guiding Principle

Produce the structured, machine-readable index of the run that faithfully records every task, input, output, finding, and result.

Summarize the run exactly as it happened; add nothing and hide nothing.
