"""
ECF Run Initialization Engine (v0.1) — the engine.

Given a validated workflow, a Work Request, and a Run identity, it materializes a
schema-valid, planner-ready runtime run and confirms the initial runnable
frontier with the existing planner. It reuses the workflow validator, the
execution planner, the provenance model, and the runtime-state models/serializers
(no parser or serializer duplication).

Crash-safety: the run is built in a temporary sibling directory, validated by
reloading, checked by the planner, and only then atomically renamed into place.
A partially initialized final run is never exposed. Standard library only.

It NEVER executes a task, invokes AI, writes a task output, or creates a
provenance record for an unexecuted task.
"""

from __future__ import annotations

import errno
import gc
import os
import re
import shutil
import stat
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    InitError, InitExitCode, InitRequest, InitResult, WorkRequest,
)

# --- external tool stacks -------------------------------------------------- #
# The validator/planner and runtime_state subsystems each bind bare module names
# ('models', 'storage', ...). We load them in two phases, purging the clashing
# names between phases so each subsystem binds ITS OWN dependencies. The bound
# names then persist on the module objects, so later sys.modules changes don't
# affect them. Constants/classes are reached via the module objects (pl.*, tx.*).
_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent


def _purge(*names):
    for n in names:
        sys.modules.pop(n, None)


