#!/usr/bin/env python3
"""
Build release/release-manifest.json for the Engineering Knowledge Base.

The manifest is a machine-readable release identity record. It records what the
release IS (name, version, commit, content digest) and its status. It does NOT
publish, tag, or commit anything.

Canonical version source: package.json `version`. VERSION and the manifest must
agree (enforced by scripts/validate-release.py).

Run: python scripts/build-release-manifest.py   (or: npm run release:manifest)
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "release" / "release-manifest.json"

SCHEMA_VERSION = "1.0.0"

# Canonical release content (mirrors the package.json `files` allowlist). The
# content digest is computed over exactly this set, so it changes only when
# canonical release content changes.
INCLUDE_DIRS = [
    "concepts", "decision_guides", "patterns", "quality_attributes", "examples",
    "standards", "foundations", "knowledge_model", "practices", "artifacts",
    "migrations", "reviews", "acceptance_tests", "coverage", "release", "scripts",
]
INCLUDE_FILES = ["README.md", "FOUNDATION.md", "VERSION", "package.json"]
INCLUDE_ENGINE = ["engine/ekb.py", "engine/test_engine.py", "engine/README.md"]

# Never hashed / never shipped.
EXCLUDE_PARTS = {"__pycache__", ".git", ".claude", "generated", "node_modules"}
EXCLUDE_SUFFIXES = {".pyc", ".tmp", ".temp", ".log", ".tgz"}
# The manifest cannot hash itself (it embeds the digest).
SELF_RELATIVE = "release/release-manifest.json"


def _excluded(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel == SELF_RELATIVE:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return any(part in EXCLUDE_PARTS for part in path.relative_to(REPO_ROOT).parts)


def canonical_files() -> list[Path]:
    files: list[Path] = []
    for name in INCLUDE_FILES + INCLUDE_ENGINE:
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
    return sorted(set(files), key=lambda p: p.relative_to(REPO_ROOT).as_posix())


def content_digest(files: list[Path]) -> tuple[str, int]:
    """sha256 over sorted (relpath, sha256(content)); returns (digest, file_count)."""
    h = hashlib.sha256()
    for p in files:
        rel = p.relative_to(REPO_ROOT).as_posix()
        fh = hashlib.sha256(p.read_bytes()).hexdigest()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(fh.encode("ascii"))
        h.update(b"\n")
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


def read_version_files() -> tuple[str, str]:
    pkg = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    version_file = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return pkg["version"], version_file


def build_manifest() -> dict:
    pkg = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    pkg_version, version_file = read_version_files()
    files = canonical_files()
    digest, count = content_digest(files)
    return {
        "schema_version": SCHEMA_VERSION,
        "package_name": pkg["name"],
        "package_version": pkg_version,
        "canonical_version_source": "package.json:version",
        "version_mirror": {"VERSION": version_file},
        "repository_url": pkg.get("repository", {}).get("url", ""),
        "git_commit": git_commit(),
        "artifact_type": "engineering_knowledge_base",
        "release_status": "draft",
        "content_digest": digest,
        "content_file_count": count,
        "tarball_digest": None,
        "compatibility": {
            "knowledge_object_schema_version": "1.0",
            "package_contract_version": "1.0",
            "relationship_model": "foundations/KNOWLEDGE_RELATIONSHIP_MODEL.md",
            "canonical_decision_guide_type": "decision_guide",
            "engine_generator_version": "0.2.0",
            "consumer_pins": ["package_version", "git_commit",
                              "knowledge_object_schema_version",
                              "package_contract_version"],
        },
        "tests_required": [
            "npm test",
            "python engine/ekb.py validate",
            "python engine/ekb.py integrity",
            "python engine/ekb.py completeness",
        ],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publish_status": "not_published",
        "git_tag": None,
    }


def main() -> int:
    manifest = build_manifest()
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print(f"  version:        {manifest['package_version']}")
    print(f"  git_commit:     {manifest['git_commit']}")
    print(f"  content_digest: {manifest['content_digest']} "
          f"({manifest['content_file_count']} files)")
    print(f"  publish_status: {manifest['publish_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
