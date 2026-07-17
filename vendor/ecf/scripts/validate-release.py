#!/usr/bin/env python3
"""Validate the Engineering Control Framework release (offline; no publish).

Mechanical release gates for the ECF Control Plane. Complements — does not
replace — `npm test` (the 226-test control-plane suite) and the workflow
validator. Exits non-zero on any failure. Publishes/tags/commits nothing.

Gates:
 1  package.json valid, private, semver version
 2  package.json / VERSION / manifest package_version agree
 3  manifest present, complete, publish_status == not_published, git_tag null
 4  git_commit is a committed ancestor of HEAD (non-recursive source-commit model)
 4b content_digest recomputes exactly (release-content identity)
 5  bundled EKB pin: version 0.2.0, 40-hex commit, ontology decision_guide,
    bundle/manifest EKB versions agree
 6  consumer entrypoints present
 7  npm pack --dry-run contains no forbidden files (bytecode/.claude/runtime/…)
 8  no runtime run is packaged
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG = REPO_ROOT / "package.json"
VERSION_FILE = REPO_ROOT / "VERSION"
MANIFEST = REPO_ROOT / "release" / "release-manifest.json"

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
                    r"(?:-[0-9A-Za-z-.]+)?(?:\+[0-9A-Za-z-.]+)?$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_PACK = ("__pycache__", ".git/", ".claude", "generated/", "runtime/",
                  "node_modules/", ".pytest_cache")
FORBIDDEN_SUFFIX = (".pyc", ".pyo", ".pyd", ".tmp", ".temp", ".log", ".tgz")

failures: list[str] = []


def fail(check: str, detail: str): failures.append(f"{check}: {detail}")
def ok(check: str): print(f"  PASS  {check}")


def run(cmd: list[str]):
    exe = shutil.which(cmd[0])
    if exe is None:
        return subprocess.CompletedProcess(cmd, 127, "", f"not found: {cmd[0]}")
    try:
        return subprocess.run([exe, *cmd[1:]], cwd=REPO_ROOT,
                              capture_output=True, text=True)
    except OSError as e:  # noqa
        return subprocess.CompletedProcess(cmd, 127, "", str(e))


def load_builder():
    path = REPO_ROOT / "scripts" / "build-release-manifest.py"
    spec = importlib.util.spec_from_file_location("_ecf_manifest_builder", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gate_1_2(pkg: dict, man: dict):
    for field in ("name", "version", "files", "scripts", "private"):
        if field not in pkg:
            fail("1 package.json", f"missing '{field}'")
    ver = pkg.get("version", "")
    if SEMVER.match(ver):
        ok(f"1 valid semver version ({ver})")
    else:
        fail("1 semver", f"'{ver}' invalid")
    if pkg.get("private") is True and "publishConfig" not in pkg:
        ok("1 package private, no publishConfig")
    else:
        fail("1 publish-safety", "must be private:true with no publishConfig")

    vfile = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else None
    mver = man.get("package_version")
    if vfile == ver == mver and ver:
        ok("2 package.json == VERSION == manifest version")
    else:
        fail("2 version agreement",
             f"package.json={ver!r} VERSION={vfile!r} manifest={mver!r}")


def gate_3_4(man: dict):
    required = ["schema_version", "package_name", "package_version", "git_commit",
                "artifact_type", "content_digest", "framework", "bundled_ekb",
                "compatibility", "publish_status"]
    miss = [k for k in required if k not in man or man[k] in (None, "")]
    if miss:
        fail("3 manifest complete", f"missing/empty: {miss}")
    else:
        ok("3 release manifest complete")
    if man.get("publish_status") != "not_published":
        fail("3 publish_status", f"expected not_published, got {man.get('publish_status')}")
    else:
        ok("3 publish_status == not_published")
    if man.get("git_tag") not in (None, ""):
        fail("3 git_tag", f"committed manifest must not claim a tag: {man.get('git_tag')}")
    else:
        ok("3 git_tag is null (non-recursive)")

    gc = man.get("git_commit", "")
    if not SHA40.match(gc or ""):
        fail("4 git commit", f"not a 40-hex commit: {gc!r}")
    else:
        exists = run(["git", "cat-file", "-e", f"{gc}^{{commit}}"]).returncode == 0
        ancestor = run(["git", "merge-base", "--is-ancestor", gc, "HEAD"]).returncode == 0
        if exists and ancestor:
            ok("4 git commit is a committed ancestor (non-recursive)")
        else:
            fail("4 git commit", f"{gc} not a committed ancestor (exists={exists} anc={ancestor})")

    try:
        b = load_builder()
        recomputed, _ = b.content_digest(b.canonical_files())
        if recomputed == man.get("content_digest"):
            ok("4b content_digest matches canonical content")
        else:
            fail("4b content_digest",
                 f"manifest={man.get('content_digest')} recomputed={recomputed}")
    except Exception as e:  # noqa
        fail("4b content_digest", f"recompute failed: {e}")


def gate_5(man: dict):
    ekb = man.get("bundled_ekb", {})
    if ekb.get("bundle_version") == "0.2.0":
        ok("5 bundled EKB version == 0.2.0")
    else:
        fail("5 EKB version", f"expected 0.2.0, got {ekb.get('bundle_version')}")
    if SHA40.match(ekb.get("source_commit") or ""):
        ok(f"5 bundled EKB source_commit is 40-hex ({ekb.get('source_commit')})")
    else:
        fail("5 EKB commit", f"invalid: {ekb.get('source_commit')}")
    if ekb.get("ontology") == "decision_guide":
        ok("5 bundled EKB ontology == decision_guide")
    else:
        fail("5 EKB ontology", f"expected decision_guide, got {ekb.get('ontology')}")
    mpv = ekb.get("manifest_package_version")
    if mpv is None or mpv == ekb.get("bundle_version"):
        ok("5 bundled EKB bundle/manifest versions agree")
    else:
        fail("5 EKB version drift",
             f"bundle={ekb.get('bundle_version')} manifest={mpv}")


def gate_6(man: dict):
    entry = man.get("compatibility", {}).get("consumer_entrypoints", [])
    builder = load_builder()
    missing = [e for e in builder.CONSUMER_ENTRYPOINTS if not (REPO_ROOT / e).exists()]
    if missing:
        fail("6 entrypoints", f"missing: {missing}")
    else:
        ok(f"6 all {len(builder.CONSUMER_ENTRYPOINTS)} consumer entrypoints present")


def gate_7_8(pkg: dict):
    res = run(["npm", "pack", "--dry-run", "--json"])
    if res.returncode != 0:
        fail("7 npm pack", f"failed: {res.stderr.strip()[:200]}")
        return
    try:
        paths = [e["path"] for e in json.loads(res.stdout)[0]["files"]]
    except Exception as e:  # noqa
        fail("7 npm pack", f"unparseable json: {e}")
        return
    forbidden = [p for p in paths if any(t in p for t in FORBIDDEN_PACK)
                 or p.endswith(FORBIDDEN_SUFFIX)]
    if forbidden:
        fail("7 forbidden files", f"{forbidden[:10]}")
    else:
        ok(f"7 no forbidden files in pack ({len(paths)} files)")
    runtime_leak = [p for p in paths
                    if re.search(r"(^|/)(runtime|generated)/", p)]
    if runtime_leak:
        fail("8 runtime packaged", f"{runtime_leak[:10]}")
    else:
        ok("8 no runtime run packaged")


def main() -> int:
    print("ECF release validation\n")
    if not PKG.is_file():
        fail("1 package.json", "missing")
    if not MANIFEST.is_file():
        fail("3 manifest", "release-manifest.json missing (run release:manifest)")
    if failures:
        for f_ in failures:
            print(f"  FAIL  {f_}")
        print(f"\nrelease:validate FAILED — {len(failures)} check(s)")
        return 1
    pkg = json.loads(PKG.read_text(encoding="utf-8"))
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    gate_1_2(pkg, man)
    gate_3_4(man)
    gate_5(man)
    gate_6(man)
    gate_7_8(pkg)
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
