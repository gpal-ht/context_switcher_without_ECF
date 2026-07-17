# DIAGRAM_STANDARD.md

# Purpose

This standard defines the role, quality requirements, lifecycle, and publication rules for engineering diagrams within the Engineering Control Framework (ECF).

Engineering diagrams are not illustrations.

They are canonical engineering artifacts that communicate structure, behavior, relationships, and engineering intent.

---

# Philosophy

A diagram should communicate engineering understanding more effectively than prose alone.

Every diagram should answer one primary engineering question.

If a diagram attempts to answer multiple unrelated questions, it should be split into multiple diagrams.

---

# Core Principles

## One Diagram, One Purpose

Each diagram exists to communicate one engineering concern.

Examples:

* Domain structure
* System architecture
* Runtime interactions
* Deployment topology
* State transitions

---

## Canonical Source

Every diagram has one canonical source.

Recommended canonical formats:

* PlantUML
* Mermaid (where appropriate)

Derived formats may include:

* SVG
* PNG
* PDF
* HTML

The canonical source is the only editable representation.

---

## Traceability

Every diagram must reference:

* Work Request
* Related Artifact(s)
* Related ADR(s)
* Related Standards
* Related Reviews

Every diagram should be traceable to the engineering decision that required it.

---

# Diagram Metadata

Every diagram shall declare:

* Diagram ID
* Title
* Version
* Status
* Author
* Reviewer(s)
* Related Workflow
* Related Transformation
* Related Artifact
* Canonical Format
* Generated Formats

---

# Diagram Categories

## Product

Examples:

* Use Case Diagram
* User Journey
* Story Map

Purpose:

Communicate user interaction.

---

## Domain

Examples:

* Domain Model
* Concept Map
* Knowledge Model

Purpose:

Communicate business concepts.

---

## Architecture

Examples:

* System Context
* Component Diagram
* Package Diagram
* Module Dependencies

Purpose:

Communicate software structure.

---

## Behavioral

Examples:

* Sequence Diagram
* Activity Diagram
* State Machine
* Event Flow

Purpose:

Communicate runtime behavior.

---

## Data

Examples:

* Entity Relationship Diagram
* Knowledge Graph
* Information Flow

Purpose:

Communicate persistent information.

---

## Infrastructure

Examples:

* Deployment Diagram
* Network Diagram
* Environment Topology

Purpose:

Communicate operational architecture.

---

# Diagram Quality Requirements

Every diagram should be:

* correct
* readable
* focused
* internally consistent
* traceable
* version controlled
* reviewable

Avoid decorative detail that does not improve engineering understanding.

---

# Required Elements

Unless intentionally omitted, every diagram should identify:

* actors
* responsibilities
* ownership
* relationships
* direction of flow
* significant boundaries

Behavioral diagrams should also show:

* failure paths
* alternative flows
* recovery paths (where applicable)

---

# Review Requirements

Diagrams are reviewed using the same process as any other engineering artifact.

Reviewers should verify:

* technical correctness
* consistency with related artifacts
* clarity
* completeness
* compliance with this standard

---

# Rendering

Canonical diagrams may be rendered into:

## Engineering

* PlantUML
* Mermaid

## Documentation

* SVG
* PNG
* PDF

## Presentation

* PowerPoint
* HTML

Rendering must never change engineering meaning.

---

# Naming Convention

Recommended:

<DiagramType>-<Identifier>-<Title>

Examples:

* CD-001-ECF-Meta-Model
* SD-003-Feature-Workflow
* UC-001-Context-Switching
* SQ-002-Repository-Evaluation

---

# Recommended Diagram Set

Every substantial software project should eventually contain:

## Product

* Use Case Diagram
* User Journey

## Architecture

* System Context Diagram
* Component Diagram
* Package Diagram

## Domain

* Domain Model

## Runtime

* Sequence Diagrams
* State Machine Diagrams

## Information

* Data Model
* Information Flow

## Deployment

* Deployment Diagram

Additional diagrams should be created only when they improve engineering understanding.

---

# Guiding Principle

A diagram is a first-class engineering artifact.

It should be governed, reviewed, versioned, and maintained with the same discipline as any other engineering deliverable.
