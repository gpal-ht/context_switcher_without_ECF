"""Tests for the runtime task-result transaction and single-run writer lock."""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PKG))
sys.path.insert(0, str(_PKG.parent))

import storage as st          # noqa: E402
import transaction as tx      # noqa: E402
from models import (          # noqa: E402
    ManifestTask, RunManifest, RunState, TaskLifecycle, TransactionPhase,
)

OUT = b"OUTPUT-BODY\n"
OSHA = hashlib.sha256(OUT).hexdigest()


def seed_run(root: Path, rev: int = 0) -> Path:
    run = root / "runs" / "RUN-T"
    run.mkdir(parents=True)
    tx.save_run_state(run, RunState(
        run_id="RUN-T", work_request_id="WR-1", workflow_id="WF", workflow_version="0.1.0",
        provenance_mode="required", revision=rev, task_states={"T": TaskLifecycle.NOT_STARTED}))
    tx.save_manifest(run, RunManifest(
        run_id="RUN-T", workflow_id="WF", workflow_version="0.1.0", revision=rev,
        tasks=[ManifestTask(id="T", version="0.1.0", output="task_outputs/o.md")]))
    return run


def provenance_text(sha=OSHA) -> str:
    return ("schema_version: 1\ntask_id: T\ntask_version: 0.1.0\ninputs: []\n"
            f"output:\n  path: task_outputs/o.md\n  sha256: {sha}\necf_version: v0.1\n")


class TxBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = seed_run(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def staged_txn(self):
        t = tx.begin_task_transaction(self.run, "T", "task_outputs/o.md",
                                      "provenance/T.yaml", owner="tester")
        t.stage_output(OUT, "task_outputs/o.md", OSHA)
        t.stage_provenance(provenance_text(), "provenance/T.yaml")
        return t


class TestLoad(TxBase):
    def test_state_and_manifest_load(self):
        self.assertEqual(tx.load_run_state(self.run).revision, 0)
        self.assertEqual(tx.load_manifest(self.run).revision, 0)

    def test_invalid_state_fails_safely(self):
        st.atomic_write_text(self.run / "state.yaml", "not: [a valid : state")
        with self.assertRaises(tx.TransactionError):
            tx.load_run_state(self.run)


class TestLock(TxBase):
    def test_lock_prevents_concurrent_writer(self):
        tx.acquire_run_lock(self.run, owner="a")
        with self.assertRaises(tx.LockHeld):
            tx.acquire_run_lock(self.run, owner="b")

    def test_release_requires_owner(self):
        tx.acquire_run_lock(self.run, owner="a")
        with self.assertRaises(tx.LockError):
            tx.release_run_lock(self.run, owner="b")
        self.assertTrue(tx.release_run_lock(self.run, owner="a"))


class TestTransaction(TxBase):
    def test_stage_does_not_touch_final(self):
        self.staged_txn()
        self.assertFalse((self.run / "task_outputs" / "o.md").exists())
        self.assertFalse((self.run / "provenance" / "T.yaml").exists())

    def test_completed_only_after_promotion(self):
        t = self.staged_txn()
        # before commit the task is running, not completed
        self.assertEqual(tx.load_run_state(self.run).task_states["T"], TaskLifecycle.RUNNING)
        t.validate()
        t.commit()
        self.assertEqual(tx.load_run_state(self.run).task_states["T"], TaskLifecycle.COMPLETED)
        self.assertTrue((self.run / "task_outputs" / "o.md").is_file())
        self.assertTrue((self.run / "provenance" / "T.yaml").is_file())

    def test_revisions_increment_together(self):
        t = self.staged_txn(); t.validate(); t.commit()
        self.assertEqual(tx.load_run_state(self.run).revision, 1)
        self.assertEqual(tx.load_manifest(self.run).revision, 1)

    def test_validation_failure_aborts_without_final_changes(self):
        t = tx.begin_task_transaction(self.run, "T", "task_outputs/o.md",
                                      "provenance/T.yaml", owner="tester")
        t.stage_output(OUT, "task_outputs/o.md", OSHA)
        t.stage_provenance(provenance_text(sha="0" * 64), "provenance/T.yaml")  # disagrees
        ok, reasons = t.validate()
        self.assertFalse(ok)
        with self.assertRaises(tx.TransactionError):
            t.commit()  # cannot commit unvalidated
        self.assertFalse((self.run / "task_outputs" / "o.md").exists())

    def test_revision_conflict_prevents_commit(self):
        t = self.staged_txn(); t.validate()
        # a concurrent writer advances the revision
        other = tx.load_run_state(self.run)
        other.revision = 5
        tx.save_run_state(self.run, other)
        with self.assertRaises(tx.RevisionConflict):
            t.commit()

    def test_commit_is_idempotent(self):
        t = self.staged_txn(); t.validate(); t.commit()
        rev = tx.load_run_state(self.run).revision
        t.commit()  # no-op
        self.assertEqual(tx.load_run_state(self.run).revision, rev)

    def test_no_path_escape(self):
        with self.assertRaises(st.PathSafetyError):
            tx.begin_task_transaction(self.run, "T", "../evil.md",
                                      "provenance/T.yaml", owner="tester")


if __name__ == "__main__":
    unittest.main(verbosity=2)
