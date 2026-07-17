---

task_id: TASK-DECIDE-0001
name: Assess Engineering Confidence
version: 0.1.0
status: draft
category: decision_support
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Assess engineering confidence across the dimensions defined by the Confidence Model.

This task produces a multidimensional confidence assessment that later informs the Engineering Recommendation and the Engineering Recommendation Report.

Because a recommendation does not yet exist when this task runs, it assesses confidence in the currently supportable recommendation direction implied by the forces, trade-offs, risks, and missing information, and it explicitly marks any dimension that remains provisional.

It consumes the prior reasoning outputs and produces one Engineering Confidence Assessment.

The task does not select an alternative, generate a recommendation, average confidence into a single score, or approve engineering work.

---

# Core Principle

Confidence is multidimensional and must always answer the question:

> Confidence in what?

A single confidence score is insufficient.

Overall Confidence must summarize the engineering situation in narrative form and must never be computed as an average of the individual dimensions.

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

## Required Input: Parent Execution Run

A valid reasoning Run ID conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

---

# Preconditions

Execution may begin only when:

* `TASK-ANALYZE-0001` through `TASK-ANALYZE-0007` completed successfully
* every consumed output validates
* the engineering question is identical across all inputs
* the Missing Information Assessment records whether any blocker exists
* the parent reasoning Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task must conform to:

```text
knowledge/CONFIDENCE_MODEL.md
```

It may also use:

* the primary Decision Guide confidence guidance
* relevant Quality Attributes
* relevant Examples

For the reference architecture scenario, relevant knowledge may include:

```text
DG-ARCH-0001
QA-0001
QA-0002
EX-ARCH-0001
```

The confidence dimensions and their meaning are defined by the Confidence Model and must not be redefined by this task.

---

# Confidence Dimensions

The task must assess the following dimensions separately, each with a level and a justification.

Allowed levels:

```text
high
medium
low
unknown
```

## Recommendation Confidence

How confident are we that the currently supportable recommendation direction is the best engineering direction?

Because no recommendation artifact exists yet, this dimension assesses the direction most supported by the forces and trade-offs, and must be marked provisional.

## Evidence Confidence

How complete and trustworthy is the available engineering evidence, considering the Missing Information Assessment and evidence-strength ratings?

## Context Confidence

How well is the engineering context understood, considering project maturity, constraints, and open questions?

## Reversibility Confidence

If the supportable direction proves incorrect, how easily can it be reversed, considering the reversibility forces and risks?

## Implementation Confidence

Assuming approval, how confident are we that implementation would succeed, considering complexity, dependencies, and production prerequisites?

## Overall Confidence

A narrative summary that explains how the individual dimensions interact.

Overall Confidence must not be an average and must not be reduced to a single level in place of the narrative.

---

# Provisional Dimensions

Because this task runs before a recommendation exists, every dimension that depends on a specific chosen alternative must be marked:

```text
provisional: true
```

A provisional dimension is a genuine assessment of the currently supportable direction, subject to revision once the recommendation is generated.

The task must identify which dimensions are provisional and why.

---

# Execution Rules

1. Read all prior reasoning outputs.
2. Confirm the exact engineering question.
3. Identify the currently supportable recommendation direction from the forces and trade-offs without selecting a final alternative.
4. Assess Recommendation Confidence in that direction and mark it provisional.
5. Assess Evidence Confidence using evidence-strength ratings and the Missing Information Assessment.
6. Assess Context Confidence using project maturity, constraints, and open questions.
7. Assess Reversibility Confidence using reversibility forces and risks.
8. Assess Implementation Confidence using complexity, dependencies, and production prerequisites.
9. Provide a justification and cited evidence for each dimension.
10. Mark each dimension provisional where it depends on a not-yet-selected alternative.
11. Write the Overall Confidence narrative that explains how the dimensions interact.
12. Do not average or numerically combine the dimensions.
13. Record contradictions or missing provenance as findings.
14. Produce the Engineering Confidence Assessment.
15. Validate the output.
16. Add the task result to the parent execution trace.

