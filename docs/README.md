# Documentation Guide

Welcome to the Context Switcher documentation.

The documentation is organized by purpose rather than by implementation.

The goal is to make it easy for both humans and AI assistants to understand the product before making changes.

---

# Reading Order

New contributors should read the documents in the following order:

1. `../README.md`
2. `product/PRODUCT.md`
3. `product/PRODUCT_PRINCIPLES.md`
4. `product/MVP_SCOPE.md`
5. `engineering/ENGINEERING.md`
6. `../CLAUDE.md`

After understanding the project vision, continue with the architecture documents.

---

# Product

These documents describe **what** we are building and **why**.

| Document                        | Purpose                     |
| ------------------------------- | --------------------------- |
| `product/PRODUCT.md`            | Product vision and mission  |
| `product/PRODUCT_PRINCIPLES.md` | Product decision principles |
| `product/MVP_SCOPE.md`          | Current MVP boundaries      |

---

# Engineering

These documents define **how** the project is engineered.

| Document                                  | Purpose                                 |
| ----------------------------------------- | --------------------------------------- |
| `engineering/ENGINEERING.md`              | Engineering constitution and governance |
| `engineering/ENGINEERING_WORKFLOW.md`     | Feature lifecycle, gates, approval flow |
| `engineering/ENGINEERING_ORGANIZATION.md` | Engineering roles and specialist responsibilities |

Future additions:

* Coding Standards
* Quality Gates
* Review Process
* Definition of Done

---

# Architecture

These documents describe **how the system is designed**.

| Document                                 | Purpose                            |
| ---------------------------------------- | ---------------------------------- |
| `architecture/SYSTEM_VISION.md`          | High-level system vision           |
| `architecture/DOMAIN_MODEL.md`           | Core business concepts             |
| `architecture/WORK_SESSION_MODEL.md`     | Work session lifecycle             |
| `architecture/KNOWLEDGE_ARCHITECTURE.md` | Knowledge model and lifecycle      |
| `architecture/AI_ARCHITECTURE.md`        | AI boundaries and responsibilities |

Future additions:

* System Context
* System Architecture
* Data Model
* UI Architecture
* Integration Architecture

---

# Features

Each feature should have its own specification.

Typical contents include:

* problem statement
* goals
* user flow
* requirements
* risks
* acceptance criteria

Current features:

| Document                             | Status |
| ------------------------------------ | ------ |
| `features/project_context_switch.md` | Draft  |

---

# Decisions

Architectural decisions are stored separately.

See:

`../decisions/`

Each Architecture Decision Record (ADR) explains:

* why a decision was needed
* alternatives considered
* chosen approach
* consequences
* review triggers

---

# Research

Research documents capture information that informs design but is not yet part of the product.

Examples include:

* technology evaluations
* API investigations
* productivity research
* AI capability research

Research does not become architecture until it is accepted through the ADR process.

---

# Documentation Principles

Every document should answer one primary question.

Avoid mixing unrelated concerns.

When introducing a significant new concept:

1. Check whether it already exists.
2. Determine which subsystem it belongs to.
3. Decide whether an ADR is required.
4. Update this index if a new document is added.

---

# Living Documentation

The documentation evolves with the product.

Documents should be:

* concise
* reviewed
* version controlled
* internally consistent

The repository should remain understandable even to someone who has never participated in the project's discussions.
