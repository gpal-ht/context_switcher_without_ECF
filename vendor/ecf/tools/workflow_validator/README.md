# ECF Workflow Conformance Validator

Read-only, mechanical validation of ECF workflow specifications.

> **This tool validates the ECF control plane. It does not execute engineering reasoning.**

It answers one question:

> Is this workflow structurally safe and internally consistent enough for an execution runner to consume?

It does **not** run the workflow, invoke any task, call any AI, or write any file.

---

## What it checks

The validator parses a workflow specification (front matter, the Stable Output
Bindings table, the machine-readable `depends_on` block, and the numbered steps)
and runs a set of stable, coded checks:

| Code  | Check |
|-------|-------|
| WF001 | Workflow file is readable |
| WF002 | Required workflow metadata present (`workflow_id`, `name`, `version`, `status`, `category`, `owner`, `entry_state`, `successful_exit_state`) |
| WF003 | Workflow ID is unique across workflow specifications |
| WF004 | Every referenced Task ID resolves to exactly one task specification |
| WF005 | Every pinned task version equals the task specification's declared version |
| WF006 | No task appears more than once (unless repeated invocation is declared) |
| WF007 | Every `depends_on` Task ID is present in the workflow |
| WF008 | Dependency graph is acyclic (reports the cycle path) |
| WF009 | Every backticked required input is produced upstream or declared |
| WF010 | Each task has exactly one output binding; no duplicate output paths |
| WF011 | Every runtime path uses `runtime/runs/<RUN_ID>/` (legacy roots rejected outside marked legacy docs) |
| WF012 | Task ordering respects declared dependencies |
| WF013 | Reasoning workflows exit at `waiting_for_human_approval` |
| WF014 | Human-approval boundary preserved (report production allowed; production-engine invocation / approval grant rejected) |
| WF015 | Required terminal artifacts present: runtime infrastructure (`state.yaml`, `manifest.yaml`) documented; task-owned (`trace.md`, `final-manifest.yaml`, `completion.yaml`, report, validation result) bound |
| WF016 | Trace/manifest/finalization tasks have explicit machine-readable dependencies |
| WF017 | No requirement for private chain-of-thought / hidden reasoning |
| WF018 | Metadata is consistent with `WORKFLOW_CATALOG.md` |
| WF019 | Status is an allowed workflow status |
| WF020 | Explicitly referenced normative files exist |
| WF021 | No task output is bound to a runtime-infrastructure file (`state.yaml` / run-root `manifest.yaml`); those are runtime-owned, not task outputs |

## What it does NOT do

- It does not execute the workflow or any task.
- It does not invoke Claude or any other AI, and it performs no engineering reasoning.
- It does not modify, repair, or normalize any file.
- It does not write runtime outputs or access the network.
- It does not read sibling repositories or modify vendor dependencies.

The only files it may write are temporary test files, and only under the OS
temporary directory (used by the test suite, not by validation).

## Usage

```powershell
# Validate one workflow (human-readable)
python tools/workflow_validator/validate_workflow.py `
  workflows/reasoning/WF-REASON-0001-engineering-recommendation.md

# JSON output
python tools/workflow_validator/validate_workflow.py `
  workflows/reasoning/WF-REASON-0001-engineering-recommendation.md --format json

# Validate every applicable workflow from the catalog
.\scripts\validate-workflows.ps1
```

Optional overrides (useful for tests / alternate layouts):

```text
--repo-root <dir>     repository root (default: inferred from this file's location)
--tasks-dir <dir>     task specifications directory (default: <repo>/tasks)
--catalog <file>      workflow catalog path (default: <repo>/workflows/WORKFLOW_CATALOG.md)
```

## Exit codes

```text
0  valid             (no error-severity findings; warnings are allowed)
1  validation errors (one or more error-severity findings)
2  validator execution/configuration failure (e.g., unreadable file)
```

Warnings never produce exit code `1`.

## JSON result shape

```json
{
  "workflow_id": "WF-REASON-0001",
  "valid": true,
  "errors": [],
  "warnings": [],
  "checks": [{ "code": "WF004", "status": "passed", "message": "18 task IDs resolved." }],
  "summary": { "task_count": 18, "edge_count": 111, "output_binding_count": 18 }
}
```

## Running the tests

```powershell
python -m unittest discover -s tools/workflow_validator/tests
```

The suite validates the real `WF-REASON-0001` (must pass) and one small invalid
fixture per failure path (`acceptance_tests/fixtures/workflows/`).

## How to add a new validation rule

1. Pick the next stable code (`WF021`, …). Codes are permanent; never reuse one.
2. Add a check function in `validate_workflow.py`:

   ```python
   @check("WF021")
   def wf021_my_rule(wf, idx, res):
       if bad_condition:
           _err(res, "WF021", "actionable message including the Task ID / field.")
       else:
           _ok(res, "WF021", "what passed.")
   ```

   - `wf` is the parsed `Workflow`; `idx` is the `RepoIndex` (tasks, catalog,
     other workflows); `res` collects results.
   - Use `_err` for error-severity, `_warn` for warning-severity, `_ok` for pass.
3. Document the code in the table above.
4. Add a positive assertion (the real workflow still passes) and a negative
   fixture + test.

Checks are independent and registered via the `@check` decorator, so adding one
does not touch the others.

## How to add a fixture

1. Create a minimal workflow under `acceptance_tests/fixtures/workflows/` that
   triggers exactly one failure. Keep it tiny — reference one or two real task
   IDs rather than duplicating the full 18-task workflow.
2. Add a test in `tests/test_validate_workflow.py` asserting the expected code:

   ```python
   def test_wf021_my_rule(self):
       self.assert_fails_with("wf021_my_rule.md", "WF021")
   ```

## Why validation precedes workflow execution

A runner that executes a workflow trusts its structure: that every task resolves,
versions are pinned, outputs are uniquely bound, dependencies form an acyclic
graph, and the run stops at the human-approval boundary. This validator makes
those guarantees **mechanical and repeatable** before any task runs, so an
execution runner (or a dry-run planner) can consume a workflow safely instead of
discovering structural defects mid-run.
