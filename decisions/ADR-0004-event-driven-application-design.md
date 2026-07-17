# ADR-0004: Adopt Event-Driven Application Design

**Status:** Accepted

**Date:** 2026-07-05

> **Clarified by [ADR-0005](ADR-0005-canonical-subsystem-model.md) (2026-07-10):** For event categorization this ADR lists "Runtime" and "Integration" among subsystems. Per ADR-0005, **Integration is a first-class subsystem**, but **Runtime is a cross-cutting execution concern, not a first-class subsystem**. The original decision text below is preserved as historical evidence and is **not** modified.

---

# Context

Context Switcher consists of several independent subsystems:

* Experience
* Work
* Knowledge
* Runtime
* AI
* Integration
* Productivity Intelligence

Many user actions naturally affect multiple subsystems.

For example:

A work session starts.

* The Work subsystem starts the session.
* The Runtime subsystem starts tracking it.
* The Experience subsystem updates the UI.
* The Productivity subsystem begins collecting metrics.
* AI may prepare contextual information.
* The Knowledge subsystem may later record the session.

If these subsystems invoke each other directly, the architecture becomes tightly coupled and difficult to evolve.

The application requires a communication mechanism that allows subsystems to remain independent while reacting to meaningful changes.

---

# Decision

Context Switcher will adopt an **event-driven internal architecture**.

Subsystems communicate primarily through meaningful domain and runtime events.

Events represent something that has already happened.

Events are not commands.

The first implementation will remain an in-process event system.

No external message broker, distributed queue, or service bus is required.

---

# Motivation

An event-driven architecture supports the project's long-term goals:

* modular platform
* AI independence
* knowledge-first design
* future integrations
* productivity analytics
* recoverable runtime

It also allows new capabilities to subscribe to existing events without modifying the subsystem that publishes them.

---

# Architectural Guidance

Events should describe completed actions.

Good examples:

* WorkSessionStarted
* WorkSessionPaused
* WorkSessionCompleted
* ContextSwitchRequested
* ContextSwitchCompleted
* KnowledgeItemCreated
* KnowledgeItemUpdated
* KnowledgeItemSuperseded
* ContextSnapshotCreated
* WrapUpSubmitted
* RepositoryAnalysisCompleted
* AIRecommendationGenerated
* AIRecommendationApproved
* AIRecommendationRejected

Avoid events that describe implementation details such as:

* ButtonClicked
* TimerLabelChanged
* ViewLoaded
* TextBoxChanged

These belong to the UI layer rather than the domain.

---

# Event Categories

## Domain Events

Represent changes to persistent knowledge.

Examples:

* KnowledgeItemCreated
* KnowledgeItemUpdated
* KnowledgeRelationshipCreated
* ContextSnapshotCreated
* ResumeBriefGenerated

---

## Runtime Events

Represent changes occurring while the application is running.

Examples:

* WorkSessionStarted
* TimerPaused
* TimerResumed
* ContextSwitchRequested
* DraftWrapUpUpdated
* SessionCheckpointCreated

---

## Integration Events

Represent activity from external systems.

Examples:

* RepositoryOpened
* RepositoryScanCompleted
* ChatGPTImportCompleted
* ExternalDocumentImported

---

## AI Events

Represent AI processing.

Examples:

* AIAnalysisRequested
* AIRecommendationGenerated
* AIRecommendationAccepted
* AIRecommendationRejected
* AISummaryGenerated

---

# Event Ownership

Every event has:

* one publisher
* zero or more subscribers

The publishing subsystem owns the event definition.

Subscribers must not modify the publisher's internal state.

---

# Event Flow Example

A simplified work session might look like:

```text
User starts work session
        │
        ▼
WorkSessionStarted
        │
        ├────────► Runtime
        │           Creates checkpoint
        │
        ├────────► Experience
        │           Updates timer UI
        │
        ├────────► Productivity
        │           Begins metrics collection
        │
        └────────► AI
                    Prepares context (optional)
```

Later:

```text
WrapUpSubmitted
        │
        ├────────► Knowledge
        │           Creates Knowledge Items
        │
        ├────────► Context
        │           Updates Context Snapshot
        │
        ├────────► Productivity
        │           Updates statistics
        │
        └────────► AI
                    Generates summary (optional)
```

---

# Event Design Rules

Events should:

* be named in past tense
* represent business meaning
* contain only relevant data
* include timestamp
* identify the originating subsystem
* be immutable after publication

Events should not:

* expose UI implementation
* replace commands
* become a generic notification mechanism
* contain unnecessary payload

---

# Commands vs Events

The architecture distinguishes between commands and events.

**Command**

A request for something to happen.

Examples:

* StartWorkSession
* PauseTimer
* SubmitWrapUp
* ImportChatGPTContext

Commands express intent.

---

**Event**

A record that something has happened.

Examples:

* WorkSessionStarted
* TimerPaused
* WrapUpSubmitted
* ChatGPTImportCompleted

Events express facts.

---

# Alternatives Considered

## Direct Service Calls

### Pros

* Simple
* Easy to debug
* Familiar

### Cons

* Tight coupling
* Difficult to extend
* AI and analytics become intertwined with business logic

---

## Full Event Bus / Message Broker

### Pros

* Highly scalable
* Distributed architecture
* Reliable messaging

### Cons

* Significant complexity
* Unnecessary for a Windows desktop MVP
* Harder to learn and maintain

---

## Hybrid Architecture (Chosen)

Commands initiate work.

Events communicate completed work.

Benefits:

* Simple for MVP
* Modular
* Easy to extend
* Fits desktop application architecture

---

# Consequences

## Positive

* Strong subsystem separation
* Easier feature growth
* Natural fit for AI integration
* Natural fit for analytics
* Supports checkpointing
* Supports runtime recovery
* Improves auditability

## Negative

* Event naming requires discipline
* Event chains can become difficult to follow
* Documentation becomes important
* Debugging tools should visualize event flow

---

# Future Considerations

Future versions may introduce:

* event replay
* event visualization
* workflow tracing
* plugin subscriptions
* telemetry
* scripting
* automation

These should build upon the same event model rather than replacing it.

---

# Review Trigger

Revisit this ADR if:

* event-driven design introduces unnecessary complexity
* debugging becomes significantly more difficult
* subsystem boundaries become unclear
* distributed deployment becomes a product requirement

---

# Approval

Approved by: Project Owner

Date: 2026-07-05
