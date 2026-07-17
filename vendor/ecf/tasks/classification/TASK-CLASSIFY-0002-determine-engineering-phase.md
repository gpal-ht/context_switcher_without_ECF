---

task_id: TASK-CLASSIFY-0002
name: Determine Engineering Phase
version: 0.1.0
status: draft
category: classification
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Determine the current Engineering Phase for a Work Request.

The Engineering Phase identifies where the requested work belongs within the software engineering process.

The selected phase helps ECF determine:

* relevant engineering knowledge
* appropriate tasks
* applicable transformations
* required reviews
* expected outputs

This task classifies the current work.

It does not perform the work.

---

# Inputs

## Required Input: Engineering Intent

The Engineering Intent result must be produced by:

```text
TASK-CLASSIFY-0001
Determine Engineering Intent
```

Required fields:

```yaml
engineering_intent:
  primary: design_solution
  secondary: []
```

## Required Input: Work Request

The Work Request must conform to:

```text
work_requests/WORK_REQUEST_SPECIFICATION.md
```

Fields used by this task include:

* Work Request ID
* Engineering Question
* Desired Outcome
* Requested Deliverables

## Required Input: Engineering Process Map

Source:

```text
vendor/engineering_kb/foundations/ENGINEERING_PROCESS_MAP.md
```

The bundled EKB version is authoritative for the execution run.

## Optional Input: Engineering Context

Project-owned Engineering Context may be used when the phase cannot be determined from the Work Request and Engineering Intent alone.

The task must not invent missing project facts.

---

# Preconditions

Execution may begin only when:

* a valid Work Request exists
* `TASK-CLASSIFY-0001` completed successfully
* exactly one primary Engineering Intent exists
* the Engineering Process Map is available
* bundled EKB version information is available
* the parent execution Run ID exists

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task depends on:

```text
vendor/engineering_kb/foundations/ENGINEERING_PROCESS_MAP.md
vendor/engineering_kb/foundations/ENGINEERING_INTENT_MODEL.md
vendor/engineering_kb/foundations/ENGINEERING_KNOWLEDGE_MATRIX.md
```

The task must reference these files rather than redefine the engineering process.

---

# Execution Rules

1. Read the primary Engineering Intent.
2. Read the Work Request’s Engineering Question.
3. Read the Desired Outcome.
4. Read the Requested Deliverables.
5. Load the Engineering Process Map from the bundled EKB.
6. Map the primary Engineering Intent to the corresponding Engineering Phase.
7. Verify that the Desired Outcome is consistent with the selected phase.
8. Record any downstream phases suggested by the request separately.
9. Record the evidence supporting the phase classification.
10. Produce exactly one current Engineering Phase.
11. Validate the phase against the bundled Engineering Process Map.
12. Add the task result to the parent execution trace.

The current Engineering Phase must represent the work that should happen now.

A future intended phase must not replace the current phase.

---

# Intent-to-Phase Mapping

The authoritative definitions remain in the bundled EKB.

The expected mapping is:

| Engineering Intent   | Engineering Phase |
| -------------------- | ----------------- |
| `discover_problem`   | `discover`        |
| `understand_problem` | `understand`      |
| `define_problem`     | `define`          |
| `design_solution`    | `design`          |
| `validate_solution`  | `validate`        |
| `plan_work`          | `plan`            |
| `implement_solution` | `implement`       |
| `verify_solution`    | `verify`          |
| `capture_learning`   | `learn`           |

If the bundled EKB defines a different mapping, the bundled EKB is authoritative.

---

# Primary Output

The primary output is an Engineering Phase result.

```yaml
task_id: TASK-CLASSIFY-0002
work_request_id: WR-0001

engineering_phase:
  current: design
  downstream:
    - validate
    - plan

classification_evidence:
  primary_intent: design_solution
  engineering_question: >
    Should Repository Integration become a first-class subsystem?
  desired_outcome: Engineering Recommendation Report

confidence:
  level: high
  justification: >
    The request evaluates a proposed architectural boundary before implementation.

status: completed
```

The output is:

* generated
* non-canonical
* consumed by the Engineering Orchestration Engine
* available to knowledge-retrieval tasks

---

# Allowed Current Phase Values

The output must use a phase defined by the bundled Engineering Process Map.

Current expected values are:

```text
discover
understand
define
design
validate
plan
implement
verify
learn
```

The bundled EKB remains authoritative if this list changes.

---

# Phase Classification Guidance

## `discover`

Use when the immediate work determines whether a meaningful problem or opportunity exists.

Typical outputs:

* Problem Statement
* Opportunity Description

## `understand`

Use when the immediate work builds knowledge of a domain, user, system, constraint, or stakeholder.

Typical outputs:

* Domain Understanding
* Constraint Analysis
* Stakeholder Understanding

## `define`

Use when the immediate work establishes precise intent, scope, success criteria, or problem boundaries.

Typical outputs:

* Problem Definition
* Scope Definition
* Success Criteria

## `design`

Use when the immediate work proposes or evaluates solution structure before formal validation.

Typical outputs:

* Product Design
* System Design
* Runtime Design
* Data Design
* Engineering Recommendation about a proposed solution

## `validate`

Use when an existing proposed solution is being challenged, reviewed, or assessed.

Typical outputs:

* Architecture Review
* Threat Model
* Accessibility Assessment
* Risk Assessment

## `plan`

Use when approved engineering work is being sequenced or prepared for execution.

Typical outputs:

* Delivery Plan
* Work Breakdown
* Test Strategy
* Dependency Plan

## `implement`

Use when approved engineering knowledge is being converted into working software, configuration, or infrastructure.

Typical outputs:

* Source Code
* Configuration
* Infrastructure Definitions

## `verify`

Use when completed implementation is being evaluated against approved engineering intent.

Typical outputs:

* Test Results
* Verification Report
* QA Findings

## `learn`

Use when the immediate work captures reusable knowledge from completed or interrupted engineering activity.

Typical outputs:

* Retrospective
* ADR Update
* Reusable Example
* Framework Improvement

---

# Distinguishing Design from Validate

This distinction must be handled carefully.

Classify as `design` when the request asks:

* what should the solution be?
* which boundary should exist?
* which architecture should be selected?
* how should responsibilities be assigned?

Classify as `validate` when the request asks:

* is this proposed solution sound?
* does this design satisfy standards?
* should this completed design be approved?
* what risks exist in this proposed design?

Example:

```text
Should Repository Integration become a subsystem?
```

Result:

```yaml
current: design
```

Example:

```text
Review the proposed Repository Integration subsystem design.
```

Result:

```yaml
current: validate
```

---

# Distinguishing Define from Design

Classify as `define` when the request clarifies:

* the problem
* scope
* success
* requirements
* engineering intent

Classify as `design` when the request proposes:

* architecture
* components
* interfaces
* runtime behavior
* technical boundaries

Example:

```text
Define what repository-aware work evaluation must achieve.
```

Result:

```yaml
current: define
```

Example:

```text
Design repository-aware work evaluation.
```

Result:

```yaml
current: design
```

---

# Downstream Phases

The task may identify expected downstream phases.

Example:

```yaml
engineering_phase:
  current: design
  downstream:
    - validate
    - plan
```

Downstream phases are informational.

They do not authorize future execution.

Each downstream phase requires orchestration and applicable approval gates.

---

# Secondary Outputs

The task may produce:

* ambiguity findings
* phase-transition observations
* inconsistent-outcome warnings
* downstream-phase suggestions
* recovery recommendations
* trace fragments

Secondary outputs must not replace the primary Engineering Phase result.

---

# Validation

The task passes validation only when:

* exactly one current Engineering Phase exists
* the phase exists in the bundled Engineering Process Map
* the phase is compatible with the primary Engineering Intent
* the phase is consistent with the immediate Desired Outcome
* downstream phases are clearly separated
* classification evidence is recorded
* confidence justification is present
* no unsupported project facts were introduced
* task status is recorded
* the result references the Work Request ID

---

# Completion Criteria

The task is complete when:

