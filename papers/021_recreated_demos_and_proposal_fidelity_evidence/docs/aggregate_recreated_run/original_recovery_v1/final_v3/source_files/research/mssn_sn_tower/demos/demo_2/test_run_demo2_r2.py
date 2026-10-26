"""Historical R2 batch is preserved as proposal evidence only."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

_DEMO_DIR = Path(__file__).resolve().parent
if str(_DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(_DEMO_DIR))

from run_demo2 import HOPPING, audit_response_r2 as audit_response, replay_r2 as replay


def terms() -> list[dict]:
    return [{"move_type": "ASSERT_TERM", "ij": ij,
             "value": str(value), "term_type": "offdiag"}
            for ij, value in HOPPING.items()]


class R2AuditTests(unittest.TestCase):
    def test_historical_batch_does_not_certify(self) -> None:
        trace = Path(__file__).parent / "traces" / "demo2_r2_freefermion_1790207175.jsonl"
        receipt = replay(trace)
        self.assertEqual(receipt["model_responses"], 1)
        self.assertEqual(receipt["terminal"], "UNKNOWN_NOT_CERTIFIED")
        self.assertEqual(receipt["audits"][0]["status"], "BATCH_FORMAT_OBSERVED")
        self.assertTrue(receipt["audits"][0]["manifest_complete"])
        self.assertEqual(receipt["audits"][0]["witness_status"], "WITNESS_UNCHECKED")

    def test_label_only_xi_cannot_be_certified(self) -> None:
        batch = terms() + [{"move_type": "VERIFY_SIGN_FREE",
                            "xi_witness": {"type": "bipartite_symmetry"}}]
        result = audit_response(json.dumps(batch))
        self.assertEqual(result["terminal"], "UNKNOWN_NOT_CERTIFIED")

    def test_premature_verify_refused(self) -> None:
        batch = terms()[:1] + [{"move_type": "VERIFY_SIGN_FREE",
                                 "xi_witness": {"type": "wick_contraction"}}]
        result = audit_response(json.dumps(batch))
        self.assertEqual(result["status"], "REJECTED_BATCH")

    def test_duplicate_and_wrong_hopping_refused(self) -> None:
        duplicate = [terms()[0], terms()[0]]
        self.assertEqual(audit_response(json.dumps(duplicate))["status"],
                         "REJECTED_BATCH")
        wrong = terms()
        wrong[0]["value"] = "1"
        self.assertEqual(audit_response(json.dumps(wrong))["status"],
                         "REJECTED_BATCH")

    def test_non_json_constant_is_not_observed_as_a_valid_batch(self) -> None:
        batch = terms() + [{"move_type": "VERIFY_SIGN_FREE", "xi_witness": {}}]
        raw = json.dumps(batch)[:-1] + ',{"move_type":"ASSERT_TERM","value":NaN}]'
        self.assertEqual(audit_response(raw)["status"], "REJECTED_PARSE")

    def test_unhashable_hopping_id_is_a_refusal(self) -> None:
        for bad_id in ([], {}):
            result = audit_response(json.dumps([{
                "move_type": "ASSERT_TERM", "ij": bad_id,
                "value": "-1", "term_type": "offdiag",
            }]))
            self.assertEqual(result["status"], "REJECTED_BATCH")
            self.assertEqual(result["terminal"], "UNKNOWN_NOT_CERTIFIED")


if __name__ == "__main__":
    unittest.main()
