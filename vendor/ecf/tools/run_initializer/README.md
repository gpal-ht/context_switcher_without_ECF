# ECF Run Initialization Engine (v0.1)

Converts a **validated workflow + a Work Request + a Run identity** into a
schema-valid, planner-ready runtime run:

```text
validated workflow  +  Work Request  +  Run ID   ─▶   runtime/runs/<RUN_ID>/
```

The resulting run is consumable — with no manual YAML authoring — by the existing
workflow validator, execution planner, runtime-state layer, recovery inspector,
single-task runner, and provenance subsystem.

> It **never** executes a task, invokes AI, creates a task output, marks a task
> completed, grants approval, or writes a provenance record for an unexecuted
> task. It only creates the initial run.

## Atomic promotion (Windows-hardened)

The run is built under a temporary `.init-<RUN_ID>-<uuid>/` directory and made
visible by a single atomic rename to the final `runs/<RUN_ID>/`. On Windows this
final rename can intermittently fail with `WinError 5 (Access denied)` /
`WinError 32 (sharing violation)` when antivirus or the search indexer transiently
locks the just-created directory. `promote_run_directory(...)`:

- releases framework-owned handles, then retries **only the final rename**, and
  **only** for known transient sharing/access errors, with a short bounded backoff;
- never retries validation or logic errors, and never overwrites an active
  destination;
- on retry exhaustion cleans the temporary directory and raises a clear
  infrastructure error — there is never a partial final run;
- exposes injectable `sleep`/`rename` for deterministic tests.

## Reused components (not duplicated)

- **workflow validator** — validates the workflow before a run is created
- **execution planner** — confirms the initial runnable frontier
- **provenance model** (`EnvContext`) — resolves ECF/EKB identity for the manifest
- **runtime-state models + serializers** — writes `state.yaml` / `manifest.yaml`
  through the exact same constrained block-YAML writers the transaction layer uses

## What it does (in order)

1. Resolve and validate the provenance mode (explicit; **legacy is never inferred**).
2. Validate the **Run ID** (`RUN-[A-Z0-9][A-Z0-9-]{2,127}`; no separators, `..`,
   whitespace, or unsafe characters).
3. Load and **validate the workflow** (invalid → exit 1).
4. Load and **validate the Work Request** against the Work Request contract
   (invalid → exit 1).
5. Resolve identities (Run ID, Work Request ID, workflow ID/version, pinned task
   versions) and the final/temp run locations.
6. Build schema-valid initial `state.yaml` and `manifest.yaml` (revision 0).
7. Materialize the run in a **temporary sibling directory**, copy the Work
   Request as a read-only run input, and create the required runtime subdirs.
8. **Validate by reloading** the just-written state/manifest.
9. **Planner readiness gate** — confirm the actual entry frontier.
10. **Atomically rename** the temp directory into `runtime/runs/<RUN_ID>/`.

A partially initialized final run is never exposed; the temp directory is removed
on any failure.

## Canonical runtime layout produced

```text
runtime/runs/<RUN_ID>/
├── state.yaml          # revision 0, provenance mode explicit, all tasks not_started
├── manifest.yaml       # revision 0, per-task bindings, no output hashes
├── inputs/
│   └── work-request.md # the Work Request, materialized read-only
├── task_outputs/       # empty
├── reports/            # empty
├── provenance/         # empty (no records for unexecuted tasks)
├── staging/            # empty
├── lock/               # empty
└── transactions/       # empty
```

`trace.md` and `completion.yaml` are **not** created — they are produced by the
run's finalization tasks, not fabricated at initialization.

## Initial state and manifest

- **state.yaml**: `run_status: accepted`, `active_task: null`, every workflow task
  `not_started`, `revision: 0`, explicit `provenance.mode`, `recovery_status: none`.
- **manifest.yaml**: workflow identity, ECF/EKB identity, `executor: {type: none,
  has_run: false}`, one entry per task (pinned version + output binding,
  `output_status: none`, `validation_status: unknown`, **no output hash**),
  `revision: 0` (in lockstep with state).

## Planner readiness gate

Before reporting success the initializer runs the existing planner against the
new run and confirms the entry frontier: the tasks with no dependencies — and
only those — are `ready`. The ready Task IDs are returned in the result (never
hard-coded). For `WF-REASON-0001` the entry frontier is `TASK-CLASSIFY-0001`.

A freshly initialized run therefore has **no** non-fresh task: nothing is
completed, stale, rerun-required, or failed before anything runs. The initializer
asserts this invariant.

> **Resolved manifest-ownership overlap:** `TASK-TRACE-0002` was previously bound
> to the run-root `manifest.yaml`, which every runnable run contains from
> initialization — so the planner read that one task as non-fresh (`stale`) in
> `required` mode. That task is now bound to the immutable
> `reports/final-manifest.yaml` (the run-root `manifest.yaml` is runtime
> infrastructure, not a task output; validator rule WF021 enforces this), so the
> overlap no longer occurs and no warning is emitted.

## CLI

```powershell
python tools/run_initializer/initialize_run.py `
  workflows/reasoning/WF-REASON-0001-engineering-recommendation.md `
  --work-request work_requests/WR-0001.md `
  --run-root runtime/runs --run-id RUN-REASON-WR0001-LIVE-0001 [--format json]

# explicit run directory (its leaf must equal --run-id):
python tools/run_initializer/initialize_run.py <workflow> `
  --work-request <WR> --run-dir runtime/runs/RUN-... --run-id RUN-...

# PowerShell wrapper (resolves ECF root from its own location, canonical/vendored):
.\scripts\initialize-run.ps1 -WorkRequest work_requests\WR-0001.md `
  -RunId RUN-REASON-WR0001-LIVE-0001
```

Options: `--provenance-mode required|legacy` (default `required`),
`--work-request-id` (override, used only when the document lacks an ID),
`--force` (replace an existing **empty / invalid / pristine** run only).

Exit codes: `0` initialized · `1` invalid workflow or Work Request ·
`2` configuration / filesystem / infrastructure failure.

## `--force` safety

`--force` replaces an existing run **only** when it is empty, has no/invalid
`state.yaml`, or is pristine (revision 0, no task progressed, status
`requested`/`accepted`). An active or completed run is never silently deleted.

## Security

Least authority: writes strictly under the supplied run root; Run IDs and paths
are rejected if they escape it (absolute paths, separators, `..`, unsafe symlinks);
the Work Request is copied verbatim as a read-only input and never executed; no
network, no shell, no AI, no sibling repositories, no vendor/canonical writes.

## Tests

```powershell
python -m unittest discover -s tools/run_initializer/tests
```

Covers valid/invalid initialization, unsafe/traversal Run IDs, no-overwrite and
`--force` rules, temp cleanup on failure, reload + revision + provenance-mode +
not_started invariants, the planner frontier, absence of outputs/provenance, JSON
output, read-only-outside-root, wrapper root resolution (canonical **and**
vendored, cwd-independent, outer-Git-root-not-used, exit codes preserved), and a
non-live end-to-end acceptance scenario (initialize → one fixture task → next task
ready). No live Claude is ever invoked; all runs use temporary directories.
