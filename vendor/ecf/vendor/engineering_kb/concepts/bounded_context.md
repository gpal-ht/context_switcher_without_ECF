---
id: CON-ARCH-0003
title: Bounded Context
type: engineering_concept
status: draft
version: 0.1.0
created: 2026-07-07
updated: 2026-07-07
relationships:
  supports:
    - DG-ARCH-0001
  related_to:
    - CON-ARCH-0001
    - CON-ARCH-0002
---

# Bounded Context

A Bounded Context is a boundary within which a model, vocabulary, and set of rules are consistent.

The same word may mean different things in different contexts.

## Why It Matters

Bounded Contexts help identify natural subsystem boundaries.

When a capability uses its own vocabulary and rules, it may deserve a separate subsystem.

## Engineering Reasoning

Ask:

- Does this area use different language from the rest of the system?
- Do its rules differ from nearby capabilities?
- Would mixing these concepts create confusion?

## Common Mistakes

- Creating bounded contexts before understanding the domain.
- Assuming every feature is its own bounded context.
- Ignoring vocabulary conflicts.