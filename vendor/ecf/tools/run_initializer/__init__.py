"""
ECF Run Initialization Engine (v0.1).

Converts a validated workflow + a Work Request + a Run identity into a
schema-valid, planner-ready runtime run that the existing validator, planner,
runtime-state layer, recovery inspector, single-task runner, and provenance
subsystem can consume without manual YAML authoring.

It NEVER executes a task, invokes AI, creates task outputs, or writes provenance
records for unexecuted tasks. It only creates an initial run.
"""

from .models import (  # noqa: F401
    InitError, InitExitCode, InitRequest, InitResult, WorkRequest,
)
