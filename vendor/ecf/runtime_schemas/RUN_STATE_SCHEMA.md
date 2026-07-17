# RUN_STATE_SCHEMA.md

# Purpose

Defines `runtime/runs/<RUN_ID>/state.yaml`: the authoritative, revisioned record
of a run's lifecycle and per-task lifecycle. The **initial** record (revision 0,
every task `not_started`) is created by the Run Initialization Engine
(`tools/run_initializer`); thereafter it is written only by the runtime
transaction layer (`tools/runtime_state`). It is read (read-only) by the planner.

The record is constrained block YAML so the read-only planner can parse
`provenance.mode` and the run status without a YAML library.

---

# Required Fields

```yaml
schema_version: "0.1.0"
run_id: RUN-REASON-20260710-0001
work_request_id: WR-0001
workflow_id: WF-REASON-0001
workflow_version: 0.1.0
provenance:
  mode: required          # required | legacy  (explicit; never inferred)
  schema_version: "0.1.0"
run_status: running
active_task: null         # task currently mid-transaction, or null
task_states:
  TASK-CLASSIFY-0001: completed
  TASK-CLASSIFY-0002: running
revision: 7               # monotonically increasing integer
created_at: 2026-07-11T00:00:00Z
updated_at: 2026-07-11T00:05:00Z
failure: null             # or a flat map: {code, description, task_id}
recovery_status: none     # none | required | applied
```

| Field | Meaning |
|-------|---------|
| `schema_version` | schema version of this record |
| `run_id` | stable run identity |
| `work_request_id` | originating Work Request |
| `workflow_id` / `workflow_version` | the executing workflow |
| `provenance.mode` | explicit provenance policy (`required`/`legacy`) — see `TASK_PROVENANCE_SCHEMA.md` |
| `run_status` | overall run state (below) |
| `active_task` | the single task currently held in a transaction, or `null` |
| `task_states` | map of Task ID → task lifecycle state |
| `revision` | integer; increments on every committed change, in lockstep with the manifest |
| `created_at` / `updated_at` | ISO-8601 UTC timestamps (informational) |
| `failure` | blocking/failure info, or `null` |
| `recovery_status` | whether recovery is required/applied |

---

# Allowed Run States

```text
requested   accepted   running   blocked   failed
cancelled   superseded   waiting_for_human_approval   completed
```

# Task Lifecycle States (aligned with the planner)

```text
not_started   running   completed   failed   cancelled   superseded
```

`stale` and `rerun_required` are **not** lifecycle states — they are the
planner's derived output-validity / planned-action labels and never appear here.

---

# Revision Rules

* `revision` is a non-negative integer.
* Every successful task-result commit increments `state.revision` and
  `manifest.revision` to the **same** new value.
* A mismatch between `state.revision` and `manifest.revision` is a recovery
  condition (see `RUNTIME_TRANSACTION_CONTRACT.md`).
* Writers use compare-before-write: a transaction records the expected current
  revision and the commit fails (`RevisionConflict`) if the actual revision
  changed — no lost updates.

---

# Consistency Guarantees

* A task is `completed` in `task_states` only after its output and provenance are
  promoted and the output hash is verified.
* `active_task` names the only task that may be mid-transaction.
* The file is written atomically (temp-file + `os.replace`); a reader never sees
  a partially written record.
