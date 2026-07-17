# Build Engineering Reasoning Context

## Identity

Task ID

TASK-ANALYZE-0001

Version

0.1.0

Status

Draft

Category

Analysis

Owner

Engineering Control Framework

---

# Purpose

Construct the Engineering Reasoning Context (ERC).

The Engineering Reasoning Context is the runtime working set used by all downstream reasoning tasks.

It combines:

* Engineering Intent
* Engineering Phase
* Engineering Context
* Engineering Knowledge Package

into a single coherent engineering reasoning object.

The Engineering Reasoning Context is generated.

It is not canonical.

It exists only for the lifetime of the current reasoning run.

---

# Philosophy

Engineering reasoning should operate on one coherent engineering context.

Downstream reasoning tasks should not repeatedly retrieve or merge engineering knowledge.

The Engineering Reasoning Context exists to reduce coupling between reasoning tasks.

---

# Inputs

## Required

Engineering Intent Result

Produced by:

```text
TASK-CLASSIFY-0001
```

---

Engineering Phase Result

Produced by:

```text
TASK-CLASSIFY-0002
```

---

Engineering Context Retrieval Result

Produced by:

```text
TASK-RETRIEVE-0001
```

---

Engineering Knowledge Package

Produced by:

```text
TASK-RETRIEVE-0002
```

---

Parent Run ID

---

# Preconditions

The following tasks must have completed successfully:

* TASK-CLASSIFY-0001
* TASK-CLASSIFY-0002
* TASK-RETRIEVE-0001
* TASK-RETRIEVE-0002

All inputs must validate successfully.

---

# Engineering Knowledge References

This task references:

* Engineering Process Map
* Engineering Knowledge Matrix
* Engineering Task Model

These references guide context construction.

They are not copied into the Engineering Reasoning Context.

---

# Execution Rules

1. Read Engineering Intent.
2. Read Engineering Phase.
3. Read Engineering Context.
4. Read Engineering Knowledge Package.
5. Validate all inputs.
6. Merge project context with engineering knowledge.
7. Preserve provenance of every engineering fact.
8. Preserve provenance of every engineering recommendation.
9. Preserve assumptions separately.
10. Preserve open questions separately.
11. Produce one Engineering Reasoning Context.
12. Validate the resulting context.
13. Record execution trace.

The task must never merge project facts with engineering guidance into a single indistinguishable representation.

---

# Context Structure

The Engineering Reasoning Context shall contain:

## Engineering Intent

Exactly one primary intent.

---

## Engineering Phase

Exactly one current engineering phase.

---

## Engineering Question

The engineering question being evaluated.

---

## Project Facts

Project-owned facts retrieved from the Engineering Context.

Examples:

* architecture
* subsystem boundaries
* implementation status
* constraints

---

## Engineering Guidance

Engineering guidance retrieved from the Engineering Knowledge Package.

Examples:

* Decision Guide
* Concepts
* Patterns
* Quality Attributes
* Examples

---

## Assumptions

Explicit assumptions.

Assumptions must never appear as facts.

---

## Open Questions

Engineering uncertainty remaining before reasoning.

---

## Findings

Existing findings inherited from previous tasks.

---

# Primary Output

Engineering Reasoning Context

Example:

```yaml
run_id: RUN-REASON-20260710-0001

engineering_intent:
  primary: design_solution

engineering_phase:
  current: design

engineering_question: >
  Should Repository Integration become a first-class subsystem?

project_facts:
  architecture_style: modular_monolith
  implementation_status: foundation
  repository_integration_in_mvp: false

engineering_guidance:
  decision_guide:
    DG-ARCH-0001

  concepts:
    - CON-ARCH-0001
    - CON-ARCH-0002
    - CON-ARCH-0003

  pattern:
    PAT-ARCH-0001

  quality_attributes:
    - QA-0001
    - QA-0002

assumptions: []

open_questions:
  - local_git_vs_github_api

findings: []

status: completed
```

---

# Validation

Verify:

* Engineering Intent present.
* Engineering Phase present.
* Engineering Context present.
* Engineering Knowledge Package present.
* Project facts separated from engineering guidance.
* Assumptions separated from facts.
* Open questions preserved.
* Provenance preserved.

---

# Completion Criteria

The task completes when:

* one Engineering Reasoning Context exists
* validation succeeds
* trace updated

---

# Failure Conditions

Examples:

* missing Engineering Context
* missing Engineering Knowledge Package
* invalid input
* conflicting context
* conflicting engineering guidance

---

# Trace Requirements

Record:

* inputs consumed
* merge operation
* inherited findings
* validation
* output identifier
* final status

The trace records the observable merge.

It does not expose private model reasoning.

---

# Executor Requirements

Requires:

* read access to runtime outputs from previous tasks
* read access to bundled ECF
* read access to bundled EKB
* permission to write runtime outputs

---

# Permission Boundaries

Allowed:

* read runtime task outputs
* write Engineering Reasoning Context
* write runtime trace

Prohibited:

* modify project artifacts
* modify bundled repositories
* generate engineering recommendations
* execute production work

---

# Idempotency

Yes.

---

# Determinism

Constrained.

The Engineering Reasoning Context should remain materially identical for identical validated inputs.

---

# Metrics

Recommended:

* merge success rate
* validation success rate
* conflicting context rate
* missing context rate

---

# Acceptance Test

Given:

* valid Engineering Intent
* valid Engineering Phase
* valid Engineering Context
* valid Engineering Knowledge Package

When:

TASK-ANALYZE-0001 executes

Then:

One valid Engineering Reasoning Context shall be produced.

Every project fact shall remain distinguishable from engineering guidance.

No engineering recommendation shall yet exist.

---

# Guiding Principle

The Engineering Reasoning Context is the single runtime working model for the Engineering Reasoning Engine.

Every downstream reasoning task consumes this context rather than independently retrieving or merging engineering knowledge.
