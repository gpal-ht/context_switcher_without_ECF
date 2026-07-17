"""
Read-only recovery inspection and explicit recovery planning.

`inspect_recovery` NEVER modifies the run — it detects inconsistency conditions
and returns a plan. `apply_recovery` performs repairs only when explicitly
called, and only the actions the plan authorizes. Nothing is repaired on read.

Standard library only.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from models import (
    OutputStatus, RunStatus, TaskLifecycle, TransactionPhase, ValidationStatus,
)
import storage as st
import transaction as tx


class ConditionType:
    STAGING_ONLY = "staging_exists_nothing_promoted"
    OUTPUT_NO_PROVENANCE = "output_promoted_provenance_missing"
    PROMOTED_STATE_STALE = "output_and_provenance_promoted_state_not_updated"
    REVISION_MISMATCH = "state_manifest_revision_mismatch"
    RUNNING_NO_TXN = "task_running_no_active_transaction"
    JOURNAL_COMMITTING = "journal_committing_after_termination"
    STALE_LOCK = "stale_lock_exists"
    HASH_MISMATCH = "output_hash_differs_from_provenance"


class ActionType:
    ABORT_STAGING = "discard_staging"                 # safe, automatic-eligible
    FINALIZE_STATE = "finalize_state_and_manifest"    # explicit
    RESET_RUNNING = "reset_running_task"              # explicit
    REMOVE_STALE_LOCK = "remove_stale_lock"           # explicit (documented rule)
    MANUAL = "manual_investigation_required"          # explicit, human


@dataclass
class RecoveryCondition:
    type: str
    detail: str = ""
    transaction_id: str = ""
    task_id: str = ""


@dataclass
class RecoveryAction:
    type: str
    detail: str = ""
    transaction_id: str = ""
    task_id: str = ""
    requires_explicit_approval: bool = True


@dataclass
class RecoveryPlan:
    run_dir: str
    consistent: bool = True
    conditions: list = field(default_factory=list)   # list[RecoveryCondition]
    actions: list = field(default_factory=list)      # list[RecoveryAction]

    def to_dict(self) -> dict:
        return {
            "run_dir": self.run_dir,
            "consistent": self.consistent,
            "conditions": [c.__dict__ for c in self.conditions],
            "actions": [a.__dict__ for a in self.actions],
        }


def inspect_recovery(run_dir: Path, lock_ttl_seconds: float = 3600,
                     now: datetime | None = None) -> RecoveryPlan:
    """Read-only. Detect inconsistency conditions and produce a recovery plan."""
    run_dir = Path(run_dir)
    plan = RecoveryPlan(run_dir=str(run_dir))
    now = now or datetime.now(timezone.utc)

    try:
        state = tx.load_run_state(run_dir)
    except tx.TransactionError as exc:
        plan.consistent = False
        plan.conditions.append(RecoveryCondition("invalid_state", str(exc)))
        plan.actions.append(RecoveryAction(ActionType.MANUAL, str(exc)))
        return plan
    try:
        manifest = tx.load_manifest(run_dir)
    except tx.TransactionError as exc:
        plan.consistent = False
        plan.conditions.append(RecoveryCondition("invalid_manifest", str(exc)))
        plan.actions.append(RecoveryAction(ActionType.MANUAL, str(exc)))
        return plan

    # (4) state/manifest revision mismatch
    if state.revision != manifest.revision:
        plan.conditions.append(RecoveryCondition(
            ConditionType.REVISION_MISMATCH,
            f"state.revision={state.revision} manifest.revision={manifest.revision}"))
        plan.actions.append(RecoveryAction(
            ActionType.MANUAL,
            "state and manifest revisions disagree; reconcile from journals"))

    # (7) stale lock
    lock = tx.read_lock(run_dir)
    if lock is not None:
        age = tx.lock_age_seconds(lock, now)
        if age is not None and age > lock_ttl_seconds:
            plan.conditions.append(RecoveryCondition(
                ConditionType.STALE_LOCK, f"lock age {int(age)}s > ttl {int(lock_ttl_seconds)}s"))
            plan.actions.append(RecoveryAction(
                ActionType.REMOVE_STALE_LOCK,
                f"lock held by {lock.owner} since {lock.created_at}",
                requires_explicit_approval=True))

    # (5) task running with no active transaction journal
    running = [t for t, s in state.task_states.items() if s == TaskLifecycle.RUNNING]
    live_txn_tasks = {j.task_id for j in tx.list_journals(run_dir)
                      if j.phase not in (TransactionPhase.COMMITTED, TransactionPhase.ABORTED)}
    for t in running:
        if t not in live_txn_tasks:
            plan.conditions.append(RecoveryCondition(
                ConditionType.RUNNING_NO_TXN, task_id=t,
                detail=f"task {t} is running but has no active transaction"))
            plan.actions.append(RecoveryAction(
                ActionType.RESET_RUNNING, task_id=t,
                detail=f"reset {t} to not_started"))

    # per-transaction journal analysis
    for j in tx.list_journals(run_dir):
        staging = run_dir / "staging" / j.transaction_id
        out_final = (run_dir / j.output_final) if j.output_final else None
        prov_final = (run_dir / j.provenance_final) if j.provenance_final else None
        out_promoted = bool(out_final and out_final.is_file())
        prov_promoted = bool(prov_final and prov_final.is_file())

        if j.phase in (TransactionPhase.COMMITTED, TransactionPhase.ABORTED):
            continue

        # (6) journal says committing after termination
        if j.phase == TransactionPhase.COMMITTING:
            plan.conditions.append(RecoveryCondition(
                ConditionType.JOURNAL_COMMITTING, transaction_id=j.transaction_id,
                task_id=j.task_id, detail="journal phase 'committing' with no completion"))

        # (1) staging exists, nothing promoted
        if staging.is_dir() and not out_promoted and not prov_promoted \
                and j.phase in (TransactionPhase.PREPARED, TransactionPhase.STAGED,
                                TransactionPhase.VALIDATED):
            plan.conditions.append(RecoveryCondition(
                ConditionType.STAGING_ONLY, transaction_id=j.transaction_id,
                task_id=j.task_id, detail="staging present, nothing promoted"))
            plan.actions.append(RecoveryAction(
                ActionType.ABORT_STAGING, transaction_id=j.transaction_id,
                detail="discard staging (no final files were written)",
                requires_explicit_approval=False))

        # (2) output promoted, provenance missing
        if out_promoted and not prov_promoted:
            plan.conditions.append(RecoveryCondition(
                ConditionType.OUTPUT_NO_PROVENANCE, transaction_id=j.transaction_id,
                task_id=j.task_id, detail="output promoted but provenance absent"))
            plan.actions.append(RecoveryAction(
                ActionType.MANUAL, transaction_id=j.transaction_id,
                detail="promote staged provenance or roll back output (explicit)"))

        # (8) promoted output hash differs from journal/provenance
        if out_promoted and j.output_sha256:
            if st.sha256_file(out_final) != j.output_sha256:
                plan.conditions.append(RecoveryCondition(
                    ConditionType.HASH_MISMATCH, transaction_id=j.transaction_id,
                    task_id=j.task_id, detail="promoted output hash != journal hash"))
                plan.actions.append(RecoveryAction(
                    ActionType.MANUAL, transaction_id=j.transaction_id,
                    detail="output hash mismatch; do not mark completed"))

        # (3) output+provenance promoted and verified, but state not updated
        if out_promoted and prov_promoted \
                and state.task_states.get(j.task_id) != TaskLifecycle.COMPLETED:
            if not j.output_sha256 or st.sha256_file(out_final) == j.output_sha256:
                plan.conditions.append(RecoveryCondition(
                    ConditionType.PROMOTED_STATE_STALE, transaction_id=j.transaction_id,
                    task_id=j.task_id, detail="output+provenance promoted; state not finalized"))
                plan.actions.append(RecoveryAction(
                    ActionType.FINALIZE_STATE, transaction_id=j.transaction_id,
                    task_id=j.task_id, detail="finalize state+manifest to target revision"))

    plan.consistent = len(plan.conditions) == 0
    return plan


def apply_recovery(plan: RecoveryPlan, approve_explicit: bool = False,
                   allow_lock_removal: bool = False) -> list:
    """
    Apply the plan's actions. Read-only actions are never taken here; this only
    performs the repairs the plan authorized, and explicit ones only when
    `approve_explicit=True`. Returns the list of applied action descriptions.

    Nothing is repaired unless this function is explicitly called.
    """
    run_dir = Path(plan.run_dir)
    applied = []
    for a in plan.actions:
        if a.requires_explicit_approval and not approve_explicit:
            continue
        if a.type == ActionType.ABORT_STAGING:
            staging = run_dir / "staging" / a.transaction_id
            j = tx.load_journal(run_dir, a.transaction_id)
            j.phase = TransactionPhase.ABORTED
            tx._write_journal(run_dir, j)
            for f in ("output.bin", "provenance.yaml"):
                fp = staging / f
                if fp.is_file():
                    fp.unlink()
            applied.append(f"discarded staging for {a.transaction_id}")
        elif a.type == ActionType.RESET_RUNNING:
            state = tx.load_run_state(run_dir)
            if state.task_states.get(a.task_id) == TaskLifecycle.RUNNING:
                state.task_states[a.task_id] = TaskLifecycle.NOT_STARTED
                if state.active_task == a.task_id:
                    state.active_task = None
                state.revision += 1
                manifest = tx.load_manifest(run_dir)
                manifest.revision = state.revision
                tx.save_run_state(run_dir, state)
                tx.save_manifest(run_dir, manifest)
                applied.append(f"reset running task {a.task_id}")
        elif a.type == ActionType.FINALIZE_STATE:
            j = tx.load_journal(run_dir, a.transaction_id)
            out_final = tx.st.safe_join(run_dir, j.output_final)
            if tx.st.sha256_file(out_final) != j.output_sha256:
                applied.append(f"skipped finalize for {a.transaction_id}: hash mismatch")
                continue
            state = tx.load_run_state(run_dir)
            manifest = tx.load_manifest(run_dir)
            target = max(state.revision, manifest.revision, j.expected_revision) + 1
            state.task_states[j.task_id] = TaskLifecycle.COMPLETED
            if state.active_task == j.task_id:
                state.active_task = None
            state.revision = target
            mt = manifest.task(j.task_id)
            if mt is None:
                from models import ManifestTask
                mt = ManifestTask(id=j.task_id)
                manifest.tasks.append(mt)
            mt.status = TaskLifecycle.COMPLETED
            mt.output = j.output_final
            mt.output_status = OutputStatus.VERIFIED
            mt.provenance_path = j.provenance_final
            mt.output_hash = j.output_sha256
            mt.validation_status = ValidationStatus.VALID
            manifest.revision = target
            tx.save_run_state(run_dir, state)
            tx.save_manifest(run_dir, manifest)
            j.phase = TransactionPhase.COMMITTED
            tx._write_journal(run_dir, j)
            applied.append(f"finalized state+manifest for {a.transaction_id} at revision {target}")
        elif a.type == ActionType.REMOVE_STALE_LOCK:
            if not allow_lock_removal:
                continue
            p = run_dir / "lock" / "lock.json"
            if p.is_file():
                p.unlink()
                applied.append("removed stale lock")
    return applied


# --------------------------------------------------------------------------- #
# Read-only CLI (used by scripts/inspect-runtime-state.ps1)
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    """
    Inspect a run directory. Read-only by default. Exit codes:
      0  consistent
      1  inconsistent (recovery conditions present)
      2  unrecoverable / invalid runtime (cannot inspect)
    """
    import argparse
    import json as _json
    parser = argparse.ArgumentParser(description="Inspect ECF runtime state (read-only).")
    parser.add_argument("run_dir")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--ttl", type=float, default=3600.0, help="stale-lock TTL seconds")
    parser.add_argument("--apply", action="store_true",
                        help="apply safe recovery actions (explicit; not read-only)")
    parser.add_argument("--allow-lock-removal", action="store_true",
                        help="permit removal of a stale lock during --apply")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        sys.stderr.write(f"RUNTIME-STATE ERROR: not a directory: {run_dir}\n")
        return 2

    plan = inspect_recovery(run_dir, lock_ttl_seconds=args.ttl)
    applied = []
    if args.apply:
        applied = apply_recovery(plan, approve_explicit=True,
                                 allow_lock_removal=args.allow_lock_removal)
        plan = inspect_recovery(run_dir, lock_ttl_seconds=args.ttl)  # re-inspect after repair

    if args.format == "json":
        out = plan.to_dict()
        out["applied"] = applied
        print(_json.dumps(out, indent=2))
    else:
        print(f"Run: {run_dir}")
        print(f"Consistent: {plan.consistent}")
        if plan.conditions:
            print("Conditions:")
            for c in plan.conditions:
                loc = f" [{c.transaction_id or c.task_id}]" if (c.transaction_id or c.task_id) else ""
                print(f"  - {c.type}{loc}: {c.detail}")
        if plan.actions:
            print("Suggested actions:")
            for a in plan.actions:
                tag = "explicit" if a.requires_explicit_approval else "safe"
                print(f"  - [{tag}] {a.type}: {a.detail}")
        if applied:
            print("Applied:")
            for a in applied:
                print(f"  - {a}")

    unrecoverable = any(c.type in ("invalid_state", "invalid_manifest") for c in plan.conditions)
    if unrecoverable:
        return 2
    return 0 if plan.consistent else 1


if __name__ == "__main__":
    sys.exit(main())
