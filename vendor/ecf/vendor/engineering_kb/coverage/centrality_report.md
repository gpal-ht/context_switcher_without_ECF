<!--
Generated file. Do not edit manually.
Generator: engine/ekb.py
Generator version: 0.2.0
Command: python engine/ekb.py centrality
-->

# Centrality Report

Centrality here is measured **across the whole current knowledge graph**. 
In-degree = how many objects point at this one; out-degree = how many it points at. High in-degree means high reuse, not operational fragility.

> Scope caveat: the graph currently contains **1 Decision Guide(s)**. With so few decisions, whole-graph centrality and a single guide's local closure largely coincide; do not read ecosystem-wide significance into these numbers yet.

| ID | Type | In | Out | Sufficiency-critical |
|---|---|---:|---:|:--:|
| `DG-ARCH-0001` | Decision Guides | 7 | 7 |  |
| `CON-ARCH-0001` | Concepts | 6 | 4 | yes |
| `CON-ARCH-0002` | Concepts | 6 | 4 | yes |
| `QA-0001` | Quality Attributes | 4 | 3 |  |
| `QA-0002` | Quality Attributes | 4 | 3 |  |
| `CON-ARCH-0003` | Concepts | 3 | 3 | yes |
| `PAT-ARCH-0001` | Patterns | 2 | 5 |  |
| `EX-ARCH-0001` | Examples | 1 | 4 |  |

## High-Centrality Objects (Whole Graph)

Most-referenced supporting objects — high **reuse** across the graph:
- `CON-ARCH-0001` — Coupling (in-degree 6)
- `CON-ARCH-0002` — Cohesion (in-degree 6)

## Load-Bearing Within a Decision Closure

In-degree measured **inside each Decision Guide's retrieval closure** (local, not ecosystem-wide):
- **DG-ARCH-0001**: `CON-ARCH-0001` (6), `CON-ARCH-0002` (6), `QA-0001` (4)

## Sufficiency-Critical Objects

Objects a Decision Guide **requires** — removing any makes *that guide's* package fail its sufficiency gate (empirically confirmed by EXP-0003, Cohesion ablation). This is a per-guide dependency, not an EKB-wide single point of failure:
- `CON-ARCH-0001` — Coupling (whole-graph in-degree 6, required by a decision guide)
- `CON-ARCH-0002` — Cohesion (whole-graph in-degree 6, required by a decision guide)
- `CON-ARCH-0003` — Bounded Context (whole-graph in-degree 3, required by a decision guide)
