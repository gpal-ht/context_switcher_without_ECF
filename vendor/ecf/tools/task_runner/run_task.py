#!/usr/bin/env python3
"""
ECF single-task runner CLI.

Executes exactly one planner-approved task and stops.

Usage:
    python tools/task_runner/run_task.py <workflow-path> \
        --run <run-directory> --task <TASK-ID> --executor fixture \
        --fixture <candidate-output-file> [--format json] [--force-rerun]

    # select the sole ready task (fails if 0 or >1 are ready):
    python tools/task_runner/run_task.py <workflow-path> --run <dir> --next \
        --executor fixture --fixture <file>

Exit codes:
    0  one task executed and committed
    1  task or workflow rejected / task execution failed
    2  runner configuration or infrastructure failure
    3  recovery required
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Import as a package so intra-package relative imports resolve and the
# task_runner 'models' never clashes with planner/runtime_state 'models'.
_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from task_runner.runner import run_one_task           # noqa: E402
from task_runner.executor import make_executor, ExecutorError  # noqa: E402
from task_runner.models import ExitCode               # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute exactly one planner-approved ECF task (read-mostly; commits one result).")
    parser.add_argument("workflow")
    parser.add_argument("--run", required=True, help="runtime run directory")
    parser.add_argument("--task", default=None, help="Task ID to execute")
    parser.add_argument("--next", action="store_true", dest="use_next",
                        help="select the sole ready task (fails if not exactly one)")
    parser.add_argument("--executor", default="fixture", choices=["fixture", "claude-code"])
    parser.add_argument("--fixture", default=None, help="candidate-output fixture file")
    parser.add_argument("--allow-ai-executor", action="store_true", dest="allow_ai",
                        help="explicitly permit the AI-backed executor (required for claude-code)")
    parser.add_argument("--claude-command", default=None, dest="claude_command",
                        help="Claude executable (e.g. 'claude'); no shell interpolation")
    parser.add_argument("--claude-arg", action="append", dest="claude_args", default=[],
                        help="fixed argument passed to the Claude command (repeatable)")
    parser.add_argument("--timeout", type=float, default=120.0, help="executor timeout (seconds)")
    parser.add_argument("--force-rerun", action="store_true", dest="force_rerun",
                        help="re-execute a completed+valid task (operator confirmation)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    wf = Path(args.workflow)
    if not wf.is_file():
        sys.stderr.write(f"RUNNER ERROR: workflow not found: {wf}\n")
        return ExitCode.CONFIG
    if not args.task and not args.use_next:
        sys.stderr.write("RUNNER ERROR: specify --task <ID> or --next\n")
        return ExitCode.CONFIG

    repo_root = Path(__file__).resolve().parents[2]
    try:
        executor = make_executor(args.executor, {
            "fixture": args.fixture,
            "allow_ai": args.allow_ai,
            "claude_command": args.claude_command,
            "claude_args": args.claude_args,
            "timeout": args.timeout,
            "repo_root": repo_root,
        })
    except ExecutorError as exc:
        sys.stderr.write(f"RUNNER ERROR: {exc}\n")
        return ExitCode.CONFIG

    result = run_one_task(wf, Path(args.run), executor, task_id=args.task,
                          use_next=args.use_next, force_rerun=args.force_rerun)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Task:   {result.task_id}")
        print(f"Status: {result.status}")
        print(f"Message: {result.message}")
        if result.state_revision is not None:
            print(f"Revisions: state={result.state_revision} manifest={result.manifest_revision}")
        print("Events: " + " -> ".join(e["event"] for e in result.events))
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
