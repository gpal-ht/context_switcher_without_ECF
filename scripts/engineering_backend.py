#!/usr/bin/env python3
"""Engineering-backend resolver — the canonical composition-root helper.

Context Switcher supports two engineering backends (ADR-0007):

  * ``standalone`` — Context Switcher's native behavior only. No ECF
    repository, bundle, artifact, or environment is required or consulted.
  * ``ecf``        — ECF-integrated mode via the bundled ``vendor/ecf`` tree.
    Selecting it validates availability AND compatibility; a missing or
    incompatible bundle is a hard configuration failure (exit 3/4), never a
    silent fallback to standalone.

Resolution order (first match wins):
  1. ``CONTEXT_SWITCHER_ENGINEERING_BACKEND`` environment variable
  2. ``config/engineering-backend.yaml`` (``engineering_backend:`` key)
  3. default: ``standalone``

The backend registry is a FIXED allowlist (standalone | ecf). No module
paths, no dynamic loading: configuration selects a name, never code.

This module is the single Python source of truth for:
  * the allowed backend names,
  * the supported ECF schema-version line,
  * the required bundled-capability list (imported by the release-manifest
    builder; mirrored deliberately by ``check_bundle_integrity.sh``).

CLI (used by tests and shell composition roots):
  python scripts/engineering_backend.py --print            # resolved mode
  python scripts/engineering_backend.py --require ecf      # exit != 0 unless valid ecf
  python scripts/engineering_backend.py --describe         # mode + capability report

Exit codes: 0 ok; 2 invalid configuration value; 3 ecf requested but
unavailable; 4 ecf requested but incompatible; 5 --require mismatch.
Standard library only.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ENV_VAR = "CONTEXT_SWITCHER_ENGINEERING_BACKEND"
CONFIG_RELPATH = Path("config") / "engineering-backend.yaml"
CONFIG_KEY = "engineering_backend"
ALLOWED_BACKENDS = ("standalone", "ecf")
DEFAULT_BACKEND = "standalone"

# Compatibility policy (release/COMPATIBILITY.md): the bundled ECF must declare
# a schema_version on this line. Bump deliberately, with adapter contract tests.
SUPPORTED_ECF_SCHEMA_LINE = "0.1"

SHA40 = re.compile(r"^[0-9a-f]{40}$")

# Required bundled ECF capabilities (relative to vendor/ecf/). Single Python
# source; build-release-manifest.py imports this list. check_bundle_integrity.sh
# keeps a deliberate bash mirror exercised in ecf mode.
REQUIRED_ECF_CAPABILITIES = [
    "workflows/reasoning/WF-REASON-0001-engineering-recommendation.md",
    "tasks/decision_support/TASK-DECIDE-0002-generate-engineering-recommendation.md",
    "tasks/production/TASK-PRODUCE-0001-generate-engineering-recommendation-report.md",
    "tools/workflow_validator/validate_workflow.py",
    "tools/workflow_planner/plan_workflow.py",
    "tools/runtime_state",
    "tools/task_runner/run_task.py",
    "tools/task_runner/executors/claude_code.py",
    "tools/artifact_fingerprint",
    "runtime_schemas/RUN_STATE_SCHEMA.md",
]

# Capability matrix: capability -> (available standalone?, available ecf?).
# Truthful by construction; consumed by --describe and the release manifest.
CAPABILITIES = [
    ("governance_acceptance_checks", True, True),
    ("release_manifest_and_validation", True, True),
    ("npm_packaging", True, True),
    ("ecf_workflow_execution", False, True),
    ("ecf_bundle_integrity_gates", False, True),
    ("ecf_provenance_claims", False, True),
    ("ecf_bundle_refresh", False, True),
]


class BackendConfigurationError(Exception):
    """Invalid backend value (unknown name). Exit code 2."""


class BackendUnavailableError(Exception):
    """ecf requested but the bundle is absent. Exit code 3."""


class BackendIncompatibleError(Exception):
    """ecf requested but the bundle fails the compatibility policy. Exit code 4."""


def repo_root() -> Path:
    """scripts/ sits at the project root; its parent is that root."""
    return Path(__file__).resolve().parents[1]


def _read_config_value(root: Path) -> tuple[str | None, str]:
    """Return (value, source_description) from env or the config file."""
    env = os.environ.get(ENV_VAR)
    if env is not None and env.strip():
        return env.strip(), f"environment variable {ENV_VAR}"
    cfg = root / CONFIG_RELPATH
    if cfg.is_file():
        for raw in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(rf"^{CONFIG_KEY}:\s*(.*)$", line)
            if m:
                return m.group(1).strip().strip('"').strip("'"), str(CONFIG_RELPATH)
    return None, "default (no configuration set)"


def _read_kv(path: Path) -> dict:
    """LF/CRLF-safe ``key: value`` parser (VERSION / ecf-version.yaml)."""
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            out.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
    return out


def validate_ecf_bundle(root: Path) -> None:
    """Raise Unavailable/Incompatible unless vendor/ecf satisfies the policy."""
    ecf_root = root / "vendor" / "ecf"
    if not ecf_root.is_dir():
        raise BackendUnavailableError(
            "engineering_backend=ecf was requested but vendor/ecf is missing.\n"
            "  Install it by refreshing the bundle from an ECF checkout:\n"
            "    powershell -File scripts/bundle-ecf.ps1 -Source <path-to-ecf-repo>\n"
            "  or select the standalone backend "
            f"({ENV_VAR}=standalone or {CONFIG_RELPATH})."
        )
    canon = _read_kv(ecf_root / "ecf-version.yaml")
    schema = canon.get("schema_version", "")
    if not schema:
        raise BackendIncompatibleError(
            "engineering_backend=ecf: vendor/ecf/ecf-version.yaml is missing or "
            "declares no schema_version — cannot verify compatibility. "
            "Refresh the bundle (scripts/bundle-ecf.ps1)."
        )
    if not (schema == SUPPORTED_ECF_SCHEMA_LINE
            or schema.startswith(SUPPORTED_ECF_SCHEMA_LINE + ".")):
        raise BackendIncompatibleError(
            f"engineering_backend=ecf: bundled ECF schema_version {schema!r} is not "
            f"on the supported line {SUPPORTED_ECF_SCHEMA_LINE!r} "
            "(release/COMPATIBILITY.md). Update the adapter compatibility policy "
            "deliberately or bundle a compatible ECF."
        )
    version = _read_kv(ecf_root / "VERSION")
    commit = version.get("source_commit", "")
    if not SHA40.match(commit):
        raise BackendIncompatibleError(
            "engineering_backend=ecf: vendor/ecf/VERSION has no valid 40-hex "
            f"source_commit (got {commit!r}) — bundle identity is unverifiable. "
            "Refresh the bundle (scripts/bundle-ecf.ps1)."
        )
    missing = [c for c in REQUIRED_ECF_CAPABILITIES if not (ecf_root / c).exists()]
    if missing:
        raise BackendIncompatibleError(
            "engineering_backend=ecf: bundled ECF is missing required "
            "capabilities:\n  " + "\n  ".join(missing)
            + "\nRefresh the bundle (scripts/bundle-ecf.ps1)."
        )


def resolve_backend(root: Path | None = None, validate: bool = True) -> str:
    """Resolve the configured backend; optionally validate ecf availability."""
    root = root or repo_root()
    value, source = _read_config_value(root)
    if value is None:
        return DEFAULT_BACKEND
    if value not in ALLOWED_BACKENDS:
        raise BackendConfigurationError(
            f"invalid engineering_backend {value!r} (from {source}); "
            f"allowed values: {', '.join(ALLOWED_BACKENDS)}"
        )
    if value == "ecf" and validate:
        validate_ecf_bundle(root)
    return value


def describe(root: Path | None = None) -> str:
    root = root or repo_root()
    mode = resolve_backend(root)
    lines = [f"engineering_backend: {mode}"]
    lines.append("capabilities:")
    for name, sa, ecf in CAPABILITIES:
        avail = sa if mode == "standalone" else ecf
        lines.append(f"  {name}: {'available' if avail else 'unavailable'}")
    if mode == "standalone":
        lines.append(
            "note: ECF workflow execution, bundle gates, and provenance claims "
            "are unavailable in standalone mode; no ECF guarantees are claimed."
        )
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Resolve the engineering backend.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--print", dest="do_print", action="store_true",
                   help="Print the resolved backend name.")
    g.add_argument("--require", metavar="BACKEND", choices=ALLOWED_BACKENDS,
                   help="Exit non-zero unless the resolved backend equals BACKEND "
                        "(ecf additionally validated).")
    g.add_argument("--describe", action="store_true",
                   help="Print the resolved backend and its capability report.")
    ap.add_argument("--root", default=None,
                    help="Repository root to resolve against "
                         "(default: this script's parent repo; used by tests).")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve() if args.root else repo_root()
    try:
        if args.do_print:
            print(resolve_backend(root))
            return 0
        if args.describe:
            print(describe(root))
            return 0
        mode = resolve_backend(root)
        if mode != args.require:
            print(f"ERROR: engineering_backend is {mode!r}, "
                  f"but {args.require!r} is required for this operation.",
                  file=sys.stderr)
            return 5
        return 0
    except BackendConfigurationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except BackendUnavailableError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    except BackendIncompatibleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
