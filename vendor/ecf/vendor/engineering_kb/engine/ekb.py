#!/usr/bin/env python3
"""
EKB engine — makes the Engineering Knowledge Base graph executable.

The KB defines a knowledge graph in version-controlled Markdown files, but until
now nothing parsed it, validated it, or performed the retrieval traversal the
models describe. This single-file, dependency-free CLI does three things:

  validate            Parse every Knowledge Object, check it against
                      KNOWLEDGE_OBJECT_STANDARD.md, and report broken references.

  retrieve <ID>       Traverse declared relationships from a primary object
                      (e.g. a Decision Guide) and print the smallest complete
                      body of supporting knowledge — the ENGINEERING_KNOWLEDGE_
                      RETRIEVAL_MODEL made real.

  test                Run the retrieval acceptance tests (RAT-*) as real
                      pass/fail checks.

Run from anywhere:  python engine/ekb.py <command>
"""

from __future__ import annotations

import sys

# Windows consoles default to cp1252; the retrieval tree uses box-drawing and
# arrow glyphs. Force UTF-8 so output is identical on every platform.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# ── Knowledge Object standard (from knowledge_model/KNOWLEDGE_OBJECT_STANDARD.md)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Bumped whenever validation semantics or report format change. Stamped into
# generated reports so a report identifies the engine that produced it.
GENERATOR_VERSION = "0.2.0"

REQUIRED_FIELDS = ["id", "title", "type", "status", "version"]
ALLOWED_STATUS = {"draft", "review", "approved", "deprecated", "superseded", "archived"}

# ── Canonical Knowledge Object types ─────────────────────────────────────────
# Canonical type strings (KNOWLEDGE_OBJECT_STANDARD.md). A Decision Guide's type
# names the ARTIFACT: `decision_guide` (ID prefix DG). `engineering_decision`
# names a decision rather than the guide, and is reserved for a possible future
# decision-record artifact — it is rejected for DG-* objects. See
# migrations/MIGRATION-0002-decision-guide-type-final.md.
DECISION = "decision_guide"
CONCEPT = "engineering_concept"
PATTERN = "engineering_pattern"
QUALITY = "quality_attribute"
EXAMPLE = "example"
REFERENCE = "reference"

TYPE_PREFIX = {
    DECISION: "DG",
    CONCEPT: "CON",
    PATTERN: "PAT",
    QUALITY: "QA",
    EXAMPLE: "EX",
    REFERENCE: "REF",
}

# Legacy/rejected type value -> canonical value. Presence of a legacy value on a
# Knowledge Object is an error. `engineering_decision` names a decision, not the
# Decision Guide artifact.
LEGACY_TYPES = {"engineering_decision": DECISION}

# Retrieval order from RETRIEVAL_ACCEPTANCE_TESTS.md: DG -> Concepts -> Pattern
# -> Quality Attributes -> Examples -> References.
TYPE_ORDER = {
    DECISION: 0, CONCEPT: 1, PATTERN: 2, QUALITY: 3, EXAMPLE: 4, REFERENCE: 5,
}

# Types that act as a decision-guide primary object (canonical only).
DECISION_TYPES = (DECISION,)

# ── Relationship policy (foundations/KNOWLEDGE_RELATIONSHIP_MODEL.md) ─────────
# For each relationship: symmetric?, inverse name, inverse requirement
# (required | optional | none), and allowed source/target types (None = any).
# inverse requirement semantics:
#   required — the target MUST declare the inverse back to the source (REL003)
#   optional — a back-edge is allowed but not required
#   none     — no inverse edge is expected
ANY = None
RELATIONSHIP_POLICY = {
    "requires":       dict(sym=False, inv="required_by",   inv_req="optional", src={DECISION, PATTERN}, tgt={CONCEPT, PATTERN}),
    "required_by":    dict(sym=False, inv="requires",      inv_req="optional", src={CONCEPT, PATTERN}, tgt={DECISION, PATTERN}),
    "supports":       dict(sym=False, inv="supported_by",  inv_req="optional", src={CONCEPT, PATTERN}, tgt={DECISION}),
    "supported_by":   dict(sym=False, inv="supports",      inv_req="optional", src={DECISION}, tgt={CONCEPT, PATTERN}),
    "illustrated_by": dict(sym=False, inv="illustrates",   inv_req="required", src=ANY, tgt={EXAMPLE}),
    "illustrates":    dict(sym=False, inv="illustrated_by", inv_req="none",    src={EXAMPLE}, tgt=ANY),
    "related_to":     dict(sym=True,  inv="related_to",    inv_req="required", src=ANY, tgt=ANY),
    "references":     dict(sym=False, inv=None,            inv_req="none",     src=ANY, tgt=ANY),
    "optimizes":      dict(sym=False, inv="optimized_by",  inv_req="optional", src={PATTERN}, tgt={QUALITY}),
    "optimized_by":   dict(sym=False, inv="optimizes",     inv_req="optional", src={QUALITY}, tgt={PATTERN}),
    "affects":        dict(sym=False, inv="affected_by",   inv_req="optional", src={DECISION, CONCEPT, PATTERN}, tgt={QUALITY}),
    "affected_by":    dict(sym=False, inv="affects",       inv_req="optional", src={QUALITY}, tgt={DECISION, CONCEPT, PATTERN}),
}
KNOWN_RELS = set(RELATIONSHIP_POLICY)

