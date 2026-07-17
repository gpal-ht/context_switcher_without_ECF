#!/usr/bin/env python3
"""
ECF Workflow Conformance Validator.

Read-only, mechanical validation of an ECF workflow specification (for example
`workflows/reasoning/WF-REASON-0001-engineering-recommendation.md`).

It answers one question:

    Is this workflow structurally safe and internally consistent enough for an
    execution runner to consume?

It validates the ECF *control plane*. It does NOT execute engineering reasoning,
invoke any AI, run any task, or modify any file. See README.md.

Standard library only. No third-party dependencies, no network access.

Exit codes:
    0  valid            (no error-severity findings)
    1  validation errors (one or more error-severity findings)
    2  validator execution/configuration failure
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

ALLOWED_WORKFLOW_STATUSES = {
    "planned", "draft", "review", "approved",
    "released", "deprecated", "superseded", "archived",
}

LEGACY_RUNTIME_ROOTS = (
    "runtime/work_requests/",
    "runtime/reasoning_runs/",
    "runtime/production_runs/",
)

CANONICAL_RUNTIME_ROOT = "runtime/runs/"

# Phrases that mark a line as legacy/compatibility documentation (WF011).
LEGACY_MARKERS = ("legacy", "non-authoritative", "superseded", "historical", "compatibility")

# Negation tokens used to distinguish a prohibition from an assertion.
NEGATIONS = ("not ", "never", "without", "no ", "must not", "does not", "cannot", "n't")

# Vague dependency phrases forbidden for trace/manifest/finalization tasks (WF016).
VAGUE_DEP_PHRASES = (
    "all previous", "all prior", "all task outputs", "all task results",
    "all reasoning outputs", "every prior", "complete reasoning run",
)

# Chain-of-thought phrases (WF017).
COT_PHRASES = ("private chain-of-thought", "private chain of thought",
               "hidden reasoning", "internal token-level", "token-level reasoning")

# Trace/manifest/finalization tasks that require explicit dependencies (WF016).
TRACE_TASKS = {"TASK-TRACE-0001", "TASK-TRACE-0002", "TASK-TRACE-0003"}

# Runtime-infrastructure files (run-root): runtime-owned, continuously mutated by
# the transaction layer, and NEVER task-owned outputs. Matched by exact bound
# path (a subdir path like reports/final-manifest.yaml is a different artifact).
RUNTIME_INFRA_FILES = ("state.yaml", "manifest.yaml")

# Required terminal artifacts for a reasoning workflow (WF015):
#  - runtime-infrastructure files must be documented (present in the spec text);
#  - task-owned terminal artifacts must be BOUND task outputs.
REQUIRED_INFRA_ARTIFACTS = ("state.yaml", "manifest.yaml")
REQUIRED_TERMINAL_BINDINGS = ("trace.md", "final-manifest.yaml", "completion.yaml")

REASONING_EXIT_STATE = "waiting_for_human_approval"

TASK_ID_RE = re.compile(r"TASK-[A-Z]+-\d{4}")
SEMVER_RE = re.compile(r"\d+\.\d+\.\d+")


# --------------------------------------------------------------------------- #
# Result model
# --------------------------------------------------------------------------- #

@dataclass
class Check:
    code: str
    status: str            # "passed" | "failed" | "skipped"
    message: str
    severity: str = "error"  # "error" | "warning"

    def to_dict(self) -> dict:
        return {"code": self.code, "status": self.status, "message": self.message}


@dataclass
class ValidationResult:
    workflow_id: str
    source_path: str
    checks: list = field(default_factory=list)

    def add(self, code, status, message, severity="error"):
        self.checks.append(Check(code, status, message, severity))

    @property
    def errors(self) -> list:
        return [c for c in self.checks if c.status == "failed" and c.severity == "error"]

    @property
    def warnings(self) -> list:
        return [c for c in self.checks if c.status == "failed" and c.severity == "warning"]

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0


# --------------------------------------------------------------------------- #
# Read-only file access
# --------------------------------------------------------------------------- #

def read_text(path: Path) -> str:
    """Read a file as UTF-8 with line endings normalized to LF. Read-only."""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n").replace("\r", "\n")


# --------------------------------------------------------------------------- #
# Parsing helpers (stdlib only; no YAML dependency)
# --------------------------------------------------------------------------- #

def parse_front_matter(text: str) -> dict:
    """Parse the leading `--- ... ---` YAML front matter as flat key: value."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        line = line.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        km = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if km:
            fm[km.group(1)] = km.group(2).strip()
    return fm


