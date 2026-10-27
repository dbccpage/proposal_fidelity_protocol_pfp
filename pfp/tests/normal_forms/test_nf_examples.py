"""Unit tests for the lesson schemas and normal-form examples.

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from pfp.domain.normal_forms.examples import (
    order_line_fails_second_normal_form,
    street_journal_title_passes_third_and_fails_boyce_codd,
    street_journal_title_split,
)
from pfp.infrastructure.normal_form_loading import validate_contract_file


class TestNfExamples(unittest.TestCase):
    def test_order_line_is_outside_second_normal_form(self) -> None:
        self.assertTrue(order_line_fails_second_normal_form())

    def test_street_journal_title_is_third_and_not_boyce_codd(self) -> None:
        self.assertTrue(street_journal_title_passes_third_and_fails_boyce_codd())

    def test_heath_split_is_lossless_and_drops_sj_to_t(self) -> None:
        lossless, preserved = street_journal_title_split()
        self.assertTrue(lossless)
        self.assertFalse(preserved)

    def test_compilation_proposal_passes_the_harness(self) -> None:
        path = Path(__file__).resolve().parents[2] / "infrastructure/yaml/normal_forms" / "nf.compilation.cpnf.yaml"
        defects = validate_contract_file(path)
        self.assertEqual(defects, [])

    def test_bqnf_cdc_examples_pass(self) -> None:
        from pfp.tests.normal_forms.test_bqnf_cdc_property import (
            TestBqnfCdcProperties,
        )

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestBqnfCdcProperties)
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 6)

    def test_certificate_and_observer_freshness_properties_pass(self) -> None:
        from pfp.tests.normal_forms.test_observer_freshness_certificate_property import (
            TestCertificateVerifierProperties,
            TestObserverRelativeFreshnessProperties,
        )

        loader = unittest.defaultTestLoader
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(TestCertificateVerifierProperties))
        suite.addTests(loader.loadTestsFromTestCase(TestObserverRelativeFreshnessProperties))
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 8)

    def test_cochain_physics_epistemic_properties_pass(self) -> None:
        from pfp.tests.normal_forms.test_cochain_physics_epistemic_property import (
            TestBssnfGaugeSignProperties,
            TestDiscreteHodgeProperties,
            TestEqnfEpistemicQuotientProperties,
            TestMicnfInvolutiveCancellationProperties,
            TestZfnfExactRationalProperties,
        )

        loader = unittest.defaultTestLoader
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(TestDiscreteHodgeProperties))
        suite.addTests(loader.loadTestsFromTestCase(TestBssnfGaugeSignProperties))
        suite.addTests(loader.loadTestsFromTestCase(TestMicnfInvolutiveCancellationProperties))
        suite.addTests(loader.loadTestsFromTestCase(TestZfnfExactRationalProperties))
        suite.addTests(loader.loadTestsFromTestCase(TestEqnfEpistemicQuotientProperties))
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 8)

    def test_cross_domain_reconciliation_properties_pass(self) -> None:
        from pfp.tests.normal_forms.test_cross_domain_reconciliation_property import (
            TestCrossDomainReconciliationProperties,
        )

        loader = unittest.defaultTestLoader
        suite = loader.loadTestsFromTestCase(TestCrossDomainReconciliationProperties)
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 6)

    def test_chase_evaluator_passes(self) -> None:
        from pfp.tests.normal_forms.test_chase_evaluator import (
            TestChaseEvaluator,
            TestChaseMonotonicityProperties,
        )

        loader = unittest.defaultTestLoader
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(TestChaseEvaluator))
        suite.addTests(loader.loadTestsFromTestCase(TestChaseMonotonicityProperties))
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 11)

    def test_quantile_sketch_properties_pass(self) -> None:
        from pfp.tests.normal_forms.test_quantile_sketch_property import (
            TestQuantileSketchCochainProperties,
        )

        loader = unittest.defaultTestLoader
        suite = loader.loadTestsFromTestCase(TestQuantileSketchCochainProperties)
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 5)

    def test_relational_confluence_and_4nf_mvd_suites_pass(self) -> None:
        from pfp.tests.normal_forms.test_relational_confluence_and_4nf_mvd import (
            TestArmstrongAxiomClosureProperties,
            TestCandidateKeyAntichainMinimality,
            TestChaseConfluenceAndOrderInvariance,
            TestMultivaluedDependencyAnd4NF,
        )

        loader = unittest.defaultTestLoader
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(TestChaseConfluenceAndOrderInvariance))
        suite.addTests(loader.loadTestsFromTestCase(TestMultivaluedDependencyAnd4NF))
        suite.addTests(loader.loadTestsFromTestCase(TestArmstrongAxiomClosureProperties))
        suite.addTests(loader.loadTestsFromTestCase(TestCandidateKeyAntichainMinimality))
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 8)

    def test_cross_domain_invariants_and_loss_ledger_suites_pass(self) -> None:
        from pfp.tests.normal_forms.test_cross_domain_invariants_and_loss_ledger import (
            TestCrossDomainDefectCocycle,
            TestSealedLossLedgerTamperFalsification,
            TestTargetVerifierPrecedenceAndAuthorityLaundering,
        )

        loader = unittest.defaultTestLoader
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(TestCrossDomainDefectCocycle))
        suite.addTests(loader.loadTestsFromTestCase(TestSealedLossLedgerTamperFalsification))
        suite.addTests(
            loader.loadTestsFromTestCase(TestTargetVerifierPrecedenceAndAuthorityLaundering)
        )
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 11)

    def test_physics_and_observer_lattice_suites_pass(self) -> None:
        from pfp.tests.normal_forms.test_physics_and_observer_lattice_properties import (
            TestObserverLatticeMonotonicityProperties,
            TestSimplicialDiscreteHodgeDecomposition,
            TestZeroFloatDualityScalingInvariance,
        )

        loader = unittest.defaultTestLoader
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(TestZeroFloatDualityScalingInvariance))
        suite.addTests(loader.loadTestsFromTestCase(TestSimplicialDiscreteHodgeDecomposition))
        suite.addTests(loader.loadTestsFromTestCase(TestObserverLatticeMonotonicityProperties))
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 7)

    def test_pjnf_5nf_join_dependency_chase_suites_pass(self) -> None:
        from pfp.tests.normal_forms.test_pjnf_5nf_join_dependency_chase import (
            TestCandidateKeyEntailmentAndSufficientConditions,
            TestFagin5NFClassicalSchemas,
            TestLosslessJoinSynthesisAndValidation,
            TestNonBinaryChaseConfluence,
            TestRelationalHierarchyChain,
        )

        loader = unittest.defaultTestLoader
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(TestFagin5NFClassicalSchemas))
        suite.addTests(loader.loadTestsFromTestCase(TestNonBinaryChaseConfluence))
        suite.addTests(
            loader.loadTestsFromTestCase(TestCandidateKeyEntailmentAndSufficientConditions)
        )
        suite.addTests(loader.loadTestsFromTestCase(TestRelationalHierarchyChain))
        suite.addTests(loader.loadTestsFromTestCase(TestLosslessJoinSynthesisAndValidation))
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 25)

    def test_classical_nf_boundary_and_pjnf_synthesis_suites_pass(self) -> None:
        from pfp.tests.normal_forms.test_classical_nf_boundary_and_pjnf_synthesis import (
            TestClassicalNFBoundaryAndPJNFSynthesis,
        )

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(
            TestClassicalNFBoundaryAndPJNFSynthesis
        )
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 18)

    def test_chase_algebra_and_bqnf_streaming_suites_pass(self) -> None:
        from pfp.tests.normal_forms.test_chase_algebra_and_bqnf_streaming import (
            TestChaseAlgebraAndBqnfStreaming,
        )

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestChaseAlgebraAndBqnfStreaming)
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 13)

    def test_cross_domain_transport_and_freshness_suites_pass(self) -> None:
        from pfp.tests.normal_forms.test_cross_domain_transport_and_freshness import (
            TestCrossDomainTransportAndFreshness,
        )

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(
            TestCrossDomainTransportAndFreshness
        )
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 13)

    def test_physics_fermion_optimization_and_hodge_suites_pass(self) -> None:
        from pfp.tests.normal_forms.test_physics_fermion_optimization_and_hodge import (
            TestPhysicsFermionOptimizationAndHodge,
        )

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(
            TestPhysicsFermionOptimizationAndHodge
        )
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 12)

    def test_ddc_trace_replay_integration_passes(self) -> None:
        from pfp.tests.normal_forms.test_ddc_trace_replay_integration import (
            TestDdcTraceReplayIntegration,
        )

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestDdcTraceReplayIntegration)
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 5)

    def test_lean4_normal_forms_theorems_aligned(self) -> None:
        import json
        import shutil
        import subprocess

        repo_root = next((p for p in Path(__file__).resolve().parents if (p / '.git').exists()), Path(__file__).resolve().parents[4])
        lean_file = repo_root / "lean4" / "NormalFormsCore.lean"
        json_dir = (
            Path(__file__).parent / "json"
            if (Path(__file__).parent / "json").is_dir()
            else Path(__file__).parent
        )
        receipt_files = [
            json_dir / "receipt_observer_freshness_certificate_property.json",
            json_dir / "receipt_cochain_physics_epistemic_property.json",
            json_dir / "receipt_quantile_sketch_property.json",
            json_dir / "receipt_chase_monotonicity_property.json",
        ]
        self.assertTrue(lean_file.is_file(), f"Missing Lean 4 file: {lean_file}")
        for rf in receipt_files:
            self.assertTrue(rf.is_file(), f"Missing receipt: {rf}")

        lean_code = lean_file.read_text(encoding="utf-8")
        self.assertNotIn("sorry", lean_code, "NormalFormsCore.lean must not contain 'sorry'")

        total_theorems = 0
        for rf in receipt_files:
            with open(rf, "r", encoding="utf-8") as f:
                receipt = json.load(f)

            aligned_theorems = receipt.get("lean4_theorems_aligned", [])
            total_theorems += len(aligned_theorems)

            for thm in aligned_theorems:
                bare_thm = thm.split(".")[-1]
                self.assertIn(
                    f"theorem {bare_thm}",
                    lean_code,
                    f"Theorem {bare_thm} must be defined in NormalFormsCore.lean",
                )

        self.assertGreaterEqual(total_theorems, 16)

        # Build Lake target to assert elaboration and proof checking passes
        lake_bin = shutil.which("lake")
        if lake_bin:
            build_res = subprocess.run(
                [lake_bin, "build", "NormalFormsCore"],
                cwd=str(repo_root / "lean4"),
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(
                build_res.returncode,
                0,
                f"lake build NormalFormsCore failed:\n{build_res.stderr}\n{build_res.stdout}",
            )


if __name__ == "__main__":
    unittest.main()
