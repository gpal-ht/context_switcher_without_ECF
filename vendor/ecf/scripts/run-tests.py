#!/usr/bin/env python3
"""Canonical ECF test runner (npm test).

ECF's tools are self-contained units: each `tools/<tool>/` puts its own modules
on sys.path and several share top-level module names (e.g. both
`tools/workflow_planner` and `tools/runtime_state` define `models`). A single
flat `pytest` over the whole tree therefore collides on import. The canonical,
collision-free way to run the control-plane suites is to invoke each tool's
`tests/` directory as an isolated pytest session and aggregate the results.

This runner is READ-ONLY: it executes tests, publishes nothing, and invokes no
live AI. Exit 0 iff every suite passes. Standard library only.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The canonical ECF control-plane suites, in dependency order.
SUITES = [
    "tools/workflow_validator/tests",
    "tools/workflow_planner/tests",
    "tools/run_initializer/tests",
    "tools/runtime_state/tests",
    "tools/task_runner/tests",
    "tools/artifact_fingerprint/tests",
]

_PASSED = re.compile(r"(\d+) passed")
_FAILED = re.compile(r"(\d+) failed")


def main() -> int:
    total_passed = 0
    total_failed = 0
    hard_errors = 0
    print("ECF canonical test suites (per-tool isolation)\n")
    for suite in SUITES:
        path = REPO_ROOT / suite
        if not path.is_dir():
            print(f"  MISSING  {suite}")
            hard_errors += 1
            continue
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(path), "-q"],
            cwd=REPO_ROOT, capture_output=True, text=True,
            env={**_env(), "PYTHONDONTWRITEBYTECODE": "1"},
        )
        tail = (proc.stdout.strip().splitlines() or ["(no output)"])[-1]
        passed = int(m.group(1)) if (m := _PASSED.search(proc.stdout)) else 0
        failed = int(m.group(1)) if (m := _FAILED.search(proc.stdout)) else 0
        total_passed += passed
        total_failed += failed
        status = "PASS" if proc.returncode == 0 else "FAIL"
        if proc.returncode != 0 and failed == 0:
            hard_errors += 1
        print(f"  {status}  {suite:42s} {tail}")
        if proc.returncode != 0:
            sys.stdout.write(proc.stdout[-1500:])
            sys.stderr.write(proc.stderr[-800:])

    print(f"\nTOTAL: {total_passed} passed, {total_failed} failed"
          f"{f', {hard_errors} suite error(s)' if hard_errors else ''}")
    return 0 if (total_failed == 0 and hard_errors == 0) else 1


def _env():
    import os
    return dict(os.environ)


if __name__ == "__main__":
    raise SystemExit(main())
