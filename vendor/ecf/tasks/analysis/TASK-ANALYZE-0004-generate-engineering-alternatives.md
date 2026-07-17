---

task_id: TASK-ANALYZE-0004
name: Generate Engineering Alternatives
version: 0.1.0
status: draft
category: analysis
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Generate realistic engineering alternatives for each viable Decision Option.

A Decision Option describes a possible direction.

An Engineering Alternative describes a concrete way that direction could be realized.

This task expands the decision space without ranking alternatives or making a recommendation.

---

# Core Principle

Alternatives must be realistic enough to evaluate.

The task must not create artificial alternatives merely to increase option count.

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

## Required Input: Parent Execution Run

A valid reasoning Run ID.

---

# Preconditions

Execution may begin only when:

* `TASK-ANALYZE-0001` completed successfully
* `TASK-ANALYZE-0002` completed successfully
* `TASK-ANALYZE-0003` completed successfully
* the Engineering Reasoning Context validates
* the Engineering Forces Analysis validates
* at least two viable Decision Options exist
* no blocking finding prevents alternative generation
* the parent Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task may use:

* the primary Decision Guide
* relevant Concepts
* relevant Patterns
* relevant Examples
* existing project architecture
* existing ADRs
* project constraints
* Engineering Forces Analysis

The task must not introduce unrelated patterns, technologies, or architectural styles.

External knowledge may be used only when explicitly authorized.

---

# Definitions

## Decision Option

A high-level direction that answers the engineering question.

Example:

```text
Keep Repository Integration within existing boundaries.
```

## Engineering Alternative

A concrete realization of a Decision Option.

Examples:

```text
Keep repository connectivity inside Integration and repository evaluation inside AI.
```

```text
Keep all repository concerns inside Integration and expose repository data to AI through a stable interface.
```

Multiple alternatives may implement the same Decision Option.

---

# Alternative Categories

Alternatives may be classified as:

## Structural

Changes system boundaries or responsibility ownership.

## Incremental

Introduces change gradually or behind existing boundaries.

## Experimental

Creates a limited spike, prototype, or temporary implementation to gather evidence.

## Deferred

Postpones a structural commitment while defining explicit review triggers.

## Status Quo

Retains the existing design.

## Hybrid

Combines elements from multiple options.

One primary category must be selected for each alternative.

---

# Execution Rules

1. Read the Engineering Question.
2. Read the Decision Option Set.
3. Read the Engineering Forces Analysis.
4. Read relevant project constraints and existing decisions.
5. For each viable Decision Option, determine whether one or more realistic implementations exist.
6. Generate only materially distinct alternatives.
7. Ensure every alternative maps to exactly one primary Decision Option.
8. Record any secondary Decision Options influenced by the alternative.
9. Describe the proposed responsibility boundaries.
10. Describe the expected interaction with the current architecture.
11. Record required assumptions.
12. Record known constraints.
13. Record expected changes at a conceptual level.
14. Record evidence still required before adoption.
15. Remove alternatives that violate approved constraints.
16. Remove alternatives that differ only in wording.
17. Mark speculative alternatives clearly.
18. Produce the Engineering Alternative Set.
19. Validate the output.
20. Add the task result to the parent execution trace.

The task must not:

* rank alternatives
* identify a preferred alternative
* produce trade-off conclusions
* calculate confidence
* modify project architecture
* select implementation technologies without evidence
* produce source code

---

# Alternative Design Rules

Every Engineering Alternative must:

* answer the Engineering Question
* implement one viable Decision Option
* remain compatible with known project constraints
* be materially different from other alternatives
* be concrete enough for trade-off analysis
* identify assumptions
* identify required evidence
* preserve provenance

An alternative must not be included when it is:

* technically impossible
* prohibited by an approved decision
* merely a renamed duplicate
* dependent entirely on unsupported assumptions
* outside the scope of the Work Request

---

# Required Alternative Structure

Each alternative must contain:

* Alternative ID
* Name
* Decision Option ID
* Category
* Status
* Summary
* Responsibility Model
* Architectural Impact
* Expected Benefits
* Expected Costs
* Constraints
* Assumptions
* Required Evidence
* Related Forces
* Related Knowledge Objects

The Expected Benefits and Expected Costs sections describe candidate consequences only.

They are not final trade-off conclusions.

---

# Alternative Status Values

Allowed values:

```text
viable
conditionally_viable
experimental
deferred
rejected
```

## Viable

Compatible with current evidence and constraints.

## Conditionally Viable

Possible only when explicit conditions are satisfied.

## Experimental

Suitable for a spike or evidence-gathering exercise, but not yet suitable for adoption.

## Deferred

Intentionally postponed until a defined review trigger occurs.

## Rejected

Excluded because it violates constraints or lacks feasibility.

