"""Tests for runtime-state storage: serialization round-trip, atomic writes, path safety."""

import sys
import tempfile
import unittest
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PKG))
sys.path.insert(0, str(_PKG.parent))

import storage as st  # noqa: E402


class TestSerialization(unittest.TestCase):
    def test_round_trip_state_shape(self):
        obj = {
            "schema_version": "0.1.0", "run_id": "RUN-1", "revision": 4,
            "active_task": None, "flag": True,
            "provenance": {"mode": "required", "schema_version": "0.1.0"},
            "task_states": {"TASK-A": "completed", "TASK-B": "not_started"},
            "failure": None,
        }
        self.assertEqual(st.load_yaml(st.dump_yaml(obj)), obj)

    def test_round_trip_manifest_shape(self):
        obj = {
            "schema_version": "0.1.0", "run_id": "RUN-2", "revision": 1,
            "executor": {"type": "tool", "tool": "runtime_state"},
            "tasks": [
                {"id": "TASK-A", "version": "0.1.0", "status": "completed", "output_hash": "abc"},
                {"id": "TASK-B", "version": "0.1.0", "status": "not_started"},
            ],
            "findings": [{"id": "F1", "classification": "minor", "task_id": "TASK-A"}],
            "tags": ["a", "b"],
            "trace_path": "trace.md",
        }
        self.assertEqual(st.load_yaml(st.dump_yaml(obj)), obj)

    def test_empty_containers(self):
        obj = {"executor": {}, "tasks": [], "note": "x"}
        self.assertEqual(st.load_yaml(st.dump_yaml(obj)), obj)

    def test_planner_compatible_output(self):
        import re
        txt = st.dump_yaml({"provenance": {"mode": "required"}, "run_status": "running"})
        m = re.search(r"^provenance:\s*\n((?:^[ \t]+.*\n?)+)", txt, re.M)
        self.assertTrue(m and "mode: required" in m.group(1))

    def test_json_round_trip(self):
        obj = {"owner": "x", "created_at": "2026-07-11T00:00:00Z", "n": 2}
        self.assertEqual(st.load_json(st.dump_json(obj)), obj)


class TestAtomicWrite(unittest.TestCase):
    def test_atomic_write_and_no_temp_left(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "state.yaml"
            st.atomic_write_text(p, "a: 1\n")
            self.assertEqual(st.read_text(p), "a: 1\n")
            leftovers = [x for x in Path(d).iterdir() if x.name.startswith(".tmp-")]
            self.assertEqual(leftovers, [])

    def test_atomic_write_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "o.bin"
            st.atomic_write_bytes(p, b"data")
            self.assertEqual(p.read_bytes(), b"data")


class TestPathSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name) / "run"
        self.run.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_rejects_absolute(self):
        with self.assertRaises(st.PathSafetyError):
            st.safe_join(self.run, "/etc/passwd")
        with self.assertRaises(st.PathSafetyError):
            st.safe_join(self.run, "C:/Windows/x")

    def test_rejects_traversal(self):
        with self.assertRaises(st.PathSafetyError):
            st.safe_join(self.run, "../escape.md")
        with self.assertRaises(st.PathSafetyError):
            st.safe_join(self.run, "task_outputs/../../escape.md")

    def test_allows_within(self):
        p = st.safe_join(self.run, "task_outputs/o.yaml")
        self.assertTrue(str(p).endswith("o.yaml"))

    def test_rejects_empty(self):
        with self.assertRaises(st.PathSafetyError):
            st.safe_join(self.run, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
