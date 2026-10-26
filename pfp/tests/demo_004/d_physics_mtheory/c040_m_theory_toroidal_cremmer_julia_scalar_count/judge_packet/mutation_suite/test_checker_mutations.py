"""Automated Kill-Rate Test Suite verifying 100% rejection of all 48 hostile mutations.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.judge_packet.checkers.coset_group_theory_checker import (
    verify_coset_group_theory_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.judge_packet.checkers.dual_evaluator import (
    evaluate_answer,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.judge_packet.checkers.field_reduction_checker import (
    verify_field_reduction_certificate,
)

MUTATIONS_DIR = Path(__file__).resolve().parent / "mutations"


class TestCheckerMutations(unittest.TestCase):
    """Verifies that Checker 1, Checker 2, and DualEvaluator kill 100% of mutations."""

    def setUp(self) -> None:
        self.mutation_files = sorted(
            MUTATIONS_DIR.glob("*.json"), key=lambda p: p.name.encode("utf-8")
        )

    def test_mutation_count(self) -> None:
        """Ensure exactly 48 hostile mutations are present in the suite."""
        self.assertEqual(
            len(self.mutation_files),
            48,
            f"Expected exactly 48 mutation files, found {len(self.mutation_files)}",
        )

    def test_all_mutations_killed_by_checker_1(self) -> None:
        """Checker 1 (field reduction) must kill 100% of applicable mutations."""
        escapes = []
        for p in self.mutation_files:
            data = json.loads(p.read_text(encoding="utf-8"))
            case = data["case"]
            result = data["result"]
            ok, msg = verify_field_reduction_certificate(case, result)
            if ok:
                escapes.append((p.name, msg))
        self.assertEqual(
            escapes,
            [],
            f"Checker 1 permitted {len(escapes)} escapes: {escapes}",
        )

    def test_all_mutations_killed_by_checker_2(self) -> None:
        """Checker 2 (coset group theory) must kill 100% of applicable mutations."""
        escapes = []
        for p in self.mutation_files:
            data = json.loads(p.read_text(encoding="utf-8"))
            case = data["case"]
            result = data["result"]
            ok, msg = verify_coset_group_theory_certificate(case, result)
            if ok:
                escapes.append((p.name, msg))
        self.assertEqual(
            escapes,
            [],
            f"Checker 2 permitted {len(escapes)} escapes: {escapes}",
        )

    def test_all_mutations_killed_by_dual_evaluator(self) -> None:
        """DualEvaluator must reject 100% of mutations (verdict != PASS)."""
        escapes = []
        for p in self.mutation_files:
            data = json.loads(p.read_text(encoding="utf-8"))
            case = data["case"]
            result = data["result"]
            eval_res = evaluate_answer(case, result)
            if eval_res.verdict == "PASS":
                escapes.append(p.name)
        self.assertEqual(
            escapes,
            [],
            f"DualEvaluator permitted {len(escapes)} escapes: {escapes}",
        )


if __name__ == "__main__":
    unittest.main()
