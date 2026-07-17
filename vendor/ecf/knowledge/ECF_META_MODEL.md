# ECF_META_MODEL.md

# Purpose

This document defines the formal vocabulary of the Engineering Control Framework (ECF).

ECF defines a common language for engineering. Every workflow, transformation, artifact, review, quality gate, and AI participant must use this language consistently.

This meta-model describes the core entities of ECF and how they relate to one another.

---

# Core Idea

ECF treats software engineering as a controlled transformation of knowledge.

A vague idea becomes structured requirements.

Requirements become designs.

Designs become implementation plans.

Implementation plans become verified software.

Every step produces or validates engineering knowledge.

---

# First-Class Entities

ECF has ten first-class entities.

1. Principle
2. Standard
3. Workflow
4. Knowledge Transformation
5. Canonical Artifact
6. Review
7. Quality Gate
8. Work Request
9. Template
10. Role

Everything else in ECF should be derived from these concepts.

---

# Entity Definitions

## Principle

A fundamental engineering belief that guides decisions.

Examples:

* Design Before Implementation
* Human Authority
* Knowledge Preservation
* Incremental Confidence

Principles change rarely.

---

## Standard

A definition of engineering quality.

A Standard answers:

> What does good look like?

Examples:

* Artifact Standard
* System Design Standard
* ADR Standard
* Accessibility Standard
* Security Standard

Standards guide transformations and reviews.

---

## Workflow

A repeatable engineering process.

A Workflow orchestrates multiple Knowledge Transformations, Reviews, and Quality Gates.

Examples:

* New Feature Workflow
* Bug Fix Workflow
* Architecture Change Workflow
* Research Workflow
* Release Workflow

A Workflow answers:

> What process should this work follow?

---

## Knowledge Transformation

A controlled engineering operation that converts one form of engineering knowledge into another.

Examples:

* Requirements Transformation
* Product Design Transformation
* System Design Transformation
* Threat Modeling Transformation
* Test Planning Transformation
* Implementation Planning Transformation

A Knowledge Transformation consumes Canonical Artifacts and produces new or updated Canonical Artifacts.

---

## Canonical Artifact

The authoritative representation of engineering knowledge.

Examples:

* Product Requirements Document
* System Design Document
* Architecture Decision Record
* Threat Model
* Test Plan
* Implementation Plan

A Canonical Artifact is the source of truth.

Derived formats may be generated from it, but they are not the source of truth.

---

## Review

An independent evaluation of a Canonical Artifact or transformation output.

A Review answers:

> Is this engineering knowledge good enough to proceed?

Examples:

* Product Review
* Architecture Review
* Security Review
* Accessibility Review
* Test Review

Reviews reduce uncertainty.

---

## Quality Gate

A decision point that determines whether work may progress.

Examples:

* Definition of Ready
* Human Approval Gate
* Merge Readiness
* Definition of Done

Quality Gates enforce control.

---

## Work Request

The starting point for engineering work.

A Work Request describes intent.

Examples:

* Add a new feature
* Fix a defect
* Change architecture
* Research an option
* Refactor a component

A Work Request selects or triggers a Workflow.

---

## Template

A reusable structure for creating Canonical Artifacts.

Templates standardize artifact creation.

A Template does not replace a Standard.

The Standard defines quality.

The Template defines structure.

---

## Role

A responsibility-bearing participant in the engineering process.

A Role may be fulfilled by:

* a human
* an AI assistant
* an automated tool
* a hybrid human-AI process

Examples:

* Product Architect
* System Architect
* Security Architect
* Accessibility Architect
* Test Architect
* Delivery Architect

Roles perform transformations, reviews, or approvals.

---

# Core Relationships

```text id="mdm3y0"
Principles
    ↓
Standards
    ↓
Workflows
    ↓
Knowledge Transformations
    ↓
Canonical Artifacts
    ↓
Reviews
    ↓
Quality Gates
    ↓
Execution
    ↓
Verification
    ↓
Knowledge Capture
```

---

# Relationship Rules

## Principles guide Standards

Standards must align with ECF Principles.

---

## Standards govern Transformations

Knowledge Transformations apply Standards to produce high-quality artifacts.

---

## Workflows orchestrate Transformations

A Workflow defines the order and conditions under which transformations occur.

---

## Transformations produce Artifacts

Every meaningful engineering transformation produces or updates at least one Canonical Artifact.

---

## Templates structure Artifacts

Templates provide reusable artifact layouts.

---

## Reviews validate Artifacts

Reviews evaluate artifacts against standards and project context.

---

## Quality Gates control progression

Work may progress only when required reviews and criteria are satisfied.

---

## Roles perform work

Roles execute transformations, conduct reviews, and approve gates according to their authority.

---

# Canonical Flow

```text id="42wu8v"
Work Request
    ↓
Workflow Selection
    ↓
Knowledge Transformation
    ↓
Canonical Artifact
    ↓
Review
    ↓
Quality Gate
    ↓
Execution
    ↓
Verification
    ↓
Knowledge Capture
```

---

# Role Neutrality

ECF defines responsibilities, not tools.

A Role is independent of the executor.

For example:

* Product Architect may be performed by Claude today.
* Product Architect may be performed by a human tomorrow.
* Product Architect may be performed by another AI system later.

The framework remains stable even when execution tools change.

---

# Canonical vs Derived Artifacts

A Canonical Artifact is the source of truth.

Derived artifacts may include:

* PDF
* DOCX
* HTML
* PPTX
* SVG
* PNG
* Mermaid
* PlantUML
* Draw.io

Derived artifacts are views.

They should not be edited directly when a canonical source exists.

---

# Meta-Model Principle

Every ECF extension should introduce as few new concepts as possible.

Before adding a new concept, ask:

1. Can it be represented as an existing entity?
2. Is it project-specific rather than framework-level?
3. Does it improve engineering control?
4. Does it increase clarity more than complexity?

---

# Guiding Statement

ECF is not merely a collection of templates.

ECF is a controlled language for transforming engineering intent into verified software.