def parse_binding_table(text: str) -> list:
    """
    Parse the 'Stable Output Bindings' table.

    Returns a list of dicts: {task_id, version, output, line} in table order,
    preserving duplicates so WF006/WF010 can detect them.
    """
    rows = []
    for i, line in enumerate(text.split("\n"), start=1):
        m = re.match(
            r"^\|\s*(TASK-[A-Z]+-\d{4})\s*\|\s*([0-9][0-9.]*)\s*\|\s*`([^`]+)`\s*\|",
            line,
        )
        if m:
            rows.append({
                "task_id": m.group(1),
                "version": m.group(2).strip(),
                "output": m.group(3).strip(),
                "line": i,
            })
    return rows


def parse_depends_on(text: str) -> dict:
    """Parse the machine-readable `depends_on:` YAML block into {task: [deps]}."""
    m = re.search(r"```yaml\s*\ndepends_on:\n(.*?)```", text, re.S)
    if not m:
        return {}
    deps: dict = {}
    current = None
    for line in m.group(1).split("\n"):
        head = re.match(r"^  (TASK-[A-Z]+-\d{4}):\s*(\[\s*\])?\s*$", line)
        if head:
            current = head.group(1)
            deps[current] = []
            continue
        item = re.match(r"^\s+-\s*(TASK-[A-Z]+-\d{4})\s*$", line)
        if item and current is not None:
            deps[current].append(item.group(1))
    return deps


def parse_steps(text: str) -> list:
    """
    Parse '## Step N — Title' blocks.

    Returns list of dicts: {seq, task_id, upstream_line, inputs_line, body}.
    """
    steps = []
    parts = re.split(r"\n## Step (\d+)\b[^\n]*\n", text)
    # parts = [pre, seq1, body1, seq2, body2, ...]
    for idx in range(1, len(parts), 2):
        seq = int(parts[idx])
        body = parts[idx + 1]
        tid = None
        tm = re.search(r"\*\s*Task:\s*(TASK-[A-Z]+-\d{4})", body)
        if tm:
            tid = tm.group(1)
        up = re.search(r"\*\s*Upstream:\s*(.*)", body)
        inp = re.search(r"\*\s*Required inputs:\s*(.*)", body)
        steps.append({
            "seq": seq,
            "task_id": tid,
            "upstream_line": up.group(1) if up else "",
            "inputs_line": inp.group(1) if inp else "",
            "body": body,
        })
    return steps


def parse_task_meta(text: str) -> tuple:
    """
    Extract (task_id, version) from a task specification, supporting both the
    YAML front-matter style and the prose '## Identity' style.
    """
    tid = None
    ver = None
    m = re.search(r"^task_id:\s*(TASK-[A-Z]+-\d{4})", text, re.M)
    if m:
        tid = m.group(1)
    m = re.search(r"^version:\s*(\d+\.\d+\.\d+)", text, re.M)
    if m:
        ver = m.group(1)
    if tid is None:
        m = re.search(r"^Task ID\s*\n\s*\n\s*(TASK-[A-Z]+-\d{4})", text, re.M)
        if m:
            tid = m.group(1)
    if ver is None:
        m = re.search(r"^Version\s*\n\s*\n\s*(\d+\.\d+\.\d+)", text, re.M)
        if m:
            ver = m.group(1)
    return tid, ver


def parse_catalog(text: str) -> dict:
    """
    Parse WORKFLOW_CATALOG.md field tables into {workflow_id: {field: value}}.

    Recognizes '| Field | Value |' rows within a '## <ID> — <name>' section.
    """
    catalog: dict = {}
    current_id = None
    for line in text.split("\n"):
        sec = re.match(r"^##\s+(WF-[A-Z]+-\d{4})\b", line)
        if sec:
            current_id = sec.group(1)
            catalog.setdefault(current_id, {})
            continue
        row = re.match(r"^\|\s*([A-Za-z ]+?)\s*\|\s*(.+?)\s*\|\s*$", line)
        if row and current_id:
            key = row.group(1).strip().lower()
            val = row.group(2).strip()
            catalog[current_id][key] = val
        # Planned-workflow table rows: | WF-... | name | category | status | notes |
        planned = re.match(r"^\|\s*(WF-[A-Z]+-\d{4})\s*\|(.+)\|\s*$", line)
        if planned and "workflow id" not in line.lower():
            wid = planned.group(1)
            cols = [c.strip() for c in planned.group(2).split("|")]
            if wid not in catalog and len(cols) >= 3:
                catalog[wid] = {"name": cols[0], "category": cols[1], "status": cols[2]}
    return catalog