# Stable relationship validation codes (see KNOWLEDGE_RELATIONSHIP_MODEL.md).
REL_CODES = {
    "REL001": "unresolved relationship target",
    "REL002": "invalid relationship type",
    "REL003": "missing required inverse",
    "REL004": "invalid inverse relationship",
    "REL005": "invalid source/target type pairing",
    "REL006": "duplicate relationship edge",
    "REL007": "contradictory relationship declaration",
}


# ── Minimal YAML front-matter parser (no third-party dependency) ──────────────
# Handles exactly the subset the KB uses: top-level scalars, top-level lists,
# and one level of nested "key: -> list" maps (the relationships block).

def _indent(s: str) -> int:
    return len(s) - len(s.lstrip(" "))


def _rel(path: Path) -> str:
    """Display a path relative to the repo root, tolerating paths outside it."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except (ValueError, AttributeError):
        return str(path)


def _safe_read(path: Path) -> str:
    """Read a file's text, returning '' if it is missing/unreadable (synthetic
    in-memory nodes used in tests have a placeholder path)."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, AttributeError):
        return ""


def _strip(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def _parse_block(block: list[str]):
    """A block of indented lines is either a list ('- x') or a map of lists."""
    if not block:
        return []
    base = min(_indent(l) for l in block)
    first = next(l for l in block if _indent(l) == base)
    if first.lstrip().startswith("-"):
        return [_strip(l.lstrip()[1:]) for l in block
                if _indent(l) == base and l.lstrip().startswith("-")]
    result: dict[str, list[str]] = {}
    key = None
    for l in block:
        stripped = l.strip()
        if _indent(l) == base and stripped.endswith(":"):
            key = stripped[:-1].strip()
            result[key] = []
        elif stripped.startswith("-") and key is not None:
            result[key].append(_strip(stripped[1:]))
    return result


def _duplicate_top_keys(text: str) -> list[str]:
    """Return top-level front-matter keys that appear more than once.

    A duplicate `type:` (or any scalar key) is a conflicting declaration — the
    parser keeps the last, which would silently hide the conflict.
    """
    if not text.startswith("---"):
        return []
    lines = text.split("\n")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return []
    seen: dict[str, int] = {}
    for line in lines[1:end]:
        if line and _indent(line) == 0 and ":" in line and not line.lstrip().startswith("#"):
            key = line.split(":", 1)[0].strip()
            seen[key] = seen.get(key, 0) + 1
    return sorted(k for k, n in seen.items() if n > 1)


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    lines = text.split("\n")
    # locate the closing '---'
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}
    body = lines[1:end]
    data: dict = {}
    i, n = 0, len(body)
    while i < n:
        line = body[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if _indent(line) == 0 and ":" in line:
            key, _, rest = line.partition(":")
            key, rest = key.strip(), rest.strip()
            if rest:
                data[key] = _strip(rest)
                i += 1
            else:
                block = []
                j = i + 1
                while j < n and (not body[j].strip() or _indent(body[j]) > 0):
                    if body[j].strip():
                        block.append(body[j])
                    j += 1
                data[key] = _parse_block(block)
                i = j
        else:
            i += 1
    return data


# ── Model ─────────────────────────────────────────────────────────────────────

@dataclass
class Node:
    id: str
    title: str
    type: str
    status: str
    version: str
    relationships: dict[str, list[str]] = field(default_factory=dict)
    path: Path = None  # type: ignore

    def edges(self):
        """Yield (relationship_type, target_id) for every declared relationship."""
        for rel, targets in self.relationships.items():
            if isinstance(targets, list):
                for t in targets:
                    yield rel, t


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)  # (path, message) rendered


def load_graph(root: Path = REPO_ROOT) -> Graph:
    """Parse every .md with front-matter that declares an id into the graph."""
    g = Graph()
    skip_dirs = {".git", "generated", "artifacts", "engine"}
    for path in sorted(root.rglob("*.md")):
        if any(part in skip_dirs for part in path.relative_to(root).parts):
            continue
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if "id" not in fm:
            continue  # narrative doc, not a Knowledge Object
        for dup in _duplicate_top_keys(text):
            g.problems.append(f"{_rel(path)}: duplicate/conflicting front-matter "
                              f"key '{dup}'")
        rels = fm.get("relationships") or {}
        if not isinstance(rels, dict):
            rels = {}
        node = Node(
            id=str(fm.get("id", "")),
            title=str(fm.get("title", "")),
            type=str(fm.get("type", "")),
            status=str(fm.get("status", "")),
            version=str(fm.get("version", "")),
            relationships=rels,
            path=path,
        )
        if node.id in g.nodes:
            g.problems.append(f"{_rel(path)}: duplicate id {node.id} "
                              f"(also in {_rel(g.nodes[node.id].path)})")
        g.nodes[node.id] = node
    return g


