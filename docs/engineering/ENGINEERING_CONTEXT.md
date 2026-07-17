# Engineering Context

## Project

Context Switcher

## Current Phase

MVP implementation. Foundation and architecture design are established;
product implementation was approved by the project owner on 2026-07-16 and
began with the Work Engine project registry (ADR-0008). Standalone mode is
the required baseline; ECF remains an optional backend (ADR-0007).

## Product Mission

AI-assisted personal work operating system for context switching, knowledge preservation, and work-session evaluation.

## Current Architecture

- Experience
- Work
- Knowledge
- AI
- Integration
- Productivity Intelligence

> Canonical subsystem model per ADR-0005. Runtime is a cross-cutting execution concern, not a subsystem.

## Active Constraints

- Native Windows application
- C# / .NET / WinUI 3
- Modular monolith
- Knowledge-first
- AI provider independent
- Human approval before implementation

## Relevant ADRs

- ADR-0001: Use WinUI 3
- ADR-0002: Modular Platform Architecture
- ADR-0003: Knowledge Item Domain Model
- ADR-0004: Event-Driven Application Design
- ADR-0005: Canonical Subsystem Model

## Known Open Questions

- Repository integration scope
- Local Git vs GitHub API
- Repository evaluation evidence requirements
- AI recommendation boundaries