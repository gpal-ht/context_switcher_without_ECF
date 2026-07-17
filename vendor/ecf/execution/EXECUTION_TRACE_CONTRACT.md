# Execution Trace Contract

## Purpose

This contract defines the trace requirements for every execution performed through the Engineering Control Framework.

It applies to:

* Engineering Reasoning Engine runs
* Knowledge Transformation Engine runs
* future automated ECF execution capabilities

Execution traces provide an auditable record of what happened during an engineering run.

They preserve:

* inputs
* evidence
* decisions
* outputs
* provenance
* validation
* unresolved issues

An execution trace must be understandable by both humans and automated tools.

---

# Core Principle

Every ECF execution must leave sufficient evidence to answer:

1. What was requested?
2. Which context was used?
3. Which engineering knowledge was used?
4. Which standards and rules were applied?
5. What conclusion or output was produced?
6. What uncertainty or failure remains?
7. What should happen next?

Execution without a trace is incomplete.

---

# Trace Boundaries

An execution trace records observable engineering reasoning and actions.

It must not attempt to capture or expose private model chain-of-thought.

The trace should contain:

* evidence used
* alternatives considered
* engineering criteria applied
* assumptions
* findings
* conclusions
* confidence
* resulting actions

The trace explains the decision without exposing hidden internal reasoning.

---

# Trace Types

ECF supports two primary trace types.

## Reasoning Trace

Produced by the Engineering Reasoning Engine.

Records how engineering knowledge and engineering context led to a recommendation.

## Transformation Trace

Produced by the Knowledge Transformation Engine.

Records how approved engineering inputs were converted into new or updated canonical artifacts.

---

# Run Identity

Every execution run must have a stable Run ID.

## Reasoning Run ID

Recommended format:

```text
RUN-REASON-<YYYYMMDD>-<SEQUENCE>
```

Example:

```text
RUN-REASON-20260710-0001
```

## Transformation Run ID

Recommended format:

```text
RUN-TRANSFORM-<YYYYMMDD>-<SEQUENCE>
```

Example:

```text
RUN-TRANSFORM-20260710-0001
```

Run IDs must be unique within the consuming repository.

---

# Required Run Metadata

Every trace must declare:

```yaml
---
run_id: RUN-REASON-20260710-0001
run_type: reasoning
status: completed
started_at: 2026-07-10T10:00:00+05:30
completed_at: 2026-07-10T10:05:00+05:30
executor:
  type: ai
  provider: anthropic
  tool: claude-code
ecf_version: v0.1-local
ekb_version: v0.1-local
consumer_repository: context_switcher
---
```

Required fields:

* Run ID
* Run type
* Status
* Start timestamp
* Completion timestamp
* Executor type
* Executor provider or identity
* Execution tool
* ECF version
* EKB version, when used
* Consumer repository

---

# Allowed Run Status Values

```text
requested
running
completed
completed_with_findings
failed
cancelled
abandoned
superseded
```

## Requested

The run has been defined but execution has not started.

## Running

Execution is currently active.

## Completed

The run completed successfully and produced the expected outputs.

## Completed With Findings

The run completed, but unresolved findings remain.

## Failed

The run could not produce a valid result.

## Cancelled

Execution was intentionally stopped before completion.

## Abandoned

The run was stopped because the underlying work was no longer relevant or viable.

## Superseded

A newer run replaces this run.

---

# Required Trace Structure

Every execution trace must contain the following sections.

## 1. Run Summary

Describe:

* what was requested
* why the run was started
* which execution engine was used
* final status

## 2. Inputs

List all inputs consumed.

Examples:

* engineering question
* work request
* engineering context
* engineering knowledge package
* approved recommendation
* transformation specification
* canonical artifacts

Each input should include:

* identifier
* path or source
* version or commit
* role in the run

## 3. Dependency Versions

Record the versions of:

* ECF
* EKB
* consuming project
* relevant standards
* relevant templates
* relevant transformation specifications

Where available, include Git commit hashes.

## 4. Evidence

List the evidence used during execution.

Examples:

* project documents
* ADRs
* Knowledge Object IDs
* test results
* measurements
* user-provided constraints

Evidence should be cited by stable ID or repository path.

## 5. Applied Rules

List the framework elements applied.

Examples:

* standards
* Decision Guides
* quality gates
* review requirements
* transformation rules
* confidence model

## 6. Execution Summary

Provide an observable explanation of what the engine did.

For a reasoning run, this includes:

* alternatives evaluated
* engineering forces considered
* trade-offs identified
* assumptions made
* recommendation reached

For a transformation run, this includes:

* input artifacts processed
* transformation steps performed
* templates applied
* outputs generated
* validation performed

## 7. Findings

Every finding must include:

* Finding ID
* Classification
* Description
* Evidence
* Required action
* Status

Allowed classifications:

```text
blocker
major
minor
observation
deferred
future_improvement
```

## 8. Outputs

List every output produced.

Examples:

* Engineering Recommendation Report
* canonical artifact
* review report
* generated diagram
* output manifest
* validation report

Each output must include:

* output ID
* output type
* location
* canonical or generated status
* approval status

## 9. Validation

Describe verification performed.

Examples:

* required sections validated
* object relationships checked
* standards compliance reviewed
* tests executed
* artifact rendering checked
* manual review performed

## 10. Unresolved Issues

List:

* missing evidence
* open questions
* blocked outputs
* failed validations
* deferred work

If none exist, state:

```text
None.
```

## 11. Next Action

State the recommended next step.

Examples:

* request human approval
* revise engineering context
* rerun knowledge retrieval
* execute a transformation
* perform specialist review
* promote output to canonical status
* close the work request

---

# Input Provenance

Every input must identify its origin.

Examples:

```yaml
inputs:
  - id: ENG-CONTEXT-0001
    type: engineering_context
    source: docs/engineering/ENGINEERING_CONTEXT.md
    repository: context_switcher
    commit: abc123

  - id: EKP-ARCH-0001
    type: engineering_knowledge_package
    source: generated
    generated_from:
      - DG-ARCH-0001
      - CON-ARCH-0001
      - CON-ARCH-0002
```

Generated inputs must identify the canonical sources from which they were produced.

---

# Output Manifest

Every run must produce an output manifest.

Recommended file:

```text
manifest.yaml
```

Minimum structure:

```yaml
run_id: RUN-TRANSFORM-20260710-0001

outputs:
  - id: ART-PRD-0001
    type: product_requirements_document
    path: outputs/PRD-0001.md
    status: draft
    canonical: false
    requires_review: true

findings:
  - id: FIND-RUN-0001
    classification: major
    status: open
```

The manifest is the machine-readable summary of the run.

Two manifests must not be conflated. The run-root `manifest.yaml` is **runtime
infrastructure**: runtime-owned, continuously mutated by the transaction layer,
and revision-coupled with `state.yaml`; it is never a task-owned output. A
finalization task (for reasoning runs, `TASK-TRACE-0002`) produces a distinct
**immutable** manifest snapshot under `reports/` (e.g.
`reports/final-manifest.yaml`), which receives task provenance and is never mutated
by the runtime. A task output must never be bound to `state.yaml` or the run-root
`manifest.yaml`.

---

# Reasoning Trace Requirements

A Reasoning Trace must additionally record:

* engineering question
* engineering intent
* engineering phase
* retrieved Knowledge Object IDs
* retrieval path
* alternatives
* engineering forces
* trade-offs
* assumptions
* recommendation
* confidence assessment
* missing information
* suggested next transformation

The confidence assessment must conform to:

```text
knowledge/CONFIDENCE_MODEL.md
```

---

# Transformation Trace Requirements

A Transformation Trace must additionally record:

* approved work request or recommendation
* transformation specification
* input artifacts
* standards applied
* templates applied
* files created
* files modified
* files superseded
* derived formats generated
* validation performed
* deviations from the approved plan
* output artifact status

---

# Runtime Storage

Execution traces are runtime outputs.

The canonical runtime root for every run is:

```text
runtime/runs/<RUN_ID>/
```

Standard layout:

```text
runtime/
└── runs/
    └── RUN-REASON-20260710-0001/
        ├── state.yaml        # runtime infrastructure: execution state
        ├── manifest.yaml     # runtime infrastructure: machine-readable execution manifest
        ├── trace.md          # execution trace (TASK-TRACE-0001)
        ├── completion.yaml   # run completion result (TASK-TRACE-0003)
        ├── inputs/           # accepted Work Request and context snapshots
        ├── task_outputs/     # one stable output file per task
        └── reports/          # generated report(s) incl. final-manifest.yaml (TASK-TRACE-0002)
```

The run directory, its `inputs/work-request.md` (materialized read-only), and the
initial `state.yaml` / `manifest.yaml` (revision 0) are created by the Run
Initialization Engine (`tools/run_initializer`) before any task runs.

Placement rules:

* Task outputs live under `task_outputs/`.
* Reports and the immutable final manifest snapshot (`final-manifest.yaml`) live under `reports/`.
* Per-task provenance records live under `provenance/<TASK_ID>.yaml`.
* Task-owned `trace.md` and `completion.yaml`, and the runtime-owned infrastructure `state.yaml` and `manifest.yaml`, live at the run root. A task output is never bound to `state.yaml` or the run-root `manifest.yaml`.
* The Work Request ID (for example `WR-0001`) is metadata and a provenance identifier recorded inside artifacts. It is never used as the run directory.