* all preconditions passed
* one current Engineering Phase was selected
* validation succeeded
* the result was recorded in the execution trace
* the result is available to downstream tasks

---

# Failure Conditions

The task must fail when:

* the Work Request is missing
* the Engineering Intent result is missing
* multiple primary Engineering Intents exist
* the Engineering Process Map cannot be loaded
* the selected intent cannot be mapped to a phase
* the Desired Outcome conflicts materially with the selected phase
* multiple current phases remain equally plausible
* output validation fails

---

# Failure Output

```yaml
task_id: TASK-CLASSIFY-0002
work_request_id: WR-0001
status: failed

failure:
  code: ambiguous_engineering_phase
  description: >
    The request may be asking either for creation of a new design or validation
    of an existing design.
  evidence:
    - path/to/work-request.md
  recovery_action: >
    Clarify whether the desired outcome is a design proposal or a formal review.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent execution Run ID
* bundled EKB version and commit
* primary Engineering Intent
* Engineering Question
* Desired Outcome
* Requested Deliverables
* process-map source
* selected current phase
* downstream phases
* classification evidence
* alternative phases rejected
* ambiguity findings
* confidence
* validation result
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace explains the observable classification basis without exposing private model chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it repeatedly with the same:

* Work Request
* Engineering Intent result
* Engineering Context
* EKB version

should produce the same current Engineering Phase.

---

# Determinism

Expected level:

```text
Constrained
```

Wording may differ, but the following must remain materially consistent:

* current Engineering Phase
* relationship to the primary intent
* downstream-phase separation
* evidence cited
* ambiguity findings
* validation result

Cross-executor disagreement must be recorded and reviewed.

---

# Executor Requirements

The executor requires:

* read access to the Work Request
* read access to the Engineering Intent result
* read access to project Engineering Context when provided
* read access to bundled ECF
* read access to bundled EKB
* permission to write runtime task output and trace data

No network access is required.

---

# Permission Boundaries

Allowed:

* read Work Request files
* read runtime classification outputs
* read project Engineering Context
* read bundled ECF
* read bundled EKB
* write runtime task output
* write runtime trace data

Prohibited:

* modify canonical project artifacts
* modify bundled dependencies
* retrieve Engineering Knowledge Packages
* generate engineering recommendations
* execute production work
* modify source code
* access external sources without authorization

---

# Security and Privacy

The task must:

* process only context required for phase classification
* avoid recording secrets or credentials
* avoid unnecessary personal information
* preserve repository boundaries
* avoid copying sensitive context into traces unnecessarily

---

# Accessibility

Human-readable output must:

* use explicit labels
* explain phase values in plain language
* remain understandable when read linearly
* avoid relying on visual formatting alone

---

# Metrics

Recommended metrics:

* successful phase-classification rate
* ambiguous phase rate
* intent-to-phase consistency
* cross-executor agreement
* human override rate
* retry count
* failure reason distribution

Metrics exist to improve task quality.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Architecture Boundary Decision

Given:

```text
Engineering Question:
Should Repository Integration become a first-class subsystem?

Primary Engineering Intent:
design_solution
```

When `TASK-CLASSIFY-0002` executes,

then:

```yaml
engineering_phase:
  current: design
```

## Scenario 2 — Architecture Review

Given:

```text
Engineering Question:
Review the proposed Repository Integration subsystem design.

Primary Engineering Intent:
validate_solution
```

Then:

```yaml
engineering_phase:
  current: validate
```

## Scenario 3 — Implementation

Given:

```text
Engineering Question:
Implement the approved repository scanner design.

Primary Engineering Intent:
implement_solution
```

Then:

```yaml
engineering_phase:
  current: implement
```

## Scenario 4 — Learning

Given:

```text
Engineering Question:
Capture lessons from the repository integration experiment.

Primary Engineering Intent:
capture_learning
```

Then:

```yaml
engineering_phase:
  current: learn
```

---

# Guiding Principle

This task identifies where the immediate work belongs in the Engineering Process.

It must classify the current phase predictably without executing that phase.
