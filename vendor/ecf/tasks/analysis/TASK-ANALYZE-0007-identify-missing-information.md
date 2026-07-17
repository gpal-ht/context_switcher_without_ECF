---

task_id: TASK-ANALYZE-0007
name: Identify Missing Information
version: 0.1.0
status: draft
category: analysis
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Identify the information that is missing from the current reasoning and classify how that gap affects the engineering decision.

This task consolidates the open questions, assumptions, required evidence, and unresolved uncertainty produced by all prior reasoning tasks, and expresses each gap in terms of when it must be resolved and who is responsible for resolving it.

It consumes all prior reasoning outputs and produces one Missing Information Assessment.

The task does not gather the missing information, recommend an alternative, assess confidence, or approve engineering work.

---

# Core Principle

Not all missing information is equal.

Some gaps must be closed before any recommendation is credible.

Some gaps would improve confidence but are not blocking.

Some gaps only matter before production.

Some gaps are useful future information that does not affect the current decision.

The task must classify each gap precisely so that later tasks and human reviewers understand what is genuinely blocking.

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

## Required Input: Parent Execution Run

A valid reasoning Run ID conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

---

# Preconditions

Execution may begin only when:

* `TASK-ANALYZE-0001` through `TASK-ANALYZE-0006` completed successfully
* every consumed output validates
* the engineering question is identical across all inputs
* assumptions, open questions, and required evidence are readable from the prior outputs
* the parent reasoning Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task may use:

* the primary Decision Guide, especially its confidence guidance and common mistakes
* relevant Examples, especially those describing when to delay a decision
* the Engineering Reasoning Context assumptions and open questions
* the Engineering Risk Analysis registers

For the reference architecture scenario, relevant knowledge may include:

```text
DG-ARCH-0001
EX-ARCH-0001
```

The task must ground each gap in prior outputs and project evidence rather than generic checklists.

---

# Definitions

## Missing Information Item

A specific piece of information that is currently unavailable and that affects reasoning, confidence, or production.

Every item must be concrete enough to be actioned.

## Classification

Every missing information item must be classified as exactly one of:

```text
blocker
confidence_reducer
production_prerequisite
future_information
```

### blocker

Information required before any recommendation can be credibly made.

While a blocker is open, the recommendation should be `defer` or `gather_additional_evidence`.

### confidence_reducer

Information that would improve confidence but does not prevent a provisional recommendation.

### production_prerequisite

Information not required to recommend, but required before implementation may begin.

### future_information

Information that would be useful later and does not affect the current decision.

## Responsible Source or Role

The source, role, or artifact expected to provide the information, where known.

Examples:

```text
product_owner
architecture_review
engineering_context_document
repository_capability_spike
```

When the responsible source is unknown, the item must say so explicitly rather than guessing.

---

# Execution Rules

1. Read all prior reasoning outputs.
2. Confirm the exact engineering question.
3. Collect open questions from the Engineering Reasoning Context.
4. Collect assumptions and their evidence strength from prior outputs.
5. Collect required evidence from the Engineering Alternative Set.
6. Collect `unknown` trade-off effects from the Engineering Trade-off Analysis.
7. Collect risks whose likelihood or impact is `unknown` from the Engineering Risk Analysis.
8. Normalize overlapping gaps into single items without losing provenance.
9. For each gap, determine why the information is needed.
10. Classify each gap as blocker, confidence_reducer, production_prerequisite, or future_information.
11. Record the responsible source or role where known, and mark it unknown otherwise.
12. Record which alternatives, forces, risks, or trade-offs each gap affects.
13. Record how the gap would change reasoning if resolved.
14. Preserve conflicting interpretations rather than resolving them.
15. Record contradictions or missing provenance as findings.
16. Produce the Missing Information Assessment.
17. Validate the output.
18. Add the task result to the parent execution trace.

The task must not:

* attempt to answer the missing questions
* gather external information
* select or rank an alternative
* generate a recommendation
* assess confidence
* approve engineering work

---

