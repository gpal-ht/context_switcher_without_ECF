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

Context Switcher is a **standalone .NET application** (ADR-0010 removed the
former optional ECF integration). Product implementation so far:

* project registry — create, list, archive, and select the active project (ADR-0008)
* work sessions and wrap-up — start/end a session, record the outcome and
  reflection, and read a resume brief on return (ADR-0009)
* local persistence (`%LOCALAPPDATA%\ContextSwitcher\workspace.json`)
* interim CLI harness pending the WinUI 3 shell

```bash
npm run app:test                                   # build + deterministic product tests
npm run app:run -- project add "My Project"        # try the interim CLI
npm run app:run -- session start --objective "..." # start a work session
```

The full context-switch flow (end → switch → resume → start) works today;
timer-driven switching and AI-assisted wrap-ups are later slices (see
`docs/features/project_context_switch.md`).

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
src/            .NET application (Work Engine + interim CLI harness)
docs/           Product, architecture, and standards
decisions/      Architecture Decision Records (ADRs)
acceptance_tests/  Offline project acceptance suite
scripts/        Release manifest / validation tooling
release/        Release process, manifest, and versioning policy
.claude/        Claude Code configuration
```

Additional directories will be introduced as the project evolves.

---

# Standalone Application

Context Switcher is a self-contained Windows application with **no external
framework dependency**. ADR-0010 removed the former optional ECF integration
and its engineering-backend abstraction; there is a single operating mode and
no backend configuration.

```bash
npm test              # offline acceptance suite (builds + runs product tests)
npm run app:test      # product build + deterministic Work Engine tests
```

## Running and packaging the GUI

The WinUI 3 desktop shell builds with Visual Studio MSBuild (ADR-0011):

```powershell
powershell -File scripts/build-gui.ps1 -Run     # build + launch the unpackaged app
powershell -File scripts/package-msix.ps1       # build a signed sideload MSIX (ADR-0020)
```

`package-msix.ps1` produces an installable **development** MSIX signed with a
self-signed dev certificate generated under the gitignored `.local/certs/`
(never committed). Store/production distribution needs a real code-signing
identity — out of scope. The script prints the install commands, or pass
`-Install` to import the cert and install in one step.

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
