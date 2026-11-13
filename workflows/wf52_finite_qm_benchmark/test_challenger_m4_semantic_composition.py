"""Independent Empirical Challenger & Adversarial Stress Harness for Milestone 4.

Authored by Independent Challenger to rigorously stress-test:
1. EIS Allosteric Consensus Gate:
   - Single-sensor attack: 1 positive sensor (S=1) fails threshold H(1) = 1/5 < 1/2.
   - Quorum enforcement: cap=1 requires at least 2 distinct positive sensors.
   - Sensor duplication attack: case-folding and whitespace aliasing raise DUPLICATE_SENSOR.
   - Value/typing attacks: values > cap, negative values, floats, booleans, bad IDs, non-keyed maps.
   - Fake trace / corrupted matrix / grid count attacks: deactivates individual sensors.
   - Exact rational Hill response mathematical invariants.

2. PCIV Task Portfolio Evaluator:
   - Empty measurements attack: empty metrics list raises MISSING_MEASUREMENTS.
   - Empty task portfolio attack: empty task set raises EMPTY_TASK_SET.
   - Forged fitness attack: self-declared status strings grant zero credit.
   - Non-dominated Pareto front partitioning: correctness vs cost tradeoffs, multi-front partitioning.
   - Lexicographic tiebreaking: strictly breaks ties by candidate ID, zero composite scalar weighting.

3. OPERADS Typed Port Composition & Associativity:
   - Sequential operadic associativity witness: (h o_0 g) o_0 f == h o_0 (g o_0 f).
   - Mismatched port colour attacks: ill-typed morphisms raise OperadAssociativityError.
   - Index bounds and exact integer index typing attacks.
   - Tree arity, root colour, and leaf colour preservation.

4. Finite Campaign Manifest & Resource Controls:
   - Manifest JSON structural validity, exact 3 runs, schema version 1.0.
   - Resource ceilings: each run cap <= 100,000 microUSD, total campaign cap <= 300,000 microUSD.
   - Frozen QM seed prompt bytes SHA-256 match.
   - Settled historical spend remains exactly USD 0.055614 with 0 held liability across 24 frozen runs.

5. End-to-End Pipeline & Evaluator Firewall:
   - Offline execution under reference_runner produces valid receipts and claims.
   - Limitations notice: final_answer_certified is strictly False; downstream QM is uncertified.
   - Serialized solver request messages contain zero evaluator answer keys or rubric leaks.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "workflows" / "wf52_finite_qm_benchmark", ROOT / "ops"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import eis.domain.allostery as allostery
from eis.domain.value_objects import AllosteryRefusal, HillParameters
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
)
import operads.domain.operad.colours as colours
import operads.domain.operad.errors as operad_errors
import operads.domain.operad.operation as ops
import operads.domain.operad.planar as planar
import pciv.use_cases.fitness as pciv_fitness
from reference_runner import HERE, OfflineTape, run, sha


class TestChallengerEISAllostericGate(unittest.TestCase):
    """Adversarial stress-testing of the EIS Allosteric Consensus Gate."""

    def setUp(self) -> None:
        self.matrix_art = build_host_matrix_artifact(SUPPORTED_SEED_SHA256)
        self.charpoly_art = build_host_charpoly_artifact(SUPPORTED_SEED_SHA256, compact=True)

    def test_single_sensor_cannot_activate_gate(self):
        """Single-sensor attack: 1 positive sensor (S=1) produces H(1)=1/5 < t=1/2."""
        single_sensor_signals = {
            "sensor_grid_identity": Fraction(1, 1),
            "sensor_degree_bounds": Fraction(0, 1),
            "sensor_trace_zero": Fraction(0, 1),
        }
        decision = EISVerificationBridge.evaluate_charpoly_evidence(
            self.charpoly_art, self.matrix_art, custom_signals=single_sensor_signals
        )
        self.assertFalse(decision["is_activated"])
        self.assertEqual(decision["positive_sensors"], 1)
        self.assertEqual(decision["aggregate_signal_str"], "1")
        self.assertEqual(decision["hill_value_str"], "1/5")
        self.assertEqual(decision["quorum_size"], 2)
        self.assertIn("NOT ACTIVATED", decision["rationale"])
        self.assertIn("needs at least 2 positive sensor(s)", decision["rationale"])

    def test_all_three_sensors_activate_gate(self):
        """Standard valid case: 3 positive sensors yield S=3, H(3)=9/13 >= 1/2."""
        decision = EISVerificationBridge.evaluate_charpoly_evidence(
            self.charpoly_art, self.matrix_art
        )
        self.assertTrue(decision["is_activated"])
        self.assertEqual(decision["positive_sensors"], 3)
        self.assertEqual(decision["aggregate_signal_str"], "3")
        self.assertEqual(decision["hill_value_str"], "9/13")
        self.assertEqual(decision["threshold_str"], "1/2")
        self.assertEqual(decision["quorum_size"], 2)
        self.assertIn("ACTIVATED", decision["rationale"])

    def test_two_sensors_reach_exact_threshold(self):
        """Boundary condition: exactly 2 positive sensors yield S=2, H(2)=4/8=1/2 == t."""
        two_sensor_signals = {
            "sensor_grid_identity": Fraction(1, 1),
            "sensor_degree_bounds": Fraction(1, 1),
            "sensor_trace_zero": Fraction(0, 1),
        }
        decision = EISVerificationBridge.evaluate_charpoly_evidence(
            self.charpoly_art, self.matrix_art, custom_signals=two_sensor_signals
        )
        self.assertTrue(decision["is_activated"])
        self.assertEqual(decision["positive_sensors"], 2)
        self.assertEqual(decision["aggregate_signal_str"], "2")
        self.assertEqual(decision["hill_value_str"], "1/2")
        self.assertEqual(decision["quorum_size"], 2)

    def test_duplicate_sensor_casing_and_whitespace_refused(self):
        """Duplication attack: same sensor key under mixed casing or trailing spaces."""
        variants = [
            {"sensor_grid_identity": Fraction(1, 1), "SENSOR_GRID_IDENTITY": Fraction(1, 1)},
            {"sensor_trace_zero": Fraction(1, 1), "  sensor_trace_zero  ": Fraction(1, 1)},
            {"sensor_degree_bounds": Fraction(1, 1), "Sensor_Degree_Bounds": Fraction(1, 1)},
        ]
        for bad_signals in variants:
            with self.assertRaises(AllosteryRefusal) as ctx:
                EISVerificationBridge.evaluate_charpoly_evidence(
                    self.charpoly_art, self.matrix_art, custom_signals=bad_signals
                )
            self.assertEqual(ctx.exception.code, "DUPLICATE_SENSOR")

    def test_sensor_cap_exceeded_refused(self):
        """Cap violation attack: sensor signal > per_sensor_cap (Fraction(1))."""
        cap_violators = [
            {"sensor_grid_identity": Fraction(3, 2), "sensor_trace_zero": Fraction(1, 1)},
            {"sensor_grid_identity": 2, "sensor_trace_zero": 0},
            {"sensor_degree_bounds": Fraction(100, 1)},
        ]
        for bad_signals in cap_violators:
            with self.assertRaises(AllosteryRefusal) as ctx:
                EISVerificationBridge.evaluate_charpoly_evidence(
                    self.charpoly_art, self.matrix_art, custom_signals=bad_signals
                )
            self.assertEqual(ctx.exception.code, "SIGNAL_ABOVE_SENSOR_CAP")

    def test_sensor_negative_signal_refused(self):
        """Negative signal attack: negative values must be refused."""
        neg_signals = [
            {"sensor_grid_identity": Fraction(-1, 1)},
            {"sensor_degree_bounds": -1},
            {"sensor_trace_zero": Fraction(-1, 1000)},
        ]
        for bad_signals in neg_signals:
            with self.assertRaises(AllosteryRefusal) as ctx:
                EISVerificationBridge.evaluate_charpoly_evidence(
                    self.charpoly_art, self.matrix_art, custom_signals=bad_signals
                )
            self.assertEqual(ctx.exception.code, "SIGNAL_OUT_OF_RANGE")

    def test_sensor_non_exact_floats_and_booleans_refused(self):
        """Type violation attack: floats, booleans, and strings must be strictly refused."""
        invalid_types = [
            {"sensor_grid_identity": 1.0},
            {"sensor_degree_bounds": True},
            {"sensor_trace_zero": False},
            {"sensor_grid_identity": "1"},
        ]
        for bad_signals in invalid_types:
            with self.assertRaises(AllosteryRefusal) as ctx:
                EISVerificationBridge.evaluate_charpoly_evidence(
                    self.charpoly_art, self.matrix_art, custom_signals=bad_signals
                )
            self.assertEqual(ctx.exception.code, "NOT_EXACT")

    def test_sensor_bad_id_types_and_empty_id_refused(self):
        """Sensor ID attack: empty strings, whitespace-only, or non-string IDs refused."""
        bad_id_signals = [
            {"": Fraction(1, 1)},
            {"   ": Fraction(1, 1)},
            {123: Fraction(1, 1)},
        ]
        for bad_signals in bad_id_signals:
            with self.assertRaises(AllosteryRefusal) as ctx:
                EISVerificationBridge.evaluate_charpoly_evidence(
                    self.charpoly_art, self.matrix_art, custom_signals=bad_signals  # type: ignore
                )
            self.assertEqual(ctx.exception.code, "BAD_SENSOR_ID")

    def test_signals_not_keyed_refused(self):
        """Non-mapping signal attack: passing list/tuple instead of dict raises SIGNALS_NOT_KEYED."""
        with self.assertRaises(AllosteryRefusal) as ctx:
            EISVerificationBridge.evaluate_charpoly_evidence(
                self.charpoly_art, self.matrix_art, custom_signals=[Fraction(1, 1), Fraction(1, 1)]  # type: ignore
            )
        self.assertEqual(ctx.exception.code, "SIGNALS_NOT_KEYED")

    def test_zero_signals_silence_refused_activation(self):
        """Zero signal silence: all 0 values produce S=0, positive_sensors=0, not activated."""
        zero_signals = {
            "sensor_grid_identity": Fraction(0, 1),
            "sensor_degree_bounds": Fraction(0, 1),
            "sensor_trace_zero": Fraction(0, 1),
        }
        decision = EISVerificationBridge.evaluate_charpoly_evidence(
            self.charpoly_art, self.matrix_art, custom_signals=zero_signals
        )
        self.assertFalse(decision["is_activated"])
        self.assertEqual(decision["positive_sensors"], 0)
        self.assertEqual(decision["aggregate_signal_str"], "0")
        self.assertEqual(decision["hill_value_str"], "0")

    def test_fake_trace_and_corrupted_matrix_deactivates_sensor(self):
        """A corrupted matrix artifact turns off both matrix-derived sensors (symbolic and structural)."""
        corrupted_mat = json.loads(json.dumps(self.matrix_art))
        corrupted_mat["coefficient_matrices"]["J"][0][0] = 1  # nonzero trace, different determinant
        decision = EISVerificationBridge.evaluate_charpoly_evidence(self.charpoly_art, corrupted_mat)
        sensors = decision["sensor_evidence"]["sensors"]
        self.assertFalse(sensors["sensor_symbolic_identity"]["ok"])
        self.assertFalse(sensors["sensor_structural_constraints"]["ok"])
        self.assertTrue(sensors["sensor_native_receipt"]["ok"])
        self.assertEqual(decision["positive_sensors"], 1)
        self.assertFalse(decision["is_activated"])

        corrupted_cp = json.loads(json.dumps(self.charpoly_art))
        corrupted_cp["polynomial"]["standard_form"] = "2*lambda^4 - 4*J^2"
        decision_corrupted = EISVerificationBridge.evaluate_charpoly_evidence(corrupted_cp, corrupted_mat)
        self.assertFalse(decision_corrupted["is_activated"])
        self.assertEqual(decision_corrupted["positive_sensors"], 0)

    def test_corrupted_grid_points_count_deactivates_sensor(self):
        """A declared grid count is never itself a signal: editing it only breaks the native sensor."""
        corrupted_cp = json.loads(json.dumps(self.charpoly_art))
        corrupted_cp["native_verification"]["grid_points_verified"] = 124
        decision = EISVerificationBridge.evaluate_charpoly_evidence(corrupted_cp, self.matrix_art)
        sensors = decision["sensor_evidence"]["sensors"]
        self.assertFalse(sensors["sensor_native_receipt"]["ok"])
        self.assertEqual(decision["positive_sensors"], 2)  # symbolic and structural recompute from the matrix
        self.assertTrue(decision["is_activated"])

        corrupted_mat = json.loads(json.dumps(self.matrix_art))
        corrupted_mat["coefficient_matrices"]["K"][1][1] = 5
        decision_both = EISVerificationBridge.evaluate_charpoly_evidence(corrupted_cp, corrupted_mat)
        self.assertFalse(decision_both["is_activated"])
        self.assertEqual(decision_both["positive_sensors"], 0)

    def test_self_reported_metadata_cannot_form_a_quorum(self):
        """Review #63 item 4: declared status plus a string starting with lambda^4 yields no signal."""
        forged = json.loads(json.dumps(self.charpoly_art))
        forged["polynomial"]["standard_form"] = "lambda^4 + J"
        decision = EISVerificationBridge.evaluate_charpoly_evidence(forged, self.matrix_art)
        self.assertEqual(decision["positive_sensors"], 0)
        self.assertFalse(decision["is_activated"])

    def test_gate_mathematical_invariance_hill_curve(self):
        """Direct HillParameters verification: H(S) = S^2 / (2^2 + S^2)."""
        gate = allostery.AllostericConsensusGate(
            parameters=HillParameters(hill_coefficient=2, half_maximal_constant=Fraction(2)),
            activation_threshold=Fraction(1, 2),
            per_sensor_cap=Fraction(1),
        )
        # S = 1 => 1 / (4 + 1) = 1/5 = 0.2 < 0.5
        dec_1 = gate.evaluate_quorum({"s1": Fraction(1, 1)})
        self.assertEqual(dec_1.hill_value, Fraction(1, 5))
        self.assertFalse(dec_1.is_activated)

        # S = 2 => 4 / (4 + 4) = 4/8 = 1/2 = 0.5 == threshold
        dec_2 = gate.evaluate_quorum({"s1": Fraction(1, 1), "s2": Fraction(1, 1)})
        self.assertEqual(dec_2.hill_value, Fraction(1, 2))
        self.assertTrue(dec_2.is_activated)

        # S = 3 => 9 / (4 + 9) = 9/13 > 0.5
        dec_3 = gate.evaluate_quorum({"s1": Fraction(1, 1), "s2": Fraction(1, 1), "s3": Fraction(1, 1)})
        self.assertEqual(dec_3.hill_value, Fraction(9, 13))
        self.assertTrue(dec_3.is_activated)


