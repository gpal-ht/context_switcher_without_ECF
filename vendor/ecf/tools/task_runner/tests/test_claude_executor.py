"""
Tests for the Claude Code executor (AI-backed intent classification).

The Claude subprocess is mocked/faked — no live Claude invocation. Full runner
integration uses a fake subprocess runner injected into the executor.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[2]
_REPO = _TOOLS.parent
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(_TOOLS / "runtime_state"))

# Import runner first (loads runtime_state; leaves bare names cached for seeding).
from task_runner.runner import run_one_task                     # noqa: E402
from task_runner.executor import make_executor, ExecutorError, FixtureExecutor  # noqa: E402
from task_runner.executors.claude_code import ClaudeCodeExecutor  # noqa: E402
from task_runner.models import ExitCode, ExecutorStatus, TaskExecutionRequest  # noqa: E402

import transaction as tx                                        # noqa: E402
from models import RunState, RunManifest                        # noqa: E402

WF = _REPO / "workflows" / "reasoning" / "WF-REASON-0001-engineering-recommendation.md"
CFX = _REPO / "acceptance_tests" / "fixtures" / "task_runner" / "claude"
VALID_ENVELOPE = (CFX / "valid_envelope.json").read_text()


def fake_returning(stdout="", code=0, timed_out=False):
    def _fake(cmd_list, prompt, timeout):
        return stdout, "", code, 0.01, timed_out
    return _fake


def request(task="TASK-CLASSIFY-0001", run_dir="", wr="WR-0001", tv="0.1.0"):
    return TaskExecutionRequest(
        run_id="RUN", work_request_id=wr, workflow_id="WF-REASON-0001",
        workflow_version="0.1.0", task_id=task, task_version=tv, task_spec_path="x",
        output_binding="task_outputs/engineering-intent.yaml", run_dir=str(run_dir))


def executor(runner=None, allow_ai=True, command="claude"):
    return ClaudeCodeExecutor(command=command, repo_root=_REPO, allow_ai=allow_ai,
                              subprocess_runner=runner or fake_returning(VALID_ENVELOPE))


class WithRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name) / "runs" / "RUN-C"
        (self.run / "inputs").mkdir(parents=True)
        (self.run / "inputs" / "work-request.md").write_text(
            (CFX / "work-request.md").read_text(), encoding="utf-8")
        tx.save_run_state(self.run, RunState(
            run_id="RUN-C", work_request_id="WR-0001", workflow_id="WF-REASON-0001",
            workflow_version="0.1.0", provenance_mode="required", revision=0,
            task_states={"TASK-CLASSIFY-0001": "not_started"}))
        tx.save_manifest(self.run, RunManifest(run_id="RUN-C", workflow_id="WF-REASON-0001",
                                               workflow_version="0.1.0", revision=0, tasks=[]))

    def tearDown(self):
        self.tmp.cleanup()


class TestExecutorBoundary(WithRun):
    def test_rejects_other_task(self):
        res = executor().execute(request(task="TASK-RETRIEVE-0002", run_dir=self.run))
        self.assertEqual(res.status, ExecutorStatus.FAILED)
        self.assertEqual(res.failure["code"], "unsupported_task")

    def test_ai_opt_in_required_at_executor(self):
        res = executor(allow_ai=False).execute(request(run_dir=self.run))
        self.assertEqual(res.failure["code"], "ai_not_permitted")

    def test_ai_opt_in_required_at_factory(self):
        with self.assertRaises(ExecutorError):
            make_executor("claude-code", {"claude_command": "claude", "repo_root": _REPO,
                                          "allow_ai": False})

    def test_missing_executable_fails_cleanly(self):
        ex = ClaudeCodeExecutor(command="definitely-not-a-real-command-xyz", repo_root=_REPO,
                                allow_ai=True)  # real subprocess -> FileNotFoundError
        res = ex.execute(request(run_dir=self.run))
        self.assertEqual(res.status, ExecutorStatus.FAILED)
        self.assertIn(res.failure["code"], ("command_not_found", "command_failed"))

    def test_timeout_fails(self):
        res = executor(runner=fake_returning(timed_out=True)).execute(request(run_dir=self.run))
        self.assertEqual(res.failure["code"], "timeout")

    def test_nonzero_exit_fails(self):
        res = executor(runner=fake_returning(stdout="x", code=1)).execute(request(run_dir=self.run))
        self.assertEqual(res.failure["code"], "nonzero_exit")


class TestOutputParsing(WithRun):
    def test_valid_json_passes(self):
        res = executor().execute(request(run_dir=self.run))
        self.assertEqual(res.status, ExecutorStatus.SUCCEEDED)
        env = json.loads(res.output_bytes.decode())
        self.assertEqual(env["engineering_intent"]["primary"], "design_solution")

    def test_freeform_markdown_fails(self):
        res = executor(runner=fake_returning((CFX / "freeform.md").read_text())).execute(
            request(run_dir=self.run))
        self.assertEqual(res.failure["code"], "invalid_output")

    def test_multiple_json_fails(self):
        two = VALID_ENVELOPE + "\n" + VALID_ENVELOPE
        res = executor(runner=fake_returning(two)).execute(request(run_dir=self.run))
        self.assertEqual(res.failure["code"], "invalid_output")

    def test_schema_failure_bubbles_up(self):
        bad = json.loads(VALID_ENVELOPE); bad["engineering_intent"]["primary"] = "make_decision"
        res = executor(runner=fake_returning(json.dumps(bad))).execute(request(run_dir=self.run))
        self.assertEqual(res.failure["code"], "schema_failure")

    def test_recommendation_field_rejected(self):
        bad = json.loads(VALID_ENVELOPE); bad["recommendation"] = "proceed"
        res = executor(runner=fake_returning(json.dumps(bad))).execute(request(run_dir=self.run))
        self.assertEqual(res.failure["code"], "schema_failure")

    def test_work_request_missing(self):
        # a run with no inputs/ -> fail before invoking Claude
        empty = Path(self.tmp.name) / "runs" / "EMPTY"
        empty.mkdir(parents=True)
        res = executor().execute(request(run_dir=empty))
        self.assertEqual(res.failure["code"], "work_request_missing")


class TestInputProtection(WithRun):
    def test_input_modification_detected(self):
        wr = self.run / "inputs" / "work-request.md"

        def tamper(cmd_list, prompt, timeout):
            wr.write_text("TAMPERED\n", encoding="utf-8")  # modify the read-only input
            return VALID_ENVELOPE, "", 0, 0.01, False

        res = executor(runner=tamper).execute(request(run_dir=self.run))
        self.assertEqual(res.failure["code"], "input_modified")


class TestRunnerIntegration(WithRun):
    def test_commit_after_valid_execution(self):
        ex = executor()
        r = run_one_task(WF, self.run, ex, task_id="TASK-CLASSIFY-0001")
        self.assertEqual(r.exit_code, ExitCode.OK, msg=r.message)
        out = self.run / "task_outputs" / "engineering-intent.yaml"
        provf = self.run / "provenance" / "TASK-CLASSIFY-0001.yaml"
        self.assertTrue(out.is_file() and provf.is_file())
        # committed output is the JSON envelope; provenance records its hash
        import hashlib
        self.assertIn(hashlib.sha256(out.read_bytes()).hexdigest(), provf.read_text())
        # runner executed exactly one task
        self.assertEqual(tx.load_run_state(self.run).task_states["TASK-CLASSIFY-0001"], "completed")

    def test_schema_failure_leaves_no_output(self):
        bad = json.loads(VALID_ENVELOPE); bad["work_request_id"] = "WR-9999"
        ex = executor(runner=fake_returning(json.dumps(bad)))
        r = run_one_task(WF, self.run, ex, task_id="TASK-CLASSIFY-0001")
        self.assertEqual(r.exit_code, ExitCode.REJECTED)
        self.assertFalse((self.run / "task_outputs" / "engineering-intent.yaml").exists())

    def test_fixture_executor_still_works(self):
        r = run_one_task(WF, self.run, FixtureExecutor(
            _REPO / "acceptance_tests" / "fixtures" / "task_runner" / "engineering-intent.yaml"),
            task_id="TASK-CLASSIFY-0001")
        self.assertEqual(r.exit_code, ExitCode.OK)


if __name__ == "__main__":
    unittest.main(verbosity=2)