The task must not:

* select an alternative or generate a recommendation
* approve engineering work
* compute Overall Confidence as an average or single aggregate score
* introduce new evidence not present in prior outputs
* hide provisional status

---

# Primary Output

The primary output is an Engineering Confidence Assessment.

Recommended path:

```text
runtime/runs/<RUN_ID>/task_outputs/engineering-confidence.yaml
```

Example:

```yaml
task_id: TASK-DECIDE-0001
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: completed

engineering_question: >
  Should Repository Integration become a first-class subsystem
  within Context Switcher?

supportable_direction:
  description: >
    Defer the first-class subsystem boundary and keep repository concerns
    within the existing Integration boundary while scope is unresolved.
  basis:
    - FORCE-0003
    - AXIS-0004
    - MISS-0001
  note: >
    This is the direction most supported by current evidence; it is not a
    recommendation.

confidence:
  recommendation_confidence:
    level: medium
    provisional: true
    justification: >
      The deferral direction is well supported by the unresolved-scope force
      and reversibility trade-off, but no alternative has been formally
      selected.
    evidence:
      - FORCE-0003
      - AXIS-0004

  evidence_confidence:
    level: low
    provisional: false
    justification: >
      No implementation exists and a blocking scope question remains open, so
      supporting evidence is incomplete.
    evidence:
      - MISS-0001
      - MISS-0002

  context_confidence:
    level: medium
    provisional: false
    justification: >
      The architecture style and constraints are documented, but repository
      scope and vocabulary are not yet settled.
    evidence:
      - engineering-reasoning-context.yaml
      - OPENQ-0001

  reversibility_confidence:
    level: high
    provisional: true
    justification: >
      Implementation has not started, so most directions remain reversible;
      committing a first-class boundary now would reduce this.
    evidence:
      - FORCE-0003
      - RISK-0001

  implementation_confidence:
    level: low
    provisional: true
    justification: >
      Interfaces, data contracts, and repository scope are undefined, so
      implementation success cannot yet be judged.
    evidence:
      - MISS-0003
      - RISK-0002

overall_confidence:
  narrative: >
    The supportable direction is to defer the boundary. Reversibility is
    currently high because no implementation exists, and the deferral direction
    is reasonably strong. However, Evidence and Implementation Confidence are
    low because repository scope is unresolved and no contracts exist. Overall,
    the situation supports a provisional, reversible direction rather than a
    firm structural commitment, and confidence should rise once the blocking
    scope question is resolved.
  is_average: false

provisional_dimensions:
  - recommendation_confidence
  - reversibility_confidence
  - implementation_confidence

findings: []

validation:
  result: passed
  dimensions_assessed: 5
  overall_is_narrative: true
  overall_averaged: false
  recommendation_generated: false
```

The output is:

* generated
* runtime
* non-canonical
* read-only for downstream tasks
* consumed by the recommendation, report, and validation tasks

---

# Secondary Outputs

The task may produce:

* provisional-dimension notes
* low-confidence warnings
* missing-evidence findings
* trace fragments
* recovery recommendations

Secondary outputs must not replace the Engineering Confidence Assessment.

---

# Validation

The task passes validation only when:

* the Work Request ID is present
* the Run ID is present
* the engineering question matches all inputs
* all five confidence dimensions are assessed
* each dimension has a level and a justification
* each dimension cites evidence from prior outputs
* provisional dimensions are marked and explained
* Overall Confidence is a narrative, not an average or single aggregate score
* the output declares that Overall Confidence was not averaged
* no alternative is selected
* no recommendation is generated
* task status is recorded
* the result is added to the parent execution trace

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* the supportable direction is identified without selecting a final alternative
* all five dimensions are assessed with justification and evidence
* provisional dimensions are marked
* the Overall Confidence narrative is written
* validation succeeds
* no unhandled blocking finding remains
* the Engineering Confidence Assessment is available to downstream tasks
* the task result is recorded in the execution trace

---

# Failure Conditions

The task must fail when:

