---

task_id: TASK-ANALYZE-0005
name: Analyze Engineering Trade-offs
version: 0.1.0
status: draft
category: analysis
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Compare every viable engineering alternative against the material engineering forces and the affected quality attributes.

This task makes the consequences of each alternative explicit and comparable.

It consumes the Engineering Reasoning Context, the Engineering Forces Analysis, the Decision Option Set, and the Engineering Alternative Set, and produces one Engineering Trade-off Analysis.

The task does not select a preferred alternative, rank alternatives into a single ordered winner, generate a recommendation, or approve engineering work.

---

# Core Principle

A trade-off is an explicit statement of what an alternative gains and what it gives up when measured against a specific engineering force or quality attribute.

The task must expose trade-offs transparently rather than compress them into a single score or a preferred choice.

Every comparison must be traceable to a force, a quality attribute, or documented project evidence.

---

# Inputs

## Required Input: Engineering Reasoning Context

Produced by:

```text
TASK-ANALYZE-0001
Build Engineering Reasoning Context
```

Provides the engineering question, project facts, engineering guidance, assumptions, and open questions.

## Required Input: Engineering Forces Analysis

Produced by:

```text
TASK-ANALYZE-0002
Identify Engineering Forces
```

Provides the material forces, their direction, materiality, and evidence strength.

## Required Input: Decision Option Set

Produced by:

```text
TASK-ANALYZE-0003
Identify Decision Options
```

Provides the feasible decision directions that the alternatives realize.

## Required Input: Engineering Alternative Set

Produced by:

```text
TASK-ANALYZE-0004
Generate Engineering Alternatives
```

Provides the concrete alternatives, their responsibility models, candidate benefits, candidate costs, and related forces.

## Required Input: Parent Execution Run

A valid reasoning Run ID conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

---

# Preconditions

Execution may begin only when:

* `TASK-ANALYZE-0001` completed successfully
* `TASK-ANALYZE-0002` completed successfully
* `TASK-ANALYZE-0003` completed successfully
* `TASK-ANALYZE-0004` completed successfully
* the Engineering Reasoning Context validates
* the Engineering Forces Analysis validates
* the Engineering Alternative Set validates
* at least two viable alternatives exist
* at least two material forces exist
* the engineering question is identical across all inputs
* no blocking inherited finding prevents comparison
* the parent reasoning Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task may use:

* the primary Decision Guide referenced by the Engineering Reasoning Context
* the Quality Attributes referenced in the Engineering Knowledge Package
* related Concepts and Patterns
* relevant Examples
* the Engineering Forces Analysis

For the reference architecture scenario, relevant knowledge may include:

```text
DG-ARCH-0001
CON-ARCH-0001
CON-ARCH-0002
CON-ARCH-0003
PAT-ARCH-0001
QA-0001
QA-0002
EX-ARCH-0001
```

The task must use retrieved EKB guidance rather than introducing unrelated engineering knowledge, and must not invent new quality attributes that were not retrieved.

---

# Definitions

## Trade-off

A directional consequence of choosing an alternative, expressed against one force or one quality attribute.

A trade-off states both the gain and the sacrifice.

## Comparison Axis

A force or quality attribute along which alternatives are compared.

Every comparison axis must originate from the Engineering Forces Analysis or the retrieved Quality Attributes.

## Relative Effect

A qualitative judgment of how an alternative performs on a comparison axis.

Allowed relative-effect values:

```text
strongly_favorable
favorable
neutral
unfavorable
strongly_unfavorable
context_dependent
unknown
```

Relative effect is not a numeric score and must not be summed or averaged into a ranking.

---

# Execution Rules

1. Read the Engineering Reasoning Context.
2. Confirm the exact engineering question.
3. Read the Engineering Forces Analysis and load the material forces.
4. Read the Decision Option Set.
5. Read the Engineering Alternative Set and load the viable alternatives.
6. Assemble the comparison axes from material forces and affected quality attributes.
7. Exclude low-materiality forces that add noise without improving comparison.
8. For each viable alternative, evaluate its relative effect on each comparison axis.
9. State, for each effect, both what is gained and what is given up.
10. Cite the force, quality attribute, or project evidence supporting each effect.
11. Record assumptions separately from evidence.
12. Preserve conflicting effects rather than resolving them.
13. Identify tensions where an alternative improves one axis while worsening another.
14. Record where evidence is insufficient to judge an effect, using `unknown`.
15. Record contradictions or missing evidence as findings.
16. Produce the Engineering Trade-off Analysis.
17. Validate the output.
18. Add the task result to the parent execution trace.

The task must not:

* select a recommended alternative
* produce a single ordered ranking that implies a decision
* collapse the multidimensional comparison into one score
* introduce new alternatives
* introduce new forces or quality attributes not present in the inputs
* estimate confidence
* approve engineering work

---

# Comparison Coverage

Every viable alternative must be compared against every material comparison axis.

Coverage must be reported so that gaps are visible.

A missing comparison must be recorded as a finding rather than silently omitted.

---

# Primary Output

The primary output is an Engineering Trade-off Analysis.

Recommended path:

