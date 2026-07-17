"""
Tests for the ECF single-task runner.

Uses temporary run directories seeded via the runtime_state layer; never touches
repository runtime data. Imports task_runner first so the bare 'models'/'transaction'
names resolve to the runtime_state subsystem the runner loaded.
"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[2]
_REPO = _TOOLS.parent
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(_TOOLS / "runtime_state"))

# Import the runner package first; this loads the runtime_state subsystem and
# leaves its 'models'/'transaction'/'storage' cached for the bare imports below.
from task_runner.runner import run_one_task, Runner            # noqa: E402
from task_runner.executor import FixtureExecutor, TaskExecutor  # noqa: E402
from task_runner.models import ExitCode, TaskExecutionResult    # noqa: E402
from task_runner import run_task                                # noqa: E402

import transaction as tx                                        # noqa: E402  (runtime_state)
import recovery as rec                                          # noqa: E402
from models import RunState, RunManifest                        # noqa: E402  (runtime_state models)

WF = _REPO / "workflows" / "reasoning" / "WF-REASON-0001-engineering-recommendation.md"
FX = _REPO / "acceptance_tests" / "fixtures" / "task_runner"
INTENT = FX / "engineering-intent.yaml"
PKG = FX / "knowledge-package.md"


def seed(root: Path, task_states=None, revision=0, mode="required",
         wf_id="WF-REASON-0001") -> Path:
    run = root / "runs" / "RUN-TR"
    run.mkdir(parents=True)
    tx.save_run_state(run, RunState(
        run_id="RUN-TR", work_request_id="WR-0001", workflow_id=wf_id, workflow_version="0.1.0",
        provenance_mode=mode, revision=revision,
        task_states=task_states or {"TASK-CLASSIFY-0001": "not_started"}))
    tx.save_manifest(run, RunManifest(run_id="RUN-TR", workflow_id=wf_id,
                                      workflow_version="0.1.0", revision=revision, tasks=[]))
    return run


class RunnerBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_classify1(self, run, fixture=INTENT, **kw):
        return run_one_task(WF, run, FixtureExecutor(fixture), task_id="TASK-CLASSIFY-0001", **kw)


class TestHappyPath(RunnerBase):
    def test_ready_task_executes_and_commits(self):
        run = seed(self.root)
        r = self.run_classify1(run)
        self.assertEqual(r.exit_code, ExitCode.OK)
        self.assertEqual(r.status, "committed")

    def test_writes_output_and_provenance(self):
        run = seed(self.root)
        self.run_classify1(run)
        self.assertTrue((run / "task_outputs" / "engineering-intent.yaml").is_file())
        self.assertTrue((run / "provenance" / "TASK-CLASSIFY-0001.yaml").is_file())

    def test_revisions_increment_together(self):
        run = seed(self.root)
        r = self.run_classify1(run)
        self.assertEqual(r.state_revision, 1)
        self.assertEqual(r.manifest_revision, 1)
        self.assertEqual(tx.load_run_state(run).revision, tx.load_manifest(run).revision)

    def test_completed_only_after_commit(self):
        run = seed(self.root)
        self.run_classify1(run)
        self.assertEqual(tx.load_run_state(run).task_states["TASK-CLASSIFY-0001"], "completed")

    def test_output_hash_matches_provenance(self):
        run = seed(self.root)
        self.run_classify1(run)
        import hashlib
        out = (run / "task_outputs" / "engineering-intent.yaml").read_bytes()
        prov = (run / "provenance" / "TASK-CLASSIFY-0001.yaml").read_text()
        self.assertIn(hashlib.sha256(out).hexdigest(), prov)

    def test_runner_stops_after_one_task(self):
        run = seed(self.root, task_states={"TASK-CLASSIFY-0001": "not_started",
                                           "TASK-CLASSIFY-0002": "not_started"})
        self.run_classify1(run)
        st = tx.load_run_state(run)
        self.assertEqual(st.task_states["TASK-CLASSIFY-0001"], "completed")
        # the runner did not touch any other task
        self.assertEqual(st.task_states["TASK-CLASSIFY-0002"], "not_started")


class TestRejections(RunnerBase):
    def test_refuse_blocked_task(self):
        run = seed(self.root)
        r = run_one_task(WF, run, FixtureExecutor(INTENT), task_id="TASK-ANALYZE-0001")
        self.assertEqual(r.exit_code, ExitCode.REJECTED)

    def test_refuse_unknown_task(self):
        run = seed(self.root)
        r = run_one_task(WF, run, FixtureExecutor(INTENT), task_id="TASK-NOPE-9999")
        self.assertEqual(r.exit_code, ExitCode.REJECTED)

    def test_refuse_invalid_workflow(self):
        run = seed(self.root)
        bad = _REPO / "acceptance_tests" / "fixtures" / "workflows" / "wf008_cycle.md"
        r = run_one_task(bad, run, FixtureExecutor(INTENT), task_id="TASK-CLASSIFY-0001")
        self.assertEqual(r.exit_code, ExitCode.REJECTED)

    def test_refuse_unresolved_recovery(self):
        run = seed(self.root, revision=0)
        # induce a state/manifest revision mismatch
        s = tx.load_run_state(run); s.revision = 3; tx.save_run_state(run, s)
        r = self.run_classify1(run)
        self.assertEqual(r.exit_code, ExitCode.RECOVERY_REQUIRED)

    def test_invalid_candidate_output_rejected(self):
        run = seed(self.root)
        r = self.run_classify1(run, fixture=FX / "empty.yaml")
        self.assertEqual(r.exit_code, ExitCode.REJECTED)
        self.assertFalse((run / "task_outputs" / "engineering-intent.yaml").is_file())

    def test_executor_failure_leaves_no_output(self):
        run = seed(self.root)
        r = self.run_classify1(run, fixture=FX / "missing.yaml")
        self.assertEqual(r.exit_code, ExitCode.REJECTED)
        self.assertFalse((run / "task_outputs" / "engineering-intent.yaml").is_file())
        self.assertEqual(tx.load_run_state(run).task_states["TASK-CLASSIFY-0001"], "failed")


class TestLockingAndConfig(RunnerBase):
    def test_second_writer_blocked_by_lock(self):
        run = seed(self.root)
        tx.acquire_run_lock(run, owner="other-writer")
        r = self.run_classify1(run)
        self.assertEqual(r.exit_code, ExitCode.CONFIG)

    def test_missing_run_config_is_config_error(self):
        run = self.root / "runs" / "EMPTY"
        (run / "task_outputs").mkdir(parents=True)  # no state.yaml/provenance mode
        r = run_one_task(WF, run, FixtureExecutor(INTENT), task_id="TASK-CLASSIFY-0001")
        self.assertEqual(r.exit_code, ExitCode.CONFIG)


class TestRerunPolicy(RunnerBase):
    def test_completed_valid_not_rerun_by_default(self):
        run = seed(self.root)
        self.run_classify1(run)
        again = self.run_classify1(run)
        self.assertEqual(again.exit_code, ExitCode.REJECTED)

    def test_force_rerun_of_valid_completed(self):
        run = seed(self.root)
        self.run_classify1(run)
        forced = self.run_classify1(run, force_rerun=True)
        self.assertEqual(forced.exit_code, ExitCode.OK)

    def test_stale_task_rerun_when_planner_requires(self):
        run = seed(self.root)
        self.run_classify1(run)
        # tamper the committed output so the planner marks it stale (rerun)
        (run / "task_outputs" / "engineering-intent.yaml").write_bytes(b"tampered: true\n")
        r = self.run_classify1(run)  # no --force-rerun needed: planner requires rerun
        self.assertEqual(r.exit_code, ExitCode.OK)


class TestInputsAndEkb(RunnerBase):
    def _chain(self, run, task, fixture):
        return run_one_task(WF, run, FixtureExecutor(fixture), task_id=task)

    def test_input_hashes_match_provenance_and_inputs_unchanged(self):
        run = seed(self.root, task_states={
            "TASK-CLASSIFY-0001": "not_started", "TASK-CLASSIFY-0002": "not_started"})
        self._chain(run, "TASK-CLASSIFY-0001", INTENT)
        intent_path = run / "task_outputs" / "engineering-intent.yaml"
        import hashlib
        before = hashlib.sha256(intent_path.read_bytes()).hexdigest()
        r = self._chain(run, "TASK-CLASSIFY-0002", INTENT)  # depends on CLASSIFY-0001
        self.assertEqual(r.exit_code, ExitCode.OK)
        prov = (run / "provenance" / "TASK-CLASSIFY-0002.yaml").read_text()
        self.assertIn("engineering-intent.yaml", prov)
        self.assertIn(before, prov)  # input hash recorded
        # the fixture executor did not modify the input
        self.assertEqual(hashlib.sha256(intent_path.read_bytes()).hexdigest(), before)

    def test_ekb_required_task_gets_ekb_identity(self):
        # complete the chain up to the EKB-consuming TASK-RETRIEVE-0002
        run = seed(self.root, task_states={t: "not_started" for t in (
            "TASK-CLASSIFY-0001", "TASK-CLASSIFY-0002", "TASK-RETRIEVE-0001", "TASK-RETRIEVE-0002")})
        for t, f in [("TASK-CLASSIFY-0001", INTENT), ("TASK-CLASSIFY-0002", INTENT),
                     ("TASK-RETRIEVE-0001", INTENT), ("TASK-RETRIEVE-0002", PKG)]:
            r = self._chain(run, t, f)
            self.assertEqual(r.exit_code, ExitCode.OK, msg=f"{t}: {r.message}")
        prov = (run / "provenance" / "TASK-RETRIEVE-0002.yaml").read_text()
        self.assertIn("ekb_version:", prov)   # provenance cannot omit required EKB identity
        self.assertIn("ekb_commit:", prov)


class TestSecurity(RunnerBase):
    def test_output_path_traversal_rejected(self):
        run = seed(self.root)
        runner = Runner(WF, run, FixtureExecutor(INTENT))
        ok, reasons = runner._validate_output(b"x: 1\n", "../escape.yaml",
                                               TaskExecutionResult(task_id="T", output_bytes=b"x"))
        self.assertFalse(ok)
        self.assertTrue(any("must be under" in r or "unsafe" in r for r in reasons))

    def test_output_into_canonical_root_rejected(self):
        run = seed(self.root)
        runner = Runner(WF, run, FixtureExecutor(INTENT))
        ok, reasons = runner._validate_output(b"x: 1\n", "vendor/engineering_kb/x.yaml",
                                               TaskExecutionResult(task_id="T", output_bytes=b"x"))
        self.assertFalse(ok)


class TestCliAndExitCodes(RunnerBase):
    def test_json_output_parseable_and_exit_ok(self):
        import json
        run = seed(self.root)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = run_task.main([str(WF), "--run", str(run), "--task", "TASK-CLASSIFY-0001",
                                "--executor", "fixture", "--fixture", str(INTENT), "--format", "json"])
        self.assertEqual(rc, ExitCode.OK)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["task_id"], "TASK-CLASSIFY-0001")
        self.assertEqual(data["status"], "committed")

    def test_exit_codes_contract(self):
        run = seed(self.root)
        # 0 on success, 1 on rejection
        self.assertEqual(self.run_classify1(run).exit_code, 0)
        self.assertEqual(
            run_one_task(WF, seed(self.root / "b", ), FixtureExecutor(INTENT),
                         task_id="TASK-NOPE").exit_code, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