class TestChallengerPCIVTaskSetEvaluator(unittest.TestCase):
    """Adversarial stress-testing of PCIV task set and Pareto front evaluation."""

    def test_empty_candidate_metrics_refused(self):
        """Empty metrics attack: passing empty candidate list raises MISSING_MEASUREMENTS."""
        with self.assertRaises(ValueError) as ctx:
            PCIVTaskSetEvaluator.evaluate_portfolio([])
        self.assertIn("MISSING_MEASUREMENTS", str(ctx.exception))

    def test_empty_task_portfolio_refused(self):
        """Empty task set attack: passing empty task portfolio raises EMPTY_TASK_SET."""
        candidates = [
            {"id": "cand_1", "metrics": {"correctness": Fraction(85, 100), "cost": Fraction(50, 1000)}}
        ]
        with self.assertRaises(ValueError) as ctx:
            PCIVTaskSetEvaluator.evaluate_portfolio(candidates, task_portfolio=())
        self.assertIn("EMPTY_TASK_SET", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            PCIVTaskSetEvaluator.evaluate_portfolio(candidates, task_portfolio=[])
        self.assertIn("EMPTY_TASK_SET", str(ctx.exception))

    def test_forged_fitness_strings_grant_zero_credit(self):
        """Forged fitness attack: self-declared status strings earn zero operational credit."""
        forged_candidates = [
            {
                "id": "forged_cand_1",
                "metrics": {"correctness": Fraction(50, 100), "cost": Fraction(1, 10)},
                "status": "VERIFIED_EXACT",
                "gate_status": "AUTHORIZED",
                "claim": "PROVEN_GLOBAL_OPTIMUM",
            },
            {
                "id": "legit_cand_2",
                "metrics": {"correctness": Fraction(80, 100), "cost": Fraction(5, 100)},
                "status": "UNVERIFIED",
            },
        ]
        # Evaluator ignores forged strings and ranks by Pareto dominance
        res = PCIVTaskSetEvaluator.evaluate_portfolio(forged_candidates)
        # legit_cand_2 has higher correctness (0.80 > 0.50) and lower cost (0.05 < 0.10)
        # therefore legit_cand_2 strictly dominates forged_cand_1
        self.assertEqual(res["total_fronts"], 2)
        self.assertEqual(res["non_dominated_front"][0]["id"], "legit_cand_2")
        self.assertEqual(res["lexicographic_leader_id"], "legit_cand_2")

    def test_non_dominated_pareto_front_partitioning_tradeoffs(self):
        """Pareto front partitioning: trade-offs between correctness and cost."""
        # A: high accuracy, high cost
        # B: medium accuracy, medium cost
        # C: low accuracy, low cost
        # All three are mutually non-dominated -> all on Front 0!
        candidates = [
            {"id": "c_high", "metrics": {"correctness": Fraction(95, 100), "cost": Fraction(10, 100)}},
            {"id": "c_med", "metrics": {"correctness": Fraction(85, 100), "cost": Fraction(5, 100)}},
            {"id": "c_low", "metrics": {"correctness": Fraction(75, 100), "cost": Fraction(1, 100)}},
        ]
        res = PCIVTaskSetEvaluator.evaluate_portfolio(candidates)
        self.assertEqual(res["total_fronts"], 1)
        self.assertEqual(len(res["non_dominated_front"]), 3)
        # Tied on front 0: sorted lexicographically by correctness desc, then cost asc, then id
        self.assertEqual(res["non_dominated_front"][0]["id"], "c_high")
        self.assertEqual(res["non_dominated_front"][1]["id"], "c_med")
        self.assertEqual(res["non_dominated_front"][2]["id"], "c_low")

    def test_pareto_front_dominated_candidates_in_lower_fronts(self):
        """Dominated candidates must be pushed to front 1 and front 2."""
        candidates = [
            {"id": "c_optimal", "metrics": {"correctness": Fraction(90, 100), "cost": Fraction(4, 100)}},
            {"id": "c_dominated_1", "metrics": {"correctness": Fraction(85, 100), "cost": Fraction(6, 100)}},  # dominated by c_optimal
            {"id": "c_dominated_2", "metrics": {"correctness": Fraction(70, 100), "cost": Fraction(8, 100)}},  # dominated by both
        ]
        res = PCIVTaskSetEvaluator.evaluate_portfolio(candidates)
        self.assertEqual(res["total_fronts"], 3)
        self.assertEqual(len(res["non_dominated_front"]), 1)
        self.assertEqual(res["non_dominated_front"][0]["id"], "c_optimal")

    def test_pareto_front_lexicographic_tiebreak_no_composite_scalar(self):
        """Identical metric ties broken strictly by candidate ID, without composite scalar."""
        candidates = [
            {"id": "cand_beta", "metrics": {"correctness": Fraction(80, 100), "cost": Fraction(5, 100)}},
            {"id": "cand_alpha", "metrics": {"correctness": Fraction(80, 100), "cost": Fraction(5, 100)}},
        ]
        res = PCIVTaskSetEvaluator.evaluate_portfolio(candidates)
        self.assertEqual(res["total_fronts"], 1)
        self.assertEqual(len(res["non_dominated_front"]), 2)
        self.assertEqual(res["non_dominated_front"][0]["id"], "cand_alpha")
        self.assertEqual(res["non_dominated_front"][1]["id"], "cand_beta")


class TestChallengerOPERADSAssociativity(unittest.TestCase):
    """Adversarial stress-testing of OPERADS typed planar tree composition and associativity."""

    def test_canonical_pipeline_sequential_associativity(self):
        """Canonical composition: (h o_0 g) o_0 f == h o_0 (g o_0 f) from State to Receipt."""
        witness = OperadCompositionPipeline.build_composition_witness()
        self.assertTrue(witness["is_associative"])
        self.assertEqual(witness["left_composite"], "(State) -> Receipt")
        self.assertEqual(witness["right_composite"], "(State) -> Receipt")
        self.assertEqual(witness["root_colour"], "Receipt")
        self.assertEqual(witness["leaf_colour"], "State")
        self.assertEqual(witness["tree_arity"], 1)
        self.assertEqual(len(witness["operations"]), 3)

    def test_mismatched_target_to_source_port_refused(self):
        """Mismatched colour attack: pass 'Paper' instead of 'Audit' as root source colour."""
        with self.assertRaises(ValueError) as ctx:
            OperadCompositionPipeline.build_composition_witness(op_root_source="Paper")
        self.assertIn("Operad associativity verification failed", str(ctx.exception))
        self.assertIn("expected Paper, got Audit", str(ctx.exception))

    def test_unadmitted_colour_name_refused(self):
        """Domain vocabulary attack: unadmitted colour names must be rejected at Colour instantiation."""
        with self.assertRaises(ValueError) as ctx:
            colours.Colour("ArbitraryColour")
        self.assertIn("not in admitted finite colours", str(ctx.exception))

    def test_direct_operad_mismatched_intermediate_port_refused(self):
        """Direct operad test: f target 'Contract' does not match g source 'Paper'."""
        c_state = colours.Colour("State")
        c_contract = colours.Colour("Contract")
        c_paper = colours.Colour("Paper")
        c_audit = colours.Colour("Audit")
        c_receipt = colours.Colour("Receipt")

        sig_f = colours.ColourSignature(source=(c_state,), target=c_contract)
        sig_g = colours.ColourSignature(source=(c_paper,), target=c_audit)
        sig_h = colours.ColourSignature(source=(c_audit,), target=c_receipt)

        op_f = ops.OperationSignature(ops.OperationId("op_f"), sig_f)
        op_g = ops.OperationSignature(ops.OperationId("op_g"), sig_g)
        op_h = ops.OperationSignature(ops.OperationId("op_h"), sig_h)

        res = planar.TreeCompositionWitness.verify_sequential_associativity(op_h, op_g, op_f, 0, 0)
        self.assertTrue(res.is_err)
        self.assertIsInstance(res.error, operad_errors.OperadAssociativityError)
        self.assertIn("expected Paper, got Contract", res.error.message)

    def test_out_of_bounds_index_composition_refused(self):
        """Index attack: composing at index >= arity raises out of bounds."""
        c_state = colours.Colour("State")
        c_contract = colours.Colour("Contract")
        sig_1 = colours.ColourSignature(source=(c_state,), target=c_contract)
        op_1 = ops.OperationSignature(ops.OperationId("op_1"), sig_1)

        # Arity is 1, so index 1 is out of bounds
        res = planar.TreeCompositionWitness.verify_sequential_associativity(op_1, op_1, op_1, 1, 0)
        self.assertTrue(res.is_err)
        self.assertIn("out of bounds for arity 1", res.error.message)

    def test_non_integer_index_composition_refused(self):
        """Type attack: passing float index raises exact int type error."""
        c_state = colours.Colour("State")
        c_contract = colours.Colour("Contract")
        sig_1 = colours.ColourSignature(source=(c_state,), target=c_contract)

        res = planar.compose_colour_signatures(sig_1, sig_1, 0.0)  # type: ignore
        self.assertTrue(res.is_err)
        self.assertIn("index must be an exact int", res.error.message)


class TestChallengerManifestAndResourceIntegrity(unittest.TestCase):
    """Adversarial verification of the finite campaign manifest and budget ledger."""

    def setUp(self) -> None:
        self.manifest_path = ROOT / "workflows" / "wf52_finite_qm_benchmark" / "host_charpoly_pilot_20261110" / "manifest.json"
        self.assertTrue(self.manifest_path.is_file(), f"Manifest file missing: {self.manifest_path}")
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def test_manifest_schema_and_runs_count(self):
        """Manifest must adhere to schema 1.0, campaign id, and have exactly 3 planned runs."""
        self.assertEqual(self.manifest.get("schema_version"), "1.0")
        self.assertEqual(self.manifest.get("campaign_id"), "qm-hostcharpoly-20261110")
        runs = self.manifest.get("runs", [])
        self.assertEqual(len(runs), 3, "Manifest must contain exactly 3 runs")

        plans = [r["plan"] for r in runs]
        self.assertEqual(
            set(plans),
            {
                "coverage_first_direct_v1",
                "coverage_first_matrix_v1",
                "coverage_first_charpoly_v1",
            },
        )

    def test_manifest_run_caps_and_total_budget_envelope(self):
        """Each run ceiling must be <= 100,000 microUSD; total campaign <= 300,000 microUSD."""
        total_cap = self.manifest.get("cap_microusd")
        self.assertLessEqual(total_cap, 300_000)
        self.assertEqual(total_cap, 300_000)

        sum_run_caps = 0
        for r in self.manifest.get("runs", []):
            run_cap = r.get("cap_microusd")
            self.assertLessEqual(run_cap, 100_000, f"Run {r['run_id']} cap exceeds 100,000 microUSD")
            self.assertEqual(r.get("max_output_tokens"), 16000)
            self.assertEqual(r.get("provider_identity", {}).get("model"), "deepseek/deepseek-v3.2")
            self.assertEqual(r.get("provider_identity", {}).get("endpoint_slug"), "atlas-cloud/fp8")
            sum_run_caps += run_cap

        self.assertEqual(sum_run_caps, total_cap, "Sum of run caps must equal campaign cap")

    def test_manifest_frozen_qm_seed_hash_and_prompt_bytes(self):
        """Confirm frozen QM seed hash across manifest and disk seed_prompt.txt."""
        seed_prompt_path = ROOT / "workflows" / "wf52_finite_qm_benchmark" / "seed_prompt.txt"
        self.assertTrue(seed_prompt_path.is_file())
        seed_bytes = seed_prompt_path.read_bytes()
        seed_hash = sha(seed_bytes)

        self.assertEqual(seed_hash, SUPPORTED_SEED_SHA256)
        self.assertEqual(self.manifest.get("seed_sha256"), SUPPORTED_SEED_SHA256)

    def test_settled_spend_frozen_at_0_055614_and_zero_liability(self):
        """Historical comparison report must preserve 24 frozen runs, USD 0.055614 spend, 0 liability."""
        summary_path = ROOT / "workflows" / "wf52_finite_qm_benchmark" / "results_summary.json"
        self.assertTrue(summary_path.is_file())
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

        raw_runs = summary.get("raw_runs", [])
        self.assertEqual(len(raw_runs), 24, "Results summary must contain exactly 24 frozen runs")
        total_spent = sum(r.get("known_spent_usd", 0.0) for r in raw_runs)
        self.assertAlmostEqual(total_spent, 0.055614, places=6)
        total_held = sum(r.get("held_usd", 0.0) for r in raw_runs)
        self.assertEqual(total_held, 0.0)


class TestChallengerEndToEndSemanticComposition(unittest.TestCase):
    """Adversarial stress-testing of end-to-end semantic composition artifact and offline execution."""

    def test_build_semantic_composition_artifact_structure(self):
        """Verify semantic composition artifact schema, status, and sub-receipts."""
        art = build_semantic_composition_artifact(SUPPORTED_SEED_SHA256)
        self.assertEqual(art["schema"], "pfp.semantic-composition.v1")
        self.assertEqual(art["status"], "VERIFIED_OFFLINE_COMPOSITION")
        self.assertEqual(art["seed_sha256"], SUPPORTED_SEED_SHA256)

        # EIS gate sub-receipt
        eis = art["eis_allosteric_consensus"]
        self.assertTrue(eis["is_activated"])
        self.assertEqual(eis["quorum_size"], 2)
        self.assertEqual(eis["positive_sensors"], 3)

        # PCIV portfolio selection sub-receipt
        pciv = art["pciv_portfolio_selection"]
        self.assertEqual(pciv["task_count"], 5)
        self.assertEqual(pciv["candidate_count"], 5)
        self.assertEqual(
            [c["id"] for c in pciv["non_dominated_front"]],
            ["compact_certified_charpoly", "public_matrix_only", "seed_only"],
        )
        self.assertEqual(pciv["lexicographic_leader_id"], "compact_certified_charpoly")

        # OPERADS composition witness sub-receipt
        op = art["operad_composition_witness"]
        self.assertTrue(op["is_associative"])
        self.assertEqual(op["root_colour"], "Receipt")
        self.assertEqual(op["leaf_colour"], "State")

    def test_unsupported_seed_rejection(self):
        """Attempting to compose with an invalid seed hash raises ValueError."""
        with self.assertRaises(ValueError):
            build_semantic_composition_artifact("deadbeef" * 8)

    def test_limitations_and_final_answer_uncertified_firewall(self):
        """Intermediate vs final answer firewall: final_answer_certified MUST be False."""
        art = build_semantic_composition_artifact(SUPPORTED_SEED_SHA256)
        self.assertIn("limitations", art)
        limits = art["limitations"]
        self.assertFalse(limits["final_answer_certified"])
        self.assertEqual(limits["scope"], "intermediate_composition_only")
        self.assertIn("uncertified", limits["notice"].lower())

    def test_reference_runner_offline_execution_operad_composition(self):
        """Execute plan coverage_first_operad_composition_v1 offline and verify artifacts."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "run_test_operad"
            run_id = "test:coverage_first_operad_composition_v1:challenger_001"
            receipt = run(
                "coverage_first_operad_composition_v1",
                OfflineTape(["Adversarial mock response"]),
                out_dir,
                run_id,
                max_output_tokens=16000,
            )
            self.assertEqual(receipt["status"], "offline_fixture_completed")
            self.assertTrue((out_dir / "host_matrix.json").is_file())
            self.assertTrue((out_dir / "host_charpoly.json").is_file())
            self.assertTrue((out_dir / "semantic_composition_receipt.json").is_file())

            host_checks = json.loads((out_dir / "host_checks.json").read_text(encoding="utf-8"))
            self.assertTrue(host_checks["host_derived_matrix"])
            self.assertTrue(host_checks["host_derived_charpoly"])
            self.assertTrue(host_checks["semantic_composition"])
            self.assertTrue(host_checks["operadic_associativity_verified"])
            self.assertFalse(host_checks["final_answer_certified"])

            claims = [c["status"] for c in host_checks["claims"]]
            self.assertIn("EXACT_AFFINE_HAMILTONIAN_MATCH", claims)
            self.assertIn("EXACT_INTERMEDIATE_CHARPOLY_IDENTITY", claims)
            self.assertIn("TYPED_OPERADIC_COMPOSITION_VERIFIED", claims)

    def test_solver_messages_evaluator_firewall_inspection(self):
        """Inspect actual serialized solver messages: zero private reference answers or formulas."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "run_firewall_test"
            run_id = "test:coverage_first_operad_composition_v1:firewall"
            receipt = run(
                "coverage_first_operad_composition_v1",
                OfflineTape(["Adversarial test response"]),
                out_dir,
                run_id,
                max_output_tokens=16000,
            )
            messages = receipt["calls"][0]["request"]["messages"]
            self.assertEqual(len(messages), 5)

            # System prompt must match coverage-first instruction
            self.assertEqual(messages[0]["content"], COVERAGE_FIRST_INSTRUCTION)
            # User seed must match frozen seed prompt exactly
            self.assertEqual(sha(messages[1]["content"].encode("utf-8")), SUPPORTED_SEED_SHA256)

            full_payload = " ".join(m["content"] for m in messages)
            # Firewall checks: private rubric / private answers must NEVER appear
            forbidden_strings = [
                "RUBRIC",
                "rubric",
                "grader",
                "private_evaluator",
                "secret_key",
                "answer_key",
            ]
            for forbidden in forbidden_strings:
                self.assertNotIn(forbidden, full_payload)


if __name__ == "__main__":
    unittest.main()