def leaf(path: str) -> str:
    return path.replace("\\", "/").split("/")[-1]


PROHIBITION_INTRO_RE = re.compile(
    r"^\s*[-*]?\s*("
    r"prohibited|"
    r"(the )?(workflow|task) (shall|must) not|"
    r"(the )?(workflow|task) must never|"
    r"must not|shall not|must never|it must not"
    r")\b.*:?\s*$",
    re.I,
)


def prohibition_flags(text: str) -> list:
    """
    Return a per-line boolean: True when the line sits inside a prohibition
    block (a 'Prohibited:'/'must not:' intro followed by bullet items).

    This lets us treat bulleted prohibitions as prohibitions even though the
    negation word is only on the introducing line.
    """
    lines = text.split("\n")
    flags = [False] * len(lines)
    in_block = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if PROHIBITION_INTRO_RE.match(line):
            in_block = True
            flags[i] = True
            continue
        if in_block:
            if stripped == "" or re.match(r"^\s*[-*]\s+", line):
                flags[i] = True          # blank or bullet continues the block
            else:
                in_block = False         # any other content ends the block
    return flags


# --------------------------------------------------------------------------- #
# Workflow model
# --------------------------------------------------------------------------- #

@dataclass
class Workflow:
    path: Path
    text: str
    front_matter: dict
    bindings: list        # list of {task_id, version, output, line}
    depends_on: dict
    steps: list

    @property
    def workflow_id(self) -> str:
        return self.front_matter.get("workflow_id", "")

    @property
    def task_ids(self) -> list:
        return [b["task_id"] for b in self.bindings]


def load_workflow(path: Path) -> Workflow:
    text = read_text(path)
    return Workflow(
        path=path,
        text=text,
        front_matter=parse_front_matter(text),
        bindings=parse_binding_table(text),
        depends_on=parse_depends_on(text),
        steps=parse_steps(text),
    )


# --------------------------------------------------------------------------- #
# Repository index (tasks + catalog + other workflows)
# --------------------------------------------------------------------------- #

class RepoIndex:
    def __init__(self, repo_root: Path, tasks_dir: Path, catalog_path: Path,
                 workflows_dir: Path):
        self.repo_root = repo_root
        self.tasks_dir = tasks_dir
        self.catalog_path = catalog_path
        self.workflows_dir = workflows_dir
        self.task_versions: dict = {}   # task_id -> list of (path, version)
        self.catalog: dict = {}
        self.workflow_ids: dict = {}    # workflow_id -> list of paths
        self._index_tasks()
        self._index_catalog()
        self._index_workflows()

    def _index_tasks(self):
        if not self.tasks_dir.is_dir():
            return
        for p in sorted(self.tasks_dir.rglob("TASK-*.md")):
            try:
                tid, ver = parse_task_meta(read_text(p))
            except OSError:
                continue
            if tid:
                self.task_versions.setdefault(tid, []).append((p, ver))

    def _index_catalog(self):
        if self.catalog_path and self.catalog_path.is_file():
            self.catalog = parse_catalog(read_text(self.catalog_path))

    def _index_workflows(self):
        if not self.workflows_dir.is_dir():
            return
        for p in sorted(self.workflows_dir.rglob("*.md")):
            fm = parse_front_matter(read_text(p))
            wid = fm.get("workflow_id")
            if wid:
                self.workflow_ids.setdefault(wid, []).append(p)


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

CHECKS: list = []  # registry of (code, function)


def check(code: str):
    def deco(fn: Callable):
        CHECKS.append((code, fn))
        return fn
    return deco


def _err(res, code, msg):
    res.add(code, "failed", msg, severity="error")


def _ok(res, code, msg):
    res.add(code, "passed", msg)


def _warn(res, code, msg):
    res.add(code, "failed", msg, severity="warning")


