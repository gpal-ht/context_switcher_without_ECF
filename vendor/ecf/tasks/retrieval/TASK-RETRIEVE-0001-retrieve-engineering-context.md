---

task_id: TASK-RETRIEVE-0001
name: Retrieve Engineering Context
version: 0.1.0
status: draft
category: retrieval
owner: engineering_control_framework
idempotent: true
determinism: constrained
------------------------

# Purpose

Retrieve the project-owned engineering context required to execute a Work Request.

This task identifies, reads, validates, and assembles the smallest relevant set of project context needed by downstream reasoning and production tasks.

The task does not interpret the context, make recommendations, or modify project artifacts.

---

# Inputs

## Required Input: Work Request

The Work Request must conform to:

```text
work_requests/WORK_REQUEST_SPECIFICATION.md
```

Fields used by this task include:

* Work Request ID
* Engineering Question
* Desired Outcome
* Engineering Context Reference
* Constraints
* Requested Deliverables
* Out of Scope

## Required Input: Consumer Repository

The repository that owns the Work Request and project context.

Example:

```text
context_switcher
```

## Required Input: Engineering Context Reference

The Work Request must identify one or more project-owned context sources.

Examples:

```text
docs/engineering/ENGINEERING_CONTEXT.md
docs/architecture/SYSTEM_ARCHITECTURE.md
decisions/ADR-0002-modular-platform-architecture.md
```

## Required Input: Parent Execution Run

A valid parent orchestration or reasoning Run ID.

## Optional Input: Engineering Phase Result

Produced by:

```text
TASK-CLASSIFY-0002
Determine Engineering Phase
```

This may be used to limit context retrieval to the current phase.

## Optional Input: Engineering Intent Result

Produced by:

```text
TASK-CLASSIFY-0001
Determine Engineering Intent
```

This may be used to prioritize relevant context sources.

---

# Preconditions

Execution may begin only when:

* the Work Request exists
* the Work Request has a stable ID
* the consumer repository is known
* at least one Engineering Context Reference exists
* the referenced repository is accessible
* the parent execution Run ID exists
* vendor dependency boundaries are known
* the task has read permission for the referenced files

If any precondition fails, the task must stop and produce a failure result.

---

# Engineering Knowledge References

This task depends on:

```text
vendor/engineering_kb/foundations/ENGINEERING_PROCESS_MAP.md
vendor/engineering_kb/foundations/ENGINEERING_KNOWLEDGE_MATRIX.md
vendor/engineering_kb/foundations/ENGINEERING_TASK_MODEL.md
```

These references guide retrieval scope.

They must not be copied into the task output unless directly relevant.

---

# Retrieval Objective

Retrieve the minimum project context required to reason about the Work Request accurately.

The task should prefer:

* explicit Work Request references
* approved canonical project artifacts
* current ADRs
* current architecture documents
* relevant product documents
* relevant constraints

The task should avoid:

* unrelated source files
* generated outputs
* runtime caches
* obsolete or superseded documents
* unrelated feature documentation
* bundled dependency content unless explicitly required for provenance

---

# Execution Rules

1. Read the Work Request.
2. Extract the Engineering Question.
3. Extract the Desired Outcome.
4. Extract all Engineering Context References.
5. Resolve each reference relative to the consumer repository.
6. Verify that each referenced file exists.
7. Identify additional directly relevant project artifacts through explicit links in the referenced context.
8. Exclude unrelated project files.
9. Exclude generated, cached, runtime, and temporary artifacts.
10. Exclude vendor content from project context.
11. Read the selected context sources.
12. Record source path, artifact status, version, and commit where available.
13. Extract factual project context required by the Work Request.
14. Separate facts, constraints, assumptions, open questions, and existing decisions.
15. Record missing or contradictory context as findings.
16. Produce the Engineering Context Retrieval Result.
17. Validate the output.
18. Add the retrieval result to the parent execution trace.

The task must not infer facts that are absent from project artifacts.

---

# Context Selection Rules

## Explicit References First

Files explicitly listed in the Work Request must be evaluated first.

## Follow Canonical Relationships

The task may follow references from:

* Engineering Context documents
* ADRs
* Architecture documents
* Product documents
* Feature specifications

Relationship traversal should remain shallow unless the Work Request requires additional detail.

## Prefer Current Artifacts

When multiple documents describe the same subject, prefer:

1. approved current artifact
2. current draft
3. older non-superseded artifact
4. historical artifact only when needed

## Respect Supersession

Superseded or deprecated documents must not be treated as current project truth.

They may be included only as historical evidence and must be labeled accordingly.