```text
runtime/runs/<RUN_ID>/task_outputs/engineering-trade-offs.yaml
```

Example:

```yaml
task_id: TASK-ANALYZE-0005
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: completed

engineering_question: >
  Should Repository Integration become a first-class subsystem
  within Context Switcher?

comparison_axes:
  - axis_id: AXIS-0001
    name: Cohesion of Repository Responsibilities
    origin: FORCE-0002
    knowledge_basis:
      - CON-ARCH-0002
      - CON-ARCH-0003
  - axis_id: AXIS-0002
    name: Structural Complexity
    origin: FORCE-0004
    knowledge_basis:
      - QA-0002
  - axis_id: AXIS-0003
    name: Maintainability
    origin: QA-0001
    knowledge_basis:
      - QA-0001
  - axis_id: AXIS-0004
    name: Decision Reversibility Under Incomplete Scope
    origin: FORCE-0003
    knowledge_basis:
      - DG-ARCH-0001
      - EX-ARCH-0001

trade_offs:
  - alternative_id: ALT-0001
    name: Dedicated Repository Integration Subsystem
    effects:
      - axis_id: AXIS-0001
        relative_effect: favorable
        gain: >
          Groups repository-specific vocabulary and rules into one cohesive
          boundary.
        sacrifice: >
          Commits to a boundary before the repository domain is fully
          understood.
        evidence:
          - FORCE-0002
          - CON-ARCH-0003
        assumptions:
          - repository_capability_will_expand_materially
      - axis_id: AXIS-0002
        relative_effect: unfavorable
        gain: >
          Provides explicit interfaces between repository concerns and the
          rest of the system.
        sacrifice: >
          Adds a new subsystem and coordination cost while implementation
          has not started.
        evidence:
          - FORCE-0004
          - QA-0002
        assumptions: []
      - axis_id: AXIS-0004
        relative_effect: strongly_unfavorable
        gain: >
          Forces early clarity about repository ownership.
        sacrifice: >
          A premature boundary is expensive to reverse once other subsystems
          depend on it.
        evidence:
          - FORCE-0003
          - DG-ARCH-0001
        assumptions: []

  - alternative_id: ALT-0003
    name: Repository Adapter Within Integration
    effects:
      - axis_id: AXIS-0001
        relative_effect: neutral
        gain: >
          Creates an internal repository boundary without a new subsystem.
        sacrifice: >
          Repository cohesion is bounded by the existing Integration
          responsibilities.
        evidence:
          - FORCE-0001
          - PAT-ARCH-0001
        assumptions: []
      - axis_id: AXIS-0002
        relative_effect: favorable
        gain: >
          Preserves the current subsystem count and dependency rules.
        sacrifice: >
          Integration complexity may grow as repository concerns increase.
        evidence:
          - FORCE-0004
          - QA-0002
        assumptions: []
      - axis_id: AXIS-0004
        relative_effect: favorable
        gain: >
          Keeps later extraction possible when evidence supports it.
        sacrifice: >
          An internal boundary may still require migration later.
        evidence:
          - DG-ARCH-0001
        assumptions: []

  - alternative_id: ALT-0004
    name: Defer Boundary and Run Repository Capability Spike
    effects:
      - axis_id: AXIS-0004
        relative_effect: strongly_favorable
        gain: >
          Gathers evidence before any irreversible structural commitment.
        sacrifice: >
          Delays the final boundary decision.
        evidence:
          - FORCE-0003
          - EX-ARCH-0001
        assumptions: []

tensions:
  - description: >
      The dedicated subsystem improves cohesion but worsens structural
      complexity and reversibility while scope is unresolved.
    axes:
      - AXIS-0001
      - AXIS-0002
      - AXIS-0004
    alternatives:
      - ALT-0001

coverage:
  ALT-0001:
    axes_compared: [AXIS-0001, AXIS-0002, AXIS-0004]
    axes_missing: [AXIS-0003]
    finding: FIND-TRADE-0001
  ALT-0003:
    axes_compared: [AXIS-0001, AXIS-0002, AXIS-0004]
    axes_missing: [AXIS-0003]
    finding: FIND-TRADE-0001
  ALT-0004:
    axes_compared: [AXIS-0004]
    axes_missing: [AXIS-0001, AXIS-0002, AXIS-0003]
    finding: FIND-TRADE-0002

findings:
  - id: FIND-TRADE-0001
    classification: minor
    description: >
      Maintainability effects could not be judged for structural alternatives
      because no implementation evidence exists yet.
    evidence:
      - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-forces.yaml
    required_action: >
      Re-evaluate maintainability once repository requirements are defined.
    status: open

validation:
  result: passed
  alternatives_compared: 3
  comparison_axes: 4
  every_effect_has_basis: true
  recommendation_generated: false
```

The output is:

* generated
* runtime
* non-canonical
* read-only for downstream tasks
* consumed by the risk-analysis, missing-information, confidence, and recommendation tasks

---

# Secondary Outputs

The task may produce:

* missing-comparison findings
* insufficient-evidence findings
* conflicting-effect observations
* unresolved-tension observations
* trace fragments
* recovery recommendations

