---
id: EX-ARCH-0001
title: Subsystem Split Examples
type: example
status: draft
version: 0.1.0
created: 2026-07-07
updated: 2026-07-07
relationships:
  illustrates:
    - DG-ARCH-0001
    - CON-ARCH-0001
    - CON-ARCH-0002
    - PAT-ARCH-0001
---

# Subsystem Split Examples

## Example 1 — Good Subsystem Split

A desktop productivity app has separate responsibilities for:

- work session timing
- persistent project knowledge
- AI recommendations

These capabilities change for different reasons.

A good split may create:

- Work subsystem
- Knowledge subsystem
- AI subsystem

Why this works:

- responsibilities are clear
- coupling can be controlled
- testing is easier
- each subsystem has a distinct vocabulary

## Example 2 — Poor Subsystem Split

A small app has one screen with three buttons.

The developer creates separate subsystems for:

- button rendering
- button state
- button styling

Why this is poor:

- the split does not reduce reasoning cost
- coordination increases
- abstractions are premature
- complexity increases without clear benefit

## Example 3 — Delay the Split

A new feature is growing, but the vocabulary and responsibilities are still unclear.

The better choice may be to keep the code together temporarily while collecting evidence.

Delay is appropriate when the boundary is not yet understood.