## Retrieve Minimally

The task should retrieve only the context required for the current engineering question.

Repository-wide document dumps are prohibited.

---

# Project Context Categories

The retrieval result should classify extracted context into these categories.

## Project Identity

Examples:

* project name
* mission
* current phase
* product type

## Current State

Examples:

* current architecture
* implementation status
* existing subsystem boundaries
* existing workflows

## Constraints

Examples:

* technology constraints
* delivery constraints
* security constraints
* accessibility requirements
* provider-independence rules

## Existing Decisions

Examples:

* ADRs
* approved architecture choices
* accepted product principles

## Relevant Evidence

Examples:

* observed behavior
* current documents
* measurements
* implementation evidence
* experiment results

## Assumptions

Project assumptions explicitly recorded in source artifacts.

## Open Questions

Unresolved questions that may affect the engineering recommendation.

## Out-of-Scope Information

Known context that should not influence the current Work Request.

---

# Primary Output

The primary output is an Engineering Context Retrieval Result.

```yaml
task_id: TASK-RETRIEVE-0001
work_request_id: WR-0001
run_id: RUN-REASON-20260710-0001

engineering_context:
  consumer_repository: context_switcher

  project_identity:
    name: Context Switcher
    current_phase: foundation

  current_state:
    architecture_style: modular_monolith
    implementation_status: not_started
    relevant_subsystems:
      - integration
      - ai
      - knowledge

  constraints:
    - knowledge_first
    - ai_provider_independent
    - human_approval_required

  existing_decisions:
    - id: ADR-0002
      title: Modular Platform Architecture
      source: decisions/ADR-0002-modular-platform-architecture.md

  assumptions: []

  open_questions:
    - local_git_vs_github_api
    - repository_evaluation_evidence

sources:
  - path: docs/engineering/ENGINEERING_CONTEXT.md
    role: primary_context
    canonical: true

  - path: docs/architecture/SYSTEM_ARCHITECTURE.md
    role: architecture_evidence
    canonical: true

  - path: decisions/ADR-0002-modular-platform-architecture.md
    role: existing_decision
    canonical: true

findings: []

status: completed
```

The output is:

* generated
* non-canonical
* read-only for downstream tasks
* consumed by the Engineering Reasoning Engine and retrieval tasks

---

# Secondary Outputs

The task may produce:

* missing-context findings
* stale-context warnings
* contradictory-context findings
* unresolved-reference findings
* superseded-artifact warnings
* retrieval trace fragments
* recovery recommendations

Secondary outputs must not replace the primary Engineering Context Retrieval Result.

---

# Findings

Every finding must include:

* Finding ID
* Classification
* Description
* Evidence
* Required Action
* Status

Examples:

```yaml
findings:
  - id: FIND-CTX-0001
    classification: major
    description: >
      Two architecture documents define different subsystem boundaries.
    evidence:
      - docs/architecture/SYSTEM_ARCHITECTURE.md
      - docs/architecture/LEGACY_ARCHITECTURE.md
    required_action: >
      Identify the current canonical architecture before reasoning proceeds.
    status: open
```

Blocking contradictions must prevent task completion.

---

# Validation

The task passes validation only when:

* the Work Request ID is present
* the consumer repository is identified
* all selected sources exist
* every extracted fact is traceable to a source
* vendor content is excluded from project context
* generated and runtime content are excluded
* assumptions are separated from facts
* open questions are explicitly listed
* stale or conflicting context is recorded
* no unsupported project facts were introduced
* the task status is recorded
* the result is linked to the parent Run ID

---

# Completion Criteria

The task is complete when:

* all preconditions pass
* relevant context sources are resolved
* the minimum sufficient context is retrieved
* source provenance is recorded
* facts, constraints, assumptions, decisions, and open questions are separated
* validation succeeds
* no blocking findings remain
* the result is available to downstream tasks
* the task result is recorded in the execution trace

---

# Failure Conditions

The task must fail when:

* the Work Request is missing
* no Engineering Context Reference exists
* the consumer repository cannot be accessed
* referenced context files do not exist
* all referenced context is obsolete or superseded
* conflicting canonical artifacts cannot be resolved
* required context is inaccessible
* repository boundaries cannot be determined
* output validation fails

The task must not compensate for missing context by inventing project facts.

---

# Failure Output

```yaml
task_id: TASK-RETRIEVE-0001
work_request_id: WR-0001
run_id: RUN-REASON-20260710-0001
status: failed

failure:
  code: engineering_context_unavailable
  description: >
    The Work Request references an Engineering Context file that does not exist.
  evidence:
    - docs/engineering/ENGINEERING_CONTEXT.md
  partial_output_available: false
  recovery_action: >
    Create or correct the project-owned Engineering Context reference and rerun
    the task.
```

