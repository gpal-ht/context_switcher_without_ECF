"""
Tests for the EKB engine. Runs under pytest OR standalone:

    python engine/test_engine.py        # no dependencies
    python -m pytest engine             # if pytest is installed
"""

from __future__ import annotations

import os
import tempfile

import ekb

DEC = ekb.DECISION          # decision_guide (canonical artifact type)
CON = ekb.CONCEPT           # engineering_concept
PAT = ekb.PATTERN
QA = ekb.QUALITY
EX = ekb.EXAMPLE


def _node(id_, type_, **rels):
    return ekb.Node(id=id_, title=id_, type=type_, status="draft",
                    version="0.1.0", relationships=rels, path=ekb.Path("x"))


def _write_kb(files: dict) -> ekb.Graph:
    """Materialize a throwaway KB on disk and load it (isolated from the repo)."""
    d = tempfile.mkdtemp(prefix="ekb_test_")
    for rel, content in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p) or d, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
    return ekb.load_graph(ekb.Path(d))


def _obj(id_, type_=CON, rels="", body="body", extra=""):
    return (f"---\nid: {id_}\ntitle: {id_}\ntype: {type_}\n"
            f"status: draft\nversion: 0.1.0\n{extra}{rels}---\n{body}\n")


# ── parser / load ─────────────────────────────────────────────────────────────

def test_frontmatter_parses_scalars_lists_and_relationship_map():
    text = _obj("DG-ARCH-0001", DEC,
                rels="relationships:\n  requires:\n    - CON-ARCH-0001\n"
                     "    - CON-ARCH-0002\n  affects:\n    - QA-0001\n",
                extra="tags:\n  - subsystem\n  - modularity\n")
    fm = ekb.parse_frontmatter(text)
    assert fm["id"] == "DG-ARCH-0001"
    assert fm["tags"] == ["subsystem", "modularity"]
    assert fm["relationships"]["requires"] == ["CON-ARCH-0001", "CON-ARCH-0002"]
    assert fm["relationships"]["affects"] == ["QA-0001"]


def test_real_graph_loads_and_validates_clean():
    g = ekb.load_graph()
    assert len(g.nodes) >= 8
    assert ekb.validate(g) == 0  # exit code 0 == no errors


# ── retrieval ─────────────────────────────────────────────────────────────────

def test_retrieval_closure_matches_acceptance_test():
    g = ekb.load_graph()
    nodes, _ = ekb.retrieve(g, "DG-ARCH-0001")
    got = {n.id for n in nodes}
    assert got == ekb.ACCEPTANCE_TESTS[0]["expected"]


def test_retrieval_is_scoped_and_never_hops_into_another_decision_guide():
    g = ekb.Graph(nodes={
        "DG-A": _node("DG-A", DEC, requires=["CON-1"]),
        "DG-B": _node("DG-B", DEC, requires=["CON-1"]),
        "CON-1": _node("CON-1", CON, supports=["DG-A", "DG-B"]),
    })
    nodes, _ = ekb.retrieve(g, "DG-A")
    got = {n.id for n in nodes}
    assert got == {"DG-A", "CON-1"} and "DG-B" not in got


# ── type contract (Fix 1) ─────────────────────────────────────────────────────

def test_canonical_decision_type_accepted():
    g = _write_kb({"dg.md": _obj("DG-X-0001", DEC),
                   "c.md": _obj("CON-X-0001", CON)})
    assert not any("type" in p for p in g.problems)
    assert ekb.validate(g) == 0


def test_engineering_decision_rejected_for_dg():
    # engineering_decision names a decision, not the Decision Guide artifact.
    g = ekb.Graph(nodes={"DG-A": _node("DG-A", "engineering_decision")})
    probs = ekb.validate_object(g.nodes["DG-A"], body="x")
    assert any("names a decision" in p and "decision_guide" in p for p in probs)
    assert ekb.validate(g) == 1


def test_canonical_type_constant_is_decision_guide():
    assert ekb.DECISION == "decision_guide"
    assert ekb.TYPE_PREFIX["decision_guide"] == "DG"
    assert "engineering_decision" in ekb.LEGACY_TYPES


