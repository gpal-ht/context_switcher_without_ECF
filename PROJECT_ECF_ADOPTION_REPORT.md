# Context Switcher — ECF Adoption Report

**Objective:** Prepare Context Switcher to become the first real consumer of the
Engineering Control Framework (ECF). This report captures the project-side
readiness audit, updated **2026-07-11** after the ECF bundle refresh. **No workflows were executed (live Claude not invoked); `vendor/ecf/` was refreshed only via the bundling script.**

- **Date:** 2026-07-10
- **Scope owned by this batch:** Context Switcher project artifacts, Engineering Context, Work Requests, project acceptance tests, project documentation.
- **Out of scope (owned elsewhere, not touched):** `vendor/ecf/`, `vendor/ecf/vendor/engineering_kb/`, bundled framework content.
- **Bundle pins (refreshed 2026-07-11):** ECF `v0.1-local` commit `8abed71` (source `github.com/gpal-ht/ecf.git`); EKB `v0.1-local` commit `6084948` (source `github.com/gpal-ht/engineering_kb.git`). Prior pin was ECF `db42b1e` / EKB `5334e69`.

---

## 1. Readiness Summary

| Readiness dimension | Status | Basis |
|---|---|---|
| Work Request(s) valid | ✅ Ready | WR-0001 passes all six WR-spec validation elements; catalog created. |
| Work Request catalog | ✅ Ready | `work_requests/WORK_REQUEST_CATALOG.md` created. |
| Engineering Context present | ✅ Ready | `docs/engineering/ENGINEERING_CONTEXT.md` exists with all required sections. |
| Engineering Context coverage | ⚠️ Partial | 7 coverage gaps (F-3). |
| Architecture consistency | ✅ Consistent | Canonical model fixed by ADR-0005 (F-1 **resolved**, WR-0002); 2 empty docs remain as non-blocking coverage warnings (F-2). |
| Vendor boundary | ✅ Ready | Vendor clean; key files present; `runtime/` + `generated/` ignored. |
| Project acceptance tests | ✅ Ready | `acceptance_tests/` created and runnable. |
| Automated workflow execution | ⚠️ Capability present, not yet executed | Refreshed bundle now contains `WF-REASON-0001` + decision/production tasks + runner/planner/validator (F-4, F-5 **resolved**). Not yet executed in Context Switcher; needs the live runner + human-approval routing. |

**Acceptance-test run (updated after ADR-0005 / WR-0002 and the 2026-07-11 bundle refresh):** all **PASS** (6 checks) — architecture-consistency WR-0002 gate blocking-clean; bundle-integrity + ignore-boundary checks pass; `DATA_MODEL.md` / `INFORMATION_ARCHITECTURE.md` remain visible as non-blocking coverage warnings.

---

## 1a. ECF Bundle Refresh (2026-07-11)

The bundle was refreshed from canonical ECF `8abed71` (EKB `6084948`) via `scripts/bundle-ecf.ps1` — semantically idempotent (identical 302-file tree across two runs; only `bundle_date` differs), hygienic (no `__pycache__`/`*.pyc`), and machine-path-free in `VERSION`. Capability status, distinguishing the four categories requested:

| Capability | Category | Evidence |
|---|---|---|
| `WF-REASON-0001` workflow | **Present in bundle** | Validator: VALID — 18 tasks, 68 edges, human-approval boundary preserved. |
| `TASK-DECIDE-0002` (generate recommendation) | **Present in bundle** | `tasks/decision_support/…` present. |
| `TASK-PRODUCE-0001` (recommendation report) | **Present in bundle** | `tasks/production/…` present. |
| validator / planner / runtime_state / task_runner / claude executor | **Present in bundle** | CLIs load; planner frontier + runner `--help` verified. |
| runtime schemas | **Present in bundle** | `runtime_schemas/RUN_STATE_SCHEMA.md` etc. |
| Reasoning run for WR-0001 | **Not yet executed in Context Switcher** | Live Claude intentionally not invoked this batch; readiness proven, execution deferred. |
| WR-0001 inputs | **No project input gap** | WR-0001 valid + unblocked (ADR-0005); `inputs/work-request.md` supplied in an ignored run dir. |
| End-to-end automation | **Residual framework/runtime step** | Requires operating the runner with an executor + routing the recommendation through human approval. |

---

## 2. Project Engineering Context Audit (Implement §1)

**Architecture documents inventory & currency:**

