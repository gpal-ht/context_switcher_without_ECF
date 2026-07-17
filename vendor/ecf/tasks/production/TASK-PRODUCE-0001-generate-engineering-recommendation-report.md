---

task_id: TASK-PRODUCE-0001
name: Generate Engineering Recommendation Report
version: 0.1.0
status: draft
category: production
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Compile the observable outputs of the reasoning pipeline into a single Engineering Recommendation Report.

This task assembles a human-readable, contract-conformant report from the already produced reasoning outputs. It performs document production only.

It consumes every reasoning output and produces one Engineering Recommendation Report.

The task does not perform new reasoning, introduce new alternatives or evidence, recompute confidence, change the recommendation, validate the report, or approve it.

---

# Core Principle

Report generation is compilation, not reasoning.

Every statement in the report must be traceable to an existing reasoning output.

If a required input is missing or inconsistent, the task must fail rather than fill the gap with new content.

---

# Inputs

## Required Input: Engineering Reasoning Context

Produced by:

```text
TASK-ANALYZE-0001
Build Engineering Reasoning Context
```

## Required Input: Engineering Forces Analysis

Produced by:

```text
TASK-ANALYZE-0002
Identify Engineering Forces
```

## Required Input: Decision Option Set

Produced by:

```text
TASK-ANALYZE-0003
Identify Decision Options
```

## Required Input: Engineering Alternative Set

Produced by:

```text
TASK-ANALYZE-0004
Generate Engineering Alternatives
```

## Required Input: Engineering Trade-off Analysis

Produced by:

```text
TASK-ANALYZE-0005
Analyze Engineering Trade-offs
```

## Required Input: Engineering Risk Analysis

Produced by:

```text
TASK-ANALYZE-0006
Identify Engineering Risks
```

## Required Input: Missing Information Assessment

Produced by:

```text
TASK-ANALYZE-0007
Identify Missing Information
```

## Required Input: Engineering Confidence Assessment

Produced by:

```text
TASK-DECIDE-0001
Assess Engineering Confidence
```

## Required Input: Engineering Recommendation

Produced by:

```text
TASK-DECIDE-0002
Generate Engineering Recommendation
```

## Required Input: Parent Execution Run

A valid reasoning Run ID conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

---

# Preconditions

Execution may begin only when:

* `TASK-ANALYZE-0001` through `TASK-ANALYZE-0007` completed successfully
* `TASK-DECIDE-0001` and `TASK-DECIDE-0002` completed successfully
* every consumed output validates
* the engineering question is identical across all inputs
* exactly one primary recommendation exists
* the parent reasoning Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task must conform to:

```text
artifacts/ENGINEERING_RECOMMENDATION_REPORT_CONTRACT.md
```

The confidence section must reflect:

```text
knowledge/CONFIDENCE_MODEL.md
```

The report must not copy EKB Knowledge Objects verbatim; it references retrieved knowledge by ID as recorded in the Engineering Knowledge Package.

---

# Required Report Sections

The report must contain the sections required by the report contract, populated only from reasoning outputs:

1. Work Request
2. Current Engineering Context
3. Retrieved Engineering Knowledge
4. Reasoning Trace
5. Engineering Forces
6. Alternatives
7. Trade-offs
8. Recommendation
9. Confidence
10. Missing Information
11. Suggested Next Transformation

The Confidence section must present all five confidence dimensions and the Overall Confidence narrative without averaging.

The Reasoning Trace section is a human-readable summary that references the full Reasoning Trace artifact; it does not replace it.

---

# Section-to-Source Mapping

Every report section must be compiled from a specific source.

```text
Work Request                  ← Engineering Reasoning Context
Current Engineering Context   ← Engineering Reasoning Context
Retrieved Engineering Knowledge ← Engineering Reasoning Context (Knowledge Package references)
Reasoning Trace (summary)     ← reasoning outputs; full trace produced by TASK-TRACE-0001
Engineering Forces            ← Engineering Forces Analysis
Alternatives                  ← Engineering Alternative Set
Trade-offs                    ← Engineering Trade-off Analysis
Recommendation                ← Engineering Recommendation
Confidence                    ← Engineering Confidence Assessment
Missing Information           ← Missing Information Assessment
Suggested Next Transformation ← Engineering Recommendation and Missing Information Assessment
```

