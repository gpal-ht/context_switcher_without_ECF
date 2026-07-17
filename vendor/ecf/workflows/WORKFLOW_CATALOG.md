# WORKFLOW_CATALOG.md

# Purpose

This catalog lists the Engineering Workflows defined in the Engineering Control Framework (ECF).

A Workflow composes existing tasks into one deterministic execution sequence. Every Workflow conforms to `workflows/WORKFLOW_EXECUTION_SPECIFICATION.md`.

This catalog is the index the Orchestration Engine consults to select a Workflow for an accepted Work Request.

---

# Workflow Status Definitions

```text
planned
draft
review
approved
released
deprecated
superseded
archived
```

* **planned** — identified but not yet specified.
* **draft** — specification exists and is being written or revised.
* **review** — specification is under review.
* **approved** — specification passed review but is not yet released for authoritative runs.
* **released** — specification is authoritative; the Orchestration Engine may select it for production runs.
* **deprecated** — still runnable but discouraged; a replacement is expected.
* **superseded** — replaced by a newer Workflow; retained for audit, not selected for new runs.
* **archived** — retained for history only; not runnable.

Only a `released` Workflow may be selected for an authoritative run. `draft` and `review` workflows may be executed only in explicitly non-authoritative validation runs.

---

# Completion Criteria for a Workflow Specification

A Workflow specification is complete when:

* it conforms to `workflows/WORKFLOW_EXECUTION_SPECIFICATION.md`
* it declares identity, version, status, owner, entry state, and successful exit state
* every referenced Task ID resolves to exactly one task specification
* every task is pinned to a version that matches its task file
* every task has exactly one workflow-bound primary output with a unique path
* every downstream required input maps to an upstream produced output
* the task graph is acyclic (aside from any declared, bounded retry edge)
* runtime paths use only the canonical run root `runtime/runs/<RUN_ID>/`
* failure propagation, human-approval boundary, and trace/manifest requirements are defined
* an acceptance-test file exists under `acceptance_tests/`

A Workflow moves from `draft` toward `released` only after its acceptance tests are defined and pass structural validation.

---

# Catalog Fields

Each catalog entry records:

* workflow ID
* workflow name
* category
* version
* status
* entry state
* exit state
* task count
* required approval
* description

---

# Released and Draft Workflows

## WF-REASON-0001 — Engineering Recommendation

| Field | Value |
|---|---|
| Workflow ID | WF-REASON-0001 |
| Name | Engineering Recommendation |
| Category | reasoning |
| Version | 0.2.0 |
| Status | draft |
| Entry state | accepted |
| Exit state | waiting_for_human_approval |
| Task count | 18 |
| Required approval | Human approval (post-workflow, outside automated reasoning execution) |
| Specification | [workflows/reasoning/WF-REASON-0001-engineering-recommendation.md](reasoning/WF-REASON-0001-engineering-recommendation.md) |
| Acceptance tests | [acceptance_tests/WF-REASON-0001-ACCEPTANCE_TESTS.md](../acceptance_tests/WF-REASON-0001-ACCEPTANCE_TESTS.md) |

**Description:** Transforms an accepted engineering Work Request into a validated Engineering Recommendation Report and a complete, auditable reasoning-run record. Composes eighteen existing tasks across classification, retrieval, analysis, decision support, production, validation, and traceability. Stops at `waiting_for_human_approval`; never invokes the Engineering Production Engine.

**Status clarification** — two separate concerns:

```text
Workflow specification status: Complete
Automated execution status:    Not implemented
```

WF-REASON-0001 is structurally complete as a declarative workflow specification: all eighteen tasks resolve, versions are pinned, outputs are bound to unique paths, the dependency graph is an explicit acyclic DAG, and the human-approval boundary is defined.

It is **not** automatically executable because no workflow runner currently invokes the task graph. Specification completeness and runtime-implementation completeness are tracked independently; the absence of a runner does not downgrade the specification status.

---

# Planned Workflows

The following workflows are anticipated but **not yet specified**. They are listed for roadmap visibility only and must not be referenced by the Orchestration Engine until they reach `released`.

| Workflow ID | Name | Category | Status | Notes |
|---|---|---|---|---|
| WF-TRANSFORM-0001 | Approved Recommendation to Canonical Artifact | transformation | planned | Post-approval production flow; begins only after human approval; out of scope for the reasoning layer. |

No workflow beyond `WF-REASON-0001` is specified in this batch.

---

# Guiding Principle

The catalog is the authoritative index of reusable engineering execution plans.

A Workflow appears here only when it is real; it becomes selectable for authoritative runs only when it is `released`.
