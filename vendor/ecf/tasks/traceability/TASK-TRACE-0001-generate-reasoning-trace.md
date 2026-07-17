---

task_id: TASK-TRACE-0001
name: Generate Reasoning Trace
version: 0.1.0
status: draft
category: traceability
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Produce the consolidated Reasoning Trace for the reasoning run.

This task assembles the observable record of the run: the inputs used, evidence and knowledge applied, rules followed, intermediate artifacts produced, findings raised, validation performed, and the conclusion reached.

It consumes the outputs of every preceding reasoning task and produces one Reasoning Trace.

The task does not request, reconstruct, or expose private model chain-of-thought, and it does not perform new reasoning or change any prior output.

---

# Core Principle

A trace records what is observable.

It explains how engineering context and knowledge led to the recommendation, using only the evidence, rules, and artifacts the pipeline actually produced.

It must never attempt to capture hidden internal reasoning.

---

# Inputs

## Required Input: Reasoning Task Outputs

The primary outputs of:

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

## Required Input: Engineering Recommendation Report

Produced by:

```text
TASK-PRODUCE-0001
Generate Engineering Recommendation Report
```

## Required Input: Report Validation Result

Produced by:

```text
TASK-VALIDATE-0001
Validate Engineering Recommendation Report
```

## Required Input: Parent Execution Run

A valid reasoning Run ID conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

---

# Preconditions

Execution may begin only when:

* every reasoning task from `TASK-ANALYZE-0001` through `TASK-DECIDE-0002` has produced a recorded result
* the Engineering Recommendation Report exists
* the Report Validation Result exists
* the parent reasoning Run ID exists
* run metadata required by the trace contract is available

If any precondition fails, the task must still attempt to produce a failure trace where technically possible.

---

# Engineering Knowledge References

This task must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

It must satisfy the additional Reasoning Trace requirements defined by that contract, and the confidence content it records must conform to:

```text
knowledge/CONFIDENCE_MODEL.md
```

---

# Reasoning Trace Content

Per the Execution Trace Contract, the Reasoning Trace must record at least:

* run summary and final status
* inputs consumed with provenance
* dependency versions, including ECF and EKB
* evidence used, cited by ID or path
* applied rules, including the Decision Guide and Confidence Model
* execution summary covering intent, phase, retrieved Knowledge Object IDs, retrieval path, forces, alternatives, trade-offs, risks, assumptions, recommendation, confidence, and missing information
* findings aggregated from all tasks
* outputs produced, including the recommendation report
* validation performed, including the report validation result
* unresolved issues
* next action

---

# Execution Rules

1. Read the outputs of every preceding reasoning task.
2. Read the Engineering Recommendation Report and the Report Validation Result.
3. Assemble the required run metadata from the parent run.
4. Compose the run summary from the engineering question and final status.
5. List every input with its identifier, path, and role.
6. Record dependency versions, including ECF and EKB versions.
7. Record the evidence used, cited by stable ID or path.
8. Record the applied rules, including the primary Decision Guide and the Confidence Model.
9. Compose the execution summary from the observable outputs of each task.
10. Aggregate findings from every task using the contract classifications.
11. List outputs produced, including the report and validation result.
12. Record the validation performed and its result.
13. Record unresolved issues from the Missing Information Assessment and open findings.
14. Record the next action derived from the recommendation and validation gate.
15. Confirm the trace records observable evidence only.
16. Produce the Reasoning Trace.
17. Register the trace location for the manifest task.

The task must not:

* request or infer private chain-of-thought
* perform new reasoning or change conclusions
* modify any prior output or the report
* omit findings or unresolved issues to present a cleaner result

---

# Primary Output

The primary output is a Reasoning Trace.

Recommended path:

```text
runtime/runs/<RUN_ID>/trace.md
```

The trace is a Markdown document with the contract-required structure and a metadata header, for example:

```yaml
---
run_id: RUN-REASON-20260710-0001
run_type: reasoning
status: completed_with_findings
started_at: 2026-07-10T10:00:00+05:30
completed_at: 2026-07-10T10:20:00+05:30
executor:
  type: ai
  provider: anthropic
  tool: claude-code
ecf_version: v0.1-local
ekb_version: v0.1-local
consumer_repository: context_switcher
engineering_question: >
  Should Repository Integration become a first-class subsystem
  within Context Switcher?
generated: true
canonical: false
---
```

The document body then contains the required sections: Run Summary, Inputs, Dependency Versions, Evidence, Applied Rules, Execution Summary, Findings, Outputs, Validation, Unresolved Issues, and Next Action, plus the Reasoning Trace additions.

The output is:

* generated
* runtime
* non-canonical
* read-only for downstream tasks
* consumed by the manifest and finalization tasks

---

