---
id: CON-ARCH-0002
title: Cohesion
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

# Cohesion

Cohesion describes how closely related the responsibilities inside a component or subsystem are.

High cohesion means the parts belong together.

Low cohesion means unrelated responsibilities have been grouped together.

## Why It Matters

Subsystems should usually have high cohesion.

A subsystem with unrelated responsibilities becomes difficult to understand, test, and evolve.

## Engineering Reasoning

Ask:

- Do these responsibilities naturally belong together?
- Do they change for the same reasons?
- Can the subsystem be explained clearly in one sentence?

## Common Mistakes

- Grouping code by technical layer only.
- Treating file location as architecture.
- Creating a subsystem with multiple unrelated reasons to change.