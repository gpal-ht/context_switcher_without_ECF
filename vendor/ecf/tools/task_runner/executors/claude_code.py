"""
Claude Code executor — first AI-backed executor vertical slice.

Executes ONLY `TASK-CLASSIFY-0001` (Determine Engineering Intent). It generates a
task-specific prompt, invokes Claude Code through one explicit configured command
(no shell interpolation), captures the result, parses exactly one JSON envelope,
and mechanically validates it against the authoritative EKB intent taxonomy and
the run's request.

It NEVER: writes the final runtime output, generates authoritative provenance,
updates state/manifest, selects another task, loops, or exposes chain-of-thought.
The runner remains responsible for output promotion, provenance, and commit.

Disabled by default: creation requires explicit AI opt-in (see make_executor).

Standard library only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

# Ensure the shared fingerprint tool is importable (tools/ on path).
_TOOLS = Path(__file__).resolve().parents[2]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from ..models import ExecutorStatus, TaskExecutionRequest, TaskExecutionResult
# The intent-result validator and taxonomy loader are owned by the runner-side
# output-contract module. The Claude executor invokes them as defense in depth;
# the SAME canonical implementation also runs in the runner for EVERY executor.
from ..output_contracts import (  # noqa: F401  (re-exported for back-compat)
    load_intent_taxonomy, validate_intent_result, extract_single_json,
)

SUPPORTED_TASKS = {"TASK-CLASSIFY-0001"}
DEFAULT_TIMEOUT = 120.0


class ClaudeExecutorError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Prompt generation
# --------------------------------------------------------------------------- #

def _read_work_request(run_dir: Path):
    """Locate the accepted Work Request under <run_dir>/inputs/. Returns (path, text) or (None, '')."""
    inputs = Path(run_dir) / "inputs"
    if not inputs.is_dir():
        return None, ""
    for name in ("work-request.md", "work_request.md", "work-request.yaml", "work_request.yaml"):
        p = inputs / name
        if p.is_file():
            return p, p.read_text(encoding="utf-8", errors="ignore")
    # fall back to the first file in inputs/
    for p in sorted(inputs.iterdir()):
        if p.is_file():
            return p, p.read_text(encoding="utf-8", errors="ignore")
    return None, ""


def _section(text: str, header: str) -> str:
    m = re.search(rf"^#+\s*(?:\d+\.\s*)?{re.escape(header)}\s*$\n(.*?)(?=^#|\Z)",
                  text, re.M | re.S | re.I)
    return (m.group(1).strip() if m else "").strip()


def build_prompt(request: TaskExecutionRequest, wr_path, wr_text: str,
                 taxonomy: list) -> str:
    question = _section(wr_text, "Engineering Question") or "(see Work Request)"
    outcome = _section(wr_text, "Desired Outcome") or "(see Work Request)"
    wr_rel = str(wr_path) if wr_path else "(none)"
    taxo = ", ".join(taxonomy)
    return f"""# ECF Task Execution — Determine Engineering Intent

You are executing exactly one Engineering Control Framework task and nothing else.

## Permission Preflight (do this first)
Before doing any work, request — ONCE — only the permissions you need for this task:
- Read: the Work Request at `{wr_rel}` (read-only).
- No writes of any kind. You do not write the runtime output; you only return an envelope on stdout.
Do not request repository-wide authority, network access, or write permissions.

## Task
- Task: {request.task_id} (Determine Engineering Intent), version {request.task_version}
- Run ID: {request.run_id}
- Work Request ID: {request.work_request_id}

## Engineering Question
{question}

## Desired Outcome
{outcome}

## Permitted inputs (read-only)
- {wr_rel}

## Prohibited
- Do NOT modify any file. Do NOT write the runtime output.
- Do NOT modify source code, `vendor/`, or canonical project artifacts.
- Do NOT produce an engineering recommendation, approval, or implementation.
- Do NOT expose private chain-of-thought. Record observable classification evidence only.

## Allowed engineering intent values (authoritative)
{taxo}

## Required output — exactly ONE JSON document on stdout, and nothing else
Return a single JSON object EXACTLY matching this shape (no Markdown, no prose):

{{
  "schema_version": "0.1.0",
  "task_id": "{request.task_id}",
  "task_version": "{request.task_version}",
  "work_request_id": "{request.work_request_id}",
  "status": "completed",
  "engineering_intent": {{ "primary": "<one allowed value>", "secondary": [] }},
  "classification_evidence": {{
    "engineering_question": "<from the work request>",
    "desired_outcome": "<from the work request>",
    "requested_deliverables": []
  }},
  "confidence": {{ "level": "high|medium|low|unknown", "justification": "<observable evidence>" }},
  "findings": []
}}

