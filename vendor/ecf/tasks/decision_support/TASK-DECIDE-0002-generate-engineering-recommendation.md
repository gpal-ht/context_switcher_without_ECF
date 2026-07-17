---

task_id: TASK-DECIDE-0002
name: Generate Engineering Recommendation
version: 0.1.0
status: draft
category: decision_support
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Produce exactly one primary engineering recommendation from the completed reasoning outputs.

This task selects a Decision Option and, where applicable, an Engineering Alternative, and explains the decisive reasoning that supports the chosen outcome.

It consumes every reasoning output and produces one Engineering Recommendation.

The task does not create new evidence, generate new alternatives, produce the human-readable report, or approve the recommendation. Human approval remains the final authority.

---

# Core Principle

A recommendation is a reasoned selection, not a new act of discovery.

Every element of the recommendation must be traceable to an already produced reasoning output.

The recommendation recommends; the human decides.

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

## Required Input: Parent Execution Run

A valid reasoning Run ID conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

---

# Preconditions

Execution may begin only when:

* `TASK-ANALYZE-0001` through `TASK-ANALYZE-0007` completed successfully
* `TASK-DECIDE-0001` completed successfully
* every consumed output validates
* the engineering question is identical across all inputs
* the Decision Option Set contains at least two viable options
* the Engineering Alternative Set contains at least one viable or experimental alternative
* the Missing Information Assessment records whether any blocker exists
* the parent reasoning Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task may use:

* the primary Decision Guide, including its recommendation and confidence guidance
* the Engineering Forces Analysis
* the Engineering Trade-off Analysis
* the Engineering Risk Analysis
* the Missing Information Assessment
* the Engineering Confidence Assessment

For the reference architecture scenario, relevant knowledge may include:

```text
DG-ARCH-0001
EX-ARCH-0001
```

The recommendation must be grounded in these outputs and must not introduce engineering knowledge that was not retrieved.

---

# Definitions

## Recommendation Outcome

The overall engineering direction recommended for the decision.

Allowed outcomes:

```text
proceed
proceed_with_conditions
defer
reject
gather_additional_evidence
```

### proceed

Adopt the selected Decision Option and Alternative now.

### proceed_with_conditions

Adopt the selected direction only when stated conditions are satisfied.

### defer

Postpone the decision because a blocking gap prevents a credible commitment.

### reject

Recommend against the proposed direction.

### gather_additional_evidence

Recommend a bounded evidence-gathering effort before deciding.

## Blocking-Gap Rule

When the Missing Information Assessment records an open blocker, the recommendation outcome must be `defer` or `gather_additional_evidence`, and the task must not recommend `proceed`.

---

# Execution Rules

1. Read every reasoning output.
2. Confirm the exact engineering question.
3. Confirm whether any open blocker exists in the Missing Information Assessment.
4. Identify the Decision Option best supported by the forces and trade-offs.
5. Where applicable, select the Engineering Alternative that realizes that option.
6. If an open blocker exists, constrain the outcome to `defer` or `gather_additional_evidence`.
7. Determine the single recommendation outcome.
8. Record the decisive forces that drove the outcome, citing the Forces Analysis.
9. Record the decisive trade-offs, citing the Trade-off Analysis.
10. Record the decisive risks, citing the Risk Analysis.
11. Record the alternatives not selected and why, without re-deriving trade-offs.
12. Record assumptions carried into the recommendation.
13. Record conditions that must hold for `proceed_with_conditions`.
14. Record unresolved information referencing the Missing Information Assessment.
15. Reference the Engineering Confidence Assessment rather than recomputing confidence.
16. Record that human approval is required and not granted.
17. Ensure exactly one primary recommendation is produced.
18. Record contradictions as findings.
19. Produce the Engineering Recommendation.
20. Validate the output.
21. Add the task result to the parent execution trace.

The task must not:

* create new evidence, forces, alternatives, trade-offs, or risks
* recompute or override the Confidence Assessment
* produce more than one primary recommendation
* approve the recommendation
* modify canonical artifacts
* produce the human-readable report

