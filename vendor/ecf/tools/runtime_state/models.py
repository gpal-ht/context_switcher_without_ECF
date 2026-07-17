"""
Typed models for Atomic Runtime State.

These describe the run-state record, the run manifest, the writer lock, and the
per-task transaction journal. They carry no engineering content.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = "0.1.0"


class RunStatus:
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    RUNNING = "running"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"
    WAITING_FOR_HUMAN_APPROVAL = "waiting_for_human_approval"
    COMPLETED = "completed"
    ALL = (REQUESTED, ACCEPTED, RUNNING, BLOCKED, FAILED, CANCELLED,
           SUPERSEDED, WAITING_FOR_HUMAN_APPROVAL, COMPLETED)


class TaskLifecycle:
    """Aligned with the planner execution-state model."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"
    ALL = (NOT_STARTED, RUNNING, COMPLETED, FAILED, CANCELLED, SUPERSEDED)


class TransactionPhase:
    PREPARED = "prepared"
    STAGED = "staged"
    VALIDATED = "validated"
    COMMITTING = "committing"
    COMMITTED = "committed"
    ABORTED = "aborted"
    RECOVERY_REQUIRED = "recovery_required"
    ALL = (PREPARED, STAGED, VALIDATED, COMMITTING, COMMITTED, ABORTED,
           RECOVERY_REQUIRED)


class TraceEvent:
    TRANSACTION_STARTED = "transaction_started"
    OUTPUT_STAGED = "output_staged"
    PROVENANCE_STAGED = "provenance_staged"
    VALIDATION_PASSED = "validation_passed"
    COMMIT_STARTED = "commit_started"
    OUTPUT_PROMOTED = "output_promoted"
    PROVENANCE_PROMOTED = "provenance_promoted"
    STATE_UPDATED = "state_updated"
    MANIFEST_UPDATED = "manifest_updated"
    TRANSACTION_COMMITTED = "transaction_committed"
    TRANSACTION_ABORTED = "transaction_aborted"
    RECOVERY_REQUIRED = "recovery_required"


class OutputStatus:
    NONE = "none"
    STAGED = "staged"
    PROMOTED = "promoted"
    VERIFIED = "verified"


class ValidationStatus:
    UNKNOWN = "unknown"
    VALID = "valid"
    INVALID = "invalid"


# --------------------------------------------------------------------------- #

@dataclass
class RunState:
    run_id: str
    work_request_id: str = ""
    workflow_id: str = ""
    workflow_version: str = ""
    provenance_mode: str = "required"
    run_status: str = RunStatus.REQUESTED
    active_task: str | None = None
    task_states: dict = field(default_factory=dict)   # task_id -> TaskLifecycle
    revision: int = 0
    created_at: str = ""
    updated_at: str = ""
    failure: dict | None = None
    recovery_status: str = "none"
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "work_request_id": self.work_request_id,
            "workflow_id": self.workflow_id,
            "workflow_version": self.workflow_version,
            "provenance": {"mode": self.provenance_mode, "schema_version": SCHEMA_VERSION},
            "run_status": self.run_status,
            "active_task": self.active_task,
            "task_states": dict(self.task_states),
            "revision": self.revision,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "failure": self.failure,
            "recovery_status": self.recovery_status,
        }

    @staticmethod
    def from_dict(d: dict) -> "RunState":
        prov = d.get("provenance") or {}
        return RunState(
            run_id=d.get("run_id", ""),
            work_request_id=d.get("work_request_id", ""),
            workflow_id=d.get("workflow_id", ""),
            workflow_version=d.get("workflow_version", ""),
            provenance_mode=(prov.get("mode") if isinstance(prov, dict) else None)
                            or d.get("provenance_mode") or "required",
            run_status=d.get("run_status", RunStatus.REQUESTED),
            active_task=d.get("active_task"),
            task_states=dict(d.get("task_states") or {}),
            revision=int(d.get("revision", 0)),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            failure=d.get("failure"),
            recovery_status=d.get("recovery_status", "none"),
            schema_version=d.get("schema_version", SCHEMA_VERSION),
        )


