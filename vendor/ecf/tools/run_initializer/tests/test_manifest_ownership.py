"""
Regression tests for the manifest-output ownership fix.

TASK-TRACE-0002 is bound to the immutable, task-owned reports/final-manifest.yaml,
not the runtime-owned run-root manifest.yaml. These tests prove the planner no
longer marks TASK-TRACE-0002 stale in a fresh (or ordinarily progressed) run, and
that the provenance model tracks the task's ACTUAL output correctly.

All work happens in temporary directories; no persistent repository runtime run is
created and no live Claude is invoked.
"""

from __future__ import annotations

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
from run_initializer.models import InitRequest          # noqa: E402

WF = REPO / "workflows" / "reasoning" / "WF-REASON-0001-engineering-recommendation.md"
WR = REPO / "acceptance_tests" / "fixtures" / "run_initializer" / "WR-0001-valid.md"
INTENT_FIXTURE = (REPO / "acceptance_tests" / "fixtures" / "task_runner"
                  / "engineering-intent.yaml")
TRACE_TASK = "TASK-TRACE-0002"
FINAL_MANIFEST = "reports/final-manifest.yaml"


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
        self._tmp = Path(tempfile.mkdtemp(prefix="ecf-mo-test-"))
        self.run_root = self._tmp / "runs"
        self.addCleanup(_rmtree, self._tmp)

    def _init(self, run_id="RUN-REASON-MO-0001"):
        return initialize_run(InitRequest(
            workflow_path=str(WF), work_request_path=str(WR), run_id=run_id,
            run_root=str(self.run_root), repo_root=str(REPO)))

    def _plan(self, run_dir):
        _, wf = I.vw.validate(WF, I.vw.RepoIndex(
            REPO, REPO / "tasks", REPO / "workflows" / "WORKFLOW_CATALOG.md",
            REPO / "workflows"))
        rt = I.pl.RuntimeState(Path(run_dir))
        env = I.prov.EnvContext.from_repo(REPO)
        return I.pl.compute_plan(wf, rt, env=env, repo_root=REPO), wf

    def _task(self, plan, tid):
        return next(t for t in plan.tasks if t.id == tid)


