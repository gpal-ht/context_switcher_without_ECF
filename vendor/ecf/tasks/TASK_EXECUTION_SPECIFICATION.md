# TASK_EXECUTION_SPECIFICATION.md

# Purpose

This specification defines the execution contract for every Engineering Task executed through the Engineering Control Framework (ECF).

Engineering Tasks are defined conceptually by the Engineering Knowledge Base.

ECF defines how those tasks are:

* invoked
* supplied with inputs
* executed
* validated
* traced
* completed
* failed

Every executable Engineering Task in ECF must conform to this specification.

---

# Core Principle

An Engineering Task performs one observable engineering operation and produces one primary output.

A Task Execution Specification defines execution behavior.

It does not redefine the underlying engineering knowledge.

---

# Relationship to EKB

The Engineering Knowledge Base defines:

* what an Engineering Task is
* why the task matters
* the engineering reasoning involved
* what good task performance looks like

ECF defines:

* required execution inputs
* permitted outputs
* execution rules
* validation requirements
* trace requirements
* failure behavior

ECF may reference EKB guidance but must not duplicate it unnecessarily.

---

# Task Execution Characteristics

Every executable task must be:

* atomic
* observable
* traceable
* independently testable
* reusable
* deterministic where practical
* explicit about failure

A task should not perform multiple unrelated operations.

---

# Required Task Structure

Every Task Execution Specification must contain the following sections.

---

# 1. Identity

Required fields:

* Task ID
* Name
* Version
* Status
* Category
* Owner

Recommended Task ID format:

```text
TASK-<CATEGORY>-<NUMBER>
```

Examples:

```text
TASK-CLASSIFY-0001
TASK-RETRIEVE-0001
TASK-ANALYZE-0001
TASK-PRODUCE-0001
TASK-VALIDATE-0001
```

Allowed status values:

* draft
* review
* approved
* released
* deprecated
* superseded
* archived

---

# 2. Purpose

Describe:

* why the task exists
* which engineering operation it performs
* which larger transformations use it

The purpose must describe exactly one primary operation.

---

# 3. Task Category

Recommended categories include:

## Classification

Examples:

* Determine Engineering Intent
* Determine Engineering Phase
* Classify Work Request

## Retrieval

Examples:

* Retrieve Engineering Context
* Request Engineering Knowledge
* Resolve Artifact Dependencies

## Analysis

Examples:

* Analyze Context
* Analyze Constraints
* Evaluate Alternatives
* Analyze Trade-offs
* Identify Risks

## Decision Support

Examples:

* Assess Confidence
* Generate Recommendation
* Identify Missing Information

## Production

Examples:

* Load Template
* Generate Artifact Sections
* Render Derived Artifact

## Validation

Examples:

* Validate Metadata
* Validate Artifact Structure
* Validate Standards Compliance

## Traceability

Examples:

* Record Evidence
* Generate Execution Trace
* Generate Output Manifest

New categories should be introduced only when existing categories are insufficient.

---

# 4. Inputs

List every required and optional input.

Each input must declare:

* Input ID or name
* Input type
* Required or optional
* Source
* Validation rule
* Purpose within the task

Example:

```yaml
inputs:
  - name: engineering_context
    type: engineering_context
    required: true
    source: consuming_project
    validation:
      - engineering_question_exists
```

Tasks must not silently obtain undeclared inputs.

---

# 5. Preconditions

Define all conditions that must be true before execution begins.

Examples:

* required inputs exist
* input versions are known
* bundled dependencies are available
* preceding task completed successfully
* approval exists
* required execution state is active

If a precondition is not satisfied, the task must not proceed.

---

# 6. Engineering Knowledge References

Identify EKB objects or foundational guidance required to perform the task correctly.

References may include:

* Decision Guides
* Concepts
* Patterns
* Quality Attributes
* Engineering Task guidance
* Engineering Process Map
* Knowledge Matrix