@check("WF002")
def wf002_metadata(wf, idx, res):
    required = ["workflow_id", "name", "version", "status", "category",
                "owner", "entry_state", "successful_exit_state"]
    missing = [k for k in required if not wf.front_matter.get(k)]
    if missing:
        _err(res, "WF002",
             f"{wf.path}: missing/empty workflow metadata field(s): {', '.join(missing)}.")
    else:
        _ok(res, "WF002", "All required workflow metadata fields are present.")


@check("WF003")
def wf003_unique_id(wf, idx, res):
    wid = wf.workflow_id
    paths = idx.workflow_ids.get(wid, [])
    if len(paths) > 1:
        _err(res, "WF003",
             f"Workflow ID {wid} is declared in {len(paths)} specifications: "
             + ", ".join(str(p) for p in paths))
    else:
        _ok(res, "WF003", f"Workflow ID {wid} is unique.")


@check("WF004")
def wf004_tasks_resolve(wf, idx, res):
    unresolved = []
    ambiguous = []
    for tid in sorted(set(wf.task_ids)):
        matches = idx.task_versions.get(tid, [])
        if not matches:
            unresolved.append(tid)
        elif len(matches) > 1:
            ambiguous.append(tid)
    if unresolved:
        _err(res, "WF004",
             f"{wf.workflow_id}: task ID(s) resolve to no specification: "
             f"{', '.join(unresolved)}. Source: {wf.path}")
    if ambiguous:
        _err(res, "WF004",
             f"{wf.workflow_id}: task ID(s) resolve to multiple specifications: "
             f"{', '.join(ambiguous)}.")
    if not unresolved and not ambiguous:
        _ok(res, "WF004", f"{len(set(wf.task_ids))} task IDs resolved.")


@check("WF005")
def wf005_versions_match(wf, idx, res):
    failed = False
    for b in wf.bindings:
        tid, pinned = b["task_id"], b["version"]
        matches = idx.task_versions.get(tid, [])
        if not matches:
            continue  # WF004 reports unresolved
        _, actual = matches[0]
        if actual is None:
            _warn(res, "WF005", f"{tid} has no parseable version in its specification.")
            continue
        if pinned != actual:
            failed = True
            _err(res, "WF005",
                 f"{tid} pins version {pinned}, but its task specification declares "
                 f"{actual}. Source: {wf.path}")
    if not failed:
        _ok(res, "WF005", "All pinned task versions match their specifications.")


@check("WF006")
def wf006_unique_tasks(wf, idx, res):
    seen: dict = {}
    for b in wf.bindings:
        seen.setdefault(b["task_id"], []).append(b["line"])
    dups = {t: ls for t, ls in seen.items() if len(ls) > 1}
    if dups:
        detail = "; ".join(f"{t} at lines {ls}" for t, ls in dups.items())
        _err(res, "WF006",
             f"{wf.workflow_id}: task(s) appear more than once (repeated invocation "
             f"is not declared for this workflow): {detail}.")
    else:
        _ok(res, "WF006", "Each task appears exactly once.")


@check("WF007")
def wf007_deps_resolve(wf, idx, res):
    task_set = set(wf.task_ids)
    bad = []
    for t, deps in wf.depends_on.items():
        for d in deps:
            if d not in task_set:
                bad.append(f"{t} -> {d}")
    if bad:
        _err(res, "WF007",
             f"{wf.workflow_id}: depends_on references task(s) not present in the "
             f"workflow: {', '.join(bad)}.")
    else:
        _ok(res, "WF007", "All depends_on task IDs are present in the workflow.")


@check("WF008")
def wf008_acyclic(wf, idx, res):
    graph = wf.depends_on
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    cycle_path = []

    def dfs(node, stack):
        color[node] = GREY
        for m in graph.get(node, []):
            if m not in color:
                continue
            if color[m] == GREY:
                cycle_path.extend(stack + [node, m])
                return True
            if color[m] == WHITE and dfs(m, stack + [node]):
                return True
        color[node] = BLACK
        return False

    for n in list(graph):
        if color[n] == WHITE and dfs(n, []):
            break
    if cycle_path:
        _err(res, "WF008",
             f"{wf.workflow_id}: dependency cycle detected: "
             f"{' -> '.join(cycle_path)}.")
    else:
        _ok(res, "WF008", "Dependency graph is acyclic.")


