# FRAMEWORK_ARCHITECTURE.md

# Purpose

This document defines the architecture of the Engineering Control Framework (ECF).

It describes the fundamental building blocks of the framework, the relationships between them, and how engineering work flows through the framework.

This document describes the framework itself—not any particular software project.

---

# Architectural Philosophy

ECF is a layered engineering governance framework.

Each layer exists to answer one engineering question.

A layer may depend only on layers above it.

This creates a predictable, explainable, and reusable engineering process.

---

# The ECF Layers

## Layer 1 — Principles

### Purpose

Define the values that guide engineering decisions.

Examples:

* Design Before Implementation
* Human Authority
* Knowledge Preservation
* Explainability
* Incremental Confidence

Principles change rarely.

They are the foundation of the framework.

---

## Layer 2 — Standards

### Purpose

Define what "good" looks like.

Examples:

* Product Requirements Standard
* System Design Standard
* ADR Standard
* UML Standard
* Accessibility Standard
* Security Standard

Standards define engineering quality.

They do not describe engineering process.

---

## Layer 3 — Workflows

### Purpose

Describe repeatable engineering processes.

Examples:

* New Feature
* Bug Fix
* Architecture Change
* Research
* Refactoring
* Release

A workflow answers:

> "What engineering process should be followed?"

---

## Layer 4 — Activities

### Purpose

Describe individual engineering disciplines.

Examples:

* Requirements Analysis
* Product Design
* Domain Modeling
* System Design
* Runtime Design
* Threat Modeling
* Test Planning
* Delivery Planning

Activities consume standards.

Activities produce engineering artifacts.

---

## Layer 5 — Canonical Artifacts

### Purpose

Capture engineering knowledge.

Artifacts are the primary outputs of engineering.

Each artifact has a **single canonical representation** that becomes the engineering source of truth.

Examples:

* Product Requirements Document
* Product Design Document
* Use Case Specification
* System Design Document
* Runtime Design
* Knowledge Design
* Threat Model
* Test Plan
* Architecture Decision Record
* Implementation Plan

Canonical artifacts should be:

* version controlled
* reviewable
* traceable
* reusable
* machine-readable where practical

Artifacts become part of the project's permanent engineering memory.

---

## Layer 6 — Reviews

### Purpose

Evaluate engineering artifacts.

Reviews reduce uncertainty.

Reviews do not create engineering artifacts.

Reviews validate them.

Examples:

* Product Review
* Architecture Review
* Security Review
* Accessibility Review
* Test Review
* Documentation Review

Reviews may recommend:

* approval
* approval with recommendations
* redesign
* rejection

---

## Layer 7 — Artifact Rendering

### Purpose

Render approved canonical artifacts into formats suitable for different audiences.

Engineering meaning should remain independent of presentation.

There should be **one canonical artifact** and **many derived representations**.

Examples include:

### Documents

* Markdown (canonical)
* DOCX
* PDF
* HTML
* ODT

### Diagrams

* PlantUML (canonical)
* Mermaid
* Draw.io
* SVG
* PNG
* PDF

### Presentations

* PowerPoint (PPTX)
* PDF

### Data

* JSON
* YAML
* CSV
* XML

Artifact Rendering answers:

> "How should engineering knowledge be delivered to different audiences while maintaining a single source of truth?"

Derived artifacts should be generated whenever practical.

Manual modification of derived artifacts should be avoided.

---

## Layer 8 — Quality Gates

### Purpose

Determine whether work may progress.

Examples:

* Definition of Ready
* Human Approval
* Merge Readiness
* Definition of Done

Quality Gates are explicit.

Work should never bypass them.

---

## Layer 9 — Execution

### Purpose

Perform implementation.

Execution may be performed by:

* humans
* AI
* collaborative teams

Execution follows engineering.

Execution does not replace engineering.

---

## Layer 10 — Verification

### Purpose

Verify implementation against approved engineering artifacts.

Examples:

* automated tests
* manual QA
* accessibility validation
* security verification
* performance validation

Verification confirms that implementation matches approved engineering intent.

---

## Layer 11 — Knowledge Capture

### Purpose

Capture lessons learned.

Examples:

* retrospective notes
* ADR updates
* architecture refinements
* framework improvements
* engineering metrics
* reusable patterns

Knowledge Capture ensures future work benefits from current experience.

---

# Layer Relationships

The framework is hierarchical.

```text
Principles
      │
      ▼
Standards
      │
      ▼
Workflows
      │
      ▼
Activities
      │
      ▼
Canonical Artifacts
      │
      ▼
Reviews
      │
      ▼
Artifact Rendering
      │
      ▼
Quality Gates
      │
      ▼
Execution
      │
      ▼
Verification
      │
      ▼
Knowledge Capture
```

Every layer depends only on the layers above it.

---

# Work Request Lifecycle

Every engineering effort begins as a Work Request.

The framework processes work through the following lifecycle.

```text
Work Request
        │
        ▼
Workflow Selection
        │
        ▼
Engineering Activities
        │
        ▼
Canonical Artifacts
        │
        ▼
Engineering Reviews
        │
        ▼
Artifact Rendering
        │
        ▼
Quality Gates
        │
        ▼
Implementation
        │
        ▼
Verification
        │
        ▼
Knowledge Capture
```

Every stage produces reusable engineering knowledge.

---

# Stable vs Configurable

ECF separates framework capabilities from project-specific configuration.

## Stable (Owned by ECF)

* Principles
* Standards
* Workflow definitions
* Activity definitions
* Artifact specifications
* Artifact rendering rules
* Review definitions
* Quality gate definitions

These evolve through versioned ECF releases.

---

## Configurable (Owned by Projects)

Examples:

* Product vision
* Technology stack
* Programming language
* Architectural style
* Review Pack selection
* AI provider
* Delivery strategy
* Implementation tooling

Projects adopt ECF without modifying the framework itself.

---

# AI Participation

AI participates by executing engineering activities.

AI consumes:

* Principles
* Standards
* Workflow definitions
* Activity definitions
* Templates

AI produces:

* draft engineering artifacts
* engineering analyses
* review recommendations

AI does **not** define:

* Principles
* Standards
* Framework architecture

Human approval remains mandatory.

---

# Framework Evolution

ECF evolves through versioned releases.

Projects adopt a specific framework version.

Framework improvements should maintain backward compatibility whenever practical.

ECF should itself be engineered using ECF.

---

# Design Goals

The framework should remain:

* deterministic
* explainable
* reusable
* provider-independent
* modular
* versioned
* auditable
* adaptable
* reviewable
* machine-friendly
* human-friendly
* support canonical artifacts with multiple derived output formats

No capability should depend on a specific programming language, AI model, software platform, or documentation tool.

---

# Architectural Principles

The framework follows these architectural principles:

1. Every engineering activity produces a canonical artifact.
2. Every canonical artifact may have multiple derived representations.
3. Reviews validate canonical artifacts, not derived formats.
4. Engineering knowledge has exactly one source of truth.
5. Presentation should never redefine engineering intent.
6. Projects configure the framework but do not redefine it.
7. AI executes the framework; it does not govern the framework.

---

# Success Criteria

The framework is successful when:

* engineering decisions are repeatable
* engineering knowledge is preserved
* artifacts remain consistent across formats
* reviews are standardized
* AI behavior is predictable
* projects can adopt ECF with minimal customization
* engineering quality improves independently of implementation tooling