Rejected alternatives may be retained in the trace, but not in the primary viable set.

---

# Primary Output

The primary output is an Engineering Alternative Set.

Recommended path:

```text
runtime/runs/<RUN_ID>/task_outputs/engineering-alternatives.yaml
```

Example:

```yaml
task_id: TASK-ANALYZE-0004
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: completed

engineering_question: >
  Should Repository Integration become a first-class subsystem
  within Context Switcher?

alternatives:
  - alternative_id: ALT-0001
    name: Dedicated Repository Integration Subsystem
    decision_option_id: OPT-0001
    category: structural
    status: conditionally_viable

    summary: >
      Introduce a first-class subsystem responsible for repository access,
      repository scanning, repository metadata, and repository-related
      integration events.

    responsibility_model:
      owns:
        - repository_connectivity
        - repository_scanning
        - repository_metadata
        - repository_integration_events
      excludes:
        - ai_evaluation
        - work_session_management

    architectural_impact:
      - add_new_subsystem
      - define_repository_interfaces
      - update_dependency_rules
      - update_system_architecture
      - create_architecture_decision_record

    expected_benefits:
      - clearer repository-specific ownership
      - isolated repository implementation details
      - potential independent evolution

    expected_costs:
      - additional subsystem coordination
      - new interfaces and event contracts
      - risk of premature architecture

    constraints:
      - must_remain_modular_monolith
      - ai_provider_independence

    assumptions:
      - repository_capability_will_expand_materially
      - repository_vocabulary_will_stabilize

    required_evidence:
      - resolved_local_git_vs_github_scope
      - repository_feature_requirements
      - observed_repository_change_patterns

    related_forces:
      - FORCE-0002
      - FORCE-0003
      - FORCE-0004

    related_knowledge:
      - DG-ARCH-0001
      - CON-ARCH-0001
      - CON-ARCH-0002
      - CON-ARCH-0003
      - PAT-ARCH-0001

  - alternative_id: ALT-0002
    name: Preserve Existing Integration and AI Ownership
    decision_option_id: OPT-0002
    category: status_quo
    status: viable

    summary: >
      Keep repository connectivity and scanning inside Integration while
      retaining repository-aware interpretation and evaluation inside AI.

    responsibility_model:
      integration_owns:
        - repository_connectivity
        - repository_scanning
        - repository_data_translation
      ai_owns:
        - repository_analysis
        - repository_work_evaluation
        - recommendation_generation

    architectural_impact:
      - clarify_existing_responsibilities
      - define_integration_to_ai_contract
      - no_new_subsystem

    expected_benefits:
      - preserves current architecture
      - minimizes structural complexity
      - maintains AI provider independence
      - supports incremental implementation

    expected_costs:
      - repository responsibilities remain distributed
      - future growth may pressure the Integration boundary
      - interface ownership must be explicit

    constraints:
      - Integration must not own AI judgment
      - AI must not access repository implementation details directly

    assumptions:
      - repository connectivity remains comparable to other integrations
      - repository evaluation remains an AI responsibility

    required_evidence:
      - interface requirements
      - repository data contract
      - integration event definitions

    related_forces:
      - FORCE-0001
      - FORCE-0003
      - FORCE-0004

    related_knowledge:
      - CON-ARCH-0001
      - CON-ARCH-0002
      - PAT-ARCH-0001
      - QA-0001
      - QA-0002

  - alternative_id: ALT-0003
    name: Repository Adapter Within Integration
    decision_option_id: OPT-0002
    category: incremental
    status: viable

    summary: >
      Implement repository support as a dedicated adapter or module inside the
      existing Integration subsystem without promoting it to a first-class
      subsystem.

    responsibility_model:
      integration_owns:
        - repository_adapter
        - repository_scanner
        - repository_event_translation
      ai_owns:
        - repository_analysis
        - repository_recommendations

    architectural_impact:
      - add_internal_integration_module
      - define_internal_repository_boundary
      - retain_existing_top_level_subsystems

    expected_benefits:
      - creates a clear internal repository boundary
      - preserves architectural simplicity
      - allows later extraction if evidence supports it

    expected_costs:
      - internal boundary may later require migration
      - repository concerns may still increase Integration complexity

    constraints:
      - module must not be treated as an independently approved subsystem
      - project dependency rules remain unchanged

    assumptions:
      - repository capability can initially evolve within Integration
      - internal modularity provides enough isolation

    required_evidence:
      - initial repository requirements
      - adapter interface definition
      - testing boundaries

    related_forces:
      - FORCE-0001
      - FORCE-0002
      - FORCE-0004

    related_knowledge:
      - PAT-ARCH-0001
      - QA-0001
      - QA-0002

  - alternative_id: ALT-0004
    name: Defer Boundary and Run Repository Capability Spike
    decision_option_id: OPT-0004
    category: experimental
    status: experimental

    summary: >
      Defer the subsystem decision and conduct a limited engineering spike to
      clarify repository scope, vocabulary, interfaces, and change patterns.

    responsibility_model:
      temporary_ownership:
        - research_only
      canonical_architecture_change:
        - none

    architectural_impact:
      - no_immediate_subsystem_change
      - produce_evidence_for_later_review
      - define_architecture_review_trigger

    expected_benefits:
      - increases evidence before commitment
      - reduces speculative architecture
      - clarifies local Git versus GitHub boundaries

    expected_costs:
      - delays final boundary decision
      - requires time-boxed research
      - may produce throwaway implementation

    constraints:
      - spike outputs must not become production architecture automatically
      - source code changes must remain isolated
      - human review required before promotion

    assumptions:
      - the current architecture can host temporary research work
      - the decision is reversible while implementation has not started

    required_evidence:
      - repository workflow use cases
      - local Git and GitHub capability comparison
      - data and event requirements
      - testing and security implications

    related_forces:
      - FORCE-0002
      - FORCE-0003
      - FORCE-0004

    related_knowledge:
      - DG-ARCH-0001
      - EX-ARCH-0001
      - QA-0002

rejected_alternatives:
  - alternative_id: ALT-REJECTED-0001
    name: Put All Repository Responsibilities Inside AI
    reason: >
      This would mix external-system connectivity with AI interpretation and
      conflict with the current provider-independent architecture.
    violated_constraints:
      - ai_provider_independence
      - existing_integration_ownership

findings: []

validation:
  result: passed
  viable_alternative_count: 3
  experimental_alternative_count: 1
  recommendation_generated: false
```

