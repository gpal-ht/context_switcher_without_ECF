"""
Models for the ECF single-task runner.

The runner executes exactly one planner-approved task and stops. These models
describe the provider-independent executor interface and the runner's result.
They carry no engineering content.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class ExitCode:
    OK = 0                 # one task executed and committed
    REJECTED = 1           # task/workflow rejected, or task execution failed
    CONFIG = 2             # runner configuration or infrastructure failure
    RECOVERY_REQUIRED = 3  # unresolved / newly-produced recovery condition


class ExecutorStatus:
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class RunnerEvent:
    RUNNER_STARTED = "runner_started"
    WORKFLOW_VALIDATED = "workflow_validated"
    RECOVERY_INSPECTED = "recovery_inspected"
    PLANNER_EVALUATED = "planner_evaluated"
    TASK_SELECTED = "task_selected"
    LOCK_ACQUIRED = "lock_acquired"
    TASK_MARKED_RUNNING = "task_marked_running"
    EXECUTOR_STARTED = "executor_started"
    EXECUTOR_COMPLETED = "executor_completed"
    OUTPUT_VALIDATED = "output_validated"
    PROVENANCE_GENERATED = "provenance_generated"
    TRANSACTION_STARTED = "transaction_started"
    TRANSACTION_COMMITTED = "transaction_committed"
    TASK_COMPLETED = "task_completed"
    RUNNER_STOPPED = "runner_stopped"
    RUNNER_FAILED = "runner_failed"
    RECOVERY_REQUIRED = "recovery_required"


@dataclass
class InputArtifact:
    name: str          # logical name (typically the producing Task ID)
    path: str          # run-relative path (read-only for the executor)

    def to_dict(self) -> dict:
        return {"name": self.name, "path": self.path}


@dataclass
class TaskExecutionRequest:
    run_id: str
    work_request_id: str
    workflow_id: str
    workflow_version: str
    task_id: str
    task_version: str
    task_spec_path: str
    output_binding: str                # run-relative output path
    inputs: list = field(default_factory=list)   # list[InputArtifact]
    ecf_version: str = ""
    ecf_commit: str = ""
    ekb_required: bool = False
    ekb_version: str = ""
    ekb_commit: str = ""
    permission_boundary: dict = field(default_factory=dict)
    executor_config: dict = field(default_factory=dict)
    run_dir: str = ""                  # absolute run directory (read-only inputs live here)

    def input_paths(self) -> list:
        return [i.path for i in self.inputs]


@dataclass
class TaskExecutionResult:
    task_id: str
    status: str = ExecutorStatus.SUCCEEDED
    output_bytes: bytes | None = None      # candidate primary output (v0.1: bytes)
    output_path: str = ""                  # optional: executor-produced path (rare)
    diagnostics: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    validation_status: str = "unknown"
    failure: dict | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == ExecutorStatus.SUCCEEDED


@dataclass
class RunnerResult:
    run_id: str
    task_id: str
    exit_code: int
    status: str                        # committed | rejected | failed | recovery_required | config_error
    message: str = ""
    events: list = field(default_factory=list)     # list[{event, at, detail?}]
    output: str = ""
    provenance: str = ""
    state_revision: int | None = None
    manifest_revision: int | None = None
    executor_id: str = ""

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "exit_code": self.exit_code,
            "status": self.status,
            "message": self.message,
            "executor": self.executor_id,
            "output": self.output or None,
            "provenance": self.provenance or None,
            "state_revision": self.state_revision,
            "manifest_revision": self.manifest_revision,
            "events": list(self.events),
        }
