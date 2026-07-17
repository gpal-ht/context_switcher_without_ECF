# EKB Engine

Makes the Engineering Knowledge Base *executable*.

The KB describes a knowledge graph (`knowledge_model/KNOWLEDGE_OBJECT_STANDARD.md`)
and a retrieval model (`knowledge_model/ENGINEERING_KNOWLEDGE_RETRIEVAL_MODEL.md`),
and defines acceptance tests for retrieval (`acceptance_tests/`). This engine
parses the Markdown Knowledge Objects, validates the graph, performs the
retrieval traversal, and runs those acceptance tests for real.

Single file, **no third-party dependencies**, Python 3.9+.

## Usage

```bash
python engine/ekb.py validate                # metadata + relationship policy
python engine/ekb.py integrity               # types, REL001-REL007, orphans, cycles
python engine/ekb.py retrieve DG-ARCH-0001   # knowledge closure + sufficiency gate
python engine/ekb.py completeness            # check every Decision Guide is complete
python engine/ekb.py coverage                # write coverage/knowledge_coverage.md
python engine/ekb.py centrality              # write coverage/centrality_report.md
python engine/ekb.py packages                # flag stale generated packages
python engine/ekb.py test                    # run retrieval acceptance tests (RAT-*)
python engine/ekb.py list                    # list all Knowledge Objects
```

## Contracts this engine enforces

- **Type contract** — the canonical Decision Guide type is `decision_guide` (it
  names the artifact, not the decision it supports); `engineering_decision` is
  rejected for DG-* objects and reserved for a future decision-record artifact
  (see `migrations/MIGRATION-0002-decision-guide-type-final.md`).
- **Relationship policy** — every edge is validated against
  `foundations/KNOWLEDGE_RELATIONSHIP_MODEL.md` with stable codes `REL001`–`REL007`
  (unresolved target, invalid type, missing required inverse, invalid inverse,
  invalid source/target pairing, duplicate edge, contradictory edge).
- **Sufficiency** — a `requires` target is valid only when it resolves, its ID
  matches, its metadata and content validate, and its own relationships resolve
  (second-level closure). "File exists" is not sufficient.
- **Generated-artifact policy** — coverage/centrality reports are committed,
  deterministic, header-stamped generated files (see `coverage/GENERATED.md`);
  Engineering Knowledge Packages are transient and gitignored.

## What each command does

- **validate** — parses every `.md` that declares an `id`, checks required
  fields, status values, ID/type prefix agreement, known relationship types,
  and (most importantly) that no relationship points at a missing object.
- **integrity** — full knowledge-graph integrity pass: canonical types, the
  relationship policy (`REL001`–`REL007`), no orphan objects, and no circular
  `requires` dependencies.
- **retrieve `<ID>`** — traverses declared relationships outward from a primary
  object and prints the smallest complete supporting set, in retrieval order
  (Decision Guide → Concepts → Pattern → Quality Attributes → Examples →
  References), plus the retrieval path. Retrieval is *scoped*: it never hops
  into a different Decision Guide. It ends with a **SUFFICIENCY** gate — if the
  primary object `requires` anything that does not exist, it prints
  `SUFFICIENCY: FAIL` and exits non-zero (package generation must not proceed).
- **completeness** — verifies every Decision Guide contains all six required
  elements: alternatives, heuristics, forces, examples, related concepts, and
  quality attributes.
- **coverage** — writes `coverage/knowledge_coverage.md`: object counts by type,
  the full inventory, catalog status (authored vs planned), and knowledge gaps.
- **centrality** — writes `coverage/centrality_report.md`: in/out-degree per
  object, load-bearing hubs, and single points of failure (objects a Decision
  Guide `requires`).
- **test** — runs the `RAT-*` acceptance tests as pass/fail checks. Currently
  `RAT-ARCH-0001` asserts that "Should I introduce another subsystem?" retrieves
  exactly the 8 expected objects and nothing else.

## Tests

```bash
python engine/test_engine.py     # standalone, no dependencies
python -m pytest engine          # if pytest is installed
```

## Notes

- The retrieval closure computed by `retrieve DG-ARCH-0001` reproduces the
  hand-written package at `generated/packages/EKP-ARCH-0001-...` — same objects,
  same path, now derived from the graph instead of authored by hand.
- To add a new acceptance test, append to `ACCEPTANCE_TESTS` in `ekb.py`.