@check("WF009")
def wf009_io_continuity(wf, idx, res):
    """
    Every backticked required-input filename in a step must be produced by a
    bound task output, be a workflow-managed run artifact, or be a declared
    workflow input. Prose-only inputs (no backticks) are skipped with a note.
    """
    produced = {leaf(b["output"]) for b in wf.bindings}
    # workflow-managed / declared inputs available to steps
    available = set(produced) | {
        "state.yaml", "manifest.yaml", "trace.md", "completion.yaml",
    }
    # declared workflow inputs (from the Required Inputs table): Work Request, EKB
    unresolved = []
    skipped_prose = 0
    for st in wf.steps:
        backticked = re.findall(r"`([^`]+)`", st["inputs_line"])
        if not backticked and st["inputs_line"].strip():
            skipped_prose += 1
        for ref in backticked:
            name = leaf(ref)
            if name.endswith((".yaml", ".yml", ".md", ".json")) and name not in available:
                unresolved.append(f"step {st['seq']} ({st['task_id']}) needs '{name}'")
    if unresolved:
        _err(res, "WF009",
             f"{wf.workflow_id}: required input(s) not produced upstream or declared: "
             + "; ".join(unresolved) + ".")
    else:
        note = f" ({skipped_prose} prose-only input line(s) not machine-checked)" if skipped_prose else ""
        _ok(res, "WF009", f"All backticked required inputs map to an upstream output{note}.")


@check("WF010")
def wf010_unique_outputs(wf, idx, res):
    by_path: dict = {}
    for b in wf.bindings:
        by_path.setdefault(b["output"], []).append(b["task_id"])
    dups = {p: ts for p, ts in by_path.items() if len(ts) > 1}
    multi = [b["task_id"] for b in wf.bindings]
    if dups:
        detail = "; ".join(f"{p} <- {', '.join(ts)}" for p, ts in dups.items())
        _err(res, "WF010", f"{wf.workflow_id}: duplicate output binding(s): {detail}.")
    elif len(multi) != len(set(multi)):
        _err(res, "WF010", f"{wf.workflow_id}: a task has more than one output binding.")
    else:
        _ok(res, "WF010", f"{len(wf.bindings)} unique output bindings.")


@check("WF011")
def wf011_canonical_root(wf, idx, res):
    offenders = []
    for i, line in enumerate(wf.text.split("\n"), start=1):
        for legacy in LEGACY_RUNTIME_ROOTS:
            if legacy in line and not any(mark in line.lower() for mark in LEGACY_MARKERS):
                offenders.append(f"line {i}: {legacy}")
    if offenders:
        _err(res, "WF011",
             f"{wf.workflow_id}: non-canonical runtime root(s) outside legacy "
             f"documentation: {'; '.join(offenders)}. Use {CANONICAL_RUNTIME_ROOT}<RUN_ID>/.")
    else:
        _ok(res, "WF011", f"All runtime paths use {CANONICAL_RUNTIME_ROOT}<RUN_ID>/.")


@check("WF012")
def wf012_ordering(wf, idx, res):
    seq_of = {st["task_id"]: st["seq"] for st in wf.steps if st["task_id"]}
    violations = []
    for t, deps in wf.depends_on.items():
        if t not in seq_of:
            continue
        for d in deps:
            if d in seq_of and seq_of[d] >= seq_of[t]:
                violations.append(f"{t} (step {seq_of[t]}) depends on {d} (step {seq_of[d]})")
    if violations:
        _err(res, "WF012",
             f"{wf.workflow_id}: task(s) sequenced before a dependency: "
             + "; ".join(violations) + ".")
    else:
        _ok(res, "WF012", "Task ordering respects all declared dependencies.")


@check("WF013")
def wf013_final_state(wf, idx, res):
    exit_state = wf.front_matter.get("successful_exit_state", "")
    if wf.front_matter.get("category") == "reasoning" or wf.workflow_id == "WF-REASON-0001":
        if exit_state != REASONING_EXIT_STATE:
            _err(res, "WF013",
                 f"{wf.workflow_id}: successful_exit_state is '{exit_state}', "
                 f"expected '{REASONING_EXIT_STATE}'.")
        else:
            _ok(res, "WF013", f"Successful exit state is '{REASONING_EXIT_STATE}'.")
    else:
        _ok(res, "WF013", f"Successful exit state is '{exit_state}'.")


