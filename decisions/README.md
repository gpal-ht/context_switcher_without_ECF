# Architecture Decision Records

This folder contains Architecture Decision Records for the Context Switcher project.

ADRs document significant product, architecture, and technical decisions.

## ADR Index

| ADR      | Title                                    | Status   | Date       |
|----------|------------------------------------------|----------|------------|
| ADR-0001 | Use WinUI 3 as the Application Framework | Accepted | 2026-07-05 |
| ADR-0002 | Adopt Modular Platform Architecture      | Accepted (clarified by ADR-0005) | 2026-07-05 |
| ADR-0003 | Adopt Knowledge Item as the Fundamental Domain Object | Accepted | 2026-07-05 |
| ADR-0004 | Adopt Event-Driven Application Design     | Accepted (clarified by ADR-0005) | 2026-07-05 |
| ADR-0005 | Canonical Subsystem Model                 | Accepted | 2026-07-10 |
| ADR-0006 | Release and Bundling Strategy              | Superseded by ADR-0010 | 2026-07-13 |
| ADR-0007 | Optional ECF Integration Behind an Engineering-Backend Boundary | Superseded by ADR-0010 | 2026-07-16 |
| ADR-0008 | Work Engine Implementation Foundation      | Accepted | 2026-07-16 |
| ADR-0009 | Work Session Lifecycle and Wrap-Up         | Accepted | 2026-07-17 |
| ADR-0010 | Remove ECF Integration                     | Accepted | 2026-07-17 |

## When to Create an ADR

Create an ADR when a decision:

- changes the architecture
- introduces a major dependency
- affects multiple parts of the system
- is hard to reverse
- involves meaningful trade-offs
- is likely to be questioned later