"""
Typed models for the ECF Run Initialization Engine.

These live in the run_initializer package namespace and are imported with a
relative import (`from .models import ...`) so they never clash with the bare
`models` modules used by the planner and runtime_state subsystems.

No engineering content is carried here — only run-initialization configuration,
the parsed Work Request, and the machine-readable initialization result.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class InitExitCode:
    """Process exit codes for the initializer CLI."""
    OK = 0            # run initialized successfully
    INVALID = 1       # invalid workflow or Work Request
    CONFIG = 2        # configuration, filesystem, or infrastructure failure


class InitError(Exception):
    """
    Raised for any initialization failure.

    Carries an explicit exit code so the CLI never has to guess, plus optional
    structured reasons (e.g. the list of missing Work Request sections).
    """

    def __init__(self, message: str, exit_code: int = InitExitCode.CONFIG,
                 reasons: list | None = None):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.reasons = list(reasons or [])


@dataclass
class WorkRequest:
    """A parsed Work Request (see work_requests/WORK_REQUEST_SPECIFICATION.md)."""
    work_request_id: str = ""
    title: str = ""
    engineering_question: str = ""
    desired_outcome: str = ""
    engineering_context_reference: str = ""
    constraints: str = ""
    requested_deliverables: str = ""
    success_criteria: str = ""
    raw_text: str = ""
    # section-key -> whether a non-empty section body was found
    present_sections: dict = field(default_factory=dict)


@dataclass
class InitRequest:
    """Everything needed to initialize exactly one run."""
    workflow_path: str
    work_request_path: str
    run_id: str
    run_root: str = ""               # runtime/runs (final = run_root/run_id)
    run_dir: str = ""                # explicit final directory (alternative to run_root)
    provenance_mode: str = "required"
    work_request_id_override: str = ""   # used only when the document lacks an ID
    force: bool = False
    repo_root: str = ""


@dataclass
class InitResult:
    """Machine-readable result of an initialization attempt."""
    status: str                       # "initialized" | "failed"
    run_id: str = ""
    run_dir: str = ""
    workflow_id: str = ""
    workflow_version: str = ""
    work_request_id: str = ""
    provenance_mode: str = ""
    revision: int = 0
    task_count: int = 0
    ready_tasks: list = field(default_factory=list)
    blocked_count: int = 0
    warnings: list = field(default_factory=list)
    message: str = ""
    exit_code: int = InitExitCode.OK

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "run_id": self.run_id,
            "run_dir": self.run_dir,
            "workflow_id": self.workflow_id,
            "workflow_version": self.workflow_version,
            "work_request_id": self.work_request_id,
            "provenance_mode": self.provenance_mode,
            "revision": self.revision,
            "task_count": self.task_count,
            "ready_tasks": list(self.ready_tasks),
            "blocked_count": self.blocked_count,
            "warnings": list(self.warnings),
            "message": self.message,
        }