# Blocker Discipline

A gap may be classified as a blocker only when a credible recommendation cannot be made while it remains open.

The task must justify every blocker with an explicit reason tied to a force, risk, or trade-off.

Over-classifying gaps as blockers is a defect, because it can stall reasoning unnecessarily.

Under-classifying a genuine blocker is a more serious defect, because it can allow an unsupported recommendation.

---

# Primary Output

The primary output is a Missing Information Assessment.

Recommended path:

```text
runtime/runs/<RUN_ID>/task_outputs/missing-information.yaml
```

Example:

```yaml
task_id: TASK-ANALYZE-0007
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: completed

engineering_question: >
  Should Repository Integration become a first-class subsystem
  within Context Switcher?

missing_information:
  - item_id: MISS-0001
    title: Repository Integration Scope
    classification: blocker
    description: >
      It is not resolved whether repository integration means local Git access,
      GitHub API access, or both.
    why_needed: >
      The subsystem boundary and its vocabulary depend on this scope; a
      credible boundary recommendation cannot be made while it is open.
    affects:
      forces:
        - FORCE-0003
      alternatives:
        - ALT-0001
        - ALT-0003
        - ALT-0004
      risks:
        - RISK-0001
        - RISK-0004
    responsible_source: product_owner
    resolution_effect: >
      Resolving scope would allow the boundary decision to move from defer to a
      concrete direction.
    status: open

  - item_id: MISS-0002
    title: Observed Repository Change Patterns
    classification: confidence_reducer
    description: >
      No implementation exists yet, so repository change frequency and coupling
      cannot be observed.
    why_needed: >
      Observed change patterns would strengthen or weaken the cohesion and
      reversibility forces.
    affects:
      forces:
        - FORCE-0002
      trade_offs:
        - AXIS-0004
    responsible_source: repository_capability_spike
    resolution_effect: >
      Evidence would raise Evidence Confidence but is not required for a
      provisional recommendation.
    status: open

  - item_id: MISS-0003
    title: Repository Data and Event Contract
    classification: production_prerequisite
    description: >
      The interface and event contract between repository connectivity and AI
      evaluation is undefined.
    why_needed: >
      The contract is required before implementation but not before a boundary
      recommendation.
    affects:
      alternatives:
        - ALT-0002
        - ALT-0003
    responsible_source: architecture_review
    resolution_effect: >
      Required before production; does not block the current recommendation.
    status: open

  - item_id: MISS-0004
    title: Long-Term Repository Feature Roadmap
    classification: future_information
    description: >
      The multi-release roadmap for repository features is not defined.
    why_needed: >
      Useful for long-term planning; does not affect the current boundary
      decision.
    affects:
      alternatives:
        - ALT-0001
    responsible_source: unknown
    resolution_effect: >
      Would inform future re-evaluation, not the current decision.
    status: open

summary:
  blocker_count: 1
  confidence_reducer_count: 1
  production_prerequisite_count: 1
  future_information_count: 1
  blocking_present: true

findings: []

validation:
  result: passed
  every_item_classified: true
  every_blocker_justified: true
  recommendation_generated: false
```

The output is:

* generated
* runtime
* non-canonical
* read-only for downstream tasks
* consumed by the confidence, recommendation, report, and validation tasks

---

# Secondary Outputs

The task may produce:

* provenance-gap findings
* conflicting-classification observations
* unknown-responsible-source notes
* trace fragments
* recovery recommendations

Secondary outputs must not replace the Missing Information Assessment.

---

# Validation

The task passes validation only when:

* the Work Request ID is present
* the Run ID is present
* the engineering question matches all inputs
* every missing information item has a unique ID
* every item is classified as exactly one allowed classification
* every blocker includes an explicit justification tied to a force, risk, or trade-off
* every item records what it affects
* every item records a responsible source or explicitly marks it unknown
* overlapping gaps are consolidated without losing provenance
* a summary count is present and includes whether any blocker exists
* no attempt is made to answer the missing questions
* no recommendation is generated
* task status is recorded
* the result is added to the parent execution trace

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* gaps are collected from every prior reasoning output
* every gap is classified and justified
* responsible sources are recorded where known
* the blocking summary is produced
* validation succeeds
* no unhandled blocking finding remains
* the Missing Information Assessment is available to downstream tasks
* the task result is recorded in the execution trace

