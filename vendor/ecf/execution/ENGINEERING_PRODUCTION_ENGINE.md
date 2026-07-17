# ENGINEERING_PRODUCTION_ENGINE.md

# Purpose

The Engineering Production Engine is responsible for producing engineering artifacts from approved engineering recommendations.

The Production Engine does not perform engineering reasoning.

Its responsibility is to execute approved engineering work in a controlled, traceable, and repeatable manner.

The Production Engine transforms approved engineering intent into canonical engineering artifacts.

---

# Philosophy

Engineering reasoning determines **what should be produced**.

Engineering production determines **how it is produced**.

Reasoning and production are intentionally separated.

This separation preserves:

* human authority
* engineering traceability
* repeatable execution
* clear accountability

---

# Core Principle

The Production Engine executes only approved engineering work.

It must never execute directly from engineering questions or engineering knowledge.

---

# Responsibilities

The Production Engine shall:

* consume approved Engineering Recommendation Reports
* execute Engineering Transformation Specifications
* apply Engineering Standards
* apply Artifact Templates
* produce canonical engineering artifacts
* produce derived engineering artifacts where required
* validate outputs
* generate Production Traces

The Production Engine shall not:

* reinterpret engineering intent
* perform architectural reasoning
* bypass approval gates
* modify Engineering Knowledge
* change Engineering Recommendations

---

# Inputs

The Production Engine consumes:

## Approved Engineering Recommendation Report

The approved recommendation is the authority for execution.

The report must identify:

* engineering objective
* recommended transformation
* constraints
* assumptions
* required outputs

Execution must stop if approval is missing.

---

## Engineering Transformation Specification

Defines:

* required inputs
* required outputs
* transformation rules
* validation requirements
* completion criteria

---

## Engineering Standards

Applicable standards define engineering quality.

Examples:

* Artifact Standard
* Diagram Standard
* Documentation Standard

---

## Artifact Templates

Templates define artifact structure.

Templates never replace standards.

---

## Existing Canonical Artifacts

Existing project artifacts may be updated.

Examples:

* Product Requirements
* System Design
* ADRs
* Domain Model

---

# Execution Pipeline

```text
Approved Engineering Recommendation
                │
                ▼
Validate Approval
                │
                ▼
Select Transformation Specification
                │
                ▼
Collect Inputs
                │
                ▼
Apply Standards
                │
                ▼
Apply Templates
                │
                ▼
Produce Engineering Artifacts
                │
                ▼
Validate Outputs
                │
                ▼
Generate Derived Artifacts
                │
                ▼
Generate Production Trace
```

---

# Step 1 — Validate Approval

Execution begins only after approval.

Required checks include:

* Engineering Recommendation approved
* required reviews complete
* Quality Gates passed
* required inputs available

---

# Step 2 — Select Transformation Specification

Select exactly one Engineering Transformation Specification.

Examples:

* Problem Definition Transformation
* Product Requirements Transformation
* System Design Transformation

Transformation specifications define execution.

---

# Step 3 — Collect Inputs

Gather:

* approved recommendation
* engineering context
* existing artifacts
* standards
* templates

Input provenance must be recorded.

---

# Step 4 — Apply Standards

Standards define engineering quality.

Every produced artifact must satisfy all applicable standards.

Standards are never optional unless explicitly stated.

---

# Step 5 — Apply Templates

Templates provide consistent artifact structure.

Templates improve consistency.

Templates do not determine engineering quality.

---

# Step 6 — Produce Engineering Artifacts

Generate canonical engineering artifacts.

Examples:

* Problem Definition
* Product Requirements
* Product Design
* System Design
* Runtime Design
* Test Strategy
* ADR

Canonical artifacts become the project's engineering source of truth after approval.

---

# Step 7 — Validate Outputs

Validation includes:

* standards compliance
* required sections
* traceability
* artifact relationships
* metadata correctness
* template compliance

Validation should occur before promotion.

---

# Step 8 — Generate Derived Artifacts

Derived artifacts may include:

* PDF
* DOCX
* HTML
* SVG
* PNG
* PowerPoint

Derived artifacts must be generated from canonical artifacts.

Derived artifacts are never canonical.

---

# Step 9 — Generate Production Trace

Produce a Production Trace according to:

```text
EXECUTION_TRACE_CONTRACT.md
```

The trace records:

* inputs
* standards
* templates
* artifacts created
* artifacts modified
* validation
* outputs
* findings

Production traces are runtime artifacts.

---

# Outputs

The Production Engine produces:

* canonical engineering artifacts
* derived engineering artifacts
* production trace
* output manifest

---

# Promotion

Generated artifacts are not automatically considered canonical.

Promotion requires:

* validation
* required reviews
* human approval
* explicit promotion into the project repository

Every promoted artifact shall reference the originating Production Run.

---

# Failure Handling

If production fails:

* stop execution
* preserve partial outputs
* generate a failed Production Trace
* identify unresolved issues
* recommend the next engineering action

Failure must never silently discard engineering work.

---

# Provider Independence

The Production Engine is independent of its executor.

Possible executors include:

* human engineer
* Claude
* ChatGPT
* Gemini
* automated tooling
* hybrid teams

The execution model remains unchanged regardless of executor.

---

# Relationship to the Engineering Reasoning Engine

The Reasoning Engine produces engineering recommendations.

The Production Engine produces engineering artifacts.

The Production Engine depends on approved recommendations.

The Reasoning Engine does not depend on the Production Engine.

This dependency direction must never be reversed.

---

# Success Criteria

A successful production run:

* follows an approved recommendation
* executes the correct transformation
* applies all required standards
* produces valid engineering artifacts
* preserves complete traceability
* generates a complete Production Trace

---

# Guiding Principle

The Engineering Production Engine does not decide what should be built.

It faithfully produces engineering artifacts from approved engineering intent while preserving quality, traceability, and repeatability.
