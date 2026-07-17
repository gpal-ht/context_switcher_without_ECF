"""
ECF single-task runner package.

Executes exactly one planner-approved task and stops. Reuses the workflow
validator, planner, provenance model, artifact fingerprinting, runtime
transaction layer, and recovery inspection. Never executes a whole workflow,
never invokes AI, never runs arbitrary shell commands.
"""

__all__ = ["run_one_task", "Runner", "make_executor", "FixtureExecutor",
           "TaskExecutor", "ExitCode"]


def __getattr__(name):
    if name in ("run_one_task", "Runner"):
        from . import runner
        return getattr(runner, name)
    if name in ("make_executor", "FixtureExecutor", "TaskExecutor"):
        from . import executor
        return getattr(executor, name)
    if name == "ExitCode":
        from . import models
        return getattr(models, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
