"""Educational Verification Suite: How to Play The Symbol Game.

Provides an executable Python test suite and interactive demonstration of the
discrete host governor rules, carrier firewall, monotonicity enforcement,
and receipt generation.
"""

import sys
import unittest
from fractions import Fraction
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

try:
    from .educational_governor import EducationalHostGovernor
except ImportError:
    from educational_governor import EducationalHostGovernor


class TestSymbolGameHowToPlay(unittest.TestCase):
    """Automated test verification of the Symbol Game gameplay rules."""

    def setUp(self):
        # 3-cycle triangle with circulation: 2 + 1 + 3 = 6 != 0
        self.vertices = [0, 1, 2]
        self.edges = ["0->1", "1->2", "2->0"]
        self.initial_claims = {"0->1": 2, "1->2": 1, "2->0": 3}
        self.host = EducationalHostGovernor(self.vertices, self.edges, self.initial_claims, fuel=5)

    def test_scenario_1_assert_adds_invariant_without_changing_defect(self):
        """ASSERT move adds to invariant register and leaves defect unchanged."""
        res = self.host.execute_move(
            {"move_type": "ASSERT", "payload": {"relation": "TREE_SPAN_0_1_2"}}
        )
        self.assertEqual(res["decision"], "ADMITTED")
        self.assertEqual(res["defect_phi1"], "6")
        self.assertIn("TREE_SPAN_0_1_2", self.host.invariants)
        self.assertEqual(self.host.fuel, 4)

    def test_scenario_2_strictly_descending_cut_is_admitted(self):
        """CUT move that reduces circulation from 6 to 2 is admitted."""
        res = self.host.execute_move(
            {"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -1}}}
        )
        # 2 + 1 + (-1) = 2 (old was 6)
        self.assertEqual(res["decision"], "ADMITTED")
        self.assertEqual(res["defect_phi1"], "2")
        self.assertEqual(self.host.fuel, 4)

    def test_scenario_3_non_monotonic_cut_is_refused_with_rollback(self):
        """CUT move that increases circulation from 6 to 10 is refused and rolled back."""
        res = self.host.execute_move(
            {"move_type": "CUT", "payload": {"proposed_claims": {"2->0": 7}}}
        )
        # 2 + 1 + 7 = 10 >= 6
        self.assertEqual(res["decision"], "REFUSED_MONOTONICITY_VIOLATION")
        self.assertIn("does not strictly decrease", res["message"])
        # Original claim preserved
        self.assertEqual(self.host.claims["2->0"], Fraction(3))
        # But fuel is decremented
        self.assertEqual(self.host.fuel, 4)

    def test_scenario_4_carrier_smuggling_is_refused(self):
        """Attempting to introduce an edge outside the pinned carrier is refused."""
        res = self.host.execute_move(
            {"move_type": "CUT", "payload": {"proposed_claims": {"3->4": 0}}}
        )
        self.assertEqual(res["decision"], "REFUSED_CARRIER_DOMAIN")
        self.assertIn("not in pinned carrier", res["message"])

    def test_scenario_5_verify_refused_when_defect_positive(self):
        """Calling VERIFY before defect is zero is refused."""
        res = self.host.execute_move({"move_type": "VERIFY", "payload": {}})
        self.assertEqual(res["decision"], "REFUSED_NONZERO_DEFECT")
        self.assertEqual(res["defect_phi1"], "6")
        self.assertFalse(self.host.is_terminal)

    def test_scenario_6_verify_accepted_at_zero_defect(self):
        """Reaching zero defect via exact chord cut enables terminal certification."""
        # 1. Propose exact chord cut: 2 + 1 + (-3) = 0
        cut_res = self.host.execute_move(
            {"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -3}}}
        )
        self.assertEqual(cut_res["decision"], "ADMITTED")
        self.assertEqual(cut_res["defect_phi1"], "0")

        # 2. Call VERIFY
        verify_res = self.host.execute_move({"move_type": "VERIFY", "payload": {}})
        self.assertEqual(verify_res["decision"], "ACCEPTED_ZERO_DEFECT")
        self.assertTrue(self.host.is_terminal)
        self.assertEqual(verify_res["receipt"]["status"], "CERTIFIED")
        self.assertEqual(verify_res["receipt"]["turns_used"], 2)

    def test_scenario_7_post_terminal_mutation_is_rejected(self):
        """Mutating the board after terminal certification is strictly rejected."""
        self.host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -3}}})
        self.host.execute_move({"move_type": "VERIFY", "payload": {}})
        self.assertTrue(self.host.is_terminal)

        # Attempt further move
        post_res = self.host.execute_move(
            {"move_type": "CUT", "payload": {"proposed_claims": {"2->0": 0}}}
        )
        self.assertEqual(post_res["decision"], "REFUSED_TERMINAL_STATE")


if __name__ == "__main__":
    unittest.main()