---

# Primary Output

The primary output is an Engineering Recommendation.

Recommended path:

```text
runtime/runs/<RUN_ID>/task_outputs/engineering-recommendation.yaml
```

Example:

```yaml
task_id: TASK-DECIDE-0002
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: completed

engineering_question: >
  Should Repository Integration become a first-class subsystem
  within Context Switcher?

recommendation:
  outcome: gather_additional_evidence
  selected_decision_option: OPT-0004
  selected_alternative: ALT-0004
  one_primary_recommendation: true

  statement: >
    Do not introduce a first-class Repository Integration subsystem yet.
    Run a bounded repository capability spike to resolve scope and vocabulary,
    and keep repository concerns within the existing Integration boundary until
    the evidence supports a boundary change.

  alternatives_not_selected:
    - alternative_id: ALT-0001
      reason: >
        Commits to a boundary before scope is understood; high reversibility
        risk while implementation has not started.
      references:
        - RISK-0001
        - AXIS-0004
    - alternative_id: ALT-0002
      reason: >
        Viable but premature to finalize before scope is resolved.
      references:
        - MISS-0001
    - alternative_id: ALT-0003
      reason: >
        Reasonable fallback; retained as the interim structure during the
        spike rather than a final commitment.
      references:
        - AXIS-0002

  decisive_forces:
    - FORCE-0003
    - FORCE-0004

  decisive_trade_offs:
    - AXIS-0004
    - AXIS-0002

  decisive_risks:
    - RISK-0001
    - RISK-0004

  assumptions:
    - id: ASSUME-0001
      statement: >
        Repository capability will expand materially beyond a small adapter.
      evidence_strength: weak

  conditions: []

  unresolved_information:
    - MISS-0001
    - MISS-0002

  confidence_reference:
    source: runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-confidence.yaml
    overall_summary: >
      Reversible direction with low evidence confidence; confidence should rise
      once scope is resolved.

  human_approval:
    required: true
    granted: false
    approver_role: human_engineer

findings: []

validation:
  result: passed
  single_primary_recommendation: true
  blocking_gap_respected: true
  new_evidence_created: false
  approval_claimed: false
```

The output is:

* generated
* runtime
* non-canonical
* read-only for downstream tasks
* consumed by the report-generation, validation, and traceability tasks

---

# Secondary Outputs

The task may produce:

* condition definitions for `proceed_with_conditions`
* contradiction findings
* unresolved-information references
* trace fragments
* recovery recommendations

Secondary outputs must not replace the Engineering Recommendation.

---

# Validation

The task passes validation only when:

* the Work Request ID is present
* the Run ID is present
* the engineering question matches all inputs
* exactly one primary recommendation exists
* the outcome is an allowed value
* a Decision Option is selected
* an Engineering Alternative is selected when the outcome requires one
* alternatives not selected are recorded with reasons
* decisive forces, trade-offs, and risks cite prior outputs
* assumptions are recorded and distinguished from evidence
* conditions are recorded when the outcome is `proceed_with_conditions`
* unresolved information references the Missing Information Assessment
* the Confidence Assessment is referenced, not recomputed
* the blocking-gap rule is respected
* no new evidence, forces, alternatives, trade-offs, or risks were created
* human approval is marked required and not granted
* task status is recorded
* the result is added to the parent execution trace

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* one primary recommendation is produced
* the selection is fully traceable to prior outputs
* the blocking-gap rule is honored
* human approval is marked required and not granted
* validation succeeds
* no unhandled blocking finding remains
* the Engineering Recommendation is available to downstream tasks
* the task result is recorded in the execution trace

---

# Failure Conditions

The task must fail when:

* any required prior output is missing
* the engineering question is inconsistent across inputs
* no viable Decision Option or Alternative exists to select
* the reasoning outputs contradict one another and cannot be reconciled
* a single primary recommendation cannot be produced
* producing a recommendation would require creating new evidence
* output validation fails

