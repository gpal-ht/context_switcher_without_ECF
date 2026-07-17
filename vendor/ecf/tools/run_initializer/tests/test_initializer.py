"""
Tests for the ECF Run Initialization Engine + wrapper portability.

All filesystem work happens in temporary directories; no persistent repository
runtime run is created. No live Claude is ever invoked.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parents[1]
REPO = _TOOLS.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from run_initializer import initializer as I           # noqa: E402
from run_initializer.initializer import initialize_run  # noqa: E402
from run_initializer.models import (                    # noqa: E402
    InitError, InitExitCode, InitRequest,
)

WF = REPO / "workflows" / "reasoning" / "WF-REASON-0001-engineering-recommendation.md"
WR_VALID = REPO / "acceptance_tests" / "fixtures" / "run_initializer" / "WR-0001-valid.md"
WR_INVALID = (REPO / "acceptance_tests" / "fixtures" / "run_initializer"
              / "WR-invalid-missing-sections.md")
INTENT_FIXTURE = (REPO / "acceptance_tests" / "fixtures" / "task_runner"
                  / "engineering-intent.yaml")
INIT_CLI = _TOOLS / "run_initializer" / "initialize_run.py"
SCRIPTS = REPO / "scripts"

PS = shutil.which("powershell") or shutil.which("pwsh")


def _rm_onerror(func, path, _exc):
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        func(path)
    except OSError:
        pass


def _rmtree(path):
    if Path(path).exists():
        shutil.rmtree(path, onerror=_rm_onerror)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="ecf-init-test-"))
        self.run_root = self._tmp / "runs"
        self.addCleanup(_rmtree, self._tmp)

    def make_request(self, **kw):
        params = dict(
            workflow_path=str(WF), work_request_path=str(WR_VALID),
            run_id="RUN-REASON-TEST-0001", run_root=str(self.run_root),
            repo_root=str(REPO),
        )
        params.update(kw)
        return InitRequest(**params)

    def _temp_leftovers(self):
        if not self.run_root.exists():
            return []
        return [p.name for p in self.run_root.iterdir() if p.name.startswith(".init-")]


# --------------------------------------------------------------------------- #
# Core initialization behavior
# --------------------------------------------------------------------------- #

class TestInitialize(Base):
    def test_01_valid_initializes(self):
        res = initialize_run(self.make_request())
        self.assertEqual(res.status, "initialized")
        self.assertEqual(res.exit_code, InitExitCode.OK)
        self.assertTrue(Path(res.run_dir).is_dir())
        self.assertEqual(res.run_id, "RUN-REASON-TEST-0001")
        self.assertEqual(res.work_request_id, "WR-0001")

    def test_02_invalid_workflow_fails_before_final_dir(self):
        bad = self._tmp / "bad-workflow.md"
        bad.write_text("# not a workflow\n", encoding="utf-8")
        with self.assertRaises(InitError) as ctx:
            initialize_run(self.make_request(workflow_path=str(bad)))
        self.assertEqual(ctx.exception.exit_code, InitExitCode.INVALID)
        self.assertFalse((self.run_root / "RUN-REASON-TEST-0001").exists())
        self.assertEqual(self._temp_leftovers(), [])

    def test_03_invalid_work_request_fails_before_final_dir(self):
        with self.assertRaises(InitError) as ctx:
            initialize_run(self.make_request(work_request_path=str(WR_INVALID)))
        self.assertEqual(ctx.exception.exit_code, InitExitCode.INVALID)
        self.assertTrue(any("missing" in r for r in ctx.exception.reasons))
        self.assertFalse((self.run_root / "RUN-REASON-TEST-0001").exists())
        self.assertEqual(self._temp_leftovers(), [])

    def test_04_unsafe_run_id_rejected(self):
        for bad in ("run-lower", "RUN WITH SPACE", "RUN-@bad!", "WR-0001", "RUN-x"):
            with self.assertRaises(InitError):
                initialize_run(self.make_request(run_id=bad))

    def test_05_path_traversal_run_id_rejected(self):
        for bad in ("RUN-../evil", "RUN-a/b", "RUN-a\\b", "..", "/abs/RUN-X"):
            with self.assertRaises(InitError) as ctx:
                initialize_run(self.make_request(run_id=bad))
            self.assertEqual(ctx.exception.exit_code, InitExitCode.CONFIG)

    def test_06_existing_run_not_overwritten_by_default(self):
        initialize_run(self.make_request())
        with self.assertRaises(InitError) as ctx:
            initialize_run(self.make_request())
        self.assertEqual(ctx.exception.exit_code, InitExitCode.CONFIG)
        self.assertIn("already exists", ctx.exception.message)

    def test_07_temp_dir_cleaned_on_failure(self):
        from unittest import mock
        with mock.patch.object(I.pl, "compute_plan",
                               side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                initialize_run(self.make_request())
        self.assertEqual(self._temp_leftovers(), [])
        self.assertFalse((self.run_root / "RUN-REASON-TEST-0001").exists())

    def test_08_state_reloads(self):
        res = initialize_run(self.make_request())
        state = I.tx.load_run_state(Path(res.run_dir))
        self.assertEqual(state.run_id, "RUN-REASON-TEST-0001")

    def test_09_manifest_reloads(self):
        res = initialize_run(self.make_request())
        mf = I.tx.load_manifest(Path(res.run_dir))
        self.assertEqual(mf.run_id, "RUN-REASON-TEST-0001")
        self.assertEqual(len(mf.tasks), 18)

    def test_10_state_and_manifest_run_ids_match(self):
        res = initialize_run(self.make_request())
        state = I.tx.load_run_state(Path(res.run_dir))
        mf = I.tx.load_manifest(Path(res.run_dir))
        self.assertEqual(state.run_id, mf.run_id)

    def test_11_revisions_both_zero(self):
        res = initialize_run(self.make_request())
        state = I.tx.load_run_state(Path(res.run_dir))
        mf = I.tx.load_manifest(Path(res.run_dir))
        self.assertEqual(state.revision, 0)
        self.assertEqual(mf.revision, 0)
        self.assertEqual(res.revision, 0)

    def test_12_provenance_mode_explicit_required(self):
        res = initialize_run(self.make_request())
        state = I.tx.load_run_state(Path(res.run_dir))
        self.assertEqual(state.provenance_mode, "required")
        self.assertEqual(res.provenance_mode, "required")

    def test_13_every_task_not_started(self):
        res = initialize_run(self.make_request())
        state = I.tx.load_run_state(Path(res.run_dir))
        self.assertEqual(len(state.task_states), 18)
        self.assertTrue(all(v == "not_started" for v in state.task_states.values()))

    def test_14_work_request_input_present(self):
        res = initialize_run(self.make_request())
        wr = Path(res.run_dir) / "inputs" / "work-request.md"
        self.assertTrue(wr.is_file())
        self.assertEqual(wr.read_bytes(), WR_VALID.read_bytes())

    def test_15_planner_reports_correct_frontier(self):
        res = initialize_run(self.make_request())
        self.assertEqual(res.ready_tasks, ["TASK-CLASSIFY-0001"])

    def test_16_no_task_output_or_provenance(self):
        res = initialize_run(self.make_request())
        rd = Path(res.run_dir)
        self.assertEqual(list((rd / "task_outputs").iterdir()), [])
        self.assertEqual(list((rd / "reports").iterdir()), [])
        self.assertEqual(list((rd / "provenance").iterdir()), [])

    def test_17_json_output_parseable(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        proc = subprocess.run(
            [sys.executable, str(INIT_CLI), str(WF), "--work-request", str(WR_VALID),
             "--run-root", str(self.run_root), "--run-id", "RUN-REASON-JSON-0001",
             "--format", "json"],
            capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "initialized")
        self.assertEqual(data["ready_tasks"], ["TASK-CLASSIFY-0001"])

    def test_18_read_only_outside_run_root(self):
        outside = self._tmp / "outside_sentinel"
        outside.mkdir()
        (outside / "keep.txt").write_text("untouched", encoding="utf-8")
        res = initialize_run(self.make_request())
        # result lives strictly under the supplied run root
        self.assertTrue(Path(res.run_dir).resolve().is_relative_to(self.run_root.resolve()))
        # the sentinel outside the run root is unchanged
        self.assertEqual((outside / "keep.txt").read_text(encoding="utf-8"), "untouched")

    def test_24_no_live_claude(self):
        # The initializer never accepts or spawns an AI executor.
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        proc = subprocess.run(
            [sys.executable, str(INIT_CLI), "--help"],
            capture_output=True, text=True, env=env)
        self.assertNotIn("claude", proc.stdout.lower())
        res = initialize_run(self.make_request())
        mf = I.tx.load_manifest(Path(res.run_dir))
        self.assertEqual(mf.executor.get("has_run"), False)

    def test_force_replaces_pristine_but_not_progressed(self):
        res = initialize_run(self.make_request())
        # a pristine run may be force-replaced
        res2 = initialize_run(self.make_request(force=True))
        self.assertEqual(res2.status, "initialized")
        # simulate progress -> force must refuse
        state = I.tx.load_run_state(Path(res2.run_dir))
        state.revision = 1
        state.task_states["TASK-CLASSIFY-0001"] = "completed"
        I.tx.save_run_state(Path(res2.run_dir), state)
        with self.assertRaises(InitError) as ctx:
            initialize_run(self.make_request(force=True))
        self.assertIn("refused", ctx.exception.message)


# --------------------------------------------------------------------------- #
# Non-live end-to-end acceptance scenario
# --------------------------------------------------------------------------- #

class TestAcceptanceScenario(Base):
    def test_initialize_then_one_fixture_task_then_next_ready(self):
        # 1) initialize
        res = initialize_run(self.make_request(run_id="RUN-REASON-ACCEPT-0001"))
        run_dir = Path(res.run_dir)
        self.assertEqual(res.ready_tasks, ["TASK-CLASSIFY-0001"])

        # 2) fixture-run EXACTLY ONE task (no AI, no looping)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        run_task = _TOOLS / "task_runner" / "run_task.py"
        proc = subprocess.run(
            [sys.executable, str(run_task), str(WF), "--run", str(run_dir),
             "--task", "TASK-CLASSIFY-0001", "--executor", "fixture",
             "--fixture", str(INTENT_FIXTURE), "--format", "json"],
            capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "committed")

        # 3) planner now shows the NEXT task ready
        plan_cli = _TOOLS / "workflow_planner" / "plan_workflow.py"
        proc2 = subprocess.run(
            [sys.executable, str(plan_cli), str(WF), "--run", str(run_dir),
             "--format", "json"],
            capture_output=True, text=True, env=env)
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        plan = json.loads(proc2.stdout)
        ready = [t["id"] for t in plan["tasks"] if t.get("display_state") == "ready"]
        self.assertIn("TASK-CLASSIFY-0002", ready)
        self.assertNotIn("TASK-CLASSIFY-0001", ready)


# --------------------------------------------------------------------------- #
# Wrapper portability (PowerShell) — canonical vs vendored, cwd-independent
# --------------------------------------------------------------------------- #

@unittest.skipUnless(PS, "PowerShell not available")
class TestWrapperPortability(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="ecf-wrap-test-"))
        self.addCleanup(_rmtree, self._tmp)

    def _ps(self, script: str, cwd: Path):
        return subprocess.run(
            [PS, "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, cwd=str(cwd))

    def _get_ecf_root(self, common_ps1: Path, cwd: Path) -> str:
        proc = self._ps(f". '{common_ps1}'; (Get-EcfRoot).Trim()", cwd)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return os.path.normcase(os.path.realpath(proc.stdout.strip()))

    def test_19_wrapper_resolves_canonical_root(self):
        got = self._get_ecf_root(SCRIPTS / "_ecf-common.ps1", cwd=Path(self._tmp))
        self.assertEqual(got, os.path.normcase(os.path.realpath(REPO)))

    def test_21_wrappers_work_from_unrelated_cwd(self):
        unrelated = self._tmp / "elsewhere"
        unrelated.mkdir()
        got = self._get_ecf_root(SCRIPTS / "_ecf-common.ps1", cwd=unrelated)
        self.assertEqual(got, os.path.normcase(os.path.realpath(REPO)))

    def _make_vendored_ecf(self):
        """An outer Git repo with a vendored ECF-like tree nested inside it."""
        outer = self._tmp / "host_repo"
        (outer).mkdir()
        subprocess.run(["git", "init"], cwd=str(outer),
                       capture_output=True, text=True)
        ecf = outer / "third_party" / "ecf"
        (ecf / "tools").mkdir(parents=True)
        (ecf / "workflows").mkdir(parents=True)
        (ecf / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPTS / "_ecf-common.ps1", ecf / "scripts" / "_ecf-common.ps1")
        return outer, ecf

    def test_20_wrapper_resolves_vendored_root(self):
        outer, ecf = self._make_vendored_ecf()
        got = self._get_ecf_root(ecf / "scripts" / "_ecf-common.ps1", cwd=outer)
        self.assertEqual(got, os.path.normcase(os.path.realpath(ecf)))

    def test_22_outer_git_root_not_used_as_ecf_root(self):
        outer, ecf = self._make_vendored_ecf()
        ecf_root = self._get_ecf_root(ecf / "scripts" / "_ecf-common.ps1", cwd=outer)
        # ECF root must be the vendored tree, never the enclosing Git repo root.
        self.assertEqual(ecf_root, os.path.normcase(os.path.realpath(ecf)))
        self.assertNotEqual(ecf_root, os.path.normcase(os.path.realpath(outer)))

    def test_23_exit_codes_preserved(self):
        # success (0) through the wrapper
        run_root = self._tmp / "runs"
        ok = self._ps(
            f"& '{SCRIPTS / 'initialize-run.ps1'}' "
            f"-Workflow '{WF}' -WorkRequest '{WR_VALID}' "
            f"-RunRoot '{run_root}' -RunId RUN-REASON-WRAP-0001; exit $LASTEXITCODE",
            cwd=Path(self._tmp))
        self.assertEqual(ok.returncode, 0, ok.stderr)
        # invalid Work Request -> exit 1 preserved
        bad = self._ps(
            f"& '{SCRIPTS / 'initialize-run.ps1'}' "
            f"-Workflow '{WF}' -WorkRequest '{WR_INVALID}' "
            f"-RunRoot '{run_root}' -RunId RUN-REASON-WRAP-0002; exit $LASTEXITCODE",
            cwd=Path(self._tmp))
        self.assertEqual(bad.returncode, 1)


# --------------------------------------------------------------------------- #
# Guard: the reused tool stacks still import cleanly (25-29 run as full suites)
# --------------------------------------------------------------------------- #

class TestReusedToolsImport(unittest.TestCase):
    def test_reused_modules_import(self):
        # The two-phase import in the initializer must leave the reused tool
        # stacks usable (no 'models' collision breakage).
        self.assertTrue(hasattr(I.vw, "validate"))
        self.assertTrue(hasattr(I.pl, "compute_plan"))
        self.assertTrue(hasattr(I.tx, "load_run_state"))
        self.assertTrue(hasattr(I.prov, "EnvContext"))


if __name__ == "__main__":
    unittest.main()