Task provenance records conform to `runtime_schemas/TASK_PROVENANCE_SCHEMA.md`. They
are written by the execution runner **after** a task completes successfully, and
must be written atomically (write to a temporary file, then rename into place) so
a reader never observes a partial record. A provenance record pins, by SHA-256,
the exact inputs and output a task was produced from, plus the task, workflow,
ECF, and (when applicable) EKB versions and commits. The read-only planner uses
these records to detect stale outputs; it never writes them.

Every run must declare an explicit **provenance mode** in `state.yaml` (or
`manifest.yaml`); it is never inferred from directory existence:

```yaml
provenance:
  mode: required        # required | legacy
  schema_version: "0.1.0"
```

Missing or unrecognized provenance configuration is an invalid runtime
configuration. ECF version identity is read from the canonical root
`ecf-version.yaml` (never README text); EKB identity from
`vendor/engineering_kb/VERSION`. Whether a task requires EKB identity is declared
authoritatively by the workflow/task contract, not by the provenance record.

Runtime state (`state.yaml`), the manifest (`manifest.yaml`), and per-task
results are written atomically and transactionally so that output, provenance,
manifest, state, and trace metadata cannot silently disagree after interruption.
See `runtime_schemas/RUN_STATE_SCHEMA.md`, `runtime_schemas/RUN_MANIFEST_SCHEMA.md`,
and `runtime_schemas/RUNTIME_TRANSACTION_CONTRACT.md`. State and manifest carry
matching integer revisions; a single-run writer lock serializes writers; and
read-only recovery inspection detects and plans repairs for interrupted runs. The
transaction layer (`tools/runtime_state`) is the sole writer; the planner and
validator never write runtime state.

The single-task runner (`tools/task_runner`) drives one planner-approved task per
invocation through that transaction layer — validating the workflow, inspecting
recovery, selecting exactly one runnable task, invoking a provider-independent
executor (a safe fixture executor in v0.1), generating authoritative provenance,
and committing atomically. It never runs a whole workflow, grants approval, or
invokes AI.

Transformation runs use the same root with their own Run ID, for example `runtime/runs/RUN-TRANSFORM-20260710-0001/`.

Earlier drafts used `runtime/work_requests/<WORK_REQUEST_ID>/` and `runtime/reasoning_runs/<RUN_ID>/` as competing roots. Those roots are **legacy and non-authoritative**; the only canonical root is `runtime/runs/<RUN_ID>/`. Existing files under the legacy roots are retained as historical run locations and are not migrated. This change adopts a single canonical root; it does not change trace semantics.

Runtime traces should not be treated as canonical framework knowledge.

---

# Promotion Rules

Generated outputs do not automatically become canonical artifacts.

Promotion requires:

1. Successful execution.
2. Required validation completed.
3. Required reviews completed.
4. Human approval.
5. Explicit movement into the canonical project location.
6. Traceability back to the originating Run ID.

Example:

```text
runtime/transformation_runs/RUN-TRANSFORM-20260710-0001/outputs/system-design.md
```

After approval:

```text
docs/architecture/SYSTEM_DESIGN.md
```

The canonical artifact should record:

```yaml
originating_run: RUN-TRANSFORM-20260710-0001
```

---

# Read-Only Dependency Rule

Bundled dependencies must remain read-only during execution.

A run may read:

* bundled ECF
* bundled EKB
* project engineering context

A run must not modify:

* `vendor/ecf/`
* `vendor/engineering_kb/`
* `vendor/ecf/vendor/engineering_kb/`

Required dependency changes must be made in the source repository and bundled again.

---

# Failure Handling

A failed run must still produce a trace when technically possible.

The trace should explain:

* where execution failed
* which inputs were available
* which outputs were incomplete
* whether partial results are usable
* how execution may be resumed or retried

Failure must not silently discard engineering evidence.

---

# Cancellation and Exit Strategy

Every run must support graceful termination.

Valid exit outcomes include:

* completed
* cancelled by user
* abandoned because the work is no longer relevant
* blocked by missing information
* superseded by another run
* failed due to invalid inputs

Partial outputs must be clearly marked as incomplete.

---

# Trace Retention

Runtime traces may be retained locally for:

* audit
* debugging
* experiment comparison
* framework improvement
* recovery

Projects may define their own retention policy.

Approved canonical artifacts must retain their originating Run ID even if the runtime trace is later archived.

---

# Security and Privacy

Execution traces may contain sensitive engineering context.

Traces must not record:

* secrets
* API keys
* passwords
* authentication tokens
* unnecessary personal data
* sensitive source content not required for auditability

Projects should define appropriate trace access and retention controls.

---

# Quality Requirements

A valid execution trace must be:

* complete
* understandable
* versioned
* attributable
* reproducible where practical
* grounded in evidence
* explicit about uncertainty
* linked to its outputs
* independent of private model reasoning

---

# Guiding Principle

Every ECF run must leave behind enough observable evidence for another engineer to understand what was requested, what information was used, what result was produced, and what should happen next.