The task must not resolve missing evidence by inventing facts.

---

# Failure Output

```yaml
task_id: TASK-DECIDE-0002
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: recommendation_not_derivable
  description: >
    The reasoning outputs do not support a single primary recommendation
    without creating new evidence.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-trade-offs.yaml
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/missing-information.yaml
  partial_output_available: false
  recovery_action: >
    Revisit the trade-off and missing-information analyses, or expand project
    evidence, then retry recommendation generation.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent Run ID
* input sources consumed
* whether an open blocker existed
* the selected Decision Option and Alternative
* the recommendation outcome
* decisive forces, trade-offs, and risks
* alternatives not selected and reasons
* assumptions
* conditions
* unresolved information
* confidence reference
* human-approval status
* findings
* validation result
* output location
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace must explain the observable basis for the recommendation without exposing private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly with the same reasoning outputs, EKB version, and ECF version should produce a materially equivalent Engineering Recommendation with the same outcome and selection.

---

# Determinism

Expected level:

```text
Constrained
```

Wording may differ, but the following should remain materially consistent:

* recommendation outcome
* selected Decision Option and Alternative
* decisive forces, trade-offs, and risks
* alternatives not selected
* conditions and unresolved information
* human-approval status
* validation result

Cross-executor disagreement about the recommendation outcome must be recorded and reviewed.

---

# Executor Requirements

The executor requires:

* read access to all prior runtime reasoning outputs
* read access to bundled ECF, including the Confidence Model and Reasoning Engine
* read access to bundled EKB
* permission to write runtime task output
* permission to update runtime trace data

No network access is required.

---

# Permission Boundaries

Allowed:

* read prior runtime outputs
* read bundled ECF
* read bundled EKB
* write the Engineering Recommendation
* write findings
* update runtime trace data

Prohibited:

* modify canonical project artifacts
* modify bundled dependencies
* create new evidence, forces, alternatives, trade-offs, or risks
* recompute or override the Confidence Assessment
* produce more than one primary recommendation
* approve the recommendation
* produce the human-readable report
* execute production work
* access external sources without authorization

---

# Security and Privacy

The task must:

* reference sensitive evidence rather than reproducing it
* avoid recording secrets or credentials
* avoid unnecessary personal information
* preserve repository boundaries

---

# Accessibility

Human-readable output must:

* state the recommendation in plain language
* clearly separate the outcome, selection, and conditions
* make the human-approval requirement explicit
* avoid color-only meaning
* remain understandable when read linearly
* expand uncommon abbreviations

---

# Metrics

Recommended metrics:

* recommendation-generation success rate
* single-recommendation compliance rate
* blocking-gap compliance rate
* traceability completeness
* cross-executor outcome agreement
* human override rate

Metrics exist to improve reasoning quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Repository Integration Boundary

Given valid prior reasoning outputs for:

```text
Should Repository Integration become a first-class subsystem?
```

with an open blocking scope gap,

when `TASK-DECIDE-0002` executes,

then the recommendation outcome must be `defer` or `gather_additional_evidence`, exactly one primary recommendation must be produced, and human approval must be marked required and not granted.

## Scenario 2 — Blocking Gap Prevents Proceed

Given an open blocker in the Missing Information Assessment,

when the task executes,

then the outcome must not be `proceed`.

## Scenario 3 — No New Evidence

Given a completed recommendation,

when the output is inspected,

then every decisive force, trade-off, and risk must reference a prior output, and no new evidence may be introduced.

## Scenario 4 — Single Recommendation

Given several viable alternatives,

when the task executes,

then exactly one primary recommendation must be produced, with the others listed as alternatives not selected.

## Scenario 5 — No Approval

Given a completed recommendation,

when the output is inspected,

then it must not claim or grant human approval.

---

# Guiding Principle

Select one engineering direction and explain the decisive reasoning behind it, drawing only on what the reasoning tasks already produced.

The recommendation recommends. The human decides.
