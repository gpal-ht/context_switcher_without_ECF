---

task_id: TASK-ANALYZE-0006
name: Identify Engineering Risks
version: 0.1.0
status: draft
category: analysis
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Identify the engineering risks associated with the viable alternatives and their trade-offs.

This task separates genuine risk from other kinds of uncertainty and consequence, so that later confidence assessment and recommendation generation reason about accurate risk information.

It consumes the Engineering Reasoning Context, the Engineering Alternative Set, and the Engineering Trade-off Analysis, and produces one Engineering Risk Analysis.

The task does not rank alternatives, select a preferred alternative, generate a recommendation, or approve engineering work.

---

# Core Principle

A risk is a possible future negative outcome whose occurrence is uncertain.

A risk is not the same as an assumption, an open question, a constraint, or a known consequence.

The task must classify each item precisely and must not fabricate probabilities or numeric risk scores that the available evidence does not support.

---

# Inputs

## Required Input: Engineering Reasoning Context

Produced by:

```text
TASK-ANALYZE-0001
Build Engineering Reasoning Context
```

Provides the engineering question, project facts, constraints, assumptions, and open questions.

## Required Input: Engineering Alternative Set

Produced by:

```text
TASK-ANALYZE-0004
Generate Engineering Alternatives
```

Provides the viable alternatives, their assumptions, and their required evidence.

## Required Input: Engineering Trade-off Analysis

Produced by:

```text
TASK-ANALYZE-0005
Analyze Engineering Trade-offs
```

Provides the comparison axes, relative effects, and identified tensions.

## Required Input: Parent Execution Run

A valid reasoning Run ID conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

---

# Preconditions

Execution may begin only when:

* `TASK-ANALYZE-0001` completed successfully
* `TASK-ANALYZE-0004` completed successfully
* `TASK-ANALYZE-0005` completed successfully
* the Engineering Reasoning Context validates
* the Engineering Alternative Set validates
* the Engineering Trade-off Analysis validates
* the engineering question is identical across all inputs
* no blocking inherited finding prevents risk analysis
* the parent reasoning Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task may use:

* the primary Decision Guide referenced by the Engineering Reasoning Context
* related Quality Attributes, especially those describing complexity and maintainability
* related Concepts and Patterns
* relevant Examples
* the Engineering Trade-off Analysis and Engineering Forces Analysis

For the reference architecture scenario, relevant knowledge may include:

```text
DG-ARCH-0001
CON-ARCH-0001
CON-ARCH-0002
QA-0001
QA-0002
EX-ARCH-0001
```

The task must ground risks in retrieved knowledge and project evidence rather than generic risk catalogs.

---

# Definitions

The task must distinguish the following item types and must not merge them.

## Risk

A possible future negative outcome that is uncertain.

Example:

```text
If the repository boundary is fixed now, later scope changes may force an
expensive migration.
```

## Assumption

A statement currently treated as true without full evidence.

Example:

```text
Repository capability will expand materially beyond a small adapter.
```

## Open Question

An unresolved question whose answer would change the analysis.

Example:

```text
Does repository integration mean local Git access, GitHub API access, or both?
```

## Constraint

A fixed condition that limits acceptable outcomes.

Example:

```text
The system must remain a modular monolith.
```

## Known Consequence

A predictable and effectively certain outcome of an alternative, not an uncertain event.

Example:

```text
Introducing a subsystem adds a new set of interface contracts.
```

A known consequence belongs in the Trade-off Analysis, not in the risk register, unless it also creates a distinct uncertain outcome.

---

# Risk Attributes

Every risk must declare:

* Risk ID
* Title
* Related alternative or alternatives
* Category
* Likelihood qualifier
* Impact qualifier
* Evidence
* Assumptions
* Detectability or early-warning signal, where known
* Candidate mitigation direction, where known
* Status

## Category

Allowed values:

```text
architectural
scope
complexity
maintainability
reversibility
delivery
operational
security
knowledge
governance
```

## Likelihood Qualifier

Allowed values:

```text
likely
possible
unlikely
unknown
```

Likelihood must be a qualitative judgment supported by evidence.

The task must not assign a numeric probability unless the project provides evidence that justifies it.

## Impact Qualifier

Allowed values:

```text
severe
moderate
minor
unknown
```

Impact must describe the engineering consequence, not a computed score.

The task must not multiply likelihood and impact into a numeric risk score without evidence-based inputs.

---

# Execution Rules

