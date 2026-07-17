"""
Runtime task-result transaction + single-run writer lock.

A transaction stages one task's output, provenance, manifest update, state
update, and trace-event metadata, then promotes them atomically. It NEVER
executes a task: callers (tests, or a future runner) supply staged content.

Atomicity is achieved with same-filesystem temp files and os.replace, a
transaction journal written before promotion, and compare-before-write revision
checks so state and manifest advance together with matching revisions.

The planner remains read-only; this module is the only writer.

Standard library only.
"""

from __future__ import annotations

import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from models import (
    ManifestTask, OutputStatus, RunLock, RunManifest, RunState, RunStatus,
    TaskLifecycle, TransactionJournal, TransactionPhase, TraceEvent,
    ValidationStatus,
)
import storage as st


class TransactionError(Exception):
    pass


class RevisionConflict(TransactionError):
    pass


class LockError(Exception):
    pass


class LockHeld(LockError):
    def __init__(self, lock: RunLock):
        self.lock = lock
        super().__init__(f"run lock already held by {lock.owner} since {lock.created_at}")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# State / manifest IO
# --------------------------------------------------------------------------- #

def load_run_state(run_dir: Path) -> RunState:
    p = Path(run_dir) / "state.yaml"
    if not p.is_file():
        raise TransactionError(f"run state not found: {p}")
    try:
        data = st.load_yaml(st.read_text(p))
    except Exception as exc:
        raise TransactionError(f"run state is unparseable: {exc}")
    if not isinstance(data, dict) or not data.get("run_id"):
        raise TransactionError("run state is invalid (missing run_id)")
    return RunState.from_dict(data)


def save_run_state(run_dir: Path, state: RunState) -> None:
    state.updated_at = _now()
    st.atomic_write_text(Path(run_dir) / "state.yaml", st.dump_yaml(state.to_dict()))


def load_manifest(run_dir: Path) -> RunManifest:
    p = Path(run_dir) / "manifest.yaml"
    if not p.is_file():
        raise TransactionError(f"manifest not found: {p}")
    try:
        data = st.load_yaml(st.read_text(p))
    except Exception as exc:
        raise TransactionError(f"manifest is unparseable: {exc}")
    return RunManifest.from_dict(data)


def save_manifest(run_dir: Path, manifest: RunManifest) -> None:
    st.atomic_write_text(Path(run_dir) / "manifest.yaml", st.dump_yaml(manifest.to_dict()))


# --------------------------------------------------------------------------- #
# Single-run writer lock
# --------------------------------------------------------------------------- #

def _lock_path(run_dir: Path) -> Path:
    return Path(run_dir) / "lock" / "lock.json"


def read_lock(run_dir: Path) -> RunLock | None:
    p = _lock_path(run_dir)
    if not p.is_file():
        return None
    try:
        return RunLock.from_dict(st.load_json(st.read_text(p)))
    except Exception:
        return None