Secondary outputs must not replace the Engineering Trade-off Analysis.

---

# Validation

The task passes validation only when:

* the Work Request ID is present
* the Run ID is present
* the engineering question matches all inputs
* at least two viable alternatives are compared
* every comparison axis originates from a force or a retrieved quality attribute
* every alternative is compared against every material axis or a gap finding exists
* every effect states both a gain and a sacrifice
* every effect cites a force, quality attribute, or project evidence
* assumptions remain separate from evidence
* conflicting effects are preserved rather than resolved
* no preferred alternative is selected
* no single ordered ranking implying a decision is produced
* no confidence value is produced
* task status is recorded
* the result is added to the parent execution trace

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* comparison axes are assembled from material forces and quality attributes
* every viable alternative is compared or gaps are recorded as findings
* trade-offs state gains and sacrifices with provenance
* tensions are made explicit
* validation succeeds
* no unhandled blocking finding remains
* the Engineering Trade-off Analysis is available to downstream tasks
* the task result is recorded in the execution trace

---

# Failure Conditions

The task must fail when:

* any required input is missing
* fewer than two viable alternatives exist
* no material forces or quality attributes exist to compare against
* the engineering question is inconsistent across inputs
* alternatives and forces cannot be reconciled
* every comparison would depend entirely on unsupported assumptions
* output validation fails

The task must not fabricate comparisons to satisfy coverage.

---

# Failure Output

```yaml
task_id: TASK-ANALYZE-0005
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: insufficient_comparison_basis
  description: >
    The Engineering Forces Analysis and Alternative Set do not provide enough
    material axes to produce a meaningful trade-off comparison.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-forces.yaml
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-alternatives.yaml
  partial_output_available: false
  recovery_action: >
    Re-run force identification and alternative generation with additional
    project evidence, then retry the trade-off analysis.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent Run ID
* input sources consumed
* comparison axes assembled
* forces and quality attributes excluded and the reason
* alternatives compared
* relative effects and their basis
* tensions identified
* coverage gaps
* assumptions
* findings
* validation result
* output location
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace must explain the observable basis for each trade-off without exposing private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly with the same:

* Engineering Reasoning Context
* Engineering Forces Analysis
* Decision Option Set
* Engineering Alternative Set
* EKB version
* ECF version

should produce a materially equivalent Engineering Trade-off Analysis.

---

# Determinism

Expected level:

```text
Constrained
```

Wording may differ, but the following should remain materially consistent:

* comparison axes
* alternative-to-axis effects
* declared gains and sacrifices
* identified tensions
* coverage gaps
* assumptions
* findings
* validation result

Cross-executor disagreement about a `strongly_favorable` or `strongly_unfavorable` effect must be recorded and reviewed.

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
* write the Engineering Trade-off Analysis
* write findings
* update runtime trace data

Prohibited:

* modify canonical project artifacts
* modify bundled dependencies
* select or rank a preferred alternative
* generate a recommendation
* estimate confidence
* approve engineering work
* execute production work
* create source code
* access external sources without authorization

---

# Security and Privacy

The task must:

* use only the context required for comparison
* avoid recording secrets or credentials
* avoid unnecessary personal information
* preserve repository boundaries
* cite sensitive evidence rather than reproducing it unnecessarily

---

# Accessibility

Human-readable output must:

* use explicit axis and alternative names
* state gains and sacrifices in plain language
* avoid color-only meaning
* remain understandable when read linearly
* expand uncommon abbreviations
* provide text equivalents for any generated visual comparison

---

# Metrics

Recommended metrics:

* trade-off completeness rate
* comparison-coverage rate
* insufficient-evidence effect rate
* cross-executor effect agreement
* tension-detection rate
* human correction rate
* downstream recommendation-support rate

Metrics exist to improve reasoning quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Repository Integration Boundary

Given valid Engineering Reasoning Context, Engineering Forces Analysis, Decision Option Set, and Engineering Alternative Set for:

```text
Should Repository Integration become a first-class subsystem?
```

when `TASK-ANALYZE-0005` executes,

then the output must compare each viable alternative against the material forces and affected quality attributes, stating gains and sacrifices,

and the output must not select or rank a preferred alternative.

## Scenario 2 — Missing Comparison Basis

Given only one viable alternative or no material forces,

when the task executes,

then it must fail with:

```text
insufficient_comparison_basis
```

## Scenario 3 — Conflicting Effects

Given an alternative that improves cohesion but worsens complexity,

when the task executes,

then both effects must be preserved as an explicit tension and must not be resolved into a single verdict.

## Scenario 4 — Insufficient Evidence for an Axis

Given an axis that cannot be judged because implementation evidence is absent,

when the task executes,

then the relative effect must be `unknown` and a finding must record the gap.

## Scenario 5 — No Ranking Leakage

Given a completed trade-off analysis,

when the output is inspected,

then it must not contain a preferred alternative, an ordered winner, or a recommendation.

---

# Guiding Principle

Make the consequences of each alternative explicit and comparable.

Show what each choice gains and what it gives up.

Do not decide which alternative wins; that belongs to the recommendation task.