| Document | Lines | State |
|---|---|---|
| SYSTEM_ARCHITECTURE.md | 286 | current |
| SYSTEM_VISION.md | 184 | current (but enumerates only 5 engines — see F-1) |
| AI_ARCHITECTURE.md | 153 | current |
| DOMAIN_MODEL.md | 305 | current |
| KNOWLEDGE_ARCHITECTURE.md | 276 | current |
| RUNTIME_MODEL.md | 178 | current |
| WORK_SESSION_MODEL.md | 194 | current |
| USER_JOURNEY.md | 195 | current |
| **DATA_MODEL.md** | **0** | **empty stub (F-2)** |
| **INFORMATION_ARCHITECTURE.md** | **0** | **empty stub (F-2)** |

**Stale / conflicting architecture:** No *superseded* documents were found to remove. However, a **material conflict** exists in the subsystem enumeration (F-1) that must be reconciled rather than deleted. No documents were removed by this batch (removal of canonical architecture is a decision for the project owner, and the divergence is a reconciliation, not a deletion).

**Unresolved architecture questions (from canonical docs):**
- Repository integration scope; Local Git vs GitHub API; repository-evaluation evidence requirements; AI recommendation boundaries (`ENGINEERING_CONTEXT.md`, `AI_ARCHITECTURE.md`).
- Domain concepts still marked open: Task, Goal, Habit, Calendar Event, External Document, AI Memory, Knowledge Graph, Automation (`DOMAIN_MODEL.md`).
- Whether "Runtime" and "Integration" are first-class subsystems (F-1).

---

## 3. Engineering Context Coverage (Implement §3)

**Present project information:** project identity & mission, current phase, subsystem list, technology constraints, ADR index, known open questions, domain model, knowledge architecture, runtime model, work-session model, user journey, MVP scope.

**Missing / thin engineering information:**

| Area | Status | Note |
|---|---|---|
| Stakeholders | ❌ Missing | No stakeholder analysis (single-user assumed but not documented as such in context). |
| Quality goals / NFRs | ❌ Missing | No quantified quality attributes / acceptance thresholds. |
| Security & privacy model | ❌ Missing | Privacy is a stated principle but there is no security/threat model or data-classification. |
| Performance targets | ❌ Missing | No performance budgets. |
| Deployment model | ❌ Missing | Packaging/update/distribution undefined. |
| Testing strategy | ❌ Missing | No test approach doc (project acceptance tests added by this batch are process-level, not product-level). |
| Operations / observability | ❌ Missing | No logging/telemetry/observability plan. |
| Data model | ❌ Missing | `DATA_MODEL.md` empty (F-2). |
| Information architecture | ❌ Missing | `INFORMATION_ARCHITECTURE.md` empty (F-2). |
| Domain model | ✅ Present | `DOMAIN_MODEL.md`. |
| Runtime model | ✅ Present | `RUNTIME_MODEL.md`. |

---

## 4. Project Workflow Readiness — WF-REASON-0001 (Implement §4)

**Finding (updated 2026-07-11):** After the bundle refresh, `WF-REASON-0001` **is present and validates** (`vendor/ecf/workflows/reasoning/WF-REASON-0001-engineering-recommendation.md`; validator result VALID). The former framework gaps F-4/F-5 are **resolved in the bundle**. What remains is *execution* in Context Switcher (operating the runner with an executor, then human approval) — not a missing capability.

**Required project-side inputs for a reasoning run (derived from the orchestration pipeline and the four executed tasks) and their status:**

| Required input | Status | Evidence |
|---|---|---|
| Work Request (WR-spec conformant) | ✅ Present | `work_requests/WR-0001-...md` (valid). |
| Engineering Context | ✅ Present | `docs/engineering/ENGINEERING_CONTEXT.md`. |
| Resolvable context references | ✅ Present | SYSTEM_ARCHITECTURE, AI_ARCHITECTURE, MVP_SCOPE, ADR-0002, ADR-0004 all exist. |
| Bundled EKB knowledge (Decision Guide + closure) | ✅ Present | `DG-ARCH-0001` + supporting objects (vendor-provided). |
| Workflow definition WF-REASON-0001 | ✅ Present | In refreshed bundle; validates VALID (F-4 resolved). |
| Reasoning/recommendation tasks (EKP → recommendation → report) | ✅ Present | `TASK-DECIDE-0002` + `TASK-PRODUCE-0001` (+ `TASK-ANALYZE-*`) in refreshed bundle (F-5 resolved). |

