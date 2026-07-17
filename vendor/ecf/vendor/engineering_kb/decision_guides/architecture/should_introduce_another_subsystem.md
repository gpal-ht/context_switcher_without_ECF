---
id: DG-ARCH-0001
title: Should I Introduce Another Subsystem?
type: decision_guide
status: draft
version: 0.1.0
created: 2026-07-07
updated: 2026-07-07

discipline:
  - architecture

tags:
  - subsystem
  - modularity
  - architecture

confidence: medium

owner: engineering_kb

relationships:
  requires:
    - CON-ARCH-0001
    - CON-ARCH-0002
    - CON-ARCH-0003
  affects:
    - QA-0001
    - QA-0002
  illustrated_by:
    - EX-ARCH-0001
  references:
    - PAT-ARCH-0001
---

# Decision Statement

Should this capability become a separate subsystem?

---

# Context

This decision occurs when a software system is growing and a capability begins to appear distinct from the surrounding system.

Typical indicators include:

* increasing implementation complexity
* different reasons for change
* growing responsibility boundaries
* increasing coordination between unrelated concepts

The engineer must decide whether introducing a new subsystem reduces long-term engineering complexity or merely redistributes it.

---

# Engineering Question

Given the current understanding of the system, should this capability remain within the existing subsystem or become an independent subsystem?

---

# Why This Decision Matters

Subsystem boundaries are among the most expensive architectural decisions to change later.

Well-designed boundaries improve:

* maintainability
* reasoning
* testing
* independent evolution

Poor boundaries increase:

* coupling
* accidental complexity
* implementation cost
* architectural drift

---

# Engineering Forces

The decision balances several competing forces.

## Encouraging Separation

* high cohesion
* independent reasons to change
* growing complexity
* independent testing
* clear ownership

## Encouraging Consolidation

* shared responsibilities
* immature understanding
* premature abstraction
* delivery urgency
* low implementation complexity

---

# Alternatives

## Keep the Capability Within the Existing Subsystem

Appropriate when:

* responsibilities remain closely related
* implementation is still evolving
* boundaries are not yet understood

### Benefits

* lower immediate complexity
* simpler implementation
* fewer architectural elements

### Risks

* future coupling
* reduced maintainability
* larger subsystem over time

---

## Create a Separate Subsystem

Appropriate when:

* responsibility is clearly defined
* change patterns differ
* boundaries are stable
* long-term evolution benefits from separation

### Benefits

* improved modularity
* clearer ownership
* easier testing
* simpler reasoning

### Risks

* additional coordination
* increased architectural complexity
* potential over-engineering

---

## Delay the Decision

Appropriate when engineering understanding is still incomplete.

This option intentionally gathers more evidence before introducing structural changes.

---

# Decision Heuristics

A separate subsystem is usually appropriate when most of the following are true:

* it has one primary responsibility
* it changes independently
* it has its own vocabulary
* it can be tested independently
* other parts of the system should not know its internal implementation
* future growth is expected

If these conditions are not yet understood, postpone the decision rather than introducing speculative architecture.

---

# Common Mistakes

* Creating subsystems based only on folder structure.
* Splitting because a file becomes large.
* Introducing architecture without a responsibility boundary.
* Optimizing for hypothetical future requirements.
* Treating every capability as a subsystem.

---

# Engineering Recommendation

Prefer introducing a subsystem only when doing so produces a clearer responsibility boundary and reduces long-term reasoning complexity.

If engineering understanding remains incomplete, continue learning before restructuring the architecture.

---

# Trade-offs

There is no universally correct answer.

The correct decision depends upon:

* engineering context
* expected evolution
* delivery constraints
* quality objectives
* available evidence

Engineering judgment should balance these factors rather than applying rigid rules.

---

# Related Knowledge Objects

## Concepts

* CON-ARCH-0001 — Coupling
* CON-ARCH-0002 — Cohesion
* CON-ARCH-0003 — Bounded Context

## Pattern

* PAT-ARCH-0001 — Modular Architecture

## Quality Attributes

* QA-0001 — Maintainability
* QA-0002 — Complexity

## Example

* EX-ARCH-0001 — Subsystem Split Examples

---

# Confidence Guidance

High confidence when responsibility boundaries are stable and supported by observed change patterns.

Medium confidence when the boundary appears reasonable but additional evidence would improve the decision.

Low confidence when the decision is driven primarily by intuition, aesthetics, or speculative future needs.
