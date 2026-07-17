# KNOWLEDGE_RELATIONSHIP_MODEL.md

# Purpose

This document defines the canonical relationship policy for the Engineering
Knowledge Base (EKB). It is the authoritative source for which relationships
exist, their direction, their inverses, their allowed source/target types, and
how the validator treats each.

It complements `knowledge_model/KNOWLEDGE_GRAPH_MODEL.md` (conceptual) by making
the rules **executable** — `engine/ekb.py` enforces exactly this policy.

---

# Principles

- Relationships are **directional** unless explicitly symmetric.
- **Not every relationship requires a reciprocal edge.** Requiring reciprocity
  everywhere produces false defects. Reciprocity is required only where the
  meaning is inherently mutual (`related_to`) or where a back-reference is
  needed for retrieval integrity (`illustrated_by`).
- The authoritative direction of an inverse pair is the one that carries the
  meaning; the reverse is optional unless stated otherwise.

---

# Relationship Policy

| Relationship | Symmetric | Inverse | Inverse requirement | Source types | Target types |
|---|:--:|---|---|---|---|
| `requires` | no | `required_by` | optional | decision, pattern | concept, pattern |
| `required_by` | no | `requires` | optional | concept, pattern | decision, pattern |
| `supports` | no | `supported_by` | optional | concept, pattern | decision |
| `supported_by` | no | `supports` | optional | decision | concept, pattern |
| `illustrated_by` | no | `illustrates` | **required** | any | example |
| `illustrates` | no | `illustrated_by` | none | example | any |
| `related_to` | **yes** | `related_to` | **required** | any | any |
| `references` | no | — | none | any | any |
| `optimizes` | no | `optimized_by` | optional | pattern | quality attribute |
| `optimized_by` | no | `optimizes` | optional | quality attribute | pattern |
| `affects` | no | `affected_by` | optional | decision, concept, pattern | quality attribute |
| `affected_by` | no | `affects` | optional | quality attribute | decision, concept, pattern |

Type names use the canonical Knowledge Object `type` values
(`decision_guide`, `engineering_concept`, `engineering_pattern`,
`quality_attribute`, `example`, `reference`).

## Notes on specific relationships

- **`related_to`** is symmetric: if A relates to B, B must relate to A. Missing
  the reciprocal is `REL003`.
- **`illustrated_by` → `illustrates`** is required *from the illustrated side*: a
  Decision Guide that claims `illustrated_by EX-…` requires that example to
  declare `illustrates` back. The reverse is **not** required — an example may
  `illustrates` many objects without each object listing the example (the
  example is the authoritative source of the illustration).
- **Decision → Quality Attribute is `affects`**, not `supports`. `supports`
  targets a decision (concept/pattern → decision). This was corrected during the
  hardening cleanup (see MIGRATION-0001 context and the `affects`/`affected_by`
  normalization of `DG-ARCH-0001` and `QA-0001`).

---

# Validation Codes

The validator emits stable codes so failures are greppable and testable:

| Code | Meaning | Severity |
|---|---|---|
| `REL001` | unresolved relationship target | error |
| `REL002` | invalid relationship type (not in policy) | error |
| `REL003` | missing required inverse | error |
| `REL004` | invalid inverse relationship (wrong reverse name where inverse is required) | error |
| `REL005` | invalid source/target type pairing | error |
| `REL006` | duplicate relationship edge | error |
| `REL007` | contradictory relationship declaration (a relation and its inverse to the same target) | error |

Optional inverses are never reported (neither error nor warning); a future
configuration flag may surface them as advisory warnings if desired.

---

# Traversal and Sufficiency Behavior

- **Traversal:** retrieval follows all declared, resolved edges outward from a
  primary object but never hops into a *different* Decision Guide, keeping each
  decision's closure self-contained.
- **Sufficiency:** only `requires` edges are sufficiency-critical. A `requires`
  target must resolve, have a matching ID, valid metadata, valid (non-empty)
  content, valid required sections (for decision-type targets), and its own
  relationships must resolve (second-level closure). Optional relationships
  (`references`, `affects`, `supports`, …) do not affect sufficiency.

---

# Guiding Principle

Relationships are enforced by policy, not by habit. The policy distinguishes
where reciprocity is meaningful from where it is noise, so the validator reports
real defects and stays silent on legitimate directional edges.