@check("WF014")
def wf014_approval_boundary(wf, idx, res):
    """
    Fail if the workflow asserts (not merely prohibits) crossing the approval
    boundary. Report production by TASK-PRODUCE-0001 is explicitly allowed.
    """
    offenders = []
    patterns = [
        (r"approval[_ ]granted\s*[:=]?\s*true", "claims approval granted"),
        (r"\bgrants?\s+approval\b", "grants approval"),
        (r"\binvoke[sd]?\b[^.\n]*production engine", "invokes the Production Engine"),
        (r"\bpromote[sd]?\b[^.\n]*canonical", "promotes canonical artifacts"),
        (r"\b(modif|writ|edit)[a-z]*\b[^.\n]*(project source|source code)", "modifies project source"),
    ]
    prohibited = prohibition_flags(wf.text)
    for i, line in enumerate(wf.text.split("\n"), start=1):
        low = line.lower()
        for pat, label in patterns:
            if re.search(pat, low):
                # allow if the line is negated inline or sits in a prohibition block
                if any(neg in low for neg in NEGATIONS) or prohibited[i - 1]:
                    continue
                offenders.append(f"line {i}: {label}")
    if offenders:
        _err(res, "WF014",
             f"{wf.workflow_id}: human-approval boundary violated: "
             + "; ".join(offenders) + ".")
    else:
        _ok(res, "WF014",
            "Human-approval boundary preserved (report production is permitted; "
            "no production-engine invocation or approval grant asserted).")


@check("WF015")
def wf015_terminal_artifacts(wf, idx, res):
    if wf.front_matter.get("successful_exit_state") != REASONING_EXIT_STATE:
        _ok(res, "WF015", "Not a reasoning-terminal workflow; terminal-artifact check skipped.")
        return
    bound_leaves = {leaf(b["output"]) for b in wf.bindings}
    text_low = wf.text.lower()
    missing = []
    # Runtime-infrastructure files are workflow-managed (never task bindings);
    # they need only be documented in the spec.
    for art in REQUIRED_INFRA_ARTIFACTS:
        if art.lower() not in text_low:
            missing.append(f"{art} (runtime infrastructure; must be documented)")
    # Task-owned terminal artifacts must be BOUND task outputs.
    for art in REQUIRED_TERMINAL_BINDINGS:
        if art not in bound_leaves:
            missing.append(f"{art} (task-owned terminal artifact; must be a bound output)")
    # report + validation result must be bound task outputs
    has_report = any(leaf(b["output"]).endswith("recommendation-report.md") for b in wf.bindings)
    has_validation = any("validation" in leaf(b["output"]) for b in wf.bindings)
    if not has_report:
        missing.append("engineering-recommendation-report.md (report)")
    if not has_validation:
        missing.append("recommendation-report-validation.yaml (validation result)")
    if missing:
        _err(res, "WF015",
             f"{wf.workflow_id}: missing required terminal artifact binding(s): "
             + ", ".join(missing) + ".")
    else:
        _ok(res, "WF015", "All required terminal artifacts are bound/declared.")


@check("WF016")
def wf016_explicit_trace_deps(wf, idx, res):
    problems = []
    for st in wf.steps:
        if st["task_id"] in TRACE_TASKS:
            up_low = st["upstream_line"].lower()
            if any(v in up_low for v in VAGUE_DEP_PHRASES):
                problems.append(f"step {st['seq']} ({st['task_id']}) uses a vague Upstream phrase")
            if not TASK_ID_RE.findall(st["upstream_line"]):
                problems.append(f"step {st['seq']} ({st['task_id']}) has no explicit Upstream task IDs")
    for t in TRACE_TASKS:
        if t in wf.task_ids:
            if not wf.depends_on.get(t):
                problems.append(f"{t} has no explicit depends_on entry")
    if problems:
        _err(res, "WF016",
             f"{wf.workflow_id}: trace/manifest/finalization dependencies must be "
             f"explicit: {'; '.join(problems)}.")
    else:
        _ok(res, "WF016", "Trace, manifest, and finalization tasks have explicit dependencies.")


@check("WF017")
def wf017_no_private_cot(wf, idx, res):
    offenders = []
    prohibited = prohibition_flags(wf.text)
    for i, line in enumerate(wf.text.split("\n"), start=1):
        low = line.lower()
        for phrase in COT_PHRASES:
            if phrase in low and not any(neg in low for neg in NEGATIONS) and not prohibited[i - 1]:
                offenders.append(f"line {i}: '{phrase}'")
    if offenders:
        _err(res, "WF017",
             f"{wf.workflow_id}: workflow requires private/hidden reasoning: "
             + "; ".join(offenders) + ". Only observable rationale is permitted.")
    else:
        _ok(res, "WF017", "No private chain-of-thought requirement found.")