---

# Failure Conditions

The task must fail when:

* any required prior output is missing
* the engineering question is inconsistent across inputs
* prior outputs cannot be read or reconciled
* gaps cannot be classified without inventing evidence
* output validation fails

The task must not resolve a gap by assuming an answer.

---

# Failure Output

```yaml
task_id: TASK-ANALYZE-0007
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: reasoning_outputs_incomplete
  description: >
    One or more prior reasoning outputs required to assess missing information
    are absent or invalid.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-risks.yaml
  partial_output_available: false
  recovery_action: >
    Complete the prior reasoning tasks and validate their outputs, then retry
    the missing-information assessment.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent Run ID
* input sources consumed
* gaps collected from each source
* consolidation decisions
* classification of each gap
* blocker justifications
* responsible sources recorded or marked unknown
* summary counts
* findings
* validation result
* output location
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace must explain the observable basis for every classification without exposing private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly with the same prior reasoning outputs, EKB version, and ECF version should produce a materially equivalent Missing Information Assessment.

---

# Determinism

Expected level:

```text
Constrained
```

Wording may differ, but the following should remain materially consistent:

* set of missing information items
* classification of each item
* blocker set
* affected forces, risks, alternatives, and trade-offs
* summary counts
* findings
* validation result

Cross-executor disagreement about whether an item is a blocker must be recorded and reviewed.

---

# Executor Requirements

The executor requires:

* read access to all prior runtime reasoning outputs
* read access to cited project artifacts
* read access to bundled ECF
* read access to bundled EKB
* permission to write runtime task output
* permission to update runtime trace data

No network access is required.

---

# Permission Boundaries

Allowed:

* read prior runtime outputs
* read cited project documentation
* read bundled ECF
* read bundled EKB
* write the Missing Information Assessment
* write findings
* update runtime trace data

Prohibited:

* modify canonical project artifacts
* modify bundled dependencies
* gather or fabricate the missing information
* select or rank an alternative
* generate a recommendation
* assess confidence
* approve engineering work
* execute production work
* access external sources without authorization

---

# Security and Privacy

The task must:

* reference sensitive gaps without reproducing sensitive content
* avoid recording secrets or credentials
* avoid unnecessary personal information
* preserve repository boundaries

---

# Accessibility

Human-readable output must:

* use explicit item titles
* group items by classification
* explain why each gap matters in plain language
* avoid color-only meaning
* remain understandable when read linearly
* expand uncommon abbreviations

---

# Metrics

Recommended metrics:

* missing-information completeness rate
* blocker precision
* blocker recall
* consolidation accuracy
* unknown-responsible-source rate
* cross-executor classification agreement
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

when `TASK-ANALYZE-0007` executes,

then the output must identify unresolved repository scope as a blocker and classify other gaps as confidence reducers, production prerequisites, or future information.

## Scenario 2 — Missing Prior Output

Given an absent Engineering Risk Analysis,

when the task executes,

then it must fail with:

```text
reasoning_outputs_incomplete
```

## Scenario 3 — Blocker Justification

Given a gap classified as a blocker,

when the output is inspected,

then the blocker must include an explicit justification tied to a force, risk, or trade-off.

## Scenario 4 — No Answering

Given an open question about repository scope,

when the task executes,

then the task must record the gap and must not supply an assumed answer.

## Scenario 5 — Consolidation

Given the same gap expressed in two prior outputs,

when the task executes,

then the gap must appear once with provenance to both sources.

---

# Guiding Principle

Make the gaps in current knowledge explicit and classify how each one affects the decision.

Say what is missing and when it must be resolved; do not resolve it and do not decide.
