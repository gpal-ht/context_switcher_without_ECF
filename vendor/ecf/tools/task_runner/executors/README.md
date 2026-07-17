# Task-Runner Executors

Provider-specific and AI-backed executors for the single-task runner. Executors
turn a `TaskExecutionRequest` into **exactly one candidate output**. They never
write the final runtime output, generate authoritative provenance, update state or
manifest, select another task, or loop — the runner owns all of that.

## `claude-code` — AI intent classification (v0.1 vertical slice)

Executes **only** `TASK-CLASSIFY-0001` (Determine Engineering Intent). Every other
Task ID is rejected.

### Disabled by default — explicit opt-in required

The executor cannot be created without an explicit AI opt-in. Both are required:

```powershell
--executor claude-code --allow-ai-executor
```

There is no silent fallback to Claude.

### What it does

1. Rejects any task other than `TASK-CLASSIFY-0001`.
2. Loads the authoritative intent taxonomy from the bundled EKB
   (`vendor/engineering_kb/foundations/ENGINEERING_INTENT_MODEL.md`). If it is
   unavailable, it **fails before invoking Claude**.
3. Reads the accepted Work Request (read-only) from `<run_dir>/inputs/`.
4. Generates a task-specific prompt (identity, engineering question, desired
   outcome, requested output schema, permitted/prohibited paths, one-primary-output
   rule, no-recommendation / no-approval / no-source-modification / no-vendor-write,
   observable-evidence-only, and a **Permission Preflight** telling Claude to
   request its permissions once).
5. Invokes the configured Claude command **without a shell** (`shell=False`), as a
   fixed executable + fixed argument list; captures stdout, stderr, exit code, and
   duration; enforces a timeout.
6. Extracts **exactly one** JSON envelope (free-form text or multiple documents
   fail) and mechanically validates it against the taxonomy and the request.
7. Returns the canonical JSON envelope as the single candidate output. The runner
   validates and commits it; the executor commits nothing.

### Configuration

```powershell
--claude-command claude        # executable (no machine-specific path hard-coded)
--claude-arg <arg>             # optional fixed argument(s), repeatable
--timeout 120                  # seconds (conservative default)
```

The prompt is passed on stdin. No network access is requested by ECF; Claude
Code's own environment remains governed by local Claude permissions.

### Output contract

The candidate output is the JSON envelope defined in
`runtime_schemas/ENGINEERING_INTENT_RESULT_SCHEMA.md` (valid JSON, hence valid
YAML). Free-form Markdown is never accepted as the authoritative output.

### Failure rules (fail the task, promote nothing)

timeout · nonzero exit · malformed JSON · multiple JSON documents · schema failure
· unexpected Task ID · unsupported intent · prohibited field (recommendation /
approval / production) · changed read-only input. Diagnostics are captured without
secrets; there is no automatic retry.

### Security

Receives only the declared read-only Work Request; no shell interpolation; no
network config changes; no secrets; no sibling repositories; no vendor or canonical
writes; never permitted to commit or run post-approval production; never exposes
hidden chain-of-thought.

## Tests

`tools/task_runner/tests/test_intent_validator.py` (validator) and
`test_claude_executor.py` (executor + runner integration) — the Claude subprocess
is mocked; no live Claude is required.
