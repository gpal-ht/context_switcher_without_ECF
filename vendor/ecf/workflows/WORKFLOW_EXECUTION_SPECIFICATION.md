# WORKFLOW_EXECUTION_SPECIFICATION.md

# Purpose

This specification defines the execution contract for every Engineering Workflow executed through the Engineering Control Framework (ECF).

A Workflow composes existing Engineering Tasks into one deterministic execution sequence.

Workflows are defined conceptually by the Engineering Reasoning Engine and the Engineering Orchestration Engine.

This document defines how a Workflow is:

* identified
* versioned
* entered
* sequenced
* bound to runtime artifacts
* validated
* traced
* suspended and resumed
* completed
* failed

Every executable Workflow in ECF must conform to this specification.

---

# Core Principle

A Workflow defines task order, dependencies, state transitions, and runtime artifacts.

A Workflow does not perform engineering reasoning, and it does not redefine the behavior of the tasks it composes.

Reasoning belongs to tasks. Coordination belongs to the Orchestration Engine. A Workflow is the reusable plan that connects them.

---

# Relationship to the Execution Hierarchy

```text
Work Request
    ↓
Engineering Orchestration Engine
    ↓
Engineering Workflow          ← defined by this specification
    ↓
Engineering Tasks
    ↓
Runtime Outputs
    ↓
Human Approval
```

Responsibilities:

* The Orchestration Engine selects and controls a released Workflow and manages its state.
* The Workflow defines task order, dependencies, state transitions, and runtime artifact bindings.
* Tasks define atomic operations and own their output structure and semantics.
* Tasks must not determine their own next task.
* The Workflow must not redefine task behavior.
* The Workflow must not perform engineering reasoning itself.
* Human approval remains outside automated reasoning execution.

---

# Required Workflow Structure

Every Workflow Execution Specification must contain the following sections.

---

# 1. Workflow Identity

Required fields:

* Workflow ID
* Name
* Version
* Status
* Category
* Owner

Workflow ID format:

```text
WF-<CATEGORY>-<NUMBER>
```

Example:

```text
WF-REASON-0001
```

The category segment identifies the workflow family (for example `REASON` for reasoning workflows). The number is zero-padded and unique within the category.

---

# 2. Purpose

Describe:

* what engineering outcome the Workflow produces
* which Work Request intents it serves
* where it starts and where it stops

A Workflow must describe exactly one coherent execution outcome.

---

# 3. Version

Workflow specifications use semantic versioning.

## Major

Breaking change to entry conditions, exit conditions, the task graph, or artifact bindings.

## Minor

Backward-compatible addition such as a new optional validation gate or a new non-blocking finding path.

## Patch

Clarification that does not change execution behavior.

A Workflow pins the version of every task it composes. A change to a pinned task version is at least a minor Workflow change.

---

# 4. Status

Allowed workflow specification status values:

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

Only a `released` Workflow may be selected by the Orchestration Engine for a production run. `draft` and `review` workflows may be executed only in explicitly non-authoritative validation runs.

---

# 5. Owner

The repository or team responsible for the Workflow specification.

For canonical ECF workflows this is `engineering_control_framework`.

---

# 6. Entry Conditions

Define the conditions that must hold before the Workflow may start.

At minimum:

* an accepted Work Request exists
* the Work Request declares exactly one primary engineering question
* required Work Request fields are present per `work_requests/WORK_REQUEST_SPECIFICATION.md`
* a Run ID has been assigned by the Orchestration Engine
* the bundled EKB and ECF dependencies are available
* every pinned task version resolves to an existing task specification

The Workflow declares its `entry_state`. Execution may begin only from that state.

---

# 7. Exit Conditions

Define the terminal states of the Workflow.

Every Workflow declares one `successful_exit_state`.

For reasoning workflows the successful exit state is:

```text
waiting_for_human_approval
```

A successful exit state is never `approved`. Approval is a separate human act performed outside automated reasoning execution.

Non-successful terminal states include `blocked`, `failed`, `cancelled`, and `superseded`.

---

# 8. Required Inputs

List every input the Workflow requires to begin, each with:

* name
* type
* source
* whether required
* the task step that first consumes it

Workflows must not obtain undeclared inputs.

---

# 9. Task Graph

The Workflow defines an ordered task graph.

The graph must be a directed acyclic graph (DAG) unless an explicitly controlled retry edge is declared and bounded by a maximum attempt count.

Each node declares:

* sequence number
* Task ID
* pinned task version
* upstream dependencies (by Task ID)
* required inputs (by bound filename)
* primary output (by bound filename)
* state before execution
* state after successful execution
* failure state
* whether non-blocking findings permit continuation
* validation required before continuing

The graph must contain no cycles other than declared retry edges. Every non-entry node must have at least one upstream dependency. Every node except the terminal node must have at least one downstream consumer, except where an output is explicitly terminal.

---

# 10. Task-Version Pinning

The Workflow pins every task to an exact version.

```text
TASK-<CATEGORY>-<NUMBER> @ <version>
```

If a pinned version does not match the current task specification, version resolution fails and the Workflow must not execute. The mismatch must be reported rather than silently changed.

Task-version pinning makes a Workflow run reproducible.

---

# 11. Input/Output Bindings

The Workflow binds each task to exactly one stable primary output filename and path.

* The task specification owns the output type, structure, and semantics.
* The Workflow binding owns the concrete filename and path for a run.
* The Workflow binding is authoritative for the run when it differs from a task's recommended filename.

Every downstream required input must resolve to exactly one upstream bound output. No two tasks may bind to the same output path.

---

# 12. Runtime-Path Conventions

## Canonical Run Root

Every run uses one canonical run root:

```text
runtime/runs/<RUN_ID>/
```

The standard layout for a run is:

```text
runtime/runs/<RUN_ID>/
├── state.yaml          # runtime infrastructure: revisioned run + per-task lifecycle state
├── manifest.yaml       # runtime infrastructure: machine-readable execution manifest
├── trace.md            # reasoning trace (TASK-TRACE-0001)
├── completion.yaml     # run completion result (TASK-TRACE-0003)
├── lock/               # single-run writer lock
├── staging/            # per-transaction staging (never final)
├── inputs/             # accepted Work Request and referenced context snapshots
├── task_outputs/       # one stable output file per task
├── provenance/         # per-task provenance records (<TASK_ID>.yaml)
└── reports/            # generated report(s) incl. final-manifest.yaml (TASK-TRACE-0002)
```

`state.yaml` and the run-root `manifest.yaml` are **runtime infrastructure**:
runtime-owned, continuously mutated by the transaction layer, and never task-owned
outputs. `TASK-TRACE-0002` produces a distinct **immutable** snapshot,
`reports/final-manifest.yaml`, which receives task provenance and is never mutated
by the runtime. A task output must never be bound to `state.yaml` or the run-root
`manifest.yaml` (enforced by validator rule WF021).

A run is created by the **Run Initialization Engine** (`tools/run_initializer`):
given a validated workflow, a Work Request, and a Run ID it materializes the run
directory, the read-only `inputs/work-request.md`, and schema-valid `state.yaml`
/ `manifest.yaml` at revision 0 (every task `not_started`, no outputs, no
provenance). Initialization is crash-safe — the run is built in a temporary
sibling directory, validated by reloading, checked by the planner, and only then
atomically renamed into place. It never executes a task or invokes AI.

Runtime state, the manifest, and per-task results are written atomically and
transactionally (`tools/runtime_state`) so that output, provenance, manifest,
state, and trace metadata cannot silently disagree after interruption. `state.yaml`
and `manifest.yaml` carry matching integer revisions; a single-run writer lock
serializes writers; and read-only recovery inspection plans repairs for
interrupted runs. See `runtime_schemas/RUN_STATE_SCHEMA.md`,
`runtime_schemas/RUN_MANIFEST_SCHEMA.md`, and
`runtime_schemas/RUNTIME_TRANSACTION_CONTRACT.md`.

