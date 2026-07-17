---

task_id: TASK-ANALYZE-0002
name: Identify Engineering Forces
version: 0.1.0
status: draft
category: analysis
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Identify the engineering forces that materially influence the current engineering question.

Engineering forces are the pressures, constraints, objectives, risks, incentives, and competing qualities that make an engineering decision non-trivial.

This task consumes a validated Engineering Reasoning Context and produces an Engineering Forces Analysis.

The task does not generate alternatives, compare solutions, make a recommendation, or approve engineering work.

---

# Core Principle

An engineering force is relevant only when it can materially influence the decision being evaluated.

The task must identify competing forces rather than collecting every possible engineering concern.

---

# Inputs

## Required Input: Engineering Reasoning Context

Produced by:

```text
TASK-ANALYZE-0001
Build Engineering Reasoning Context
```

The Engineering Reasoning Context must contain:

* Work Request ID
* parent Run ID
* engineering question
* engineering intent
* engineering phase
* project facts
* project constraints
* existing decisions
* engineering guidance
* assumptions
* open questions
* inherited findings
* provenance

## Required Input: Engineering Knowledge Package

The Engineering Knowledge Package is already referenced from the Engineering Reasoning Context.

It must contain the Decision Guide and supporting knowledge relevant to the engineering question.

## Required Input: Parent Execution Run

A valid reasoning Run ID conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

---

# Preconditions

Execution may begin only when:

* `TASK-ANALYZE-0001` completed successfully
* the Engineering Reasoning Context validates successfully
* the engineering question is explicit
* project facts and engineering guidance remain distinguishable
* the primary Decision Guide is identified
* relevant project constraints are available
* no blocking inherited finding prevents analysis
* the parent reasoning Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task may use:

* the primary Decision Guide in the Engineering Knowledge Package
* related Concepts
* related Patterns
* related Quality Attributes
* relevant Examples
* the Engineering Process Map
* the Engineering Knowledge Matrix
* the Engineering Task Model

For the reference architecture scenario, expected knowledge may include:

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

The task must use retrieved EKB guidance rather than introducing unrelated engineering knowledge.

---

# Definition of an Engineering Force

An Engineering Force is a factor that influences which engineering outcome is preferable.

Examples include:

* responsibility clarity
* coupling
* cohesion
* complexity
* maintainability
* security
* accessibility
* performance
* delivery timing
* reversibility
* implementation maturity
* organizational constraints
* unresolved scope
* technical risk

A force may encourage one direction while discouraging another.

A force is not:

* a final recommendation
* a solution alternative
* an unsupported preference
* a generic quality attribute with no project relevance
* a repeated project fact with no effect on the decision

---

# Force Sources

Engineering forces may originate from four source classes.

## Project Evidence

Facts documented by the consuming project.

Examples:

* current architecture
* implementation maturity
* existing subsystem ownership
* approved ADRs
* MVP boundaries

## Project Constraints

Conditions that limit or shape possible outcomes.

Examples:

* modular monolith requirement
* provider independence
* delivery deadlines
* human approval requirements

## Engineering Knowledge

Guidance from EKB.

Examples:

* coupling and cohesion considerations
* modular architecture trade-offs
* maintainability impacts
* premature abstraction risks

## Uncertainty

Missing or unresolved information that affects the decision.

Examples:

* unresolved integration scope
* no observed change patterns
* missing implementation evidence
* unknown performance requirements

Every identified force must cite at least one source.

---

# Force Categories

The task should classify forces using the following categories where applicable.

## Structural

Concerns system boundaries, responsibilities, dependencies, and architecture.

Examples:

* cohesion
* coupling
* modular boundaries
* ownership

## Quality

Concerns quality attributes.

Examples:

* maintainability
* complexity
* reliability
* accessibility
* security
* performance

## Delivery

Concerns time, sequencing, effort, and project maturity.

Examples:

* MVP timing
* implementation readiness
* delivery simplicity
* rework cost

## Operational

Concerns runtime, deployment, support, and recovery.

Examples:

* observability
* failure isolation
* deployment independence
* recoverability

## Knowledge

Concerns uncertainty and the completeness of engineering understanding.

Examples:

* unresolved vocabulary
* missing evidence
* incomplete domain understanding
* unvalidated assumptions

## Governance

Concerns existing decisions, standards, approvals, and policy constraints.

Examples:

* existing ADR
* human approval requirement
* provider-independence rule
* security policy

A force may belong to more than one category, but one primary category should be selected.

---

# Direction

Every force must identify its effect on the decision.

Allowed direction values:

```text
encourages_change
discourages_change
encourages_deferral
context_dependent
neutral
```

For a subsystem-boundary question:

* `encourages_change` means the force supports introducing a new subsystem.
* `discourages_change` means the force supports retaining the current boundary.
* `encourages_deferral` means the force supports gathering more evidence first.
* `context_dependent` means the effect depends on unresolved project conditions.
* `neutral` means the force is relevant but does not currently favor a direction.

The task must not convert direction into a final recommendation.

---

# Materiality

Every force must be assigned a materiality level.

Allowed values:

```text
critical
high
medium
low
```

## Critical

The force may independently block or require a decision.

## High

The force strongly influences the preferred outcome.

## Medium

The force materially affects the decision but is not dominant alone.

## Low

The force provides context but is unlikely to change the outcome.

Low-materiality forces should be omitted when they add noise without improving reasoning.

---

# Evidence Strength

Every force must include an evidence-strength assessment.

Allowed values:

```text
strong
moderate
weak
unknown
```

## Strong

Supported by approved project artifacts, measurements, observed behavior, or explicit constraints.

## Moderate

Supported by current documentation or consistent project evidence but not yet validated through implementation.

## Weak

Supported mainly by assumptions, incomplete documentation, or indirect evidence.

## Unknown

The relevant evidence is missing.

Evidence strength is distinct from materiality.

A highly material force may have weak evidence.

---

# Execution Rules

1. Read the Engineering Reasoning Context.
2. Confirm the exact engineering question.
3. Load the primary Decision Guide from the Engineering Knowledge Package.
4. Identify forces explicitly named by the Decision Guide.
5. Identify project constraints that materially affect the question.
6. Identify current project facts that strengthen or weaken each force.
7. Identify unresolved questions that create uncertainty.
8. Remove forces that are unrelated to the current decision.
9. Merge duplicate forces only when they represent the same engineering concern.
10. Keep distinct forces separate when their effects differ.
11. Classify each force by category.
12. assign each force a direction.
13. assign each force a materiality level.
14. assess evidence strength.
15. record supporting project evidence.
16. record supporting EKB knowledge.
17. record assumptions separately.
18. record contradictions or missing evidence as findings.
19. produce the Engineering Forces Analysis.
20. validate the output.
21. add the task result to the parent execution trace.

The task must not rank alternatives because alternatives have not yet been generated.

The task must not state which final decision should be made.

---

# Force Identification Questions

The executor should evaluate questions such as:

* What project fact makes the current design harder to maintain?
* What would become simpler if the architecture changed?
* What new coordination cost would the change introduce?
* Which responsibilities currently change for different reasons?
* Which responsibilities belong together?
* Which quality attributes are most affected?
* Which constraints rule out or weaken certain directions?
* Which current decisions already govern this area?
* Which unknowns make the decision premature?
* Which evidence would materially change the future recommendation?

These questions guide observable analysis.

They must not be used to expose private chain-of-thought.

---

# Primary Output

The primary output is an Engineering Forces Analysis.

Recommended path:

```text
runtime/runs/<RUN_ID>/task_outputs/engineering-forces.yaml
```

Example:

```yaml
task_id: TASK-ANALYZE-0002
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: completed

engineering_question: >
  Should Repository Integration become a first-class subsystem
  within Context Switcher?

forces:
  - force_id: FORCE-0001
    name: Existing Integration Boundary
    category: structural
    direction: discourages_change
    materiality: high
    evidence_strength: strong
    description: >
      The current architecture already assigns external-system connectivity
      to the Integration subsystem.
    project_evidence:
      - source: docs/architecture/SYSTEM_ARCHITECTURE.md
        statement: >
          Local Git repositories are listed as an Integration responsibility.
      - source: decisions/ADR-0002-modular-platform-architecture.md
        statement: >
          The project should begin with modular boundaries rather than
          introducing unnecessary new structure.
    engineering_knowledge:
      - id: CON-ARCH-0002
        relevance: >
          A new subsystem should increase cohesion rather than fragment an
          already coherent responsibility.
    assumptions: []

  - force_id: FORCE-0002
    name: Distinct Repository Vocabulary
    category: structural
    direction: encourages_change
    materiality: medium
    evidence_strength: moderate
    description: >
      Repository work introduces concepts such as branches, commits, diffs,
      pull requests, and repository scans that may form a distinct bounded
      context.
    project_evidence:
      - source: docs/architecture/AI_ARCHITECTURE.md
        statement: >
          Repository-aware work evaluation introduces repository-specific
          concepts and unresolved design questions.
    engineering_knowledge:
      - id: CON-ARCH-0003
        relevance: >
          Distinct vocabulary and rules may indicate a bounded context.
    assumptions:
      - >
        Repository capabilities will grow beyond a small adapter.

  - force_id: FORCE-0003
    name: Incomplete Repository Scope
    category: knowledge
    direction: encourages_deferral
    materiality: high
    evidence_strength: strong
    description: >
      The project has not resolved whether repository integration means local
      Git access, GitHub API access, or both.
    project_evidence:
      - source: docs/architecture/AI_ARCHITECTURE.md
        statement: >
          Local Git versus GitHub API remains an open question.
    engineering_knowledge:
      - id: DG-ARCH-0001
        relevance: >
          Subsystem separation should be delayed when the boundary is not yet
          understood.
    assumptions: []

  - force_id: FORCE-0004
    name: Premature Complexity
    category: quality
    direction: discourages_change
    materiality: high
    evidence_strength: moderate
    description: >
      Introducing a subsystem before implementation exists may increase
      coordination cost without reducing actual reasoning complexity.
    project_evidence:
      - source: docs/product/MVP_SCOPE.md
        statement: >
          Repository integration is outside the initial MVP.
    engineering_knowledge:
      - id: QA-0002
        relevance: >
          New architecture can increase complexity when introduced
          speculatively.
      - id: EX-ARCH-0001
        relevance: >
          The delay example recommends gathering evidence before splitting.
    assumptions: []

dominant_forces:
  - FORCE-0001
  - FORCE-0003
  - FORCE-0004

uncertain_forces:
  - FORCE-0002

findings: []

validation:
  result: passed
  force_count: 4
  every_force_has_project_evidence: true
  every_force_has_engineering_basis: true
  recommendation_generated: false
```

The output is:

* generated
* non-canonical
* read-only for downstream tasks
* consumed by alternative-generation and trade-off-analysis tasks

---

# Secondary Outputs

The task may produce:

* missing-evidence findings
* contradictory-force findings
* weak-evidence warnings
* duplicate-force warnings
* irrelevant-guidance warnings
* unresolved-quality-attribute findings
* trace fragments
* recovery recommendations

Secondary outputs must not replace the Engineering Forces Analysis.

---

# Dominant Forces

The task may identify dominant forces.

A dominant force is one that:

* has high or critical materiality
* is supported by moderate or strong evidence
* materially constrains the decision space

Dominant-force identification is allowed.

Dominant-force identification is not a recommendation.

The task must not state that one outcome “wins.”

---

# Conflicting Forces

Conflicting forces are expected.

Example:

```text
Distinct repository vocabulary
encourages_change
```

may conflict with:

```text
Incomplete repository scope
encourages_deferral
```

The task must preserve both.

It must not resolve the conflict.

Conflict resolution belongs to later alternative and trade-off analysis.

---

# Findings

Every finding must include:

* Finding ID
* Classification
* Description
* Evidence
* Required Action
* Status

Example:

```yaml
findings:
  - id: FIND-FORCE-0001
    classification: major
    description: >
      The project uses both "Local Git repository" and "GitHub repository"
      without defining whether they represent one capability.
    evidence:
      - docs/architecture/SYSTEM_ARCHITECTURE.md
      - docs/architecture/AI_ARCHITECTURE.md
    required_action: >
      Clarify the repository integration scope before final architecture
      approval.
    status: open
```

A blocking finding should cause task status:

```text
completed_with_findings
```

or:

```text
failed
```

depending on whether a usable Engineering Forces Analysis can still be produced.

---

# Validation

The task passes validation only when:

* the Work Request ID is present
* the Run ID is present
* the Engineering Question matches the Engineering Reasoning Context
* at least two materially distinct forces are identified
* every force has a unique Force ID
* every force has a category
* every force has a direction
* every force has a materiality level
* every force has an evidence-strength rating
* every force cites project evidence or explicitly states evidence is missing
* every force references relevant EKB guidance where applicable
* assumptions remain separate from evidence
* duplicate forces are removed or justified
* unresolved contradictions are recorded
* no final recommendation is produced
* task status is recorded
* the result is added to the parent execution trace

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* the Engineering Reasoning Context is read successfully
* material engineering forces are identified
* provenance is preserved
* dominant and uncertain forces are identified where applicable
* validation succeeds
* no unhandled blocking finding remains
* the primary output is available to downstream tasks
* the task result is recorded in the parent execution trace

---

# Failure Conditions

The task must fail when:

* the Engineering Reasoning Context is missing
* the engineering question is missing or inconsistent
* project facts and engineering guidance cannot be distinguished
* the primary Decision Guide is unavailable
* no relevant force can be identified
* forces rely entirely on unsupported assumptions
* evidence contradictions prevent a coherent force analysis
* output validation fails

The task must not invent forces to satisfy minimum output requirements.

---

# Failure Output

```yaml
task_id: TASK-ANALYZE-0002
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: insufficient_engineering_evidence
  description: >
    The Engineering Reasoning Context does not contain enough project evidence
    to identify material forces for the architectural question.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-reasoning-context.yaml
  partial_output_available: false
  recovery_action: >
    Expand the project Engineering Context with current architectural
    constraints and rerun the context-retrieval pipeline.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent Run ID
* Engineering Reasoning Context source
* Decision Guide used
* project sources consulted
* candidate forces considered
* forces included
* forces excluded
* exclusion reasons
* force categories
* force directions
* materiality assessments
* evidence-strength assessments
* assumptions
* findings
* validation result
* output location
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace should explain the observable basis for every force without exposing private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly with the same:

* Engineering Reasoning Context
* Engineering Knowledge Package
* EKB version
* ECF version

should produce materially equivalent Engineering Forces Analyses.

---

# Determinism

Expected level:

```text
Constrained
```

Wording and grouping may vary, but the following should remain materially consistent:

* major force set
* force directions
* dominant forces
* materiality
* evidence sources
* assumptions
* findings
* validation result

Cross-executor disagreement about high- or critical-materiality forces must be recorded and reviewed.

---

# Executor Requirements

The executor requires:

* read access to the Engineering Reasoning Context
* read access to the Engineering Knowledge Package
* read access to cited project context
* read access to bundled ECF
* read access to bundled EKB
* permission to write runtime task output
* permission to update runtime trace data

No network access is required.

---

# Permission Boundaries

Allowed:

* read runtime outputs from previous tasks
* read cited project artifacts
* read bundled ECF
* read bundled EKB
* write the Engineering Forces Analysis
* write findings
* update runtime trace data

Prohibited:

* modify canonical project artifacts
* modify bundled dependencies
* generate alternatives
* rank solution alternatives
* generate a final recommendation
* approve engineering work
* execute production work
* modify source code
* access external sources without authorization

---

# Security and Privacy

The task must:

* use only project context required for force identification
* avoid recording secrets or credentials
* avoid unnecessary personal information
* preserve repository boundaries
* avoid copying sensitive project content when a source citation is sufficient
* identify sensitive evidence without unnecessarily reproducing it

---

# Accessibility

Human-readable output must:

* use explicit labels
* explain force direction in plain language
* avoid color-only status indicators
* remain understandable when read linearly
* avoid unexplained abbreviations
* provide text equivalents for any generated visual representation

---

# Metrics

Recommended metrics:

* force-identification success rate
* average force count
* irrelevant-force rejection rate
* cross-executor force agreement
* dominant-force agreement
* missing-evidence finding rate
* human correction rate
* downstream alternative-coverage rate

Metrics exist to improve reasoning quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Repository Integration Boundary

Given a valid Engineering Reasoning Context for:

```text
Should Repository Integration become a first-class subsystem?
```

when `TASK-ANALYZE-0002` executes,

then the result should identify forces including:

* existing Integration ownership
* repository-specific vocabulary
* incomplete scope
* maintainability
* complexity
* lack of implementation evidence

The task must not produce a final recommendation.

## Scenario 2 — Insufficient Evidence

Given an Engineering Reasoning Context containing only the engineering question and no project facts,

when the task executes,

then it must fail with:

```text
insufficient_engineering_evidence
```

## Scenario 3 — Conflicting Forces

Given evidence that strongly supports both separation and consolidation,

when the task executes,

then both directions must be preserved.

The task must not resolve the conflict.

## Scenario 4 — Unrelated Quality Attribute

Given an Engineering Knowledge Package containing an unrelated quality attribute that has no project relevance,

when the task executes,

then that quality attribute must not become an Engineering Force unless its relevance is explicitly demonstrated.

## Scenario 5 — Weak Assumption

Given a force supported only by an unvalidated assumption,

when the task executes,

then:

* evidence strength must be `weak`
* the assumption must be recorded separately
* the force must not be treated as dominant without additional evidence

---

# Guiding Principle

Identify the engineering forces that shape the decision space.

Do not resolve the decision.

This task makes competing pressures visible so later reasoning tasks can evaluate alternatives and trade-offs transparently.