References should use stable IDs or versioned repository paths.

This section defines knowledge dependencies.

It does not contain copied engineering knowledge.

---

# 7. Execution Rules

Define the observable rules governing task execution.

Rules must be:

* precise
* ordered where sequence matters
* testable
* provider-independent
* implementation-neutral where practical

Execution rules describe what must occur.

They should not expose private model chain-of-thought.

Example:

```text
1. Read the engineering question from Engineering Context.
2. Identify the requested engineering outcome.
3. Compare the outcome against the approved intent taxonomy.
4. Select exactly one primary intent.
5. Record secondary intents separately when applicable.
6. Produce the Engineering Intent output.
```

---

# 8. Primary Output

Every task must produce exactly one primary output.

The primary output must declare:

* Output ID or type
* Required structure
* Validation criteria
* Canonical or generated status
* Expected consumer

Example:

```yaml
primary_output:
  type: engineering_intent
  canonical: false
  consumer: engineering_orchestration_engine
```

A task may produce supporting runtime files, but it must still have one clearly identified primary output.

## Output Ownership Versus Workflow Binding

A task owns the **type, structure, and semantics** of its primary output.

A Workflow owns the **concrete filename and path** used for that output within a run, per `workflows/WORKFLOW_EXECUTION_SPECIFICATION.md`.

* A task specification may recommend a filename, but the Workflow binding is authoritative for a run.
* Tasks do not own execution sequence and do not select their successor; the Workflow determines task order and dependencies.
* When a task's recommended filename differs from the Workflow binding, the Workflow binding governs the run.

This keeps tasks atomic and reusable across workflows while allowing each Workflow to bind stable, run-specific output paths.

## Environment Dependencies

