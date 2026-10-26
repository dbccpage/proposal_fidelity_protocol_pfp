"""Host-gate regressions for the historical false R1 terminal."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

_DEMO_DIR = Path(__file__).resolve().parent
if str(_DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(_DEMO_DIR))

from run_demo2 import R1Governor, TFI_MATRIX, run_replay_r1 as run_replay, run_scripted_r1 as run_scripted


def full_matrix() -> dict:
    return {"move_type": "ASSERT_MATRIX",
            "matrix": [[str(value) for value in row] for row in TFI_MATRIX]}


class R1GovernorTests(unittest.TestCase):
    def test_scripted_identity_gauge_is_only_restricted_repair(self) -> None:
        receipt = run_scripted()
        self.assertEqual(receipt["terminal"], "RestrictedSignGaugeRepair")
        self.assertIsNone(receipt["bqnf_phi1_zero"])

    def test_incomplete_matrix_cannot_verify(self) -> None:
        host = R1Governor()
        host.evaluate(json.dumps({"move_type": "ASSERT_TERM", "ij": "0->1",
                                  "value": "-1/2", "term_type": "offdiag"}), 1)
        result = host.evaluate(json.dumps({"move_type": "VERIFY_REPAIR",
                                           "gauge": [0, 0, 0, 0]}), 2)
        self.assertEqual(result["status"], "RefusedIncompleteManifest")
        self.assertIsNone(host.terminal)

    def test_wrong_entry_duplicate_and_float_refused(self) -> None:
        host = R1Governor()
        wrong = {"move_type": "ASSERT_TERM", "ij": "0->1",
                 "value": "1/2", "term_type": "offdiag"}
        self.assertEqual(host.evaluate(json.dumps(wrong), 1)["status"],
                         "RefusedEntryMismatch")
        wrong["value"] = "-1/2"
        self.assertTrue(host.evaluate(json.dumps(wrong), 2)["admitted"])
        self.assertEqual(host.evaluate(json.dumps(wrong), 3)["status"],
                         "RefusedDuplicateAssertion")
        float_move = {"move_type": "ASSERT_TERM", "ij": "0->2",
                      "value": -0.5, "term_type": "offdiag"}
        self.assertEqual(host.evaluate(json.dumps(float_move), 4)["status"],
                         "RefusedMalformedMove")

    def test_fake_xi_is_not_a_gauge_certificate(self) -> None:
        host = R1Governor()
        host.evaluate(json.dumps(full_matrix()), 1)
        result = host.evaluate(json.dumps({"move_type": "VERIFY_SIGN_FREE",
                                           "xi_witness": {"type": "identity"},
                                           "phi1_claim": 0}), 2)
        self.assertEqual(result["status"], "RefusedWrongWitnessRoute")
        self.assertIsNone(host.terminal)

    def test_bad_gauge_refused_after_full_manifest(self) -> None:
        host = R1Governor()
        host.evaluate(json.dumps(full_matrix()), 1)
        result = host.evaluate(json.dumps({"move_type": "VERIFY_REPAIR",
                                           "gauge": [1, 0, 0, 0]}), 2)
        self.assertEqual(result["status"], "RefusedGaugeDoesNotRepair")

    def test_batch_is_atomic_on_invalid_witness(self) -> None:
        host = R1Governor()
        batch = [full_matrix(), {"move_type": "VERIFY_SIGN_FREE",
                                 "xi_witness": {"type": "anything"}}]
        result = host.evaluate(json.dumps(batch), 1)
        self.assertEqual(result["status"], "RefusedBatchItem")
        self.assertEqual(host.asserted, {})
        self.assertIsNone(host.terminal)

    def test_batch_valid_repair(self) -> None:
        host = R1Governor()
        batch = [full_matrix(), {"move_type": "VERIFY_REPAIR", "gauge": [0] * 4}]
        result = host.evaluate(json.dumps(batch), 1)
        self.assertEqual(result["status"], "BatchAdmitted")
        self.assertEqual(host.terminal, "RestrictedSignGaugeRepair")

    def test_duplicate_json_key_refused(self) -> None:
        host = R1Governor()
        result = host.evaluate('{"move_type":"ASSERT_MATRIX","move_type":"VERIFY_REPAIR"}', 1)
        self.assertEqual(result["status"], "RefusedMalformedMove")

    def test_nonstandard_or_inexact_json_cannot_assert_matrix(self) -> None:
        for token in ("NaN", "Infinity", "-Infinity", "1e10000", "0.5"):
            with self.subTest(token=token):
                host = R1Governor()
                raw = json.dumps(full_matrix())[:-1] + ',"host_verdict":' + token + '}'
                self.assertEqual(host.evaluate(raw, 1)["status"], "RefusedMalformedMove")
                self.assertEqual(host.asserted, {})

    def test_historical_trace_no_longer_certifies(self) -> None:
        trace = Path(__file__).parent / "traces" / "demo2_r1_stoquastic_1790206807.jsonl"
        receipt = run_replay(trace)
        self.assertEqual(receipt["terminal"], "UNKNOWN_NOT_CERTIFIED")
        self.assertEqual(receipt["decisions"][-1]["status"], "RefusedWrongWitnessRoute")


if __name__ == "__main__":
    unittest.main()