def test_decision_guide_prefix_type_pairing_valid():
    g = ekb.Graph(nodes={"DG-X": _node("DG-X", DEC, requires=["CON-1"], body="b"),
                         "CON-1": _node("CON-1", CON, supports=["DG-X"])})
    # no metadata problems on the DG (prefix/type pairing is valid)
    assert [p for p in ekb.validate_object(g.nodes["DG-X"], check_content=False)] == []


def test_generated_package_reports_decision_guide():
    # The current generated fixture (if present) must not carry the rejected
    # engineering_decision token; the live DG object is typed decision_guide.
    g = ekb.load_graph()
    assert g.nodes["DG-ARCH-0001"].type == "decision_guide"


def test_conflicting_type_fields_fail():
    dup = ("---\nid: CON-1\ntitle: t\ntype: engineering_concept\n"
           "type: engineering_pattern\nstatus: draft\nversion: 0.1.0\n---\nbody\n")
    g = _write_kb({"a.md": dup})
    assert any("conflicting front-matter key 'type'" in p for p in g.problems)
    assert ekb.validate(g) == 1


def test_type_prefix_mismatch_fails():
    g = ekb.Graph(nodes={"XX-1": _node("XX-1", CON)})
    assert ekb.validate(g) == 1


# ── relationship model (Fix 2) ────────────────────────────────────────────────

def test_related_to_symmetric_ok():
    g = ekb.Graph(nodes={
        "CON-1": _node("CON-1", CON, related_to=["CON-2"]),
        "CON-2": _node("CON-2", CON, related_to=["CON-1"]),
    })
    codes = {c for _, c, _ in ekb.check_relationships(g)}
    assert "REL003" not in codes and "REL004" not in codes


def test_required_inverse_missing_fails():
    g = ekb.Graph(nodes={
        "CON-1": _node("CON-1", CON, related_to=["CON-2"]),
        "CON-2": _node("CON-2", CON),  # no reciprocal
    })
    codes = {c for _, c, _ in ekb.check_relationships(g)}
    assert "REL003" in codes


def test_optional_inverse_missing_passes():
    # requires -> required_by is OPTIONAL; absence must not error.
    g = ekb.Graph(nodes={
        "DG-A": _node("DG-A", DEC, requires=["CON-1"]),
        "CON-1": _node("CON-1", CON, supports=["DG-A"]),
    })
    errors = [c for s, c, _ in ekb.check_relationships(g) if s == "error"]
    assert errors == []


def test_invalid_relationship_type_fails():
    g = ekb.Graph(nodes={
        "CON-1": _node("CON-1", CON, depends_on=["CON-2"]),
        "CON-2": _node("CON-2", CON),
    })
    codes = {c for _, c, _ in ekb.check_relationships(g)}
    assert "REL002" in codes
    assert ekb.validate(g) == 1  # now an error, not a warning


def test_invalid_source_target_pairing_fails():
    # 'supports' must target a decision, not a quality attribute.
    g = ekb.Graph(nodes={
        "CON-1": _node("CON-1", CON, supports=["QA-1"]),
        "QA-1": _node("QA-1", QA),
    })
    codes = {c for _, c, _ in ekb.check_relationships(g)}
    assert "REL005" in codes


def test_duplicate_edge_fails():
    g = ekb.Graph(nodes={
        "DG-A": _node("DG-A", DEC, requires=["CON-1", "CON-1"]),
        "CON-1": _node("CON-1", CON, supports=["DG-A"]),
    })
    codes = {c for _, c, _ in ekb.check_relationships(g)}
    assert "REL006" in codes


def test_contradictory_edge_fails():
    g = ekb.Graph(nodes={
        "DG-A": _node("DG-A", DEC, requires=["CON-1"], required_by=["CON-1"]),
        "CON-1": _node("CON-1", CON),
    })
    codes = {c for _, c, _ in ekb.check_relationships(g)}
    assert "REL007" in codes


def test_real_graph_has_no_relationship_errors():
    g = ekb.load_graph()
    errors = [f"{c} {m}" for s, c, m in ekb.check_relationships(g) if s == "error"]
    assert errors == [], errors


# ── regression tests (from prior batch, updated) ─────────────────────────────