# ── validate ──────────────────────────────────────────────────────────────────

def validate(g: Graph) -> int:
    """Standard conformance: per-object metadata + relationship policy."""
    errors = list(g.problems)
    warnings: list[str] = []
    for node in g.nodes.values():
        for p in validate_object(node):
            errors.append(f"{_rel(node.path)}: {p}")
    for severity, code, msg in check_relationships(g):
        line = f"[{code}] {msg}"
        (errors if severity == "error" else warnings).append(line)
    return _report("validate", g, errors, warnings)


# ── retrieve ──────────────────────────────────────────────────────────────────

def retrieve(g: Graph, start_id: str) -> tuple[list[Node], list[tuple[str, str, str]]]:
    """
    Traverse declared relationships outward from a primary object and return the
    scoped closure. We follow every declared edge but never hop *into* another
    Decision Guide, which keeps retrieval scoped to a single engineering
    decision (per the retrieval model: smallest useful body of knowledge).

    Returns (nodes_in_retrieval_order, discovery_edges) where discovery_edges is
    the tree of first-discovery relationships, for rendering a retrieval path.
    """
    if start_id not in g.nodes:
        raise KeyError(start_id)
    visited = {start_id}
    queue = [start_id]
    discovery: list[tuple[str, str, str]] = []  # (source, rel, target)
    while queue:
        current = queue.pop(0)
        for rel, target in g.nodes[current].edges():
            if target not in g.nodes:
                continue
            tnode = g.nodes[target]
            # never traverse into a different decision guide
            if tnode.type in DECISION_TYPES and target != start_id:
                continue
            if target not in visited:
                visited.add(target)
                discovery.append((current, rel, target))
                queue.append(target)
    ordered = sorted(
        (g.nodes[i] for i in visited),
        key=lambda nd: (TYPE_ORDER.get(nd.type, 99), nd.id),
    )
    return ordered, discovery


def cmd_retrieve(g: Graph, start_id: str) -> int:
    try:
        nodes, discovery = retrieve(g, start_id)
    except KeyError:
        print(f"error: no Knowledge Object with id '{start_id}'")
        return 2
    primary = g.nodes[start_id]
    print(f"Engineering question: {primary.title}")
    print(f"Primary object:       {primary.id} ({primary.type})\n")
    print(f"Retrieved {len(nodes)} objects (retrieval order):\n")
    label = {
        0: "Decision Guide", 1: "Concept", 2: "Pattern",
        3: "Quality Attribute", 4: "Example", 5: "Reference",
    }
    for nd in nodes:
        kind = label.get(TYPE_ORDER.get(nd.type, 99), nd.type)
        print(f"  {nd.id:<14} {kind:<18} {nd.title}")
    print("\nRetrieval path (first-discovery edges):\n")
    print(f"  {primary.id} ({primary.title})")
    children: dict[str, list[tuple[str, str]]] = {}
    for src, rel, tgt in discovery:
        children.setdefault(src, []).append((rel, tgt))

    def walk(node_id: str, depth: int):
        for rel, tgt in children.get(node_id, []):
            print(f"  {'  ' * depth}└─ {rel} → {tgt} ({g.nodes[tgt].title})")
            walk(tgt, depth + 1)

    walk(start_id, 1)

    result = check_sufficiency(g, start_id)
    print()
    if not result["ok"]:
        print("sufficiency: fail")
        for f_ in result["failures"]:
            print(f"  [{f_['code']}] {f_['id']}: {f_['detail']}")
        return 1
    print("sufficiency: pass — every required object resolves and validates")
    return 0


# ── acceptance tests (RAT-*) ────────────────────────────────────────────────

ACCEPTANCE_TESTS = [
    {
        "id": "RAT-ARCH-0001",
        "question": "Should I introduce another subsystem?",
        "primary": "DG-ARCH-0001",
        "expected": {
            "DG-ARCH-0001", "CON-ARCH-0001", "CON-ARCH-0002", "CON-ARCH-0003",
            "PAT-ARCH-0001", "QA-0001", "QA-0002", "EX-ARCH-0001",
        },
    },
]


def run_acceptance_tests(g: Graph) -> int:
    passed = 0
    failed = 0
    for t in ACCEPTANCE_TESTS:
        failures = []
        try:
            nodes, _ = retrieve(g, t["primary"])
        except KeyError:
            failures.append(f"primary object {t['primary']} not found")
            nodes = []
        got = {nd.id for nd in nodes}
        if t["primary"] not in got:
            failures.append("primary object not retrieved")
        missing = t["expected"] - got
        if missing:
            failures.append(f"missing expected objects: {sorted(missing)}")
        extra = got - t["expected"]
        if extra:
            failures.append(f"unexpected objects retrieved: {sorted(extra)}")
        if failures:
            failed += 1
            print(f"FAIL {t['id']}  — {t['question']}")
            for f_ in failures:
                print(f"       · {f_}")
        else:
            passed += 1
            print(f"PASS {t['id']}  — {t['question']}  ({len(got)} objects)")
    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