When a run records per-task provenance (`provenance/<TASK_ID>.yaml`, per
`runtime_schemas/TASK_PROVENANCE_SCHEMA.md`), the read-only planner re-verifies
each completed output against its record — SHA-256 fingerprints of inputs and
output, plus task/workflow/ECF/EKB versions and commits — and classifies invalid
outputs as `stale`/`rerun_required`. Provenance is written by the runner after a
task succeeds; the planner and validator never write it.

Every run declares an explicit provenance **mode** (`required` | `legacy`) in
`state.yaml`/`manifest.yaml`; the planner never infers policy from directory
existence, and missing configuration is an invalid runtime configuration. A
workflow declares authoritative per-task **environment dependencies** so the
planner knows which tasks require ECF and EKB identity without consulting the
provenance record being validated:

```yaml
environment_dependencies:
  default:
    ecf: required
    ekb: not_required
  TASK-RETRIEVE-0002:
    ecf: required
    ekb: required
```

Placement rules:

* Task outputs live under `runtime/runs/<RUN_ID>/task_outputs/`.
* Reports and the immutable final manifest snapshot (`final-manifest.yaml`) live under `runtime/runs/<RUN_ID>/reports/`.
* `trace.md` and `completion.yaml` (task-owned) and `state.yaml`, `manifest.yaml` (runtime infrastructure) live at the run root.

## Run Identity

Run IDs follow the Execution Trace Contract:

```text
RUN-REASON-<YYYYMMDD>-<SEQUENCE>
```

The Work Request ID (for example `WR-0001`) is metadata and a provenance identifier. It must appear inside artifacts but must never be used as a filesystem run root.

## Compatibility Guidance

Earlier drafts referenced `runtime/work_requests/<WORK_REQUEST_ID>/` and `runtime/reasoning_runs/<RUN_ID>/` as competing roots. Those roots are **legacy and non-authoritative**; the only canonical root is `runtime/runs/<RUN_ID>/`.

Existing runtime files created under the older roots must not be migrated by a workflow or task. New runs use the canonical root only. A reader encountering a legacy path should treat it as a historical run location.

---

# 13. State Transitions

The Workflow declares its execution states and the valid transitions between them.

State must be persisted in `state.yaml` at the run root after every transition.

Every state has:

* the task or tasks executed while in it
* the successful next state
* the failure next state

Terminal states have no successful next state.

---

# 14. Validation Gates

The Workflow declares validation gates between steps.

A validation gate verifies that a task's primary output exists and passes the task's declared validation before the next task may run.

At minimum a reasoning workflow declares:

* a per-task output-presence and output-validity gate
* a report-validation gate before finalization
* a completeness gate before the successful exit state

A failed gate stops forward progress and moves the run to `blocked` or `failed`.

---

# 15. Findings Behavior

Findings are produced by tasks, not by the Workflow.

The Workflow declares, per step, whether non-blocking findings permit continuation.

* A `blocker` finding always stops the Workflow.
* A non-blocking finding permits continuation only when the task contract explicitly allows completion with findings.
* Open non-blocking findings are carried forward into the manifest and completion result and remain visible at the approval gate.

The Workflow must not suppress, resolve, or downgrade findings.

---

# 16. Failure Propagation

The Workflow stops forward execution when:

* a task fails
* a required primary output is missing
* a task output fails validation
* a blocking finding exists
* the recommendation report fails validation
* trace or manifest generation fails
* task-version resolution fails

On any of these, the run transitions to `blocked` or `failed`, the state is persisted, and a failure record is written. Downstream reasoning tasks must not run.

The Workflow may continue past a step with non-blocking findings only when the step's task contract explicitly permits it.

---

# 17. Cancellation

A run may be cancelled by the Orchestration Engine before it reaches a terminal state.

Cancellation:

* sets the state to `cancelled`
* preserves all completed outputs and the trace
* records the reason
* does not delete runtime evidence

---

# 18. Suspension

A run may be suspended, for example to await external information.

Suspension preserves `state.yaml`, all completed task outputs, and the partial trace. A suspended run is resumable.

---

# 19. Resumption

Resumption is deterministic and driven by observable state, not by task self-selection.

The Orchestration Engine determines the next runnable task using:

* `state.yaml`
* `manifest.yaml`
* per-task status
* existence of each task's bound primary output
* validation status of each existing output

A completed task must not be rerun unless:

* its inputs changed
* its output is invalid
* its pinned version changed
* the run was explicitly restarted

Resumption selects the first incomplete or invalid task in graph order and continues from there.

---

# 20. Supersession

A Workflow specification or a run may be superseded.

* A superseded Workflow specification is retained but not selected for new runs.
* A superseded run records the superseding Run ID and is retained for audit.

Supersession never rewrites history.

---

# 21. Human Approval Boundaries

Human approval is outside automated reasoning execution.

A Workflow must not:

* grant approval
* invoke the Engineering Production Engine
* start a production or transformation run
* modify canonical project artifacts
* create ADRs
* update architecture documents
* write source code

A successful reasoning workflow stops at `waiting_for_human_approval`. What happens after approval is coordinated by the Orchestration Engine as a separate step, not by the reasoning Workflow.

---

# 22. Trace and Manifest Requirements

Every run must produce, at the run root:

* a reasoning trace conforming to `execution/EXECUTION_TRACE_CONTRACT.md`
* a machine-readable manifest conforming to the same contract
* a completion result
* a persisted `state.yaml`

The trace, manifest, state, and completion outputs must exist before the run may reach its successful exit state.

The trace and manifest record observable evidence only and must not request or expose private model chain-of-thought.

---

# 23. Permission Boundaries

Allowed:

* read the accepted Work Request and referenced project context
* read bundled ECF and bundled EKB (read-only)
* invoke pinned task specifications in graph order
* write runtime outputs under `runtime/runs/<RUN_ID>/`
* persist workflow state

Prohibited:

* modify `vendor/engineering_kb/`
* modify canonical project artifacts
* modify task specifications during a run
* invoke the Engineering Production Engine
* grant human approval
* access sibling repositories or external sources without authorization

---

# 24. Security and Privacy

A Workflow run must:

* record identifiers and paths rather than sensitive content where a citation is sufficient
* exclude secrets, keys, passwords, and tokens from runtime outputs
* minimize personal information
* preserve repository boundaries
* respect vendor read-only rules

---

# 25. Accessibility

Workflow specifications and human-readable runtime outputs must:

* use explicit headings and labels
* express state and findings as text, not color alone
* remain understandable when read linearly
* provide text equivalents for any diagram
* expand uncommon abbreviations

---

# 26. Metrics

Recommended workflow metrics:

* workflow completion rate
* successful-exit rate
* blocked-run rate
* average resumptions per run
* task-version-resolution failure rate
* report-validation pass rate
* human correction rate

Metrics exist to improve workflow quality. They must not measure individual human productivity.

---

# 27. Workflow Acceptance-Test Requirements

Every Workflow must have an acceptance-test file under `acceptance_tests/`.

Acceptance tests validate contract and flow structure, including at minimum:

* task reachability (every referenced Task ID resolves to one specification)
* version compatibility (every pinned version matches the task file)
* input/output continuity (every downstream input has an upstream producer)
* stable filenames (one bound output per task, no duplicate paths)
* runtime-root consistency (only `runtime/runs/<RUN_ID>/`)
* failure propagation
* human-approval boundary
* trace completeness
* resumption

Acceptance tests validate structure and contracts, not the correctness of any specific engineering conclusion.

---

# Definition of a Valid Workflow Execution

A Workflow Execution is valid only when:

* the Workflow specification is identified and released for authoritative runs
* entry conditions are satisfied
* every pinned task version resolves
* tasks execute in declared graph order
* each task's bound output exists and passes validation before the next task runs
* no task selects its own successor
* failure propagation is honored
* the trace, manifest, state, and completion outputs exist at the run root
* the run reaches a declared terminal state
* a successful reasoning run stops at `waiting_for_human_approval` without invoking production

---

# Guiding Principle

A Workflow is the reusable, versioned plan that turns atomic tasks into one auditable engineering execution.

It orders the work and binds the evidence. It never does the reasoning, and it never crosses the human-approval boundary.
