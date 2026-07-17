# ADR-0001: Future Introduction of an Engineering Intermediate Representation (EIR)

**Status:** Deferred

**Date:** 2026-07-06

---

# Context

Engineering Control Framework currently defines canonical engineering artifacts as the source of truth.

Examples include:

* Product Requirements Documents
* Product Design Documents
* System Design Documents
* Architecture Decision Records
* Threat Models

These artifacts are human-readable, version controlled, and reviewed.

As the framework evolves, engineering activities may require a richer internal representation than independent Markdown documents.

---

# Problem

Multiple engineering artifacts often describe overlapping concepts.

Examples include:

* features
* requirements
* domain concepts
* quality attributes
* architectural decisions
* implementation plans

Maintaining consistency across many artifacts becomes increasingly difficult.

Future AI capabilities may also require structured engineering knowledge rather than unstructured documents.

---

# Proposed Future Direction

Introduce an **Engineering Intermediate Representation (EIR)**.

The EIR would become the canonical engineering model.

Engineering artifacts would become rendered views of the EIR rather than independent sources of truth.

Conceptually:

Idea
↓

Engineering Intermediate Representation

↓

Engineering Transformations

↓

Rendered Engineering Artifacts

↓

Implementation

---

# Why This Is Deferred

ECF is currently in its foundational stage.

The framework should first validate:

* engineering principles
* standards
* transformations
* artifacts
* reviews
* quality gates

through real projects.

Introducing an EIR now would significantly increase framework complexity before sufficient experience has been gathered.

---

# Decision

ECF v0.x will use canonical engineering artifacts as the engineering source of truth.

The Engineering Intermediate Representation remains a strategic direction for a future major version.

No implementation work will begin until:

* multiple projects have successfully adopted ECF
* common engineering patterns have emerged
* artifact relationships are well understood
* clear benefits outweigh additional complexity

---

# Benefits of Delaying

* Simpler framework adoption
* Faster validation through real projects
* Better understanding of engineering knowledge
* Reduced architectural risk
* Opportunity to design the EIR using empirical evidence rather than assumptions

---

# Review Trigger

Revisit this ADR after:

* at least three substantial projects have been engineered using ECF
* recurring consistency problems appear across artifacts
* AI transformations demonstrate the need for structured engineering knowledge

---

# Guiding Principle

> Build today's framework around today's needs while deliberately preserving tomorrow's possibilities.
