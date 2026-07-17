# Atomic Runtime State

Runtime transaction primitives that ensure a task's **output, provenance,
manifest, run state, and trace metadata cannot silently disagree** after
interruption or failure.

> This capability is the prerequisite for a task execution **runner**. It does
> not execute engineering tasks and never invokes AI — callers supply staged
> content. The planner remains strictly read-only.

Contracts: `runtime_schemas/RUN_STATE_SCHEMA.md`,
`runtime_schemas/RUN_MANIFEST_SCHEMA.md`,
`runtime_schemas/RUNTIME_TRANSACTION_CONTRACT.md`.

> The **initial** `state.yaml` / `manifest.yaml` (revision 0) are created by the
> Run Initialization Engine (`tools/run_initializer`) using these same models and
> serializers; this transaction layer is the sole writer thereafter.

## Modules

```text
tools/runtime_state/
├── models.py       typed dataclasses: RunState, RunManifest, RunLock, TransactionJournal
├── storage.py      constrained block-YAML round-trip, atomic writes, path safety, hashing
├── transaction.py  single-run writer lock + atomic one-task-result transaction
├── recovery.py     read-only recovery inspection + explicit repair (+ CLI)
└── tests/          storage / transaction / recovery tests
```

## What one atomic task result is

The atomic promotion of: the task **output**, its **provenance** record, the
**manifest** entry, the **run-state** entry, and the **trace-event** metadata.
Nothing is final until commit completes.

## Transaction lifecycle

```text
prepared → staged → validated → committing → committed
                                   ↘ aborted / recovery_required
```

Guarantees:

- Nothing is written directly to a final path; everything is staged under
  `staging/<TXN_ID>/` and promoted with `os.replace` (atomic, same filesystem).
- A **journal** records intent + the expected revision before promotion.
- **Compare-before-write**: commit fails with `RevisionConflict` if the run
  revision drifted — no lost updates.
- **State and manifest revisions increment together** to the same value.
- A task becomes `completed` **only after** output and provenance are promoted
  and the promoted output hash is verified.
- Commit is **idempotent** (re-committing a committed transaction is a no-op).

## API

```python
from tools.runtime_state import (
    load_run_state, load_manifest,
    acquire_run_lock, release_run_lock,
    begin_task_transaction, inspect_recovery, apply_recovery,
)

lock = acquire_run_lock(run_dir, owner="runner-1")
txn = begin_task_transaction(run_dir, task_id, output_rel, provenance_rel, owner="runner-1")
txn.stage_output(output_bytes, output_rel, output_sha256)
txn.stage_provenance(provenance_text, provenance_rel)
ok, reasons = txn.validate()
state = txn.commit()          # raises RevisionConflict on drift
```

## Locking

A single-run writer lock (`lock/lock.json`, atomic exclusive create) prevents two
writers from committing the same run concurrently. It fails safely when held,
carries owner + timestamp (never secrets), is **never broken automatically**, and
a stale lock (age > TTL) is only removable via an explicit recovery action.

## Recovery (read-only inspection, explicit repair)

```powershell
# read-only consistency summary (exit 0 consistent, 1 inconsistent, 2 unrecoverable)
python tools/runtime_state/recovery.py runtime/runs/<RUN_ID>
.\scripts\inspect-runtime-state.ps1 -RunDir runtime\runs\<RUN_ID>

# explicit repair (not read-only)
.\scripts\inspect-runtime-state.ps1 -RunDir <dir> -Apply -AllowLockRemoval
```

`inspect_recovery` never modifies the run. Only discard-staging (where no final
file was written) is eligible for automatic repair; everything else requires
explicit approval. See the transaction contract for the detected conditions.

## Security

All staged/final paths must resolve under the run directory; absolute paths,
`..` traversal, and symlink escapes are rejected. Promotion refuses unsafe
symlinks. No secrets appear in lock or journal metadata.

## Serialization

`state.yaml` / `manifest.yaml` use a **constrained block-YAML** round-tripper
(so the planner can read `provenance.mode` and the manifest task list without a
YAML library). Lock and journal use JSON (a strict YAML subset). Parsing
failures are explicit and conservative. No PyYAML dependency.

## Consumers

The single-task runner (`tools/task_runner`) is the first writer that drives this
layer: it stages and commits one planner-approved task's output + provenance,
advancing state and manifest to the same new revision.

## Tests

```powershell
python -m unittest discover -s tools/runtime_state/tests
```