---

# Trace Requirements

The task trace must record:

* Task ID and version
* Work Request ID
* parent execution Run ID
* consumer repository
* repository commit where available
* Engineering Intent when provided
* Engineering Phase when provided
* Engineering Context References
* sources evaluated
* sources selected
* sources rejected
* rejection reasons
* extracted context categories
* assumptions
* open questions
* findings
* validation result
* final status

The trace must conform to:

```text
execution/EXECUTION_TRACE_CONTRACT.md
```

The trace must explain observable retrieval decisions without exposing private model chain-of-thought.

---

# Retrieval Boundaries

Allowed project sources include:

* canonical project documentation
* current ADRs
* approved product artifacts
* approved architecture artifacts
* current engineering context
* relevant feature specifications
* relevant experiment findings
* relevant source code only when explicitly required

Excluded by default:

* `.git/`
* `runtime/`
* `generated/`
* `cache/`
* logs
* temporary files
* local IDE settings
* unrelated source code
* vendor dependency content

Vendor dependencies may be read only to resolve framework or knowledge provenance, not as project context.

---

# Idempotency

This task is idempotent.

Running it repeatedly with the same:

* Work Request
* consumer repository commit
* Engineering Intent
* Engineering Phase
* ECF version

should produce the same selected sources and materially equivalent context output.

---

# Determinism

Expected level:

```text
Constrained
```

Wording may differ, but the following must remain materially consistent:

* selected source set
* extracted project facts
* constraints
* existing decisions
* assumptions
* open questions
* findings
* validation result

Cross-executor disagreement about source selection must be recorded and reviewed.

---

# Executor Requirements

The executor requires:

* read access to the Work Request
* read access to the consumer repository
* read access to referenced project documentation
* read access to bundled ECF
* read access to bundled EKB
* permission to write runtime task output
* permission to write runtime trace data

No network access is required.

---

# Permission Boundaries

Allowed:

* read project-owned context files
* read current ADRs
* read current architecture and product documents
* read bundled ECF and EKB for retrieval guidance
* write runtime task output
* write runtime trace data

Prohibited:

* modify project artifacts
* modify source code
* modify bundled dependencies
* access sibling repositories
* use generated package caches as canonical context
* access external sources without explicit authorization
* produce an Engineering Recommendation Report
* execute production work

---

# Security and Privacy

The task must:

* retrieve only context necessary for the Work Request
* avoid copying secrets into runtime output
* avoid recording credentials or tokens
* minimize personal information
* preserve repository boundaries
* identify sensitive sources without reproducing unnecessary content
* follow project retention and access rules

---

# Accessibility

Human-readable context output must:

* use explicit headings and labels
* distinguish facts, assumptions, and open questions in text
* avoid color-only meaning
* remain understandable when read linearly
* expand uncommon abbreviations where practical

---

# Metrics

Recommended metrics:

* context retrieval success rate
* average selected-source count
* irrelevant-source rejection rate
* missing-context rate
* stale-context finding rate
* contradictory-context finding rate
* human correction rate
* cross-executor source-selection agreement

Metrics exist to improve retrieval precision and completeness.

They must not measure individual productivity.

---

# Acceptance Tests

## Scenario 1 — Repository Integration Architecture Question

Given a Work Request asking:

```text
Should Repository Integration become a first-class subsystem?
```

and referencing:

```text
docs/engineering/ENGINEERING_CONTEXT.md
```

when `TASK-RETRIEVE-0001` executes,

then the result must include relevant project context from:

* Engineering Context
* current System Architecture
* applicable ADRs
* relevant AI or Integration architecture documents

and must exclude unrelated product and implementation documents.

## Scenario 2 — Missing Context Reference

Given a Work Request referencing a nonexistent file,

when the task executes,

then it must fail with:

```text
engineering_context_unavailable
```

and must recommend correcting or creating the context reference.

## Scenario 3 — Conflicting Architecture Sources

Given two current artifacts defining incompatible subsystem boundaries,

when the task executes,

then it must produce a blocking finding and must not mark the context as valid.

## Scenario 4 — Superseded Artifact

Given a referenced architecture artifact marked as superseded,

when a current replacement exists,

then the current artifact must be selected and the superseded artifact must be recorded only as historical context.

---

# Guiding Principle

Retrieve the smallest complete body of project-owned context required to execute the Work Request accurately.

The task must expose what the project says without interpreting what the project should do.
