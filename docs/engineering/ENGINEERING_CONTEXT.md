# Engineering Context

## Project

Context Switcher

## Current Phase

MVP implementation. Foundation and architecture design are established;
product implementation began with the Work Engine project registry
(ADR-0008) and work-session lifecycle (ADR-0009). Context Switcher is a
standalone .NET application with no external framework dependency; the
former optional ECF integration was removed (ADR-0010).

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