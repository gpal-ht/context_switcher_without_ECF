# ARTIFACT_STANDARD.md

# Purpose

This standard defines the lifecycle, structure, ownership, quality expectations, and publication rules for all engineering artifacts produced within the Engineering Control Framework (ECF).

Every engineering activity produces one or more artifacts.

Every artifact shall conform to this standard.

---

# Core Principle

Engineering knowledge must have exactly one canonical source of truth.

Every other representation is a derived artifact.

---

# Artifact Philosophy

Artifacts exist to:

* preserve engineering knowledge
* communicate engineering decisions
* enable engineering reviews
* support implementation
* provide long-term traceability

Artifacts are not temporary documents.

Artifacts become part of the engineering memory of a project.

---

# Canonical Artifact

Every artifact shall have exactly one canonical representation.

The canonical representation is:

* version controlled
* reviewable
* editable
* traceable
* human readable
* AI readable

The canonical representation is the only artifact that may be edited directly.

---

# Derived Artifacts

Derived artifacts are generated from the canonical artifact.

Derived artifacts exist for different audiences and purposes.

Examples include:

* PDF
* DOCX
* HTML
* PPTX
* SVG
* PNG
* PlantUML diagrams
* Mermaid diagrams

Derived artifacts should never become the engineering source of truth.

---

# Standard Artifact Metadata

Every artifact shall declare:

## Identity

* Artifact ID
* Artifact Name
* Artifact Type
* Version
* Status

---

## Ownership

* Author
* Reviewer(s)
* Approver
* Owning Activity
* Related Workflow

---

## Purpose

* Objective
* Intended Audience
* Scope
* Assumptions
* Constraints

---

## Traceability

* Related Work Request
* Related ADRs
* Related Standards
* Related Reviews
* Related Artifacts

---

## Lifecycle

* Created
* Reviewed
* Approved
* Published
* Superseded
* Archived

---

# Artifact Quality Requirements

Every artifact should be:

* complete
* correct
* consistent
* understandable
* reviewable
* traceable
* reusable
* versioned

---

# Artifact Categories

ECF recognizes several categories of engineering artifacts.

## Product

Examples:

* Product Vision
* Product Requirements
* Product Design
* Use Cases

---

## Architecture

Examples:

* System Design
* Component Design
* Runtime Design
* Data Design
* AI Design

---

## Governance

Examples:

* ADR
* Engineering Review
* Risk Assessment
* Decision Log

---

## Quality

Examples:

* Threat Model
* Accessibility Assessment
* Test Plan
* Performance Assessment

---

## Delivery

Examples:

* Implementation Plan
* Release Plan
* Deployment Plan

---

# Supported Output Formats

Every artifact may be published in one or more formats.

## Canonical

Preferred canonical formats:

* Markdown
* PlantUML (for diagrams)
* Mermaid (where appropriate)
* YAML (structured specifications)
* JSON (machine-readable interchange)

---

## Published Documents

* PDF
* DOCX
* HTML
* ODT

---

## Diagrams

* PlantUML
* Mermaid
* Draw.io
* SVG
* PNG
* PDF

---

## Presentations

* PPTX
* PDF

---

## Structured Data

* JSON
* YAML
* CSV
* XML

---

# Rendering Rules

Rendering must preserve engineering meaning.

Rendering may change presentation.

Rendering must never change content.

If rendering requires manual modification, the canonical artifact must be updated first.

---

# Versioning

Artifacts follow semantic versioning.

Major

Breaking engineering changes.

Minor

Additional content.

Patch

Corrections and editorial improvements.

---

# Review Rules

Only canonical artifacts are reviewed.

Derived artifacts are regenerated after approval.

Review comments should always reference the canonical artifact.

---

# Approval Rules

Approval applies to the canonical artifact.

Derived artifacts inherit approval automatically.

---

# Naming Convention

Recommended format:

<ArtifactType>-<Identifier>-<Title>

Examples:

* PRD-001-Context-Switching
* SDD-003-Knowledge-Architecture
* ADR-014-Event-Driven-Design
* TP-005-Repository-Evaluation

---

# Traceability Principle

Every artifact should answer:

* Why does this exist?
* What activity created it?
* Which workflow required it?
* Which standards governed it?
* Which reviews approved it?
* Which implementation depends on it?

---

# Guiding Principle

Engineering artifacts are not documentation.

They are the persistent, reviewable, and reusable outputs of engineering.

The artifact—not the conversation—is the source of engineering truth.
