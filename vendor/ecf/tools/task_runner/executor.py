"""
Provider-independent task executor interface + a safe local fixture executor.

An executor turns a TaskExecutionRequest into exactly one candidate primary
output. The runner (not the executor) validates the output, generates
authoritative provenance, and commits through the runtime transaction layer.

v0.1 ships only the `fixture` executor: it reads a predefined output file and
returns its bytes. It never writes, never touches the network, never invokes an
AI, and never modifies the declared read-only inputs. There is deliberately no
Claude-specific or arbitrary-shell logic here.
"""

from __future__ import annotations

from pathlib import Path

from .models import ExecutorStatus, TaskExecutionRequest, TaskExecutionResult


class ExecutorError(Exception):
    pass


class TaskExecutor:
    """Provider-independent executor. Implementations must be side-effect free
    with respect to declared read-only inputs and must return exactly one
    candidate primary output."""

    id = "abstract"

    def execute(self, request: TaskExecutionRequest) -> TaskExecutionResult:  # pragma: no cover
        raise NotImplementedError


class FixtureExecutor(TaskExecutor):
    """
    Reads a predefined candidate-output fixture file and returns it verbatim.

    Read-only: it only reads the fixture (and never the run's inputs). It cannot
    modify inputs, reach the network, or run shell commands.
    """

    id = "fixture"

    def __init__(self, fixture_path: str | Path):
        self.fixture_path = Path(fixture_path)

    def execute(self, request: TaskExecutionRequest) -> TaskExecutionResult:
        if not self.fixture_path.is_file():
            return TaskExecutionResult(
                task_id=request.task_id, status=ExecutorStatus.FAILED,
                validation_status="not_run",
                failure={"code": "fixture_missing",
                         "detail": f"fixture not found: {self.fixture_path}"},
                diagnostics=[f"fixture executor could not read {self.fixture_path}"])
        try:
            data = self.fixture_path.read_bytes()
        except OSError as exc:
            return TaskExecutionResult(
                task_id=request.task_id, status=ExecutorStatus.FAILED,
                failure={"code": "fixture_unreadable", "detail": str(exc)})
        return TaskExecutionResult(
            task_id=request.task_id, status=ExecutorStatus.SUCCEEDED,
            output_bytes=data, validation_status="produced",
            diagnostics=[f"fixture executor returned {len(data)} bytes"])


def make_executor(kind: str, config: dict) -> TaskExecutor:
    """
    Factory for executors. The safe 'fixture' executor is always available. The
    AI-backed 'claude-code' executor is disabled by default and requires explicit
    opt-in (config['allow_ai'] is True) — there is no silent fallback to Claude.
    """
    if kind == "fixture":
        fixture = config.get("fixture")
        if not fixture:
            raise ExecutorError("fixture executor requires --fixture <candidate-output-file>")
        return FixtureExecutor(fixture)
    if kind == "claude-code":
        if not config.get("allow_ai"):
            raise ExecutorError(
                "the claude-code executor is disabled by default; pass --allow-ai-executor "
                "AND --executor claude-code to enable it (no silent fallback).")
        from .executors.claude_code import ClaudeCodeExecutor
        command = config.get("claude_command")
        if not command:
            raise ExecutorError("claude-code executor requires --claude-command <executable>")
        return ClaudeCodeExecutor(
            command=command, repo_root=config["repo_root"], allow_ai=True,
            fixed_args=config.get("claude_args") or [],
            timeout=config.get("timeout", 120.0),
            subprocess_runner=config.get("subprocess_runner"))
    raise ExecutorError(
        f"unsupported executor '{kind}'. Supported: 'fixture' (safe) and "
        "'claude-code' (AI; requires explicit opt-in).")