A task declares which environment identities its provenance must pin — at minimum
**ECF**, and **EKB** when the task reads or derives its output directly from the
bundled Engineering Knowledge Base. This declaration is **authoritative**: the
read-only planner decides whether EKB validation applies from the task/workflow
contract (surfaced in the workflow's `environment_dependencies` block), never
from the provenance record being validated. A record therefore cannot omit its
EKB fields to bypass an EKB-required check. In `WF-REASON-0001` only
`TASK-RETRIEVE-0002` reads the EKB directly and requires EKB identity.

---

# 9. Secondary Outputs

Optional secondary outputs may include:

* findings
* warnings
* trace fragments
* metrics
* diagnostics

Secondary outputs must not replace the primary output.

---

# 10. Validation

Define how successful task execution is verified.

Validation should address:

* output presence
* output structure
* input-to-output traceability
* allowed value compliance
* completeness
* standards compliance
* relationship integrity

Validation may be:

* automated
* manual
* hybrid

A task is not complete until validation succeeds.

---

# 11. Completion Criteria

Define every condition required for the task to be marked complete.

Examples:

* primary output exists
* output validation passes
* required trace data recorded
* no blocking findings remain
* output is available to the next task

Completion criteria must be objective.

---

# 12. Failure Conditions

Define known reasons for failure.

Examples:

* missing required input
* invalid input structure
* ambiguous classification
* conflicting evidence
* unsupported output value
* missing EKB dependency
* validation failure
* executor unavailable

Tasks must fail explicitly.

They must not replace missing evidence with unsupported assumptions.

---

# 13. Failure Output

A failed task should produce an observable failure result containing:

* Task ID
* Run ID
* Failure classification
* Failure description
* Failed precondition or rule
* Available evidence
* Partial output status
* Recommended recovery action

Failure output is a runtime artifact.

---

# 14. Trace Requirements

Every task execution must contribute to an execution trace conforming to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

At minimum, the task trace must record:

* Task ID and version
* Run ID
* Executor
* Start and completion time
* Inputs consumed
* EKB references used
* Execution rules applied
* Primary output produced
* Validation result
* Findings
* Final task status

The trace must explain observable reasoning and evidence without exposing private model chain-of-thought.

---

# 15. Allowed Task Status Values

Task executions may use:

* requested
* running
* completed
* completed_with_findings
* failed
* cancelled
* abandoned
* superseded

Task status must be included in the parent execution trace.

---

# 16. Idempotency

Every Task Execution Specification must state whether the task is idempotent.

An idempotent task can be safely repeated with the same inputs without creating inconsistent results.

Examples:

Usually idempotent:

* Determine Engineering Intent
* Validate Metadata
* Retrieve Engineering Knowledge

Potentially non-idempotent:

* Promote Artifact
* Assign Sequential Artifact ID
* Modify Canonical Document

Non-idempotent tasks require additional safeguards.

---

# 17. Determinism

Every task must describe its expected determinism level.

Recommended levels:

## Deterministic

The same valid inputs should produce the same output.

## Constrained

The wording may differ, but structure, classification, evidence, and conclusion should remain materially consistent.

## Judgment-Based

Different valid outputs may exist, but all must satisfy the same engineering criteria.

Tasks should be deterministic or constrained whenever practical.

Judgment-based tasks require stronger validation and review.

---

# 18. Executor Requirements

Specify any required executor capabilities.

Examples:

* repository read access
* file creation permission
* diagram generation capability
* ability to run tests
* ability to retrieve bundled EKB content

Tasks must use the least authority required.

---

# 19. Permission Boundaries

Every task must declare allowed and prohibited actions.

Examples:

Allowed:

* read project engineering documents
* read bundled ECF and EKB files
* write runtime trace files

Prohibited:

* modify vendor dependencies
* modify canonical project artifacts
* access external sources without approval
* execute code
* create implementation files

Permission boundaries must align with the task’s purpose.

---

# 20. Composition Rules

Tasks may be composed into Engineering Transformations.

A transformation may invoke a task only when:

* the task specification is released or explicitly approved
* required inputs are available
* prior dependencies have completed
* task outputs are compatible with downstream inputs

Transformations should not redefine task behavior.

They should reference Task IDs and versions.

---

# 21. Versioning

Task Execution Specifications use semantic versioning.

## Major

Breaking change to:

* input contract
* primary output contract
* execution meaning
* failure behavior

## Minor

Backward-compatible addition such as:

* new optional input
* additional validation
* new trace metadata

## Patch

Clarification or correction that does not change execution behavior.

Transformations should pin compatible task versions.

---

# 22. Metrics

Recommended task metrics include:

* execution duration
* validation success rate
* failure rate
* retry count
* output revision count
* executor agreement
* human override rate

Metrics exist to improve task quality.

They must not be used to measure individual human productivity.

---

# 23. Security and Privacy

Tasks must:

* avoid recording secrets
* minimize collected context
* preserve repository boundaries
* respect vendor read-only rules
* avoid unnecessary personal information
* record external access when permitted

Sensitive inputs must be identified explicitly.

---

# 24. Accessibility

Human-readable task outputs and traces should be:

* clearly structured
* understandable without visual-only cues
* readable with assistive technologies
* free of unexplained abbreviations where practical

Generated diagrams or visual outputs require accessible text alternatives.

---

# Task Execution Lifecycle

```text
Defined
    ↓
Reviewed
    ↓
Approved
    ↓
Released
    ↓
Invoked
    ↓
Running
    ↓
Validated
    ↓
Completed
```

Failure, cancellation, abandonment, or supersession may occur during execution.

---

# Definition of a Valid Task Execution

A Task Execution is valid only when:

* the Task Execution Specification is identified
* required inputs are present
* preconditions pass
* permission boundaries are respected
* execution rules are followed
* one primary output is produced
* validation passes
* trace requirements are satisfied
* final status is recorded

---

# Guiding Principle

An Engineering Task is complete only when its input, operation, output, validation, and trace are all observable.

ECF must never rely on an invisible or unstructured AI action as an engineering task.
