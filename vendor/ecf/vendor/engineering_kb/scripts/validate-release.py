#!/usr/bin/env python3
"""
Validate the Engineering Knowledge Base release foundation.

Mechanical, non-publishing checks. Exits non-zero on any failure. Does NOT
publish, tag, commit, or push. Run: python scripts/validate-release.py
(or: npm run release:validate)

Checks:
 1. valid package.json
 2. valid semantic version
 3. package.json / VERSION / manifest version agreement
 4. clean package `files` allowlist
 5. no forbidden files in `npm pack --dry-run`
 6. required canonical directories included in the pack
 7. release manifest complete
 8. git commit recorded correctly
 9. all EKB tests pass
10. validate / integrity / completeness pass
11. deterministic reports remain deterministic
12. no publication configuration enables accidental publishing
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Do NOT write .pyc bytecode: this tool loads the manifest builder by path
# (check 8b) and must not leave scripts/__pycache__ behind in the working tree.
sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG = REPO_ROOT / "package.json"
VERSION_FILE = REPO_ROOT / "VERSION"
MANIFEST = REPO_ROOT / "release" / "release-manifest.json"

SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-.]+)?(?:\+[0-9A-Za-z-.]+)?$")

FORBIDDEN_PACK = ("__pycache__", ".git/", ".claude", "generated/", "node_modules/")
FORBIDDEN_SUFFIX = (".pyc", ".tmp", ".temp", ".log", ".tgz")
REQUIRED_DIRS = ("engine/", "knowledge_model/", "standards/", "decision_guides/",
                 "concepts/", "migrations/", "release/")

failures: list[str] = []
notes: list[str] = []


def fail(check: str, detail: str):
    failures.append(f"{check}: {detail}")


def ok(check: str):
    print(f"  PASS  {check}")


def run(cmd: list[str], **kw):
    """Run a command, resolving the executable (npm is npm.cmd on Windows).
    Returns a CompletedProcess-like object even if the executable is missing."""
    exe = shutil.which(cmd[0])
    if exe is None:
        return subprocess.CompletedProcess(cmd, 127, "", f"executable not found: {cmd[0]}")
    try:
        return subprocess.run([exe, *cmd[1:]], cwd=REPO_ROOT,
                              capture_output=True, text=True, **kw)
    except OSError as e:  # noqa
        return subprocess.CompletedProcess(cmd, 127, "", str(e))


def load_pkg() -> dict | None:
    try:
        return json.loads(PKG.read_text(encoding="utf-8"))
    except Exception as e:  # noqa
        fail("1 package.json", f"unreadable/invalid JSON: {e}")
        return None


def check_1_2_3_4_12(pkg: dict):
    # 1 valid package.json
    for field in ("name", "version", "files", "scripts"):
        if field not in pkg:
            fail("1 package.json", f"missing '{field}'")
    if not failures:
        ok("1 valid package.json")

    # 2 valid semver
    ver = pkg.get("version", "")
    if SEMVER.match(ver):
        ok("2 valid semantic version")
    else:
        fail("2 semver", f"'{ver}' is not valid semver")

    # 3 version agreement
    vfile = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else None
    man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else None
    mver = man.get("package_version") if man else None
    if vfile == ver == mver and ver:
        ok("3 package.json == VERSION == manifest version")
    else:
        fail("3 version agreement",
             f"package.json={ver!r} VERSION={vfile!r} manifest={mver!r}")

    # 4 clean allowlist
    files = pkg.get("files", [])
    bad = [f for f in files if f.startswith("/") or ".." in f]
    if isinstance(files, list) and files and not bad:
        ok("4 clean package allowlist")
    else:
        fail("4 allowlist", f"empty or unsafe entries: {bad or files}")

    # 12 no accidental publish
    if pkg.get("private") is True and "publishConfig" not in pkg:
        ok("12 no publication configuration enables accidental publishing")
    else:
        fail("12 publish-safety",
             "package must be private:true with no publishConfig")


def check_5_6_pack():
    res = run(["npm", "pack", "--dry-run", "--json"])
    if res.returncode != 0:
        fail("5/6 npm pack", f"npm pack failed: {res.stderr.strip()[:200]}")
        return
    try:
        data = json.loads(res.stdout)
        entries = data[0]["files"]
        paths = [e["path"] for e in entries]
    except Exception as e:  # noqa
        fail("5/6 npm pack", f"could not parse npm pack json: {e}")
        return
    forbidden = [p for p in paths
                 if any(tok in p for tok in FORBIDDEN_PACK)
                 or p.endswith(FORBIDDEN_SUFFIX)]
    if forbidden:
        fail("5 forbidden files", f"{forbidden[:10]}")
    else:
        ok(f"5 no forbidden files in pack ({len(paths)} files)")
    missing = [d for d in REQUIRED_DIRS
               if not any(p.startswith(d) or p.startswith("package/" + d)
                          for p in paths)]
    if missing:
        fail("6 required dirs", f"missing from pack: {missing}")
    else:
        ok("6 required canonical directories included")


def check_7_8_manifest():
    if not MANIFEST.exists():
        fail("7 manifest", "release-manifest.json missing (run release:manifest)")
        return
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    required_keys = ["schema_version", "package_name", "package_version",
                     "canonical_version_source", "repository_url", "git_commit",
                     "artifact_type", "release_status", "content_digest",
                     "compatibility", "tests_required", "generated_at",
                     "publish_status"]
    miss = [k for k in required_keys if k not in man or man[k] in (None, "")
            and k not in ("tarball_digest", "git_tag")]
    if miss:
        fail("7 manifest complete", f"missing/empty: {miss}")
    else:
        ok("7 release manifest complete")

    if man.get("publish_status") != "not_published":
        fail("7 publish_status", f"expected not_published, got {man.get('publish_status')}")

    # 8 git commit — NON-RECURSIVE source-commit model (Model C).
    # A committed manifest cannot assert its own containing commit without a
    # self-reference loop (generate -> commit -> HEAD moves -> manifest stale).
    # So git_commit records the best-effort SOURCE commit the manifest content
    # was generated from (its base in history). We verify it is a real, committed
    # ancestor of HEAD (or HEAD itself) — never that it equals HEAD. Release
    # content identity is verified by content_digest (check 8b); the final
    # tag->commit binding is recorded in release/RELEASE_NOTES_0.2.0.md.
    gc = man.get("git_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", gc or ""):
        fail("8 git commit", f"git_commit is not a 40-hex commit: {gc!r}")
    else:
        exists = run(["git", "cat-file", "-e", f"{gc}^{{commit}}"]).returncode == 0
        ancestor = run(["git", "merge-base", "--is-ancestor", gc, "HEAD"]).returncode == 0
        if exists and ancestor:
            ok("8 git commit is a committed ancestor (non-recursive source-commit model)")
        else:
            fail("8 git commit",
                 f"git_commit {gc} is not a committed ancestor of HEAD "
                 f"(exists={exists} ancestor={ancestor})")

    # 8b content digest — the real, non-recursive release-content identity.
    # Recompute the digest over canonical content (the manifest itself excluded,
    # per build-release-manifest.py) and require it to equal the recorded value.
    try:
        import importlib.util
        bpath = REPO_ROOT / "scripts" / "build-release-manifest.py"
        spec = importlib.util.spec_from_file_location("_ekb_manifest_builder", bpath)
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        recomputed, _count = builder.content_digest(builder.canonical_files())
        if recomputed == man.get("content_digest"):
            ok("8b content_digest matches canonical content")
        else:
            fail("8b content_digest",
                 f"manifest={man.get('content_digest')} recomputed={recomputed} "
                 f"(regenerate the manifest)")
    except Exception as e:  # noqa
        fail("8b content_digest", f"could not recompute digest: {e}")


def check_9_10_tests():
    for label, cmd in [
        ("9 EKB test suite", ["python", "engine/test_engine.py"]),
        ("10 validate", ["python", "engine/ekb.py", "validate"]),
        ("10 integrity", ["python", "engine/ekb.py", "integrity"]),
        ("10 completeness", ["python", "engine/ekb.py", "completeness"]),
    ]:
        res = run(cmd)
        if res.returncode == 0:
            ok(label)
        else:
            fail(label, res.stdout.strip().splitlines()[-1] if res.stdout else "failed")


def check_11_determinism():
    for label, cmd in [("coverage", ["python", "engine/ekb.py", "coverage"]),
                       ("centrality", ["python", "engine/ekb.py", "centrality"])]:
        dest = REPO_ROOT / "coverage" / (
            "knowledge_coverage.md" if label == "coverage" else "centrality_report.md")
        run(cmd)
        first = dest.read_text(encoding="utf-8")
        run(cmd)
        second = dest.read_text(encoding="utf-8")
        if first == second:
            ok(f"11 {label} report deterministic")
        else:
            fail(f"11 {label} determinism", "output differs across runs")


def main() -> int:
    print("EKB release validation\n")
    pkg = load_pkg()
    if pkg is not None:
        check_1_2_3_4_12(pkg)
    check_7_8_manifest()
    check_5_6_pack()
    check_9_10_tests()
    check_11_determinism()
    print()
    if failures:
        for f_ in failures:
            print(f"  FAIL  {f_}")
        print(f"\nrelease:validate FAILED — {len(failures)} check(s) failed")
        return 1
    print("release:validate OK — all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
