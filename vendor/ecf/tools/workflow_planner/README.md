# ECF Execution Planner

Read-only computation of **which task(s) are runnable right now** for a validated
ECF workflow.

> The planner is part of the ECF **control plane**. It computes execution.
> It does not perform execution, and it does not perform engineering reasoning.

## Validator vs. Planner vs. Runner

Three distinct control-plane roles — this tool is the **Planner**:

| Component | Question it answers | Writes files? | Runs tasks? |
|-----------|--------------------|---------------|-------------|
| **Validator** (`tools/workflow_validator`) | Is this workflow structurally safe and internally consistent? | No | No |
| **Planner** (this tool) | Given the current runtime state, which task(s) could execute next, and what is blocked and why? | **No** | No |
| **Runner** (`tools/task_runner`) | Actually execute one runnable task and record its result. | Yes | **Yes** |

The run a plan is computed against is created by the **Run Initialization Engine**
(`tools/run_initializer`), which materializes a schema-valid, planner-ready run
from a workflow + a Work Request + a Run ID (no task execution, no AI).

The planner **computes** execution. The runner **performs** execution. The
planner never crosses that line: it reads the workflow and the runtime, and
reports a plan.

## What it does

Given a validated workflow, repository state, and an optional runtime directory,
the planner:

1. loads the workflow (reusing the validator's parser — no duplication),
2. **validates the workflow first** (an invalid workflow yields no plan),
3. loads execution state when a `--run` directory is provided,
4. inspects runtime outputs (`state.yaml`, `manifest.yaml`, `completion.yaml`, `task_outputs/`, `reports/`),
5. determines completed, runnable, and blocked tasks,
6. explains every blocking reason,
7. computes the remaining topological execution order,
8. prints an execution plan.

It **never**: executes tasks, modifies files, invokes AI, updates runtime, or
infers engineering recommendations.

## Separated state dimensions

A task is described by three **independent** dimensions — lifecycle, output
validity, and the advisory next action are never conflated:

```text
execution_state:  not_started  running  completed  failed  cancelled  superseded
output_validity:  not_applicable  unknown  valid  stale  missing  malformed
planned_action:   none  run  rerun  wait  blocked  stop
```

`STALE` and `RERUN REQUIRED` are **derived display labels**, not lifecycle states.
For example, a task that ran but whose input changed is
`execution_state=completed, output_validity=stale, planned_action=rerun`. The JSON
output carries all three dimensions plus a `display_state` convenience label.

## Provenance mode (explicit)

Every runtime run declares an explicit provenance **mode** in `state.yaml`/`manifest.yaml`:

```yaml
provenance:
  mode: required        # required | legacy
  schema_version: "0.1.0"
```

- `required` — every completed output is re-verified against its provenance record.
- `legacy` — output existence is trusted, output validity is `unknown`, and the planner emits a **WARNING**.
- **Missing or unrecognized configuration is an invalid runtime configuration** (exit 2). Policy is never inferred from directory existence.

## Provenance and stale-output detection

In `required` mode the planner re-verifies every completed output against
`runtime/runs/<RUN_ID>/provenance/<TASK_ID>.yaml` (see
`runtime_schemas/TASK_PROVENANCE_SCHEMA.md`): it re-hashes each declared input and
the output with SHA-256 (`tools/artifact_fingerprint`) and compares
task/workflow/ECF/EKB versions and commits.

- **ECF version** identity comes only from the canonical `ecf-version.yaml` (never README). EKB identity from `vendor/engineering_kb/VERSION`.
- Whether a task requires **EKB** identity is authoritative from the workflow's `environment_dependencies` block — a record cannot omit EKB fields to bypass the check.
- If required current ECF/EKB identity cannot be resolved, that is a **planner configuration error** (exit 2), not staleness. Git commit resolution is best-effort with version-only fallback.

Conservative v0.1 — treated as stale: missing/malformed provenance, changed
input/output hash, changed task/workflow version, changed ECF version/commit,
changed EKB version/commit (when the contract requires EKB), and a stale direct
dependency. Staleness propagates: **a downstream task never gets `planned_action:
run` while a required upstream needs rerun.** Modification times are never the
validity signal. Semantic compatibility ranges are not implemented.

The planner **never** creates, repairs, updates, or deletes provenance. The future runner writes provenance after successful task execution.

Runtime state, the manifest, and per-task results are written atomically by the
runtime transaction layer (`tools/runtime_state`), not by the planner. The planner
only reads `state.yaml`/`manifest.yaml`; see
`runtime_schemas/RUNTIME_TRANSACTION_CONTRACT.md`. The single-task runner (`tools/task_runner`) consumes the planner's
runnable frontier to execute one approved task.

## Usage

```powershell
# Fresh plan (no runtime yet): only the entry task is ready
python tools/workflow_planner/plan_workflow.py workflows/reasoning/WF-REASON-0001-engineering-recommendation.md

# Plan against an existing run directory
python tools/workflow_planner/plan_workflow.py `
  workflows/reasoning/WF-REASON-0001-engineering-recommendation.md `
  --run runtime/runs/RUN-REASON-20260710-0001

# JSON output
python tools/workflow_planner/plan_workflow.py `
  workflows/reasoning/WF-REASON-0001-engineering-recommendation.md --format json

# PowerShell wrapper (defaults to WF-REASON-0001)
.\scripts\plan-workflow.ps1 -Run runtime\runs\RUN-REASON-20260710-0001
```

## Output

Human-readable summary lists Completed / Ready / Blocked counts, then a `READY`
section (with the reason each task can run), a `BLOCKED` section (with what each
task is waiting for), and the remaining topological order.

JSON (`--format json`) returns `{workflow, status, run_dir, counts, tasks[],
remaining_order[], validation_errors[], notes[]}`, where each task is
`{id, state, reason?, waiting_for?}`.

## Exit codes

```text
0  a plan was produced (runnable, blocked, complete, or failed run)
1  the workflow failed validation (cannot plan safely)
2  planner execution/configuration failure (bad file, invalid runtime)
```

## Files

```text
tools/workflow_planner/
├── README.md            this file
├── plan_workflow.py     CLI entry point (argument parsing + rendering)
├── planner.py           planning engine + read-only runtime reader
├── models.py            TaskState / TaskPlan / ExecutionPlan
└── tests/
    ├── test_planner.py  scenario tests (empty, partial, completed, failed, ...)
    └── fixtures/        runtime fixtures per scenario
```

## Running the tests

```powershell
python -m unittest discover -s tools/workflow_planner/tests
```

## Design notes

- **Parser reuse:** `planner.py` imports `validate_workflow` and calls its
  `load_workflow`, `RepoIndex`, `validate`, and `parse_*` helpers. The planner
  adds only runtime interpretation and frontier computation.
- **Completion signal:** a task counts as completed when its bound output file
  exists, or the manifest records a successful terminal status. This makes the
  planner robust whether or not a manifest is present.
- **Read-only guarantee:** the runtime reader opens files for reading only; a
  test asserts the inspected run directory is byte-for-byte unchanged after
  planning.
- **Not the runner:** turning "ready" into "running/completed" requires a
  component that writes runtime outputs. That component is intentionally out of
  scope here.
