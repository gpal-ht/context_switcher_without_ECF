# Knowledge Architecture

## Purpose

This document defines how knowledge is represented, evolves, and flows through Context Switcher.

The application is built on the principle that **knowledge is the primary asset**. Timers, AI, Git repositories, and productivity analytics all exist to create, refine, or consume knowledge.

This document describes the conceptual architecture only. It does not prescribe implementation details or storage technologies.

---

# Core Principles

## Knowledge First

Knowledge is the application's source of truth.

AI interprets knowledge.

The user makes decisions.

---

## Preserve Meaning

The goal is not to store data.

The goal is to preserve:

* intent
* reasoning
* decisions
* assumptions
* evidence
* progress

---

## Knowledge Evolves

Knowledge should evolve rather than be replaced.

Users refine understanding over time.

The application should preserve both the current state and the history of that evolution.

---

# Fundamental Concepts

## Project

A long-lived body of work.

Projects own work sessions, context, and knowledge.

---

## Work Session

An intentional period of focused work.

Work Sessions produce or update knowledge.

---

## Knowledge Item

The smallest meaningful unit in the system.

Knowledge Items are atomic.

Examples include:

* Decision
* Blocker
* Assumption
* Risk
* Question
* Next Action
* Evidence
* Insight
* Note
* AI Recommendation

Knowledge Items are typed.

They represent meaning rather than storage structures.

---

## Knowledge Event

A record of how a Knowledge Item changes over time.

Examples:

* Created
* Edited
* Accepted
* Superseded
* Archived
* Linked
* Referenced

Knowledge Events preserve provenance.

They are append-only.

---

## Context Snapshot

A curated collection of Knowledge Items at a point in time.

A Context Snapshot represents the knowledge required to resume productive work.

It does not duplicate knowledge.

It references existing Knowledge Items.

---

## Resume Brief

A human-friendly summary generated from a Context Snapshot.

Initially, Resume Briefs may be user-authored.

Later, AI may assist with generating them.

---

# Knowledge Flow

Knowledge moves through the system in a continuous cycle.

```text
Evidence
    ↓
Knowledge Capture
    ↓
Knowledge Items
    ↓
Knowledge Events
    ↓
Context Snapshot
    ↓
Resume Brief
    ↓
User Work
    ↓
New Evidence
```

Every completed work session enriches the knowledge available to future work sessions.

---

# Knowledge Sources

Knowledge may originate from:

* User input
* Work Sessions
* Local Git repositories
* Imported ChatGPT exports
* Imported documents
* Future external integrations
* AI-generated suggestions (after user review)

Every Knowledge Item should record its origin.

---

# Provenance

Every Knowledge Item should answer:

* Who created it?
* When was it created?
* Why was it created?
* What evidence supports it?
* Has it changed?
* What is its current status?

Provenance is essential for user trust and AI explainability.

---

# Knowledge Relationships

Knowledge does not exist in isolation.

Relationships between Knowledge Items are first-class concepts.

Examples include:

* supports
* contradicts
* answers
* blocks
* depends on
* supersedes
* derived from
* related to

These relationships allow the application to reason over connected knowledge rather than isolated notes.

---

# Current State vs. History

The application distinguishes between:

**Current State**

The latest accepted understanding presented to the user.

**History**

The sequence of Knowledge Events that explains how the current state evolved.

Users primarily interact with the current state.

History is available for review, auditing, and AI reasoning.

---

# AI Interaction

AI does not own knowledge.

AI may:

* summarize
* classify
* connect related Knowledge Items
* identify inconsistencies
* generate recommendations
* reconstruct context

AI must not silently modify accepted knowledge.

User approval is required before AI-generated changes become part of the knowledge base.

---

# Design Principles

The knowledge architecture should:

* preserve context over time
* encourage intentional work
* reduce cognitive load
* support explainable AI
* remain provider-independent
* allow new knowledge sources without redesign
* evolve without losing historical understanding

---

# Future Considerations

Future versions may introduce:

* semantic search
* knowledge graph visualization
* automatic relationship discovery
* duplicate detection
* confidence scoring
* knowledge health metrics
* AI-assisted knowledge maintenance

These capabilities should build on the existing architecture rather than replace it.
