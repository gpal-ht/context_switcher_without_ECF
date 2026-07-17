# DECISION_GUIDE_MODEL.md

# Purpose

This document defines the Decision Guide Model used throughout the Engineering Knowledge Base (EKB).

The Decision Guide Model establishes decision guide as the primary unit of reasoning within EKB.

Engineering knowledge exists to improve engineering decisions.

Every concept, pattern, practice, quality attribute, and example should support one or more engineering decisions.

---

# Philosophy

Software engineering is fundamentally the process of making informed decisions under uncertainty.

The purpose of EKB is not to prescribe solutions.

The purpose of EKB is to improve the quality of engineering decisions.

---

# Core Principle

Every engineering decision attempts to answer:

> **"Given this context, what is the most appropriate engineering choice, and why?"**

The correct decision depends on context.

EKB should teach engineers how to reason rather than what to memorize.

---

# What Is an Decision Guide?

An Decision Guide is a deliberate choice between two or more engineering alternatives.

Examples include:

* Should this become a separate subsystem?
* Should this requirement be split?
* Should this process be event-driven?
* Should this component be reused?
* Should this API be synchronous or asynchronous?
* Should this work be postponed?

Engineering decisions always involve trade-offs.

---

# Decision Structure

Every Decision Guide should describe:

## Decision Statement

A single engineering question.

Example:

Should this capability become a separate subsystem?

---

## Context

The engineering situation.

Examples:

* current architecture
* project constraints
* team experience
* technology
* quality requirements

---

## Forces

Factors influencing the decision.

Examples:

* complexity
* coupling
* performance
* maintainability
* cost
* delivery time
* security
* scalability

Engineering decisions should explicitly identify competing forces.

---

## Alternatives

List the realistic alternatives.

Each alternative should be described objectively.

---

## Trade-offs

Describe the advantages and disadvantages of each alternative.

Trade-offs should be explicit.

Engineering quality comes from understanding trade-offs rather than hiding them.

---

## Decision Heuristics

Practical guidance that helps engineers evaluate alternatives.

Heuristics should be:

* evidence-based
* contextual
* explainable

Heuristics are not absolute rules.

---

## Risks

Identify engineering risks associated with each alternative.

Examples:

* technical debt
* increased complexity
* reduced flexibility
* security exposure

---

## Examples

Provide examples of:

* appropriate usage
* inappropriate usage
* borderline cases

Examples improve engineering judgment.

---

## Related Knowledge

Reference:

* Concepts
* Patterns
* Standards
* Quality Attributes
* Other Decision Guides

Engineering knowledge should be interconnected.

---

## References

List books, papers, specifications, or authoritative sources that informed the guidance.

---

# Decision Categories

Decision Guides may belong to multiple categories.

Examples:

## Product

* feature scope
* MVP boundaries
* user workflows

---

## Requirements

* requirement decomposition
* requirement quality
* prioritization

---

## Architecture

* subsystem boundaries
* integration strategy
* deployment strategy

---

## Design

* abstraction
* composition
* modularity
* interfaces

---

## Runtime

* state management
* concurrency
* event handling

---

## Data

* persistence
* consistency
* versioning

---

## Quality

* testing
* security
* accessibility
* performance
* maintainability

---

## Delivery

* implementation sequencing
* incremental delivery
* rollout strategy

---

# Decision Relationships

Engineering decisions are connected.

Examples:

A Product Decision may influence:

* Requirements Decisions

Requirements Decisions influence:

* Architecture Decisions

Architecture Decisions influence:

* Design Decisions

Design Decisions influence:

* Implementation Decisions

Engineering decisions should preserve these relationships.

---

# Decision Confidence

Every Decision Guide should indicate confidence.

Suggested levels:

* High
* Medium
* Low
* Unknown

Confidence should be supported by evidence rather than opinion.

---

# Decision Evolution

Engineering decisions evolve.

A decision may be:

* confirmed
* refined
* superseded
* rejected

EKB should preserve previous reasoning when decisions evolve.

---

# Relationship to ECF

EKB teaches engineers how to reason about decisions.

ECF defines how engineering decisions are incorporated into engineering workflows.

Projects apply those decisions within a specific context.

---

# Success Criteria

An Decision Guide entry is successful when it:

* improves engineering judgment
* explains trade-offs
* identifies relevant forces
* supports multiple contexts
* avoids prescribing universal solutions
* remains useful across projects

---

# Guiding Principle

The purpose of engineering knowledge is not to provide answers.

The purpose of engineering knowledge is to improve the quality of engineering decisions.