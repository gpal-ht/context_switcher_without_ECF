# ENGINEERING_KNOWLEDGE_MATRIX.md

# Purpose

This document defines how engineering knowledge is used throughout the software engineering process.

It connects the Engineering Process Map with the Engineering Knowledge Base.

The matrix describes:

* which Knowledge Objects are relevant to each engineering phase
* how those objects are used
* which objects are produced
* which objects are expected as outputs

This matrix is the primary bridge between EKB and ECF.

---

# Philosophy

Engineering is the application of knowledge to progressively reduce uncertainty.

Different engineering phases require different knowledge.

The purpose of this matrix is to ensure that engineers retrieve **the right knowledge at the right time** rather than the largest amount of knowledge.

---

# Usage Levels

The matrix uses four usage levels.

| Level          | Meaning                                                       |
| -------------- | ------------------------------------------------------------- |
| **Primary**    | Essential for this phase. Work should not proceed without it. |
| **Supporting** | Frequently used to improve engineering decisions.             |
| **Optional**   | Useful in specific situations.                                |
| **Output**     | Knowledge typically produced during this phase.               |

---

# Engineering Knowledge Matrix

| Engineering Phase | Decision Guides | Concepts    | Patterns    | Quality Attributes | Examples    | References  |
| ----------------- | --------------- | ----------- | ----------- | ------------------ | ----------- | ----------- |
| Discover          | **Primary**     | Supporting  | Optional    | Supporting         | Supporting  | Supporting  |
| Understand        | **Primary**     | **Primary** | Optional    | Supporting         | **Primary** | Supporting  |
| Define            | **Primary**     | **Primary** | Supporting  | **Primary**        | Supporting  | Supporting  |
| Design            | **Primary**     | **Primary** | **Primary** | **Primary**        | Supporting  | Supporting  |
| Validate          | **Primary**     | Supporting  | Supporting  | **Primary**        | **Primary** | Supporting  |
| Plan              | Supporting      | Optional    | Supporting  | **Primary**        | Optional    | Optional    |
| Implement         | Optional        | Supporting  | **Primary** | **Primary**        | Supporting  | Optional    |
| Verify            | Supporting      | Supporting  | Optional    | **Primary**        | **Primary** | Supporting  |
| Learn             | Supporting      | Supporting  | Supporting  | Supporting         | **Output**  | **Primary** |

---

# Phase Guidance

## Discover

Primary objective:

Determine whether a meaningful engineering problem exists.

Knowledge emphasis:

* Decision Guides
* Problem Examples
* Relevant References

Avoid early design patterns.

---

## Understand

Primary objective:

Develop a shared understanding of the problem space.

Knowledge emphasis:

* Concepts
* Decision Guides
* Examples

Patterns should be introduced only when they improve understanding.

---

## Define

Primary objective:

Transform understanding into clear engineering intent.

Knowledge emphasis:

* Decision Guides
* Concepts
* Quality Attributes

Engineering quality begins here.

---

## Design

Primary objective:

Create engineering solutions.

Knowledge emphasis:

* Decision Guides
* Concepts
* Patterns
* Quality Attributes

This phase makes the greatest use of engineering knowledge.

---

## Validate

Primary objective:

Challenge engineering decisions before implementation.

Knowledge emphasis:

* Decision Guides
* Quality Attributes
* Examples

Validation should reduce uncertainty rather than merely confirm existing ideas.

---

## Plan

Primary objective:

Prepare work for implementation.

Knowledge emphasis:

* Quality Attributes
* Relevant Patterns
* Delivery-related Decision Guides

Planning should not redefine engineering decisions.

---

## Implement

Primary objective:

Convert engineering knowledge into working software.

Implementation should consume engineering knowledge rather than create it.

---

## Verify

Primary objective:

Determine whether implementation satisfies engineering intent.

Knowledge emphasis:

* Quality Attributes
* Examples
* Decision Guides

Verification compares implementation against approved engineering knowledge.

---

## Learn

Primary objective:

Capture reusable engineering knowledge.

Outputs include:

* Examples
* References
* New Decision Guides
* Improved Concepts
* Updated Patterns

Learning enriches the Engineering Knowledge Base for future work.

---

# Relationship to EKB

The matrix determines **what engineering knowledge should be retrieved** for each engineering phase.

It does not specify **how** retrieval is implemented.

---

# Relationship to ECF

ECF should use this matrix when selecting engineering knowledge during execution.

Given:

* current engineering phase
* engineering intent
* engineering question

ECF retrieves the Knowledge Objects identified by this matrix before performing engineering reasoning.

---

# Guiding Principle

Engineers should retrieve the smallest body of knowledge that provides the greatest improvement in engineering reasoning for the current phase.
