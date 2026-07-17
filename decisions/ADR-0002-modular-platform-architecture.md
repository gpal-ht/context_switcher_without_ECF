# ADR-0002: Adopt Modular Platform Architecture

**Status:** Accepted

**Date:** 2026-07-05

> **Clarified by [ADR-0005](ADR-0005-canonical-subsystem-model.md) (2026-07-10):** The engines listed in this ADR were illustrative of the modular approach, not an exhaustive subsystem registry. The canonical subsystem model is defined by ADR-0005 and includes **Integration** as a first-class subsystem. The original decision text below is preserved as historical evidence and is **not** modified.

## Context

Context Switcher is evolving beyond a timer or simple productivity app.

The long-term vision includes:

- project context switching
- persistent knowledge capture
- ChatGPT context import
- AI-assisted recommendations
- productivity intelligence
- possible future integrations with calendars, IDEs, documents, and AI providers

These capabilities should not be tightly coupled into one large application layer.

## Decision

Context Switcher will be designed as a modular platform.

The system will separate major capabilities into clear modules or engines:

- Experience Engine
- Work Engine
- Knowledge Engine
- AI Engine
- Productivity Intelligence Engine

The application may begin as a single deployable Windows app, but its internal design should preserve modular boundaries.

## Alternatives Considered

### Simple Monolith

Pros:
- fastest to build
- easiest initial setup
- fewer abstractions

Cons:
- harder to evolve
- AI, UI, storage, and workflow logic may become tangled
- future integrations become risky

### Plugin-First Platform

Pros:
- maximum extensibility
- clean capability isolation

Cons:
- too complex for MVP
- premature abstraction
- higher learning burden

## Consequences

### Positive

- Easier to add AI providers later.
- Easier to import external context sources.
- Better long-term maintainability.
- Clearer separation of responsibilities.
- Supports the long-term product vision.

### Negative

- Slightly more upfront design effort.
- Risk of over-engineering if boundaries become too abstract too early.
- Requires discipline to keep MVP small.

## Architectural Guidance

Start with modular boundaries, not a full plugin system.

The first version should be a modular monolith:

- one Windows application
- clearly separated projects/namespaces later
- explicit interfaces between major engines
- no runtime plugin infrastructure yet

## Review Trigger

Revisit this decision if:

- modular boundaries slow development without clear benefit
- the project remains permanently small
- a real plugin ecosystem becomes necessary
- external integrations become central to the product

## Approval

Approved by: Project Owner

Date: 2026-07-05