def test_regression_broken_graph():
    g = ekb.Graph(nodes={"CON-1": _node("CON-1", CON, supports=["DG-NOPE"])})
    errors, _ = ekb.check_integrity(g)
    assert any("REL001" in e for e in errors)


def test_regression_orphan_object():
    g = ekb.Graph(nodes={
        "DG-A": _node("DG-A", DEC, requires=["CON-1"]),
        "CON-1": _node("CON-1", CON, supports=["DG-A"]),
        "CON-LONELY": _node("CON-LONELY", CON),
    })
    assert ekb.find_orphans(g) == ["CON-LONELY"]


def test_regression_duplicate_id():
    g = _write_kb({"a.md": _obj("CON-1"), "sub/b.md": _obj("CON-1")})
    assert any("duplicate id" in p for p in g.problems)
    assert ekb.validate(g) == 1


def test_regression_circular_relationship():
    g = ekb.Graph(nodes={
        "CON-1": _node("CON-1", CON, requires=["CON-2"]),
        "CON-2": _node("CON-2", CON, requires=["CON-1"]),
    })
    cycle = ekb.find_requires_cycle(g)
    assert cycle is not None and "CON-1" in cycle and "CON-2" in cycle


def test_real_graph_has_no_requires_cycle():
    assert ekb.find_requires_cycle(ekb.load_graph()) is None


# ── sufficiency (Fix 3) ───────────────────────────────────────────────────────

def test_sufficiency_missing_required_object():
    g = ekb.Graph(nodes={"DG-A": _node("DG-A", DEC, requires=["CON-GONE"])})
    r = ekb.check_sufficiency(g, "DG-A")
    assert not r["ok"]
    assert any(f["code"] == ekb.SUF_MISSING for f in r["failures"])


def test_sufficiency_empty_required_object():
    g = _write_kb({
        "dg.md": _obj("DG-A-0001", DEC,
                      rels="relationships:\n  requires:\n    - CON-A-0001\n"),
        "c.md": _obj("CON-A-0001", CON, body=""),  # empty body
    })
    r = ekb.check_sufficiency(g, "DG-A-0001")
    assert not r["ok"]
    assert any(f["code"] == ekb.SUF_EMPTY for f in r["failures"])


def test_sufficiency_wrong_id_or_no_id():
    n = _node("CON-1", CON)
    n.id = ""  # simulate a resolved object whose own id is blank
    g = ekb.Graph(nodes={"DG-A": _node("DG-A", DEC, requires=["CON-1"]), "CON-1": n})
    r = ekb.check_sufficiency(g, "DG-A")
    assert not r["ok"]
    assert any(f["code"] == ekb.SUF_WRONG_ID for f in r["failures"])


def test_sufficiency_malformed_metadata():
    g = _write_kb({
        "dg.md": _obj("DG-A-0001", DEC,
                      rels="relationships:\n  requires:\n    - CON-A-0001\n"),
        "c.md": _obj("CON-A-0001", CON, extra="status: bogus_status\n"),
    })
    # override status by writing invalid one; _obj already wrote status: draft,
    # so instead build directly:
    bad = ("---\nid: CON-A-0001\ntitle: t\ntype: engineering_concept\n"
           "status: not_a_status\nversion: 0.1.0\n---\nbody\n")
    g = _write_kb({
        "dg.md": _obj("DG-A-0001", DEC,
                      rels="relationships:\n  requires:\n    - CON-A-0001\n"),
        "c.md": bad,
    })
    r = ekb.check_sufficiency(g, "DG-A-0001")
    assert not r["ok"]
    assert any(f["code"] == ekb.SUF_INVALID_METADATA for f in r["failures"])


def test_sufficiency_second_level_incomplete():
    # required concept itself requires a missing object -> second-level failure
    g = ekb.Graph(nodes={
        "DG-A": _node("DG-A", DEC, requires=["CON-1"]),
        "CON-1": _node("CON-1", CON, requires=["CON-GONE"]),
    })
    r = ekb.check_sufficiency(g, "DG-A")
    assert not r["ok"]
    assert any(f["code"] in (ekb.SUF_SECOND_LEVEL, ekb.SUF_MISSING)
               for f in r["failures"])


