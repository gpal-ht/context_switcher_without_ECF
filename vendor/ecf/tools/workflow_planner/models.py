"""
Data models for the ECF Execution Planner.

The planner is a read-only control-plane component. A task is described by three
SEPARATE dimensions so that lifecycle, output validity, and the planned next
action are never conflated:

  * execution_state  - where the task is in its run lifecycle
  * output_validity  - whether its produced output is still trustworthy
  * planned_action   - what the planner would do next (advisory; never executed)

`STALE` and `RERUN REQUIRED` are presentation labels derived from these
dimensions; they are not lifecycle states.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class ExecutionState:
    """Where a task is in its run lifecycle (independent of output validity)."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"
    ALL = (NOT_STARTED, RUNNING, COMPLETED, FAILED, CANCELLED, SUPERSEDED)


class OutputValidity:
    """Whether a task's produced output is still valid for its inputs/versions."""
    NOT_APPLICABLE = "not_applicable"   # task has not produced an output
    UNKNOWN = "unknown"                 # not verified (e.g. legacy provenance mode)
    VALID = "valid"
    STALE = "stale"                     # provenance mismatch (hash/version/commit)
    MISSING = "missing"                 # required provenance record absent
    MALFORMED = "malformed"             # provenance record unparseable
    ALL = (NOT_APPLICABLE, UNKNOWN, VALID, STALE, MISSING, MALFORMED)
    INVALID = (STALE, MISSING, MALFORMED)


class PlannedAction:
    """The planner's advisory next action for a task. Never executed here."""
    NONE = "none"
    RUN = "run"
    RERUN = "rerun"
    WAIT = "wait"
    BLOCKED = "blocked"
    STOP = "stop"
    ALL = (NONE, RUN, RERUN, WAIT, BLOCKED, STOP)


class DisplayState:
    """Derived, human-facing labels (NOT stored lifecycle states)."""
    NOT_STARTED = "not_started"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"
    STALE = "stale"
    RERUN_REQUIRED = "rerun_required"


# Backwards-compatible alias: existing callers/tests read `TaskState.*` labels.
TaskState = DisplayState


class PlanStatus:
    """Overall plan status."""
    RUNNABLE = "runnable"                 # at least one task's planned action is run
    BLOCKED = "blocked"                   # nothing runnable, run not complete
    COMPLETE = "complete"                 # every task completed with valid output
    FAILED = "failed"                     # the run failed
    INVALID = "invalid"                   # the workflow failed validation; no plan
    RERUN_REQUIRED = "rerun_required"     # one or more completed outputs are stale


def derive_display_state(execution_state: str, output_validity: str,
                         planned_action: str) -> str:
    """Collapse the three dimensions into a single human-facing label."""
    ex, ov, act = execution_state, output_validity, planned_action
    if ex == ExecutionState.COMPLETED:
        if ov in OutputValidity.INVALID:
            return DisplayState.STALE
        if act == PlannedAction.RERUN:
            return DisplayState.RERUN_REQUIRED
        return DisplayState.COMPLETED
    if ex == ExecutionState.NOT_STARTED:
        if act == PlannedAction.RUN:
            return DisplayState.READY
        if act in (PlannedAction.WAIT, PlannedAction.BLOCKED):
            return DisplayState.BLOCKED
        return DisplayState.NOT_STARTED
    if ex == ExecutionState.RUNNING:
        return DisplayState.RUNNING
    if ex == ExecutionState.FAILED:
        return DisplayState.FAILED
    if ex == ExecutionState.CANCELLED:
        return DisplayState.CANCELLED
    if ex == ExecutionState.SUPERSEDED:
        return DisplayState.SUPERSEDED
    return DisplayState.NOT_STARTED


@dataclass
class TaskPlan:
    id: str
    execution_state: str = ExecutionState.NOT_STARTED
    output_validity: str = OutputValidity.NOT_APPLICABLE
    planned_action: str = PlannedAction.NONE
    output: str = ""                       # bound primary output path (relative)
    reason: str = ""                       # why ready / why blocked / status note
    waiting_for: list = field(default_factory=list)   # missing outputs / incomplete deps
    depends_on: list = field(default_factory=list)
    stale_reasons: list = field(default_factory=list)  # list[dict] structured reasons

    @property
    def state(self) -> str:
        """Derived display label (backwards-compatible convenience)."""
        return derive_display_state(self.execution_state, self.output_validity,
                                    self.planned_action)

    @property
    def rerun_required(self) -> bool:
        return self.planned_action == PlannedAction.RERUN

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "execution_state": self.execution_state,
            "output_validity": self.output_validity,
            "planned_action": self.planned_action,
            "display_state": self.state,
        }
        if self.reason:
            d["reason"] = self.reason
        if self.waiting_for:
            d["waiting_for"] = list(self.waiting_for)
        if self.stale_reasons:
            d["stale_reasons"] = list(self.stale_reasons)
        return d


@dataclass
class ExecutionPlan:
    workflow_id: str
    status: str
    source_path: str = ""
    run_dir: str = ""
    provenance_mode: str = ""
    tasks: list = field(default_factory=list)          # list[TaskPlan] in workflow order
    remaining_order: list = field(default_factory=list)  # topological order of not-done tasks
    validation_errors: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    # --- convenience groupings (by derived display label) ----------------- #
    def _ids(self, label):
        return [t.id for t in self.tasks if t.state == label]

    @property
    def completed(self):
        return self._ids(DisplayState.COMPLETED)

    @property
    def ready(self):
        return self._ids(DisplayState.READY)

    @property
    def blocked(self):
        return self._ids(DisplayState.BLOCKED)

    @property
    def failed(self):
        return self._ids(DisplayState.FAILED)

    @property
    def stale(self):
        return self._ids(DisplayState.STALE)

    @property
    def rerun_required(self):
        return self._ids(DisplayState.RERUN_REQUIRED)

    def to_dict(self) -> dict:
        return {
            "workflow": self.workflow_id,
            "status": self.status,
            "run_dir": self.run_dir or None,
            "provenance_mode": self.provenance_mode or None,
            "counts": {
                "completed": len(self.completed),
                "ready": len(self.ready),
                "blocked": len(self.blocked),
                "failed": len(self.failed),
                "stale": len(self.stale),
                "rerun_required": len(self.rerun_required),
                "total": len(self.tasks),
            },
            "tasks": [t.to_dict() for t in self.tasks],
            "remaining_order": list(self.remaining_order),
            "warnings": list(self.warnings),
            "validation_errors": list(self.validation_errors),
            "notes": list(self.notes),
        }
