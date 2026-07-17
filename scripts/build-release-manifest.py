#!/usr/bin/env python3
"""Build the Context Switcher release manifest (app-only; ADR-0010).

Reads the authoritative identity sources and emits a deterministic
``release/release-manifest.json`` describing what a Context Switcher release
artifact contains:

  * project identity/version    -> package.json
  * project commit              -> `git rev-parse HEAD` (best-effort)
  * application projects         -> the .NET projects under src/
  * decision baseline            -> decisions/ADR-*.md

This tool is READ-ONLY over the repository except for the manifest file it
writes. It never invokes live tooling and never publishes. Standard library
only (no npm/pip dependencies).

Usage:
  python scripts/build-release-manifest.py            # write release/release-manifest.json
  python scripts/build-release-manifest.py --print    # print to stdout, write nothing
  python scripts/build-release-manifest.py --check     # fail if the on-disk manifest is stale
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Do NOT write .pyc bytecode into the working tree / release package.
sys.dont_write_bytecode = True

SCHEMA_VERSION = "1.0.0"
MANIFEST_KIND = "context_switcher_release_manifest"

# Application projects a release is built from (paths relative to repo root).
APP_PROJECTS = [
    "src/Work/ContextSwitcher.Work/ContextSwitcher.Work.csproj",
    "src/App/ContextSwitcher.Cli/ContextSwitcher.Cli.csproj",
]


def repo_root() -> Path:
    """scripts/ sits at the project root; its parent is that root."""
    return Path(__file__).resolve().parents[1]


def git_head(root: Path):
    """Best-effort project commit. None if git or the commit is unavailable."""
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


def project_status(root: Path):
    return [{"path": rel, "present": (root / rel).exists()} for rel in APP_PROJECTS]


def build_manifest(root: Path | None = None) -> dict:
    root = root or repo_root()
    name, version, private = read_project_identity(root)
    projects = project_status(root)

    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_kind": MANIFEST_KIND,
        # generated_at is informational only and is EXCLUDED from drift comparison.
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": {
            "name": name,
            "version": version,
            "private": private,
            "commit": git_head(root),
            "commit_policy": "best_effort",
            "platform": "Windows",
            "stack": ".NET / WinUI 3 (interim CLI harness)",
        },
        "application": {
            "projects": projects,
            "projects_present": all(p["present"] for p in projects),
        },
        "baselines": {
            "architecture_decisions": list_stems(root / "decisions", "ADR-*.md"),
        },
    }


def strip_volatile(manifest: dict) -> dict:
    """Return a copy without fields that legitimately change every build, so the
    drift check is stable.

    Excludes:
      * ``generated_at`` — a timestamp.
      * ``project.commit`` — a committed manifest cannot assert its own
        containing commit without a self-reference loop; per best_effort policy
        the commit is informational provenance, excluded from equality.
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
    manifest = build_manifest(root)
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
    print(f"  project {manifest['project']['name']} {manifest['project']['version']} "
          f"(commit {manifest['project']['commit']})")
    print(f"  application projects present: {manifest['application']['projects_present']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