@check("WF018")
def wf018_catalog_consistency(wf, idx, res):
    wid = wf.workflow_id
    entry = idx.catalog.get(wid)
    if not entry:
        _err(res, "WF018",
             f"{wid} is not present in the Workflow Catalog ({idx.catalog_path}).")
        return
    mismatches = []
    checks = {
        "version": wf.front_matter.get("version", ""),
        "status": wf.front_matter.get("status", ""),
        "entry state": wf.front_matter.get("entry_state", ""),
        "exit state": wf.front_matter.get("successful_exit_state", ""),
    }
    for field_name, wf_val in checks.items():
        cat_val = entry.get(field_name)
        if cat_val is not None and cat_val.strip().lower() != wf_val.strip().lower():
            mismatches.append(f"{field_name}: workflow='{wf_val}' catalog='{cat_val}'")
    # task count
    cat_count = entry.get("task count")
    if cat_count and cat_count.isdigit() and int(cat_count) != len(wf.task_ids):
        mismatches.append(f"task count: workflow={len(wf.task_ids)} catalog={cat_count}")
    if mismatches:
        _err(res, "WF018", f"{wid}: catalog mismatch — " + "; ".join(mismatches) + ".")
    else:
        _ok(res, "WF018", "Workflow metadata is consistent with the catalog.")


@check("WF019")
def wf019_status_allowed(wf, idx, res):
    status = wf.front_matter.get("status", "").strip().lower()
    if status not in ALLOWED_WORKFLOW_STATUSES:
        _err(res, "WF019",
             f"{wf.workflow_id}: status '{status}' is not an allowed workflow "
             f"status ({', '.join(sorted(ALLOWED_WORKFLOW_STATUSES))}).")
    else:
        _ok(res, "WF019", f"Workflow status '{status}' is allowed.")


@check("WF020")
def wf020_referenced_files(wf, idx, res):
    pattern = re.compile(
        r"\b((?:execution|workflows|knowledge|artifacts|tasks|work_requests)/"
        r"[A-Za-z0-9_./-]+\.md)\b"
    )
    refs = sorted(set(pattern.findall(wf.text)))
    missing = [r for r in refs if not (idx.repo_root / r).exists()]
    if missing:
        _err(res, "WF020",
             f"{wf.workflow_id}: referenced normative file(s) do not exist: "
             + ", ".join(missing) + ".")
    else:
        _ok(res, "WF020", f"All {len(refs)} referenced normative file path(s) exist.")


@check("WF021")
def wf021_no_infra_binding(wf, idx, res):
    """
    A task output must not be bound to a runtime-infrastructure file.

    `state.yaml` and the run-root `manifest.yaml` are runtime-owned and are
    continuously mutated by the transaction layer (revision-coupled). Binding a
    task's immutable, provenance-tracked output to one of them causes the planner
    to read the task as already-produced (and, in required mode, stale) from the
    moment the run is initialized. Task-owned final artifacts belong under an
    immutable output location (e.g. `reports/`). Matched by exact bound path so a
    sub-directory artifact such as `reports/final-manifest.yaml` is unaffected.
    """
    infra = set(RUNTIME_INFRA_FILES)
    offenders = [f"{b['task_id']} -> {b['output']}"
                 for b in wf.bindings
                 if b["output"].replace("\\", "/").strip() in infra]
    if offenders:
        _err(res, "WF021",
             f"{wf.workflow_id}: task output(s) bound to runtime-infrastructure "
             f"file(s): {', '.join(offenders)}. state.yaml and the run-root "
             "manifest.yaml are runtime-owned and must not be task outputs; use an "
             "immutable output location such as reports/.")
    else:
        _ok(res, "WF021",
            "No task output is bound to a runtime-infrastructure file "
            "(state.yaml / run-root manifest.yaml).")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def validate(path: Path, idx: RepoIndex) -> ValidationResult:
    wf = load_workflow(path)
    res = ValidationResult(workflow_id=wf.workflow_id or "(unknown)",
                           source_path=str(path))
    # WF001 handled by caller (readability). Metadata first.
    for code, fn in CHECKS:
        try:
            fn(wf, idx, res)
        except Exception as exc:  # a check crashing is a validator config failure
            res.add(code, "failed",
                    f"validator internal error in {code}: {exc}", severity="error")
    return res, wf