# Secondary Outputs

The task may produce:

* trace-assembly findings
* missing-metadata findings
* recovery recommendations

Secondary outputs must not replace the Reasoning Trace.

---

# Validation

The task passes validation only when:

* the Run ID and required run metadata are present
* every contract-required section is present
* every reasoning task output is represented in the inputs or execution summary
* evidence is cited by stable ID or path
* the confidence content conforms to the Confidence Model
* findings from all tasks are aggregated
* the recommendation report and validation result are recorded as outputs and validation
* unresolved issues are stated, or explicitly `None.`
* the next action is present
* no private chain-of-thought is requested or exposed
* task status is recorded

---

# Completion Criteria

The task is complete when:

* all preconditions pass or a failure trace is produced
* the Reasoning Trace contains every required section
* the trace records observable evidence only
* validation succeeds
* the trace location is available to the manifest task
* the trace is written to the runtime run directory

---

# Failure Conditions

The task must fail when:

* required run metadata is unavailable
* the reasoning task outputs cannot be read
* the recommendation report or validation result is missing
* a contract-required section cannot be populated from observable evidence

When failure occurs, the task should still write a failure trace where technically possible, explaining where assembly stopped.

---

# Failure Output

```yaml
task_id: TASK-TRACE-0001
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: trace_assembly_incomplete
  description: >
    The Report Validation Result is missing, so the Validation section of the
    Reasoning Trace cannot be populated from observable evidence.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/recommendation-report-validation.yaml
  partial_output_available: true
  recovery_action: >
    Complete report validation, then regenerate the Reasoning Trace.
```

---

# Trace Requirements

This task produces the Reasoning Trace, and its own execution must additionally be recorded with:

* Task ID and version
* Run ID
* inputs consumed
* trace sections assembled
* findings aggregated
* trace output location
* final status

The produced trace and this task record must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

Neither the trace nor its task record may expose private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly against the same reasoning outputs, report, validation result, and run metadata should produce a materially equivalent Reasoning Trace.

---

# Determinism

Expected level:

```text
Constrained
```

Narrative wording may differ, but the following must remain materially consistent:

* run metadata
* inputs and dependency versions
* evidence and applied rules recorded
* aggregated findings
* recorded recommendation and confidence
* unresolved issues
* next action

---

# Executor Requirements

The executor requires:

* read access to all reasoning task outputs
* read access to the recommendation report and validation result
* read access to run metadata
* read access to bundled ECF, including the trace contract
* permission to write the runtime trace
* permission to update runtime run records

No network access is required.

---

# Permission Boundaries

Allowed:

* read reasoning outputs, report, and validation result
* read bundled ECF
* write the Reasoning Trace to the runtime run directory
* update runtime run records

Prohibited:

* request or expose private chain-of-thought
* modify canonical project artifacts
* modify bundled dependencies
* perform new reasoning or change conclusions
* modify the report or prior outputs
* approve the report
* execute production work
* access external sources without authorization

---

# Security and Privacy

The task must:

* exclude secrets, keys, passwords, and tokens from the trace
* avoid unnecessary personal data
* cite sensitive sources rather than reproducing them
* preserve repository boundaries
* record only evidence required for auditability

---

# Accessibility

The trace must:

* use explicit section headings in the contract order
* present findings and unresolved issues as labeled text
* avoid color-only status indicators
* provide text descriptions for any diagrams
* remain understandable when read linearly
* expand uncommon abbreviations

---

# Metrics

Recommended metrics:

* trace-generation success rate
* section-completeness rate
* finding-aggregation completeness
* missing-metadata rate
* human correction rate

Metrics exist to improve traceability quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Complete Run

Given completed reasoning outputs, a report, and a validation result for:

```text
Should Repository Integration become a first-class subsystem?
```

when `TASK-TRACE-0001` executes,

then it must produce a Reasoning Trace containing every contract-required section and the Reasoning Trace additions, citing evidence by ID or path.

## Scenario 2 — No Chain-of-Thought

Given the reasoning outputs,

when the trace is inspected,

then it must record observable evidence and rules only, with no private model chain-of-thought.

## Scenario 3 — Findings Aggregated

Given open findings in several reasoning outputs,

when the task executes,

then all findings must appear in the trace Findings section.

## Scenario 4 — Failure Trace

Given a missing validation result,

when the task executes,

then it must fail with `trace_assembly_incomplete` and still write a partial failure trace where possible.

## Scenario 5 — Next Action

Given a recommendation to gather additional evidence,

when the trace is generated,

then the Next Action section must reflect that direction.

---

# Guiding Principle

Leave behind enough observable evidence for another engineer to understand what was requested, what was used, what was concluded, and what should happen next.

Record what can be seen; never expose what cannot.
