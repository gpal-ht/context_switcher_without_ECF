"""
ECF Execution Planner engine (read-only).

Given a validated workflow, repository state, and an optional runtime directory,
compute which task(s) are runnable right now, which are blocked and why, and the
remaining topological execution order.

The planner NEVER executes tasks, invokes AI, or writes files. It reuses the
workflow parser from tools/workflow_validator (no parser duplication).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Reuse the validator's parser + validation (no duplication).
_VALIDATOR_DIR = Path(__file__).resolve().parents[1] / "workflow_validator"
if str(_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_DIR))

import validate_workflow as vw  # noqa: E402

from models import (  # noqa: E402
    ExecutionPlan, ExecutionState, OutputValidity, PlanStatus, PlannedAction,
    TaskPlan, TaskState,
)
import provenance as prov  # noqa: E402


class PlannerError(Exception):
    """Raised for planner execution/configuration failures (exit code 2)."""


# --------------------------------------------------------------------------- #
# Minimal, tolerant runtime readers (stdlib only; never write)
# --------------------------------------------------------------------------- #

# Map manifest/state task-status strings onto planner TaskStates.
_STATUS_MAP = {
    "completed": TaskState.COMPLETED,
    "completed_with_findings": TaskState.COMPLETED,
    "running": TaskState.RUNNING,
    "failed": TaskState.FAILED,
    "cancelled": TaskState.CANCELLED,
    "abandoned": TaskState.CANCELLED,
    "superseded": TaskState.SUPERSEDED,
    "requested": TaskState.NOT_STARTED,
}

# Run-level statuses that mean the whole run has stopped.
_RUN_FAILED = {"failed"}
_RUN_BLOCKED = {"blocked"}
_RUN_CANCELLED = {"cancelled", "abandoned"}
_RUN_SUPERSEDED = {"superseded"}
_RUN_COMPLETE = {"completed", "completed_with_findings", "waiting_for_human_approval"}


def _read(path: Path) -> str:
    try:
        return vw.read_text(path)
    except OSError as exc:
        raise PlannerError(f"cannot read runtime file: {path} ({exc})")


def _scalar(text: str, *keys: str):
    """Return the first `key: value` scalar found for any of the given keys."""
    for key in keys:
        m = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", text, re.M)
        if m:
            return m.group(1).strip().strip('"\'')
    return None


def _parse_provenance_config(text: str):
    """
    Parse an explicit provenance policy block:

        provenance:
          mode: required
          schema_version: "0.1.0"

    Returns (mode, schema_version) or (None, None) when absent.
    """
    if not text:
        return None, None
    m = re.search(r"^provenance:\s*\n((?:^[ \t]+.*\n?)+)", text, re.M)
    if not m:
        return None, None
    block = m.group(1)
    mode_m = re.search(r"^[ \t]+mode:\s*(\S+)\s*$", block, re.M)
    schema_m = re.search(r"^[ \t]+schema_version:\s*(.+?)\s*$", block, re.M)
    mode = mode_m.group(1).strip().strip('"\'').lower() if mode_m else "(unset)"
    schema = schema_m.group(1).strip().strip('"\'') if schema_m else None
    return mode, schema


def _parse_manifest_task_statuses(text: str) -> dict:
    """
    Parse a manifest 'tasks:' block into {task_id: raw_status}.

    Tolerant of both block and inline mapping styles. Never raises on shape.
    """
    statuses: dict = {}
    current = None
    in_tasks = False
    for line in text.split("\n"):
        if re.match(r"^tasks:\s*$", line):
            in_tasks = True
            continue
        if in_tasks and re.match(r"^\S", line) and not line.lstrip().startswith("-"):
            # a new top-level key ends the tasks block
            if not re.match(r"^\s", line):
                in_tasks = False
        idm = re.match(r"^\s*-\s*id:\s*(TASK-[A-Z]+-\d{4})", line)
        if idm:
            current = idm.group(1)
            # inline status on same logical item may appear on later lines
            continue
        if current:
            sm = re.match(r"^\s*status:\s*([A-Za-z_]+)", line)
            if sm:
                statuses[current] = sm.group(1)
                current = None
    return statuses


class RuntimeState:
    """
    A read-only snapshot of a runtime run directory.

    Reads (never writes): state.yaml, manifest.yaml, completion.yaml, and the
    task_outputs/ + reports/ trees. Absent files are tolerated; a present but
    unreadable/garbled required file is a PlannerError (invalid runtime).
    """

    ALLOWED_PROVENANCE_MODES = ("required", "legacy")

    def __init__(self, run_dir: Path | None):
        self.run_dir = run_dir
        self.present = run_dir is not None
        self.run_status = None
        self.task_statuses: dict = {}
        self.findings: list = []
        self._existing_files: set = set()
        # Provenance policy is EXPLICIT configuration, never inferred from the
        # filesystem. `provenance_mode` is read from run state/manifest.
        self.provenance_mode = None
        self.provenance_schema_version = None
        self.provenance_config_present = False

        if not self.present:
            return
        if not run_dir.exists():
            raise PlannerError(f"runtime directory does not exist: {run_dir}")
        if not run_dir.is_dir():
            raise PlannerError(f"runtime path is not a directory: {run_dir}")

        self._load()

        # Fix 1: explicit provenance mode is mandatory for any runtime.
        if not self.provenance_config_present:
            raise PlannerError(
                "invalid runtime configuration: no provenance mode declared in "
                "state.yaml or manifest.yaml (expected 'provenance.mode: required|legacy'). "
                "Missing provenance configuration must never silently enter legacy mode.")
        if self.provenance_mode not in self.ALLOWED_PROVENANCE_MODES:
            raise PlannerError(
                f"invalid runtime configuration: provenance mode '{self.provenance_mode}' "
                f"is not one of {self.ALLOWED_PROVENANCE_MODES}.")

    @property
    def provenance_required(self) -> bool:
        return self.provenance_mode == "required"

    def provenance_path(self, task_id: str) -> Path:
        return self.run_dir / "provenance" / f"{task_id}.yaml"

    def _load(self):
        rd = self.run_dir
        state_txt = _read(rd / "state.yaml") if (rd / "state.yaml").is_file() else ""
        manifest_txt = _read(rd / "manifest.yaml") if (rd / "manifest.yaml").is_file() else ""
        completion_txt = _read(rd / "completion.yaml") if (rd / "completion.yaml").is_file() else ""

        # Run-level status: completion > state > manifest.
        self.run_status = (
            _scalar(completion_txt, "final_run_status")
            or _scalar(state_txt, "state", "current_state", "run_status", "status")
            or _scalar(manifest_txt, "run_status", "run_state")
        )
        if self.run_status:
            self.run_status = self.run_status.lower()

        # Explicit provenance mode (state.yaml wins over manifest.yaml).
        for txt in (state_txt, manifest_txt):
            mode, schema = _parse_provenance_config(txt)
            if mode is not None:
                self.provenance_mode = mode
                self.provenance_schema_version = schema
                self.provenance_config_present = True
                break

        if manifest_txt:
            self.task_statuses = _parse_manifest_task_statuses(manifest_txt)
            # open blocker findings (informational)
            for m in re.finditer(r"classification:\s*blocker", manifest_txt):
                self.findings.append("blocker")

        # Index existing output files (relative to run dir), read-only.
        for sub in ("", "task_outputs", "reports"):
            base = rd / sub if sub else rd
            if base.is_dir():
                for p in base.iterdir():
                    if p.is_file():
                        rel = p.relative_to(rd).as_posix()
                        self._existing_files.add(rel)

    def output_exists(self, rel_output: str) -> bool:
        """True if a bound output path (e.g. 'task_outputs/x.yaml') exists."""
        if not self.present:
            return False
        rel = rel_output.replace("\\", "/")
        if rel in self._existing_files:
            return True
        # also accept a bare leaf match at the run root (trace.md/manifest.yaml)
        return Path(self.run_dir / rel).is_file()

    def declared_status(self, task_id: str):
        raw = self.task_statuses.get(task_id)
        return _STATUS_MAP.get(raw.lower()) if raw else None


# --------------------------------------------------------------------------- #
# Topological order (deterministic)
# --------------------------------------------------------------------------- #

def topological_order(wf) -> list:
    """
    Kahn's algorithm over depends_on, tie-broken by the workflow's declared
    binding-table order for determinism. Raises PlannerError on a cycle
    (the validator's WF008 should already have caught it).
    """
    order_index = {tid: i for i, tid in enumerate(wf.task_ids)}
    deps = {t: set(wf.depends_on.get(t, [])) for t in wf.task_ids}
    indeg = {t: len(deps[t]) for t in wf.task_ids}
    ready = sorted([t for t in wf.task_ids if indeg[t] == 0], key=lambda t: order_index[t])
    out = []
    while ready:
        n = ready.pop(0)
        out.append(n)
        for m in wf.task_ids:
            if n in deps[m]:
                deps[m].discard(n)
                indeg[m] -= 1
                if indeg[m] == 0:
                    ready.append(m)
        ready.sort(key=lambda t: order_index[t])
    if len(out) != len(wf.task_ids):
        raise PlannerError("workflow dependency graph contains a cycle")
    return out


# --------------------------------------------------------------------------- #
# Planning
# --------------------------------------------------------------------------- #

def compute_plan(wf, runtime: RuntimeState, source_path: str = "",
                 env=None, repo_root: Path | None = None) -> ExecutionPlan:
    """
    Compute the execution plan for a (already validated) workflow given a
    runtime snapshot. Read-only.

    When the runtime enables provenance, completed outputs are re-verified
    against their provenance records (fingerprints + versions) and may be
    reclassified `stale` (own record invalid) or `rerun_required` (a dependency
    is stale).
    """
    output_of = {b["task_id"]: b["output"] for b in wf.bindings}
    version_of = {b["task_id"]: b["version"] for b in wf.bindings}
    wf_version = wf.front_matter.get("version", "")
    topo = topological_order(wf)
    env_deps = prov.parse_environment_dependencies(wf.text)

    required_mode = runtime.present and runtime.provenance_required
    legacy_mode = runtime.present and runtime.provenance_mode == "legacy"

    if required_mode and env is None and repo_root is not None:
        env = prov.EnvContext.from_repo(repo_root)

    run_failed = bool(runtime.run_status and runtime.run_status in _RUN_FAILED)
    run_blocked = bool(runtime.run_status and runtime.run_status in _RUN_BLOCKED)
    run_cancelled = bool(runtime.run_status and runtime.run_status in _RUN_CANCELLED)
    run_superseded = bool(runtime.run_status and runtime.run_status in _RUN_SUPERSEDED)

    ES, OV, PA = ExecutionState, OutputValidity, PlannedAction
    exec_state: dict = {}
    validity: dict = {}
    action: dict = {}
    reasons_map: dict = {}    # tid -> list[dict] structured reasons
    reason_text: dict = {}
    waiting_for: dict = {}

    # ---- Pass 1: execution_state and output_validity (independent per task) ---
    for tid in wf.task_ids:
        declared = runtime.declared_status(tid) if runtime.present else None
        out_exists = runtime.output_exists(output_of.get(tid, "")) if runtime.present else False
        if declared in (ES.FAILED, ES.CANCELLED, ES.SUPERSEDED, ES.RUNNING):
            exec_state[tid] = declared
        elif declared == ES.COMPLETED or out_exists:
            exec_state[tid] = ES.COMPLETED
        else:
            exec_state[tid] = ES.NOT_STARTED

        if exec_state[tid] != ES.COMPLETED:
            validity[tid] = OV.NOT_APPLICABLE
        elif required_mode:
            reasons = prov.load_and_validate(
                runtime.provenance_path(tid),
                task_id=tid, task_version=version_of.get(tid, ""),
                workflow_id=wf.workflow_id, workflow_version=wf_version,
                env=env, run_dir=runtime.run_dir,
                ekb_required=prov.ekb_required_for(env_deps, tid),
                repo_root=repo_root,
            )  # may raise prov.PlannerConfigError (propagated as a config failure)
            if not reasons:
                validity[tid] = OV.VALID
            else:
                codes = {r.check for r in reasons}
                if "missing_provenance" in codes:
                    validity[tid] = OV.MISSING
                elif "malformed_provenance" in codes:
                    validity[tid] = OV.MALFORMED
                else:
                    validity[tid] = OV.STALE
                reasons_map[tid] = [r.to_dict() for r in reasons]
        else:  # legacy mode: output existence trusted, validity unverified
            validity[tid] = OV.UNKNOWN

    def needs_rerun(d):
        return validity.get(d) in OV.INVALID or action.get(d) == PA.RERUN

    # ---- Pass 2 (topological): planned_action + cascade ----------------------
    for tid in topo:
        ex, ov = exec_state[tid], validity[tid]
        deps = wf.depends_on.get(tid, [])

        if ex == ES.COMPLETED:
            if ov in OV.INVALID:
                action[tid] = PA.RERUN
                first = (reasons_map.get(tid) or [{}])[0]
                reason_text[tid] = _stale_summary(first)
            elif any(needs_rerun(d) for d in deps):
                action[tid] = PA.RERUN
                cause = next(d for d in deps if needs_rerun(d))
                reasons_map[tid] = [{"check": "stale_dependency", "artifact": cause}]
                reason_text[tid] = f"dependency {cause} needs rerun; rerun required."
            else:
                action[tid] = PA.NONE
                if legacy_mode:
                    reason_text[tid] = "Output present (provenance mode: legacy; not verified)."
                elif required_mode:
                    reason_text[tid] = "Output present and provenance valid."
                else:
                    reason_text[tid] = "Recorded completed."
            continue
        if ex == ES.FAILED:
            action[tid] = PA.STOP
            reason_text[tid] = "runtime reports task failed."
            continue
        if ex in (ES.CANCELLED, ES.SUPERSEDED):
            action[tid] = PA.NONE
            reason_text[tid] = f"runtime reports task {ex}."
            continue
        if ex == ES.RUNNING:
            action[tid] = PA.NONE
            reason_text[tid] = "task is running."
            continue

        # ex == NOT_STARTED
        if run_cancelled:
            exec_state[tid] = ES.CANCELLED
            action[tid] = PA.NONE
            reason_text[tid] = "run cancelled."
            continue
        if run_superseded:
            exec_state[tid] = ES.SUPERSEDED
            action[tid] = PA.NONE
            reason_text[tid] = "run superseded."
            continue

        blocking, waiting = [], []
        if run_failed:
            blocking.append("workflow run has failed")
        if run_blocked:
            blocking.append("workflow run is blocked")
        for d in deps:
            dex, dov, dact = exec_state[d], validity[d], action.get(d)
            if dov in OV.INVALID or dact == PA.RERUN:
                blocking.append(f"upstream {d} needs rerun ({dov if dov in OV.INVALID else 'rerun'})")
            elif dex == ES.FAILED:
                blocking.append(f"dependency {d} failed")
            elif dex in (ES.CANCELLED, ES.SUPERSEDED):
                blocking.append(f"dependency {d} {dex}")
            elif dex != ES.COMPLETED:
                waiting.append(d)
            else:
                dout = output_of.get(d, "")
                if dout and not runtime.output_exists(dout):
                    blocking.append(f"required output {vw.leaf(dout)} missing")
                    waiting.append(vw.leaf(dout))

        uniq_wait = list(dict.fromkeys(waiting))
        if blocking:
            action[tid] = PA.BLOCKED
            waiting_for[tid] = uniq_wait
            reason_text[tid] = "; ".join(dict.fromkeys(blocking)) + "."
        elif waiting:
            action[tid] = PA.WAIT
            waiting_for[tid] = uniq_wait
            reason_text[tid] = "waiting for " + ", ".join(uniq_wait) + "."
        else:
            action[tid] = PA.RUN
            reason_text[tid] = ("Entry task; no dependencies." if not deps
                                else "All dependencies completed and required outputs exist.")

    # ---- Build TaskPlans -----------------------------------------------------
    ordered = []
    for tid in wf.task_ids:
        ordered.append(TaskPlan(
            id=tid,
            execution_state=exec_state[tid],
            output_validity=validity[tid],
            planned_action=action[tid],
            output=output_of.get(tid, ""),
            depends_on=list(wf.depends_on.get(tid, [])),
            reason=reason_text.get(tid, ""),
            waiting_for=waiting_for.get(tid, []),
            stale_reasons=reasons_map.get(tid, []),
        ))

    remaining = [t for t in topo
                 if not (exec_state[t] == ES.COMPLETED
                         and validity[t] not in OV.INVALID
                         and action[t] != PA.RERUN)]

    # ---- Overall plan status -------------------------------------------------
    any_rerun = any(validity[t] in OV.INVALID or action[t] == PA.RERUN for t in wf.task_ids)
    all_done = all(exec_state[t] == ES.COMPLETED and validity[t] not in OV.INVALID
                   and action[t] != PA.RERUN for t in wf.task_ids)
    if run_failed:
        status = PlanStatus.FAILED
    elif run_cancelled or run_superseded:
        status = PlanStatus.BLOCKED
    elif all_done:
        status = PlanStatus.COMPLETE
    elif any_rerun:
        status = PlanStatus.RERUN_REQUIRED
    elif any(action[t] == PA.RUN for t in wf.task_ids):
        status = PlanStatus.RUNNABLE
    else:
        status = PlanStatus.BLOCKED

    plan = ExecutionPlan(
        workflow_id=wf.workflow_id,
        status=status,
        source_path=source_path,
        run_dir=str(runtime.run_dir) if runtime.present else "",
        provenance_mode=(runtime.provenance_mode or "") if runtime.present else "",
        tasks=ordered,
        remaining_order=remaining,
    )
    if runtime.run_status:
        plan.notes.append(f"runtime run status: {runtime.run_status}")
    if legacy_mode:
        plan.warnings.append(
            "provenance mode is 'legacy': completion is determined by output "
            "existence only; outputs are NOT verified against provenance.")
    if runtime.findings:
        plan.notes.append(
            f"{len(runtime.findings)} open blocker finding(s) recorded in the manifest "
            "(informational; the workflow contract governs whether they halt progression)")
    return plan


_STALE_LABELS = {
    "missing_provenance": "provenance record is missing",
    "malformed_provenance": "provenance record is malformed",
    "input_hash_changed": "input hash changed",
    "input_missing": "a declared input is missing",
    "output_hash_changed": "output hash changed",
    "output_missing": "recorded output is missing",
    "task_version_changed": "task version changed",
    "workflow_version_changed": "workflow version changed",
    "workflow_id_mismatch": "workflow id mismatch",
    "task_id_mismatch": "task id mismatch",
    "ecf_version_changed": "ECF version changed",
    "ecf_commit_changed": "ECF commit changed",
    "ekb_version_changed": "EKB version changed",
    "ekb_commit_changed": "EKB commit changed",
}


def _stale_summary(reason: dict) -> str:
    if not reason:
        return "output is stale."
    label = _STALE_LABELS.get(reason.get("check"), reason.get("check", "stale"))
    art = reason.get("artifact")
    return f"{label}{(' (' + art + ')') if art else ''}."


def plan_from_paths(workflow_path: Path, run_dir: Path | None, idx) -> ExecutionPlan:
    """Validate the workflow, then compute the plan. Read-only."""
    result, wf = vw.validate(workflow_path, idx)
    if not result.valid:
        plan = ExecutionPlan(
            workflow_id=wf.workflow_id or "(unknown)",
            status=PlanStatus.INVALID,
            source_path=str(workflow_path),
            validation_errors=[f"{c.code}: {c.message}" for c in result.errors],
        )
        return plan
    runtime = RuntimeState(run_dir)
    repo_root = getattr(idx, "repo_root", None)
    return compute_plan(wf, runtime, source_path=str(workflow_path), repo_root=repo_root)
