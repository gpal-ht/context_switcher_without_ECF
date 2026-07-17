# Coverage Directory — Generated Artifact Policy

The files in this directory are **version-controlled generated reports**, not
hand-authored knowledge.

| File | Generator command |
|---|---|
| `knowledge_coverage.md` | `python engine/ekb.py coverage` |
| `centrality_report.md` | `python engine/ekb.py centrality` |

## Ownership rules

- These reports are **committed** so changes are reviewable in `git diff`, but
  they are **generated** — never edit them by hand. Each carries a provenance
  header (`Generator`, `Generator version`, `Command`).
- Generation is **deterministic**: identical inputs produce byte-identical
  output (no timestamps or volatile content). `engine/test_engine.py` asserts
  this (`test_coverage_report_deterministic`, `test_centrality_report_deterministic`).
- To refresh after any knowledge change: re-run both commands and commit the
  result alongside the knowledge change.

## Distinction from Engineering Knowledge Packages

Engineering Knowledge Packages (`generated/packages/`) are **transient,
non-canonical** query outputs and are gitignored per
`artifacts/ENGINEERING_KNOWLEDGE_PACKAGE_CONTRACT.md`. Coverage/centrality
reports are different: they are whole-graph health snapshots intended to be
committed. `GENERATED.md` itself is the only hand-authored file here.