_purge("models", "storage", "transaction", "recovery")
for _p in (str(_TOOLS / "workflow_validator"), str(_TOOLS / "workflow_planner")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import validate_workflow as vw    # noqa: E402
import provenance as prov         # noqa: E402
import planner as pl              # noqa: E402

_purge("models", "storage", "transaction", "recovery")
if str(_TOOLS / "runtime_state") not in sys.path:
    sys.path.insert(0, str(_TOOLS / "runtime_state"))
import storage as rt_storage      # noqa: E402
import transaction as tx          # noqa: E402

# planner / runtime_state constants reached via the already-bound module objects
PS = pl.PlanStatus
RunStatus, TaskLifecycle = tx.RunStatus, tx.TaskLifecycle
OutputStatus, ValidationStatus = tx.OutputStatus, tx.ValidationStatus

# A conservative, filesystem-safe Run ID. The character class alone forbids path
# separators, '..', whitespace, and unsafe characters; the length is bounded.
RUN_ID_RE = re.compile(r"RUN-[A-Z0-9][A-Z0-9-]{2,127}\Z")

ALLOWED_PROVENANCE_MODES = ("required", "legacy")

# Runtime subdirectories required by the current runtime contracts. Only these
# are created — no fake terminal artifacts (trace.md/completion.yaml/outputs).
RUNTIME_SUBDIRS = (
    "inputs", "task_outputs", "reports", "provenance",
    "staging", "lock", "transactions",
)

WORK_REQUEST_INPUT = "inputs/work-request.md"

# Required Work Request sections (matched by normalized heading text). Aligned
# with WORK_REQUEST_SPECIFICATION.md "Validation".
_REQUIRED_WR_SECTIONS = (
    ("engineering_question", "engineering question"),
    ("desired_outcome", "desired outcome"),
    ("engineering_context_reference", "engineering context"),
    ("constraints", "constraints"),
    ("requested_deliverables", "requested deliverables"),
    ("success_criteria", "success criteria"),
)

_WR_ID_RE = re.compile(r"\bWR-[A-Z0-9][A-Z0-9-]*\b")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# Run ID validation
# --------------------------------------------------------------------------- #

def validate_run_id(run_id: str) -> None:
    """Reject unsafe / malformed Run IDs before touching the filesystem."""
    if not run_id or not run_id.strip():
        raise InitError("Run ID is empty.", InitExitCode.CONFIG)
    if run_id != run_id.strip():
        raise InitError("Run ID must not contain leading/trailing whitespace.",
                        InitExitCode.CONFIG)
    if os.path.isabs(run_id) or (len(run_id) >= 2 and run_id[1] == ":"):
        raise InitError(f"Run ID must not be an absolute path: {run_id!r}",
                        InitExitCode.CONFIG)
    if "/" in run_id or "\\" in run_id:
        raise InitError(f"Run ID must not contain a path separator: {run_id!r}",
                        InitExitCode.CONFIG)
    if ".." in run_id:
        raise InitError(f"Run ID must not contain '..': {run_id!r}", InitExitCode.CONFIG)
    if any(c.isspace() for c in run_id):
        raise InitError(f"Run ID must not contain whitespace: {run_id!r}",
                        InitExitCode.CONFIG)
    if not RUN_ID_RE.fullmatch(run_id):
        raise InitError(
            f"Run ID {run_id!r} is not of the required form "
            "RUN-[A-Z0-9][A-Z0-9-]{2,127}.", InitExitCode.CONFIG)


# --------------------------------------------------------------------------- #
# Work Request parsing + validation
# --------------------------------------------------------------------------- #

_HEADING_RE = re.compile(r"^#{1,6}\s+(.*\S)\s*$")


def _normalize_heading(text: str) -> str:
    # Drop leading section numbering like "1." / "12)" and surrounding markup.
    t = text.strip().lower()
    t = re.sub(r"^\d+[.)]\s*", "", t)
    t = t.strip(" #*_`")
    return t


def parse_work_request(text: str) -> WorkRequest:
    """
    Parse a Markdown Work Request into sections (heading -> body). Tolerant of
    heading levels and optional section numbering; never raises on shape.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    sections: dict = {}
    current = None
    buf: list = []

    def _flush():
        if current is not None:
            sections[current] = "\n".join(buf).strip()

    for line in text.split("\n"):
        m = _HEADING_RE.match(line)
        if m:
            _flush()
            current = _normalize_heading(m.group(1))
            buf = []
        else:
            buf.append(line)
    _flush()

    wr = WorkRequest(raw_text=text)

    # Work Request ID: an explicit "Work Request ID:" field wins; else the first
    # WR-xxxx token anywhere in the document.
    field_m = re.search(r"work\s*request\s*id\s*[:=]\s*(WR-[A-Z0-9][A-Z0-9-]*)",
                        text, re.I)
    if field_m:
        wr.work_request_id = field_m.group(1)
    else:
        tok = _WR_ID_RE.search(text)
        if tok:
            wr.work_request_id = tok.group(0)

    def _section_body(keyword: str) -> str:
        for heading, body in sections.items():
            if keyword in heading:
                return body
        return ""

    for attr, keyword in _REQUIRED_WR_SECTIONS:
        body = _section_body(keyword)
        setattr(wr, attr, body)
        wr.present_sections[attr] = bool(body.strip())

    # Title (best-effort; not a validation gate).
    title_body = _section_body("title")
    if title_body:
        wr.title = title_body.splitlines()[0].strip() if title_body.splitlines() else ""

    return wr


def validate_work_request(wr: WorkRequest, id_override: str = "") -> list:
    """Return a list of human-readable reasons the Work Request is invalid."""
    reasons: list = []

    wr_id = wr.work_request_id or id_override
    if not wr_id:
        reasons.append("missing Work Request ID (no 'WR-xxxx' found and no override given)")
    elif not re.fullmatch(r"WR-[A-Z0-9][A-Z0-9-]*", wr_id):
        reasons.append(f"Work Request ID {wr_id!r} is malformed (expected WR-xxxx)")

    for attr, keyword in _REQUIRED_WR_SECTIONS:
        if not wr.present_sections.get(attr):
            reasons.append(f"missing or empty required section: {keyword}")
    return reasons


# --------------------------------------------------------------------------- #
# Filesystem helpers
# --------------------------------------------------------------------------- #

def _on_rm_error(func, path, _exc):
    """rmtree onerror: clear read-only bit and retry (handles read-only inputs)."""
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        func(path)
    except OSError:
        pass


def _robust_rmtree(path: Path) -> None:
    if Path(path).exists():
        shutil.rmtree(path, onerror=_on_rm_error)


# Transient Windows sharing/access errors (antivirus, search indexer, a handle
# not yet fully released). NEVER includes logic errors.
_TRANSIENT_WINERRORS = frozenset({5, 32, 33})  # ACCESS_DENIED, SHARING/LOCK_VIOLATION


def _is_transient_fs_error(exc: BaseException) -> bool:
    if not isinstance(exc, OSError):
        return False
    if getattr(exc, "winerror", None) in _TRANSIENT_WINERRORS:
        return True
    return getattr(exc, "errno", None) in (errno.EACCES, errno.EBUSY)


def promote_run_directory(temp_dir, final_dir, *, retries: int = 5,
                          backoff: float = 0.1, sleep=time.sleep, rename=os.rename) -> None:
    """Atomically promote temp_dir -> final_dir with narrow Windows hardening.

    Retries ONLY the final rename, ONLY on transient Windows sharing/access
    errors, with a short bounded backoff. Never overwrites an active destination,
    never retries validation or logic errors, and preserves atomic visibility
    (there is no partial final run). On retry exhaustion the temporary directory
    is cleaned and a clear infrastructure error (InitExitCode.CONFIG) is raised.
    `sleep` and `rename` are injectable for deterministic tests.
    """
    temp_dir = Path(temp_dir)
    final_dir = Path(final_dir)
    gc.collect()  # deterministically release framework-owned handles before promotion
    attempts = max(1, int(retries))
    for attempt in range(attempts):
        if final_dir.exists():
            _robust_rmtree(temp_dir)  # never overwrite an active destination
            raise InitError(
                f"run directory already exists at promotion time: {final_dir}",
                InitExitCode.CONFIG)
        try:
            rename(temp_dir, final_dir)
            return
        except OSError as exc:
            if not _is_transient_fs_error(exc):
                raise  # non-transient: do not retry (caller cleans temp)
            if attempt == attempts - 1:
                _robust_rmtree(temp_dir)  # exhausted: leave no partial final run
                raise InitError(
                    f"run promotion failed after {attempts} attempts due to a "
                    f"transient filesystem lock (WinError "
                    f"{getattr(exc, 'winerror', '?')}): {exc}",
                    InitExitCode.CONFIG)
            sleep(backoff * (attempt + 1))


def _make_read_only(path: Path) -> None:
    """Best-effort read-only marking of a materialized run input."""
    try:
        os.chmod(path, stat.S_IREAD)
    except OSError:
        pass


def _dir_is_empty(path: Path) -> bool:
    try:
        next(iter(path.iterdir()))
        return False
    except StopIteration:
        return True
    except OSError:
        return False


def _force_replaceable(final_dir: Path) -> tuple:
    """
    Decide whether an existing run may be replaced under --force.

    Allowed only when the run is empty, has no/invalid state, or is a pristine
    never-progressed run (revision 0, no completed/running task, status
    requested/accepted). An active or completed run is never silently deleted.
    """
    if _dir_is_empty(final_dir):
        return True, "existing run directory is empty"
    state_file = final_dir / "state.yaml"
    if not state_file.is_file():
        return True, "existing run has no state.yaml (invalid/disposable)"
    try:
        state = tx.load_run_state(final_dir)
    except Exception:
        return True, "existing run state is unparseable (invalid/disposable)"
    progressed = any(
        s not in (TaskLifecycle.NOT_STARTED,)
        for s in (state.task_states or {}).values()
    )
    if (state.revision == 0 and not progressed
            and state.run_status in (RunStatus.REQUESTED, RunStatus.ACCEPTED)):
        return True, "existing run is pristine (revision 0, no task progressed)"
    return (False,
            f"existing run has progressed (status={state.run_status}, "
            f"revision={state.revision}); refusing to replace")


# --------------------------------------------------------------------------- #
# Initialization
# --------------------------------------------------------------------------- #

def _resolve_final_and_root(request: InitRequest) -> tuple:
    """Return (final_dir, run_root) from either --run-dir or --run-root/--run-id."""
    if request.run_dir:
        final = Path(request.run_dir).resolve()
        if final.name != request.run_id:
            raise InitError(
                f"--run-dir leaf {final.name!r} does not match --run-id "
                f"{request.run_id!r}.", InitExitCode.CONFIG)
        return final, final.parent
    if request.run_root:
        root = Path(request.run_root).resolve()
        return (root / request.run_id), root
    raise InitError("either --run-root or --run-dir is required.", InitExitCode.CONFIG)


def initialize_run(request: InitRequest) -> InitResult:
    """Initialize exactly one run and return a machine-readable result."""
    warnings: list = []

    # 1) provenance mode is explicit; legacy is never inferred.
    mode = (request.provenance_mode or "required").lower()
    if mode not in ALLOWED_PROVENANCE_MODES:
        raise InitError(f"invalid provenance mode {mode!r} "
                        f"(expected one of {ALLOWED_PROVENANCE_MODES}).",
                        InitExitCode.CONFIG)

    # 2) Run ID is validated before anything touches the filesystem.
    validate_run_id(request.run_id)

    # 3) load + validate the workflow (reuse the validator; no duplication).
    workflow_path = Path(request.workflow_path)
    if not workflow_path.is_file():
        raise InitError(f"workflow not found: {workflow_path}", InitExitCode.INVALID)
    try:
        repo_root = (Path(request.repo_root).resolve() if request.repo_root
                     else vw.resolve_repo_root(None, workflow_path))
        idx = vw.RepoIndex(repo_root, repo_root / "tasks",
                           repo_root / "workflows" / "WORKFLOW_CATALOG.md",
                           repo_root / "workflows")
        result, wf = vw.validate(workflow_path, idx)
    except InitError:
        raise
    except Exception as exc:
        raise InitError(f"could not load/validate workflow: {exc}", InitExitCode.CONFIG)
    if not result.valid:
        errs = "; ".join(f"{c.code}: {c.message}" for c in result.errors)
        raise InitError(f"workflow failed validation: {errs}", InitExitCode.INVALID,
                        reasons=[f"{c.code}: {c.message}" for c in result.errors])
    if not wf.task_ids:
        raise InitError("workflow declares no tasks.", InitExitCode.INVALID)
    wf_version = wf.front_matter.get("version", "")

    # 4) load + validate the Work Request.
    wr_path = Path(request.work_request_path)
    if not wr_path.is_file():
        raise InitError(f"Work Request not found: {wr_path}", InitExitCode.INVALID)
    wr_text = vw.read_text(wr_path)
    wr = parse_work_request(wr_text)
    wr_reasons = validate_work_request(wr, request.work_request_id_override)
    if wr_reasons:
        raise InitError("Work Request is invalid: " + "; ".join(wr_reasons),
                        InitExitCode.INVALID, reasons=wr_reasons)
    wr_id = wr.work_request_id or request.work_request_id_override

    # 5) resolve identities + final/temp locations.
    final_dir, run_root = _resolve_final_and_root(request)

    if final_dir.exists():
        if not request.force:
            raise InitError(
                f"run already exists: {final_dir} (use --force to replace an "
                "empty/invalid/pristine run).", InitExitCode.CONFIG)
        ok, why = _force_replaceable(final_dir)
        if not ok:
            raise InitError(f"--force refused: {why}.", InitExitCode.CONFIG)
        warnings.append(f"--force replacing existing run: {why}")

    # ECF / EKB identity for the manifest (read-only; git head best-effort).
    env = prov.EnvContext.from_repo(repo_root)

    # 6) build initial state + manifest objects (schema defaults baked in).
    state = tx.RunState(
        run_id=request.run_id, work_request_id=wr_id,
        workflow_id=wf.workflow_id, workflow_version=wf_version,
        provenance_mode=mode, run_status=RunStatus.ACCEPTED, active_task=None,
        task_states={tid: TaskLifecycle.NOT_STARTED for tid in wf.task_ids},
        revision=0, created_at=_now(), failure=None, recovery_status="none",
    )
    manifest_tasks = []
    for b in wf.bindings:
        tid = b["task_id"]
        manifest_tasks.append(tx.ManifestTask(
            id=tid, version=b.get("version", ""), output=b.get("output", ""),
            output_status=OutputStatus.NONE, provenance_path=f"provenance/{tid}.yaml",
            output_hash="", validation_status=ValidationStatus.UNKNOWN,
            status=TaskLifecycle.NOT_STARTED,
        ))
    manifest = tx.RunManifest(
        run_id=request.run_id, workflow_id=wf.workflow_id, workflow_version=wf_version,
        revision=0, executor={"type": "none", "has_run": False},
        ecf_version=env.ecf_version or "", ekb_version=env.ekb_version or "",
        tasks=manifest_tasks, findings=[], trace_path="trace.md",
        completion_path="completion.yaml",
    )

    # 7) materialize in a temporary sibling dir, then atomically rename.
    run_root.mkdir(parents=True, exist_ok=True)
    temp_dir = run_root / f".init-{request.run_id}-{uuid.uuid4().hex[:12]}"
    try:
        temp_dir.mkdir(parents=True, exist_ok=False)
        for sub in RUNTIME_SUBDIRS:
            (temp_dir / sub).mkdir(parents=True, exist_ok=True)

        # materialize the Work Request as a read-only run input (verbatim bytes).
        input_path = temp_dir / WORK_REQUEST_INPUT
        input_path.write_bytes(wr_path.read_bytes())
        _make_read_only(input_path)

        # write schema-valid state + manifest via the canonical serializers.
        tx.save_run_state(temp_dir, state)
        tx.save_manifest(temp_dir, manifest)

        # 8) validate by reloading (never trust what we just wrote).
        _validate_initialized(temp_dir, request.run_id, wr_id, mode, wf.task_ids)

        # 9) planner readiness gate — confirm the ACTUAL entry frontier.
        rt = pl.RuntimeState(temp_dir)
        plan = pl.compute_plan(wf, rt, source_path=str(workflow_path),
                               env=env, repo_root=repo_root)
        ready = list(plan.ready)
        blocked = list(plan.blocked)

        # The workflow's entry frontier = tasks with no dependencies. On a fresh
        # run these — and only these — must be ready. We confirm this from the
        # planner rather than hard-coding any Task ID.
        entry = [t for t in wf.task_ids if not wf.depends_on.get(t)]
        if set(ready) != set(entry):
            raise InitError(
                f"planner entry frontier {sorted(ready)} does not match the "
                f"workflow entry tasks {sorted(entry)}.", InitExitCode.CONFIG)

        # A freshly initialized run must have NO non-fresh task: nothing is
        # completed, stale, rerun-required, or failed before anything has run.
        # (The former TASK-TRACE-0002 / run-root manifest.yaml binding overlap
        # that made this impossible was resolved by rebinding that task to the
        # immutable reports/final-manifest.yaml.)
        non_fresh = [t.id for t in plan.tasks
                     if t.state in ("stale", "rerun_required", "completed", "failed")]
        if non_fresh:
            raise InitError(
                f"unexpected non-fresh task(s) at initialization: {sorted(non_fresh)}.",
                InitExitCode.CONFIG)
        for w in plan.warnings:
            warnings.append(f"planner: {w}")

        # 10) atomically promote the run. On Windows the final rename can hit a
        # transient sharing/access lock (antivirus/indexer); promote_run_directory
        # retries ONLY that rename, ONLY for transient errors, and never
        # overwrites an active destination. Validation failures never reach here.
        if final_dir.exists():
            _robust_rmtree(final_dir)
        promote_run_directory(temp_dir, final_dir)
    except BaseException:
        _robust_rmtree(temp_dir)
        raise

    return InitResult(
        status="initialized", run_id=request.run_id, run_dir=str(final_dir),
        workflow_id=wf.workflow_id, workflow_version=wf_version,
        work_request_id=wr_id, provenance_mode=mode, revision=0,
        task_count=len(wf.task_ids), ready_tasks=ready, blocked_count=len(blocked),
        warnings=warnings, message="run initialized", exit_code=InitExitCode.OK,
    )


def _validate_initialized(run_dir: Path, run_id: str, wr_id: str, mode: str,
                          task_ids: list) -> None:
    """Reload the just-written run and assert it is internally consistent."""
    try:
        rs = tx.load_run_state(run_dir)
        mf = tx.load_manifest(run_dir)
    except Exception as exc:
        raise InitError(f"initialized run did not reload: {exc}", InitExitCode.CONFIG)

    if rs.run_id != run_id or mf.run_id != run_id:
        raise InitError("state/manifest Run ID mismatch after initialization.",
                        InitExitCode.CONFIG)
    if rs.revision != 0 or mf.revision != 0:
        raise InitError("initial revisions must both be 0.", InitExitCode.CONFIG)
    if rs.work_request_id != wr_id:
        raise InitError("state Work Request ID mismatch after initialization.",
                        InitExitCode.CONFIG)
    if rs.provenance_mode != mode:
        raise InitError(f"provenance mode not persisted (got {rs.provenance_mode!r}).",
                        InitExitCode.CONFIG)
    missing = [t for t in task_ids if rs.task_states.get(t) != TaskLifecycle.NOT_STARTED]
    if missing:
        raise InitError(f"tasks not initialized as not_started: {missing}",
                        InitExitCode.CONFIG)
    if len(mf.tasks) != len(task_ids):
        raise InitError("manifest task count does not match the workflow.",
                        InitExitCode.CONFIG)
    for mt in mf.tasks:
        if mt.output_hash:
            raise InitError(f"unexecuted task {mt.id} must not carry an output hash.",
                            InitExitCode.CONFIG)
        if mt.status != TaskLifecycle.NOT_STARTED:
            raise InitError(f"manifest task {mt.id} is not not_started.",
                            InitExitCode.CONFIG)
    # no provenance record must exist for any unexecuted task
    prov_dir = run_dir / "provenance"
    if prov_dir.is_dir() and any(prov_dir.iterdir()):
        raise InitError("provenance records must not exist at initialization.",
                        InitExitCode.CONFIG)
