"""
Executor-independent output-contract enforcement (runner-owned).

Proves that the TASK-CLASSIFY-0001 output contract is enforced by the RUNNER for
the fixture executor (i.e. independently of the Claude executor), that invalid
candidates never reach commit, and that failure is transaction-safe. Test 19
(valid Claude mock commits) is covered by test_claude_executor.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]
_TOOLS = _REPO / "tools"
for _p in (_TOOLS, _TOOLS / "runtime_state"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from task_runner.runner import run_one_task                     # noqa: E402
from task_runner.executor import FixtureExecutor                # noqa: E402
from task_runner.models import ExitCode, TaskExecutionRequest   # noqa: E402
from task_runner import output_contracts as oc                  # noqa: E402
from task_runner.executors import claude_code as cc             # noqa: E402
import transaction as tx                                        # noqa: E402
from models import RunState, RunManifest                        # noqa: E402

WF = _REPO / "workflows" / "reasoning" / "WF-REASON-0001-engineering-recommendation.md"

VALID = {
    "schema_version": "0.1.0", "task_id": "TASK-CLASSIFY-0001", "task_version": "0.1.0",
    "work_request_id": "WR-0001", "status": "completed",
    "engineering_intent": {"primary": "design_solution", "secondary": []},
    "classification_evidence": {"engineering_question": "Q?", "desired_outcome": "Rec",
                                "requested_deliverables": ["Report"]},
    "confidence": {"level": "high", "justification": "because evidence"},
    "findings": [],
}


def seed(root: Path) -> Path:
    run = root / "runs" / "RUN-OC"
    run.mkdir(parents=True)
    tx.save_run_state(run, RunState(
        run_id="RUN-OC", work_request_id="WR-0001", workflow_id="WF-REASON-0001",
        workflow_version="0.1.0", provenance_mode="required", revision=0,
        task_states={"TASK-CLASSIFY-0001": "not_started"}))
    tx.save_manifest(run, RunManifest(run_id="RUN-OC", workflow_id="WF-REASON-0001",
                                      workflow_version="0.1.0", revision=0, tasks=[]))
    return run


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run = seed(self.root)
        self.fxdir = self.root / "fx"
        self.fxdir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _fixture(self, content) -> Path:
        p = self.fxdir / "cand.json"
        p.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
        return p

    def classify(self, content):
        return run_one_task(WF, self.run, FixtureExecutor(self._fixture(content)),
                            task_id="TASK-CLASSIFY-0001")

    def assert_rejected_safely(self, r):
        self.assertEqual(r.exit_code, ExitCode.REJECTED, msg=r.message)                 # 12/13/15
        self.assertFalse((self.run / "task_outputs" / "engineering-intent.yaml").exists())  # 13 no output
        self.assertFalse((self.run / "provenance" / "TASK-CLASSIFY-0001.yaml").exists())    # 14 no provenance
        st = tx.load_run_state(self.run)
        self.assertNotEqual(st.task_states.get("TASK-CLASSIFY-0001"), "completed")       # 15 not completed
        self.assertIsNone(tx.read_lock(self.run))                                        # 16 lock released


class TestContract(Base):
    def test_01_valid_fixture_commits(self):
        r = self.classify(VALID)
        self.assertEqual(r.exit_code, ExitCode.OK, msg=r.message)
        self.assertEqual(tx.load_run_state(self.run).task_states["TASK-CLASSIFY-0001"], "completed")

    def test_02_wrong_task_id_rejected(self):
        self.assert_rejected_safely(self.classify({**VALID, "task_id": "WRONG"}))

    def test_03_wrong_work_request_id_rejected(self):
        self.assert_rejected_safely(self.classify({**VALID, "work_request_id": "WR-9999"}))

    def test_04_wrong_task_version_rejected(self):
        self.assert_rejected_safely(self.classify({**VALID, "task_version": "9.9.9"}))

    def test_05_missing_required_field_rejected(self):
        e = dict(VALID); e.pop("confidence")
        self.assert_rejected_safely(self.classify(e))

    def test_06_invalid_primary_intent_rejected(self):
        self.assert_rejected_safely(self.classify(
            {**VALID, "engineering_intent": {"primary": "make_decision", "secondary": []}}))

    def test_07_invalid_secondary_intent_rejected(self):
        self.assert_rejected_safely(self.classify(
            {**VALID, "engineering_intent": {"primary": "design_solution", "secondary": ["not_real"]}}))

    def test_08_unknown_field_rejected(self):
        self.assert_rejected_safely(self.classify({**VALID, "extra_field": 1}))

    def test_09_recommendation_field_rejected(self):
        self.assert_rejected_safely(self.classify({**VALID, "recommendation": "do X"}))

    def test_10_approval_field_rejected(self):
        self.assert_rejected_safely(self.classify({**VALID, "approval": "granted"}))

    def test_11_multiple_json_documents_rejected(self):
        self.assert_rejected_safely(self.classify(json.dumps(VALID) + "\n" + json.dumps(VALID)))

    def test_12_markdown_rejected(self):
        self.assert_rejected_safely(self.classify("# Engineering Intent\n\nThis is free-form prose.\n"))

    # 13/14/15/16 are asserted by assert_rejected_safely above; make one explicit.
    def test_13_16_no_artifacts_no_lock_on_failure(self):
        self.assert_rejected_safely(self.classify({"task_id": "WRONG"}))

    def test_17_planner_not_advanced_after_failure(self):
        self.assert_rejected_safely(self.classify({"task_id": "WRONG"}))
        # the frontier is unchanged: the downstream task is not runnable.
        r2 = run_one_task(WF, self.run, FixtureExecutor(self._fixture(VALID)),
                          task_id="TASK-CLASSIFY-0002")
        self.assertEqual(r2.exit_code, ExitCode.REJECTED)

    def test_18_fixture_and_claude_use_the_same_validator(self):
        # same canonical function object — no drift between executors
        self.assertIs(cc.validate_intent_result, oc.validate_intent_result)
        req = TaskExecutionRequest(
            run_id="RUN-OC", work_request_id="WR-0001", workflow_id="WF-REASON-0001",
            workflow_version="0.1.0", task_id="TASK-CLASSIFY-0001", task_version="0.1.0",
            task_spec_path="x", output_binding="task_outputs/engineering-intent.yaml")
        bad = {**VALID, "task_id": "WRONG"}
        ok_runner, _ = oc.validate_task_output("TASK-CLASSIFY-0001",
                                               json.dumps(bad).encode("utf-8"), req, _REPO)
        ok_claude, _ = cc.validate_intent_result(bad, req, oc.load_intent_taxonomy(_REPO))
        self.assertFalse(ok_runner)
        self.assertFalse(ok_claude)

    def test_20_exactly_one_task_executes(self):
        r = self.classify(VALID)
        self.assertEqual(r.exit_code, ExitCode.OK)
        st = tx.load_run_state(self.run)
        self.assertEqual(st.task_states["TASK-CLASSIFY-0001"], "completed")
        # only the one task advanced; nothing else was completed
        completed = [k for k, v in st.task_states.items() if v == "completed"]
        self.assertEqual(completed, ["TASK-CLASSIFY-0001"])


if __name__ == "__main__":
    unittest.main()