# ── graph analysis: degrees, orphans, relationship policy, cycles ─────────────

def build_degrees(g: Graph) -> dict:
    """Compute in/out-degree and incident edges for every node (resolved edges only)."""
    deg = {nid: {"in": 0, "out": 0, "in_from": [], "out_to": []} for nid in g.nodes}
    for node in g.nodes.values():
        for rel, target in node.edges():
            if target not in g.nodes:
                continue
            deg[node.id]["out"] += 1
            deg[node.id]["out_to"].append((rel, target))
            deg[target]["in"] += 1
            deg[target]["in_from"].append((rel, node.id))
    return deg


def find_orphans(g: Graph) -> list[str]:
    """Objects with no resolved relationships in either direction."""
    deg = build_degrees(g)
    return sorted(nid for nid, d in deg.items() if d["in"] == 0 and d["out"] == 0)


def check_relationships(g: Graph) -> list[tuple[str, str, str]]:
    """Validate every edge against RELATIONSHIP_POLICY.

    Returns a list of (severity, code, message) where severity is
    'error' or 'warning'. Codes are the stable REL001-REL007 values.
    """
    out: list[tuple[str, str, str]] = []

    def err(code, msg):
        out.append(("error", code, msg))

    def warn(code, msg):
        out.append(("warning", code, msg))

    for node in g.nodes.values():
        seen_edges = set()
        edge_set = {(rel, tgt) for rel, tgt in node.edges()}
        for rel, target in node.edges():
            # REL006 duplicate edge (same rel+target declared twice)
            if (rel, target) in seen_edges:
                err("REL006", f"{node.id}: duplicate edge {rel} → {target}")
                continue
            seen_edges.add((rel, target))

            # REL002 invalid relationship type
            policy = RELATIONSHIP_POLICY.get(rel)
            if policy is None:
                err("REL002", f"{node.id}: unknown relationship type '{rel}'")
                continue

            # REL001 unresolved target
            if target not in g.nodes:
                err("REL001", f"{node.id} --{rel}--> unresolved target '{target}'")
                continue
            tnode = g.nodes[target]

            # REL007 contradictory: same object declares rel and its inverse to target
            if policy["inv"] and (policy["inv"], target) in edge_set and not policy["sym"]:
                err("REL007", f"{node.id}: declares both {rel} and "
                              f"{policy['inv']} to {target}")

            # REL005 invalid source/target type pairing
            if policy["src"] is not None and node.type not in policy["src"]:
                err("REL005", f"{node.id} ({node.type}) may not be the source of "
                              f"'{rel}' (allowed: {sorted(policy['src'])})")
            if policy["tgt"] is not None and tnode.type not in policy["tgt"]:
                err("REL005", f"{node.id} --{rel}--> {target} ({tnode.type}): "
                              f"invalid target type (allowed: {sorted(policy['tgt'])})")

            # REL003 / REL004 inverse handling
            if policy["inv_req"] in ("required", "optional") and policy["inv"]:
                back = {r for r, t in tnode.edges() if t == node.id}
                if policy["inv"] in back:
                    pass  # correct inverse present
                elif back:
                    # a back-edge exists but with the wrong relationship name
                    if policy["inv_req"] == "required":
                        err("REL004", f"{target} points back to {node.id} via "
                                      f"{sorted(back)} but expected inverse "
                                      f"'{policy['inv']}' of '{rel}'")
                elif policy["inv_req"] == "required":
                    err("REL003", f"{node.id} --{rel}--> {target}: missing required "
                                  f"inverse '{policy['inv']}' on {target}")
    return out


def find_requires_cycle(g: Graph) -> list[str] | None:
    """Detect a cycle following only 'requires' edges — a circular dependency."""
    WHITE, GREY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in g.nodes}
    path: list[str] = []

    def dfs(nid: str):
        color[nid] = GREY
        path.append(nid)
        for rel, target in g.nodes[nid].edges():
            if rel != "requires" or target not in g.nodes:
                continue
            if color[target] == GREY:
                return path[path.index(target):] + [target]
            if color[target] == WHITE:
                found = dfs(target)
                if found:
                    return found
        path.pop()
        color[nid] = BLACK
        return None

    for nid in g.nodes:
        if color[nid] == WHITE:
            cyc = dfs(nid)
            if cyc:
                return cyc
    return None


def validate_object(node: Node, body: str | None = None,
                    check_content: bool = True) -> list[str]:
    """Per-object structural validation. Returns a list of problem strings.

    A Knowledge Object is well-formed only when its metadata validates, its ID
    matches its type prefix, and (when check_content) it has non-empty content.
    """
    problems = []
    for f_ in REQUIRED_FIELDS:
        if not getattr(node, f_):
            problems.append(f"missing required field '{f_}'")
    if node.type in LEGACY_TYPES:
        problems.append(
            f"type '{node.type}' names a decision, not the Decision Guide "
            f"artifact; use canonical '{LEGACY_TYPES[node.type]}'")
    elif node.type not in TYPE_PREFIX:
        problems.append(f"unknown type '{node.type}'")
    else:
        prefix = TYPE_PREFIX[node.type]
        if not node.id.startswith(prefix + "-"):
            problems.append(f"id '{node.id}' does not match type '{node.type}' "
                            f"(expected prefix {prefix}-)")
    if node.status and node.status not in ALLOWED_STATUS:
        problems.append(f"invalid status '{node.status}'")
    if check_content:
        if body is None:
            body = _safe_read(node.path)
        after_fm = re.sub(r"^---.*?---", "", body, count=1, flags=re.DOTALL).strip()
        if not after_fm:
            problems.append("no human-readable content (body is empty)")
    return problems


