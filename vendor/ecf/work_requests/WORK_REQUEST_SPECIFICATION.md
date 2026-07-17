# WORK_REQUEST_SPECIFICATION.md

# Purpose

This specification defines the Work Request, the primary entry point into the Engineering Control Framework (ECF).

Every execution within ECF begins with a Work Request.

A Work Request expresses an engineering need.

It does not prescribe an engineering solution.

---

# Core Principle

A Work Request describes **what engineering work is requested**.

It does not describe **how the work will be executed**.

Execution is the responsibility of the Engineering Control Framework.

---

# Responsibilities

A Work Request shall:

* identify the engineering problem
* identify the desired engineering outcome
* provide sufficient context to begin engineering
* initiate engineering execution
* become the root of all execution traces

A Work Request shall not:

* prescribe architecture
* prescribe implementation
* bypass engineering reasoning
* bypass approval gates

---

# Relationship to ECF

A Work Request is consumed by the Engineering Orchestration Engine.

The Orchestration Engine determines:

* engineering intent
* engineering phase
* reasoning strategy
* required engineering knowledge
* required engineering roles
* required engineering transformations

---

# Relationship to Projects

Projects own Work Requests.

ECF executes Work Requests.

Projects remain responsible for:

* business priorities
* product goals
* engineering context

---

# Required Structure

Every Work Request shall contain the following sections.

---

# 1. Identity

Required fields:

* Work Request ID
* Title
* Version
* Status
* Requested By
* Created Date

Example:

```text
WR-0001
```

---

# 2. Engineering Question

The primary engineering question.

Examples:

* Should Repository Integration become a first-class subsystem?
* How should user context be persisted?
* Which architecture should support AI providers?

Exactly one primary engineering question shall exist.

---

# 3. Desired Outcome

Describe the expected engineering outcome.

Examples:

* Engineering Recommendation
* Product Requirements
* System Design
* Architecture Review
* ADR
* Test Strategy

The outcome describes **what should be produced**, not the solution.

---

# 4. Business Motivation

Why is this work being requested?

Examples:

* reduce engineering uncertainty
* support a new feature
* improve maintainability
* investigate technical risk

---

# 5. Engineering Context Reference

Reference project-owned engineering context.

Examples:

* ENGINEERING_CONTEXT.md
* ADRs
* existing architecture
* product documentation

The Work Request references context.

It should not duplicate it.

---

# 6. Constraints

Identify known constraints.

Examples:

* technology
* budget
* delivery schedule
* regulatory requirements
* existing architecture

Constraints should describe reality, not preferred solutions.

---

# 7. Assumptions

Document assumptions known at request creation.

Assumptions may change during engineering.

---

# 8. Requested Deliverables

List expected outputs.

Examples:

* Engineering Recommendation Report
* Product Requirements Document
* System Design
* ADR
* Risk Assessment

Deliverables should reference canonical artifact types.

---

# 9. Priority

Recommended values:

* Critical
* High
* Medium
* Low

Priority influences scheduling.

It does not change engineering quality.

---

# 10. Approval Requirements

Specify required approval.

Examples:

* Human Approval
* Architecture Review
* Security Review
* Product Approval

Approval requirements should reference Review Packs where appropriate.

---

# 11. Success Criteria

Describe how successful completion will be evaluated.

Examples:

* engineering uncertainty reduced
* architectural recommendation produced
* approved engineering artifact created

---

# 12. Out of Scope

Explicitly identify what this Work Request does not attempt to achieve.

This helps prevent scope expansion.

---

# Work Request Lifecycle

```text
Draft
    ↓
Submitted
    ↓
Accepted
    ↓
Running
    ↓
Waiting for Approval
    ↓
Completed
```

Alternative outcomes:

* Cancelled
* Rejected
* Superseded
* Abandoned

---

# Validation

A valid Work Request must include:

* engineering question
* desired outcome
* engineering context reference
* constraints
* requested deliverables
* success criteria

---

# Traceability

Every execution trace must reference the originating Work Request.

Every produced engineering artifact must be traceable back to one or more Work Requests.

---

# Guiding Principle

The Work Request is the root object of engineering execution.

Everything executed by ECF should ultimately exist to satisfy an approved Work Request.