**Conclusion:** Both project-side inputs **and** the framework-side workflow/tasks are now present. The fresh planner frontier for WF-REASON-0001 is exactly `TASK-CLASSIFY-0001`; a valid run directory initializes (schema-valid `state.yaml` + `inputs/work-request.md`); validator, planner, and runner CLIs load; the Claude executor wrapper is present. The only remaining step is *executing* the run — deferred here (live Claude not invoked).

---

## 5. Repository Boundary Validation (Implement §5)

| Check | Result |
|---|---|
| Claude cannot modify `vendor/` (this batch) | ✅ Vendor working tree clean; no vendor writes performed. |
| `runtime/` is ignored | ✅ `.gitignore:42 runtime/` — `runtime/out.txt` → IGNORED. |
| `generated/` is ignored | ✅ `.gitignore:43 generated/` (added this batch) — `generated/out.txt` → IGNORED. |
| Bundled key files intact | ✅ 9/9 key ECF/EKB files present (`check_vendor_integrity.sh`). |

---

## 6. Engineering Risks & Open Findings

| ID | Severity | Finding | Impact | Remediation |
|---|---|---|---|---|
| ~~F-1~~ | Resolved | Subsystem enumeration was inconsistent (Integration present in some docs, absent in others; Runtime a subsystem only in ADR-0004). | Was blocking WR-0001. | **Resolved by ADR-0005 (WR-0002):** canonical 6-subsystem model; Integration first-class; Runtime a cross-cutting concern; historical ADRs clarified; docs aligned; severity-aware test passes. |
| **F-2** | Major | `DATA_MODEL.md` and `INFORMATION_ARCHITECTURE.md` are empty stubs. | Data/information architecture unavailable to reasoning and future design. | Author both, or mark explicitly `status: deferred` (WR-CAND-B). |
| **F-3** | Medium | Engineering context lacks stakeholders, quality goals/NFRs, security/privacy, performance, deployment, testing, operations. | Reasoning/validation for non-arch questions will be under-supported. | Extend Engineering Context (WR-CAND-C). |
| ~~F-4~~ | Resolved | `WF-REASON-0001` was undefined in the bundled ECF. | Was: no automated reasoning workflow. | **Resolved by bundle refresh (ECF `8abed71`):** WF-REASON-0001 present and validates. |
| ~~F-5~~ | Resolved | No reasoning/recommendation task consumed the EKP. | Was: WR-0001 could not progress from EKP to recommendation. | **Resolved by bundle refresh:** `TASK-DECIDE-0002` + `TASK-PRODUCE-0001` present. Capability present, not yet executed. |
| **F-6** | Minor | Runtime output layout divergence: WR-0001 outputs under `runtime/work_requests/WR-0001/` vs orchestration engine's recommended `runtime/reasoning_runs/RUN-.../`. | Trace discoverability inconsistency. | Adopt one runtime layout convention. |

---

## 7. Recommended Adoption Sequence

1. **Reconcile the subsystem enumeration (F-1).** Smallest, highest-leverage change; it directly conditions WR-0001's answer. → *WR-CAND-A*.
2. **Resolve the empty architecture stubs (F-2)** — author or explicitly defer `DATA_MODEL.md` and `INFORMATION_ARCHITECTURE.md`. → *WR-CAND-B*.
3. **Extend Engineering Context coverage (F-3)** — quality goals, security/privacy, testing, deployment, operations. → *WR-CAND-C*.
4. **(Done 2026-07-11)** Refreshed the ECF bundle so `WF-REASON-0001` + decision/production tasks + tooling are available (F-4/F-5 resolved).
5. **Execute WF-REASON-0001 for WR-0001** — start with `TASK-CLASSIFY-0001` via the single-task runner (fixture executor first; live Claude only with explicit approval), then route the recommendation through the human-approval gate.

Steps 1–3 are project-owned and can proceed now. Steps 4–5 depend on framework work owned by the parallel ECF batches.

---

## 8. What Was Prepared by This Batch

- `work_requests/WORK_REQUEST_CATALOG.md` — Work Request index.
- `acceptance_tests/` — four executable checks + aggregate runner + PowerShell mirror + README.
- `.gitignore` — added `generated/` (runtime/ already ignored).
- This report.

No canonical architecture/product/ADR files were edited; no vendor files were touched; no workflow was executed.
