---
work_request_id: WR-0002
title: Reconcile the Canonical Subsystem Model
version: 0.1.0
status: completed
requested_by: project_owner
created: 2026-07-10
priority: high
---

# Engineering Question

What is the canonical first-class subsystem model for Context Switcher?

# Desired Outcome

A resolved, single source of architectural truth for the subsystem model, delivered as:

* an Architecture Decision Record (ADR) defining the canonical subsystem model;
* a single canonical subsystem enumeration;
* an explicit definition of "first-class subsystem";
* an explicit status for Integration and for Runtime;
* identified canonical-document updates required to align with the ADR;
* updated architecture-consistency acceptance tests (with severity levels).

# Business Motivation

Current project artifacts disagree on whether **Integration** and **Runtime** are
first-class subsystems (five- vs six- vs seven-subsystem enumerations across
SYSTEM_ARCHITECTURE, SYSTEM_VISION, ENGINEERING_CONTEXT, ADR-0002, and ADR-0004).

This inconsistency directly blocks WR-0001 ("Should Repository Integration become a
first-class subsystem?"): the question cannot be answered coherently while the
canonical status of the Integration subsystem itself is undefined. Resolving the
subsystem model is a prerequisite for reasoning about WR-0001.

# Engineering Context Reference

* `docs/engineering/ENGINEERING_CONTEXT.md`
* `docs/architecture/SYSTEM_ARCHITECTURE.md`
* `docs/architecture/SYSTEM_VISION.md`
* `docs/architecture/RUNTIME_MODEL.md`
* `decisions/ADR-0002-modular-platform-architecture.md`
* `decisions/ADR-0004-event-driven-application-design.md`
* `PROJECT_ECF_ADOPTION_REPORT.md` (finding F-1)

# Constraints

* Context Switcher is in the foundation / architecture phase; implementation has not started.
* Modular monolith architecture; knowledge-first; AI provider independent.
* Canonical architecture changes require an ADR and human approval.
* Accepted ADRs are historical evidence; original decision text must be preserved (supersede/clarify rather than rewrite).
* This Work Request must not modify `vendor/ecf/`, bundled EKB, or refresh vendor bundles.

# Assumptions

* The disagreement is a documentation/consistency gap, not a genuine architectural fork.
* SYSTEM_ARCHITECTURE.md is the most authoritative *architecture* description among current documents.
* Runtime-state management is described by RUNTIME_MODEL.md as an execution concern rather than a product subsystem.

# Requested Deliverables

* Evidence matrix (source-by-source subsystem comparison) — runtime/review artifact
* Alternatives evaluation
* Engineering Recommendation (pre-approval)
* ADR-0005: Canonical Subsystem Model (post-approval)
* Aligned canonical documents (post-approval, minimum set)
* Updated architecture-consistency acceptance tests with severity levels

# Priority

High — blocks WR-0001.

# Approval Requirements

* Human Approval required before creating the ADR or modifying any canonical architecture document (Step 4 decision boundary).
* Architecture Review (the decision is an architecture boundary change).

# Success Criteria

* Exactly one canonical subsystem enumeration is defined and approved.
* "First-class subsystem" is precisely defined.
* Integration and Runtime each have an unambiguous status.
* WR-0001 becomes a coherent, answerable question.
* Architecture-consistency acceptance tests pass against the approved model and distinguish decision-blockers from general coverage gaps.
* ADR history is preserved.

# Out of Scope

* Repository Integration design (WR-0001's subject)
* Source-code implementation
* Module decomposition inside subsystems
* ECF or EKB changes
* Vendor bundle refresh

# Resolution (2026-07-10)

**Completed.** Human-approved decision: **Alternative B**.

* Canonical model (6): Experience, Work, Knowledge, AI, Integration, Productivity Intelligence.
* Integration = first-class subsystem. Runtime = cross-cutting execution concern (not a subsystem).
* Decision recorded in [ADR-0005](../decisions/ADR-0005-canonical-subsystem-model.md).
* ADR-0002 and ADR-0004 preserved as historical evidence (clarify banners added; original text unmodified).
* Aligned: `SYSTEM_ARCHITECTURE.md`, `ENGINEERING_CONTEXT.md`, `SYSTEM_VISION.md`; ADR index updated.
* Architecture-consistency acceptance test is now severity-aware; WR-0002 gate = PASS (blocking=0).
* Evidence + recommendation: `runtime/work_requests/WR-0002/` (git-ignored).
