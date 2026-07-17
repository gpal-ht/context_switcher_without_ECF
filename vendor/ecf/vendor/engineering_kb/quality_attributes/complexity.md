---
id: QA-0002
title: Complexity
type: quality_attribute
status: draft
version: 0.1.0
created: 2026-07-07
updated: 2026-07-07
relationships:
  affected_by:
    - DG-ARCH-0001
    - CON-ARCH-0001
    - CON-ARCH-0002
---

# Complexity

Complexity is the amount of mental effort required to understand, change, and verify a system.

## Why It Matters

Complexity increases engineering risk.

Subsystems can reduce complexity by creating clear boundaries, but they can also increase complexity if introduced prematurely.

## Engineering Reasoning

Ask:

- Does this design reduce reasoning effort?
- Does it introduce coordination cost?
- Is the abstraction easier to understand than the problem it hides?

## Common Mistakes

- Adding architecture to appear organized.
- Splitting simple behavior into too many parts.
- Moving complexity instead of reducing it.