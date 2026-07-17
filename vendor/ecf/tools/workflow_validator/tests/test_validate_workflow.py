"""
Unit tests for the ECF workflow conformance validator.

Read-only: tests validate the real WF-REASON-0001 and small invalid fixtures.
They never modify repository files. Any temporary files are created under the
OS temporary directory only.

Run:
    python -m unittest discover -s tools/workflow_validator/tests
    python tools/workflow_validator/tests/test_validate_workflow.py
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

# Make the validator importable regardless of CWD.
MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))

import validate_workflow as vw  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_WF = REPO_ROOT / "workflows" / "reasoning" / "WF-REASON-0001-engineering-recommendation.md"
FIXTURES = REPO_ROOT / "acceptance_tests" / "fixtures" / "workflows"


def build_index():
    return vw.RepoIndex(
        repo_root=REPO_ROOT,
        tasks_dir=REPO_ROOT / "tasks",
        catalog_path=REPO_ROOT / "workflows" / "WORKFLOW_CATALOG.md",
        workflows_dir=REPO_ROOT / "workflows",
    )


class ValidatorTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.idx = build_index()

    def validate(self, path: Path):
        res, wf = vw.validate(path, self.idx)
        return res

    def error_codes(self, res):
        return {c.code for c in res.errors}


class TestValidWorkflow(ValidatorTestBase):
    def test_real_wf_reason_0001_is_valid(self):
        res = self.validate(REAL_WF)
        self.assertTrue(res.valid, msg=f"Unexpected errors: {self.error_codes(res)}")
        self.assertEqual(len(res.errors), 0)

    def test_real_wf_summary_counts(self):
        _, wf = vw.validate(REAL_WF, self.idx)
        summary = vw.build_summary(wf)
        self.assertEqual(summary["task_count"], 18)
        self.assertEqual(summary["output_binding_count"], 18)
        # Minimized direct/causal graph (was 111 before trace-dependency cleanup).
        self.assertEqual(summary["edge_count"], 68)

    def test_catalog_and_approval_checks_pass(self):
        res = self.validate(REAL_WF)
        by_code = {c.code: c for c in res.checks}
        self.assertEqual(by_code["WF018"].status, "passed")  # catalog consistency
        self.assertEqual(by_code["WF014"].status, "passed")  # approval boundary
        self.assertEqual(by_code["WF016"].status, "passed")  # explicit trace deps
        self.assertEqual(by_code["WF021"].status, "passed")  # no infra-file binding

    def test_trace0002_bound_to_immutable_final_manifest(self):
        _, wf = vw.validate(REAL_WF, self.idx)
        binding = {b["task_id"]: (b["output"], b["version"]) for b in wf.bindings}
        self.assertEqual(binding["TASK-TRACE-0002"], ("reports/final-manifest.yaml", "0.2.0"))
        # the run-root manifest.yaml is NOT a task binding
        self.assertNotIn("manifest.yaml", {b["output"] for b in wf.bindings})


class TestNegativeFixtures(ValidatorTestBase):
    def assert_fails_with(self, fixture_name, code):
        res = self.validate(FIXTURES / fixture_name)
        self.assertFalse(res.valid, msg=f"{fixture_name} should be invalid")
        self.assertIn(code, self.error_codes(res),
                      msg=f"{fixture_name} expected {code}; got {sorted(self.error_codes(res))}")

    def test_wf004_missing_task(self):
        self.assert_fails_with("wf004_missing_task.md", "WF004")

    def test_wf005_version_mismatch(self):
        self.assert_fails_with("wf005_version_mismatch.md", "WF005")

    def test_wf006_duplicate_task(self):
        self.assert_fails_with("wf006_duplicate_task.md", "WF006")

    def test_wf007_unknown_dependency(self):
        self.assert_fails_with("wf007_unknown_dep.md", "WF007")

    def test_wf008_cycle(self):
        self.assert_fails_with("wf008_cycle.md", "WF008")

    def test_wf009_missing_input(self):
        self.assert_fails_with("wf009_missing_input.md", "WF009")

    def test_wf010_duplicate_output(self):
        self.assert_fails_with("wf010_duplicate_output.md", "WF010")

    def test_wf011_legacy_root(self):
        self.assert_fails_with("wf011_legacy_root.md", "WF011")

    def test_wf013_bad_exit_state(self):
        self.assert_fails_with("wf013_bad_exit.md", "WF013")

    def test_wf014_production_after_approval(self):
        self.assert_fails_with("wf014_production_after_approval.md", "WF014")

    def test_wf015_missing_terminal_artifact(self):
        self.assert_fails_with("wf015_missing_terminal.md", "WF015")

    def test_wf016_vague_trace_dependency(self):
        self.assert_fails_with("wf016_vague_trace.md", "WF016")

    def test_wf017_private_chain_of_thought(self):
        self.assert_fails_with("wf017_private_cot.md", "WF017")

    def test_wf018_catalog_mismatch(self):
        self.assert_fails_with("wf018_catalog_mismatch.md", "WF018")

    # --- mechanical rules that previously lacked dedicated negative tests ---

    def test_wf002_missing_metadata(self):
        self.assert_fails_with("wf002_missing_metadata.md", "WF002")

    def test_wf012_order_violation(self):
        res = self.validate(FIXTURES / "wf012_order_violation.md")
        self.assertIn("WF012", self.error_codes(res))
        self.assertNotIn("WF008", self.error_codes(res),
                         msg="WF012 fixture must not also form a cycle")

    def test_wf019_bad_status(self):
        self.assert_fails_with("wf019_bad_status.md", "WF019")

    def test_wf020_missing_reference(self):
        self.assert_fails_with("wf020_missing_reference.md", "WF020")

    def test_wf021_task_bound_to_runtime_infra(self):
        # A task output bound to the runtime-owned manifest.yaml is rejected.
        self.assert_fails_with("wf021_infra_binding.md", "WF021")


class TestDuplicateWorkflowId(unittest.TestCase):
    def test_wf003_duplicate_workflow_id(self):
        dup_dir = FIXTURES / "dup_id"
        idx = vw.RepoIndex(
            repo_root=REPO_ROOT,
            tasks_dir=REPO_ROOT / "tasks",
            catalog_path=REPO_ROOT / "workflows" / "WORKFLOW_CATALOG.md",
            workflows_dir=dup_dir,   # both fixture files share workflow_id WF-DUP-0001
        )
        res, _ = vw.validate(dup_dir / "dup_a.md", idx)
        codes = {c.code for c in res.errors}
        self.assertIn("WF003", codes,
                      msg=f"expected WF003; got {sorted(codes)}")


class TestCliBehavior(ValidatorTestBase):
    def test_exit_code_zero_on_valid(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = vw.main([str(REAL_WF)])
        self.assertEqual(rc, 0)

    def test_exit_code_one_on_invalid(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = vw.main([str(FIXTURES / "wf008_cycle.md")])
        self.assertEqual(rc, 1)

    def test_exit_code_two_on_missing_file(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = vw.main([str(REPO_ROOT / "does-not-exist.md")])
        self.assertEqual(rc, 2)

    def test_json_output_is_parseable(self):
        import json
        buf = io.StringIO()
        with redirect_stdout(buf):
            vw.main([str(REAL_WF), "--format", "json"])
        data = json.loads(buf.getvalue())
        self.assertEqual(data["workflow_id"], "WF-REASON-0001")
        self.assertTrue(data["valid"])
        self.assertIn("summary", data)

    def test_validator_makes_no_repo_changes(self):
        before = {p: p.stat().st_mtime_ns for p in [REAL_WF, FIXTURES / "wf008_cycle.md"]}
        buf = io.StringIO()
        with redirect_stdout(buf):
            vw.main([str(REAL_WF)])
            vw.main([str(FIXTURES / "wf008_cycle.md")])
        after = {p: p.stat().st_mtime_ns for p in before}
        self.assertEqual(before, after, "validator must not modify files")


if __name__ == "__main__":
    unittest.main(verbosity=2)