The output is:

* generated
* runtime
* non-canonical
* read-only for downstream tasks
* consumed by trade-off-analysis tasks

---

# Secondary Outputs

The task may produce:

* rejected alternatives
* missing-evidence findings
* feasibility warnings
* constraint-conflict findings
* duplicate-alternative warnings
* speculative-alternative warnings
* trace fragments
* recovery recommendations

Secondary outputs must not replace the Engineering Alternative Set.

---

# Relationship to Decision Options

Every alternative must reference exactly one primary Decision Option.

One Decision Option may have:

* zero alternatives
* one alternative
* several alternatives

A viable Decision Option with no feasible alternative must produce a finding.

Example:

```yaml
finding:
  code: viable_option_without_realization
  decision_option_id: OPT-0003
```

The task must not invent an alternative merely to satisfy coverage.

---

# Alternative Coverage

The task should attempt to cover every viable Decision Option.

Coverage must be reported:

```yaml
option_coverage:
  OPT-0001:
    alternatives:
      - ALT-0001

  OPT-0002:
    alternatives:
      - ALT-0002
      - ALT-0003

  OPT-0003:
    alternatives: []
    finding: FIND-ALT-0001

  OPT-0004:
    alternatives:
      - ALT-0004
```

Uncovered options require explanation.

---

# Rejected Alternatives

Rejected alternatives should be recorded when they were materially considered.

Every rejected alternative must include:

* Alternative ID
* Name
* Rejection reason
* Violated constraint or missing prerequisite
* Evidence

Rejected alternatives remain part of the trace but are not evaluated as viable candidates unless a later run reopens them.

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
  - id: FIND-ALT-0001
    classification: major
    description: >
      The decision option "Separate Connectivity and Evaluation
      Responsibilities" cannot be expanded beyond the current Integration/AI
      split because the repository domain responsibilities remain undefined.
    evidence:
      - runtime/runs/RUN-REASON-20260710-0001/task_outputs/decision-options.yaml
      - docs/architecture/AI_ARCHITECTURE.md
    required_action: >
      Define repository capability responsibilities before generating a more
      detailed alternative.
    status: open
```

Blocking findings may prevent downstream trade-off analysis.

---

# Validation

The task passes validation only when:

* the Work Request ID is present
* the Run ID is present
* the Engineering Question matches prior task outputs
* every viable alternative has a unique ID
* every alternative references one Decision Option
* every alternative has a category
* every alternative has a status
* every alternative has a concrete responsibility model
* every alternative records architectural impact
* every alternative records assumptions
* every alternative records constraints
* every alternative records required evidence
* every alternative references relevant Engineering Forces
* duplicate alternatives are removed
* rejected alternatives include reasons
* option coverage is reported
* no preferred alternative is identified
* no final recommendation is generated
* no canonical artifact is modified
* the output is linked to the parent trace

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* every viable Decision Option is evaluated for alternative generation
* realistic alternatives are produced
* rejected alternatives are recorded where material
* option coverage is reported
* validation succeeds
* no unhandled blocking finding remains
* the Engineering Alternative Set is available to downstream tasks
* the task result is recorded in the execution trace

---

# Failure Conditions

The task must fail when:

* the Engineering Reasoning Context is missing
* the Engineering Forces Analysis is missing
* the Decision Option Set is missing
* no viable Decision Option exists
* no feasible alternative can be generated
* all alternatives violate project constraints
* alternatives rely entirely on unsupported assumptions
* the Engineering Question changes during execution
* output validation fails

The task must not produce fictional alternatives to avoid failure.

---

# Failure Output

```yaml
task_id: TASK-ANALYZE-0004
task_version: 0.1.0
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
status: failed