1. Read the Engineering Reasoning Context.
2. Confirm the exact engineering question.
3. Read the Engineering Alternative Set.
4. Read the Engineering Trade-off Analysis.
5. Extract candidate uncertain outcomes from unfavorable and strongly unfavorable trade-off effects.
6. Extract candidate uncertain outcomes from alternative assumptions and required evidence.
7. For each candidate, classify it as risk, assumption, open question, constraint, or known consequence.
8. Retain only true risks in the risk register.
9. Record assumptions, open questions, constraints, and known consequences in their separate registers.
10. Assign each risk a category, likelihood qualifier, and impact qualifier.
11. Cite the trade-off effect, force, or project evidence supporting each risk.
12. Record a detectability signal where one is observable.
13. Record a candidate mitigation direction only when it is evident from project context; do not design solutions.
14. Associate each risk with the alternatives it affects.
15. Record risks that apply to all alternatives as shared risks.
16. Record contradictions or missing evidence as findings.
17. Produce the Engineering Risk Analysis.
18. Validate the output.
19. Add the task result to the parent execution trace.

The task must not:

* rank alternatives by aggregate risk
* select a least-risky alternative as a recommendation
* fabricate probabilities or numeric risk scores
* invent risks unsupported by evidence
* design mitigations or produce implementation plans
* estimate confidence
* approve engineering work

---

# Separation Requirement

The output must keep the five item types in distinct sections.

An item must not appear as both a risk and an assumption.

When an item could be read two ways, the task must record the chosen classification and a short justification.

---

# Primary Output

The primary output is an Engineering Risk Analysis.

Recommended path:

```text
runtime/runs/<RUN_ID>/task_outputs/engineering-risks.yaml
```

Example:

```yaml
task_id: TASK-ANALYZE-0006
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: completed

engineering_question: >
  Should Repository Integration become a first-class subsystem
  within Context Switcher?

risks:
  - risk_id: RISK-0001
    title: Premature Boundary Migration
    related_alternatives:
      - ALT-0001
    category: reversibility
    likelihood: possible
    impact: severe
    description: >
      If a first-class subsystem boundary is committed before repository scope
      is understood, later scope changes may require an expensive migration of
      dependent subsystems.
    evidence:
      - AXIS-0004
      - FORCE-0003
      - DG-ARCH-0001
    assumptions: []
    early_warning_signal: >
      Repository scope changes materially after the boundary is fixed.
    candidate_mitigation_direction: >
      Defer the boundary or keep it internal until scope stabilizes.
    status: open

  - risk_id: RISK-0002
    title: Integration Complexity Growth
    related_alternatives:
      - ALT-0003
    category: complexity
    likelihood: possible
    impact: moderate
    description: >
      Repository concerns implemented inside Integration may increase its
      complexity as capability grows.
    evidence:
      - AXIS-0002
      - QA-0002
    assumptions:
      - repository_capability_will_expand_materially
    early_warning_signal: >
      Integration change frequency and defect rate rise as repository features
      are added.
    candidate_mitigation_direction: >
      Maintain a clear internal repository boundary that supports later
      extraction.
    status: open

  - risk_id: RISK-0003
    title: Spike Output Treated as Production Architecture
    related_alternatives:
      - ALT-0004
    category: governance
    likelihood: unlikely
    impact: moderate
    description: >
      A deferral spike may be promoted into production architecture without
      the required human review.
    evidence:
      - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-alternatives.yaml
    assumptions: []
    early_warning_signal: >
      Spike code appears in canonical architecture without an approval record.
    candidate_mitigation_direction: >
      Enforce the existing human-approval boundary before promotion.
    status: open

shared_risks:
  - RISK-0004

shared_risk_details:
  - risk_id: RISK-0004
    title: Unresolved Repository Scope
    category: scope
    likelihood: likely
    impact: moderate
    description: >
      Every alternative is affected by the unresolved question of whether
      repository integration means local Git, GitHub API, or both.
    evidence:
      - FORCE-0003
    assumptions: []
    status: open

assumptions_register:
  - id: ASSUME-0001
    statement: >
      Repository capability will expand materially beyond a small adapter.
    source: ALT-0001
    evidence_strength: weak

open_questions_register:
  - id: OPENQ-0001
    statement: >
      Does repository integration mean local Git access, GitHub API access,
      or both?
    source: engineering-reasoning-context.yaml

constraints_register:
  - id: CONST-0001
    statement: The system must remain a modular monolith.
    source: engineering-reasoning-context.yaml

known_consequences_register:
  - id: CONSEQ-0001
    statement: >
      Introducing a subsystem adds new interface and event contracts.
    related_alternatives:
      - ALT-0001
    source: AXIS-0002

findings: []

validation:
  result: passed
  risk_count: 4
  numeric_scores_used: false
  item_types_separated: true
  recommendation_generated: false
```

The output is:

* generated
* runtime
* non-canonical
* read-only for downstream tasks
* consumed by the missing-information, confidence, and recommendation tasks

---

# Secondary Outputs

The task may produce:

* misclassification-correction notes
* missing-evidence findings
* unsupported-risk warnings
* shared-risk observations
* trace fragments
* recovery recommendations

Secondary outputs must not replace the Engineering Risk Analysis.

---

# Validation

The task passes validation only when:

* the Work Request ID is present
* the Run ID is present
* the engineering question matches all inputs
* every risk has a unique Risk ID
* every risk is a genuine uncertain outcome, not an assumption, open question, constraint, or known consequence
* the five item types appear in separate registers
* every risk has a category, likelihood qualifier, and impact qualifier
* no numeric probability or numeric risk score is present unless justified by cited evidence
* every risk cites a trade-off effect, force, or project evidence
* assumptions remain separate from risks
* shared risks are identified where applicable
* no alternative is ranked by aggregate risk
* no recommendation is generated
* task status is recorded
* the result is added to the parent execution trace

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* candidate uncertain outcomes are extracted and classified
* genuine risks are separated from other item types
* each risk carries category, likelihood, impact, and provenance
* shared risks are identified
* validation succeeds
* no unhandled blocking finding remains
* the Engineering Risk Analysis is available to downstream tasks
* the task result is recorded in the execution trace

---

# Failure Conditions

The task must fail when:

* any required input is missing
* the engineering question is inconsistent across inputs
* the alternatives or trade-offs cannot be interpreted
* no item can be classified without inventing evidence
* output validation fails

The task must not invent risks or probabilities to produce a non-empty register.

---

# Failure Output

```yaml
task_id: TASK-ANALYZE-0006
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: risk_analysis_inputs_inconsistent
  description: >
    The Engineering Trade-off Analysis and Engineering Alternative Set describe
    different alternatives, so risks cannot be attributed reliably.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-trade-offs.yaml
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-alternatives.yaml
  partial_output_available: false
  recovery_action: >
    Re-run the trade-off analysis against the current Alternative Set, then
    retry risk identification.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent Run ID
* input sources consumed
* candidate uncertain outcomes considered
* classification of each candidate
* risks retained
* items reclassified as assumption, open question, constraint, or known consequence
* likelihood and impact qualifiers and their basis
* shared risks
* assumptions
* findings
* validation result
* output location
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace must explain the observable basis for each risk without exposing private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly with the same:

* Engineering Reasoning Context
* Engineering Alternative Set
* Engineering Trade-off Analysis
* EKB version
* ECF version

should produce a materially equivalent Engineering Risk Analysis.

---

# Determinism

Expected level:

```text
Constrained
```

Wording may differ, but the following should remain materially consistent:

* identified risks
* risk classification versus other item types
* categories
* likelihood and impact qualifiers
* shared risks
* assumptions
* findings
* validation result

Cross-executor disagreement about a `severe` impact risk must be recorded and reviewed.

---

# Executor Requirements

The executor requires:

* read access to prior runtime reasoning outputs
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
* write the Engineering Risk Analysis
* write findings
* update runtime trace data

Prohibited:

* modify canonical project artifacts
* modify bundled dependencies
* rank alternatives by risk
* select a least-risky alternative as a recommendation
* fabricate probabilities or numeric risk scores
* design mitigations or implementation plans
* estimate confidence
* approve engineering work
* execute production work
* create source code
* access external sources without authorization

---

# Security and Privacy

The task must:

* use only context required for risk identification
* record security risks by reference rather than reproducing sensitive detail
* avoid recording secrets or credentials
* avoid unnecessary personal information
* preserve repository boundaries

---

# Accessibility

Human-readable output must:

* use explicit risk titles
* keep risks, assumptions, open questions, constraints, and consequences visually and structurally separate
* explain likelihood and impact in plain language
* avoid color-only meaning
* remain understandable when read linearly
* expand uncommon abbreviations

---

# Metrics

Recommended metrics:

* risk-identification success rate
* misclassification-correction rate
* unsupported-risk rejection rate
* shared-risk detection rate
* cross-executor risk agreement
* human correction rate
* downstream confidence-support rate

Metrics exist to improve reasoning quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Repository Integration Boundary

Given valid Engineering Reasoning Context, Engineering Alternative Set, and Engineering Trade-off Analysis for:

```text
Should Repository Integration become a first-class subsystem?
```

when `TASK-ANALYZE-0006` executes,

then the output must identify genuine risks such as premature boundary migration, integration complexity growth, and unresolved scope,

and the output must not rank alternatives by aggregate risk.

## Scenario 2 — No Fabricated Probabilities

Given no project evidence about failure frequency,

when the task executes,

then no numeric probability or numeric risk score may appear, and likelihood must be expressed with a qualitative qualifier.

## Scenario 3 — Item Type Separation

Given an item that is actually an assumption,

when the task executes,

then it must appear in the assumptions register and must not appear as a risk.

## Scenario 4 — Known Consequence

Given a certain outcome of an alternative,

when the task executes,

then it must be recorded as a known consequence, not as a risk, unless it also creates a distinct uncertain outcome.

## Scenario 5 — Shared Risk

Given a risk that affects every alternative,

when the task executes,

then it must be recorded as a shared risk.

---

# Guiding Principle

Identify what could go wrong and how uncertain it is, keeping risk distinct from assumption, open question, constraint, and known consequence.

Do not decide which alternative is least risky; that judgment belongs to confidence assessment and recommendation.
