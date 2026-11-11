"""Tests for host-derived characteristic-polynomial coverage-first workflows."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "dag" / "benchmark", ROOT / "ops"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from eis.domain.allostery import AllosteryRefusal
from host_charpoly_workflows import (
    COVERAGE_FIRST_INSTRUCTION,
    EISVerificationBridge,
    HOST_CHARPOLY_PLANS,
    OperadCompositionPipeline,
    PCIVTaskSetEvaluator,
    SUPPORTED_SEED_SHA256,
    build_host_charpoly_artifact,
    build_host_matrix_artifact,
    build_semantic_composition_artifact,
    prepare_source_pins,
)
from reference_runner import HERE, PLANS, OfflineTape, run, sha


class TestHostCharpolyWorkflows(unittest.TestCase):
    def test_host_charpoly_plans_registered(self):
        expected_plans = {
            "coverage_first_direct_v1",
            "coverage_first_matrix_v1",
            "coverage_first_charpoly_v1",
            "coverage_first_operad_composition_v1",
        }
        self.assertTrue(expected_plans.issubset(set(HOST_CHARPOLY_PLANS.keys())))
        self.assertTrue(expected_plans.issubset(set(PLANS.keys())))

    def test_identical_coverage_instruction(self):
        for plan_id in [
            "coverage_first_direct_v1",
            "coverage_first_matrix_v1",
            "coverage_first_charpoly_v1",
            "coverage_first_operad_composition_v1",
        ]:
            spec = HOST_CHARPOLY_PLANS[plan_id]
            self.assertEqual(len(spec["stages"]), 1)
            self.assertEqual(spec["stages"][0]["instruction"], COVERAGE_FIRST_INSTRUCTION)
            self.assertEqual(spec["stages"][0]["max_output_tokens"], 16000)

    def test_source_pins_integrity(self):
        pins = prepare_source_pins()
        self.assertGreaterEqual(len(pins), 5)
        for filename, expected_hash in pins.items():
            filepath = HERE / filename
            self.assertTrue(filepath.is_file())
            self.assertEqual(sha(filepath.read_bytes()), expected_hash)

    def test_host_matrix_artifact_derivation(self):
        artifact = build_host_matrix_artifact(SUPPORTED_SEED_SHA256)
        self.assertEqual(artifact["schema_version"], "1.0")
        self.assertEqual(artifact["seed_sha256"], SUPPORTED_SEED_SHA256)
        matrices = artifact["coefficient_matrices"]
        self.assertEqual(set(matrices.keys()), {"J", "Delta", "K"})
        for mat in matrices.values():
            self.assertEqual(len(mat), 4)
            for row in mat:
                self.assertEqual(len(row), 4)

    def test_host_charpoly_artifact_derivation(self):
        # Compact certificate derivation (default)
        compact = build_host_charpoly_artifact(SUPPORTED_SEED_SHA256, compact=True)
        self.assertEqual(compact["schema"], "pfp.qm-host-charpoly.compact-certificate.v1")
        self.assertEqual(compact["status"], "CERTIFIED_INTERMEDIATE_CHARPOLY")
        self.assertEqual(compact["seed_sha256"], SUPPORTED_SEED_SHA256)
        self.assertFalse(compact["limitations"]["final_answer_certified"])
        self.assertEqual(compact["native_verification"]["grid_points_verified"], 125)
        self.assertIn("standard_form", compact["polynomial"])
        self.assertNotIn("failure_states", compact)

        compact_str = json.dumps(compact, sort_keys=True, separators=(",", ":"))
        self.assertLessEqual(len(compact_str), 1200)

        # Full certified context derivation (compact=False)
        full = build_host_charpoly_artifact(SUPPORTED_SEED_SHA256, compact=False)
        self.assertEqual(full["schema"], "pfp.qm-host-charpoly.certified-context.v1")
        self.assertEqual(full["status"], "CERTIFIED_INTERMEDIATE_CHARPOLY")
        self.assertEqual(full["seed_sha256"], SUPPORTED_SEED_SHA256)
        self.assertFalse(full["limitations"]["final_answer_certified"])
        self.assertEqual(full["native_verification"]["grid_points_verified"], 125)
        self.assertEqual(len(full["solver_context"]["coefficients"]), 5)
        self.assertNotIn("failure_states", full)

    def test_offline_run_coverage_first_direct(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "run_direct"
            run_id = "test:coverage_first_direct_v1:000"
            receipt = run(
                "coverage_first_direct_v1",
                OfflineTape(["Synthetic coverage-first direct response"]),
                out_dir,
                run_id,
                max_output_tokens=16000,
            )
            self.assertEqual(receipt["status"], "offline_fixture_completed")
            self.assertEqual(receipt["seed_sha256"], SUPPORTED_SEED_SHA256)
            self.assertEqual(receipt["answer_text"], "Synthetic coverage-first direct response")
            self.assertEqual(len(receipt["calls"]), 1)

            # Check request messages: only system and seed
            req_messages = receipt["calls"][0]["request"]["messages"]
            self.assertEqual(len(req_messages), 2)
            self.assertEqual(req_messages[0]["role"], "system")
            self.assertEqual(req_messages[0]["content"], COVERAGE_FIRST_INSTRUCTION)
            self.assertEqual(req_messages[1]["role"], "user")
            self.assertEqual(sha(req_messages[1]["content"].encode("utf-8")), SUPPORTED_SEED_SHA256)

            # Host checks
            host_checks = json.loads((out_dir / "host_checks.json").read_text(encoding="utf-8"))
            self.assertFalse(host_checks["final_answer_certified"])
            self.assertEqual(host_checks["claims"], [])

    def test_offline_run_coverage_first_matrix(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "run_matrix"
            run_id = "test:coverage_first_matrix_v1:000"
            receipt = run(
                "coverage_first_matrix_v1",
                OfflineTape(["Synthetic coverage-first matrix response"]),
                out_dir,
                run_id,
                max_output_tokens=16000,
            )
            self.assertEqual(receipt["status"], "offline_fixture_completed")
            self.assertTrue((out_dir / "host_matrix.json").is_file())
            self.assertFalse((out_dir / "host_charpoly.json").is_file())

            # Request messages: system, seed, matrix context
            req_messages = receipt["calls"][0]["request"]["messages"]
            self.assertEqual(len(req_messages), 3)
            self.assertEqual(req_messages[0]["content"], COVERAGE_FIRST_INSTRUCTION)
            self.assertEqual(sha(req_messages[1]["content"].encode("utf-8")), SUPPORTED_SEED_SHA256)
            self.assertIn("coefficient_matrices", req_messages[2]["content"])

            host_checks = json.loads((out_dir / "host_checks.json").read_text(encoding="utf-8"))
            self.assertTrue(host_checks["host_derived_matrix"])
            self.assertEqual(host_checks["claims"], [{"status": "EXACT_AFFINE_HAMILTONIAN_MATCH"}])
            self.assertFalse(host_checks["final_answer_certified"])

    def test_offline_run_coverage_first_charpoly(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "run_charpoly"
            run_id = "test:coverage_first_charpoly_v1:000"
            receipt = run(
                "coverage_first_charpoly_v1",
                OfflineTape(["Synthetic coverage-first charpoly response"]),
                out_dir,
                run_id,
                max_output_tokens=16000,
            )
            self.assertEqual(receipt["status"], "offline_fixture_completed")
            self.assertTrue((out_dir / "host_matrix.json").is_file())
            self.assertTrue((out_dir / "host_charpoly.json").is_file())

            # Request messages: system, seed, matrix context, charpoly context
            req_messages = receipt["calls"][0]["request"]["messages"]
            self.assertEqual(len(req_messages), 4)
            self.assertEqual(req_messages[0]["content"], COVERAGE_FIRST_INSTRUCTION)
            self.assertEqual(sha(req_messages[1]["content"].encode("utf-8")), SUPPORTED_SEED_SHA256)
            self.assertIn("coefficient_matrices", req_messages[2]["content"])
            self.assertIn("CERTIFIED_INTERMEDIATE_CHARPOLY", req_messages[3]["content"])
            self.assertIn("pfp.qm-host-charpoly.compact-certificate.v1", req_messages[3]["content"])
            self.assertNotIn("failure_states", req_messages[3]["content"])
            charpoly_msg = req_messages[3]["content"]
            json_text = charpoly_msg.split("\n", 1)[1] if "\n" in charpoly_msg else charpoly_msg
            self.assertLessEqual(len(json_text), 1200)

            host_checks = json.loads((out_dir / "host_checks.json").read_text(encoding="utf-8"))
            self.assertTrue(host_checks["host_derived_matrix"])
            self.assertTrue(host_checks["host_derived_charpoly"])
            self.assertEqual(
                host_checks["claims"],
                [
                    {"status": "EXACT_AFFINE_HAMILTONIAN_MATCH"},
                    {"status": "EXACT_INTERMEDIATE_CHARPOLY_IDENTITY"},
                ],
            )
            self.assertFalse(host_checks["final_answer_certified"])
            self.assertEqual(host_checks["grid_points_verified"], 125)

    def test_offline_run_coverage_first_operad_composition(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "run_operad"
            run_id = "test:coverage_first_operad_composition_v1:000"
            receipt = run(
                "coverage_first_operad_composition_v1",
                OfflineTape(["Synthetic coverage-first operad composition response"]),
                out_dir,
                run_id,
                max_output_tokens=16000,
            )
            self.assertEqual(receipt["status"], "offline_fixture_completed")
            self.assertTrue((out_dir / "host_matrix.json").is_file())
            self.assertTrue((out_dir / "host_charpoly.json").is_file())
            self.assertTrue((out_dir / "semantic_composition_receipt.json").is_file())

            # 5 messages in solver request: system, seed, matrix context, charpoly context, semantic receipt
            req_messages = receipt["calls"][0]["request"]["messages"]
            self.assertEqual(len(req_messages), 5)
            self.assertEqual(req_messages[0]["content"], COVERAGE_FIRST_INSTRUCTION)
            self.assertEqual(sha(req_messages[1]["content"].encode("utf-8")), SUPPORTED_SEED_SHA256)
            self.assertIn("coefficient_matrices", req_messages[2]["content"])
            self.assertIn("CERTIFIED_INTERMEDIATE_CHARPOLY", req_messages[3]["content"])
            self.assertIn("pfp.semantic-composition.v1", req_messages[4]["content"])

            host_checks = json.loads((out_dir / "host_checks.json").read_text(encoding="utf-8"))
            self.assertTrue(host_checks["host_derived_matrix"])
            self.assertTrue(host_checks["host_derived_charpoly"])
            self.assertTrue(host_checks["semantic_composition"])
            self.assertTrue(host_checks["operadic_associativity_verified"])
            self.assertFalse(host_checks["final_answer_certified"])
            self.assertEqual(
                host_checks["claims"],
                [
                    {"status": "EXACT_AFFINE_HAMILTONIAN_MATCH"},
                    {"status": "EXACT_INTERMEDIATE_CHARPOLY_IDENTITY"},
                    {"status": "TYPED_OPERADIC_COMPOSITION_VERIFIED"},
                ],
            )

    def test_eis_verification_bridge_activated(self):
        mat = build_host_matrix_artifact(SUPPORTED_SEED_SHA256)
        cp = build_host_charpoly_artifact(SUPPORTED_SEED_SHA256, compact=True)
        decision = EISVerificationBridge.evaluate_charpoly_evidence(cp, mat)
        self.assertTrue(decision["is_activated"])
        self.assertEqual(decision["positive_sensors"], 3)
        self.assertEqual(decision["quorum_size"], 2)
        self.assertEqual(decision["aggregate_signal_str"], "3")
        self.assertEqual(decision["hill_value_str"], "9/13")

    def test_eis_verification_bridge_refusal_single_sensor(self):
        mat = build_host_matrix_artifact(SUPPORTED_SEED_SHA256)
        cp = build_host_charpoly_artifact(SUPPORTED_SEED_SHA256, compact=True)
        # Custom signals with only 1 positive sensor
        single_signal = {
            "sensor_grid_identity": Fraction(1, 1),
            "sensor_degree_bounds": Fraction(0, 1),
            "sensor_trace_zero": Fraction(0, 1),
        }
        decision = EISVerificationBridge.evaluate_charpoly_evidence(cp, mat, custom_signals=single_signal)
        self.assertFalse(decision["is_activated"])
        self.assertEqual(decision["positive_sensors"], 1)
        self.assertEqual(decision["quorum_size"], 2)
        self.assertIn("NOT ACTIVATED", decision["rationale"])

    def test_eis_verification_bridge_refusal_duplicate_sensor(self):
        mat = build_host_matrix_artifact(SUPPORTED_SEED_SHA256)
        cp = build_host_charpoly_artifact(SUPPORTED_SEED_SHA256, compact=True)
        dup_signals = {
            "sensor_grid_identity": Fraction(1, 1),
            "SENSOR_GRID_IDENTITY": Fraction(1, 1),
        }
        with self.assertRaises(AllosteryRefusal) as ctx:
            EISVerificationBridge.evaluate_charpoly_evidence(cp, mat, custom_signals=dup_signals)
        self.assertEqual(ctx.exception.code, "DUPLICATE_SENSOR")

    def test_pciv_task_set_evaluator_portfolio(self):
        candidates = [
            {"id": "c1", "metrics": {"correctness": Fraction(83, 100), "cost": Fraction(4211, 1000000)}},
            {"id": "c2", "metrics": {"correctness": Fraction(88, 100), "cost": Fraction(5500, 1000000)}},
            {"id": "c3", "metrics": {"correctness": Fraction(90, 100), "cost": Fraction(5800, 1000000)}},
        ]
        results = PCIVTaskSetEvaluator.evaluate_portfolio(candidates)
        self.assertEqual(results["task_count"], 5)
        self.assertEqual(results["candidate_count"], 3)
        self.assertEqual(len(results["non_dominated_front"]), 3)
        self.assertEqual(results["total_fronts"], 1)
        self.assertEqual(results["lexicographic_leader_id"], "c3")

    def test_pciv_task_set_evaluator_missing_measurements(self):
        with self.assertRaises(ValueError) as ctx:
            PCIVTaskSetEvaluator.evaluate_portfolio([])
        self.assertIn("MISSING_MEASUREMENTS", str(ctx.exception))

    def test_pciv_task_set_evaluator_empty_task_set(self):
        candidates = [{"id": "c1", "metrics": {"correctness": Fraction(1, 1), "cost": Fraction(1, 1)}}]
        with self.assertRaises(ValueError) as ctx:
            PCIVTaskSetEvaluator.evaluate_portfolio(candidates, task_portfolio=())
        self.assertIn("EMPTY_TASK_SET", str(ctx.exception))

    def test_operad_composition_pipeline_witness(self):
        witness = OperadCompositionPipeline.build_composition_witness()
        self.assertTrue(witness["is_associative"])
        self.assertEqual(witness["left_composite"], "(State) -> Receipt")
        self.assertEqual(witness["right_composite"], "(State) -> Receipt")
        self.assertEqual(witness["root_colour"], "Receipt")
        self.assertEqual(witness["leaf_colour"], "State")
        self.assertEqual(witness["tree_arity"], 1)

    def test_operad_composition_pipeline_mismatched_port(self):
        with self.assertRaises(ValueError) as ctx:
            OperadCompositionPipeline.build_composition_witness(op_root_source="Paper")
        self.assertIn("Operad associativity verification failed", str(ctx.exception))

    def test_build_semantic_composition_artifact(self):
        art = build_semantic_composition_artifact(SUPPORTED_SEED_SHA256)
        self.assertEqual(art["schema"], "pfp.semantic-composition.v1")
        self.assertEqual(art["status"], "VERIFIED_OFFLINE_COMPOSITION")
        self.assertEqual(art["seed_sha256"], SUPPORTED_SEED_SHA256)
        self.assertFalse(art["limitations"]["final_answer_certified"])
        self.assertTrue(art["eis_allosteric_consensus"]["is_activated"])
        self.assertTrue(art["operad_composition_witness"]["is_associative"])
        self.assertEqual(art["pciv_portfolio_selection"]["task_count"], 5)

    def test_unsupported_seed_refused(self):
        with self.assertRaises(ValueError):
            build_host_matrix_artifact("0" * 64)
        with self.assertRaises(ValueError):
            build_host_charpoly_artifact("0" * 64)
        with self.assertRaises(ValueError):
            build_semantic_composition_artifact("0" * 64)


if __name__ == "__main__":
    unittest.main()
