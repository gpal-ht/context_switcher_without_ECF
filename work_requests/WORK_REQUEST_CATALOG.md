# Work Request Catalog

Project-owned index of every Context Switcher Work Request submitted to the
Engineering Control Framework (ECF).

- **Scope:** Context Switcher project artifacts only.
- **Authority:** Projects own Work Requests; ECF executes them
  (`vendor/ecf/work_requests/WORK_REQUEST_SPECIFICATION.md`).
- **Status vocabulary (WR lifecycle):** `draft → submitted → accepted → running → waiting_for_approval → completed`; alternatives: `cancelled`, `rejected`, `superseded`, `abandoned`.
- **Engineering phase vocabulary:** `discover, understand, define, design, validate, plan, implement, verify, learn` (`vendor/ecf/vendor/engineering_kb/foundations/ENGINEERING_PROCESS_MAP.md`).

---

## Active Work Requests

| WR ID | Title | Status | Owner | Engineering Phase | Expected Workflow | Primary Deliverable |
|-------|-------|--------|-------|-------------------|-------------------|---------------------|
| [WR-0002](WR-0002-reconcile-canonical-subsystem-model.md) | Reconcile the Canonical Subsystem Model | **completed** — ADR-0005 accepted; canonical docs aligned; acceptance tests pass | project_owner | define → design | manual (reasoning + ADR) | ADR-0005 + single canonical subsystem enumeration + aligned docs + severity-aware tests |
| [WR-0001](WR-0001-repository-integration-subsystem.md) | Evaluate Repository Integration Subsystem Boundary | **ready** — unblocked by ADR-0005; classification & retrieval executed; awaiting reasoning/recommendation | project_owner | design | WF-REASON-0001 *(not yet defined in bundled ECF)* | Engineering Recommendation Report (preceded by Engineering Knowledge Package) |

---

## Work Request Detail

### WR-0001 — Evaluate Repository Integration Subsystem Boundary

- **Engineering question:** Should Repository Integration become a first-class subsystem within Context Switcher?
- **Desired outcome:** Engineering Knowledge Package suitable for a later Engineering Recommendation Report.
- **Requested by:** project_owner · **Created:** 2026-07-10 · **Priority:** medium
- **Classification (from run `RUN-REASON-20260710-0001`):** intent `design_solution` → phase `design`.
- **Execution progress:**
  - `TASK-CLASSIFY-0001` (intent) — completed
  - `TASK-CLASSIFY-0002` (phase) — completed
  - `TASK-RETRIEVE-0001` (context) — completed
  - `TASK-RETRIEVE-0002` (Engineering Knowledge Package `EKP-ARCH-0001`) — completed
  - Reasoning → Recommendation → Human Approval — **not started** (no reasoning/recommendation task exists in the bundle; see adoption report).
- **Runtime outputs:** `runtime/work_requests/WR-0001/` (intent/phase/context results, EKP, trace, manifest).
- **WR spec validation:** contains all six required elements (engineering question, desired outcome, engineering context reference, constraints, requested deliverables, success criteria) — **valid**.
- **Out of scope (per WR):** final architectural recommendation, ADR creation, architecture modification, source-code implementation, repository scanner design.

---

## Candidate Work Requests (not yet created)

These are recommended future Work Requests surfaced during the ECF adoption audit.
They are **candidates only** — none has been submitted.

| Candidate | Engineering question | Likely phase | Rationale |
|-----------|----------------------|--------------|-----------|
| ~~WR-CAND-A~~ | Reconcile the canonical subsystem enumeration. | — | **Realized as WR-0002.** |
| WR-CAND-B | Define the Context Switcher data model. | design | `docs/architecture/DATA_MODEL.md` and `INFORMATION_ARCHITECTURE.md` are empty stubs (F-2). |
| WR-CAND-C | Define non-functional/quality goals, security, and privacy model. | define | Engineering context lacks quantified quality goals, security, performance, deployment, testing, operations coverage (F-3). |
| WR-CAND-D | Resolve the repository-integration open questions (Local Git vs GitHub API; evaluation evidence). | understand / define | Directly unblocks WR-0001's reasoning stage. |

---

## Maintenance

Update this catalog whenever a Work Request is created, changes status, changes
owner, is superseded, or completes. This file is the single project-owned index of
Work Requests and their expected ECF workflows.
