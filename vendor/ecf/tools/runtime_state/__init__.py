"""
Atomic Runtime State for the ECF control plane.

Runtime transaction primitives that ensure a task's output, provenance,
manifest, state, and trace metadata cannot silently disagree after interruption
or failure. This package NEVER executes engineering tasks and NEVER invokes AI;
callers supply staged content.

Public surface is resolved lazily so importing the package does not import every
submodule eagerly.
"""

__all__ = [
    "load_run_state", "save_run_state", "load_manifest", "save_manifest",
    "acquire_run_lock", "release_run_lock", "read_lock", "is_lock_stale",
    "begin_task_transaction", "TaskTransaction",
    "inspect_recovery", "apply_recovery",
    "RunState", "RunManifest", "RunLock", "TransactionJournal",
    "RunStatus", "TaskLifecycle", "TransactionPhase", "TraceEvent",
]


def __getattr__(name):
    if name in ("RunState", "RunManifest", "RunLock", "TransactionJournal",
                "RunStatus", "TaskLifecycle", "TransactionPhase", "TraceEvent"):
        from . import models
        return getattr(models, name)
    if name in ("load_run_state", "save_run_state", "load_manifest", "save_manifest",
                "acquire_run_lock", "release_run_lock", "read_lock", "is_lock_stale",
                "begin_task_transaction", "TaskTransaction"):
        from . import transaction
        return getattr(transaction, name)
    if name in ("inspect_recovery", "apply_recovery"):
        from . import recovery
        return getattr(recovery, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
