#!/usr/bin/env python3
"""Validate Context Switcher release readiness (offline; no publish, no live Claude).

Enforces the identity/compatibility/packaging release gates against live
repository state and the on-disk release manifest. Complements — does NOT
replace — the acceptance suite:

  * `npm test`                    -> project acceptance tests (offline)
  * `npm run test:bundle:selftest`-> bundle-integrity parser/validator self-test
  * `npm run test:consumer`       -> offline consumer integration
  * `npm run release:validate`    -> THIS tool (identity + manifest + packaging)
  * `npm run release:pack`        -> `npm pack --dry-run --json` (content review)

Standard library only. Reads the manifest builder by file path so both tools
share one capability list and one manifest shape. Exit 0 = all gates pass.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

# Do NOT write .pyc bytecode. This tool loads the manifest builder by path (below);
# without this guard, importing it would create scripts/__pycache__/*.pyc — a dev
# artifact that is neither wanted in the working tree nor in the release package.
sys.dont_write_bytecode = True

SHA40 = re.compile(r"^[0-9a-f]{40}$")
# Windows drive path (C:\ or C:/), git-bash mount (/c/...), or any backslash.
MACHINE_PATH = re.compile(r"^[A-Za-z]:[\\/]|^/[A-Za-z]/|\\")


def is_sha40(v) -> bool:
    return bool(v) and bool(SHA40.match(v))


def has_machine_path(v) -> bool:
    return bool(v) and bool(MACHINE_PATH.search(v))


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

    def skip(self, msg):
        print(f"SKIP: {msg}")

    def assert_(self, cond, ok_msg, bad_msg):
        if cond:
            self.ok(ok_msg)
        else:
            self.bad(bad_msg)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    builder = load_builder(root)
    eb = builder.ENGINEERING_BACKEND
    g = Gates()

    print("== Context Switcher Release Validation ==")
    # Composition root (ADR-0007): an invalid backend configuration is itself
    # a release-gate failure — reported clearly, never silently downgraded.
    try:
        live = builder.build_manifest(root)
    except (eb.BackendConfigurationError,
            eb.BackendUnavailableError,
            eb.BackendIncompatibleError) as exc:
        g.bad(f"engineering backend configuration invalid: {exc}")
        print()
        print(f"release-validation: {g.fail} failure(s), {g.warn} warning(s)")
        print("RESULT: RELEASE GATES FAIL")
        return 1
    backend = live["engineering_backend"]
    ecf_mode = backend == "ecf"
    g.ok(f"engineering backend resolved and valid: {backend}")

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

    ecf = live["bundled_ecf"]
    ekb = live["bundled_ekb"]

    if ecf_mode:
        # --- Gate 3: bundled ECF identity complete & machine-path-free --------
        g.assert_(is_sha40(ecf.get("source_commit")),
                  f"ECF source_commit is a 40-hex commit ({ecf.get('source_commit')})",
                  f"ECF source_commit missing/invalid ({ecf.get('source_commit')})")
        g.assert_(bool(ecf.get("source")) and not has_machine_path(ecf.get("source")),
                  f"ECF source is machine-path-free ({ecf.get('source')})",
                  f"ECF source missing or embeds a machine path ({ecf.get('source')})")

        # --- Gate 4: nested EKB identity + ECF<->EKB metadata agreement -------
        recorded = ekb.get("ecf_recorded_ekb_commit")
        nested = ekb.get("source_commit")
        g.assert_(is_sha40(nested),
                  f"nested EKB source_commit is 40-hex ({nested})",
                  f"nested EKB source_commit missing/invalid ({nested})")
        g.assert_(is_sha40(recorded),
                  f"ECF VERSION records an EKB commit ({recorded})",
                  f"ECF VERSION ekb_commit missing/invalid ({recorded})")
        if is_sha40(recorded) and is_sha40(nested):
            g.assert_(recorded == nested,
                      "ECF-recorded EKB commit matches nested EKB VERSION",
                      f"ECF/EKB metadata DISAGREE: ecf.ekb_commit={recorded} nested={nested}")

        # --- Gate 5: required bundled capabilities present ---------------------
        caps = live["compatibility"]["required_capabilities"]
        missing = [c["path"] for c in caps if not c["present"]]
        g.assert_(not missing,
                  f"all {len(caps)} required bundled capabilities present",
                  "missing bundled capabilities: " + ", ".join(missing))
    else:
        # --- Gates 3-5 (standalone): honesty instead of identity --------------
        # ECF identity gates do not apply; what MUST hold is that the manifest
        # claims no ECF guarantee of any kind.
        g.skip("Gates 3-5 (ECF/EKB identity, bundled capabilities): "
               "not applicable on the standalone backend")
        g.assert_(ecf.get("claimed") is False,
                  "manifest claims no bundled-ECF identity (standalone)",
                  "manifest claims bundled-ECF identity on the standalone backend")
        g.assert_(ekb.get("claimed") is False,
                  "manifest claims no bundled-EKB identity (standalone)",
                  "manifest claims bundled-EKB identity on the standalone backend")
        g.assert_(live["compatibility"].get("workflow") is None,
                  "manifest claims no ECF workflow compatibility (standalone)",
                  "manifest claims ECF workflow compatibility on the standalone backend")
        unavailable = {c["name"]: c["available"] for c in live.get("capabilities", [])}
        g.assert_(unavailable.get("ecf_workflow_execution") is False,
                  "capability matrix reports ecf_workflow_execution unavailable",
                  "capability matrix wrongly advertises ecf_workflow_execution")

    # --- Gate 6: consumer scripts present -------------------------------------
    for s in builder.CONSUMER_SCRIPTS:
        g.assert_((root / s).exists(),
                  f"consumer script present: {s}",
                  f"consumer script missing: {s}")

    # --- Gate 7: packaging excludes runtime/generated output ------------------
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

    # --- Gate 8: acceptance level recorded honestly ---------------------------
    al = live["acceptance_level"]
    if ecf_mode:
        g.assert_(al.get("claimed") is True
                  and al.get("single_live_task_proven") is True
                  and al.get("full_workflow_proven") is False,
                  f"acceptance level recorded honestly ({al.get('statement')})",
                  "acceptance level not recorded as expected")
    else:
        g.assert_(al.get("claimed") is False,
                  "no ECF acceptance level claimed (standalone)",
                  "ECF acceptance level claimed on the standalone backend")

    # Advisory: version-line independence (informational, never fails; ecf only).
    if ecf_mode and pj_data.get("version") and ecf.get("bundle_version") \
            and pj_data["version"] == ecf["bundle_version"].lstrip("v"):
        g.wn("project version equals ECF bundle version string — keep the version "
             "lines independent (do not bump the project as a proxy for ECF/EKB)")

    print()
    print(f"release-validation: {g.fail} failure(s), {g.warn} warning(s)")
    if g.fail == 0:
        print("RESULT: RELEASE GATES PASS "
              "(offline; live Claude not invoked; nothing published)")
        return 0
    print("RESULT: RELEASE GATES FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