failure:
  code: no_feasible_engineering_alternatives
  description: >
    No Decision Option can currently be realized without violating approved
    project constraints.
  evidence:
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/decision-options.yaml
    - runtime/runs/RUN-REASON-20260710-0001/task_outputs/engineering-forces.yaml
  partial_output_available: true
  recovery_action: >
    Resolve the conflicting constraints or revise the Work Request before
    continuing.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent Run ID
* Engineering Reasoning Context source
* Engineering Forces Analysis source
* Decision Option Set source
* Decision Options evaluated
* alternatives generated
* alternatives rejected
* rejection reasons
* option coverage
* project evidence used
* EKB guidance used
* assumptions
* required evidence
* findings
* validation result
* output location
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace must explain the observable basis for each alternative without exposing private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly with the same:

* Engineering Reasoning Context
* Engineering Forces Analysis
* Decision Option Set
* EKB version
* ECF version

should produce a materially equivalent Alternative Set.

---

# Determinism

Expected level:

```text
Constrained
```

Wording and grouping may differ, but the following should remain materially consistent:

* major alternatives
* option-to-alternative mapping
* responsibility boundaries
* constraint compatibility
* rejected alternatives
* assumptions
* findings
* validation result

Cross-executor disagreement about the existence of a major viable alternative must be recorded and reviewed.

---

# Executor Requirements

The executor requires:

* read access to runtime outputs from prior reasoning tasks
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
* write the Engineering Alternative Set
* write findings
* update runtime trace data

Prohibited:

* modify canonical project artifacts
* modify bundled dependencies
* rank alternatives
* perform final trade-off evaluation
* generate a final recommendation
* approve engineering work
* execute production work
* create source code
* access external sources without authorization

---

# Security and Privacy

The task must:

* use only context required to generate alternatives
* avoid recording secrets or credentials
* avoid unnecessary personal information
* preserve repository boundaries
* avoid copying sensitive source content when a citation is sufficient
* identify security implications as constraints or required evidence where relevant

---

# Accessibility

Human-readable output must:

* use explicit alternative names
* explain technical alternatives in plain language
* remain understandable when read linearly
* avoid color-only distinctions
* expand uncommon abbreviations
* include text descriptions for any diagrams

---

# Metrics

Recommended metrics:

* alternative-generation success rate
* average viable-alternative count
* option-coverage rate
* rejected-alternative rate
* duplicate-alternative rejection rate
* cross-executor alternative agreement
* human-added alternative rate
* downstream trade-off coverage
* unsupported-assumption rate

Metrics exist to improve reasoning quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Repository Integration Boundary

Given:

* a valid Engineering Reasoning Context
* a valid Engineering Forces Analysis
* a valid Decision Option Set

for:

```text
Should Repository Integration become a first-class subsystem?
```

when `TASK-ANALYZE-0004` executes,

then the output should include realistic alternatives such as:

* a dedicated Repository Integration subsystem
* preserving Integration and AI ownership
* an internal repository adapter or module
* a deferred, evidence-gathering spike

The task must not rank these alternatives.

## Scenario 2 — Constraint Violation

Given an alternative that places provider-specific repository logic directly inside the provider-independent AI core,

when the task evaluates it,

then the alternative must be rejected or marked conditionally viable with the violated constraint recorded.

## Scenario 3 — Duplicate Alternatives

Given two alternatives that differ only in wording,

when the task executes,

then they must be merged or one must be rejected as a duplicate.

## Scenario 4 — Uncovered Decision Option

Given a viable Decision Option for which no realistic alternative can be generated,

when the task executes,

then option coverage must show the gap and a finding must be created.

## Scenario 5 — Speculative Alternative

Given an alternative that assumes major future growth without supporting evidence,

when the task executes,

then:

* the assumption must be explicit
* status must be `conditionally_viable` or `experimental`
* the alternative must not be presented as established architecture

---

# Guiding Principle

Generate realistic ways to realize the available Decision Options.

Do not decide which alternative is best.

This task makes candidate solutions explicit so later tasks can compare their consequences transparently.
