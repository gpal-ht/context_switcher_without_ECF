"""
Unit tests for the ECF Execution Planner.

Read-only: tests plan the real WF-REASON-0001 against runtime fixtures and
assert task states. They never modify repository files; a dedicated test proves
the planner does not mutate the runtime directory it inspects.

Run:
    python -m unittest discover -s tools/workflow_planner/tests
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PLANNER_DIR = _HERE.parent
_VALIDATOR_DIR = _PLANNER_DIR.parent / "workflow_validator"
for _p in (str(_PLANNER_DIR), str(_VALIDATOR_DIR)):
    sys.path.insert(0, _p)

import validate_workflow as vw          # noqa: E402
import plan_workflow                     # noqa: E402
from planner import PlannerError, RuntimeState, compute_plan, plan_from_paths  # noqa: E402
from models import PlanStatus, TaskState  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_WF = REPO_ROOT / "workflows" / "reasoning" / "WF-REASON-0001-engineering-recommendation.md"
FIX = _HERE / "fixtures"
VALIDATOR_FIX = REPO_ROOT / "acceptance_tests" / "fixtures" / "workflows"


def index():
    return vw.RepoIndex(
        repo_root=REPO_ROOT,
        tasks_dir=REPO_ROOT / "tasks",
        catalog_path=REPO_ROOT / "workflows" / "WORKFLOW_CATALOG.md",
        workflows_dir=REPO_ROOT / "workflows",
    )


class PlannerTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.idx = index()

    def plan(self, run_dir):
        return plan_from_paths(REAL_WF, run_dir, self.idx)

    def state_of(self, plan, task_id):
        return next(t.state for t in plan.tasks if t.id == task_id)

    def reason_of(self, plan, task_id):
        return next(t.reason for t in plan.tasks if t.id == task_id)


class TestNoRuntime(PlannerTestBase):
    def test_fresh_start_only_entry_ready(self):
        plan = self.plan(None)
        self.assertEqual(plan.status, PlanStatus.RUNNABLE)
        self.assertEqual(plan.ready, ["TASK-CLASSIFY-0001"])
        self.assertEqual(len(plan.completed), 0)
        self.assertEqual(len(plan.blocked), 17)

    def test_remaining_order_is_full_topo(self):
        plan = self.plan(None)
        self.assertEqual(len(plan.remaining_order), 18)
        self.assertEqual(plan.remaining_order[0], "TASK-CLASSIFY-0001")
        self.assertEqual(plan.remaining_order[-1], "TASK-TRACE-0003")


class TestEmptyRuntime(PlannerTestBase):
    def test_empty_run_dir_like_fresh(self):
        plan = self.plan(FIX / "empty_run")
        self.assertEqual(plan.status, PlanStatus.RUNNABLE)
        self.assertEqual(plan.ready, ["TASK-CLASSIFY-0001"])


class TestPartialRuntime(PlannerTestBase):
    def test_three_completed_one_ready(self):
        plan = self.plan(FIX / "partial_run")
        self.assertEqual(plan.status, PlanStatus.RUNNABLE)
        self.assertEqual(len(plan.completed), 3)
        self.assertEqual(plan.ready, ["TASK-RETRIEVE-0002"])
        self.assertEqual(len(plan.blocked), 14)


class TestCompletedRuntime(PlannerTestBase):
    def test_all_completed(self):
        plan = self.plan(FIX / "completed_run")
        self.assertEqual(plan.status, PlanStatus.COMPLETE)
        self.assertEqual(len(plan.completed), 18)
        self.assertEqual(plan.remaining_order, [])


class TestFailedTask(PlannerTestBase):
    def test_failed_task_blocks_dependents(self):
        plan = self.plan(FIX / "failed_run")
        self.assertEqual(self.state_of(plan, "TASK-ANALYZE-0002"), TaskState.FAILED)
        self.assertEqual(self.state_of(plan, "TASK-ANALYZE-0003"), TaskState.BLOCKED)
        self.assertIn("failed", self.reason_of(plan, "TASK-ANALYZE-0003"))
        self.assertEqual(plan.status, PlanStatus.BLOCKED)


class TestMissingOutput(PlannerTestBase):
    def test_missing_required_output_blocks(self):
        plan = self.plan(FIX / "missing_output_run")
        # declared completed even though the file is absent
        self.assertEqual(self.state_of(plan, "TASK-CLASSIFY-0001"), TaskState.COMPLETED)
        # dependent blocked precisely because the output is missing
        self.assertEqual(self.state_of(plan, "TASK-CLASSIFY-0002"), TaskState.BLOCKED)
        self.assertIn("missing", self.reason_of(plan, "TASK-CLASSIFY-0002"))


class TestInvalidRuntime(PlannerTestBase):
    def test_file_instead_of_dir_raises(self):
        with self.assertRaises(PlannerError):
            self.plan(FIX / "invalid_run_is_a_file")

    def test_nonexistent_run_dir_raises(self):
        with self.assertRaises(PlannerError):
            self.plan(FIX / "does_not_exist_dir")

    def test_cli_exit_2_on_invalid_runtime(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = plan_workflow.main([str(REAL_WF), "--run", str(FIX / "invalid_run_is_a_file")])
        self.assertEqual(rc, 2)


class TestCancelledRun(PlannerTestBase):
    def test_cancelled_marks_incomplete_cancelled(self):
        plan = self.plan(FIX / "cancelled_run")
        self.assertEqual(self.state_of(plan, "TASK-CLASSIFY-0002"), TaskState.CANCELLED)
        self.assertEqual(plan.status, PlanStatus.BLOCKED)


class TestSupersededRun(PlannerTestBase):
    def test_superseded_marks_incomplete_superseded(self):
        plan = self.plan(FIX / "superseded_run")
        self.assertEqual(self.state_of(plan, "TASK-CLASSIFY-0002"), TaskState.SUPERSEDED)


class TestInvalidWorkflow(PlannerTestBase):
    def test_invalid_workflow_yields_invalid_plan_exit_1(self):
        bad = VALIDATOR_FIX / "wf008_cycle.md"
        if not bad.is_file():
            self.skipTest("validator cycle fixture not present")
        plan = plan_from_paths(bad, None, self.idx)
        self.assertEqual(plan.status, PlanStatus.INVALID)
        self.assertTrue(plan.validation_errors)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = plan_workflow.main([str(bad)])
        self.assertEqual(rc, 1)


class TestReadOnly(PlannerTestBase):
    def _snapshot(self, root: Path):
        snap = {}
        for p in sorted(root.rglob("*")):
            if p.is_file():
                st = p.stat()
                snap[str(p)] = (st.st_mtime_ns, st.st_size)
        return snap

    def test_planner_does_not_modify_runtime(self):
        target = FIX / "partial_run"
        before = self._snapshot(target)
        buf = io.StringIO()
        with redirect_stdout(buf):
            plan_workflow.main([str(REAL_WF), "--run", str(target), "--format", "json"])
        after = self._snapshot(target)
        self.assertEqual(before, after, "planner must not modify runtime files")

    def test_json_output_parseable(self):
        import json
        buf = io.StringIO()
        with redirect_stdout(buf):
            plan_workflow.main([str(REAL_WF), "--run", str(FIX / "partial_run"), "--format", "json"])
        data = json.loads(buf.getvalue())
        self.assertEqual(data["workflow"], "WF-REASON-0001")
        self.assertEqual(data["counts"]["total"], 18)


if __name__ == "__main__":
    unittest.main(verbosity=2)