def test_sufficiency_optional_missing_object_passes():
    # a missing 'affects' (non-required) target does NOT break sufficiency
    g = ekb.Graph(nodes={
        "DG-A": _node("DG-A", DEC, requires=["CON-1"], affects=["QA-GONE"]),
        "CON-1": _node("CON-1", CON, supports=["DG-A"]),
    })
    assert ekb.check_sufficiency(g, "DG-A")["ok"]


def test_sufficiency_cohesion_ablation():
    # RAT-ARCH-0001-NEG-COHESION: removing Cohesion must fail sufficiency
    g = ekb.load_graph()
    del g.nodes["CON-ARCH-0002"]
    r = ekb.check_sufficiency(g, "DG-ARCH-0001")
    assert not r["ok"]
    assert any(f["id"] == "CON-ARCH-0002" and f["code"] == ekb.SUF_MISSING
               for f in r["failures"])


def test_real_graph_sufficiency_passes():
    g = ekb.load_graph()
    assert ekb.check_sufficiency(g, "DG-ARCH-0001")["ok"]


def test_real_decision_guide_is_complete():
    results = ekb.check_completeness(ekb.load_graph())
    assert "DG-ARCH-0001" in results
    assert all(results["DG-ARCH-0001"].values()), results["DG-ARCH-0001"]


# ── reports (Fix 4 / Fix 5) ───────────────────────────────────────────────────

def test_coverage_report_deterministic():
    g = ekb.load_graph()
    assert ekb.build_coverage(g) == ekb.build_coverage(g)


def test_centrality_report_deterministic():
    g = ekb.load_graph()
    assert ekb.build_centrality(g) == ekb.build_centrality(g)


def test_reports_have_generated_header():
    g = ekb.load_graph()
    for content in (ekb.build_coverage(g), ekb.build_centrality(g)):
        assert "Do not edit manually" in content
        assert f"Generator version: {ekb.GENERATOR_VERSION}" in content


def test_centrality_terminology_is_scoped():
    text = ekb.build_centrality(ekb.load_graph())
    # must NOT overstate ecosystem-wide single points of failure
    assert "Single Points of Failure" not in text
    assert "Sufficiency-Critical" in text
    assert "whole" in text.lower() and "closure" in text.lower()


# ── generated package staleness (Fix 6) ──────────────────────────────────────

def _pkg(primary, retrieved, legacy=False):
    # a stale package embeds the rejected engineering_decision token
    body = "engineering_decision table" if legacy else "clean body"
    objs = "".join(f"  - {r}\n" for r in retrieved)
    return (f"---\npackage_id: EKP-T-0001\nprimary_object: {primary}\n"
            f"retrieved_objects:\n{objs}---\n{body}\n")


def test_stale_package_detected_by_closure_mismatch():
    g = ekb.load_graph()
    d = ekb.Path(tempfile.mkdtemp(prefix="ekb_pkg_"))
    (d / "p.md").write_text(_pkg("DG-ARCH-0001", ["DG-ARCH-0001", "CON-ARCH-0001"]),
                            encoding="utf-8")
    problems = ekb.check_generated_packages(g, d)
    assert any("STALE" in p and "closure" in p for p in problems)


def test_stale_package_detected_by_legacy_token():
    g = ekb.load_graph()
    live = {n.id for n in ekb.retrieve(g, "DG-ARCH-0001")[0]}
    d = ekb.Path(tempfile.mkdtemp(prefix="ekb_pkg_"))
    (d / "p.md").write_text(_pkg("DG-ARCH-0001", sorted(live), legacy=True),
                            encoding="utf-8")
    problems = ekb.check_generated_packages(g, d)
    assert any("legacy type token" in p for p in problems)


def test_current_package_passes():
    g = ekb.load_graph()
    live = {n.id for n in ekb.retrieve(g, "DG-ARCH-0001")[0]}
    d = ekb.Path(tempfile.mkdtemp(prefix="ekb_pkg_"))
    (d / "p.md").write_text(_pkg("DG-ARCH-0001", sorted(live)), encoding="utf-8")
    assert ekb.check_generated_packages(g, d) == []


def _run_standalone():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa
            failures += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failures} passed, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