# Sufficiency failure reason codes (machine-readable).
SUF_MISSING = "MISSING"                 # required object file does not exist
SUF_WRONG_ID = "WRONG_ID"               # resolved but id mismatched
SUF_INVALID_METADATA = "INVALID_METADATA"
SUF_EMPTY = "EMPTY"                     # exists but no content
SUF_INCOMPLETE_CONTENT = "INCOMPLETE_CONTENT"  # DG missing required sections
SUF_MALFORMED_RELATIONSHIPS = "MALFORMED_RELATIONSHIPS"
SUF_SECOND_LEVEL = "SECOND_LEVEL_INCOMPLETE"


def check_sufficiency(g: Graph, primary_id: str) -> dict:
    """Strong sufficiency gate.

    A required object (a 'requires' target of the primary, transitively) is valid
    only when it resolves, its ID matches, its metadata validates, its required
    content structure validates, and its relationships resolve. 'File exists' is
    NOT sufficient. Returns {"ok": bool, "failures": [{id, code, detail}]}.
    """
    failures: list[dict] = []
    if primary_id not in g.nodes:
        return {"ok": False, "failures": [
            {"id": primary_id, "code": SUF_MISSING, "detail": "primary not found"}]}

    completeness = check_completeness(g)
    seen = set()

    def check_required(holder_id: str, depth: int):
        for rel, target in g.nodes[holder_id].edges():
            if rel != "requires":
                continue
            if target not in g.nodes:
                failures.append({"id": target, "code": SUF_MISSING,
                                 "detail": f"required by {holder_id}"})
                continue
            if target in seen:
                continue
            seen.add(target)
            tnode = g.nodes[target]
            exists = bool(tnode.path) and tnode.path.exists()
            body = _safe_read(tnode.path) if exists else ""
            # wrong id (frontmatter id != what the reference used) is caught by
            # load; here we re-affirm the node's own id is non-empty/consistent.
            if not tnode.id:
                failures.append({"id": target, "code": SUF_WRONG_ID,
                                 "detail": "object has no id"})
            probs = validate_object(tnode, body=body, check_content=exists)
            empty = [p for p in probs if "empty" in p]
            meta = [p for p in probs if p not in empty]
            if empty:
                failures.append({"id": target, "code": SUF_EMPTY,
                                 "detail": "; ".join(empty)})
            if meta:
                failures.append({"id": target, "code": SUF_INVALID_METADATA,
                                 "detail": "; ".join(meta)})
            if tnode.type in DECISION_TYPES and target in completeness:
                missing_sec = [k for k, v in completeness[target].items() if not v]
                if missing_sec:
                    failures.append({"id": target, "code": SUF_INCOMPLETE_CONTENT,
                                     "detail": f"missing sections: {missing_sec}"})
            # malformed relationships on the required object
            for r, t in tnode.edges():
                if r not in RELATIONSHIP_POLICY:
                    failures.append({"id": target, "code": SUF_MALFORMED_RELATIONSHIPS,
                                     "detail": f"invalid relationship '{r}'"})
                elif t not in g.nodes:
                    failures.append({"id": target, "code": SUF_SECOND_LEVEL,
                                     "detail": f"{r} → unresolved {t}"})
            check_required(target, depth + 1)

    check_required(primary_id, 0)
    # dedupe
    uniq = {(f["id"], f["code"], f["detail"]): f for f in failures}
    return {"ok": not uniq, "failures": list(uniq.values())}


def check_integrity(g: Graph) -> tuple[list[str], list[str]]:
    """Full knowledge-graph integrity pass (task 1 + relationship policy)."""
    errors = list(g.problems)  # duplicate ids / conflicting keys surfaced at load
    warnings: list[str] = []
    for node in g.nodes.values():
        for p in validate_object(node):
            errors.append(f"{_rel(node.path)}: {p}")
    for severity, code, msg in check_relationships(g):
        line = f"[{code}] {msg}"
        (errors if severity == "error" else warnings).append(line)
    for nid in find_orphans(g):
        warnings.append(f"orphan object (no relationships): {nid}")
    cyc = find_requires_cycle(g)
    if cyc:
        errors.append("circular 'requires' dependency: " + " → ".join(cyc))
    return errors, warnings


def cmd_integrity(g: Graph) -> int:
    errors, warnings = check_integrity(g)
    return _report("integrity", g, errors, warnings)


# ── decision-guide completeness (task 6) ─────────────────────────────────────

def _headings(text: str) -> list[str]:
    return [ln.strip("# ").strip().lower()
            for ln in text.split("\n") if ln.lstrip().startswith("#")]