Exactly one primary intent. Secondary intents optional. No fields beyond those shown.
"""


# --------------------------------------------------------------------------- #
# Subprocess invocation
# --------------------------------------------------------------------------- #

def _default_subprocess_runner(cmd_list, prompt, timeout):
    """Invoke the configured command WITHOUT a shell. Returns (stdout, stderr, code, dur, timed_out)."""
    t0 = time.monotonic()
    try:
        proc = subprocess.run(cmd_list, input=prompt, capture_output=True, text=True,
                              timeout=timeout, shell=False)
        return proc.stdout, proc.stderr, proc.returncode, time.monotonic() - t0, False
    except subprocess.TimeoutExpired as exc:
        return (exc.stdout or ""), (exc.stderr or ""), None, time.monotonic() - t0, True


# --------------------------------------------------------------------------- #
# Executor
# --------------------------------------------------------------------------- #

class ClaudeCodeExecutor:
    id = "claude-code"

    def __init__(self, command, repo_root, allow_ai: bool, fixed_args=None,
                 timeout: float = DEFAULT_TIMEOUT, subprocess_runner=None):
        self.command = command
        self.repo_root = Path(repo_root)
        self.allow_ai = bool(allow_ai)
        self.fixed_args = list(fixed_args or [])
        self.timeout = float(timeout)
        self._runner = subprocess_runner or _default_subprocess_runner

    def _fail(self, task_id, code, detail, diagnostics=None):
        return TaskExecutionResult(
            task_id=task_id, status=ExecutorStatus.FAILED,
            failure={"code": code, "detail": detail[:400]},
            diagnostics=diagnostics or [detail[:400]])

    def execute(self, request: TaskExecutionRequest) -> TaskExecutionResult:
        # explicit AI opt-in (defense in depth; the factory also enforces this)
        if not self.allow_ai:
            return self._fail(request.task_id, "ai_not_permitted",
                              "AI executor requires explicit opt-in (--allow-ai-executor)")
        # supported task only
        if request.task_id not in SUPPORTED_TASKS:
            return self._fail(request.task_id, "unsupported_task",
                              f"claude-code executor supports only {sorted(SUPPORTED_TASKS)}")
        # authoritative taxonomy must be available BEFORE invoking the AI
        taxonomy = load_intent_taxonomy(self.repo_root)
        if not taxonomy:
            return self._fail(request.task_id, "taxonomy_unavailable",
                              "EKB engineering intent model unavailable; refusing to invoke AI")
        # locate the Work Request (permitted read-only input)
        wr_path, wr_text = _read_work_request(Path(request.run_dir))
        if not wr_text.strip():
            return self._fail(request.task_id, "work_request_missing",
                              "no Work Request found under <run_dir>/inputs/")

        prompt = build_prompt(request, wr_path, wr_text, taxonomy)
        # snapshot the permitted read-only input so a modification can be detected
        wr_hash_before = None
        if wr_path is not None:
            from artifact_fingerprint import fingerprint as _fp
            wr_hash_before = _fp.sha256_file(wr_path)

        cmd_list = [self.command, *self.fixed_args]
        try:
            stdout, stderr, code, dur, timed_out = self._runner(cmd_list, prompt, self.timeout)
        except FileNotFoundError as exc:
            return self._fail(request.task_id, "command_not_found",
                              f"claude command not found: {self.command} ({exc})")
        except OSError as exc:
            return self._fail(request.task_id, "command_failed",
                              f"could not invoke claude command: {exc}")
        diag = [f"duration={dur:.2f}s", f"exit={code}"]  # no secrets

        # the executor must not have modified its read-only input
        if wr_path is not None and wr_hash_before is not None:
            from artifact_fingerprint import fingerprint as _fp
            if _fp.sha256_file(wr_path) != wr_hash_before:
                return self._fail(request.task_id, "input_modified",
                                  f"read-only Work Request was modified: {wr_path}", diag)

        if timed_out:
            return self._fail(request.task_id, "timeout",
                              f"claude command timed out after {self.timeout}s", diag)
        if code != 0:
            return self._fail(request.task_id, "nonzero_exit",
                              f"claude command exited {code}", diag)

        env, err = extract_single_json(stdout)
        if err:
            return self._fail(request.task_id, "invalid_output", err, diag)

        ok, reasons = validate_intent_result(env, request, taxonomy)
        if not ok:
            return self._fail(request.task_id, "schema_failure",
                              "; ".join(reasons), diag + reasons)

        # candidate primary output = canonical JSON envelope (valid JSON, valid YAML)
        candidate = (json.dumps(env, indent=2, sort_keys=False) + "\n").encode("utf-8")
        return TaskExecutionResult(
            task_id=request.task_id, status=ExecutorStatus.SUCCEEDED,
            output_bytes=candidate, validation_status="intent_result_valid",
            findings=env.get("findings", []), diagnostics=diag)
