---

task_id: TASK-VALIDATE-0001
name: Validate Engineering Recommendation Report
version: 0.1.0
status: draft
category: validation
owner: engineering_control_framework
idempotent: true
determinism: deterministic
------------------------

# Purpose

Validate that the Engineering Recommendation Report is complete, traceable, internally consistent, and conformant to its contract before the report is allowed to move toward human approval.

This task consumes the Engineering Recommendation Report and the reasoning outputs it was compiled from, and produces one Engineering Recommendation Report Validation Result.

The task does not repair the report, change the recommendation, approve the report, or perform new reasoning. A failed validation must prevent the report from moving to human approval.

---

# Core Principle

Validation is an independent check, not an editing pass.

The task reports what is wrong; it never silently fixes the report.

If validation fails, the report is not eligible for human approval until it is regenerated and revalidated.

---

# Inputs

## Required Input: Engineering Recommendation Report

Produced by:

```text
TASK-PRODUCE-0001
Generate Engineering Recommendation Report
```

## Required Input: Reasoning Outputs

The outputs the report was compiled from:

```text
TASK-ANALYZE-0001  Engineering Reasoning Context
TASK-ANALYZE-0002  Engineering Forces Analysis
TASK-ANALYZE-0003  Decision Option Set
TASK-ANALYZE-0004  Engineering Alternative Set
TASK-ANALYZE-0005  Engineering Trade-off Analysis
TASK-ANALYZE-0006  Engineering Risk Analysis
TASK-ANALYZE-0007  Missing Information Assessment
TASK-DECIDE-0001   Engineering Confidence Assessment
TASK-DECIDE-0002   Engineering Recommendation
```

## Required Input: Report Contract

```text
artifacts/ENGINEERING_RECOMMENDATION_REPORT_CONTRACT.md
```

## Required Input: Confidence Model

```text
knowledge/CONFIDENCE_MODEL.md
```

## Required Input: Parent Execution Run

A valid reasoning Run ID conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

---

# Preconditions

Execution may begin only when:

* `TASK-PRODUCE-0001` produced a report
* the reasoning outputs the report cites are available
* the report contract and Confidence Model are available
* the parent reasoning Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task references:

* the Engineering Recommendation Report Contract
* the Confidence Model
* the Execution Trace Contract

These references define the required structure and rules the report must satisfy.

They must not be modified.

---

# Validation Checks

The task must perform, at minimum, the following checks. Each check produces a pass or fail result with evidence.

## 1. Contract Completeness

Every required report section is present and non-empty, in the contract order.

## 2. Provenance

Every report section traces to the correct reasoning output, and every cited identifier exists in the source outputs.

## 3. Evidence Versus Assumptions Separation

The report keeps evidence distinct from assumptions, consistent with the reasoning outputs, and does not present assumptions as facts.

## 4. Alternative Coverage

Every viable alternative from the Engineering Alternative Set appears in the report, including alternatives not selected.

## 5. Trade-off Coverage

The report reflects the trade-off comparisons from the Engineering Trade-off Analysis without adding new comparisons.

## 6. Multidimensional Confidence

All five confidence dimensions are present, each with a level and justification, and the Overall Confidence is a narrative that is not an average.

## 7. Recommendation Consistency

The report presents exactly one primary recommendation, and its outcome, selected option, and selected alternative match the Engineering Recommendation exactly.

## 8. Missing-Information Disclosure

Every blocker and every classified gap from the Missing Information Assessment is disclosed in the report.

## 9. Absence of Human-Approval Claims

The report does not claim, imply, or grant human approval, and it is marked pending human approval.

## 10. Absence of Unsupported Project Facts

The report contains no project fact that is absent from the reasoning outputs.

## Blocking-Gap Consistency

If the Missing Information Assessment records an open blocker, the report recommendation outcome must be `defer` or `gather_additional_evidence`.

---

# Severity Rules

Each failed check is assigned a severity.

```text
blocker
major
minor
```

A `blocker` or any failed contract-completeness, recommendation-consistency, human-approval, or unsupported-fact check makes the overall validation result `failed`.

A report with a `failed` result must not move to human approval.

A report with only `minor` findings may be marked `passed_with_findings` at the discretion of the finalization task, but the findings must remain visible.

---

# Execution Rules

1. Read the Engineering Recommendation Report.
2. Read every reasoning output the report cites.
3. Load the report contract and the Confidence Model.
4. Run each validation check in order.
5. For each check, record pass or fail with cited evidence.
6. Assign a severity to each failed check.
7. Determine the overall validation result from the check results and severity rules.
8. Do not modify the report under any circumstance.
9. Record every failed check as a finding.
10. Set the gate decision on whether the report may proceed to human approval.
11. Produce the Engineering Recommendation Report Validation Result.
12. Add the task result to the parent execution trace.

The task must not:

* edit or repair the report
* change the recommendation or confidence
* approve the report
* perform new reasoning
* re-derive alternatives, trade-offs, or risks

---

# Primary Output

The primary output is an Engineering Recommendation Report Validation Result.

Recommended path:

```text
runtime/runs/<RUN_ID>/task_outputs/recommendation-report-validation.yaml
```

Example:

```yaml
task_id: TASK-VALIDATE-0001
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: completed

report_under_validation:
  path: runtime/runs/RUN-REASON-20260710-0001/reports/recommendation-report.md
  report_id: ERR-0001

checks:
  - id: CHK-01-contract-completeness
    result: pass
    evidence: all eleven required sections present in order
  - id: CHK-02-provenance
    result: pass
    evidence: every cited identifier resolves to a source output
  - id: CHK-03-evidence-vs-assumptions
    result: pass
    evidence: assumptions section distinct from evidence
  - id: CHK-04-alternative-coverage
    result: pass
    evidence: ALT-0001..ALT-0004 all present
  - id: CHK-05-trade-off-coverage
    result: pass
    evidence: axes AXIS-0001..AXIS-0004 reflected
  - id: CHK-06-multidimensional-confidence
    result: pass
    evidence: five dimensions and narrative present; not averaged
  - id: CHK-07-recommendation-consistency
    result: pass
    evidence: single recommendation matches engineering-recommendation.yaml
  - id: CHK-08-missing-information-disclosure
    result: pass
    evidence: blocker MISS-0001 disclosed
  - id: CHK-09-no-approval-claims
    result: pass
    evidence: report marked pending_human_approval; no approval statement
  - id: CHK-10-no-unsupported-facts
    result: pass
    evidence: no project fact outside source outputs
  - id: CHK-11-blocking-gap-consistency
    result: pass
    evidence: open blocker present; outcome is gather_additional_evidence

overall:
  result: passed
  eligible_for_human_approval: true

findings: []

validation:
  result: passed
  checks_run: 11
  report_modified: false
```

The output is:

* generated
* runtime
* non-canonical
* read-only for downstream tasks
* consumed by the traceability and finalization tasks

---

# Secondary Outputs

The task may produce:

* per-check findings
* severity classifications
* remediation recommendations that reference regeneration, not in-place edits
* trace fragments

Secondary outputs must not replace the Validation Result.

---

# Validation

The task passes its own execution validation only when:

* the Work Request ID is present
* the Run ID is present
* every required check was run
* every check has a pass or fail result with evidence
* the overall result follows the severity rules
* the gate decision on human-approval eligibility is present
* the report was not modified
* task status is recorded
* the result is added to the parent execution trace

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* every validation check has run
* the overall result and gate decision are recorded
* the report remains unmodified
* the Validation Result is available to the finalization task
* the task result is recorded in the execution trace

---

# Failure Conditions

The task must fail when:

* the report is missing
* a reasoning output required to verify a check is missing
* the report contract or Confidence Model cannot be read
* a check cannot be evaluated because inputs are unreadable
* the task cannot produce a Validation Result

A failed task execution is distinct from a report that validates as `failed`.

A `failed` report result is a successful task execution that correctly reports non-conformance.

---

# Failure Output

```yaml
task_id: TASK-VALIDATE-0001
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: validation_inputs_unavailable
  description: >
    The report could not be validated because a cited reasoning output is
    missing and its checks cannot be evaluated.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-recommendation.yaml
  partial_output_available: false
  recovery_action: >
    Restore the missing reasoning outputs or regenerate the report, then
    re-run validation.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent Run ID
* report under validation
* reasoning outputs consulted
* each check and its result with evidence
* severities assigned
* overall result
* human-approval gate decision
* confirmation that the report was not modified
* findings
* output location
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace must explain the observable basis for each check result without exposing private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly against the same report and reasoning outputs must produce the same Validation Result.

---

# Determinism

Expected level:

```text
Deterministic
```

The same report and the same reasoning outputs must produce the same check results and the same overall result.

Any nondeterminism in validation is a defect.

---

# Executor Requirements

The executor requires:

* read access to the Engineering Recommendation Report
* read access to the reasoning outputs
* read access to bundled ECF, including the report contract and Confidence Model
* permission to write runtime task output
* permission to update runtime trace data

No network access is required.

The executor must have no permission to modify the report.

---

# Permission Boundaries

Allowed:

* read the report and reasoning outputs
* read bundled ECF
* write the Validation Result
* write findings
* update runtime trace data

Prohibited:

* modify or repair the report
* modify canonical project artifacts
* modify bundled dependencies
* change the recommendation or confidence
* approve the report
* perform new reasoning
* execute production work
* access external sources without authorization

---

# Security and Privacy

The task must:

* reference sensitive report content rather than duplicating it
* avoid recording secrets or credentials
* avoid unnecessary personal information
* preserve repository boundaries

---

# Accessibility

Human-readable output must:

* list each check with an explicit name and result
* state failures in plain language with remediation guidance
* avoid color-only pass or fail indicators
* remain understandable when read linearly
* expand uncommon abbreviations

---

# Metrics

Recommended metrics:

* validation execution success rate
* report pass rate
* most frequently failed check
* false-pass rate detected downstream
* human correction rate
* regeneration-after-failure rate

Metrics exist to improve report quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Conformant Report

Given a report compiled faithfully from valid reasoning outputs,

when `TASK-VALIDATE-0001` executes,

then every check must pass, the overall result must be `passed`, and the report must be eligible for human approval.

## Scenario 2 — Missing Confidence Dimension

Given a report missing one confidence dimension,

when the task executes,

then the multidimensional-confidence check must fail, the overall result must be `failed`, and the report must not be eligible for human approval.

## Scenario 3 — Approval Claim

Given a report that states approval has been granted,

when the task executes,

then the no-approval-claims check must fail and the overall result must be `failed`.

## Scenario 4 — Unsupported Project Fact

Given a report containing a project fact absent from the reasoning outputs,

when the task executes,

then the no-unsupported-facts check must fail.

## Scenario 5 — No Silent Repair

Given a report with a missing section,

when the task executes,

then the task must record the failure and must not add the missing section itself.

## Scenario 6 — Blocking Gap With Proceed

Given a report whose recommendation is `proceed` while an open blocker exists,

when the task executes,

then the blocking-gap-consistency check must fail.

---

# Guiding Principle

Independently verify that the report is complete, traceable, and honest about uncertainty and approval.

Report problems; never fix them silently, and never let a non-conformant report reach human approval.
