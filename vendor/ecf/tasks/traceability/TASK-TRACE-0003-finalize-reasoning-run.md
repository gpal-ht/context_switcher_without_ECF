---

task_id: TASK-TRACE-0003
name: Finalize Reasoning Run
version: 0.2.0
status: draft
category: traceability
owner: engineering_control_framework
idempotent: true
determinism: deterministic
------------------------

# Purpose

Finalize the reasoning run by verifying that it is complete and setting its final status.

This task confirms that every required reasoning task completed, that the report passed validation, and that the trace and the final manifest snapshot exist. It then sets the final reasoning-run status, states whether the run is ready for human approval, records any blockers and required recovery actions, and closes or pauses the run.

It consumes the immutable Final Reasoning Run Manifest (`reports/final-manifest.yaml`), the trace, and the validation result, and produces one Reasoning Run Completion Result. The runtime execution manifest (`manifest.yaml`) is runtime infrastructure; terminal completion evidence is taken from the immutable final manifest snapshot, not the mutable runtime manifest.

The task does not perform reasoning, change any prior result, approve the recommendation, or invoke the Engineering Production Engine.

---

# Core Principle

Finalization is a gate, not a continuation.

It determines the disposition of the run based only on observable results.

Reaching a ready-for-approval state is the end of the reasoning run; the run must not proceed into production, and human approval remains a separate human act.

---

# Inputs

## Required Input: Final Reasoning Run Manifest

The immutable final manifest snapshot at `reports/final-manifest.yaml`, produced by:

```text
TASK-TRACE-0002
Generate Reasoning Manifest
```

## Required Input: Reasoning Trace

Produced by:

```text
TASK-TRACE-0001
Generate Reasoning Trace
```

## Required Input: Report Validation Result

Produced by:

```text
TASK-VALIDATE-0001
Validate Engineering Recommendation Report
```

## Required Input: Engineering Recommendation Report

Produced by:

```text
TASK-PRODUCE-0001
Generate Engineering Recommendation Report
```

## Required Input: Parent Execution Run

A valid reasoning Run ID conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

---

# Preconditions

Execution may begin only when:

* the Final Reasoning Run Manifest (`reports/final-manifest.yaml`) exists
* the Reasoning Trace exists
* the Report Validation Result exists
* the Engineering Recommendation Report exists
* the parent reasoning Run ID exists

If a required artifact is missing, the task must still produce a Completion Result that records the run as `blocked` or `failed` with the missing artifact identified.

---

# Engineering Knowledge References

This task must conform to the run-status and exit-strategy requirements of:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

It applies the human-authority boundary defined by:

```text
execution/ENGINEERING_REASONING_ENGINE.md
```

It must not read or invoke:

```text
execution/ENGINEERING_PRODUCTION_ENGINE.md
```

---

# Required Reasoning Tasks

For the run to be considered complete, the manifest must record a successful terminal status for:

```text
TASK-ANALYZE-0001 .. TASK-ANALYZE-0007
TASK-DECIDE-0001, TASK-DECIDE-0002
TASK-PRODUCE-0001
TASK-VALIDATE-0001
TASK-TRACE-0001
TASK-TRACE-0002
```

A successful terminal status is `completed` or `completed_with_findings`.

---

# Allowed Final Statuses

The task must set exactly one final reasoning-run status from:

```text
completed
completed_with_findings
waiting_for_human_approval
blocked
failed
cancelled
superseded
```

## Status Selection Rules

* `waiting_for_human_approval` when all required tasks succeeded, the report validation result is `passed` or `passed_with_findings`, the trace and manifest exist, and the report is eligible for human approval.
* `completed_with_findings` when the run is otherwise complete but open non-blocking findings remain and human approval is not the immediate next step.
* `completed` when the run is complete and no open findings remain.
* `blocked` when a blocking gap, failed validation, or missing required artifact prevents readiness for approval.
* `failed` when a required reasoning task failed or the run cannot yield a valid outcome.
* `cancelled` when the run was intentionally stopped.
* `superseded` when a newer run replaces this run.

When a run is ready for approval and also carries open findings, `waiting_for_human_approval` takes precedence, and the findings are carried forward in the Completion Result.

---

# Execution Rules

1. Read the Final Reasoning Run Manifest (`reports/final-manifest.yaml`).
2. Verify that every required reasoning task has a successful terminal status.
3. Verify that the Report Validation Result is `passed` or `passed_with_findings`.
4. Verify that the Reasoning Trace and the Final Reasoning Run Manifest exist.
5. Collect open blockers from the manifest findings and the Missing Information Assessment references.
6. Determine readiness for human approval.
7. Select exactly one final reasoning-run status using the status selection rules.
8. Record blockers and required recovery actions for any non-ready status.
9. Set the disposition to close the run or pause it pending recovery or approval.
10. Confirm the human-authority boundary: the run does not grant approval.
11. Confirm that the Engineering Production Engine is not invoked.
12. Produce the Reasoning Run Completion Result.
13. Record the completion result in the run records and reference it from the manifest.

The task must not:

* perform new reasoning or change any prior result
* approve the recommendation
* invoke or reference the Engineering Production Engine as a next step it performs
* mark a run ready for approval when validation failed or a blocker is open

---

# Primary Output

The primary output is a Reasoning Run Completion Result.

Recommended path:

```text
runtime/runs/<RUN_ID>/completion.yaml
```

Example:

```yaml
task_id: TASK-TRACE-0003
task_version: 0.2.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: completed

completeness_checks:
  required_tasks_succeeded: true
  report_validation: passed
  trace_exists: true
  final_manifest_exists: true

open_blockers:
  - id: MISS-0001
    description: Repository integration scope unresolved
    classification: blocker
    origin: missing-information.yaml

readiness:
  ready_for_human_approval: true
  rationale: >
    All required tasks completed, report validation passed, and the trace and
    manifest exist. The open scope blocker is reflected in a
    gather_additional_evidence recommendation, which is itself a valid outcome
    awaiting human approval.

final_run_status: waiting_for_human_approval

required_recovery_actions: []

disposition:
  action: pause
  reason: awaiting_human_approval

human_authority:
  approval_granted: false
  approval_required: true

production_engine_invoked: false

next_action: request_human_approval

validation:
  result: passed
  single_final_status: true
  production_not_invoked: true
  approval_not_granted: true
```

The output is:

* generated
* runtime
* non-canonical
* the terminal record of the reasoning run

---

# Secondary Outputs

The task may produce:

* blocker summaries
* recovery-action recommendations
* run-disposition notes

Secondary outputs must not replace the Reasoning Run Completion Result.

---

# Validation

The task passes validation only when:

* the Work Request ID and Run ID are present
* the completeness checks are recorded
* exactly one final reasoning-run status is set
* the final status is an allowed value and consistent with the completeness checks
* open blockers and required recovery actions are recorded for any non-ready status
* readiness for human approval is stated with rationale
* the disposition to close or pause is recorded
* the human-authority boundary is honored and approval is not granted
* the Engineering Production Engine is not invoked
* task status is recorded

---

# Completion Criteria

The task is complete when:

* all preconditions pass or a blocked or failed result is produced
* completeness checks are performed
* one final reasoning-run status is set
* readiness and disposition are recorded
* validation succeeds
* the Completion Result is written to the runtime run directory
* the run is closed or paused accordingly

---

# Failure Conditions

The task must fail, and set the run status to `blocked` or `failed`, when:

* a required reasoning task did not succeed
* the report validation result is `failed`
* the trace or the final manifest snapshot is missing
* an open blocker prevents readiness and no valid deferral outcome exists
* the completion result cannot be produced

A `blocked` or `failed` run is a correctly finalized run; it is distinct from an execution error of this task.

---

# Failure Output

```yaml
task_id: TASK-TRACE-0003
task_version: 0.2.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: run_not_finalizable
  description: >
    The Report Validation Result is failed, so the run cannot be marked ready
    for human approval.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/recommendation-report-validation.yaml
  partial_output_available: true
  recovery_action: >
    Regenerate and revalidate the recommendation report, then re-run
    finalization. The final run status is set to blocked.
```

---

# Trace Requirements

This task must be recorded with:

* Task ID and version
* Run ID
* completeness checks performed
* open blockers
* final reasoning-run status
* readiness decision
* disposition
* confirmation that approval was not granted
* confirmation that production was not invoked
* final status

The record must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

It must not expose private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly against the same manifest, trace, and validation result must produce the same Reasoning Run Completion Result and the same final status.

---

# Determinism

Expected level:

```text
Deterministic
```

The same completeness inputs must produce the same final status and disposition.

Any nondeterminism in finalization is a defect.

---

# Executor Requirements

The executor requires:

* read access to the manifest, trace, validation result, and report
* read access to bundled ECF, including the trace contract and Reasoning Engine
* permission to write the runtime completion result
* permission to update runtime run records

No network access is required.

The executor must not have permission to invoke the Engineering Production Engine as part of this task.

---

# Permission Boundaries

Allowed:

* read the manifest, trace, validation result, and report
* read bundled ECF
* write the Reasoning Run Completion Result
* set the final reasoning-run status
* update runtime run records

Prohibited:

* perform new reasoning or change prior results
* approve the recommendation
* invoke the Engineering Production Engine
* start a transformation or production run
* modify canonical project artifacts
* modify bundled dependencies
* execute production work
* access external sources without authorization

---

# Security and Privacy

The task must:

* record identifiers and statuses, not sensitive content
* exclude secrets, keys, and tokens
* avoid unnecessary personal data
* preserve repository boundaries

---

# Accessibility

Human-readable output must:

* state the final run status and readiness in plain language
* list blockers and recovery actions as labeled text
* avoid color-only status indicators
* remain understandable when read linearly
* expand uncommon abbreviations

---

# Metrics

Recommended metrics:

* finalization success rate
* ready-for-approval rate
* blocked-run rate
* premature-production-invocation rate, expected to be zero
* human correction rate

Metrics exist to improve run governance.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Ready for Approval

Given a final manifest snapshot showing all required tasks succeeded, a passed validation result, and an existing trace and final manifest,

when `TASK-TRACE-0003` executes,

then the final run status must be `waiting_for_human_approval`, approval must not be granted, and the Engineering Production Engine must not be invoked.

## Scenario 2 — Failed Validation

Given a failed report validation result,

when the task executes,

then the final run status must be `blocked` and required recovery actions must be recorded.

## Scenario 3 — Missing Final Manifest

Given a missing final manifest snapshot (`reports/final-manifest.yaml`),

when the task executes,

then the run must be finalized as `blocked` with the missing artifact identified.

## Scenario 4 — No Production Invocation

Given a run that is ready for approval,

when the task executes,

then the Completion Result must record `production_engine_invoked: false` and the next action must be `request_human_approval`, not a production step.

## Scenario 5 — Single Final Status

Given the completion checks,

when the task executes,

then exactly one final reasoning-run status must be set.

---

# Guiding Principle

Close the reasoning run honestly: confirm completeness, set one final status, and state whether the run is ready for human approval.

Stop at the approval gate. The reasoning run ends here; production begins only after a human decides.