def build_summary(wf: Workflow) -> dict:
    edge_count = sum(len(v) for v in wf.depends_on.values())
    return {
        "task_count": len(wf.task_ids),
        "edge_count": edge_count,
        "output_binding_count": len(wf.bindings),
    }


# --------------------------------------------------------------------------- #
# Output rendering
# --------------------------------------------------------------------------- #

def render_text(res: ValidationResult, summary: dict) -> str:
    lines = []
    verdict = "VALID" if res.valid else "INVALID"
    lines.append(f"Workflow: {res.workflow_id}")
    lines.append(f"Source:   {res.source_path}")
    lines.append(f"Result:   {verdict}")
    lines.append(f"Summary:  {summary['task_count']} tasks, "
                 f"{summary['edge_count']} edges, "
                 f"{summary['output_binding_count']} output bindings")
    lines.append("")
    for c in res.checks:
        if c.status == "passed":
            lines.append(f"  [PASS] {c.code}: {c.message}")
    for c in res.checks:
        if c.status == "failed" and c.severity == "warning":
            lines.append(f"  [WARN] {c.code}: {c.message}")
    for c in res.checks:
        if c.status == "failed" and c.severity == "error":
            lines.append(f"  [FAIL] {c.code} ERROR: {c.message}")
    lines.append("")
    lines.append(f"{len(res.errors)} error(s), {len(res.warnings)} warning(s).")
    return "\n".join(lines)


def render_json(res: ValidationResult, summary: dict) -> str:
    return json.dumps({
        "workflow_id": res.workflow_id,
        "valid": res.valid,
        "errors": [c.to_dict() for c in res.errors],
        "warnings": [c.to_dict() for c in res.warnings],
        "checks": [c.to_dict() for c in res.checks],
        "summary": summary,
    }, indent=2)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def resolve_repo_root(explicit: str | None, workflow_path: Path) -> Path:
    if explicit:
        return Path(explicit).resolve()
    # tools/workflow_validator/validate_workflow.py -> repo root is parents[2]
    here = Path(__file__).resolve()
    candidate = here.parents[2]
    if (candidate / "tasks").is_dir():
        return candidate
    # fall back to searching upward from the workflow file
    for parent in workflow_path.resolve().parents:
        if (parent / "tasks").is_dir() and (parent / "workflows").is_dir():
            return parent
    return candidate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only conformance validator for ECF workflow specifications.")
    parser.add_argument("workflow", help="Path to the workflow specification (.md).")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--repo-root", default=None,
                        help="Repository root (default: inferred).")
    parser.add_argument("--tasks-dir", default=None,
                        help="Task specifications directory (default: <repo>/tasks).")
    parser.add_argument("--catalog", default=None,
                        help="Workflow catalog path (default: <repo>/workflows/WORKFLOW_CATALOG.md).")
    args = parser.parse_args(argv)

    workflow_path = Path(args.workflow)
    if not workflow_path.is_file():
        sys.stderr.write(f"WF001 ERROR: workflow file not readable: {workflow_path}\n")
        return 2
    try:
        read_text(workflow_path)
    except OSError as exc:
        sys.stderr.write(f"WF001 ERROR: cannot read workflow file: {exc}\n")
        return 2

    try:
        repo_root = resolve_repo_root(args.repo_root, workflow_path)
        tasks_dir = Path(args.tasks_dir).resolve() if args.tasks_dir else repo_root / "tasks"
        catalog_path = (Path(args.catalog).resolve() if args.catalog
                        else repo_root / "workflows" / "WORKFLOW_CATALOG.md")
        workflows_dir = repo_root / "workflows"
        idx = RepoIndex(repo_root, tasks_dir, catalog_path, workflows_dir)
    except Exception as exc:
        sys.stderr.write(f"WF-CONFIG ERROR: could not build repository index: {exc}\n")
        return 2

    res, wf = validate(workflow_path, idx)
    # WF001 explicit pass (file was read successfully above).
    res.checks.insert(0, Check("WF001", "passed", "Workflow file is readable."))
    summary = build_summary(wf)

    out = render_json(res, summary) if args.format == "json" else render_text(res, summary)
    print(out)
    return 0 if res.valid else 1


if __name__ == "__main__":
    sys.exit(main())