def check_completeness(g: Graph) -> dict[str, dict[str, bool]]:
    """For each Decision Guide, which required elements are present.

    Required elements: alternatives, heuristics, forces, examples,
    related concepts, quality attributes.
    """
    results: dict[str, dict[str, bool]] = {}
    for node in g.nodes.values():
        if node.type not in DECISION_TYPES:
            continue
        headings = _headings(_safe_read(node.path))
        rels = node.relationships

        def has_heading(*keys):
            return any(any(k in h for h in headings) for k in keys)

        def has_edge(*names):
            return any(rels.get(n) for n in names)

        results[node.id] = {
            "alternatives": has_heading("alternative"),
            "heuristics": has_heading("heuristic"),
            "forces": has_heading("force"),
            "examples": has_edge("illustrated_by") or has_heading("example"),
            "related concepts": has_edge("requires") or has_heading("concept"),
            "quality attributes": has_edge("supports", "affects")
            or has_heading("quality attribute"),
        }
    return results


def cmd_completeness(g: Graph) -> int:
    results = check_completeness(g)
    print(f"Decision Guide completeness ({len(results)} guide(s)):\n")
    complete = 0
    for gid, elems in sorted(results.items()):
        missing = [k for k, v in elems.items() if not v]
        if missing:
            print(f"  INCOMPLETE {gid}: missing {', '.join(missing)}")
        else:
            complete += 1
            print(f"  COMPLETE   {gid}: all 6 required elements present")
    pct = (100 * complete / len(results)) if results else 0
    print(f"\n{complete}/{len(results)} complete ({pct:.0f}%)")
    return 0 if complete == len(results) else 1


# ── coverage report (task 3) ──────────────────────────────────────────────────

TYPE_LABELS = {
    DECISION: "Decision Guides",
    CONCEPT: "Concepts",
    PATTERN: "Patterns",
    QUALITY: "Quality Attributes",
    EXAMPLE: "Examples",
    REFERENCE: "References",
}
COVERAGE_CATEGORIES = [
    ("Decision Guides", DECISION_TYPES),
    ("Concepts", (CONCEPT,)),
    ("Patterns", (PATTERN,)),
    ("Quality Attributes", (QUALITY,)),
    ("Examples", (EXAMPLE,)),
    ("References", (REFERENCE,)),
]


def _generated_header(command: str) -> list[str]:
    """Deterministic provenance header for generated reports (Fix 4)."""
    return [
        "<!--",
        "Generated file. Do not edit manually.",
        "Generator: engine/ekb.py",
        f"Generator version: {GENERATOR_VERSION}",
        f"Command: {command}",
        "-->",
        "",
    ]


def _catalog_decision_guides() -> list[tuple[str, str, str]]:
    """Parse DECISION_GUIDE_CATALOG.md → [(id, title, status)]. Empty if absent."""
    path = REPO_ROOT / "decision_guides" / "DECISION_GUIDE_CATALOG.md"
    if not path.exists():
        return []
    rows = []
    row_re = re.compile(r"^\|\s*(DG-[A-Z0-9]+-\d+)\s*\|\s*(.+?)\s*\|.*\|\s*(\w[\w ]*?)\s*\|\s*$")
    for line in path.read_text(encoding="utf-8").split("\n"):
        m = row_re.match(line.strip())
        if m:
            rows.append((m.group(1), m.group(2), m.group(3)))
    return rows


def build_coverage(g: Graph) -> str:
    counts = {label: [] for label, _ in COVERAGE_CATEGORIES}
    for node in g.nodes.values():
        for label, types in COVERAGE_CATEGORIES:
            if node.type in types:
                counts[label].append(node)
    catalog = _catalog_decision_guides()
    authored_dg = {n.id for n in g.nodes.values() if n.type in DECISION_TYPES}
    planned = [(i, t, s) for (i, t, s) in catalog if i not in authored_dg]

    out = _generated_header("python engine/ekb.py coverage")
    out += ["# Knowledge Coverage Report", "",
            "## Object Counts", "", "| Category | Count |", "|---|---:|"]
    for label, _ in COVERAGE_CATEGORIES:
        out.append(f"| {label} | {len(counts[label])} |")
    out.append(f"| **Total Knowledge Objects** | **{len(g.nodes)}** |")

    for label, _ in COVERAGE_CATEGORIES:
        out += ["", f"## {label} ({len(counts[label])})", ""]
        if counts[label]:
            for n in sorted(counts[label], key=lambda x: x.id):
                out.append(f"- `{n.id}` — {n.title}")
        else:
            out.append("- _none authored yet_")

    out += ["", "## Decision Guide Catalog Status", ""]
    if catalog:
        done = [c for c in catalog if c[0] in authored_dg]
        out.append(f"- Catalog defines **{len(catalog)}** decision guides; "
                   f"**{len(done)}** authored, **{len(planned)}** planned.")
        out += ["", "### Missing (Planned but not authored)", ""]
        for i, t, s in planned:
            out.append(f"- `{i}` — {t} ({s})")
    else:
        out.append("- _catalog not found_")

    out += ["", "## Missing Knowledge (Gaps)", ""]
    gaps = []
    if len(counts["Patterns"]) <= 1:
        gaps.append("Only one Pattern exists; patterns are the thinnest object type.")
    if len(counts["References"]) == 0:
        gaps.append("No References exist — no external evidence is cited anywhere.")
    disciplines = {n.id.split("-")[1] for n in g.nodes.values()
                   if n.type in DECISION_TYPES and "-" in n.id}
    gaps.append(f"Only the '{', '.join(sorted(disciplines))}' discipline has an "
                f"authored decision guide; all other catalog disciplines are empty.")
    if planned:
        gaps.append(f"{len(planned)} catalog decision guides remain unauthored.")
    for gtext in gaps:
        out.append(f"- {gtext}")
    out.append("")
    return "\n".join(out)


