# ECF Single-Task Runner (v0.1)

Executes **exactly one** planner-approved task and stops. It is the first, minimal
step toward an execution runner and deliberately does the least possible.

> Never executes a whole workflow. Never grants human approval. Never invokes the
> Engineering Production Engine. Never invokes AI. Never runs arbitrary shell
> commands. The only v0.1 executor is a safe local **fixture** executor.

> The run it executes against is created by the **Run Initialization Engine**
> (`tools/run_initializer`), which writes the schema-valid initial `state.yaml` /
> `manifest.yaml` (revision 0) so the runner never has to author runtime YAML.

## Reused components (not duplicated)

- **workflow validator** — validates the workflow before anything runs
- **workflow planner** — computes the runnable frontier and per-task `execution_state / output_validity / planned_action`
- **provenance model** — authoritative ECF/EKB identity + environment dependencies
- **artifact fingerprint** — SHA-256 of inputs and output
- **runtime transaction layer** — atomic stage → commit of output + provenance + state + manifest, with the single-run writer lock

## Output validation ownership (executor-independent)

**Executor success is never sufficient for commit.** The runner applies the
task-specific output contract to **every** executor's candidate output — fixture,
Claude Code, future providers, test doubles — *before* provenance generation and
commit. Task-specific validation must never live inside a single executor, or a
non-Claude executor could commit a structurally invalid output.

- Generic checks (non-empty, allowed output root, safe path, parseable JSON/YAML)
  run first, then the **task-specific** validator.
- `tools/task_runner/output_contracts.py` owns the validators and a registry:
  `TASK_OUTPUT_VALIDATORS[task_id] -> validator(candidate, request, repo_root)`.
  A registered validator is **always** invoked for its task; unknown tasks pass
  through generic validation only until a task-specific contract exists.
- `TASK-CLASSIFY-0001` is registered with the full engineering-intent-result
  contract (exactly one JSON envelope; matching task/version/Work-Request IDs;
  primary/secondary intents drawn from the authoritative EKB taxonomy; required
  evidence and confidence; no recommendation/approval/production/unknown fields;
  no trailing or free-form content).
- The Claude executor invokes the **same** canonical `validate_intent_result` as
  defense in depth (single implementation, no drift).
- A failed contract check aborts the transaction: no output/provenance is
  promoted, the task is not completed, prior valid output is untouched, and the
  writer lock is released.
- **recovery inspection** — read-only pre-flight consistency check

## What the runner does (in order)

1. Load and **validate** the workflow (invalid → exit 1).
2. Load run **state + manifest** (missing/invalid provenance mode → exit 2).
3. **Inspect recovery** — refuse if any condition is unresolved (exit 3).
4. Ask the **planner** for the runnable frontier.
5. Select **exactly one** task (explicit `--task`, or `--next` when exactly one is ready).
6. Resolve the task spec + pinned version (version mismatch → exit 2).
7. Build a `TaskExecutionRequest` and invoke **one** executor (read-only input paths).
8. Receive **one** candidate output; **validate** it (one non-empty output, path under `task_outputs/`|`reports/`, no escape, parseable where mechanical, inputs unmodified).
9. Generate **authoritative provenance** (the executor never supplies provenance values).
10. **Stage and commit** output + provenance + state + manifest via the transaction layer.
11. Release the lock and **stop**.

A task becomes `completed` only after the transaction commit verifies the promoted
output hash. The runner stops after one task regardless of success or failure.

## Executor interface (provider-independent)

```python
class TaskExecutor:
    id = "..."
    def execute(self, request: TaskExecutionRequest) -> TaskExecutionResult: ...
```

The runner core contains no Claude-specific or shell logic. Two executors ship:

- **`fixture`** (always available, safe) — reads a predefined candidate-output file and returns its bytes.
- **`claude-code`** (AI-backed; **disabled by default**) — executes only `TASK-CLASSIFY-0001`, invoking Claude Code through one configured command to produce a validated JSON intent envelope. Requires **both** `--executor claude-code` and `--allow-ai-executor`. See `tools/task_runner/executors/README.md` and `runtime_schemas/ENGINEERING_INTENT_RESULT_SCHEMA.md`.

A successful executor result is **not** a committed task result — the runner still
validates and transacts it.

## Readiness rules

A task may execute only when: the workflow validates; the run configuration is
valid; no unresolved recovery condition exists; the planner marks the task
`planned_action: run` or `rerun`; every required input exists; task and workflow
versions match; permission boundaries permit the executor; and the run lock can be
acquired. A completed **valid** task is not rerun without `--force-rerun`; a
`stale` task (planner `planned_action: rerun`) may run because the planner requires it.

## CLI

```powershell
python tools/task_runner/run_task.py <workflow> --run <run-dir> `
  --task TASK-CLASSIFY-0001 --executor fixture --fixture <candidate-output-file> [--format json]

# select the sole ready task (fails if 0 or >1 ready):
python tools/task_runner/run_task.py <workflow> --run <run-dir> --next --executor fixture --fixture <file>

# PowerShell wrapper (no implicit looping):
.\scripts\run-one-task.ps1 -Workflow <wf> -Run <dir> -Task TASK-CLASSIFY-0001 -Fixture <file>
```

Exit codes: `0` committed · `1` rejected/failed · `2` config/infra · `3` recovery required.

## Trace events

`runner_started, workflow_validated, recovery_inspected, planner_evaluated,
task_selected, lock_acquired, task_marked_running, executor_started,
executor_completed, output_validated, provenance_generated, transaction_started,
transaction_committed, task_completed, runner_stopped` (and `runner_failed` /
`recovery_required`). No private chain-of-thought is generated or exposed.

## Security

Least authority: fixture executor only; no network, no arbitrary shell, no Claude,
no sibling repositories, no vendor/canonical writes. All final outputs stay under
the supplied run directory; path traversal and unsafe symlinks are rejected; no
secrets are written to logs, events, provenance, or lock files.

## Tests

```powershell
python -m unittest discover -s tools/task_runner/tests
```
