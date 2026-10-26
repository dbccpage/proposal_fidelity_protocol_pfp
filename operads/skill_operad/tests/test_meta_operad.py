"""test_meta_operad.py
===================

Unit tests for Higher-Order Operadic Management Calculus (HOMC-v1) and Operadic Ecology.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
import unittest

from omega_engine_operads.skill_operad.meta_operad import (
    MorphismViolationError,
    ObstructionClass,
    OperadEcology,
    OperadManagementError,
    OperadMorphism,
    OperadSpec,
    Receipt,
)


class MetaOperadHOMC1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.yaml_path = (
            Path(__file__).resolve().parents[3]
            / "omega_engine_atlas"
            / "coda_atlas"
            / "prompts"
            / "pilots"
            / "pilot_001"
            / "homc_v1_ecology.yaml"
        )
        self.ecology = OperadEcology.load_from_yaml(self.yaml_path)

    def test_ecology_loads_three_pilot_operads(self) -> None:
        """Verifies all 3 pilot operads are loaded and internally coherent."""
        self.assertEqual(len(self.ecology.operads), 3)
        self.assertIn("omega.operad.rational_linear.v1", self.ecology.operads)
        self.assertIn("omega.operad.wdp_homotopy.v1", self.ecology.operads)
        self.assertIn("omega.operad.mub6_stengle.v1", self.ecology.operads)

        for op in self.ecology.operads.values():
            # Must not raise OperadManagementError
            op.validate_internal_coherence()

    def test_morphism_verification_rl_to_wdp_and_mub6(self) -> None:
        """Verifies strict colour and generator preservation for embeddings."""
        self.assertIn("phi_rl_to_wdp", self.ecology.morphisms)
        self.assertIn("phi_rl_to_mub6", self.ecology.morphisms)

        m_wdp = self.ecology.morphisms["phi_rl_to_wdp"]
        rc_wdp = m_wdp.verify(
            self.ecology.operads["omega.operad.rational_linear.v1"],
            self.ecology.operads["omega.operad.wdp_homotopy.v1"],
        )
        self.assertTrue(rc_wdp.is_pass)
        self.assertEqual(len(rc_wdp.obstructions), 0)

        m_mub6 = self.ecology.morphisms["phi_rl_to_mub6"]
        rc_mub6 = m_mub6.verify(
            self.ecology.operads["omega.operad.rational_linear.v1"],
            self.ecology.operads["omega.operad.mub6_stengle.v1"],
        )
        self.assertTrue(rc_mub6.is_pass)
        self.assertEqual(len(rc_mub6.obstructions), 0)

    def test_embedding_lattice(self) -> None:
        """Verifies O_RL embeds into O_WDP and O_MUB6."""
        self.assertTrue(
            self.ecology.check_embedding(
                "omega.operad.rational_linear.v1",
                "omega.operad.wdp_homotopy.v1",
            )
        )
        self.assertTrue(
            self.ecology.check_embedding(
                "omega.operad.rational_linear.v1",
                "omega.operad.mub6_stengle.v1",
            )
        )
        # Non-embedded pair should return False
        self.assertFalse(
            self.ecology.check_embedding(
                "omega.operad.wdp_homotopy.v1",
                "omega.operad.mub6_stengle.v1",
            )
        )

    def test_receipt_monad_fail_closed_composition(self) -> None:
        """Verifies Kleisli composition of receipts fails closed upon any obstruction."""
        r_pass_1 = Receipt(receipt_id="r1", status="PASS", evidence_scope="scope1")
        r_pass_2 = Receipt(receipt_id="r2", status="PASS", evidence_scope="scope2")
        r_comp_pass = r_pass_1.compose(r_pass_2)
        self.assertTrue(r_comp_pass.is_pass)
        self.assertEqual(r_comp_pass.status, "PASS")

        # Obstruction injection (H^1 decoy)
        obs_decoy = ObstructionClass(
            degree=1,
            antibody_id="AB_TEST_DECOY",
            description="Detected ungrounded claim",
        )
        r_fail = Receipt(
            receipt_id="r3",
            status="FAIL",
            evidence_scope="scope3",
            obstructions=[obs_decoy],
        )

        r_comp_fail = r_pass_1.compose(r_fail)
        self.assertFalse(r_comp_fail.is_pass)
        self.assertEqual(r_comp_fail.status, "FAIL")
        self.assertEqual(len(r_comp_fail.obstructions), 1)
        self.assertEqual(r_comp_fail.obstructions[0].degree, 1)

    def test_witness_translation_across_morphism(self) -> None:
        """Verifies witness colour translation from O_RL to O_WDP."""
        witness = {
            "claim": "x=1, y=2",
            "types": {"input": "Eq2", "output": "IsoY"},
        }
        translated = self.ecology.translate_witness(witness, "phi_rl_to_wdp")
        self.assertEqual(translated["status"], "TRANSLATED")
        self.assertEqual(translated["translated_types"]["input"], "ZChain")
        self.assertEqual(translated["translated_types"]["output"], "Hom_k")

    def test_obstruction_cohomology_degrees(self) -> None:
        """Verifies obstruction classes are properly typed into H^0, H^1, H^2."""
        rl_op = self.ecology.operads["omega.operad.rational_linear.v1"]
        h0_classes = [c for c in rl_op.obstruction_classes if c.degree == 0]
        h1_classes = [c for c in rl_op.obstruction_classes if c.degree == 1]
        self.assertTrue(len(h0_classes) >= 1)
        self.assertEqual(h0_classes[0].antibody_id, "IDEAL_EXACT_RATIONAL_DOMAIN")
        self.assertTrue(len(h1_classes) >= 1)
        self.assertEqual(h1_classes[0].antibody_id, "AB_FALSE_CERTAINTY_DECOY")

        wdp_op = self.ecology.operads["omega.operad.wdp_homotopy.v1"]
        h2_classes = [c for c in wdp_op.obstruction_classes if c.degree == 2]
        self.assertTrue(len(h2_classes) >= 1)
        self.assertEqual(h2_classes[0].antibody_id, "AB_SPARSE_LIFT_OBSTRUCTION")

    def test_morphism_violation_detection(self) -> None:
        """Verifies an ill-typed morphism raises or yields an obstruction receipt."""
        bad_morph = OperadMorphism(
            id="phi_bad",
            source_id="omega.operad.rational_linear.v1",
            target_id="omega.operad.wdp_homotopy.v1",
            colour_map={"Eq1": "NONEXISTENT_COLOUR"},
            generator_map={"isolate_y": "isolate_y"},
        )
        receipt = bad_morph.verify(
            self.ecology.operads["omega.operad.rational_linear.v1"],
            self.ecology.operads["omega.operad.wdp_homotopy.v1"],
        )
        self.assertFalse(receipt.is_pass)
        self.assertTrue(any("NONEXISTENT_COLOUR" in ob.description for ob in receipt.obstructions))


if __name__ == "__main__":
    unittest.main()