def cmd_coverage(g: Graph) -> int:
    content = build_coverage(g)
    dest = REPO_ROOT / "coverage" / "knowledge_coverage.md"
    os.makedirs(dest.parent, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    print(f"Wrote {_rel(dest)}")
    print(content)
    return 0


# ── centrality report (task 4) ────────────────────────────────────────────────

def sufficiency_critical_objects(g: Graph) -> set[str]:
    """Objects a Decision Guide 'requires' — removing any fails that guide's
    sufficiency gate. Scoped to the specific guide(s), NOT the whole ecosystem."""
    s = set()
    for node in g.nodes.values():
        if node.type in DECISION_TYPES:
            for rel, target in node.edges():
                if rel == "requires" and target in g.nodes:
                    s.add(target)
    return s


def closure_centrality(g: Graph, primary_id: str) -> dict[str, int]:
    """In-degree of each object WITHIN one Decision Guide's retrieval closure."""
    if primary_id not in g.nodes:
        return {}
    nodes, _ = retrieve(g, primary_id)
    ids = {n.id for n in nodes}
    indeg = {nid: 0 for nid in ids}
    for nid in ids:
        for rel, target in g.nodes[nid].edges():
            if target in ids:
                indeg[target] += 1
    return indeg


def build_centrality(g: Graph) -> str:
    deg = build_degrees(g)
    critical = sufficiency_critical_objects(g)
    n_decisions = sum(1 for n in g.nodes.values() if n.type in DECISION_TYPES)

    out = _generated_header("python engine/ekb.py centrality")
    out += [
        "# Centrality Report", "",
        "Centrality here is measured **across the whole current knowledge graph**. ",
        "In-degree = how many objects point at this one; out-degree = how many it "
        "points at. High in-degree means high reuse, not operational fragility.", "",
        f"> Scope caveat: the graph currently contains **{n_decisions} Decision "
        f"Guide(s)**. With so few decisions, whole-graph centrality and a single "
        f"guide's local closure largely coincide; do not read ecosystem-wide "
        f"significance into these numbers yet.", "",
        "| ID | Type | In | Out | Sufficiency-critical |",
        "|---|---|---:|---:|:--:|",
    ]
    for nid in sorted(g.nodes, key=lambda n: (-deg[n]["in"], n)):
        t = TYPE_LABELS.get(g.nodes[nid].type, g.nodes[nid].type)
        flag = "yes" if nid in critical else ""
        out.append(f"| `{nid}` | {t} | {deg[nid]['in']} | {deg[nid]['out']} | {flag} |")

    # whole-graph high-centrality (high reuse)
    max_in = max((d["in"] for d in deg.values()), default=0)
    high_central = sorted(
        (nid for nid, d in deg.items()
         if d["in"] >= max(2, max_in - 1) and g.nodes[nid].type not in DECISION_TYPES),
        key=lambda nid: (-deg[nid]["in"], nid))
    out += ["", "## High-Centrality Objects (Whole Graph)", "",
            "Most-referenced supporting objects — high **reuse** across the graph:"]
    out += ([f"- `{nid}` — {g.nodes[nid].title} (in-degree {deg[nid]['in']})"
             for nid in high_central] or ["- _none_"])

    # local-closure load-bearing, per decision guide
    out += ["", "## Load-Bearing Within a Decision Closure", "",
            "In-degree measured **inside each Decision Guide's retrieval closure** "
            "(local, not ecosystem-wide):"]
    any_dg = False
    for dg in sorted(n.id for n in g.nodes.values() if n.type in DECISION_TYPES):
        any_dg = True
        cc = closure_centrality(g, dg)
        top = sorted((i for i in cc if i != dg), key=lambda i: (-cc[i], i))[:3]
        out.append(f"- **{dg}**: " + ", ".join(
            f"`{i}` ({cc[i]})" for i in top) if top else f"- **{dg}**: _none_")
    if not any_dg:
        out.append("- _no decision guides_")

    # sufficiency-critical
    out += ["", "## Sufficiency-Critical Objects", "",
            "Objects a Decision Guide **requires** — removing any makes *that guide's* "
            "package fail its sufficiency gate (empirically confirmed by EXP-0003, "
            "Cohesion ablation). This is a per-guide dependency, not an EKB-wide "
            "single point of failure:"]
    out += ([f"- `{nid}` — {g.nodes[nid].title} "
             f"(whole-graph in-degree {deg[nid]['in']}, required by a decision guide)"
             for nid in sorted(critical, key=lambda n: (-deg[n]["in"], n))]
            or ["- _none_"])
    out.append("")
    return "\n".join(out)


def cmd_centrality(g: Graph) -> int:
    content = build_centrality(g)
    dest = REPO_ROOT / "coverage" / "centrality_report.md"
    os.makedirs(dest.parent, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    print(f"Wrote {_rel(dest)}")
    print(content)
    return 0


# ── generated package staleness (Fix 6) ─────────────────────────────────────

GENERATED_PACKAGES_DIR = REPO_ROOT / "generated" / "packages"


def check_generated_packages(g: Graph, directory: Path = None) -> list[str]:
    """Compare each generated Engineering Knowledge Package's declared
    retrieved_objects against the live retrieval closure. Stale packages
    (produced before a migration) are reported so they fail a check rather than
    masquerading as current. Generated packages are transient, non-canonical
    artifacts (artifacts/ENGINEERING_KNOWLEDGE_PACKAGE_CONTRACT.md)."""
    directory = directory or GENERATED_PACKAGES_DIR
    problems: list[str] = []
    if not directory.exists():
        return problems
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        primary = fm.get("primary_object") or fm.get("generated_from")
        declared = fm.get("retrieved_objects")
        if not primary or not isinstance(declared, list):
            problems.append(f"{_rel(path)}: missing primary_object / "
                            f"retrieved_objects metadata (cannot verify)")
            continue
        if primary not in g.nodes:
            problems.append(f"{_rel(path)}: primary {primary} no longer exists")
            continue
        live_nodes, _ = retrieve(g, primary)
        live = {n.id for n in live_nodes}
        if set(declared) != live:
            problems.append(
                f"{_rel(path)}: STALE — declared closure {sorted(declared)} != "
                f"current closure {sorted(live)}")
        # embeds a legacy type token → produced before the type migration
        for legacy in LEGACY_TYPES:
            if re.search(rf"\b{re.escape(legacy)}\b", text):
                problems.append(f"{_rel(path)}: STALE — embeds legacy type token "
                                f"'{legacy}' (pre-migration output)")
    return problems


def cmd_packages(g: Graph) -> int:
    problems = check_generated_packages(g)
    if not GENERATED_PACKAGES_DIR.exists():
        print("No generated packages directory; nothing to check.")
        return 0
    for p in problems:
        print(f"  STALE:   {p}")
    if problems:
        print(f"\npackages: {len(problems)} stale/invalid generated package(s). "
              f"These are non-canonical artifacts and must be regenerated, not "
              f"hand-edited.")
        return 1
    print("packages: all generated packages match the current graph.")
    return 0


# ── reporting / cli ───────────────────────────────────────────────────────────

def _report(name: str, g: Graph, errors: list[str], warnings: list[str]) -> int:
    print(f"Loaded {len(g.nodes)} Knowledge Objects from {REPO_ROOT}\n")
    for w in warnings:
        print(f"  warning: {w}")
    for e in errors:
        print(f"  ERROR:   {e}")
    print()
    if errors:
        print(f"{name}: FAILED — {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"{name}: OK — 0 errors, {len(warnings)} warning(s)")
    return 0


USAGE = """usage: python engine/ekb.py <command> [args]

commands:
  validate            Validate every Knowledge Object + relationship policy.
  integrity           Full graph integrity: types, relationship policy
                      (REL001-REL007), orphans, circular 'requires'.
  retrieve <ID>       Retrieve the knowledge closure for a primary object
                      (with a strong sufficiency gate), e.g. retrieve DG-ARCH-0001
  completeness        Check every Decision Guide has all required sections.
  coverage            Write coverage/knowledge_coverage.md.
  centrality          Write coverage/centrality_report.md.
  packages            Check generated Engineering Knowledge Packages for staleness.
  test                Run retrieval acceptance tests (RAT-*).
  list                List all loaded Knowledge Objects.
"""


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    cmd = argv[0]
    g = load_graph()
    if cmd == "validate":
        return validate(g)
    if cmd == "integrity":
        return cmd_integrity(g)
    if cmd == "completeness":
        return cmd_completeness(g)
    if cmd == "coverage":
        return cmd_coverage(g)
    if cmd == "centrality":
        return cmd_centrality(g)
    if cmd == "packages":
        return cmd_packages(g)
    if cmd == "retrieve":
        if len(argv) < 2:
            print("error: retrieve requires an object ID, e.g. DG-ARCH-0001")
            return 2
        return cmd_retrieve(g, argv[1])
    if cmd == "test":
        return run_acceptance_tests(g)
    if cmd == "list":
        for nd in sorted(g.nodes.values(), key=lambda n: n.id):
            print(f"  {nd.id:<14} {nd.type:<20} {nd.title}")
        return 0
    print(f"error: unknown command '{cmd}'\n")
    print(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
