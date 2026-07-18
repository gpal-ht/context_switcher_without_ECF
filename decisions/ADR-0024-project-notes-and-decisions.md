# ADR-0024: Project Notes & Decisions (Knowledge Capture)

**Status:** Accepted

**Date:** 2026-07-18

**Approved by:** Project Owner (directive: "build all four slices at once",
2026-07-18)

**Related Work:** ADR-0003 (knowledge-item domain model), ADR-0008 (work-engine
foundation), ADR-0009 (session lifecycle & additive persistence), ADR-0014
(shared project resolution); `docs/product/PRODUCT.md` (knowledge capture).

## Context

The work engine records *sessions* and their wrap-ups, but there was no way to
capture the small, durable pieces of knowledge that accrue against a project
between sessions — a free-form **note** ("watch the caching gotcha") or a
**decision** ("use JSON file storage — no server dependency"). This is the
Phase-2 "knowledge capture" gap: when you return to a project, the reasoning and
observations you accumulated are gone unless they happened to land in a session
wrap-up.

## Decision

### One append-only record, discriminated by kind

Add a single immutable `KnowledgeEntry` record (id, projectId, `KnowledgeKind`
{Note, Decision}, text, optional rationale, createdAt) rather than two parallel
types. A note and a decision differ only in whether a rationale is meaningful;
one record keeps the domain, the service, and the JSON round-trip simple.
Knowledge is append-only — a record of what happened and why, not editable
state.

### Additive persistence (backward compatible)

`WorkspaceState` gains a `Knowledge` collection. Per ADR-0009 this is additive
on schema 0.1.0: a file written before this slice has no `knowledge` key and
deserializes to an empty list — no version bump, no migration.

### Service layer, clock-injected

A `KnowledgeService` mirrors `WorkSessionService`: deterministic, clock-injected
(every entry is timestamped from the injected clock), all persistence through
`IWorkspaceStore`. Methods: `AddNote`, `AddDecision`, `ListKnowledge(projectRef)`,
`ListKnowledgeForActiveProject()`. Empty text is a `ValidationException`; an
unknown project is a `NotFoundException` via the shared `ProjectLookup`
(ADR-0014). A null project reference targets the active project, matching the
existing planning-recommendation idiom.

### Surface on resume

Recent knowledge (most recent first, capped) folds additively into
`ResumeBrief`, so returning to a project shows the last session's reflection
*and* the captured notes/decisions. The CLI grows `note add`, `decision add`,
and `knowledge list`; the WinUI shell mirrors the existing panels.

## Consequences

- Knowledge persists across sessions and resurfaces on resume, closing the
  knowledge-capture gap without changing the persistence schema version.
- A single record type keeps the model small; the `KnowledgeKind` discriminator
  is the only branch callers reason about.
- Because entries are append-only, there is no edit/delete surface yet (see
  non-goals).

## Non-goals (this slice)

Editing or deleting entries, tagging/linking knowledge to specific sessions,
full-text search, AI summarization, and a knowledge-only resume brief when a
project has knowledge but no completed session. These are deferred; this slice
delivers capture, scoped listing, resume-brief inclusion, and durable
round-trip persistence.
