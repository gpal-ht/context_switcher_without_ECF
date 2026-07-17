---

work_request_id: WR-0001
title: Evaluate Repository Integration Subsystem Boundary
version: 0.1.0
status: submitted
requested_by: project_owner
created: 2026-07-10
priority: medium
----------------

# Engineering Question

Should Repository Integration become a first-class subsystem within Context Switcher?

# Desired Outcome

Produce an Engineering Knowledge Package suitable for a later Engineering Recommendation Report.

# Business Motivation

Repository-aware work evaluation is expected to become an important Context Switcher capability.

Before implementation begins, the project needs to determine whether repository connectivity and repository-aware evaluation justify a separate architectural subsystem.

# Engineering Context Reference

Primary context:

* `docs/engineering/ENGINEERING_CONTEXT.md`

Relevant supporting context may include:

* `docs/architecture/SYSTEM_ARCHITECTURE.md`
* `docs/architecture/AI_ARCHITECTURE.md`
* `docs/product/MVP_SCOPE.md`
* `decisions/ADR-0002-modular-platform-architecture.md`
* `decisions/ADR-0004-event-driven-application-design.md`

# Constraints

* Context Switcher is currently in the foundation and architecture phase.
* Implementation has not started.
* The application uses a modular monolith architecture.
* Repository integration is not part of the initial MVP.
* Local Git versus GitHub API scope remains unresolved.
* AI capabilities must remain provider-independent.
* Human approval is required before production work begins.

# Assumptions

* Repository-aware evaluation will be considered after the MVP foundation is stable.
* Repository connectivity and repository evaluation may remain separate responsibilities.

# Requested Deliverables

* Engineering Intent result
* Engineering Phase result
* Engineering Context Retrieval Result
* Engineering Knowledge Package
* Execution trace
* Output manifest

# Approval Requirements

No production approval is requested.

This Work Request covers classification and retrieval only.

# Success Criteria

The run succeeds when:

* the Work Request is classified predictably
* the correct Engineering Phase is selected
* relevant project context is retrieved without unrelated repository content
* the bundled EKB generates a valid Engineering Knowledge Package
* all task outputs and provenance are recorded
* no canonical project files are modified

# Out of Scope

* Final architectural recommendation
* ADR creation
* Architecture modification
* Source-code implementation
* Repository scanner design

# Update (2026-07-10) — Unblocked by ADR-0005

The subsystem-model inconsistency that blocked this Work Request is resolved by
[ADR-0005](../decisions/ADR-0005-canonical-subsystem-model.md) (via WR-0002): the
canonical model has **six** subsystems and **Integration is a first-class subsystem**.

This Work Request is therefore now coherent and is best read as: *"Should Repository
Integration be promoted **out of** the existing Integration subsystem into its own
first-class subsystem, or remain within Integration?"* Status: **unblocked; ready for
the reasoning/recommendation stage** (still pending the framework-side WF-REASON-0001 /
recommendation task — see PROJECT_ECF_ADOPTION_REPORT.md).
