---

task_id: TASK-CLASSIFY-0001
name: Determine Engineering Intent
version: 0.1.0
status: draft
category: classification
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Classify a Work Request according to the Engineering Intent Model defined by the bundled Engineering Knowledge Base.

This task identifies why engineering work is being requested.

It produces one primary Engineering Intent value for use by the Engineering Orchestration Engine.

This task does not select a workflow, produce a recommendation, or modify project artifacts.

---

# Inputs

## Required Input: Work Request

The Work Request must conform to:

```text
work_requests/WORK_REQUEST_SPECIFICATION.md
```

Required fields used by this task:

* Work Request ID
* Engineering Question
* Desired Outcome
* Requested Deliverables

## Required Input: Engineering Intent Model

Source:

```text
vendor/engineering_kb/foundations/ENGINEERING_INTENT_MODEL.md
```

The bundled EKB version is authoritative for the execution run.

## Optional Input: Engineering Context

A project-owned Engineering Context may be used to resolve ambiguity.

The task must not infer unsupported project facts.

---

# Preconditions

Execution may begin only when:

* the Work Request exists
* the Work Request has a stable ID
* exactly one primary Engineering Question is present
* the Desired Outcome is present
* the bundled Engineering Intent Model is available
* the bundled dependency version is known

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task depends on:

```text
vendor/engineering_kb/foundations/ENGINEERING_INTENT_MODEL.md
vendor/engineering_kb/foundations/ENGINEERING_PROCESS_MAP.md
vendor/engineering_kb/foundations/ENGINEERING_KNOWLEDGE_MATRIX.md
```

The task must reference these files rather than duplicating their engineering definitions.

---

# Execution Rules

1. Read the Work Request.
2. Extract the Engineering Question.
3. Extract the Desired Outcome.
4. Extract the Requested Deliverables.
5. Load the Engineering Intent taxonomy from the bundled EKB.
6. Compare the requested outcome with the purpose of each permitted intent.
7. Select exactly one primary Engineering Intent.
8. Record secondary intents only when they materially affect downstream work.
9. Record the evidence used for classification.
10. Record ambiguity or missing information as findings.
11. Produce the Engineering Intent result.
12. Validate the result against the bundled taxonomy.
13. Add the task result to the parent execution trace.

The task must not select an intent based only on keywords when the Desired Outcome provides clearer evidence.

---

# Primary Output

The primary output is an Engineering Intent result.

When produced by an AI-backed executor (`tools/task_runner/executors/claude-code`),
the runtime output is a machine-readable JSON envelope conforming to
`runtime_schemas/ENGINEERING_INTENT_RESULT_SCHEMA.md`, committed to the bound path
`task_outputs/engineering-intent.yaml`. Allowed intent values are authoritative from
the bundled EKB Engineering Intent Model. The example below is illustrative.

```yaml
task_id: TASK-CLASSIFY-0001
work_request_id: WR-0001

engineering_intent:
  primary: design_solution
  secondary: []

classification_evidence:
  engineering_question: >
    Should Repository Integration become a first-class subsystem?
  desired_outcome: Engineering Recommendation Report
  requested_deliverables:
    - engineering_recommendation_report

confidence:
  level: high
  justification: >
    The request asks for evaluation of a proposed architectural boundary.

status: completed
```

The output is:

* generated
* non-canonical
* consumed by the Engineering Orchestration Engine

---

# Allowed Primary Intent Values

The output must use a value defined by the bundled Engineering Intent Model.

Current expected values are:

```text
discover_problem
understand_problem
define_problem
design_solution
validate_solution
plan_work
implement_solution
verify_solution
capture_learning
```

The bundled EKB remains authoritative if this list changes.

---

# Classification Guidance

## `discover_problem`

Use when the requested outcome is to determine whether a problem or opportunity exists.

## `understand_problem`

Use when the requested outcome is greater understanding of an existing problem, domain, stakeholder, system, or constraint.

## `define_problem`

Use when the requested outcome is a precise problem definition, scope boundary, or success definition.

## `design_solution`

Use when the requested outcome is a proposed architecture, design, responsibility boundary, interaction model, or technical approach.

## `validate_solution`

Use when the requested outcome is evaluation or review of an already proposed solution.

## `plan_work`

Use when the requested outcome is sequencing, dependency planning, delivery planning, or work decomposition.

## `implement_solution`

Use when approved engineering knowledge is to be converted into software or configuration.

## `verify_solution`

Use when the requested outcome is evidence that implementation satisfies approved intent.

## `capture_learning`

Use when the requested outcome is preservation of lessons, decisions, findings, or reusable engineering knowledge.

---

# Ambiguity Rules

A Work Request may appear to contain multiple intents.

The task must select the intent corresponding to the immediate requested outcome.

Example:

```text
Question:
Should Repository Integration become a subsystem?

Future goal:
Implement Repository Integration.
```

Classification:

```yaml
primary: design_solution
secondary:
  - implement_solution
```

The future goal does not replace the immediate intent.

If two intents remain equally plausible after reading the complete Work Request and Engineering Context, the task must fail with:

```text
ambiguous_engineering_intent
```

It must not choose arbitrarily.

---

# Examples

## Architecture Boundary Question

Input:

```text
Should Repository Integration become a first-class subsystem?
```

Output:

```yaml
primary: design_solution
secondary: []
```

## Architecture Review

Input:

```text
Review the proposed Repository Integration subsystem design.
```

Output:

```yaml
primary: validate_solution
secondary: []
```

## Requirements Definition

Input:

```text
Define the problem and success criteria for repository-aware work evaluation.
```

Output:

```yaml
primary: define_problem
secondary: []
```

## Implementation Request

Input:

```text
Implement the approved repository scanner design.
```

Output:

```yaml
primary: implement_solution
secondary: []
```

---

# Secondary Outputs

The task may produce:

* ambiguity warnings
* missing-context findings
* classification alternatives
* recovery recommendations
* trace fragments

Secondary outputs must not replace the primary Engineering Intent output.

---

# Validation

The task passes validation only when:

* exactly one primary intent exists
* the primary intent is present in the bundled taxonomy
* every secondary intent is present in the bundled taxonomy
* classification evidence is recorded
* confidence justification is present
* no unsupported project facts were introduced
* task status is recorded
* the result is linked to the Work Request ID

---

# Completion Criteria

The task is complete when:

* all preconditions passed
* one primary intent was selected
* validation succeeded
* the result was recorded in the execution trace
* the result is available to the Orchestration Engine

---

# Failure Conditions

The task must fail when:

* the Work Request is missing
* the Engineering Question is missing
* the Desired Outcome is missing
* the bundled Engineering Intent Model cannot be loaded
* no taxonomy value applies
* multiple primary intents remain equally valid
* output validation fails

---

# Failure Output

```yaml
task_id: TASK-CLASSIFY-0001
work_request_id: WR-0001
status: failed

failure:
  code: ambiguous_engineering_intent
  description: >
    The request equally supports design_solution and validate_solution.
  evidence:
    - path/to/work-request.md
  recovery_action: >
    Clarify whether the request is asking for a new design or a review of an existing design.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* execution Run ID
* bundled EKB version and commit
* Engineering Question
* Desired Outcome
* taxonomy source
* selected primary intent
* secondary intents
* classification evidence
* alternatives rejected
* ambiguity findings
* confidence
* validation result
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace explains the observable classification basis. It must not request or expose private chain-of-thought.

---

# Idempotency

This task is idempotent.

Running it again with the same:

* Work Request
* Engineering Context
* EKB version

should produce the same primary intent.

---

# Determinism

Expected level:

```text
Constrained
```

Wording may differ, but the following must remain materially consistent:

* selected primary intent
* secondary intent selection
* evidence cited
* ambiguity findings
* validation result

Cross-executor disagreement must be recorded and reviewed.

---

# Executor Requirements

The executor requires:

* read access to the Work Request
* read access to project Engineering Context when provided
* read access to bundled ECF
* read access to bundled EKB
* permission to write runtime trace data

No network access is required.

---

# Permission Boundaries

Allowed:

* read Work Request files
* read project Engineering Context
* read bundled ECF
* read bundled EKB
* write runtime task output
* write runtime trace data

Prohibited:

* modify canonical project artifacts
* modify bundled dependencies
* generate an Engineering Recommendation Report
* execute production work
* modify source code
* access external sources without explicit authorization

---

# Security and Privacy

The task must:

* record only context needed for classification
* avoid secrets and credentials
* avoid unnecessary personal data
* preserve repository boundaries
* identify sensitive inputs without copying their contents unnecessarily

---

# Accessibility

Human-readable output must:

* use explicit labels
* avoid color-only meaning
* remain understandable when read linearly
* explain taxonomy values in plain language when presented to humans

---

# Metrics

Recommended metrics:

* successful classification rate
* ambiguous classification rate
* cross-executor agreement
* human override rate
* retry count
* failure reason distribution

Metrics should improve task quality, not measure individual productivity.

---

# Acceptance Test

## Scenario

Given a Work Request asking:

```text
Should Repository Integration become a first-class subsystem?
```

with the desired output:

```text
Engineering Recommendation Report
```

when `TASK-CLASSIFY-0001` executes,

then the primary Engineering Intent must be:

```yaml
primary: design_solution
```

and the result must reference the Work Request and bundled EKB taxonomy.

---

# Guiding Principle

This task classifies the immediate purpose of engineering work.

It must identify intent predictably without performing the engineering work itself.
