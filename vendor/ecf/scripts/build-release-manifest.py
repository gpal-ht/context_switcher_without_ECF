#!/usr/bin/env python3
"""Build release/release-manifest.json for the Engineering Control Framework.

Machine-readable release identity for the ECF **Control Plane**. Records what the
release IS (name, version, content digest) and the exact upstream Knowledge-Plane
dependency it pins (bundled EKB version + released commit + ontology). It does NOT
publish, tag, commit, or push.

Non-recursive identity (Critical Release-Manifest Rule): release-content identity
is `content_digest`, a sha256 over canonical content EXCLUDING the manifest
itself. `git_commit` is the best-effort SOURCE commit (a committed ancestor of
HEAD), never a claim to equal its own containing commit. The final tag->commit
binding lives in release notes / the platform compatibility table.

Canonical release (package) version source: package.json `version` (mirrored in
VERSION). This is independent of the ECF *framework* version in ecf-version.yaml,
which is recorded separately as provenance.

Run: python scripts/build-release-manifest.py   (or: npm run release:manifest)
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "release" / "release-manifest.json"
SCHEMA_VERSION = "1.0.0"

INCLUDE_DIRS = [
    "workflows", "tasks", "tools", "runtime_schemas", "scripts", "standards",
    "roles", "knowledge", "transformations", "review_packs", "decisions",
    "work_requests", "examples", "research", "execution", "vendor", "release",
]
INCLUDE_FILES = [
    "README.md", "FOUNDATION.md", "FRAMEWORK_ARCHITECTURE.md", "ECF_ROADMAP.md",
    "ecf-version.yaml", "VERSION", "package.json", ".gitattributes",
]
EXCLUDE_PARTS = {"__pycache__", ".git", ".claude", "generated", "runtime",
                 "node_modules", ".pytest_cache", ".mypy_cache", ".vs", ".vscode"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".pyd", ".tmp", ".temp", ".log", ".tgz"}
SELF_RELATIVE = "release/release-manifest.json"

# Consumer entrypoints a release must ship for the offline control-plane pipeline.
CONSUMER_ENTRYPOINTS = [
    "scripts/initialize-run.ps1",
    "scripts/plan-workflow.ps1",
    "scripts/run-one-task.ps1",
    "scripts/validate-workflows.ps1",
    "tools/workflow_validator/validate_workflow.py",
    "tools/workflow_planner/plan_workflow.py",
    "tools/run_initializer",
    "tools/runtime_state",
    "tools/task_runner/run_task.py",
    "tools/task_runner/executors/claude_code.py",
    "tools/artifact_fingerprint",
    "runtime_schemas/RUN_STATE_SCHEMA.md",
]


def read_kv(path: Path) -> dict:
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
        out.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
    return out


def _excluded(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel == SELF_RELATIVE:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return any(part in EXCLUDE_PARTS for part in path.relative_to(REPO_ROOT).parts)


def _git_ignored(paths: list[Path]) -> set[str]:
    """Posix relpaths that git ignores. npm pack respects .gitignore, so the
    digest must too — otherwise a gitignored scratch file (e.g. scripts/*.txt)
    would be hashed but never shipped, and the digest could not be reproduced
    from a clean checkout."""
    git = shutil.which("git")
    if git is None or not paths:
        return set()
    rels = [p.relative_to(REPO_ROOT).as_posix() for p in paths]
    proc = subprocess.run([git, "check-ignore", "--stdin"], cwd=REPO_ROOT,
                          input="\n".join(rels), capture_output=True, text=True)
    return {ln.strip() for ln in proc.stdout.splitlines() if ln.strip()}


def canonical_files() -> list[Path]:
    files: list[Path] = []
    for name in INCLUDE_FILES:
        p = REPO_ROOT / name
        if p.is_file() and not _excluded(p):
            files.append(p)
    for d in INCLUDE_DIRS:
        base = REPO_ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and not _excluded(p):
                files.append(p)
    ignored = _git_ignored(files)
    files = [p for p in files if p.relative_to(REPO_ROOT).as_posix() not in ignored]
    return sorted(set(files), key=lambda p: p.relative_to(REPO_ROOT).as_posix())


def content_digest(files: list[Path]) -> tuple[str, int]:
    h = hashlib.sha256()
    for p in files:
        rel = p.relative_to(REPO_ROOT).as_posix()
        fh = hashlib.sha256(p.read_bytes()).hexdigest()
        h.update(rel.encode("utf-8")); h.update(b"\0")
        h.update(fh.encode("ascii")); h.update(b"\n")
    return "sha256:" + h.hexdigest(), len(files)


def git_commit() -> str:
    git = shutil.which("git")
    if git is None:
        return "unknown"
    try:
        out = subprocess.run([git, "rev-parse", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return "unknown"


def bundled_ekb() -> dict:
    ekb_root = REPO_ROOT / "vendor" / "engineering_kb"
    ver = read_kv(ekb_root / "VERSION")
    ontology = None
    contract = None
    ekb_manifest = ekb_root / "release" / "release-manifest.json"
    manifest_pkg_version = None
    if ekb_manifest.is_file():
        try:
            m = json.loads(ekb_manifest.read_text(encoding="utf-8"))
            manifest_pkg_version = m.get("package_version")
            comp = m.get("compatibility", {})
            ontology = comp.get("canonical_decision_guide_type")
            contract = comp.get("package_contract_version")
        except Exception:
            pass
    if ontology is None and (ekb_root / "decision_guides").is_dir():
        ontology = "decision_guide"  # structural fallback
    return {
        "package_name": "@gpal-ht/engineering-kb",
        "bundle_version": ver.get("version"),
        "manifest_package_version": manifest_pkg_version,
        "source_commit": ver.get("source_commit"),
        "source_tag": ver.get("source_tag") or None,
        "source": ver.get("source"),
        "status": ver.get("status"),
        "ontology": ontology,
        "package_contract_version": contract,
    }


def build_manifest() -> dict:
    pkg = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    version_file = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip() \
        if (REPO_ROOT / "VERSION").is_file() else None
    framework = read_kv(REPO_ROOT / "ecf-version.yaml")
    files = canonical_files()
    digest, count = content_digest(files)
    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_kind": "ecf_release_manifest",
        "package_name": pkg["name"],
        "package_version": pkg["version"],
        "canonical_version_source": "package.json:version",
        "version_mirror": {"VERSION": version_file},
        "repository_url": pkg.get("repository", {}).get("url", ""),
        "git_commit": git_commit(),
        "artifact_type": "engineering_control_framework",
        "release_status": "released",
        "content_digest": digest,
        "content_file_count": count,
        "tarball_digest": None,
        "framework": {
            "version": framework.get("version"),
            "schema_version": framework.get("schema_version"),
            "commit_policy": framework.get("commit_policy"),
        },
        "bundled_ekb": bundled_ekb(),
        "compatibility": {
            "workflow": "WF-REASON-0001",
            "workflow_version": "0.2.0",
            "changed_task_versions": {
                "TASK-TRACE-0002": "0.2.0",
                "TASK-TRACE-0003": "0.2.0",
            },
            "consumer_entrypoints": [e for e in CONSUMER_ENTRYPOINTS
                                     if (REPO_ROOT / e).exists()],
            "live_task_adapters": ["TASK-CLASSIFY-0001"],
        },
        "tests_required": [
            "npm test",
            "python scripts/validate-workflows.ps1 (WF-REASON-0001: 21 rules)",
        ],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publish_status": "not_published",
        "git_tag": None,
    }


def main() -> int:
    manifest = build_manifest()
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    ekb = manifest["bundled_ekb"]
    print(f"Wrote {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print(f"  package:        {manifest['package_name']} {manifest['package_version']}")
    print(f"  git_commit:     {manifest['git_commit']}")
    print(f"  content_digest: {manifest['content_digest']} ({manifest['content_file_count']} files)")
    print(f"  bundled EKB:    {ekb['bundle_version']} @ {ekb['source_commit']} "
          f"(tag {ekb['source_tag']}, ontology {ekb['ontology']})")
    print(f"  publish_status: {manifest['publish_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
