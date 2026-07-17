# RETRIEVAL_ACCEPTANCE_TESTS.md

# Purpose

This document defines acceptance tests for the Engineering Knowledge Base (EKB).

Acceptance tests validate the conceptual retrieval model rather than any specific retrieval technology.

A retrieval implementation (keyword search, graph traversal, vector search, hybrid search, etc.) is considered correct only if it satisfies these conceptual acceptance tests.

---

# Test Naming

Acceptance tests use the following format:

```
RAT-<Domain>-<Number>
```

Examples:

* RAT-ARCH-0001
* RAT-DESIGN-0001
* RAT-TEST-0001

---

# RAT-ARCH-0001

## Title

Retrieve engineering knowledge for deciding whether to introduce another subsystem.

---

## Purpose

Validate that EKB retrieves the minimum complete body of engineering knowledge required to reason about subsystem boundaries.

---

## Engineering Intent

Make a decision.

---

## Engineering Question

Should I introduce another subsystem?

---

## Primary Retrieval Object

Expected:

```
DG-ARCH-0001
Should I Introduce Another Subsystem?
```

Failure:

* Primary object not found.
* Multiple competing primary objects returned without justification.

---

## Supporting Knowledge

Expected Concepts

```
CON-ARCH-0001
Coupling

CON-ARCH-0002
Cohesion

CON-ARCH-0003
Bounded Context
```

Expected Pattern

```
PAT-ARCH-0001
Modular Architecture
```

Expected Quality Attributes

```
QA-0001
Maintainability

QA-0002
Complexity
```

Expected Example

```
EX-ARCH-0001
Subsystem Split Examples
```

---

## Objects That Should NOT Be Retrieved

Examples:

* unrelated security guidance
* accessibility guidance
* testing strategies
* deployment patterns
* unrelated design patterns

unless explicitly connected through Knowledge Object relationships.

---

## Retrieval Order

The preferred conceptual order is:

```
Engineering Question

↓

Decision Guide

↓

Supporting Concepts

↓

Supporting Pattern

↓

Quality Attributes

↓

Examples

↓

References
```

The retrieval technology may optimize internally, but the logical reasoning order should remain consistent.

---

## Acceptance Criteria

The test passes when:

* the correct Decision Guide is retrieved.
* all required supporting objects are retrieved.
* no unrelated engineering knowledge is included.
* relationships between retrieved objects are preserved.
* retrieved knowledge is sufficient for an engineer to reason about the decision.

---

## Failure Conditions

The test fails if:

* the Decision Guide is missing.
* supporting Concepts are incomplete.
* unrelated knowledge dominates the retrieval.
* object relationships are lost.
* engineering reasoning cannot be completed from the retrieved knowledge.

---

## Human Validation

An experienced engineer should be able to answer the engineering question using only the retrieved knowledge.

No additional engineering references should be required for this decision.

---

## Future Automation

Future retrieval implementations should execute this acceptance test automatically.

The retrieval engine is considered compliant only if it consistently produces the expected conceptual result.

---

# Acceptance Test Philosophy

Acceptance tests validate engineering reasoning support.

They do not validate:

* retrieval algorithms
* vector databases
* embedding models
* search performance

Those are implementation concerns.

The purpose of these tests is to ensure that EKB consistently delivers the correct engineering knowledge needed to support sound engineering decisions.
