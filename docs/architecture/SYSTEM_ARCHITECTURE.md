# System Architecture

## Purpose

This document defines the logical architecture of Context Switcher.

It describes the major subsystems, their responsibilities, and the rules governing communication between them.

The objective is to create clear architectural boundaries before implementation begins.

This document intentionally avoids implementation details such as projects, assemblies, or class names.

---

# Architectural Philosophy

Context Switcher is a **modular, knowledge-centric platform**.

The application is delivered as a single Windows desktop application (a modular monolith) while maintaining strong internal boundaries between major capabilities.

Every subsystem should have one primary responsibility.

The canonical subsystem model — the six subsystems defined below — is established by [ADR-0005](../../decisions/ADR-0005-canonical-subsystem-model.md). "Runtime" is a cross-cutting execution concern (see `RUNTIME_MODEL.md`), not a subsystem.

---

# Architectural Principles

## Knowledge First

Knowledge is the application's source of truth.

All subsystems either:

* create knowledge
* consume knowledge
* transform knowledge
* present knowledge

---

## Explicit Dependencies

Subsystems communicate through well-defined interfaces.

No subsystem should directly depend on the internal implementation of another subsystem.

---

## AI Independence

The application should never depend on a specific AI provider.

The AI subsystem provides capabilities.

Provider-specific implementations remain isolated.

---

## Progressive Evolution

The architecture should allow the application to grow without requiring major redesign.

The MVP should remain simple while preserving long-term extensibility.

---

# Core Subsystems

## Experience

### Responsibility

Everything the user sees and interacts with.

Examples:

* Windows
* Navigation
* Dialogs
* Notifications
* Animations
* Accessibility
* Full-screen transition experience

The Experience subsystem owns presentation only.

It should not contain business logic.

---

## Work

### Responsibility

Manage the user's work lifecycle.

Examples:

* Work sessions
* Focus intervals
* Session planning
* Session outcomes
* Context transitions
* Workday orchestration

The Work subsystem understands time and workflow.

---

## Knowledge

### Responsibility

Maintain the user's persistent knowledge.

Examples:

* Projects
* Knowledge Items
* Context Snapshots
* Resume Briefs
* Knowledge relationships
* Knowledge history

This subsystem is the primary source of truth.

---

## AI

### Responsibility

Interpret knowledge and assist the user.

Examples:

* Summarization
* Classification
* Recommendation
* Context reconstruction
* Planning assistance
* Repository evaluation

AI does not own data.

AI proposes.

The user approves.

---

## Integration

### Responsibility

Connect Context Switcher to external systems.

Examples:

* Local Git repositories
* ChatGPT exports
* Future AI providers
* Calendar integrations
* Document imports

External systems should never bypass the Knowledge subsystem.

---

## Productivity Intelligence

### Responsibility

Analyze historical knowledge and work patterns.

Examples:

* Planning accuracy
* Focus trends
* Session analytics
* Recurring blockers
* Knowledge growth
* Productivity insights

This subsystem operates primarily on historical information.

---

# Runtime (Cross-Cutting Concern)

Runtime state — active sessions, timers, drafts, in-progress scans and analyses — is described by `RUNTIME_MODEL.md` as three state categories (Persistent Knowledge, Recoverable Runtime State, Transient UI State).

Runtime is a **cross-cutting execution concern, not a first-class product subsystem**. It is realized within and across the six subsystems above (primarily Work and Experience) and coordinated through the event model of ADR-0004. Per [ADR-0005](../../decisions/ADR-0005-canonical-subsystem-model.md), the canonical subsystem model contains exactly the six subsystems listed above; "Runtime" is not one of them.

---

# Dependency Rules

The following dependency rules are mandatory.

Experience may depend on:

* Work
* Knowledge
* AI

Work may depend on:

* Knowledge

AI may depend on:

* Knowledge
* Integration

Integration may depend on:

* External systems only

Productivity Intelligence may depend on:

* Knowledge
* Work

Knowledge should not depend on AI.

Knowledge should not depend on Experience.

Knowledge should remain the stable center of the architecture.

---

# Information Flow

A typical work session follows this flow:

```text
User
    ↓
Experience
    ↓
Work
    ↓
Knowledge
    ↓
AI (optional)
    ↓
Knowledge
    ↓
Experience
    ↓
User
```

External systems interact through the Integration subsystem.

---

# Architectural Boundaries

Each subsystem owns its own responsibilities.

Subsystems should communicate through contracts rather than implementation details.

Business rules belong in the subsystem responsible for the business concept.

Presentation concerns belong exclusively to the Experience subsystem.

---

# Future Evolution

The architecture should support future capabilities including:

* multiple AI providers
* additional knowledge sources
* repository-aware evaluation
* semantic search
* plugin-style integrations
* enterprise deployment (if ever required)

These capabilities should be introduced without violating existing subsystem boundaries.

---

# Success Criteria

The architecture is successful when:

* responsibilities are clear
* dependencies remain simple
* knowledge remains the source of truth
* AI remains replaceable
* new capabilities can be added with minimal architectural disruption
* the system remains understandable to both humans and AI collaborators