class TestManifestOwnership(Base):
    def test_binding_is_immutable_final_manifest(self):
        _, wf = self._plan(self._init().run_dir)
        out = {b["task_id"]: b["output"] for b in wf.bindings}
        self.assertEqual(out[TRACE_TASK], FINAL_MANIFEST)
        self.assertNotIn("manifest.yaml", set(out.values()))

    def test_fresh_run_trace0002_blocked_not_stale(self):
        res = self._init()
        plan, _ = self._plan(res.run_dir)
        t = self._task(plan, TRACE_TASK)
        self.assertEqual(t.state, "blocked")
        self.assertNotEqual(t.state, "stale")
        self.assertEqual(t.output_validity, "not_applicable")
        # no non-fresh tasks at all
        self.assertEqual(plan.stale, [])
        self.assertEqual(plan.rerun_required, [])

    def test_final_manifest_absent_and_not_provenance_tracked_before_exec(self):
        res = self._init()
        rd = Path(res.run_dir)
        self.assertFalse((rd / "reports" / "final-manifest.yaml").exists())
        self.assertFalse((rd / "provenance" / f"{TRACE_TASK}.yaml").exists())
        # runtime manifest.yaml exists (infrastructure) but is NOT trace-0002's output
        self.assertTrue((rd / "manifest.yaml").is_file())

    def test_runtime_manifest_mutation_does_not_affect_trace0002_validity(self):
        res = self._init()
        rd = Path(res.run_dir)
        before = self._task(self._plan(rd)[0], TRACE_TASK).state
        # mutate the runtime-owned manifest.yaml (append a comment)
        mp = rd / "manifest.yaml"
        mp.write_text(mp.read_text(encoding="utf-8") + "\n# runtime mutation\n",
                      encoding="utf-8")
        after = self._task(self._plan(rd)[0], TRACE_TASK).state
        self.assertEqual(before, "blocked")
        self.assertEqual(after, "blocked")   # unaffected by runtime-manifest churn

    def test_after_classify0001_trace0002_still_blocked_not_stale(self):
        res = self._init(run_id="RUN-REASON-MO-ACCEPT-0001")
        rd = Path(res.run_dir)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        run_task = _TOOLS / "task_runner" / "run_task.py"
        proc = subprocess.run(
            [sys.executable, str(run_task), str(WF), "--run", str(rd),
             "--task", "TASK-CLASSIFY-0001", "--executor", "fixture",
             "--fixture", str(INTENT_FIXTURE)],
            capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        plan, _ = self._plan(rd)
        # next task ready, but TASK-TRACE-0002 remains blocked (never stale)
        self.assertIn("TASK-CLASSIFY-0002", plan.ready)
        t = self._task(plan, TRACE_TASK)
        self.assertEqual(t.state, "blocked")
        self.assertNotIn(TRACE_TASK, plan.stale)

    def test_trace0003_consumes_final_manifest(self):
        # input/output continuity: TASK-TRACE-0003 (finalize) reads the immutable
        # final manifest snapshot produced by TASK-TRACE-0002.
        spec = (REPO / "tasks" / "traceability"
                / "TASK-TRACE-0003-finalize-reasoning-run.md").read_text(encoding="utf-8")
        self.assertIn("reports/final-manifest.yaml", spec)


class TestExecutedTrace0002Provenance(Base):
    """
    Prove the provenance model tracks TASK-TRACE-0002's ACTUAL output
    (reports/final-manifest.yaml) once it executes: a missing/changed record for
    that output is stale, while runtime-manifest churn is irrelevant.
    """

    def _write_executed_trace0002(self, rd: Path):
        """Materialize a completed TASK-TRACE-0002 with a valid provenance record."""
        fp = I.rt_storage  # runtime_state.storage (fingerprint helpers via fp)
        from artifact_fingerprint import fingerprint as afp
        out_rel = FINAL_MANIFEST
        out_path = rd / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_bytes = b"run_id: RUN-REASON-MO-EXEC-0001\nfinal_manifest: true\n"
        out_path.write_bytes(out_bytes)
        osha = afp.sha256_bytes(out_bytes)
        env = I.prov.EnvContext.from_repo(REPO)
        _, wf = I.vw.validate(WF, I.vw.RepoIndex(
            REPO, REPO / "tasks", REPO / "workflows" / "WORKFLOW_CATALOG.md",
            REPO / "workflows"))
        wf_ver = wf.front_matter.get("version", "")
        prov_text = (
            "schema_version: 1\n"
            f"run_id: {rd.name}\n"
            "work_request_id: WR-0001\n"
            "workflow_id: WF-REASON-0001\n"
            f"workflow_version: {wf_ver}\n"
            f"task_id: {TRACE_TASK}\n"
            "task_version: 0.2.0\n"
            "inputs: []\n"
            "output:\n"
            f"  path: {out_rel}\n"
            f"  sha256: {osha}\n"
            f"ecf_version: {env.ecf_version or ''}\n"
            f"ecf_commit: {env.ecf_commit or ''}\n"
        )
        (rd / "provenance" / f"{TRACE_TASK}.yaml").write_text(prov_text, encoding="utf-8")
        return osha, env

    def _validate_trace0002(self, rd, env):
        return I.prov.load_and_validate(
            rd / "provenance" / f"{TRACE_TASK}.yaml",
            task_id=TRACE_TASK, task_version="0.2.0",
            workflow_id="WF-REASON-0001",
            workflow_version=I.vw.load_workflow(WF).front_matter.get("version", ""),
            env=env, run_dir=rd, ekb_required=False, repo_root=REPO)

    def test_executed_output_valid_then_stale_on_hash_change(self):
        res = self._init(run_id="RUN-REASON-MO-EXEC-0001")
        rd = Path(res.run_dir)
        _, env = self._write_executed_trace0002(rd)

        # 1) valid record for the actual output
        self.assertEqual(self._validate_trace0002(rd, env), [])

        # 2) missing provenance for the ACTUAL output -> stale (missing)
        prov_file = rd / "provenance" / f"{TRACE_TASK}.yaml"
        saved = prov_file.read_text(encoding="utf-8")
        prov_file.unlink()
        reasons = self._validate_trace0002(rd, env)
        self.assertTrue(any(r.check == "missing_provenance" for r in reasons))
        prov_file.write_text(saved, encoding="utf-8")

        # 3) changed final-manifest output hash -> stale
        (rd / FINAL_MANIFEST).write_bytes(b"tampered: true\n")
        reasons = self._validate_trace0002(rd, env)
        self.assertTrue(any(r.check == "output_hash_changed" for r in reasons))

    def test_runtime_manifest_revision_change_does_not_invalidate(self):
        res = self._init(run_id="RUN-REASON-MO-EXEC-0002")
        rd = Path(res.run_dir)
        _, env = self._write_executed_trace0002(rd)
        self.assertEqual(self._validate_trace0002(rd, env), [])
        # bump the runtime manifest revision (runtime churn) -> final-manifest valid
        mp = rd / "manifest.yaml"
        mp.write_text(mp.read_text(encoding="utf-8").replace("revision: 0", "revision: 9"),
                      encoding="utf-8")
        self.assertEqual(self._validate_trace0002(rd, env), [])


if __name__ == "__main__":
    unittest.main()
