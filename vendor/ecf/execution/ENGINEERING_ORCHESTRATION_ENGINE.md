# ENGINEERING_ORCHESTRATION_ENGINE.md

# Purpose

The Engineering Orchestration Engine coordinates engineering execution within the Engineering Control Framework (ECF).

It is responsible for:

* managing Work Requests
* selecting execution paths
* invoking engineering roles
* coordinating execution engines
* enforcing approval boundaries
* maintaining execution state
* supporting resumable engineering execution

The Orchestration Engine coordinates engineering work.

It does not perform engineering reasoning or engineering production.

---

# Philosophy

Engineering execution is a controlled process.

The Orchestration Engine exists to coordinate engineering activities while preserving:

* traceability
* reproducibility
* human authority
* engineering quality

The engine ensures that engineering progresses through approved execution stages.

---

# Core Principle

The Orchestration Engine coordinates.

It never replaces engineering judgment.

---

# Workflow Layer

The Orchestration Engine executes engineering work by selecting and controlling an Engineering Workflow.

* Orchestration selects a `released` Workflow from `workflows/WORKFLOW_CATALOG.md` for an accepted Work Request.
* Workflow definitions own task ordering, dependencies, and runtime-artifact bindings, per `workflows/WORKFLOW_EXECUTION_SPECIFICATION.md`.
* Orchestration manages Workflow execution state, suspension, resumption, and approval gating.
* Orchestration does not hard-code individual task behavior and does not embed a task sequence of its own.
* Tasks are atomic and do not choose their successors; the Workflow determines what runs next.
* A successful reasoning Workflow stops at a human-approval state (`waiting_for_human_approval`).

The Orchestration Engine coordinates Workflows. Workflows order tasks. Tasks perform atomic operations.

---

# Responsibilities

The Orchestration Engine shall:

* receive Work Requests
* determine execution state
* invoke Roles
* coordinate the Engineering Reasoning Engine
* enforce approval gates
* coordinate the Engineering Production Engine
* manage execution traces
* support suspension and resumption

The Orchestration Engine shall not:

* make engineering recommendations
* produce engineering artifacts
* bypass human approval
* modify Engineering Knowledge

---

# Inputs

The Orchestration Engine consumes:

## Work Request

Defines the engineering work to perform.

---

## Engineering Context

Supplied by the consuming project.

---

## Engineering Control Framework

Provides:

* workflow definitions
* role definitions
* review packs
* execution rules
* quality gates

---

# Execution State Model

Every Work Request moves through defined execution states.

```text id="u2xk0f"
Requested
        │
        ▼
Classified
        │
        ▼
Reasoning
        │
        ▼
Recommendation Produced
        │
        ▼
Waiting for Human Approval
        │
        ├──────────────┐
        │              │
    Rejected       Approved
        │              │
        ▼              ▼
     Closed       Production
                       │
                       ▼
                 Validation
                       │
                       ▼
                 Completed
```

Execution state must always be persisted.

---

# Execution Pipeline

```text id="8lpk3e"
Work Request
        │
        ▼
Determine Workflow
        │
        ▼
Determine Required Roles
        │
        ▼
Invoke Reasoning Engine
        │
        ▼
Receive Engineering Recommendation Report
        │
        ▼
Pause for Human Approval
        │
        ▼
Invoke Production Engine
        │
        ▼
Validate Outputs
        │
        ▼
Complete Work Request
```

The Orchestration Engine controls the pipeline.

---

# Role Coordination

The Orchestration Engine invokes engineering Roles.

Examples:

* Product Architect
* System Architect
* Security Architect
* Test Architect
* Repository Guardian

The engine coordinates responsibilities.

Executors fulfill those responsibilities.

Possible executors include:

* human engineers
* Claude
* ChatGPT
* Gemini
* automated systems
* hybrid teams

---

# Human Approval Boundary

Human approval is mandatory between:

Engineering Recommendation

and

Engineering Production.

The Orchestration Engine must never bypass this boundary.

---

# Suspension

Execution may pause for:

* human approval
* missing information
* external dependency
* scheduled continuation
* engineering review

Paused execution should preserve complete execution state.

---

# Resumption

Execution should resume without repeating completed work.

The engine should restore:

* execution state
* execution trace
* completed outputs
* pending actions

Resumption should be deterministic.

---

# Cancellation

Execution may be cancelled.

Reasons include:

* work no longer relevant
* engineering question resolved elsewhere
* project cancelled
* user decision
* duplicate work request

Cancellation should preserve execution history.

---

# Failure Recovery

Failures include:

* invalid engineering context
* missing knowledge
* failed reasoning
* failed production
* failed validation

Failures should:

* preserve traces
* identify blocking issues
* recommend recovery actions

---

# Engine Coordination

The Orchestration Engine coordinates:

## Engineering Reasoning Engine

Produces:

Engineering Recommendation Report

---

## Engineering Production Engine

Produces:

Engineering Artifacts

---

## Execution Trace

Both engines generate execution traces.

The Orchestration Engine links them into a complete execution history.

---

# Runtime State

The canonical runtime root for a run is:

```text
runtime/runs/<RUN_ID>/
```

Within a run, task outputs live under `task_outputs/`, reports under `reports/`, and `state.yaml`, `trace.md`, `manifest.yaml`, and `completion.yaml` at the run root, as defined in `execution/EXECUTION_TRACE_CONTRACT.md` and `workflows/WORKFLOW_EXECUTION_SPECIFICATION.md`.

The Work Request ID is metadata and a provenance identifier, not a filesystem run root.

Earlier `runtime/work_requests/` and `runtime/reasoning_runs/` roots are **legacy and non-authoritative**; the only canonical root is `runtime/runs/<RUN_ID>/`. Existing runtime files under the legacy roots are retained as historical run locations and are not migrated.

Runtime state is not canonical engineering knowledge.

---

# Outputs

The Orchestration Engine produces:

* execution state
* execution history
* execution coordination
* linked execution traces
* workflow status

It does not produce engineering artifacts.

---

# Provider Independence

The Orchestration Engine coordinates Roles rather than AI systems.

Execution remains independent of:

* Claude
* ChatGPT
* Gemini
* future reasoning systems

The orchestration model remains unchanged regardless of executor.

---

# Success Criteria

A successful orchestration run:

* follows the approved workflow
* invokes the correct Roles
* preserves execution state
* enforces approval boundaries
* supports resumption
* links all execution traces
* completes with full traceability

---

# Guiding Principle

The Engineering Orchestration Engine ensures that engineering execution is coordinated, observable, resumable, and governed.

It coordinates engineering.

It never replaces engineering judgment.
