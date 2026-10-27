"""Tests verifying the mutation suite and dual checker kill rates for c038."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.judge_packet.checkers.combinatorial_primal_checker import (
    verify_combinatorial_primal_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.judge_packet.checkers.homology_dual_potential_checker import (
    verify_homology_dual_potential_certificate,
)

MUTATIONS_DIR = Path(__file__).resolve().parent / "mutations"


class TestCheckerMutations(unittest.TestCase):
    """Verifies that all seeded mutations are killed by both independent checkers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mutation_files = sorted(MUTATIONS_DIR.glob("mut_*.json"))

    def test_mutation_count(self) -> None:
        """Protocol requires >= 45 mutations. We provide 48."""
        self.assertGreaterEqual(
            len(self.mutation_files),
            45,
            f"Expected at least 45 mutations, found {len(self.mutation_files)}",
        )
        self.assertEqual(
            len(self.mutation_files),
            48,
            f"Expected exactly 48 seeded mutations, found {len(self.mutation_files)}",
        )

    def test_checker1_kills_all_mutations(self) -> None:
        """Checker 1 (combinatorial & primal) must achieve 100% kill rate."""
        killed = 0
        escaped = []
        for mf in self.mutation_files:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            case = data["case"]
            answer = data.get("result", data.get("answer"))
            passed, reason = verify_combinatorial_primal_certificate(case, answer)
            if not passed:
                killed += 1
            else:
                escaped.append((mf.name, reason))

        self.assertEqual(
            escaped,
            [],
            f"Checker 1 failed to kill {len(escaped)} mutations: {escaped}",
        )
        self.assertEqual(killed, len(self.mutation_files))

    def test_checker2_kills_all_mutations(self) -> None:
        """Checker 2 (homology & dual potential) must achieve 100% kill rate."""
        killed = 0
        escaped = []
        for mf in self.mutation_files:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            case = data["case"]
            answer = data.get("result", data.get("answer"))
            passed, reason = verify_homology_dual_potential_certificate(case, answer)
            if not passed:
                killed += 1
            else:
                escaped.append((mf.name, reason))

        self.assertEqual(
            escaped,
            [],
            f"Checker 2 failed to kill {len(escaped)} mutations: {escaped}",
        )
        self.assertEqual(killed, len(self.mutation_files))

    def test_dual_evaluator_rejects_all_mutations(self) -> None:
        """Dual evaluator must reject all mutations (both checkers agree to reject)."""
        for mf in self.mutation_files:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            case = data["case"]
            answer = data.get("result", data.get("answer"))
            eval_res = evaluate_dual(case, answer)
            self.assertFalse(
                eval_res["checker1_combinatorial_primal"]["ok"],
                f"Checker 1 unexpectedly passed {mf.name}",
            )
            self.assertFalse(
                eval_res["checker2_homology_dual_potential"]["ok"],
                f"Checker 2 unexpectedly passed {mf.name}",
            )
            self.assertTrue(eval_res["agreed"], f"Checkers disagreed on rejection for {mf.name}")
            self.assertEqual(eval_res["verdict"], "FAIL", f"Expected FAIL verdict for {mf.name}")

    def test_mutation_schema_structure(self) -> None:
        """Each mutation file must contain valid metadata, case, and result."""
        for mf in self.mutation_files:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("mutation_id", data)
            self.assertIn("description", data)
            self.assertIn("case", data)
            self.assertTrue("result" in data or "answer" in data)

    def test_isolated_mutations_killed_by_proper_defect_channel(self) -> None:
        """Verifies that mutations 15, 16, 19, 20, 22 are killed specifically by their
        respective defect channels, and not by collateral ollivier curvature mismatch."""
        target_checks = {
            "mut_15_transport_marginal_source_violation.json": "marginal",
            "mut_16_transport_marginal_target_violation.json": "marginal",
            "mut_19_potential_lipschitz_violation_slope2.json": "lipschitz",
            "mut_20_potential_lipschitz_violation_k4.json": "lipschitz",
            "mut_22_potential_duality_gap_nonzero.json": "duality gap",
        }

        for fname, keyword in target_checks.items():
            fpath = MUTATIONS_DIR / fname
            self.assertTrue(fpath.is_file(), f"Missing mutation file: {fname}")
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            case = data["case"]
            answer = data.get("result", data.get("answer"))

            ok1, msg1 = verify_combinatorial_primal_certificate(case, answer)
            ok2, msg2 = verify_homology_dual_potential_certificate(case, answer)
            eval_res = evaluate_dual(case, answer)

            self.assertFalse(ok1, f"Checker 1 passed isolated mutation {fname}")
            self.assertFalse(ok2, f"Checker 2 passed isolated mutation {fname}")
            self.assertIn(
                keyword,
                msg1.lower(),
                f"Checker 1 killed {fname} for wrong reason: {msg1} (expected '{keyword}')",
            )
            self.assertIn(
                keyword,
                msg2.lower(),
                f"Checker 2 killed {fname} for wrong reason: {msg2} (expected '{keyword}')",
            )
            self.assertTrue(eval_res["agreed"])
            self.assertEqual(eval_res["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
