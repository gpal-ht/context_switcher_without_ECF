#!/usr/bin/env python3
"""
ECF Execution Planner (read-only CLI).

Answers exactly one question: which task(s) are runnable right now?

It validates the workflow, inspects an optional runtime directory, and prints an
execution plan (completed / ready / blocked, with blocking reasons and remaining
topological order).

It does NOT execute tasks, invoke AI, or modify any file.

Usage:
    python tools/workflow_planner/plan_workflow.py <workflow.md>
    python tools/workflow_planner/plan_workflow.py <workflow.md> --run runtime/runs/<RUN_ID>
    python tools/workflow_planner/plan_workflow.py <workflow.md> --format json

Exit codes:
    0  a plan was produced (runnable, blocked, complete, or failed run)
    1  the workflow failed validation (cannot plan safely)
    2  planner execution/configuration failure (bad file, invalid runtime)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_VALIDATOR_DIR = _HERE.parents[0] / "workflow_validator"
for _p in (str(_HERE), str(_VALIDATOR_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import validate_workflow as vw          # noqa: E402
from models import PlanStatus, TaskState  # noqa: E402
from planner import PlannerError, plan_from_paths  # noqa: E402
from provenance import PlannerConfigError  # noqa: E402

_SEP = "-" * 48


def render_text(plan) -> str:
    lines = []
    lines.append("Workflow")
    lines.append(f"  {plan.workflow_id}")
    lines.append("")
    lines.append("Status")
    lines.append(f"  {plan.status}")

    if plan.status == PlanStatus.INVALID:
        lines.append("")
        lines.append("Workflow failed validation; no execution plan produced.")
        for e in plan.validation_errors:
            lines.append(f"  - {e}")
        return "\n".join(lines)

    if plan.provenance_mode:
        lines.append(f"Provenance {plan.provenance_mode}")
    lines.append("")
    lines.append(f"Completed  {len(plan.completed)}")
    lines.append(f"Ready      {len(plan.ready)}")
    lines.append(f"Blocked    {len(plan.blocked)}")
    if plan.stale:
        lines.append(f"Stale      {len(plan.stale)}")
    if plan.rerun_required:
        lines.append(f"Rerun      {len(plan.rerun_required)}")
    if plan.failed:
        lines.append(f"Failed     {len(plan.failed)}")
    for w in plan.warnings:
        lines.append(f"WARNING    {w}")
    for note in plan.notes:
        lines.append(f"Note       {note}")

    stale = [t for t in plan.tasks if t.state in (TaskState.STALE, TaskState.RERUN_REQUIRED)]
    if stale:
        lines.append("")
        lines.append(_SEP)
        lines.append("STALE / RERUN REQUIRED")
        for t in stale:
            lines.append(f"  {t.id}  ({t.state})")
            lines.append(f"  Reason: {t.reason}")
            for r in t.stale_reasons:
                if r.get("check") in ("input_hash_changed", "output_hash_changed"):
                    lines.append(f"    {r['check']}")
                    if r.get("artifact"):
                        lines.append(f"    Artifact: {r['artifact']}")
                    if r.get("recorded"):
                        lines.append(f"    Recorded: {r['recorded']}")
                    if r.get("current"):
                        lines.append(f"    Current:  {r['current']}")

    ready = [t for t in plan.tasks if t.state == TaskState.READY]
    if ready:
        lines.append("")
        lines.append(_SEP)
        lines.append("READY")
        for t in ready:
            lines.append(f"  {t.id}")
            lines.append(f"  Reason: {t.reason}")

    blocked = [t for t in plan.tasks if t.state == TaskState.BLOCKED]
    if blocked:
        lines.append("")
        lines.append(_SEP)
        lines.append("BLOCKED")
        for t in blocked:
            lines.append(f"  {t.id}")
            if t.waiting_for:
                lines.append(f"  Waiting for: {', '.join(t.waiting_for)}")
            lines.append(f"  Reason: {t.reason}")

    other = [t for t in plan.tasks
             if t.state in (TaskState.FAILED, TaskState.CANCELLED,
                            TaskState.SUPERSEDED, TaskState.RUNNING)]
    if other:
        lines.append("")
        lines.append(_SEP)
        lines.append("OTHER")
        for t in other:
            lines.append(f"  {t.id}: {t.state} - {t.reason}")

    lines.append("")
    lines.append(_SEP)
    lines.append("REMAINING ORDER")
    lines.append("  " + (" -> ".join(plan.remaining_order) if plan.remaining_order else "(none; run complete)"))
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only ECF execution planner: which tasks are runnable now?")
    parser.add_argument("workflow", help="Path to the workflow specification (.md).")
    parser.add_argument("--run", default=None,
                        help="Optional runtime run directory (runtime/runs/<RUN_ID>).")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--tasks-dir", default=None)
    parser.add_argument("--catalog", default=None)
    args = parser.parse_args(argv)

    workflow_path = Path(args.workflow)
    if not workflow_path.is_file():
        sys.stderr.write(f"PLANNER ERROR: workflow file not readable: {workflow_path}\n")
        return 2

    try:
        repo_root = vw.resolve_repo_root(args.repo_root, workflow_path)
        tasks_dir = Path(args.tasks_dir).resolve() if args.tasks_dir else repo_root / "tasks"
        catalog_path = (Path(args.catalog).resolve() if args.catalog
                        else repo_root / "workflows" / "WORKFLOW_CATALOG.md")
        idx = vw.RepoIndex(repo_root, tasks_dir, catalog_path, repo_root / "workflows")
    except Exception as exc:
        sys.stderr.write(f"PLANNER ERROR: could not build repository index: {exc}\n")
        return 2

    run_dir = Path(args.run) if args.run else None
    try:
        plan = plan_from_paths(workflow_path, run_dir, idx)
    except (PlannerError, PlannerConfigError) as exc:
        sys.stderr.write(f"PLANNER ERROR: {exc}\n")
        return 2

    if args.format == "json":
        print(json.dumps(plan.to_dict(), indent=2))
    else:
        print(render_text(plan))

    if plan.status == PlanStatus.INVALID:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
