# RUN_MANIFEST_SCHEMA.md

# Purpose

Defines `runtime/runs/<RUN_ID>/manifest.yaml`: the machine-readable index of a
run — its identity, framework versions, executor, and per-task output bindings,
statuses, provenance paths, hashes, and validation status. The **initial**
manifest (revision 0, no output hashes, `executor: {type: none, has_run: false}`)
is created by the Run Initialization Engine (`tools/run_initializer`); thereafter
it is written only by the runtime transaction layer. It is read (read-only) by
the planner.

The manifest revision advances in lockstep with the run-state revision (see
`RUN_STATE_SCHEMA.md`).

**Ownership.** This run-root `manifest.yaml` is **runtime infrastructure**:
runtime-owned and continuously mutated by the transaction layer. It is distinct
from a finalization task's **immutable** manifest snapshot (for reasoning runs,
`reports/final-manifest.yaml`, produced by `TASK-TRACE-0002`), which is
task-owned, provenance-tracked, and never mutated by the runtime. A task output
must never be bound to the run-root `manifest.yaml` (validator rule WF021).

---

# Required Fields

```yaml
schema_version: "0.1.0"
run_id: RUN-REASON-20260710-0001
workflow_id: WF-REASON-0001
workflow_version: 0.1.0
revision: 7
executor:
  type: tool
  tool: runtime_state
ecf_version: v0.1
ekb_version: v0.1-local
tasks:
  - id: TASK-CLASSIFY-0001
    version: 0.1.0
    status: completed
    output: task_outputs/engineering-intent.yaml
    output_status: verified          # none | staged | promoted | verified
    provenance_path: provenance/TASK-CLASSIFY-0001.yaml
    output_hash: 9f2c...e1
    validation_status: valid         # unknown | valid | invalid
findings:
  - id: FIND-TRADE-0001
    classification: minor
    status: open
    task_id: TASK-ANALYZE-0005
trace_path: trace.md
completion_path: completion.yaml
```

| Field | Meaning |
|-------|---------|
| `schema_version` | schema version of this record |
| `run_id` | stable run identity |
| `workflow_id` / `workflow_version` | executing workflow |
| `revision` | integer; equals the run-state revision after every commit |
| `executor` | flat map of executor metadata (no secrets) |
| `ecf_version` / `ekb_version` | framework identities pinned for the run |
| `tasks[]` | per-task record: id, version, status, output binding, output status, provenance path, output hash, validation status |
| `findings[]` | flat list of findings (each may carry a `task_id`); kept at the manifest top level so task entries stay flat |
| `trace_path` | path to the run trace |
| `completion_path` | path to the completion record |

Task `status` values are drawn from the task lifecycle states; `output_status`
tracks the promotion lifecycle (`none → staged → promoted → verified`).

---

# Consistency Rules

* Each `tasks[].output` matches the workflow's stable output binding for that
  task (see `workflows/WORKFLOW_EXECUTION_SPECIFICATION.md`).
* `output_hash` is the lowercase SHA-256 of the promoted output, and equals the
  hash recorded in the task's provenance record.
* A task reaches `status: completed` / `output_status: verified` only after the
  atomic commit verified the promoted output hash.
* The manifest is written atomically; a reader never sees a partial manifest.
* `revision` mismatch with `state.yaml` is a recovery condition.
