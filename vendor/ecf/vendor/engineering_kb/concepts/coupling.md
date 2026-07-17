---
id: CON-ARCH-0001
title: Coupling
type: engineering_concept
status: draft
version: 0.1.0
created: 2026-07-07
updated: 2026-07-07
relationships:
  supports:
    - DG-ARCH-0001
  affects:
    - QA-0001
    - QA-0002
  related_to:
    - CON-ARCH-0003
---

# Coupling

Coupling describes how strongly one part of a system depends on another.

Low coupling means a component can change with limited impact elsewhere.

High coupling means changes often ripple across the system.

## Why It Matters

Coupling affects maintainability, testability, and architectural flexibility.

Subsystem boundaries are often introduced to reduce harmful coupling.

## Engineering Reasoning

Ask:

- What does this component need to know about another component?
- Can one change without forcing the other to change?
- Are implementation details leaking across boundaries?

## Common Mistakes

- Treating all coupling as bad.
- Hiding coupling behind unnecessary abstractions.
- Splitting code without reducing real dependencies.