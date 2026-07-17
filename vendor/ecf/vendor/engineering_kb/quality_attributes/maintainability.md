---
id: QA-0001
title: Maintainability
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

# Maintainability

Maintainability is the ease with which software can be understood, changed, tested, and safely evolved.

## Why It Matters

Most software cost occurs after initial implementation.

Maintainable systems reduce the cost and risk of future change.

## Engineering Signals

Maintainability improves when:

- responsibilities are clear
- coupling is controlled
- cohesion is high
- tests can be written without excessive setup
- changes are localized

Maintainability decreases when:

- unrelated concerns are mixed
- implementation details leak across boundaries
- small changes require broad edits