@dataclass
class ManifestTask:
    id: str
    version: str = ""
    output: str = ""                 # bound output path (relative)
    output_status: str = OutputStatus.NONE
    provenance_path: str = ""
    output_hash: str = ""
    validation_status: str = ValidationStatus.UNKNOWN
    status: str = TaskLifecycle.NOT_STARTED

    def to_dict(self) -> dict:
        return {
            "id": self.id, "version": self.version, "status": self.status,
            "output": self.output, "output_status": self.output_status,
            "provenance_path": self.provenance_path, "output_hash": self.output_hash,
            "validation_status": self.validation_status,
        }

    @staticmethod
    def from_dict(d: dict) -> "ManifestTask":
        return ManifestTask(
            id=d.get("id", ""), version=d.get("version", ""),
            output=d.get("output", ""), output_status=d.get("output_status", OutputStatus.NONE),
            provenance_path=d.get("provenance_path", ""), output_hash=d.get("output_hash", ""),
            validation_status=d.get("validation_status", ValidationStatus.UNKNOWN),
            status=d.get("status", TaskLifecycle.NOT_STARTED),
        )


@dataclass
class RunManifest:
    run_id: str
    workflow_id: str = ""
    workflow_version: str = ""
    revision: int = 0
    executor: dict = field(default_factory=dict)
    ecf_version: str = ""
    ekb_version: str = ""
    tasks: list = field(default_factory=list)         # list[ManifestTask]
    findings: list = field(default_factory=list)      # list[dict]
    trace_path: str = ""
    completion_path: str = ""
    schema_version: str = SCHEMA_VERSION

    def task(self, task_id: str) -> "ManifestTask | None":
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "workflow_version": self.workflow_version,
            "revision": self.revision,
            "executor": dict(self.executor),
            "ecf_version": self.ecf_version,
            "ekb_version": self.ekb_version,
            "tasks": [t.to_dict() for t in self.tasks],
            "findings": list(self.findings),
            "trace_path": self.trace_path,
            "completion_path": self.completion_path,
        }

    @staticmethod
    def from_dict(d: dict) -> "RunManifest":
        return RunManifest(
            run_id=d.get("run_id", ""),
            workflow_id=d.get("workflow_id", ""),
            workflow_version=d.get("workflow_version", ""),
            revision=int(d.get("revision", 0)),
            executor=dict(d.get("executor") or {}),
            ecf_version=d.get("ecf_version", ""),
            ekb_version=d.get("ekb_version", ""),
            tasks=[ManifestTask.from_dict(t) for t in (d.get("tasks") or [])],
            findings=list(d.get("findings") or []),
            trace_path=d.get("trace_path", ""),
            completion_path=d.get("completion_path", ""),
            schema_version=d.get("schema_version", SCHEMA_VERSION),
        )


@dataclass
class RunLock:
    owner: str
    created_at: str
    transaction_id: str = ""

    def to_dict(self) -> dict:
        return {"owner": self.owner, "created_at": self.created_at,
                "transaction_id": self.transaction_id}

    @staticmethod
    def from_dict(d: dict) -> "RunLock":
        return RunLock(owner=d.get("owner", ""), created_at=d.get("created_at", ""),
                       transaction_id=d.get("transaction_id", ""))


@dataclass
class TransactionJournal:
    transaction_id: str
    run_id: str
    task_id: str
    phase: str = TransactionPhase.PREPARED
    expected_revision: int = 0
    target_revision: int = 0
    output_final: str = ""            # relative final output path
    provenance_final: str = ""        # relative final provenance path
    output_sha256: str = ""
    created_at: str = ""
    updated_at: str = ""
    events: list = field(default_factory=list)   # list[dict] {event, at}

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id, "run_id": self.run_id,
            "task_id": self.task_id, "phase": self.phase,
            "expected_revision": self.expected_revision,
            "target_revision": self.target_revision,
            "output_final": self.output_final, "provenance_final": self.provenance_final,
            "output_sha256": self.output_sha256,
            "created_at": self.created_at, "updated_at": self.updated_at,
            "events": list(self.events),
        }

    @staticmethod
    def from_dict(d: dict) -> "TransactionJournal":
        return TransactionJournal(
            transaction_id=d.get("transaction_id", ""), run_id=d.get("run_id", ""),
            task_id=d.get("task_id", ""), phase=d.get("phase", TransactionPhase.PREPARED),
            expected_revision=int(d.get("expected_revision", 0)),
            target_revision=int(d.get("target_revision", 0)),
            output_final=d.get("output_final", ""), provenance_final=d.get("provenance_final", ""),
            output_sha256=d.get("output_sha256", ""),
            created_at=d.get("created_at", ""), updated_at=d.get("updated_at", ""),
            events=list(d.get("events") or []),
        )
