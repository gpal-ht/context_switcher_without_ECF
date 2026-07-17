# ADR-0003: Adopt Knowledge Item as the Fundamental Domain Object

**Status:** Accepted

**Date:** 2026-07-05

## Context

Context Switcher aims to become an AI-assisted personal work operating system rather than a traditional task manager.

The application will ingest and generate information from many sources, including:

* work sessions
* project planning
* user notes
* architectural decisions
* Git repositories
* ChatGPT exports
* future AI providers
* future external integrations

The system requires a consistent way to represent knowledge without forcing all information into a single concept such as a task or note.

## Decision

The fundamental unit of information in the system will be the **Knowledge Item**.

Every meaningful piece of information will be represented as a typed Knowledge Item.

Examples include:

* Decision
* Blocker
* Assumption
* Risk
* Question
* Next Action
* Insight
* Evidence
* Note
* AI Recommendation

Higher-level concepts such as Context Snapshots and Resume Briefs will be composed from Knowledge Items rather than duplicating information.

## Alternatives Considered

### Task-Centric Model

**Pros**

* Familiar to users
* Simple to understand

**Cons**

* Focuses on execution rather than understanding
* Poor representation of reasoning and learning

---

### Note-Centric Model

**Pros**

* Flexible
* Easy to capture information

**Cons**

* Information lacks structure
* Difficult for AI to reason over consistently

---

### Decision-Centric Model

**Pros**

* Preserves reasoning well
* Valuable for software projects

**Cons**

* Many important observations are not decisions
* Too narrow for the broader product vision

## Consequences

### Positive

* A unified knowledge representation across the application.
* Easier AI reasoning and context reconstruction.
* Simpler integration with external context sources.
* Supports future analytics and productivity insights.
* Reduces duplication between features.

### Negative

* Requires thoughtful taxonomy of Knowledge Item types.
* Needs governance to prevent inconsistent usage.
* Adds a small amount of conceptual complexity.

## Architectural Guidance

Knowledge Items are atomic.

They should represent one meaningful piece of information.

Relationships between Knowledge Items should be explicit rather than embedded in free-form text.

Work Sessions create or update Knowledge Items.

Context Snapshots select relevant Knowledge Items.

Resume Briefs summarize selected Knowledge Items for human consumption.

## Review Trigger

Revisit this decision if:

* the taxonomy becomes unmanageable
* performance requires a different representation
* a simpler model clearly provides the same capabilities

## Approval

Approved by: Project Owner

Date: 2026-07-05
