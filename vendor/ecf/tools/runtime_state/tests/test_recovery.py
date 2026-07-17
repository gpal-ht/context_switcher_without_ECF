"""Tests for read-only recovery inspection and explicit recovery application."""

import hashlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PKG))
sys.path.insert(0, str(_PKG.parent))

import storage as st          # noqa: E402
import transaction as tx      # noqa: E402
import recovery as rec        # noqa: E402
from models import (          # noqa: E402
    ManifestTask, RunLock, RunManifest, RunState, TaskLifecycle, TransactionPhase,
)

OUT = b"OUTPUT-BODY\n"
OSHA = hashlib.sha256(OUT).hexdigest()


def seed(root: Path) -> Path:
    run = root / "runs" / "RUN-R"
    run.mkdir(parents=True)
    tx.save_run_state(run, RunState(run_id="RUN-R", workflow_id="WF", workflow_version="0.1.0",
                                    provenance_mode="required", revision=0,
                                    task_states={"T": TaskLifecycle.NOT_STARTED}))
    tx.save_manifest(run, RunManifest(run_id="RUN-R", workflow_id="WF", workflow_version="0.1.0",
                                      revision=0, tasks=[ManifestTask(id="T", version="0.1.0",
                                      output="task_outputs/o.md")]))
    return run


def prov_text(sha=OSHA) -> str:
    return ("schema_version: 1\ntask_id: T\ntask_version: 0.1.0\ninputs: []\n"
            f"output:\n  path: task_outputs/o.md\n  sha256: {sha}\necf_version: v0.1\n")


class RecBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = seed(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def types(self, plan):
        return {c.type for c in plan.conditions}


class TestConsistent(RecBase):
    def test_clean_run_is_consistent(self):
        plan = rec.inspect_recovery(self.run)
        self.assertTrue(plan.consistent)


class TestCrashScenarios(RecBase):
    def test_staging_only_recoverable(self):
        # (1) crash before promotion: staged + validated, nothing promoted
        t = tx.begin_task_transaction(self.run, "T", "task_outputs/o.md",
                                      "provenance/T.yaml", owner="x")
        t.stage_output(OUT, "task_outputs/o.md", OSHA)
        t.stage_provenance(prov_text(), "provenance/T.yaml")
        t.validate()
        plan = rec.inspect_recovery(self.run)
        self.assertIn(rec.ConditionType.STAGING_ONLY, self.types(plan))
        # safe/automatic action available
        auto = [a for a in plan.actions if not a.requires_explicit_approval]
        self.assertTrue(auto)
        rec.apply_recovery(plan)  # applies only safe actions
        self.assertFalse((self.run / "staging" / t.journal.transaction_id / "output.bin").exists())

    def test_output_promoted_provenance_missing_detected(self):
        # (2) crash after output promotion, before provenance
        t = tx.begin_task_transaction(self.run, "T", "task_outputs/o.md",
                                      "provenance/T.yaml", owner="x")
        t.stage_output(OUT, "task_outputs/o.md", OSHA)
        t.stage_provenance(prov_text(), "provenance/T.yaml")
        t.validate()
        j = t.journal
        j.phase = TransactionPhase.COMMITTING
        tx._write_journal(self.run, j)
        st.atomic_promote(t.staging_dir / "output.bin",
                          self.run / "task_outputs" / "o.md", self.run)
        plan = rec.inspect_recovery(self.run)
        self.assertIn(rec.ConditionType.OUTPUT_NO_PROVENANCE, self.types(plan))
        self.assertIn(rec.ConditionType.JOURNAL_COMMITTING, self.types(plan))

    def test_promoted_state_stale_recoverable(self):
        # (3) crash after both promoted, before state update
        t = tx.begin_task_transaction(self.run, "T", "task_outputs/o.md",
                                      "provenance/T.yaml", owner="x")
        t.stage_output(OUT, "task_outputs/o.md", OSHA)
        t.stage_provenance(prov_text(), "provenance/T.yaml")
        t.validate()
        j = t.journal
        j.phase = TransactionPhase.COMMITTING
        tx._write_journal(self.run, j)
        st.atomic_promote(t.staging_dir / "output.bin", self.run / "task_outputs" / "o.md", self.run)
        st.atomic_promote(t.staging_dir / "provenance.yaml", self.run / "provenance" / "T.yaml", self.run)
        plan = rec.inspect_recovery(self.run)
        self.assertIn(rec.ConditionType.PROMOTED_STATE_STALE, self.types(plan))
        # explicit recovery restores consistency
        applied = rec.apply_recovery(plan, approve_explicit=True)
        self.assertTrue(applied)
        self.assertEqual(tx.load_run_state(self.run).task_states["T"], TaskLifecycle.COMPLETED)
        after = rec.inspect_recovery(self.run)
        self.assertTrue(after.consistent, msg=str(after.to_dict()))

    def test_revision_mismatch_detected(self):
        # (4)
        state = tx.load_run_state(self.run)
        state.revision = 3
        tx.save_run_state(self.run, state)  # manifest stays at 0
        plan = rec.inspect_recovery(self.run)
        self.assertIn(rec.ConditionType.REVISION_MISMATCH, self.types(plan))

    def test_running_no_transaction_detected(self):
        # (5)
        state = tx.load_run_state(self.run)
        state.task_states["T"] = TaskLifecycle.RUNNING
        state.active_task = "T"
        tx.save_run_state(self.run, state)
        plan = rec.inspect_recovery(self.run)
        self.assertIn(rec.ConditionType.RUNNING_NO_TXN, self.types(plan))
        rec.apply_recovery(plan, approve_explicit=True)
        self.assertEqual(tx.load_run_state(self.run).task_states["T"], TaskLifecycle.NOT_STARTED)

    def test_hash_mismatch_detected(self):
        # (8)
        t = tx.begin_task_transaction(self.run, "T", "task_outputs/o.md",
                                      "provenance/T.yaml", owner="x")
        t.stage_output(OUT, "task_outputs/o.md", OSHA)
        t.stage_provenance(prov_text(), "provenance/T.yaml")
        t.validate()
        j = t.journal
        j.phase = TransactionPhase.COMMITTING
        tx._write_journal(self.run, j)
        # promote DIFFERENT bytes than the recorded hash
        st.atomic_write_bytes(self.run / "task_outputs" / "o.md", b"TAMPERED\n")
        plan = rec.inspect_recovery(self.run)
        self.assertIn(rec.ConditionType.HASH_MISMATCH, self.types(plan))


class TestStaleLock(RecBase):
    def test_stale_lock_reported_not_removed(self):
        tx.acquire_run_lock(self.run, owner="ghost")
        old = datetime.now(timezone.utc) + timedelta(seconds=10000)  # inspect "far future" now
        plan = rec.inspect_recovery(self.run, lock_ttl_seconds=1, now=old)
        self.assertIn(rec.ConditionType.STALE_LOCK, self.types(plan))
        # read-only: lock still present after inspection
        self.assertIsNotNone(tx.read_lock(self.run))
        # apply without lock-removal approval leaves it in place
        rec.apply_recovery(plan, approve_explicit=True, allow_lock_removal=False)
        self.assertIsNotNone(tx.read_lock(self.run))
        # explicit removal
        rec.apply_recovery(plan, approve_explicit=True, allow_lock_removal=True)
        self.assertIsNone(tx.read_lock(self.run))


class TestReadOnly(RecBase):
    def test_inspect_is_read_only(self):
        # create a mismatch, snapshot, inspect, confirm no file changed
        state = tx.load_run_state(self.run)
        state.revision = 2
        tx.save_run_state(self.run, state)

        def snap():
            return {str(p): (p.stat().st_mtime_ns, p.stat().st_size)
                    for p in sorted(self.run.rglob("*")) if p.is_file()}
        before = snap()
        rec.inspect_recovery(self.run)
        self.assertEqual(before, snap())


if __name__ == "__main__":
    unittest.main(verbosity=2)
