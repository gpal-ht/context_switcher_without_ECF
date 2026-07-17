#!/usr/bin/env python3
"""
ECF Run Initialization Engine CLI.

Converts a validated workflow + a Work Request + a Run identity into a
schema-valid, planner-ready runtime run. It never executes a task, invokes AI,
or creates task outputs / provenance records for unexecuted tasks.

Usage:
    python tools/run_initializer/initialize_run.py <workflow.md> \
        --work-request <WR.md> --run-root runtime/runs --run-id RUN-... [--format json]

    # explicit run directory (its leaf must equal --run-id):
    python tools/run_initializer/initialize_run.py <workflow.md> \
        --work-request <WR.md> --run-dir runtime/runs/RUN-... --run-id RUN-...

Exit codes:
    0  run initialized successfully
    1  invalid workflow or Work Request
    2  configuration, filesystem, or infrastructure failure
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Import as a package so the relative 'models' import resolves and never clashes
# with the planner/runtime_state bare 'models' modules.
_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from run_initializer.initializer import initialize_run          # noqa: E402
from run_initializer.models import InitError, InitExitCode, InitRequest  # noqa: E402


def _render_text(result) -> str:
    lines = [
        "Run initialized", "",
        "Run ID:", f"  {result.run_id}", "",
        "Workflow:", f"  {result.workflow_id}", "",
        "Work Request:", f"  {result.work_request_id}", "",
        "Revision:", f"  {result.revision}", "",
        "Provenance mode:", f"  {result.provenance_mode}", "",
        "Ready tasks:",
    ]
    if result.ready_tasks:
        lines += [f"  {t}" for t in result.ready_tasks]
    else:
        lines.append("  (none)")
    lines += ["", "Run directory:", f"  {result.run_dir}"]
    if result.warnings:
        lines += ["", "Warnings:"]
        lines += [f"  - {w}" for w in result.warnings]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Initialize a schema-valid, planner-ready ECF runtime run "
                    "(no task execution, no AI).")
    parser.add_argument("workflow", help="path to the workflow specification (.md)")
    parser.add_argument("--work-request", required=True, dest="work_request",
                        help="path to the Work Request (.md)")
    parser.add_argument("--run-id", required=True, dest="run_id",
                        help="conservative Run ID (RUN-...)")
    parser.add_argument("--run-root", default=None, dest="run_root",
                        help="run root; final run = <run-root>/<run-id> (e.g. runtime/runs)")
    parser.add_argument("--run-dir", default=None, dest="run_dir",
                        help="explicit final run directory (leaf must equal --run-id)")
    parser.add_argument("--provenance-mode", default="required", dest="provenance_mode",
                        choices=["required", "legacy"],
                        help="explicit provenance policy (default: required; never inferred)")
    parser.add_argument("--work-request-id", default="", dest="wr_id_override",
                        help="Work Request ID override (used only if the document lacks one)")
    parser.add_argument("--force", action="store_true",
                        help="replace an existing empty/invalid/pristine run")
    parser.add_argument("--repo-root", default="", dest="repo_root")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    if not args.run_root and not args.run_dir:
        sys.stderr.write("INIT ERROR: specify --run-root or --run-dir\n")
        return InitExitCode.CONFIG

    request = InitRequest(
        workflow_path=args.workflow, work_request_path=args.work_request,
        run_id=args.run_id, run_root=args.run_root or "", run_dir=args.run_dir or "",
        provenance_mode=args.provenance_mode, work_request_id_override=args.wr_id_override,
        force=args.force, repo_root=args.repo_root,
    )

    try:
        result = initialize_run(request)
    except InitError as exc:
        if args.format == "json":
            print(json.dumps({
                "status": "failed", "message": exc.message,
                "reasons": exc.reasons, "exit_code": exc.exit_code,
            }, indent=2))
        else:
            sys.stderr.write(f"INIT ERROR: {exc.message}\n")
            for r in exc.reasons:
                sys.stderr.write(f"  - {r}\n")
        return exc.exit_code

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(_render_text(result))
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
