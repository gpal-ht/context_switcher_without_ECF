#!/usr/bin/env python3
"""Build the Context Switcher release manifest.

Reads the authoritative identity sources and emits a deterministic
``release/release-manifest.json`` describing what a Context Switcher release
artifact contains and the versions it is compatible with:

  * project identity/version    -> package.json
  * bundled ECF identity        -> vendor/ecf/VERSION + vendor/ecf/ecf-version.yaml
  * nested EKB identity         -> vendor/ecf/vendor/engineering_kb/VERSION
  * project commit              -> `git rev-parse HEAD` (best-effort, per ECF policy)
  * decision / work-request baselines -> decisions/ + work_requests/
  * required bundled capabilities     -> presence check under vendor/ecf/

This tool is READ-ONLY over the repository except for the manifest file it
writes. It never touches vendor/, never invokes live Claude, and never
publishes. Standard library only (no npm/pip dependencies).

Usage:
  python scripts/build-release-manifest.py            # write release/release-manifest.json
  python scripts/build-release-manifest.py --print    # print to stdout, write nothing
  python scripts/build-release-manifest.py --check     # fail if the on-disk manifest is stale
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Loading the sibling engineering_backend module must not litter the release
# tooling directory (or the release package) with __pycache__/*.pyc.
sys.dont_write_bytecode = True

SCHEMA_VERSION = "0.2.0"
MANIFEST_KIND = "context_switcher_release_manifest"
BUNDLE_STRATEGY = "included_self_contained_bundle"
WORKFLOW = "WF-REASON-0001"


def _load_backend_module():
    """Load the sibling engineering-backend resolver (scripts/ is not a package)."""
    path = Path(__file__).resolve().parent / "engineering_backend.py"
    spec = importlib.util.spec_from_file_location("engineering_backend", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ENGINEERING_BACKEND = _load_backend_module()

# Required bundled ECF capabilities (paths relative to vendor/ecf/). The single
# Python source of this list is scripts/engineering_backend.py (ADR-0007); it
# deliberately MIRRORS the capabilities asserted by
# acceptance_tests/check_bundle_integrity.sh so the release manifest and the
# bundle-integrity gate cannot silently diverge.
REQUIRED_CAPABILITIES = ENGINEERING_BACKEND.REQUIRED_ECF_CAPABILITIES

# Consumer-side ECF wrappers that a release must ship for the offline pipeline,
# plus the backend resolvers they depend on (ADR-0007).
CONSUMER_SCRIPTS = [
    "scripts/initialize-ecf-run.ps1",
    "scripts/plan-ecf-workflow.ps1",
    "scripts/run-ecf-task.ps1",
    "scripts/bundle-ecf.ps1",
    "scripts/lib/Resolve-EngineeringBackend.ps1",
    "scripts/engineering_backend.py",
]


def repo_root() -> Path:
    """scripts/ sits at the project root; its parent is that root."""
    return Path(__file__).resolve().parents[1]


def read_kv(path: Path) -> dict:
    """Parse simple ``key: value`` metadata (VERSION, ecf-version.yaml).

    LF/CRLF-safe, ignores blank/comment lines, strips surrounding quotes, and
    keeps the first occurrence of each key. Returns {} if the file is absent.
    """
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m:
            continue
        key = m.group(1)
        val = m.group(2).strip().strip('"').strip("'")
        out.setdefault(key, val)
    return out


def git_head(root: Path):
    """Best-effort project commit (ECF commit_policy: best_effort). None if unavailable."""
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None


def read_project_identity(root: Path):
    pj = root / "package.json"
    if pj.is_file():
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
            return data.get("name"), data.get("version"), bool(data.get("private", False))
        except Exception:
            pass
    return None, None, None


def list_stems(dir_path: Path, pattern: str):
    if not dir_path.is_dir():
        return []
    return sorted(p.stem for p in dir_path.glob(pattern))


def capability_status(ecf_root: Path):
    return [{"path": rel, "present": (ecf_root / rel).exists()} for rel in REQUIRED_CAPABILITIES]


def build_manifest(root: Path | None = None) -> dict:
    root = root or repo_root()

    # Composition root (ADR-0007): resolve the configured backend once. In ecf
    # mode the bundle is validated (availability + compatibility) and the
    # backend exceptions propagate as clear failures; the manifest never
    # describes an invalid ecf configuration. In standalone mode no ECF
    # identity is read and no ECF guarantee is claimed.
    backend = ENGINEERING_BACKEND.resolve_backend(root)
    ecf_mode = backend == "ecf"
    ecf_root = root / "vendor" / "ecf"

    name, version, private = read_project_identity(root)

    if ecf_mode:
        ecf_ver = read_kv(ecf_root / "VERSION")
        ecf_canon = read_kv(ecf_root / "ecf-version.yaml")
        ekb_ver = read_kv(ecf_root / "vendor" / "engineering_kb" / "VERSION")
        caps = capability_status(ecf_root)
        acceptance_level = {
            "claimed": True,
            "single_live_task_proven": True,
            "full_workflow_proven": False,
            "statement": "single live task proven; full workflow not yet proven",
        }
        bundled_ecf = {
            "claimed": True,
            "strategy": BUNDLE_STRATEGY,
            "canonical_version": ecf_canon.get("version"),
            "canonical_schema_version": ecf_canon.get("schema_version"),
            "commit_policy": ecf_canon.get("commit_policy"),
            "bundle_version": ecf_ver.get("version"),
            "source": ecf_ver.get("source"),
            "source_commit": ecf_ver.get("source_commit"),
            "bundle_date": ecf_ver.get("bundle_date"),
            "status": ecf_ver.get("status"),
        }
        bundled_ekb = {
            "claimed": True,
            "version": ekb_ver.get("version"),
            "source": ekb_ver.get("source"),
            "source_commit": ekb_ver.get("source_commit"),
            "ecf_recorded_ekb_version": ecf_ver.get("ekb_version"),
            "ecf_recorded_ekb_source": ecf_ver.get("ekb_source"),
            "ecf_recorded_ekb_commit": ecf_ver.get("ekb_commit"),
        }
        commit_policy = ecf_canon.get("commit_policy", "best_effort")
    else:
        not_claimed = ("not claimed — standalone engineering backend "
                       "(no ECF bundled, validated, or relied upon)")
        caps = []
        acceptance_level = {"claimed": False, "statement": not_claimed}
        bundled_ecf = {"claimed": False, "statement": not_claimed}
        bundled_ekb = {"claimed": False, "statement": not_claimed}
        commit_policy = "best_effort"

    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_kind": MANIFEST_KIND,
        # generated_at is informational only and is EXCLUDED from drift comparison.
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engineering_backend": backend,
        "capabilities": [
            {"name": cap_name,
             "available": (standalone_avail if backend == "standalone" else ecf_avail)}
            for cap_name, standalone_avail, ecf_avail in ENGINEERING_BACKEND.CAPABILITIES
        ],
        "project": {
            "name": name,
            "version": version,
            "private": private,
            "commit": git_head(root),
            "commit_policy": commit_policy,
        },
        "acceptance_level": acceptance_level,
        "bundled_ecf": bundled_ecf,
        "bundled_ekb": bundled_ekb,
        "compatibility": {
            "workflow": WORKFLOW if ecf_mode else None,
            "consumer_scripts": [s for s in CONSUMER_SCRIPTS if (root / s).exists()],
            "required_capabilities": caps,
            "required_capabilities_present": (all(c["present"] for c in caps)
                                              if ecf_mode else None),
        },
        "baselines": {
            "architecture_decisions": list_stems(root / "decisions", "ADR-*.md"),
            "accepted_work_requests": list_stems(root / "work_requests", "WR-*.md"),
        },
    }


def strip_volatile(manifest: dict) -> dict:
    """Return a copy without fields that legitimately change every build, so the
    drift check is NON-RECURSIVE (Critical Release-Manifest Rule).

    Excludes:
      * ``generated_at`` — a timestamp.
      * ``project.commit`` — the project's own HEAD. A committed manifest cannot
        assert its own containing commit without a self-reference loop (generate
        at HEAD -> commit -> HEAD moves -> manifest stale -> regenerate -> ...).
        Per ``commit_policy: best_effort`` the commit is informational provenance;
        it is recorded but excluded from the drift/equality comparison. The
        authoritative release-content identity is the bundled ECF/EKB pins and
        capabilities (all retained here); the final tag->commit binding lives in
        the release notes and the platform compatibility table.
    """
    clone = copy.deepcopy(manifest)
    clone.pop("generated_at", None)
    if isinstance(clone.get("project"), dict):
        clone["project"].pop("commit", None)
    return clone


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build the Context Switcher release manifest.")
    ap.add_argument("--out", default=None,
                    help="Output path (default: release/release-manifest.json).")
    ap.add_argument("--print", dest="to_stdout", action="store_true",
                    help="Print the manifest to stdout and write nothing.")
    ap.add_argument("--check", action="store_true",
                    help="Compare a freshly built manifest to the on-disk file "
                         "(ignoring generated_at); exit 1 if they differ.")
    args = ap.parse_args(argv)

    root = repo_root()
    out = Path(args.out) if args.out else (root / "release" / "release-manifest.json")
    try:
        manifest = build_manifest(root)
    except (ENGINEERING_BACKEND.BackendConfigurationError,
            ENGINEERING_BACKEND.BackendUnavailableError,
            ENGINEERING_BACKEND.BackendIncompatibleError) as exc:
        print(f"ERROR: cannot build release manifest: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(manifest, indent=2) + "\n"

    if args.to_stdout:
        sys.stdout.write(text)
        return 0

    if args.check:
        if not out.is_file():
            print(f"DRIFT: manifest not found on disk: {out}")
            return 1
        try:
            on_disk = json.loads(out.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"DRIFT: cannot parse on-disk manifest: {exc}")
            return 1
        if strip_volatile(on_disk) == strip_volatile(manifest):
            print("OK: on-disk release manifest matches live repository state.")
            return 0
        print("DRIFT: on-disk release manifest is stale; run `npm run release:manifest`.")
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out.relative_to(root)}")
    print(f"  engineering backend: {manifest['engineering_backend']}")
    print(f"  project {manifest['project']['name']} {manifest['project']['version']} "
          f"(commit {manifest['project']['commit']})")
    if manifest["engineering_backend"] == "ecf":
        print(f"  ECF bundle {manifest['bundled_ecf']['bundle_version']} "
              f"commit {manifest['bundled_ecf']['source_commit']}")
        print(f"  EKB {manifest['bundled_ekb']['version']} "
              f"commit {manifest['bundled_ekb']['source_commit']}")
    else:
        print("  ECF/EKB identity: not claimed (standalone backend)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
