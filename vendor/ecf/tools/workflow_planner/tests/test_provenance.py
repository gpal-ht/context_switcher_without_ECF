"""
Tests for the hardened runtime provenance and stale-output model.

Covers explicit provenance modes, authoritative EKB requirements, canonical ECF
version identity, the separated (execution_state / output_validity /
planned_action) dimensions, and read-only behavior.

All ECF/EKB comparisons use a fixed injected EnvContext so results are
deterministic and independent of the live repository git state.
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_PLANNER_DIR = Path(__file__).resolve().parents[1]
_VALIDATOR_DIR = _PLANNER_DIR.parent / "workflow_validator"
_TOOLS = _PLANNER_DIR.parent
for _p in (str(_PLANNER_DIR), str(_VALIDATOR_DIR), str(_TOOLS)):
    sys.path.insert(0, _p)

import validate_workflow as vw          # noqa: E402
import planner                           # noqa: E402
import provenance                        # noqa: E402
import plan_workflow                     # noqa: E402
from models import (  # noqa: E402
    ExecutionState, OutputValidity, PlannedAction, PlanStatus, DisplayState,
)

REPO = Path(__file__).resolve().parents[3]
WF_PATH = REPO / "workflows" / "reasoning" / "WF-REASON-0001-engineering-recommendation.md"
FX = REPO / "acceptance_tests" / "fixtures" / "provenance"

ENV = provenance.EnvContext(
    ecf_version="v0.1", ecf_commit="TESTCOMMIT",
    ekb_version="v0.1-local", ekb_commit="TESTEKB",
)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = vw.load_workflow(WF_PATH)

    def plan(self, run_name, wf=None, env=ENV):
        rt = planner.RuntimeState(FX / run_name)
        return planner.compute_plan(wf or self.wf, rt, env=env, repo_root=REPO)

    def task(self, plan, tid):
        return next(t for t in plan.tasks if t.id == tid)


# ---------------------------------------------------------------- Fix 1: modes
class TestProvenanceModes(Base):
    def test_required_mode_valid(self):
        plan = self.plan("valid_run")
        t = self.task(plan, "TASK-CLASSIFY-0001")
        self.assertEqual(plan.provenance_mode, "required")
        self.assertEqual(t.execution_state, ExecutionState.COMPLETED)
        self.assertEqual(t.output_validity, OutputValidity.VALID)

    def test_required_mode_missing_provenance_dir_marks_stale(self):
        # required mode but no provenance record present -> missing -> stale
        plan = self.plan("missing_provenance_run")
        t = self.task(plan, "TASK-CLASSIFY-0001")
        self.assertEqual(t.output_validity, OutputValidity.MISSING)

    def test_missing_provenance_config_is_invalid_runtime(self):
        with self.assertRaises(planner.PlannerError):
            planner.RuntimeState(FX / "missing_config_run")

    def test_invalid_mode_value_is_invalid_runtime(self):
        with self.assertRaises(planner.PlannerError):
            planner.RuntimeState(FX / "invalid_mode_run")

    def test_explicit_legacy_mode(self):
        plan = self.plan("legacy_run")
        self.assertEqual(plan.provenance_mode, "legacy")
        t = self.task(plan, "TASK-CLASSIFY-0001")
        self.assertEqual(t.execution_state, ExecutionState.COMPLETED)
        self.assertEqual(t.output_validity, OutputValidity.UNKNOWN)

    def test_legacy_warning_text_and_json(self):
        # text
        buf = io.StringIO()
        with redirect_stdout(buf):
            plan_workflow.main([str(WF_PATH), "--run", str(FX / "legacy_run")])
        self.assertIn("WARNING", buf.getvalue())
        self.assertIn("legacy", buf.getvalue())
        # json
        import json
        buf = io.StringIO()
        with redirect_stdout(buf):
            plan_workflow.main([str(WF_PATH), "--run", str(FX / "legacy_run"), "--format", "json"])
        data = json.loads(buf.getvalue())
        self.assertEqual(data["provenance_mode"], "legacy")
        self.assertTrue(any("legacy" in w for w in data["warnings"]))

    def test_directory_presence_does_not_set_policy(self):
        # legacy_run has NO provenance/ dir yet is validly configured as legacy;
        # missing_config_run HAS outputs but no config -> error. Policy comes
        # from configuration, not directories.
        self.assertFalse((FX / "legacy_run" / "provenance").exists())
        self.assertEqual(self.plan("legacy_run").provenance_mode, "legacy")


# ------------------------------------------------------- Fix 2: EKB authority
class TestEkbAuthority(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ekb_wf = vw.load_workflow(FX / "ekb_workflow.md")

    def test_ekb_required_from_workflow_metadata(self):
        deps = provenance.parse_environment_dependencies(self.wf.text)
        self.assertTrue(provenance.ekb_required_for(deps, "TASK-RETRIEVE-0002"))
        self.assertFalse(provenance.ekb_required_for(deps, "TASK-CLASSIFY-0001"))

    def test_ekb_valid(self):
        t = self.task(self.plan("ekb_valid_run", wf=self.ekb_wf), "TASK-RETRIEVE-0002")
        self.assertEqual(t.output_validity, OutputValidity.VALID)

    def test_omitting_ekb_fields_cannot_bypass(self):
        t = self.task(self.plan("ekb_missing_run", wf=self.ekb_wf), "TASK-RETRIEVE-0002")
        self.assertEqual(t.output_validity, OutputValidity.STALE)
        self.assertIn("ekb_provenance_missing", {r["check"] for r in t.stale_reasons})

    def test_changed_ekb_marks_stale(self):
        t = self.task(self.plan("ekb_changed_run", wf=self.ekb_wf), "TASK-RETRIEVE-0002")
        self.assertEqual(t.output_validity, OutputValidity.STALE)
        self.assertIn("ekb_commit_changed", {r["check"] for r in t.stale_reasons})

    def test_unit_omission_cannot_bypass(self):
        # direct unit proof at the validator level
        prov = provenance.parse_provenance(
            "schema_version: 1\nworkflow_id: WF-EKB-0001\nworkflow_version: 0.1.0\n"
            "task_id: TASK-RETRIEVE-0002\ntask_version: 0.1.0\ninputs: []\n"
            "output:\n  path: x\n  sha256: " + "0" * 64 + "\n"
            "ecf_version: v0.1\necf_commit: TESTCOMMIT\n")
        reasons = provenance.validate_provenance(
            prov, task_id="TASK-RETRIEVE-0002", task_version="0.1.0",
            workflow_id="WF-EKB-0001", workflow_version="0.1.0",
            env=ENV, run_dir=FX / "ekb_missing_run", ekb_required=True, repo_root=REPO)
        self.assertIn("ekb_provenance_missing", {r.check for r in reasons})

    def test_missing_current_ekb_identity_is_config_error(self):
        env_no_ekb = provenance.EnvContext(ecf_version="v0.1", ecf_commit="TESTCOMMIT",
                                           ekb_version=None, ekb_commit=None)
        prov = provenance.parse_provenance(
            "task_id: TASK-RETRIEVE-0002\ntask_version: 0.1.0\ninputs: []\n"
            "output:\n  path: x\n  sha256: " + "0" * 64 + "\n"
            "ecf_version: v0.1\nekb_version: v0.1-local\n")
        with self.assertRaises(provenance.PlannerConfigError):
            provenance.validate_provenance(
                prov, task_id="TASK-RETRIEVE-0002", task_version="0.1.0",
                workflow_id="", workflow_version="", env=env_no_ekb,
                run_dir=FX / "ekb_changed_run", ekb_required=True, repo_root=REPO)


# --------------------------------------------------- Fix 3: ECF version source
class TestEcfVersionSource(Base):
    def test_ecf_version_from_canonical_file_not_readme(self):
        env = provenance.EnvContext.from_repo(REPO)
        self.assertEqual(env.ecf_version, "v0.1")
        # canonical file exists; README is not the source
        self.assertTrue((REPO / "ecf-version.yaml").is_file())

    def test_missing_current_ecf_identity_is_config_error(self):
        env_no_ecf = provenance.EnvContext(ecf_version=None)
        prov = provenance.parse_provenance(
            "task_id: T\ntask_version: 0.1.0\ninputs: []\n"
            "output:\n  path: x\n  sha256: " + "0" * 64 + "\necf_version: v0.1\n")
        with self.assertRaises(provenance.PlannerConfigError):
            provenance.validate_provenance(
                prov, task_id="T", task_version="0.1.0", workflow_id="",
                workflow_version="", env=env_no_ecf, run_dir=FX / "valid_run")

    def test_changed_ecf_marks_stale(self):
        t = self.task(self.plan("changed_ecf_run"), "TASK-CLASSIFY-0001")
        self.assertEqual(t.output_validity, OutputValidity.STALE)
        self.assertIn("ecf_commit_changed", {r["check"] for r in t.stale_reasons})


# --------------------------------------------- Fix 4: separated state dimensions
class TestSeparatedDimensions(Base):
    def test_stale_completed_has_three_distinct_dimensions(self):
        t = self.task(self.plan("changed_input_run"), "TASK-CLASSIFY-0002")
        self.assertEqual(t.execution_state, ExecutionState.COMPLETED)  # it ran
        self.assertEqual(t.output_validity, OutputValidity.STALE)       # output invalid
        self.assertEqual(t.planned_action, PlannedAction.RERUN)         # action
        self.assertEqual(t.state, DisplayState.STALE)                   # derived label

    def test_not_started_downstream_dimensions(self):
        t = self.task(self.plan("stale_dependency_run"), "TASK-RETRIEVE-0001")
        self.assertEqual(t.execution_state, ExecutionState.NOT_STARTED)
        self.assertEqual(t.output_validity, OutputValidity.NOT_APPLICABLE)
        self.assertEqual(t.planned_action, PlannedAction.BLOCKED)

    def test_rerun_required_cascade_own_output_still_valid(self):
        t = self.task(self.plan("changed_output_run"), "TASK-CLASSIFY-0002")
        self.assertEqual(t.execution_state, ExecutionState.COMPLETED)
        self.assertEqual(t.output_validity, OutputValidity.VALID)    # its own output is fine
        self.assertEqual(t.planned_action, PlannedAction.RERUN)      # but must rerun
        self.assertEqual(t.state, DisplayState.RERUN_REQUIRED)

    def test_json_exposes_three_dimensions(self):
        import json
        buf = io.StringIO()
        with redirect_stdout(buf):
            plan_workflow.main([str(WF_PATH), "--run", str(FX / "changed_output_run"),
                                "--format", "json"])
        data = json.loads(buf.getvalue())
        t = next(x for x in data["tasks"] if x["id"] == "TASK-CLASSIFY-0001")
        self.assertIn("execution_state", t)
        self.assertIn("output_validity", t)
        self.assertIn("planned_action", t)
        self.assertEqual(t["output_validity"], "stale")

    def test_independent_branch_unaffected(self):
        wf2 = vw.load_workflow(FX / "indep_workflow.md")
        plan = self.plan("indep_run", wf=wf2)
        st = {t.id: (t.output_validity) for t in plan.tasks}
        self.assertEqual(st["TASK-CLASSIFY-0001"], OutputValidity.VALID)
        self.assertEqual(st["TASK-CLASSIFY-0002"], OutputValidity.STALE)
        self.assertEqual(st["TASK-RETRIEVE-0001"], OutputValidity.VALID)  # unaffected


class TestReadOnly(Base):
    def test_planner_does_not_modify_fixtures(self):
        target = FX / "changed_output_run"
        def snap():
            return {str(p): (p.stat().st_mtime_ns, p.stat().st_size)
                    for p in sorted(target.rglob("*")) if p.is_file()}
        before = snap()
        self.plan("changed_output_run")
        self.assertEqual(before, snap())


if __name__ == "__main__":
    unittest.main(verbosity=2)
