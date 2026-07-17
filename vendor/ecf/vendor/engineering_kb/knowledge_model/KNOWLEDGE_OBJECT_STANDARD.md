# KNOWLEDGE_OBJECT_STANDARD.md

# Purpose

This standard defines the required structure for every Knowledge Object in the Engineering Knowledge Base (EKB).

A Knowledge Object is the atomic unit of reusable engineering knowledge.

No engineering knowledge should be added to EKB unless it is represented as a valid Knowledge Object.

---

# Core Principle

Every Knowledge Object must be:

* identifiable
* versioned
* typed
* traceable
* relationship-aware
* human-readable
* machine-readable

EKB is not a folder of Markdown files.

EKB is a knowledge graph represented through version-controlled files.

---

# Knowledge Object Structure

Every Knowledge Object has four parts:

1. Identity
2. Metadata
3. Knowledge Content
4. Relationships

---

# 1. Identity

Every Knowledge Object must have a stable ID.

IDs must not change when files are renamed or moved.

## ID Prefixes

| Object Type          | Prefix |
| -------------------- | ------ |
| Decision Guide       | DG     |
| Engineering Concept  | CON    |
| Engineering Pattern  | PAT    |
| Quality Attribute    | QA     |
| Example              | EX     |
| Reference            | REF    |

## Recommended ID Format

```text
<TYPE>-<DOMAIN>-<NUMBER>
```

Examples:

```text
DG-ARCH-0001
CON-ARCH-0001
PAT-ARCH-0001
QA-0001
EX-ARCH-0001
REF-0001
```

---

# 2. Metadata

Every Knowledge Object must begin with YAML front matter.

Minimum required metadata:

```yaml
---
id: DG-ARCH-0001
title: Should I Introduce Another Subsystem?
type: decision_guide
status: draft
version: 0.1.0
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Recommended metadata:

```yaml
discipline:
  - architecture

tags:
  - subsystem
  - modularity

confidence: medium

owner: engineering_kb
```

---

# 3. Knowledge Content

The body of the file contains the human-readable explanation.

Content should be:

* practical
* decision-oriented
* example-driven
* trade-off aware
* technology-neutral where practical

Knowledge content should explain reasoning, not merely state rules.

---

# 4. Relationships

Relationships should be expressed in metadata when possible.

Example:

```yaml
relationships:
  requires:
    - CON-ARCH-0001
  supports:
    - QA-0001
  illustrated_by:
    - EX-ARCH-0001
  related_to:
    - DG-ARCH-0002
```

## Recommended Relationship Types

| Relationship   | Meaning                                     |
| -------------- | ------------------------------------------- |
| requires       | This object depends on another object       |
| supports       | This object supports another object         |
| explains       | This object explains another object         |
| implements     | This object implements a concept            |
| optimizes      | This object improves a quality attribute    |
| affects        | This object impacts another object          |
| contrasts_with | This object should be compared with another |
| illustrated_by | This object is demonstrated by an example   |
| references     | This object cites a reference               |

---

# Object Types

## Decision Guide

A reusable decision-support object.

Example:

```yaml
type: decision_guide
```

> **Canonical type.** The Decision Guide `type` value is `decision_guide`
> (ID prefix `DG-`). The type names the **artifact** — a reusable, verdict-free
> decision-support object — not the decision it supports. The value
> `engineering_decision` is **rejected** for DG-* objects and is reserved for a
> possible future artifact representing an actual project decision (a decision
> record), which EKB does not currently store. See
> `migrations/MIGRATION-0002-decision-guide-type-final.md`.

Answers:

> Given this context, what engineering choice should be made and why?

---

## Engineering Concept

A reusable explanation of an engineering idea.

Example:

```yaml
type: engineering_concept
```

Answers:

> What does this engineering idea mean and why does it matter?

---

## Engineering Pattern

A reusable solution to a recurring engineering problem.

Example:

```yaml
type: engineering_pattern
```

Answers:

> What recurring problem does this solve, and what are the trade-offs?

---

## Quality Attribute

An engineering quality objective.

Example:

```yaml
type: quality_attribute
```

Answers:

> What quality are we trying to protect or improve?

---

## Example

A concrete illustration of engineering knowledge.

Example:

```yaml
type: example
```

Answers:

> How does this knowledge appear in practice?

---

## Reference

A source that supports engineering knowledge.

Example:

```yaml
type: reference
```

Answers:

> Where does this knowledge come from?

---

# Status Values

Allowed status values:

```text
draft
review
approved
deprecated
superseded
archived
```

---

# Versioning

Knowledge Objects use semantic versioning.

## Major

Breaking conceptual change.

## Minor

Meaningful content expansion.

## Patch

Corrections or editorial improvements.

---

# File Naming

File names should be readable but are not the object identity.

Recommended:

```text
should_introduce_another_subsystem.md
coupling.md
modular_architecture.md
```

The stable ID in metadata is authoritative.

---

# Validation Rules

A valid Knowledge Object must:

* contain YAML front matter
* include a stable ID
* include a title
* include a type
* include a status
* include a version
* use approved relationship types
* avoid broken object references
* contain meaningful human-readable content

---

# Guiding Principle

A Knowledge Object is not just a document.

It is a node in the Engineering Knowledge Graph.
