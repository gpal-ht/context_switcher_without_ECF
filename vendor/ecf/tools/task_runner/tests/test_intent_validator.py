"""Unit tests for the mechanical Engineering Intent Result validator + taxonomy loader."""

import copy
import sys
import unittest
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[2]
_REPO = _TOOLS.parent
sys.path.insert(0, str(_TOOLS))

from task_runner.executors.claude_code import (  # noqa: E402
    load_intent_taxonomy, validate_intent_result,
)
from task_runner.models import TaskExecutionRequest  # noqa: E402

TAXO = load_intent_taxonomy(_REPO)


def request(wr="WR-0001", tv="0.1.0"):
    return TaskExecutionRequest(
        run_id="R", work_request_id=wr, workflow_id="WF", workflow_version="0.1.0",
        task_id="TASK-CLASSIFY-0001", task_version=tv, task_spec_path="x",
        output_binding="task_outputs/engineering-intent.yaml")


def valid_env():
    return {
        "schema_version": "0.1.0", "task_id": "TASK-CLASSIFY-0001", "task_version": "0.1.0",
        "work_request_id": "WR-0001", "status": "completed",
        "engineering_intent": {"primary": "design_solution", "secondary": []},
        "classification_evidence": {"engineering_question": "Q?", "desired_outcome": "Rec",
                                    "requested_deliverables": ["Report"]},
        "confidence": {"level": "high", "justification": "because"},
        "findings": [],
    }


class TestTaxonomy(unittest.TestCase):
    def test_taxonomy_from_ekb(self):
        self.assertIn("design_solution", TAXO)
        self.assertIn("discover_problem", TAXO)
        self.assertGreaterEqual(len(TAXO), 8)


class TestValidator(unittest.TestCase):
    def ok(self, env):
        return validate_intent_result(env, request(), TAXO)[0]

    def fail_contains(self, env, needle, req=None):
        ok, reasons = validate_intent_result(env, req or request(), TAXO)
        self.assertFalse(ok)
        self.assertTrue(any(needle in r for r in reasons), msg=str(reasons))

    def test_valid_passes(self):
        self.assertTrue(self.ok(valid_env()))

    def test_invalid_primary_intent(self):
        e = valid_env(); e["engineering_intent"]["primary"] = "make_decision"
        self.fail_contains(e, "not in taxonomy")

    def test_secondary_not_in_taxonomy(self):
        e = valid_env(); e["engineering_intent"]["secondary"] = ["bogus_intent"]
        self.fail_contains(e, "not in taxonomy")

    def test_duplicate_primary_in_secondary(self):
        e = valid_env(); e["engineering_intent"]["secondary"] = ["design_solution"]
        self.fail_contains(e, "duplicated")

    def test_missing_evidence(self):
        e = valid_env(); del e["classification_evidence"]
        self.fail_contains(e, "classification_evidence missing")

    def test_missing_confidence_justification(self):
        e = valid_env(); e["confidence"]["justification"] = "  "
        self.fail_contains(e, "justification is empty")

    def test_invalid_confidence_level(self):
        e = valid_env(); e["confidence"]["level"] = "certain"
        self.fail_contains(e, "invalid confidence level")

    def test_work_request_mismatch(self):
        e = valid_env(); e["work_request_id"] = "WR-9999"
        self.fail_contains(e, "work_request_id mismatch")

    def test_task_version_mismatch(self):
        e = valid_env(); e["task_version"] = "0.0.9"
        self.fail_contains(e, "task_version mismatch")

    def test_task_id_mismatch(self):
        e = valid_env(); e["task_id"] = "TASK-CLASSIFY-0002"
        self.fail_contains(e, "task_id mismatch")

    def test_invalid_status(self):
        e = valid_env(); e["status"] = "approved"
        self.fail_contains(e, "invalid status")

    def test_recommendation_field_rejected(self):
        e = valid_env(); e["recommendation"] = "proceed"
        self.fail_contains(e, "prohibited field")

    def test_approval_claim_rejected(self):
        e = valid_env(); e["confidence"]["approval_granted"] = True
        self.fail_contains(e, "prohibited field")

    def test_unknown_top_level_field(self):
        e = valid_env(); e["extra_stuff"] = 1
        self.fail_contains(e, "unknown top-level field")

    def test_missing_primary(self):
        e = valid_env(); e["engineering_intent"]["primary"] = ""
        self.fail_contains(e, "exactly one primary intent")


if __name__ == "__main__":
    unittest.main(verbosity=2)