def acquire_run_lock(run_dir: Path, owner: str, transaction_id: str = "") -> RunLock:
    """
    Acquire the single-run writer lock via an atomic exclusive create.
    Fails safely (LockHeld) when already held; never breaks a live lock.
    """
    p = _lock_path(run_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    lock = RunLock(owner=owner, created_at=_now(), transaction_id=transaction_id)
    try:
        fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        existing = read_lock(run_dir) or RunLock(owner="unknown", created_at="unknown")
        raise LockHeld(existing)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(st.dump_json(lock.to_dict()))
            fh.flush()
            os.fsync(fh.fileno())
    except BaseException:
        try:
            os.unlink(p)
        except OSError:
            pass
        raise
    return lock


def release_run_lock(run_dir: Path, owner: str) -> bool:
    p = _lock_path(run_dir)
    lock = read_lock(run_dir)
    if lock is None:
        return False
    if lock.owner != owner:
        raise LockError(f"cannot release a lock owned by {lock.owner}")
    os.unlink(p)
    return True


def lock_age_seconds(lock: RunLock, now: datetime | None = None) -> float | None:
    try:
        created = datetime.strptime(lock.created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
    now = now or datetime.now(timezone.utc)
    return (now - created).total_seconds()


def is_lock_stale(run_dir: Path, ttl_seconds: float, now: datetime | None = None) -> bool:
    lock = read_lock(run_dir)
    if lock is None:
        return False
    age = lock_age_seconds(lock, now)
    return age is not None and age > ttl_seconds


# --------------------------------------------------------------------------- #
# Journal IO
# --------------------------------------------------------------------------- #

def _journal_path(run_dir: Path, txn_id: str) -> Path:
    return Path(run_dir) / "staging" / txn_id / "journal.json"


def _write_journal(run_dir: Path, j: TransactionJournal) -> None:
    j.updated_at = _now()
    st.atomic_write_text(_journal_path(run_dir, j.transaction_id), st.dump_json(j.to_dict()))


def load_journal(run_dir: Path, txn_id: str) -> TransactionJournal:
    p = _journal_path(run_dir, txn_id)
    if not p.is_file():
        raise TransactionError(f"journal not found: {p}")
    return TransactionJournal.from_dict(st.load_json(st.read_text(p)))


def list_journals(run_dir: Path) -> list:
    staging = Path(run_dir) / "staging"
    out = []
    if staging.is_dir():
        for d in sorted(staging.iterdir()):
            jp = d / "journal.json"
            if jp.is_file():
                try:
                    out.append(TransactionJournal.from_dict(st.load_json(st.read_text(jp))))
                except Exception:
                    pass
    return out


# --------------------------------------------------------------------------- #
# Transaction
# --------------------------------------------------------------------------- #

class TaskTransaction:
    def __init__(self, run_dir: Path, journal: TransactionJournal, owner: str):
        self.run_dir = Path(run_dir)
        self.journal = journal
        self.owner = owner

    @property
    def staging_dir(self) -> Path:
        return self.run_dir / "staging" / self.journal.transaction_id

    def _event(self, name: str) -> None:
        self.journal.events.append({"event": name, "at": _now()})

    def stage_output(self, data: bytes, final_rel: str, output_sha256: str = "") -> None:
        final = st.safe_join(self.run_dir, final_rel)  # validates path safety
        self.journal.output_final = str(Path(final).relative_to(self.run_dir).as_posix())
        staged = self.staging_dir / "output.bin"
        staged.parent.mkdir(parents=True, exist_ok=True)
        st.atomic_write_bytes(staged, data)
        self.journal.output_sha256 = output_sha256 or st.sha256_file(staged)
        self.journal.phase = TransactionPhase.STAGED
        self._event(TraceEvent.OUTPUT_STAGED)
        _write_journal(self.run_dir, self.journal)

    def stage_provenance(self, text: str, final_rel: str) -> None:
        final = st.safe_join(self.run_dir, final_rel)
        self.journal.provenance_final = str(Path(final).relative_to(self.run_dir).as_posix())
        st.atomic_write_text(self.staging_dir / "provenance.yaml", text)
        self._event(TraceEvent.PROVENANCE_STAGED)
        _write_journal(self.run_dir, self.journal)

    def validate(self) -> tuple:
        """Verify staged files exist and the staged output hash is self-consistent."""
        reasons = []
        out = self.staging_dir / "output.bin"
        prov = self.staging_dir / "provenance.yaml"
        if not out.is_file():
            reasons.append("staged output missing")
        if not prov.is_file():
            reasons.append("staged provenance missing")
        if out.is_file():
            if st.sha256_file(out) != self.journal.output_sha256:
                reasons.append("staged output hash does not match journal")
            # cross-check against the staged provenance's recorded output sha
            if prov.is_file():
                rec = _provenance_output_sha(st.read_text(prov))
                if rec and rec.lower() != self.journal.output_sha256.lower():
                    reasons.append("staged provenance output hash disagrees with output")
        if reasons:
            return False, reasons
        self.journal.phase = TransactionPhase.VALIDATED
        self._event(TraceEvent.VALIDATION_PASSED)
        _write_journal(self.run_dir, self.journal)
        return True, []

    def commit(self) -> RunState:
        j = self.journal
        # idempotent no-op if already committed
        if j.phase == TransactionPhase.COMMITTED:
            return load_run_state(self.run_dir)
        if j.phase == TransactionPhase.COMMITTING:
            raise TransactionError("transaction is mid-commit; run recovery instead of re-committing")
        if j.phase != TransactionPhase.VALIDATED:
            raise TransactionError(f"cannot commit from phase '{j.phase}' (validate first)")

        # compare-before-write: no lost updates
        state = load_run_state(self.run_dir)
        if state.revision != j.expected_revision:
            raise RevisionConflict(
                f"state revision changed (expected {j.expected_revision}, found {state.revision})")
        manifest = load_manifest(self.run_dir)
        if manifest.revision != j.expected_revision:
            raise RevisionConflict(
                f"manifest revision {manifest.revision} != expected {j.expected_revision}")

        j.target_revision = j.expected_revision + 1
        j.phase = TransactionPhase.COMMITTING
        self._event(TraceEvent.COMMIT_STARTED)
        _write_journal(self.run_dir, j)  # durable intent before promotion

        # promote output, then provenance (atomic rename)
        out_final = st.safe_join(self.run_dir, j.output_final)
        st.atomic_promote(self.staging_dir / "output.bin", out_final, self.run_dir)
        self._event(TraceEvent.OUTPUT_PROMOTED)
        _write_journal(self.run_dir, j)

        prov_final = st.safe_join(self.run_dir, j.provenance_final)
        st.atomic_promote(self.staging_dir / "provenance.yaml", prov_final, self.run_dir)
        self._event(TraceEvent.PROVENANCE_PROMOTED)
        _write_journal(self.run_dir, j)

        # verify promoted output matches recorded hash BEFORE marking completed
        if st.sha256_file(out_final) != j.output_sha256:
            j.phase = TransactionPhase.RECOVERY_REQUIRED
            self._event(TraceEvent.RECOVERY_REQUIRED)
            _write_journal(self.run_dir, j)
            raise TransactionError("promoted output hash mismatch; recovery required")

        # state update (task completed only now)
        state.task_states[j.task_id] = TaskLifecycle.COMPLETED
        state.active_task = None
        state.revision = j.target_revision
        if state.run_status in (RunStatus.REQUESTED, RunStatus.ACCEPTED):
            state.run_status = RunStatus.RUNNING
        save_run_state(self.run_dir, state)
        self._event(TraceEvent.STATE_UPDATED)
        _write_journal(self.run_dir, j)

        # manifest update with the SAME revision
        mt = manifest.task(j.task_id) or ManifestTask(id=j.task_id)
        mt.status = TaskLifecycle.COMPLETED
        mt.output = j.output_final
        mt.output_status = OutputStatus.VERIFIED
        mt.provenance_path = j.provenance_final
        mt.output_hash = j.output_sha256
        mt.validation_status = ValidationStatus.VALID
        if manifest.task(j.task_id) is None:
            manifest.tasks.append(mt)
        manifest.revision = j.target_revision
        save_manifest(self.run_dir, manifest)
        self._event(TraceEvent.MANIFEST_UPDATED)

        j.phase = TransactionPhase.COMMITTED
        self._event(TraceEvent.TRANSACTION_COMMITTED)
        _write_journal(self.run_dir, j)
        return state

    def abort(self, reason: str = "") -> None:
        j = self.journal
        if j.phase in (TransactionPhase.COMMITTING, TransactionPhase.COMMITTED):
            raise TransactionError("cannot abort a transaction that has begun/finished committing")
        j.phase = TransactionPhase.ABORTED
        self._event(TraceEvent.TRANSACTION_ABORTED)
        _write_journal(self.run_dir, j)
        # remove staged (non-final) content only
        shutil.rmtree(self.staging_dir / "output.bin", ignore_errors=True)
        for f in ("output.bin", "provenance.yaml"):
            fp = self.staging_dir / f
            if fp.is_file():
                fp.unlink()


def begin_task_transaction(run_dir: Path, task_id: str, output_final_rel: str,
                           provenance_final_rel: str, owner: str,
                           transaction_id: str = "") -> TaskTransaction:
    run_dir = Path(run_dir)
    state = load_run_state(run_dir)
    txn_id = transaction_id or ("TXN-" + uuid.uuid4().hex[:12])
    # validate final paths early (path safety)
    st.safe_join(run_dir, output_final_rel)
    st.safe_join(run_dir, provenance_final_rel)
    journal = TransactionJournal(
        transaction_id=txn_id, run_id=state.run_id, task_id=task_id,
        phase=TransactionPhase.PREPARED, expected_revision=state.revision,
        output_final=output_final_rel, provenance_final=provenance_final_rel,
        created_at=_now(),
    )
    journal.events.append({"event": TraceEvent.TRANSACTION_STARTED, "at": _now()})
    # mark the task running in state (active task)
    state.task_states[task_id] = TaskLifecycle.RUNNING
    state.active_task = task_id
    if state.run_status in (RunStatus.REQUESTED, RunStatus.ACCEPTED):
        state.run_status = RunStatus.RUNNING
    save_run_state(run_dir, state)
    _write_journal(run_dir, journal)
    return TaskTransaction(run_dir, journal, owner)


def _provenance_output_sha(text: str) -> str | None:
    import re
    m = re.search(r"^output:\s*\n(?:^[ \t]+.*\n)*?^[ \t]+sha256:\s*(\S+)", text, re.M)
    return m.group(1) if m else None