Risk information must be presented where relevant, sourced from the Engineering Risk Analysis.

The task must not create a section that has no source.

---

# Execution Rules

1. Read every reasoning output.
2. Confirm the exact engineering question is consistent across all inputs.
3. Load the report contract and enumerate the required sections.
4. For each required section, compile content from its mapped source only.
5. Preserve provenance identifiers so each claim can be traced.
6. Present the recommendation exactly as produced, without alteration.
7. Present all five confidence dimensions and the Overall Confidence narrative.
8. Present missing information grouped by classification, including blockers.
9. Present alternatives, including which were not selected.
10. Present trade-offs without adding new comparisons.
11. Derive the Suggested Next Transformation from the recommendation outcome and unresolved information.
12. State explicitly that the report recommends and the human decides.
13. State that human approval is required and not granted.
14. Mark the report as generated and non-canonical.
15. Record any missing or inconsistent input as a finding and fail if a required section cannot be compiled.
16. Produce the Engineering Recommendation Report.
17. Add the task result to the parent execution trace.

The task must not:

* perform new reasoning
* introduce new alternatives, forces, trade-offs, risks, or evidence
* change the recommendation outcome or selection
* recompute or average confidence
* validate the report against the contract, which is the responsibility of `TASK-VALIDATE-0001`
* approve the report

---

# Primary Output

The primary output is an Engineering Recommendation Report.

Recommended path:

```text
runtime/runs/<RUN_ID>/reports/recommendation-report.md
```

The report is a Markdown document conforming to the report contract. It records its own metadata header, for example:

```yaml
---
report_id: ERR-0001
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
engineering_question: >
  Should Repository Integration become a first-class subsystem
  within Context Switcher?
generated: true
canonical: false
approval_status: pending_human_approval
source_outputs:
  - engineering-reasoning-context.yaml
  - engineering-forces.yaml
  - decision-options.yaml
  - engineering-alternatives.yaml
  - engineering-trade-offs.yaml
  - engineering-risks.yaml
  - missing-information.yaml
  - engineering-confidence.yaml
  - engineering-recommendation.yaml
contract: artifacts/ENGINEERING_RECOMMENDATION_REPORT_CONTRACT.md
---
```

The document body then contains the eleven required sections in order.

The output is:

* generated
* runtime
* non-canonical
* pending human approval
* read-only for downstream tasks
* consumed by the validation and traceability tasks

---

# Secondary Outputs

The task may produce:

* compilation findings
* missing-section findings
* input-inconsistency findings
* trace fragments
* recovery recommendations

Secondary outputs must not replace the Engineering Recommendation Report.

---

# Validation

This task performs only self-checks sufficient to produce a well-formed document. Contract validation is performed by `TASK-VALIDATE-0001`.

The task passes its own self-check only when:

* the report metadata header is present and well-formed
* every required section is present
* every section is compiled from its mapped source
* the recommendation matches the Engineering Recommendation exactly
* all five confidence dimensions and the Overall Confidence narrative are present
* missing information is grouped by classification
* the report is marked generated, non-canonical, and pending human approval
* no section contains content without a source
* the task status is recorded
* the result is added to the parent execution trace

The self-check must not silently repair a missing input; it must produce a finding and fail if a required section cannot be compiled.

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* every required section is compiled from reasoning outputs
* the recommendation and confidence are presented faithfully
* the report is marked generated and pending human approval
* the self-check passes
* the Engineering Recommendation Report is available to the validation task
* the task result is recorded in the execution trace

---

# Failure Conditions

The task must fail when:

* any required reasoning output is missing
* the engineering question is inconsistent across inputs
* more than one primary recommendation is present in the input
* a required report section has no source content
* the report contract cannot be satisfied by compilation alone
* producing a section would require new reasoning

The task must fail rather than invent content to complete a section.

---

# Failure Output

```yaml
task_id: TASK-PRODUCE-0001
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: report_inputs_incomplete
  description: >
    The Engineering Confidence Assessment is missing, so the required
    Confidence section cannot be compiled without new reasoning.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-confidence.yaml
  partial_output_available: false
  recovery_action: >
    Complete the confidence assessment, then regenerate the report.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent Run ID
* input sources consumed
* report contract used
* sections compiled and their sources
* recommendation as presented
* confidence dimensions presented
* self-check result
* findings
* output location
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace must explain the observable compilation without exposing private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly with the same reasoning outputs, report contract, EKB version, and ECF version should produce a materially equivalent Engineering Recommendation Report.

---

# Determinism

Expected level:

```text
Constrained
```

Wording may differ in narrative passages, but the following must remain materially consistent:

* set of sections present
* recommendation outcome and selection
* confidence dimensions and Overall Confidence narrative substance
* missing information classifications
* generated and non-canonical status
* approval status

Because the report compiles fixed inputs, any material difference in the recommendation or confidence between reruns indicates an upstream inconsistency and must be investigated.

---

# Executor Requirements

The executor requires:

* read access to all prior runtime reasoning outputs
* read access to bundled ECF, including the report contract and Confidence Model
* read access to bundled EKB for knowledge references
* permission to write the runtime report
* permission to update runtime trace data

No network access is required.

---

# Permission Boundaries

Allowed:

* read prior runtime outputs
* read bundled ECF and the report contract
* read bundled EKB
* write the Engineering Recommendation Report
* write findings
* update runtime trace data

Prohibited:

* modify canonical project artifacts
* modify bundled dependencies
* perform new reasoning
* introduce new alternatives, evidence, or conclusions
* change the recommendation
* recompute or average confidence
* validate the report against the contract
* approve the report
* execute production code
* access external sources without authorization

---

# Security and Privacy

The task must:

* reference sensitive evidence rather than reproducing it unnecessarily
* avoid recording secrets or credentials
* avoid unnecessary personal information
* preserve repository boundaries
* mark the report as non-canonical to prevent accidental promotion

---

# Accessibility

The report must:

* use explicit section headings in the contract order
* present confidence dimensions as labeled text, not color or icons alone
* provide text descriptions for any embedded diagrams
* remain understandable when read linearly
* expand uncommon abbreviations
* clearly state that human approval is required and not granted

---

# Metrics

Recommended metrics:

* report-generation success rate
* contract-section completeness
* source-traceability rate
* self-check pass rate
* downstream validation pass rate
* human correction rate

Metrics exist to improve report quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Repository Integration Boundary

Given valid reasoning outputs and exactly one primary recommendation for:

```text
Should Repository Integration become a first-class subsystem?
```

when `TASK-PRODUCE-0001` executes,

then it must produce a report containing all eleven contract sections compiled from the reasoning outputs, with the recommendation and all five confidence dimensions presented faithfully.

## Scenario 2 — No New Reasoning

Given a completed report,

when the output is inspected,

then every section must trace to a reasoning output and no new alternative, force, trade-off, risk, or evidence may appear.

## Scenario 3 — Missing Input

Given an absent Engineering Confidence Assessment,

when the task executes,

then it must fail with:

```text
report_inputs_incomplete
```

## Scenario 4 — Approval Boundary

Given a completed report,

when the output is inspected,

then it must be marked pending human approval and must state that the report recommends and the human decides.

## Scenario 5 — Confidence Fidelity

Given the Engineering Confidence Assessment,

when the report is generated,

then the Confidence section must present all five dimensions and the Overall Confidence narrative without averaging.

---

# Guiding Principle

Compile the reasoning into a faithful, contract-conformant report.

Present what was reasoned; do not reason anew, and do not approve.
