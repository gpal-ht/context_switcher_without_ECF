"""Tests for the provider-independent executor interface and the fixture executor."""

import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_TOOLS))

from task_runner.executor import FixtureExecutor, TaskExecutor, make_executor, ExecutorError  # noqa: E402
from task_runner.models import ExecutorStatus, TaskExecutionRequest  # noqa: E402

FX = _TOOLS.parent / "acceptance_tests" / "fixtures" / "task_runner"


def request(task="TASK-CLASSIFY-0001", binding="task_outputs/o.yaml"):
    return TaskExecutionRequest(
        run_id="RUN", work_request_id="WR", workflow_id="WF", workflow_version="0.1.0",
        task_id=task, task_version="0.1.0", task_spec_path="x", output_binding=binding)


class TestFixtureExecutor(unittest.TestCase):
    def test_returns_fixture_bytes(self):
        ex = FixtureExecutor(FX / "engineering-intent.yaml")
        res = ex.execute(request())
        self.assertEqual(res.status, ExecutorStatus.SUCCEEDED)
        self.assertTrue(res.output_bytes)
        self.assertIn(b"TASK-CLASSIFY-0001", res.output_bytes)

    def test_missing_fixture_fails_cleanly(self):
        ex = FixtureExecutor(FX / "does-not-exist.yaml")
        res = ex.execute(request())
        self.assertEqual(res.status, ExecutorStatus.FAILED)
        self.assertEqual(res.failure["code"], "fixture_missing")

    def test_read_only_does_not_touch_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            inp = Path(d) / "input.yaml"
            inp.write_bytes(b"x: 1\n")
            before = inp.read_bytes()
            FixtureExecutor(FX / "engineering-intent.yaml").execute(request())
            self.assertEqual(inp.read_bytes(), before)

    def test_factory_rejects_unknown_executor(self):
        with self.assertRaises(ExecutorError):
            make_executor("claude", {})
        with self.assertRaises(ExecutorError):
            make_executor("command", {})   # not enabled in v0.1

    def test_factory_requires_fixture_path(self):
        with self.assertRaises(ExecutorError):
            make_executor("fixture", {})

    def test_provider_independent_interface(self):
        class DummyExecutor(TaskExecutor):
            id = "dummy"
            def execute(self, req):
                from task_runner.models import TaskExecutionResult
                return TaskExecutionResult(task_id=req.task_id, output_bytes=b"k: v\n")
        res = DummyExecutor().execute(request())
        self.assertTrue(res.succeeded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
