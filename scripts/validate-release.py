#!/usr/bin/env python3
"""Validate Context Switcher release readiness (offline; app-only; ADR-0010).

Enforces the identity and packaging release gates against live repository
state and the on-disk release manifest. Complements — does NOT replace — the
acceptance suite:

  * `npm test`                 -> project acceptance tests (offline)
  * `npm run release:validate` -> THIS tool (identity + manifest + packaging)
  * `npm run release:pack`     -> `npm pack --dry-run --json` (content review)

Standard library only. Loads the manifest builder by file path so both tools
share one manifest shape. Exit 0 = all gates pass.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

# Do NOT write .pyc bytecode when importing the builder by path.
sys.dont_write_bytecode = True


def load_builder(root: Path):
    path = root / "scripts" / "build-release-manifest.py"
    spec = importlib.util.spec_from_file_location("release_manifest_builder", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Gates:
    def __init__(self):
        self.fail = 0
        self.warn = 0

    def ok(self, msg):
        print(f"PASS: {msg}")

    def bad(self, msg):
        print(f"FAIL: {msg}")
        self.fail += 1

    def wn(self, msg):
        print(f"WARN: {msg}")
        self.warn += 1

    def assert_(self, cond, ok_msg, bad_msg):
        if cond:
            self.ok(ok_msg)
        else:
            self.bad(bad_msg)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    builder = load_builder(root)
    g = Gates()

    print("== Context Switcher Release Validation ==")
    live = builder.build_manifest(root)

    # --- Gate 1: project identity (private + version present) -----------------
    pj = root / "package.json"
    pj_data = {}
    if pj.is_file():
        try:
            pj_data = json.loads(pj.read_text(encoding="utf-8"))
        except Exception as exc:
            g.bad(f"package.json is unparseable: {exc}")
    else:
        g.bad("package.json missing")
    g.assert_(pj_data.get("private") is True,
              "package is private (not for public distribution)",
              "package.json is not marked private:true")
    g.assert_(bool(pj_data.get("version")),
              f"project version present ({pj_data.get('version')})",
              "package.json version missing")

    # --- Gate 2: on-disk manifest present, parseable, and not stale -----------
    mpath = root / "release" / "release-manifest.json"
    disk = None
    if mpath.is_file():
        try:
            disk = json.loads(mpath.read_text(encoding="utf-8"))
            g.ok("release-manifest.json present and parseable")
        except Exception as exc:
            g.bad(f"release-manifest.json unparseable: {exc}")
    else:
        g.bad("release-manifest.json missing (run `npm run release:manifest`)")

    if disk is not None:
        g.assert_(builder.strip_volatile(disk) == builder.strip_volatile(live),
                  "release manifest matches live repository state (no drift)",
                  "release manifest is STALE vs live state (run `npm run release:manifest`)")
        g.assert_(disk.get("project", {}).get("version") == pj_data.get("version"),
                  "manifest and package.json versions agree",
                  f"version drift: manifest={disk.get('project', {}).get('version')} "
                  f"package.json={pj_data.get('version')}")

    # --- Gate 3: application projects present ----------------------------------
    projects = live["application"]["projects"]
    missing = [p["path"] for p in projects if not p["present"]]
    g.assert_(not missing,
              f"all {len(projects)} application projects present",
              "missing application projects: " + ", ".join(missing))

    # --- Gate 4: packaging excludes runtime/generated output ------------------
    files = pj_data.get("files", [])
    leaked = [f for f in files if f.strip("/").split("/")[0] in ("runtime", "generated")]
    g.assert_(not leaked,
              "package files allowlist excludes runtime/ and generated/",
              f"package would include runtime/generated output: {leaked}")
    gi = root / ".gitignore"
    gi_text = gi.read_text(encoding="utf-8") if gi.is_file() else ""
    for d in ("runtime/", "generated/"):
        g.assert_(d in gi_text,
                  f".gitignore ignores {d}",
                  f".gitignore does not ignore {d}")

    print()
    print(f"release-validation: {g.fail} failure(s), {g.warn} warning(s)")
    if g.fail == 0:
        print("RESULT: RELEASE GATES PASS (offline; nothing published)")
        return 0
    print("RESULT: RELEASE GATES FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
