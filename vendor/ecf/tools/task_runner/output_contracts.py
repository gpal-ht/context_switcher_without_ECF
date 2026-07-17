"""
Task-output contracts (runner-owned, executor-INDEPENDENT).

Invariant enforced here: **executor success is never sufficient for commit.**
The runner applies the task-specific output contract to EVERY executor's
candidate output — fixture, Claude Code, future providers, test doubles — before
provenance generation and commit. Task-specific validation must not live inside a
single executor (where non-Claude executors would bypass it).

This module has no AI, subprocess, or network dependency. It loads contract and
taxonomy truth from canonical ECF/EKB sources, never from executor output.

Registration:
    TASK_OUTPUT_VALIDATORS[task_id] -> validator(candidate_bytes, request, repo_root)
A registered validator is ALWAYS invoked for its task, regardless of executor.
Unknown tasks pass through generic validation only until a task-specific contract
exists.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# --------------------------------------------------------------------------- #
# Engineering-intent result contract (moved out of the Claude executor so it is
# enforced for every executor, not only Claude).
# --------------------------------------------------------------------------- #

ALLOWED_STATUS = {"completed", "completed_with_findings"}
ALLOWED_CONFIDENCE = {"high", "medium", "low", "unknown"}
ALLOWED_TOP_LEVEL = {
    "schema_version", "task_id", "task_version", "work_request_id", "status",
    "engineering_intent", "classification_evidence", "confidence", "findings",
}
PROHIBITED_KEY_RE = re.compile(r"recommend|approv|production", re.I)


def load_intent_taxonomy(repo_root) -> list:
    """Parse the allowed intent values from the bundled EKB Engineering Intent
    Model. Returns [] when the model is unavailable."""
    model = Path(repo_root) / "vendor" / "engineering_kb" / "foundations" / \
        "ENGINEERING_INTENT_MODEL.md"
    if not model.is_file():
        return []
    text = model.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^# Engineering Intent Taxonomy\s*$(.*)", text, re.M | re.S)
    body = m.group(1) if m else text
    values = re.findall(r"^##\s+([a-z_]+)\s*$", body, re.M)
    return [v for v in values if "_" in v]


def extract_single_json(text: str):
    """Return (obj, error). Requires EXACTLY one top-level JSON object and
    nothing else — rejects empty output, free-form/Markdown, trailing content,
    and multiple documents."""
    text = (text or "").strip()
    if not text:
        return None, "empty output (no JSON envelope)"
    objs, depth, start = [], 0, None
    in_str, esc = False, False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objs.append(text[start:i + 1])
                start = None
    if len(objs) == 0:
        return None, "no JSON object found (free-form output is not accepted)"
    if len(objs) > 1:
        return None, f"multiple JSON documents found ({len(objs)})"
    if objs[0].strip() != text:
        return None, "extra content outside the single JSON document"
    try:
        return json.loads(objs[0]), None
    except json.JSONDecodeError as exc:
        return None, f"malformed JSON: {exc}"


def _has_prohibited_key(obj) -> str | None:
    if isinstance(obj, dict):
        for k in obj:
            if PROHIBITED_KEY_RE.search(str(k)):
                return str(k)
        for v in obj.values():
            r = _has_prohibited_key(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _has_prohibited_key(v)
            if r:
                return r
    return None


def validate_intent_result(env: dict, request, taxonomy: list) -> tuple:
    """Return (ok, reasons). Mechanical; uses the authoritative taxonomy + request."""
    reasons = []
    if not isinstance(env, dict):
        return False, ["envelope is not a JSON object"]

    extra = set(env.keys()) - ALLOWED_TOP_LEVEL
    if extra:
        reasons.append(f"unknown top-level field(s): {sorted(extra)}")
    bad_key = _has_prohibited_key(env)
    if bad_key:
        reasons.append(f"prohibited field present (recommendation/approval/production): {bad_key}")

    if env.get("task_id") != request.task_id:
        reasons.append(f"task_id mismatch: {env.get('task_id')} != {request.task_id}")
    if str(env.get("task_version")) != str(request.task_version):
        reasons.append(f"task_version mismatch: {env.get('task_version')} != {request.task_version}")
    if env.get("work_request_id") != request.work_request_id:
        reasons.append(f"work_request_id mismatch: {env.get('work_request_id')} != {request.work_request_id}")
    if env.get("status") not in ALLOWED_STATUS:
        reasons.append(f"invalid status: {env.get('status')}")

    ei = env.get("engineering_intent")
    if not isinstance(ei, dict):
        reasons.append("engineering_intent missing or not an object")
    else:
        primary = ei.get("primary")
        secondary = ei.get("secondary", [])
        if not primary or not isinstance(primary, str):
            reasons.append("exactly one primary intent is required")
        elif primary not in taxonomy:
            reasons.append(f"primary intent '{primary}' not in taxonomy")
        if not isinstance(secondary, list):
            reasons.append("secondary must be a list")
        else:
            for s in secondary:
                if s not in taxonomy:
                    reasons.append(f"secondary intent '{s}' not in taxonomy")
            if primary in secondary:
                reasons.append("primary intent duplicated in secondary")
            if len(secondary) != len(set(secondary)):
                reasons.append("duplicate secondary intents")

    ev = env.get("classification_evidence")
    if not isinstance(ev, dict):
        reasons.append("classification_evidence missing")
    else:
        if not ev.get("engineering_question"):
            reasons.append("classification_evidence.engineering_question is empty")
        if not ev.get("desired_outcome"):
            reasons.append("classification_evidence.desired_outcome is empty")
        if not isinstance(ev.get("requested_deliverables"), list):
            reasons.append("classification_evidence.requested_deliverables must be a list")

    conf = env.get("confidence")
    if not isinstance(conf, dict):
        reasons.append("confidence missing")
    else:
        if conf.get("level") not in ALLOWED_CONFIDENCE:
            reasons.append(f"invalid confidence level: {conf.get('level')}")
        if not str(conf.get("justification") or "").strip():
            reasons.append("confidence.justification is empty")

    if "findings" in env and not isinstance(env["findings"], list):
        reasons.append("findings must be a list")

    return (len(reasons) == 0), reasons


# --------------------------------------------------------------------------- #
# Task-output validators + registry (executor-independent)
# --------------------------------------------------------------------------- #

def validate_engineering_intent_result(candidate, request, repo_root) -> tuple:
    """TASK-CLASSIFY-0001 full output contract over raw candidate bytes.

    Enforces: exactly one JSON envelope (no trailing/extra/free-form content),
    authoritative taxonomy from the EKB, and the complete intent-result contract.
    """
    try:
        text = candidate.decode("utf-8", errors="strict") \
            if isinstance(candidate, (bytes, bytearray)) else str(candidate)
    except Exception as exc:
        return False, [f"candidate is not valid UTF-8: {exc}"]
    env, err = extract_single_json(text)
    if err:
        return False, [err]
    taxonomy = load_intent_taxonomy(repo_root)
    if not taxonomy:
        return False, ["authoritative intent taxonomy unavailable (EKB intent model missing)"]
    return validate_intent_result(env, request, taxonomy)


# task_id -> validator(candidate_bytes, request, repo_root) -> (ok, reasons)
TASK_OUTPUT_VALIDATORS = {
    "TASK-CLASSIFY-0001": validate_engineering_intent_result,
}


def validate_task_output(task_id: str, candidate, request, repo_root) -> tuple:
    """Runner-owned dispatch. A registered validator is ALWAYS invoked for its
    task, regardless of which executor produced the candidate. Unknown tasks pass
    through (generic validation only) until a task-specific contract exists."""
    validator = TASK_OUTPUT_VALIDATORS.get(task_id)
    if validator is None:
        return True, []
    return validator(candidate, request, repo_root)
