# ENGINEERING_PROCESS_MAP.md

# Purpose

This document defines the conceptual process of software engineering.

It describes the major engineering phases that transform an initial idea into verified software and accumulated engineering knowledge.

The Engineering Process Map is independent of:

* programming language
* framework
* methodology
* organization
* tooling
* AI provider

It describes engineering itself.

---

# Philosophy

Software engineering is a progressive refinement of understanding.

Engineering does not begin with implementation.

Engineering begins with uncertainty and progressively replaces uncertainty with validated engineering knowledge.

Implementation is one phase of engineering—not its purpose.

---

# Core Principle

Every engineering phase should increase engineering confidence.

Each phase transforms uncertainty into engineering knowledge.

---

# The Engineering Process

Software engineering consists of nine primary phases.

```text
Need
    ↓
Discover
    ↓
Understand
    ↓
Define
    ↓
Design
    ↓
Validate
    ↓
Plan
    ↓
Implement
    ↓
Verify
    ↓
Learn
```

Each phase answers a different engineering question.

---

# Phase 1 — Discover

## Purpose

Determine whether there is a problem or opportunity worth solving.

Questions include:

* What problem exists?
* Who experiences it?
* Why does it matter?
* Is action justified?

Typical outputs:

* Problem Statement
* Opportunity Description

---

# Phase 2 — Understand

## Purpose

Develop sufficient understanding before making decisions.

Questions include:

* How does the current system work?
* What constraints exist?
* Who are the stakeholders?
* What assumptions exist?

Typical outputs:

* Domain Understanding
* Stakeholder Understanding
* Constraint Analysis

---

# Phase 3 — Define

## Purpose

Convert understanding into precise engineering intent.

Questions include:

* What exactly are we trying to achieve?
* What is in scope?
* What is out of scope?
* How will success be measured?

Typical outputs:

* Problem Definition
* Success Criteria
* Scope Definition

---

# Phase 4 — Design

## Purpose

Create engineering solutions.

Questions include:

* What architecture is appropriate?
* What boundaries should exist?
* What responsibilities belong where?
* Which quality attributes matter?

Typical outputs:

* Product Design
* System Design
* Runtime Design
* Data Design
* Security Design

---

# Phase 5 — Validate

## Purpose

Evaluate engineering decisions before implementation.

Questions include:

* Is the design sound?
* Are risks understood?
* Are trade-offs acceptable?
* Is additional engineering required?

Typical outputs:

* Reviews
* Risk Assessments
* Threat Models
* Accessibility Assessments

---

# Phase 6 — Plan

## Purpose

Prepare engineering work for execution.

Questions include:

* What should be implemented first?
* How should work be organized?
* What dependencies exist?
* What verification is required?

Typical outputs:

* Delivery Plan
* Work Breakdown
* Test Strategy

---

# Phase 7 — Implement

## Purpose

Convert approved engineering knowledge into working software.

Implementation follows engineering.

It should not redefine engineering decisions.

Typical outputs:

* Source Code
* Configuration
* Infrastructure

---

# Phase 8 — Verify

## Purpose

Confirm that implementation satisfies engineering intent.

Questions include:

* Does the implementation work?
* Does it satisfy requirements?
* Are quality objectives achieved?
* Are defects understood?

Typical outputs:

* Test Results
* Verification Reports
* QA Findings

---

# Phase 9 — Learn

## Purpose

Capture engineering knowledge for future work.

Questions include:

* What did we learn?
* Which assumptions were incorrect?
* What should change?
* What reusable knowledge was created?

Typical outputs:

* Retrospectives
* ADR Updates
* Engineering Knowledge
* Framework Improvements

---

# Process Characteristics

The engineering process is:

* iterative
* evidence-driven
* knowledge-centric
* review-oriented
* continuously improving

Engineering rarely progresses strictly linearly.

Feedback loops are expected.

---

# Feedback Loops

Examples:

```text
Design
    ↓
Review
    ↓
Redesign
```

```text
Implementation
    ↓
Verification
    ↓
Implementation
```

```text
Verification
    ↓
Learning
    ↓
Improved Design
```

Learning continuously improves future engineering.

---

# Relationship to EKB

EKB explains:

* how engineers perform each phase
* how experienced engineers reason
* which engineering decisions arise
* which concepts and patterns apply

---

# Relationship to ECF

ECF executes engineering by orchestrating the activities within these phases.

ECF does not redefine the engineering process.

It governs and automates it.

---

# Guiding Principle

Engineering is the disciplined progression from uncertainty to validated knowledge.

Every phase exists to increase understanding before increasing implementation effort.
