# AuthorityEffect: None.
"""
Unit tests for participant packet and mutation kill rate.
"""

import json
import unittest
from pathlib import Path

from c042_sat_with_drat_certificates.judge_packet.checkers.dual_evaluator import evaluate_dual
from c042_sat_with_drat_certificates.reference_solver.solver import solve

PKG_ROOT = Path(__file__).resolve().parent.parent


class TestParticipantPacket(unittest.TestCase):
    def test_public_examples_pass(self):
        ex_dir = PKG_ROOT / "participant_packet" / "examples"
        cases = sorted(ex_dir.glob("*.json"))
        self.assertEqual(len(cases), 10)

        for cpath in cases:
            with open(cpath, "r", encoding="utf-8") as f:
                case = json.load(f)
            ans = solve(case)
            ok, msg, _ = evaluate_dual(case, ans)
            self.assertTrue(ok, f"Public case {case['case_id']} failed: {msg}")

    def test_mutation_kill_rate_100_percent(self):
        mut_dir = PKG_ROOT / "judge_packet" / "mutation_suite"
        mut_files = sorted(mut_dir.glob("*.json"))
        self.assertEqual(len(mut_files), 48)

        killed = 0
        for mf in mut_files:
            with open(mf, "r", encoding="utf-8") as f:
                item = json.load(f)
            case = item["case"]
            corrupted = item["corrupted_answer"]
            ok, msg, _ = evaluate_dual(case, corrupted)
            if not ok:
                killed += 1

        self.assertEqual(killed, 48, f"Mutation kill rate {killed}/48 is not 100%")


if __name__ == "__main__":
    unittest.main()
