# ADR-0005: Canonical Subsystem Model

**Status:** Accepted

**Date:** 2026-07-10

**Approved by:** Project Owner

**Originating Work Request:** WR-0002 — Reconcile the Canonical Subsystem Model

## Context

Context Switcher's canonical documents disagreed on the subsystem model:

- `SYSTEM_ARCHITECTURE.md` and `ENGINEERING_CONTEXT.md` enumerate **six** subsystems (including Integration).
- `SYSTEM_VISION.md` describes **five** "engines" (no Integration).
- `ADR-0002` lists **five** engines by example (no Integration, no Runtime).
- `ADR-0004` lists **seven** subsystems (adding both Runtime and Integration).
- `RUNTIME_MODEL.md` describes "Runtime" as a state category (an execution concern), not a product subsystem.

This inconsistency blocked WR-0001 ("Should Repository Integration become a first-class subsystem?"), which cannot be reasoned about while the canonical status of the Integration subsystem — and of "Runtime" — is undefined. An evidence matrix (source-by-source, authority-ranked) and alternatives evaluation were produced under WR-0002 before this decision.

## Definition — "First-Class Subsystem"

A **first-class subsystem** is a top-level architectural module that:

1. owns exactly one distinct primary **product/domain responsibility**;
2. exposes an explicit **boundary and contract** to other subsystems;
3. participates in the subsystem **dependency-rule graph**; and
4. can be **reasoned about, owned, and tested independently**.

Cross-cutting **execution mechanisms** (runtime-state recovery, checkpointing, the in-process event bus) are **concerns realized within/across subsystems**, not subsystems themselves.

## Decision

The **canonical subsystem model** for Context Switcher is exactly these **six** first-class subsystems:

1. **Experience** — everything the user sees and interacts with (presentation only).
2. **Work** — the user's work lifecycle: sessions, focus intervals, transitions, workday orchestration.
3. **Knowledge** — persistent knowledge and the system's source of truth.
4. **AI** — interpretation and assistance over knowledge; provider-independent.
5. **Integration** — connectivity to external systems (local Git repositories, ChatGPT exports, future providers, documents).
6. **Productivity Intelligence** — analysis of historical knowledge and work patterns.

- **Integration is a first-class subsystem.** It owns a distinct responsibility (external connectivity), has an explicit boundary, and appears in the dependency rules (`AI may depend on Integration`; `Integration may depend on External systems only`).
- **Runtime is NOT a first-class subsystem.** Runtime-state management is a **cross-cutting execution/runtime concern** (see `RUNTIME_MODEL.md`), realized primarily within Work and Experience and coordinated by the event model of ADR-0004.

## Dependency Implications

The dependency rules in `SYSTEM_ARCHITECTURE.md` remain in force and are unchanged by this ADR:

- Experience → Work, Knowledge, AI
- Work → Knowledge
- AI → Knowledge, Integration
- Integration → External systems only
- Productivity Intelligence → Knowledge, Work
- Knowledge depends on nothing above it (stable center).

Runtime, being a concern rather than a subsystem, introduces no new node in this graph; it is expressed through events and checkpoints within existing subsystems.

## Documents Superseded or Corrected

Accepted ADRs are historical evidence; their original decision text is **preserved unmodified**. This ADR **clarifies** them:

- **ADR-0002** — its five-engine list was illustrative, not an exhaustive registry. Clarified: the canonical registry is the six subsystems above (adds Integration). *(Clarify banner added; original text preserved.)*
- **ADR-0004** — its seven-item list served event categorization. Clarified: Integration is first-class; **Runtime is a concern, not a subsystem**. *(Clarify banner added; original text preserved.)*

Current documents aligned to this ADR (minimum set):

- `docs/architecture/SYSTEM_ARCHITECTURE.md` — canonical-model reference + explicit "Runtime is a cross-cutting concern" clarification.
- `docs/engineering/ENGINEERING_CONTEXT.md` — Runtime note + ADR-0005 added to Relevant ADRs.
- `docs/architecture/SYSTEM_VISION.md` — clarifies that its "five engines" are a **user-facing conceptual lens**, not the canonical subsystem registry (Integration is infrastructure-facing).

## Consequences

### Positive
- A single canonical subsystem model; the architecture-consistency gate can pass.
- WR-0001 becomes coherent: it is now "should Repository Integration be promoted **out of** the Integration subsystem into its own subsystem?"
- The Integration boundary (and its dependency direction) is unambiguous.
- "Runtime" terminology no longer collides between "runtime state" and a purported subsystem.

### Negative / Costs
- Two historical ADRs now carry clarification banners (mild indirection).
- SYSTEM_VISION's "five engines" framing requires a reconciliation note to avoid re-introducing the inconsistency.

## Review Triggers

Revisit this decision if:

- a genuine need arises to make runtime-state handling an independently owned/tested subsystem (e.g., a dedicated recovery/runtime service);
- external integrations grow such that Integration must be split (this is exactly WR-0001's scope — a split *within* the confirmed model, not a change to it);
- the subsystem count changes for product reasons (new top-level responsibility).

## Scope Notes

This ADR does **not** design Repository Integration, decompose any subsystem internally, or change source code. It establishes only the canonical subsystem registry and the status of Integration and Runtime.
