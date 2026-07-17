# RUNTIME_TRANSACTION_CONTRACT.md

# Purpose

Defines the atomic runtime transaction that records **one task result** so that
a task's output, provenance, manifest entry, run state, and trace-event metadata
can never silently disagree after interruption or failure.

This contract is implemented read-only-safe by `tools/runtime_state`. The
transaction layer NEVER executes a task and NEVER invokes AI — callers supply
staged content. The planner remains strictly read-only.

**Validation ownership.** The transaction layer promotes only what it is given;
it does not know task output contracts. The **runner** (`tools/task_runner`) is
responsible for validating a candidate output against the task-specific contract
*before* staging/commit, and it does so for **every** executor (executor success
is never sufficient for commit — see `tools/task_runner/output_contracts.py`).
Only a contract-valid candidate is ever staged; a failed check aborts the
transaction with no promotion.

---

# One Atomic Task Result

A single task result is the atomic promotion of:

* the task **output** (`task_outputs/…` or `reports/…`),
* the task **provenance** record (`provenance/<TASK_ID>.yaml`),
* the **manifest** entry (status, output binding, hash, validation),
* the **run state** entry (task lifecycle, revision),
* the **trace-event** metadata (journal events).

None of these is considered final until the commit completes.

---

# Runtime Layout

```text
runtime/runs/<RUN_ID>/
├── state.yaml          # RUN_STATE_SCHEMA.md
├── manifest.yaml       # RUN_MANIFEST_SCHEMA.md
├── trace.md
├── completion.yaml
├── lock/               # single-run writer lock (lock.json)
├── staging/            # per-transaction staging: <TXN_ID>/{output.bin, provenance.yaml, journal.json}
├── provenance/
├── task_outputs/
└── reports/
```

All transaction paths must resolve strictly under the run directory.

---

# Transaction Phases

```text
prepared   staged   validated   committing   committed   aborted   recovery_required
```

---

# Atomicity Rules

1. Never write directly to a final output path.
2. Stage all content under `staging/<TRANSACTION_ID>/`.
3. Validate staged files before promotion (output hash self-consistency).
4. Record the transaction journal (with intent + expected revision) **before**
   final promotion.
5. Promote output and provenance with atomic replacement (`os.replace` on the
   same filesystem).
6. Update state and manifest with monotonically increasing, **matching**
   revisions (compare-before-write; `RevisionConflict` on drift — no lost updates).
7. Preserve enough journal information to recover after interruption.
8. **Never mark a task `completed` before output and provenance are promoted and
   the output hash is verified.**
9. Never expose a partially written YAML or artifact as final (atomic writes only).
10. The planner remains read-only; the transaction layer is the sole writer.

---

# Trace Events

The transaction emits structured events (stored in the journal) for later trace
assembly — it does not build the human-readable reasoning trace:

```text
transaction_started   output_staged   provenance_staged   validation_passed
commit_started   output_promoted   provenance_promoted   state_updated
manifest_updated   transaction_committed   transaction_aborted   recovery_required
```

---

# Locking

A single-run writer lock (`lock/lock.json`, created with an atomic exclusive
open) ensures two writers cannot commit the same run concurrently. The lock
carries owner identity and a creation timestamp (never secrets). It fails safely
when already held and is **never broken automatically**. A stale lock (age >
documented TTL) is reported by recovery and may be removed only by an explicit
recovery action.

---

# Recovery

Recovery is read-only inspection plus explicit repair. `inspect_recovery`
produces a plan and changes nothing. `apply_recovery` performs only authorized
actions, and explicit actions only when approved. Detected conditions:

| # | Condition | Typical action |
|---|-----------|----------------|
| 1 | staging exists, nothing promoted | discard staging (**safe/automatic-eligible**) |
| 2 | output promoted, provenance missing | manual (explicit) |
| 3 | output + provenance promoted, state not updated | finalize state+manifest (explicit) |
| 4 | state / manifest revision mismatch | manual reconcile (explicit) |
| 5 | task `running` with no active transaction | reset to `not_started` (explicit) |
| 6 | journal `committing` after termination | inspect adjacent conditions |
| 7 | stale lock | remove stale lock (explicit; documented TTL) |
| 8 | output hash differs from provenance | manual; never mark completed (explicit) |

Only condition (1) — discard-staging, where **no final file was written** — is
eligible for automatic repair. Everything that could affect a promoted artifact
or the run's committed state requires explicit approval. Nothing is repaired on
read.

---

# Security

* All staged and final paths must resolve under the run directory. Absolute
  paths, `..` traversal, and symlink escapes are rejected.
* Promotion refuses to write onto/through a symlink that escapes the run root.
* Secrets are never placed in lock or journal metadata.

---

# Boundaries

* The transaction layer does not execute engineering tasks and does not invoke AI.
* It may create, update, and recover test runtime directories.
* The planner and validator never write runtime state.

---

# Consumers

The single-task runner (`tools/task_runner`) is the first writer that drives this
contract: it stages one task's output + provenance and commits them through the
transaction layer, advancing state and manifest to the same new revision. It
executes exactly one planner-approved task per invocation, uses only the safe
fixture executor in v0.1, and never invokes AI or the Engineering Production
Engine. See `tools/task_runner/README.md`.
