# GLOSSARY.md

# Purpose

This glossary defines the official vocabulary of the Engineering Control Framework (ECF).

Terms defined here have precise meanings within ECF.

All framework documents, project adoptions, AI participants, and engineering artifacts should use these definitions consistently.

When a term is defined here, other documents should reference this glossary rather than redefine it.

---

# A

## Activity

Deprecated term.

Within ECF, an Activity is more precisely described as a **Knowledge Transformation**.

---

## Approval

A formal decision allowing engineering work to proceed beyond a Quality Gate.

Approvals are made by an authorized Role.

Human approval remains the final authority unless a project explicitly defines otherwise.

---

## Artifact

See **Canonical Artifact**.

---

# C

## Canonical Artifact

The authoritative representation of engineering knowledge.

A Canonical Artifact is:

* version controlled
* reviewable
* traceable
* editable

Derived formats (PDF, DOCX, SVG, etc.) are generated from the Canonical Artifact and are not the engineering source of truth.

---

## Confidence

The degree of engineering certainty achieved at a given point in the workflow.

Engineering work should increase confidence before increasing implementation effort.

Confidence is based on evidence—not intuition.

---

# D

## Derived Artifact

A published representation of a Canonical Artifact.

Examples:

* PDF
* DOCX
* HTML
* SVG
* PNG
* PPTX

Derived Artifacts communicate engineering knowledge but do not replace the Canonical Artifact.

---

# E

## Engineering Knowledge

The collective body of engineering information produced throughout a project.

Examples include:

* requirements
* designs
* ADRs
* reviews
* test plans
* implementation plans

Engineering Knowledge is preserved through Canonical Artifacts.

---

## Executor

The entity performing a Role.

Examples:

* Human engineer
* AI assistant
* Automated tooling
* Hybrid human-AI collaboration

ECF assigns responsibilities to Roles rather than Executors.

---

# F

## Finding

An observation produced during a Review.

Finding classifications include:

* Blocker
* Major
* Minor
* Observation
* Deferred
* Future Improvement

---

# K

## Knowledge Capture

The process of preserving engineering knowledge gained during execution.

Examples include:

* lessons learned
* ADR updates
* reusable patterns
* documentation improvements

Knowledge Capture is the final stage of the ECF execution lifecycle.

---

## Knowledge Transformation

A controlled engineering operation that converts existing engineering knowledge into new engineering knowledge.

Knowledge Transformations:

* consume Canonical Artifacts
* apply Standards
* produce Canonical Artifacts
* increase engineering confidence

---

# P

## Principle

A foundational engineering belief that guides decision making.

Principles rarely change.

Standards derive from Principles.

---

# Q

## Quality Gate

A formal checkpoint determining whether engineering work may progress.

Examples:

* Definition of Ready
* Human Approval
* Merge Readiness
* Definition of Done

Quality Gates reduce engineering risk.

---

# R

## Review

An independent evaluation of one or more Canonical Artifacts.

Reviews validate engineering knowledge.

Reviews do not create engineering knowledge.

---

## Review Pack

A reusable review orchestration defining:

* participating Roles
* required Reviews
* Quality Gates
* escalation rules

Review Packs coordinate engineering expertise for a category of work.

---

## Role

A named engineering responsibility.

Roles own engineering concerns.

Examples:

* Product Architect
* System Architect
* Security Architect
* Accessibility Architect

A Role is independent of its Executor.

---

# S

## Standard

A definition of engineering quality.

A Standard answers:

"What does good look like?"

Standards govern Knowledge Transformations and Reviews.

---

# T

## Template

A reusable structure for creating Canonical Artifacts.

Templates define layout.

Standards define quality.

Templates do not replace Standards.

---

## Traceability

The ability to follow engineering knowledge from its origin to its implementation.

A traceable project can answer:

* Why does this exist?
* Which Work Request created it?
* Which Standards governed it?
* Which Reviews approved it?
* Which implementation depends on it?

---

# V

## Verification

The process of confirming that implementation satisfies approved engineering intent.

Verification may include:

* automated testing
* manual QA
* accessibility validation
* security validation
* performance validation

---

# W

## Work Request

The formal entry point into the Engineering Control Framework.

A Work Request expresses engineering intent.

It initiates a Workflow.

Every engineering artifact, review, implementation, and decision should be traceable to one or more Work Requests.

---

## Workflow

A repeatable engineering process.

A Workflow orchestrates:

* Knowledge Transformations
* Reviews
* Quality Gates

A Workflow defines *how* engineering work progresses.

It does not define engineering quality.

---

# Guiding Rule

When introducing a new concept into ECF:

1. Check whether an existing glossary term already represents it.
2. Reuse existing terminology whenever practical.
3. Introduce new terms only when they add meaningful expressive power.
4. Update this glossary before using the new term elsewhere.

The ECF vocabulary should evolve deliberately and remain as small, precise, and stable as possible.
