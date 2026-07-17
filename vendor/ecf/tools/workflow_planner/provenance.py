"""
Task provenance parsing and read-only stale-output validation.

Reads `runtime/runs/<RUN_ID>/provenance/<TASK_ID>.yaml`, re-fingerprints the
declared inputs and output, and compares versions/commits to decide whether a
completed task output is still valid.

Read-only: never creates, repairs, or modifies provenance, outputs, or state.
Standard library only (no PyYAML); parses the constrained subset documented in
runtime_schemas/TASK_PROVENANCE_SCHEMA.md.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Reuse the fingerprint tool (tools/ on path -> import as a package).
_TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from artifact_fingerprint import fingerprint as fp  # noqa: E402

SCHEMA_VERSION = 1


class ProvenanceError(Exception):
    """Raised when a provenance record cannot be read or parsed (=> malformed)."""


# --------------------------------------------------------------------------- #
# Environment context (ECF / EKB identity at planning time)
# --------------------------------------------------------------------------- #

@dataclass
class EnvContext:
    ecf_version: str | None = None
    ecf_commit: str | None = None
    ekb_version: str | None = None
    ekb_commit: str | None = None

    @staticmethod
    def from_repo(repo_root: Path) -> "EnvContext":
        """
        Build the live ECF/EKB context (read-only).

        ECF version comes ONLY from the canonical machine-readable version file
        (`ecf-version.yaml`), never from README text. Git commit is best-effort
        (see commit_policy in that file). EKB identity comes from the bundled
        `vendor/engineering_kb/VERSION`.
        """
        ecf_version = None
        ver_file = repo_root / "ecf-version.yaml"
        if ver_file.is_file():
            txt = ver_file.read_text(encoding="utf-8", errors="ignore")
            mv = re.search(r"^version:\s*(\S+)", txt, re.M)
            ecf_version = mv.group(1) if mv else None
        ecf_commit = _git_head(repo_root)

        ekb_version = ekb_commit = None
        ekb_ver_file = repo_root / "vendor" / "engineering_kb" / "VERSION"
        if ekb_ver_file.is_file():
            txt = ekb_ver_file.read_text(encoding="utf-8", errors="ignore")
            mv = re.search(r"^version:\s*(\S+)", txt, re.M)
            mc = re.search(r"^source_commit:\s*(\S+)", txt, re.M)
            ekb_version = mv.group(1) if mv else None
            ekb_commit = mc.group(1) if mc else None
        return EnvContext(ecf_version, ecf_commit, ekb_version, ekb_commit)


def _git_head(repo_root: Path) -> str | None:
    """Return the short HEAD commit, or None. Read-only, no network."""
    try:
        import subprocess
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip() or None
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------- #
# Provenance record + constrained parser
# --------------------------------------------------------------------------- #

@dataclass
class Provenance:
    schema_version: str | None = None
    run_id: str | None = None
    work_request_id: str | None = None
    workflow_id: str | None = None
    workflow_version: str | None = None
    task_id: str | None = None
    task_version: str | None = None
    inputs: list = field(default_factory=list)   # [{name, path, sha256}]
    output_path: str | None = None
    output_sha256: str | None = None
    ecf_version: str | None = None
    ecf_commit: str | None = None
    ekb_version: str | None = None
    ekb_commit: str | None = None

    @property
    def declares_ekb(self) -> bool:
        return bool(self.ekb_version or self.ekb_commit)


def _scalar(text: str, key: str):
    m = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", text, re.M)
    return m.group(1).strip().strip('"\'') if m else None


def parse_environment_dependencies(wf_text: str) -> dict:
    """
    Parse the authoritative `environment_dependencies` block from a workflow.

    Returns {"default": {"ecf": bool, "ekb": bool}, "<TASK-ID>": {...}, ...}.

    The workflow/task contract is authoritative: whether EKB validation applies
    is decided here, NOT by the provenance record being validated. If no block
    is present, ECF is required for every task and EKB for none (safe default;
    the workflow SHOULD declare the block explicitly).
    """
    result = {"default": {"ecf": True, "ekb": False}}
    m = re.search(r"```yaml\s*\nenvironment_dependencies:\n(.*?)```", wf_text, re.S)
    if not m:
        return result
    body = m.group(1)
    current = None
    for line in body.split("\n"):
        head = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if head:
            current = head.group(1)
            result.setdefault(current, {"ecf": True, "ekb": False})
            continue
        kv = re.match(r"^\s+(ecf|ekb):\s*(\S+)\s*$", line)
        if kv and current is not None:
            required = kv.group(2).strip().lower() in ("required", "true", "yes")
            result[current][kv.group(1)] = required
    return result


def ekb_required_for(env_deps: dict, task_id: str) -> bool:
    entry = env_deps.get(task_id, env_deps.get("default", {}))
    return bool(entry.get("ekb", False))


def parse_provenance(text: str) -> Provenance:
    """Parse the constrained provenance subset. Raise ProvenanceError if unusable."""
    if not text.strip():
        raise ProvenanceError("empty provenance record")

    p = Provenance()
    p.schema_version = _scalar(text, "schema_version")
    p.run_id = _scalar(text, "run_id")
    p.work_request_id = _scalar(text, "work_request_id")
    p.workflow_id = _scalar(text, "workflow_id")
    p.workflow_version = _scalar(text, "workflow_version")
    p.task_id = _scalar(text, "task_id")
    p.task_version = _scalar(text, "task_version")
    p.ecf_version = _scalar(text, "ecf_version")
    p.ecf_commit = _scalar(text, "ecf_commit")
    p.ekb_version = _scalar(text, "ekb_version")
    p.ekb_commit = _scalar(text, "ekb_commit")

    lines = text.split("\n")

    # inputs: list of {name, path, sha256}
    in_inputs = False
    cur = None
    for raw in lines:
        if re.match(r"^inputs:\s*$", raw):
            in_inputs = True
            continue
        if in_inputs:
            if re.match(r"^\S", raw) and not raw.lstrip().startswith("-"):
                in_inputs = False
            else:
                nm = re.match(r"^\s*-\s*name:\s*(.+?)\s*$", raw)
                if nm:
                    cur = {"name": nm.group(1).strip(), "path": None, "sha256": None}
                    p.inputs.append(cur)
                    continue
                if cur is not None:
                    pm = re.match(r"^\s*path:\s*(.+?)\s*$", raw)
                    sm = re.match(r"^\s*sha256:\s*(.+?)\s*$", raw)
                    if pm:
                        cur["path"] = pm.group(1).strip()
                    elif sm:
                        cur["sha256"] = sm.group(1).strip()

    # output: block { path, sha256 }
    om = re.search(r"^output:\s*$\n((?:^[ \t]+.*\n?)+)", text, re.M)
    if om:
        block = om.group(1)
        p.output_path = _block_scalar(block, "path")
        p.output_sha256 = _block_scalar(block, "sha256")

    if not p.task_id or not p.output_path or not p.output_sha256:
        raise ProvenanceError("provenance missing required fields (task_id/output)")
    return p


def _block_scalar(block: str, key: str):
    m = re.search(rf"^[ \t]+{re.escape(key)}:\s*(.+?)\s*$", block, re.M)
    return m.group(1).strip().strip('"\'') if m else None


# --------------------------------------------------------------------------- #
# Validation (read-only)
# --------------------------------------------------------------------------- #

@dataclass
class StaleReason:
    check: str
    detail: str = ""
    artifact: str = ""
    recorded: str = ""
    current: str = ""

    def to_dict(self) -> dict:
        d = {"check": self.check}
        for k in ("detail", "artifact", "recorded", "current"):
            v = getattr(self, k)
            if v:
                d[k] = v
        return d


def _resolve(path: str, run_dir: Path, repo_root: Path | None) -> Path | None:
    candidates = [run_dir / path]
    if repo_root is not None:
        candidates.append(repo_root / path)
    candidates.append(Path(path))
    for c in candidates:
        if c.is_file():
            return c
    return None


class PlannerConfigError(Exception):
    """Raised when required current environment identity cannot be resolved."""


def validate_provenance(
    prov: Provenance,
    *,
    task_id: str,
    task_version: str,
    workflow_id: str,
    workflow_version: str,
    env: EnvContext,
    run_dir: Path,
    ekb_required: bool = False,
    repo_root: Path | None = None,
) -> list:
    """
    Return a list of StaleReason. Empty list => the output is still valid.
    Pure/read-only: only reads and hashes files.

    `ekb_required` is authoritative and comes from workflow/task metadata, NOT
    from the provenance record. When True, an EKB-less record is stale and an
    unresolved current EKB identity is a PlannerConfigError.
    """
    reasons: list = []

    # identity / version pins
    if prov.task_id != task_id:
        reasons.append(StaleReason("task_id_mismatch", recorded=prov.task_id or "", current=task_id))
    if prov.task_version != task_version:
        reasons.append(StaleReason("task_version_changed", artifact=task_id,
                                   recorded=prov.task_version or "", current=task_version))
    if prov.workflow_id != workflow_id:
        reasons.append(StaleReason("workflow_id_mismatch", recorded=prov.workflow_id or "",
                                   current=workflow_id))
    if prov.workflow_version != workflow_version:
        reasons.append(StaleReason("workflow_version_changed",
                                   recorded=prov.workflow_version or "", current=workflow_version))

    # inputs
    for spec in prov.inputs:
        ipath, irec = spec.get("path"), spec.get("sha256")
        if not ipath or not irec:
            reasons.append(StaleReason("input_provenance_incomplete", artifact=spec.get("name", "")))
            continue
        resolved = _resolve(ipath, run_dir, repo_root)
        if resolved is None:
            reasons.append(StaleReason("input_missing", artifact=ipath))
            continue
        try:
            cur = fp.sha256_file(resolved)
        except fp.FingerprintError as exc:
            reasons.append(StaleReason("input_unreadable", artifact=ipath, detail=str(exc)))
            continue
        if cur != irec.lower():
            reasons.append(StaleReason("input_hash_changed", artifact=ipath,
                                       recorded=irec, current=cur))

    # output
    resolved_out = _resolve(prov.output_path, run_dir, repo_root)
    if resolved_out is None:
        reasons.append(StaleReason("output_missing", artifact=prov.output_path or ""))
    else:
        try:
            cur = fp.sha256_file(resolved_out)
            if cur != (prov.output_sha256 or "").lower():
                reasons.append(StaleReason("output_hash_changed", artifact=prov.output_path,
                                           recorded=prov.output_sha256 or "", current=cur))
        except fp.FingerprintError as exc:
            reasons.append(StaleReason("output_unreadable", artifact=prov.output_path or "",
                                       detail=str(exc)))

    # ECF identity is required for every task. Missing current ECF identity is a
    # planner configuration error (not silently ignored).
    if env.ecf_version is None:
        raise PlannerConfigError(
            "current ECF version identity is unavailable (ecf-version.yaml missing "
            "or unparseable); cannot validate provenance")
    if prov.ecf_version != env.ecf_version:
        reasons.append(StaleReason("ecf_version_changed",
                                   recorded=prov.ecf_version or "", current=env.ecf_version))
    # Commit comparison is best-effort (version-only fallback when unavailable).
    if env.ecf_commit and prov.ecf_commit and prov.ecf_commit != env.ecf_commit:
        reasons.append(StaleReason("ecf_commit_changed",
                                   recorded=prov.ecf_commit, current=env.ecf_commit))

    # EKB identity: driven by authoritative `ekb_required`, NOT by the record.
    if ekb_required:
        # A record that omits EKB fields cannot bypass an EKB-required check.
        if not prov.declares_ekb:
            reasons.append(StaleReason("ekb_provenance_missing", artifact=task_id,
                                       detail="EKB identity required but not recorded"))
        if env.ekb_version is None:
            raise PlannerConfigError(
                "current EKB identity is unavailable (vendor/engineering_kb/VERSION "
                "missing or unparseable) but EKB is required for this task")
        if prov.declares_ekb and prov.ekb_version != env.ekb_version:
            reasons.append(StaleReason("ekb_version_changed",
                                       recorded=prov.ekb_version or "", current=env.ekb_version))
        if env.ekb_commit and prov.ekb_commit and prov.ekb_commit != env.ekb_commit:
            reasons.append(StaleReason("ekb_commit_changed",
                                       recorded=prov.ekb_commit, current=env.ekb_commit))

    return reasons


def load_and_validate(
    provenance_path: Path,
    *,
    task_id: str,
    task_version: str,
    workflow_id: str,
    workflow_version: str,
    env: EnvContext,
    run_dir: Path,
    ekb_required: bool = False,
    repo_root: Path | None = None,
) -> list:
    """
    Load a provenance file and validate it. Returns a list of StaleReason.

    Missing file  -> [missing_provenance]
    Unparseable   -> [malformed_provenance]
    Otherwise     -> content/version reasons (possibly empty = valid).

    May raise PlannerConfigError when required current environment identity is
    unavailable (that is a configuration failure, not staleness).
    """
    if not provenance_path.is_file():
        return [StaleReason("missing_provenance", artifact=provenance_path.name)]
    try:
        text = fp_read(provenance_path)
        prov = parse_provenance(text)
    except (ProvenanceError, OSError) as exc:
        return [StaleReason("malformed_provenance", artifact=provenance_path.name, detail=str(exc))]
    return validate_provenance(
        prov, task_id=task_id, task_version=task_version,
        workflow_id=workflow_id, workflow_version=workflow_version,
        env=env, run_dir=run_dir, ekb_required=ekb_required, repo_root=repo_root,
    )


def fp_read(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n").replace("\r", "\n")
