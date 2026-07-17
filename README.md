# Context Switcher

> **An AI-assisted personal work operating system for Windows.**

## Vision

Context Switcher is a native Windows application that helps users preserve, transfer, and improve their work context.

Rather than acting as a simple timer or task manager, the application aims to become a trusted work companion that reduces the cognitive cost of switching between projects, captures knowledge as work progresses, and provides thoughtful AI-assisted recommendations while keeping the user in control.

The long-term vision is to build an application that understands:

* what the user is working on
* where they left off
* what decisions have been made
* what remains unfinished
* how the user's work habits evolve over time

The application should help users return to productive work with minimal mental overhead.

---

# Guiding Principles

This project is built on five core principles:

1. **Design First**
   We understand the problem before writing code.

2. **Human in Control**
   AI assists with engineering and productivity but never replaces human decision-making.

3. **Quality by Design**
   Architecture, testing, accessibility, maintainability, and documentation are considered from the beginning.

4. **Small, Reviewable Changes**
   Large rewrites are avoided. Every change should be understandable and reviewable.

5. **Documentation is Part of the Product**
   Engineering decisions are captured alongside the source code.

---

# Project Status

**Current Phase**

MVP implementation (Stage 1 — Assisted Context Switching)

The repository foundation (product vision, governance, architecture,
workflow) is established. Product implementation began 2026-07-16 with the
Work Engine project registry (ADR-0008):

* create, list, and archive projects
* select the active project
* local persistence (`%LOCALAPPDATA%\ContextSwitcher\workspace.json`)
* interim CLI harness pending the WinUI 3 shell

```bash
npm run app:test                              # build + deterministic product tests
npm run app:run -- project add "My Project"   # try the interim CLI
```

Work sessions, wrap-up, and the full context-switch flow are the next
slices (see `docs/features/project_context_switch.md`).

---

# Long-Term Roadmap

## Phase 1 — Intentional Context Switching

* Focus timer
* Background operation
* Session management
* Wrap-up workflow
* Context transition experience
* Local persistence

## Phase 2 — Persistent Work Context

* Projects
* Tasks
* Notes
* Decisions
* Knowledge capture
* Context restoration

## Phase 3 — AI Work Companion

* Session summaries
* Context reconstruction
* Intelligent recommendations
* Decision support
* Planning assistance

## Phase 4 — Productivity Intelligence

* Work pattern analysis
* Focus trends
* Context-switch analysis
* Productivity insights
* Personalized coaching

---

# Engineering Philosophy

This repository follows a **design-first engineering process**.

Every feature progresses through the following lifecycle:

1. Product Brief
2. Requirements
3. UX Design
4. Architecture Design
5. Data Model
6. Risk Review
7. Test Strategy
8. Implementation Plan
9. Human Approval
10. Implementation
11. Review
12. Merge

Implementation begins only after explicit approval.

---

# Repository Structure

```text
docs/           Product, architecture, and standards
decisions/      Architecture Decision Records (ADRs)
prompts/        Reusable AI prompts
templates/      Project document templates
config/         Explicit project configuration (engineering backend)
scripts/        Release tooling and the ECF adapter scripts
acceptance_tests/  Offline project acceptance suite
release/        Release process, manifest, and compatibility policy
vendor/ecf/     Optional bundled ECF (ecf backend only)
.claude/        Claude Code configuration
```

Additional directories will be introduced as the project evolves.

---

# Engineering Backends — ECF Is Optional

Context Switcher supports two explicit engineering backends
([ADR-0007](decisions/ADR-0007-optional-ecf-integration.md),
[docs/engineering/ENGINEERING_BACKENDS.md](docs/engineering/ENGINEERING_BACKENDS.md)):

- **`standalone`** (default when unconfigured) — develop, test, validate, and
  package Context Switcher with **no ECF** repository, bundle, or environment.
  ECF-only operations refuse honestly (`UNSUPPORTED_CAPABILITY`) instead of
  pretending ECF guarantees exist.
- **`ecf`** — ECF-integrated mode through a narrow, validated adapter over the
  bundled `vendor/ecf/`. Explicitly requested ECF that is missing or
  incompatible is a hard configuration failure, never a silent fallback.

```bash
npm run backend            # show the active backend + capability report
npm run test:standalone    # required gate — no ECF needed
npm run test:ecf           # standalone suite + ECF integration suite
```

Mode is selected in `config/engineering-backend.yaml` (or the
`CONTEXT_SWITCHER_ENGINEERING_BACKEND` environment variable). This repository
commits `ecf` because it ships a pinned, validated bundle.

---

# Core Documents

| Document         | Purpose                                         |
| ---------------- | ----------------------------------------------- |
| `README.md`      | Project overview and onboarding                 |
| `ENGINEERING.md` | Engineering constitution and governance         |
| `CLAUDE.md`      | Instructions for Claude Code                    |
| `docs/`          | Product, architecture, and design documentation |
| `decisions/`     | Architecture Decision Records                   |

---

# Technology Direction

Target platform:

* Windows 11

Planned technology stack:

* C#
* .NET
* WinUI 3
* MVVM architecture

Technology choices are documented through Architecture Decision Records and may evolve with project needs.

---

# AI Collaboration

AI is treated as an engineering collaborator.

Its responsibilities include:

* exploring design alternatives
* identifying risks
* reviewing architecture
* explaining trade-offs
* proposing implementation plans
* reviewing code

Implementation authority remains with the human project owner.

---

# Success Criteria

The project will be considered successful if it:

* Helps users switch contexts intentionally.
* Preserves valuable work context.
* Reduces cognitive overhead.
* Encourages disciplined work habits.
* Provides transparent, trustworthy AI assistance.
* Demonstrates high engineering quality and maintainability.

---

# License

To be determined.