* any required prior output is missing
* the engineering question is inconsistent across inputs
* a confidence dimension cannot be assessed without inventing evidence
* the Confidence Model cannot be satisfied
* output validation fails

The task must not substitute a single numeric score for the multidimensional assessment.

---

# Failure Output

```yaml
task_id: TASK-DECIDE-0001
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: confidence_inputs_incomplete
  description: >
    The Missing Information Assessment required to judge Evidence Confidence is
    absent, so a Confidence Model compliant assessment cannot be produced.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/missing-information.yaml
  partial_output_available: false
  recovery_action: >
    Complete the missing-information assessment, then retry confidence
    assessment.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent Run ID
* input sources consumed
* the identified supportable direction and its basis
* each confidence dimension, level, and justification
* provisional dimensions and reasons
* the Overall Confidence narrative
* explicit confirmation that no averaging was used
* findings
* validation result
* output location
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The confidence assessment recorded in the trace must conform to:

```text
knowledge/CONFIDENCE_MODEL.md
```

The trace must explain the observable basis for each confidence judgment without exposing private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly with the same prior reasoning outputs, EKB version, and ECF version should produce a materially equivalent Engineering Confidence Assessment.

---

# Determinism

Expected level:

```text
Constrained
```

Wording may differ, but the following should remain materially consistent:

* the identified supportable direction
* the level assigned to each dimension
* which dimensions are provisional
* the substance of the Overall Confidence narrative
* findings
* validation result

Cross-executor disagreement about a `high` or `low` dimension level must be recorded and reviewed.

---

# Executor Requirements

The executor requires:

* read access to all prior runtime reasoning outputs
* read access to bundled ECF, including the Confidence Model
* read access to bundled EKB
* permission to write runtime task output
* permission to update runtime trace data

No network access is required.

---

# Permission Boundaries

Allowed:

* read prior runtime outputs
* read bundled ECF and the Confidence Model
* read bundled EKB
* write the Engineering Confidence Assessment
* write findings
* update runtime trace data

Prohibited:

* modify canonical project artifacts
* modify bundled dependencies
* select or rank an alternative
* generate a recommendation
* approve engineering work
* compute Overall Confidence as an average
* execute production work
* access external sources without authorization

---

# Security and Privacy

The task must:

* cite sensitive evidence rather than reproducing it
* avoid recording secrets or credentials
* avoid unnecessary personal information
* preserve repository boundaries

---

# Accessibility

Human-readable output must:

* label each confidence dimension explicitly
* express levels and justifications in plain language
* clearly mark provisional dimensions
* avoid color-only meaning
* remain understandable when read linearly
* expand uncommon abbreviations

---

# Metrics

Recommended metrics:

* dimension-completeness rate
* provisional-dimension rate
* averaging-violation rate
* cross-executor level agreement
* confidence-evolution across reruns
* human correction rate

Metrics exist to improve reasoning quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Repository Integration Boundary

Given valid prior reasoning outputs for:

```text
Should Repository Integration become a first-class subsystem?
```

when `TASK-DECIDE-0001` executes,

then the output must assess Recommendation, Evidence, Context, Reversibility, and Implementation Confidence separately, with an Overall Confidence narrative,

and dimensions that depend on a not-yet-selected alternative must be marked provisional.

## Scenario 2 — No Averaging

Given the individual dimension levels,

when the output is inspected,

then Overall Confidence must be a narrative and must not be the average of the dimension levels.

## Scenario 3 — Blocking Gap Lowers Evidence Confidence

Given a blocking missing-information item,

when the task executes,

then Evidence Confidence must not be `high`.

## Scenario 4 — Missing Input

Given an absent Missing Information Assessment,

when the task executes,

then it must fail with:

```text
confidence_inputs_incomplete
```

## Scenario 5 — No Recommendation Leakage

Given a completed confidence assessment,

when the output is inspected,

then it must not select an alternative or state a final recommendation.

---

# Guiding Principle

Communicate engineering uncertainty across every dimension of the Confidence Model.

Assess confidence in the currently supportable direction, mark what is provisional, and never compress the assessment into a single averaged score.
