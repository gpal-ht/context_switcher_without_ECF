# System Vision

## Purpose

Context Switcher is an AI-assisted personal work operating system.

It is designed to help a knowledge worker move through an entire workday with minimal cognitive friction by preserving context, guiding transitions, and continuously improving understanding of ongoing work.

The system is not a timer application, a task manager, or a chatbot.

It is an orchestration platform for intentional knowledge work.

---

# Core System

The system is composed of five collaborating engines.

> **Note (see [ADR-0005](../../decisions/ADR-0005-canonical-subsystem-model.md)):** The "five engines" below are a **user-facing conceptual lens**, not the canonical subsystem registry. The canonical architecture defines **six subsystems** — these five plus **Integration**, an infrastructure-facing subsystem not surfaced to users as an "engine" (see `SYSTEM_ARCHITECTURE.md`). "Runtime" is a cross-cutting execution concern, not a subsystem.

## 1. Work Engine

Responsible for the flow of work.

Examples:

* work sessions
* focus intervals
* context switching
* workday orchestration
* interruptions
* session lifecycle

The Work Engine understands **time**.

---

## 2. Knowledge Engine

Responsible for preserving information.

Examples:

* projects
* context
* notes
* decisions
* blockers
* documents
* knowledge graph
* context snapshots

The Knowledge Engine understands **work**.

It is the source of truth for the application.

---

## 3. AI Engine

Responsible for understanding and reasoning.

Examples:

* summarization
* recommendations
* planning assistance
* semantic search
* context reconstruction
* prioritization

The AI Engine understands **meaning**.

It never owns user data.

---

## 4. Productivity Intelligence Engine

Responsible for learning over time.

Examples:

* work patterns
* interruption analysis
* productivity trends
* focus statistics
* recurring blockers
* estimation accuracy

This engine understands **history**.

---

## 5. Experience Engine

Responsible for every interaction with the user.

Examples:

* navigation
* windows
* overlays
* notifications
* transitions
* accessibility
* animations

This engine understands **people**.

---

# System Principles

The system follows three principles.

## Knowledge First

Knowledge is the foundation.

AI operates on knowledge.

Knowledge must remain useful even if AI providers change.

---

## AI as an Advisor

AI recommends.

AI explains.

AI never silently makes important decisions.

---

## Human Agency

The user owns:

* priorities
* projects
* decisions
* approvals

Automation should reduce effort, not remove control.

---

# Information Flow

The system operates as a continuous cycle.

```text
Work
    ↓
Capture
    ↓
Knowledge
    ↓
AI Understanding
    ↓
Recommendation
    ↓
Human Decision
    ↓
Work
```

Every work session enriches the knowledge base, which improves future recommendations.

---

# Long-Term Vision

Over time, Context Switcher should become the primary interface through which the user:

* plans work
* performs focused work
* captures knowledge
* resumes projects
* reflects on progress
* receives AI assistance
* continuously improves work habits

The application should become increasingly valuable as it learns from the user's work history while remaining transparent, privacy-conscious, and under the user's control.
