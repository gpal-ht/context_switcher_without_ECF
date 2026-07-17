"""
ECF single-task runner (v0.1).

Executes exactly ONE planner-approved task and stops. It reuses — and does not
duplicate — the workflow validator, planner, provenance model, artifact
fingerprinting, runtime transaction layer, and recovery inspection.

It never executes an entire workflow, never grants human approval, never invokes
the Engineering Production Engine, never invokes AI, and never runs arbitrary
shell commands. The only executor in v0.1 is the safe local fixture executor.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# --- intra-package imports (relative -> task_runner.models never clashes) --- #
from .models import (
    ExitCode, InputArtifact, RunnerEvent, RunnerResult, TaskExecutionRequest,
)
from .executor import TaskExecutor
from .output_contracts import validate_task_output

# --- external tool stacks -------------------------------------------------- #
# The validator/planner and runtime_state subsystems each use bare module names
# ('models', 'storage', ...). We load them in two phases, purging the clashing
# names between phases so each subsystem binds ITS OWN dependencies. Their bound
# names persist on the module objects afterwards, so later sys.modules changes
# don't affect them. Constants are accessed via the module objects (pl.*, tx.*).
_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent


def _purge(*names):
    for n in names:
        sys.modules.pop(n, None)


_purge("models", "storage", "transaction", "recovery")
sys.path.insert(0, str(_TOOLS / "workflow_validator"))
sys.path.insert(0, str(_TOOLS / "workflow_planner"))
import validate_workflow as vw    # noqa: E402
import provenance as prov         # noqa: E402
import planner as pl              # noqa: E402

_purge("models", "storage", "transaction", "recovery")
sys.path.insert(0, str(_TOOLS / "runtime_state"))
import storage as rt_storage      # noqa: E402
import transaction as tx          # noqa: E402
import recovery as rec            # noqa: E402

from artifact_fingerprint import fingerprint as fp  # noqa: E402

# planner + runtime_state constants (via the already-bound module objects)
ES, OV, PA, PS = pl.ExecutionState, pl.OutputValidity, pl.PlannedAction, pl.PlanStatus
TL = tx.TaskLifecycle

ALLOWED_OUTPUT_ROOTS = ("task_outputs/", "reports/")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Runner:
    def __init__(self, workflow_path, run_dir, executor: TaskExecutor, repo_root=None):
        self.workflow_path = Path(workflow_path)
        self.run_dir = Path(run_dir)
        self.executor = executor
        self.repo_root = repo_root
        self.events: list = []

    def _emit(self, name, detail=""):
        ev = {"event": name, "at": _now()}
        if detail:
            ev["detail"] = detail
        self.events.append(ev)

    def _result(self, task_id, exit_code, status, message="", run_id="", **kw):
        return RunnerResult(
            run_id=run_id, task_id=task_id, exit_code=exit_code, status=status,
            message=message, events=self.events,
            executor_id=getattr(self.executor, "id", ""),
            output=kw.get("output", ""), provenance=kw.get("provenance", ""),
            state_revision=kw.get("state_revision"),
            manifest_revision=kw.get("manifest_revision"))

    def run(self, task_id=None, use_next=False, force_rerun=False) -> RunnerResult:
        self._emit(RunnerEvent.RUNNER_STARTED)

        # 1) validate workflow
        try:
            repo_root = self.repo_root or vw.resolve_repo_root(None, self.workflow_path)
            idx = vw.RepoIndex(repo_root, repo_root / "tasks",
                               repo_root / "workflows" / "WORKFLOW_CATALOG.md",
                               repo_root / "workflows")
            result, wf = vw.validate(self.workflow_path, idx)
        except Exception as exc:
            self._emit(RunnerEvent.RUNNER_FAILED, str(exc))
            return self._result(task_id or "", ExitCode.CONFIG, "config_error",
                                f"could not load workflow: {exc}")
        if not result.valid:
            self._emit(RunnerEvent.RUNNER_FAILED, "workflow invalid")
            return self._result(task_id or "", ExitCode.REJECTED, "rejected",
                                "workflow failed validation")
        self._emit(RunnerEvent.WORKFLOW_VALIDATED)

        # 2) run configuration (state + manifest; RuntimeState validates prov mode)
        try:
            rt = pl.RuntimeState(self.run_dir)
            state = tx.load_run_state(self.run_dir)
            tx.load_manifest(self.run_dir)
        except (pl.PlannerError, tx.TransactionError) as exc:
            self._emit(RunnerEvent.RUNNER_FAILED, str(exc))
            return self._result(task_id or "", ExitCode.CONFIG, "config_error",
                                f"invalid run configuration: {exc}")

        # 3) recovery inspection — refuse when inconsistent
        recovery_plan = rec.inspect_recovery(self.run_dir)
        self._emit(RunnerEvent.RECOVERY_INSPECTED,
                   "consistent" if recovery_plan.consistent else "inconsistent")
        if not recovery_plan.consistent:
            self._emit(RunnerEvent.RECOVERY_REQUIRED)
            conds = ", ".join(c.type for c in recovery_plan.conditions)
            return self._result(task_id or "", ExitCode.RECOVERY_REQUIRED, "recovery_required",
                                f"unresolved recovery conditions: {conds}", run_id=state.run_id)

        # 4) planner frontier
        try:
            env = prov.EnvContext.from_repo(repo_root)
            plan = pl.compute_plan(wf, rt, env=env, repo_root=repo_root)
        except Exception as exc:
            self._emit(RunnerEvent.RUNNER_FAILED, str(exc))
            return self._result(task_id or "", ExitCode.CONFIG, "config_error",
                                f"planner failed: {exc}", run_id=state.run_id)
        self._emit(RunnerEvent.PLANNER_EVALUATED, f"status={plan.status}")
        by_id = {t.id: t for t in plan.tasks}

        # 5/6) select exactly one task
        if use_next:
            ready = [t for t in plan.tasks if t.planned_action == PA.RUN]
            if len(ready) != 1:
                return self._result(task_id or "", ExitCode.REJECTED, "rejected",
                                    f"--next requires exactly one ready task; found {len(ready)}",
                                    run_id=state.run_id)
            selected = ready[0]
        else:
            if not task_id:
                return self._result("", ExitCode.CONFIG, "config_error",
                                    "no task specified (use --task or --next)", run_id=state.run_id)
            if task_id not in by_id:
                return self._result(task_id, ExitCode.REJECTED, "rejected",
                                    f"unknown task {task_id} (not in workflow)", run_id=state.run_id)
            selected = by_id[task_id]

        tid = selected.id
        act = selected.planned_action
        if act in (PA.RUN, PA.RERUN):
            pass
        elif (selected.execution_state == ES.COMPLETED
              and selected.output_validity == OV.VALID and act == PA.NONE and force_rerun):
            pass  # operator-confirmed forced rerun of a valid completed task
        elif (selected.execution_state == ES.COMPLETED and selected.output_validity == OV.VALID):
            return self._result(tid, ExitCode.REJECTED, "rejected",
                                f"{tid} is completed and valid; use --force-rerun to re-execute",
                                run_id=state.run_id)
        else:
            return self._result(tid, ExitCode.REJECTED, "rejected",
                                f"{tid} is not runnable (planned_action={act}); {selected.reason}",
                                run_id=state.run_id)
        self._emit(RunnerEvent.TASK_SELECTED, f"{tid} action={act}")

        # 7) resolve task spec + pinned version
        binding = selected.output
        version_of = {b["task_id"]: b["version"] for b in wf.bindings}
        pinned = version_of.get(tid, "")
        matches = idx.task_versions.get(tid, [])
        if not matches:
            return self._result(tid, ExitCode.REJECTED, "rejected",
                                f"task specification for {tid} not found", run_id=state.run_id)
        task_spec_path, spec_version = matches[0]
        if spec_version and pinned and spec_version != pinned:
            return self._result(tid, ExitCode.CONFIG, "config_error",
                                f"version mismatch: workflow pins {pinned}, spec is {spec_version}",
                                run_id=state.run_id)

        # inputs = producing dependencies' bound outputs (read-only)
        output_of = {b["task_id"]: b["output"] for b in wf.bindings}
        inputs, input_hashes = [], {}
        for d in wf.depends_on.get(tid, []):
            dout = output_of.get(d)
            if not dout:
                continue
            inputs.append(InputArtifact(name=d, path=dout))
        for ia in inputs:
            try:
                p = rt_storage.safe_join(self.run_dir, ia.path)
            except rt_storage.PathSafetyError as exc:
                return self._result(tid, ExitCode.REJECTED, "rejected",
                                    f"unsafe input path: {exc}", run_id=state.run_id)
            if not p.is_file():
                return self._result(tid, ExitCode.REJECTED, "rejected",
                                    f"required input missing: {ia.path}", run_id=state.run_id)
            input_hashes[ia.path] = fp.sha256_file(p)

        # EKB identity (authoritative from workflow metadata)
        env_deps = prov.parse_environment_dependencies(wf.text)
        ekb_required = prov.ekb_required_for(env_deps, tid)
        if ekb_required and env.ekb_version is None:
            return self._result(tid, ExitCode.CONFIG, "config_error",
                                f"{tid} requires EKB identity but it is unavailable",
                                run_id=state.run_id)

        # 8) acquire lock
        owner = f"task_runner:{tid}"
        try:
            tx.acquire_run_lock(self.run_dir, owner)
        except tx.LockHeld as exc:
            return self._result(tid, ExitCode.CONFIG, "config_error",
                                f"run lock held by {exc.lock.owner}", run_id=state.run_id)
        self._emit(RunnerEvent.LOCK_ACQUIRED)

        try:
            txn = tx.begin_task_transaction(self.run_dir, tid, binding,
                                            f"provenance/{tid}.yaml", owner)
            self._emit(RunnerEvent.TASK_MARKED_RUNNING)
            self._emit(RunnerEvent.TRANSACTION_STARTED, txn.journal.transaction_id)

            request = TaskExecutionRequest(
                run_id=state.run_id, work_request_id=state.work_request_id,
                workflow_id=wf.workflow_id, workflow_version=wf.front_matter.get("version", ""),
                task_id=tid, task_version=pinned, task_spec_path=str(task_spec_path),
                output_binding=binding, inputs=inputs,
                ecf_version=env.ecf_version or "", ecf_commit=env.ecf_commit or "",
                ekb_required=ekb_required, ekb_version=env.ekb_version or "",
                ekb_commit=env.ekb_commit or "",
                permission_boundary={"read_inputs": [i.path for i in inputs],
                                     "write_output": binding, "no_network": True,
                                     "no_shell": True, "no_ai": True, "no_vendor_write": True},
                executor_config={}, run_dir=str(self.run_dir))

            self._emit(RunnerEvent.EXECUTOR_STARTED, getattr(self.executor, "id", ""))
            try:
                exec_result = self.executor.execute(request)
            except Exception as exc:
                self._fail_task(tid, txn, f"executor raised: {exc}")
                return self._result(tid, ExitCode.REJECTED, "failed",
                                    f"executor error: {exc}", run_id=state.run_id)
            self._emit(RunnerEvent.EXECUTOR_COMPLETED, exec_result.status)
            if not exec_result.succeeded:
                self._fail_task(tid, txn, "executor reported failure")
                return self._result(tid, ExitCode.REJECTED, "failed",
                                    f"executor failed: {exec_result.failure}", run_id=state.run_id)

            # 10) validate candidate output — generic checks, THEN the
            # task-specific output contract applied to EVERY executor's candidate
            # (fixture, Claude, future providers). Executor success is never
            # sufficient for commit; the runner owns the contract.
            candidate = exec_result.output_bytes
            ok, reasons = self._validate_output(candidate, binding, exec_result)
            if candidate is not None:
                tok, treasons = validate_task_output(tid, candidate, request, repo_root)
                if not tok:
                    reasons.extend(treasons)
            for ia in inputs:  # declared read-only inputs must be unchanged
                p = rt_storage.safe_join(self.run_dir, ia.path)
                if fp.sha256_file(p) != input_hashes[ia.path]:
                    reasons.append(f"declared read-only input modified: {ia.path}")
            if reasons:
                self._fail_task(tid, txn, "; ".join(reasons))
                return self._result(tid, ExitCode.REJECTED, "failed",
                                    "invalid candidate output: " + "; ".join(reasons),
                                    run_id=state.run_id)
            self._emit(RunnerEvent.OUTPUT_VALIDATED)

            # 11) authoritative provenance (executor does NOT supply these values)
            osha = fp.sha256_bytes(candidate)
            prov_text = self._build_provenance(state, wf, tid, pinned, inputs, input_hashes,
                                               binding, osha, env, ekb_required)
            self._emit(RunnerEvent.PROVENANCE_GENERATED)

            # 12) stage + commit through the transaction layer
            txn.stage_output(candidate, binding, osha)
            txn.stage_provenance(prov_text, f"provenance/{tid}.yaml")
            vok, vreasons = txn.validate()
            if not vok:
                self._fail_task(tid, txn, "; ".join(vreasons))
                return self._result(tid, ExitCode.REJECTED, "failed",
                                    "transaction validation failed: " + "; ".join(vreasons),
                                    run_id=state.run_id)
            try:
                new_state = txn.commit()
            except tx.RevisionConflict as exc:
                self._fail_task(tid, txn, str(exc))
                return self._result(tid, ExitCode.CONFIG, "config_error",
                                    f"revision conflict: {exc}", run_id=state.run_id)
            except tx.TransactionError as exc:
                if "recovery" in str(exc).lower():
                    self._emit(RunnerEvent.RECOVERY_REQUIRED, str(exc))
                    return self._result(tid, ExitCode.RECOVERY_REQUIRED, "recovery_required",
                                        str(exc), run_id=state.run_id)
                self._fail_task(tid, txn, str(exc))
                return self._result(tid, ExitCode.REJECTED, "failed", str(exc), run_id=state.run_id)

            self._emit(RunnerEvent.TRANSACTION_COMMITTED)
            self._emit(RunnerEvent.TASK_COMPLETED)
            new_manifest = tx.load_manifest(self.run_dir)
            self._emit(RunnerEvent.RUNNER_STOPPED)
            return self._result(tid, ExitCode.OK, "committed",
                                f"{tid} executed and committed", run_id=new_state.run_id,
                                output=binding, provenance=f"provenance/{tid}.yaml",
                                state_revision=new_state.revision,
                                manifest_revision=new_manifest.revision)
        finally:
            try:
                tx.release_run_lock(self.run_dir, owner)
            except tx.LockError:
                pass

    # -- helpers ------------------------------------------------------------ #
    def _fail_task(self, task_id, txn, detail):
        """Record a safe failure: abort staging, mark task failed, keep revisions matched."""
        try:
            if txn.journal.phase not in ("committing", "committed"):
                txn.abort(detail)
        except Exception:
            pass
        try:
            state = tx.load_run_state(self.run_dir)
            manifest = tx.load_manifest(self.run_dir)
            state.task_states[task_id] = TL.FAILED
            if state.active_task == task_id:
                state.active_task = None
            state.failure = {"code": "task_execution_failed", "detail": detail[:200],
                             "task_id": task_id}
            mt = manifest.task(task_id)
            if mt is not None:
                mt.status = TL.FAILED
            tx.save_run_state(self.run_dir, state)
            tx.save_manifest(self.run_dir, manifest)
        except Exception:
            pass
        self._emit(RunnerEvent.RUNNER_FAILED, detail)

    def _validate_output(self, candidate, binding, exec_result):
        reasons = []
        if candidate is None:
            reasons.append("no candidate output bytes returned")
            return False, reasons
        if exec_result.output_path:
            reasons.append("executor returned both bytes and a path (ambiguous)")
        if len(candidate) == 0:
            reasons.append("candidate output is empty")
        norm = binding.replace("\\", "/")
        if not any(norm.startswith(r) for r in ALLOWED_OUTPUT_ROOTS):
            reasons.append(f"output binding must be under {ALLOWED_OUTPUT_ROOTS}: {binding}")
        try:
            rt_storage.safe_join(self.run_dir, binding)
        except rt_storage.PathSafetyError as exc:
            reasons.append(f"unsafe output path: {exc}")
        if norm.endswith((".yaml", ".yml", ".json")):
            text = candidate.decode("utf-8", errors="strict") if isinstance(candidate, bytes) else candidate
            # JSON is a strict subset of YAML; accept either (Claude returns a JSON envelope).
            try:
                import json as _json
                _json.loads(text)
            except Exception:
                try:
                    rt_storage.load_yaml(text)
                except Exception as exc:
                    reasons.append(f"output is not parseable JSON/YAML: {exc}")
        return (len(reasons) == 0), reasons

    def _build_provenance(self, state, wf, tid, pinned, inputs, input_hashes,
                          binding, osha, env, ekb_required):
        lines = [
            "schema_version: 1",
            f"run_id: {state.run_id}",
            f"work_request_id: {state.work_request_id}",
            f"workflow_id: {wf.workflow_id}",
            f"workflow_version: {wf.front_matter.get('version', '')}",
            f"task_id: {tid}",
            f"task_version: {pinned}",
        ]
        if inputs:
            lines.append("inputs:")
            for ia in inputs:
                lines += [f"  - name: {ia.name}", f"    path: {ia.path}",
                          f"    sha256: {input_hashes[ia.path]}"]
        else:
            lines.append("inputs: []")
        lines += ["output:", f"  path: {binding}", f"  sha256: {osha}",
                  f"ecf_version: {env.ecf_version or ''}", f"ecf_commit: {env.ecf_commit or ''}"]
        if ekb_required:
            lines += [f"ekb_version: {env.ekb_version or ''}", f"ekb_commit: {env.ekb_commit or ''}"]
        lines += ["executor:", f"  id: {getattr(self.executor, 'id', 'fixture')}",
                  f"generated_at: {_now()}"]
        return "\n".join(lines) + "\n"


def run_one_task(workflow_path, run_dir, executor, task_id=None, use_next=False,
                 force_rerun=False, repo_root=None) -> RunnerResult:
    return Runner(workflow_path, run_dir, executor, repo_root=repo_root).run(
        task_id, use_next=use_next, force_rerun=force_rerun)
