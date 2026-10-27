"""Unit test fixtures executing runtime evaluation checks for nf.recursion.asrf and nf.physics.bqnf_fsign.

Grounding Contracts:
- education/documentation/13_normal_forms/contracts_normal_forms/nf.recursion.asrf.yaml
- education/documentation/13_normal_forms/contracts_normal_forms/nf.physics.bqnf_fsign.yaml
- education/documentation/13_normal_forms/contracts_normal_forms/normal_form_foundational_definitions.md

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List

import yaml

from pfp.domain.normal_forms.asrf import AsrfResult, verify_asrf
from pfp.domain.normal_forms.bqnf_fsign import (
    BqnfFsignCertificateGate,
    FloatContaminationRefusal,
    verify_bqnf_fsign,
)
from pfp.infrastructure.normal_form_loading import validate_contract_file

_CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "infrastructure/yaml/normal_forms"


class TestAsrfRuntimeEvaluation(unittest.TestCase):
    """Runtime evaluation fixtures for Autopoietic Self-Reference Refusal Form (ASRF)."""

    def test_asrf_contract_yaml_schema_conformance(self) -> None:
        """Verify nf.recursion.asrf.yaml matches the canonical normal form contract schema."""
        contract_path = _CONTRACTS_DIR / "nf.recursion.asrf.yaml"
        self.assertTrue(contract_path.is_file(), f"Missing contract file: {contract_path}")

        defects = validate_contract_file(contract_path)
        self.assertEqual(defects, [], f"Schema defects in {contract_path}: {defects}")

        with open(contract_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        ident = data["identity"]
        self.assertEqual(ident["id"], "nf.recursion.asrf")
        self.assertEqual(ident["short_name"], "ASRF")
        self.assertEqual(ident["family"], "recursion")

        terminal_routes = data["terminal_routes"]
        self.assertEqual(set(terminal_routes), {"Accept", "SelfReferenceRefusal"})

        route_map = data["terminal_route_map"]
        self.assertEqual(route_map["Accept"], "Preserve")
        self.assertEqual(route_map["SelfReferenceRefusal"], "Refuse")

    def test_asrf_accept_distinct_caller_and_target_hashes_no_graph(self) -> None:
        """Admitted step: caller hash distinct from target hash without call graph."""
        res = verify_asrf(
            caller_hash="sha256:0123456789abcdef0123456789abcdef",
            target_hash="sha256:fedcba9876543210fedcba9876543210",
        )
        self.assertEqual(res.terminal, "Accept")
        self.assertEqual(res.action, "Preserve")
        self.assertTrue(res.admitted)
        self.assertFalse(res.cycle_detected)
        self.assertIsNone(res.detected_cycle)
        self.assertEqual(res.status, "Accept")
        self.assertIn("differs", res.reason)

    def test_asrf_refusal_identical_hashes_direct_loop(self) -> None:
        """Refused step: caller hash equals target hash (direct self-certification cycle)."""
        same_hash = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        res = verify_asrf(caller_hash=same_hash, target_hash=same_hash)
        self.assertEqual(res.terminal, "SelfReferenceRefusal")
        self.assertEqual(res.action, "Refuse")
        self.assertFalse(res.admitted)
        self.assertTrue(res.cycle_detected)
        self.assertEqual(res.detected_cycle, (same_hash, same_hash))
        self.assertEqual(res.status, "SelfReferenceRefusal_IdenticalHashes")
        self.assertIn("equals target hash", res.reason)

    def test_asrf_accept_acyclic_dependency_pipeline(self) -> None:
        """Admitted step: directed pipeline A -> B -> C -> D contains no cycle through caller and target."""
        call_graph = {
            "node_A": ["node_B"],
            "node_B": ["node_C"],
            "node_C": ["node_D"],
            "node_D": [],
        }
        res = verify_asrf(caller_hash="node_A", target_hash="node_B", call_graph=call_graph)
        self.assertEqual(res.terminal, "Accept")
        self.assertEqual(res.action, "Preserve")
        self.assertTrue(res.admitted)
        self.assertFalse(res.cycle_detected)
        self.assertEqual(res.call_graph_nodes, 4)
        self.assertEqual(res.call_graph_edges, 3)

    def test_asrf_refusal_transitive_call_graph_cycle(self) -> None:
        """Refused step: transitive path from target back to caller completes directed self-cycle."""
        # Existing graph has path: target_B -> node_C -> node_D -> caller_A
        # Caller A calling Target B would close the directed cycle A -> B -> C -> D -> A.
        call_graph = {
            "target_B": ["node_C"],
            "node_C": ["node_D"],
            "node_D": ["caller_A"],
            "caller_A": [],
        }
        res = verify_asrf(caller_hash="caller_A", target_hash="target_B", call_graph=call_graph)
        self.assertEqual(res.terminal, "SelfReferenceRefusal")
        self.assertEqual(res.action, "Refuse")
        self.assertFalse(res.admitted)
        self.assertTrue(res.cycle_detected)
        self.assertEqual(res.status, "SelfReferenceRefusal_CallGraphCycle")
        self.assertIsNotNone(res.detected_cycle)
        expected_cycle = ("caller_A", "target_B", "node_C", "node_D", "caller_A")
        self.assertEqual(res.detected_cycle, expected_cycle)

    def test_asrf_refusal_two_node_mutual_cycle(self) -> None:
        """Refused step: target already calls caller (B -> A), so A calling B closes 2-cycle."""
        call_graph = [("node_B", "node_A")]
        res = verify_asrf(caller_hash="node_A", target_hash="node_B", call_graph=call_graph)
        self.assertEqual(res.terminal, "SelfReferenceRefusal")
        self.assertEqual(res.action, "Refuse")
        self.assertFalse(res.admitted)
        self.assertTrue(res.cycle_detected)
        self.assertEqual(res.detected_cycle, ("node_A", "node_B", "node_A"))

    def test_asrf_accept_disjoint_cycle_not_involving_caller_or_target(self) -> None:
        """Admitted step: cycle exists in disconnected component (X <-> Y) without touching caller or target."""
        call_graph = {
            "node_X": ["node_Y"],
            "node_Y": ["node_X"],
            "caller_A": ["target_B"],
            "target_B": ["node_Z"],
        }
        res = verify_asrf(caller_hash="caller_A", target_hash="target_B", call_graph=call_graph)
        self.assertEqual(res.terminal, "Accept")
        self.assertEqual(res.action, "Preserve")
        self.assertTrue(res.admitted)
        self.assertFalse(res.cycle_detected)

    def test_asrf_refusal_malformed_empty_or_whitespace_hashes(self) -> None:
        """Malformed input: empty or whitespace strings fail closed as SelfReferenceRefusal."""
        for c_hash, t_hash in [("", "h2"), ("h1", ""), ("   ", "h2"), ("h1", "   ")]:
            res = verify_asrf(caller_hash=c_hash, target_hash=t_hash)
            self.assertEqual(res.terminal, "SelfReferenceRefusal")
            self.assertEqual(res.action, "Refuse")
            self.assertFalse(res.admitted)
            self.assertEqual(res.status, "SelfReferenceRefusal_MalformedDeclaration")

    def test_asrf_refusal_record_partitioning_lossless_separation(self) -> None:
        """Quadrilateral lossless reconstruction: refused steps remain quarantined apart from admitted evaluations."""
        evaluation_ledger: List[Dict[str, Any]] = [
            {"step_id": "eval_01", "caller": "agent_alpha", "target": "solver_beta"},
            {"step_id": "eval_02", "caller": "agent_alpha", "target": "agent_alpha"},  # Self-loop
            {"step_id": "eval_03", "caller": "agent_gamma", "target": "solver_delta"},
            {"step_id": "eval_04", "caller": "solver_delta", "target": "agent_gamma"},  # Cyclic
        ]
        history_graph = [("agent_gamma", "solver_delta")]

        admitted_evaluations: List[AsrfResult] = []
        quarantined_refusals: List[AsrfResult] = []

        for record in evaluation_ledger:
            cg = history_graph if record["step_id"] == "eval_04" else None
            res = verify_asrf(record["caller"], record["target"], call_graph=cg)
            if res.terminal == "Accept":
                admitted_evaluations.append(res)
            else:
                quarantined_refusals.append(res)

        self.assertEqual(len(admitted_evaluations), 2)
        self.assertEqual(len(quarantined_refusals), 2)
        self.assertTrue(all(r.admitted for r in admitted_evaluations))
        self.assertTrue(all(not r.admitted for r in quarantined_refusals))
        # Total partition equals input cardinality (lossless separation)
        self.assertEqual(
            len(admitted_evaluations) + len(quarantined_refusals), len(evaluation_ledger)
        )

    def test_asrf_cohomology_and_incompleteness_non_claim_telemetry(self) -> None:
        """Verify non-claims: contract computes no cohomology groups and claims no incompleteness theorem."""
        res = verify_asrf(caller_hash="hash_1", target_hash="hash_2")
        self.assertEqual(res.terminal, "Accept")
        self.assertFalse(hasattr(res, "cohomology_group"))
        self.assertFalse(hasattr(res, "incompleteness_proof"))


class TestBqnfFsignRuntimeEvaluation(unittest.TestCase):
    """Runtime evaluation fixtures for Fermion Sign Problem Boundary-Quotient Normal Form (BQNF-FSIGN)."""

    def test_bqnf_fsign_contract_yaml_schema_conformance(self) -> None:
        """Verify nf.physics.bqnf_fsign.yaml matches the canonical normal form contract schema."""
        contract_path = _CONTRACTS_DIR / "nf.physics.bqnf_fsign.yaml"
        self.assertTrue(contract_path.is_file(), f"Missing contract file: {contract_path}")

        defects = validate_contract_file(contract_path)
        self.assertEqual(defects, [], f"Schema defects in {contract_path}: {defects}")

        with open(contract_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        ident = data["identity"]
        self.assertEqual(ident["id"], "nf.physics.bqnf_fsign")
        self.assertEqual(ident["short_name"], "BQNF-FSIGN")
        self.assertEqual(ident["family"], "representation")

        expected_terminals = {
            "StoquasticPositivityPreserved",
            "InvolutionCancellationPreserved",
            "DeterminantalPositivityPreserved",
            "AlternatingGaugeObstruction",
            "IntegratedPathGapObstruction",
            "UnsupportedProposal",
            "Refuse",
        }
        self.assertEqual(set(data["terminal_routes"]), expected_terminals)

        route_map = data["terminal_route_map"]
        self.assertEqual(route_map["StoquasticPositivityPreserved"], "Preserve")
        self.assertEqual(route_map["InvolutionCancellationPreserved"], "Preserve")
        self.assertEqual(route_map["DeterminantalPositivityPreserved"], "Preserve")
        self.assertEqual(route_map["AlternatingGaugeObstruction"], "Invalidate")
        self.assertEqual(route_map["IntegratedPathGapObstruction"], "Invalidate")
        self.assertEqual(route_map["UnsupportedProposal"], "Unsupported")
        self.assertEqual(route_map["Refuse"], "Refuse")

    # -------------------------------------------------------------------------
    # Route 1: Positivity (Stoquastic & Non-negative carriers)
    # -------------------------------------------------------------------------

    def test_positivity_stoquastic_matrix_2x2(self) -> None:
        """Positivity route: explicit real symmetric matrix with non-positive off-diagonals."""
        host_params = {
            "hamiltonian_matrix": [[0, -1], [-1, 0]],
        }
        proposal = {"route": "positivity"}
        res = verify_bqnf_fsign(host_params, proposal, hamiltonian_type="stoquastic")
        self.assertEqual(res.terminal, "Positivity")
        self.assertEqual(res.action, "Preserve")
        self.assertTrue(res.admitted)
        self.assertTrue(res.condition_checks.get("positivity"))

    def test_positivity_stoquastic_matrix_bipartite_4x4(self) -> None:
        """Positivity route: 4-site bipartite ring with non-positive off-diagonal hopping."""
        matrix = [
            [0, -1, 0, -1],
            [-1, 0, -1, 0],
            [0, -1, 0, -1],
            [-1, 0, -1, 0],
        ]
        host_params = {"hamiltonian_matrix": matrix}
        proposal = {"representation": "worldline_hopping", "route": "positivity"}
        res = verify_bqnf_fsign(host_params, proposal, hamiltonian_type="stoquastic")
        self.assertEqual(res.terminal, "Positivity")
        self.assertEqual(res.action, "Preserve")
        self.assertTrue(res.admitted)

    def test_positivity_finite_signed_weights_all_nonnegative(self) -> None:
        """Positivity route: declared finite configuration weights are strictly non-negative."""
        host_params = {
            "configuration_weights": {
                "config_1": Fraction(3, 4),
                "config_2": Fraction(1, 2),
                "config_3": 0,
            }
        }
        proposal = {"representation": "finite_signed", "route": "positivity"}
        res = verify_bqnf_fsign(host_params, proposal)
        self.assertEqual(res.terminal, "Positivity")
        self.assertEqual(res.action, "Preserve")
        self.assertTrue(res.admitted)

    def test_positivity_refused_on_unstoquastic_matrix(self) -> None:
        """Positivity route fails closed when off-diagonal elements are positive (unstoquastic)."""
        host_params = {
            "hamiltonian_matrix": [[0, 1], [1, 0]],  # +1 off-diagonal violates stoquasticity
        }
        proposal = {"route": "positivity"}
        res = verify_bqnf_fsign(host_params, proposal, hamiltonian_type="stoquastic")
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.action, "Refuse")
        self.assertFalse(res.admitted)
        self.assertEqual(res.status, "Refused_UnverifiedPositivity")

    # -------------------------------------------------------------------------
    # Route 2: Determinantal Positivity (Free Fermions & Attractive Hubbard)
    # -------------------------------------------------------------------------

    def test_determinantal_positivity_free_fermion_u0(self) -> None:
        """Determinantal route: U=0 free fermions with real symmetric hopping matrix."""
        hopping = [
            [0, -1, -1],
            [-1, 0, -1],
            [-1, -1, 0],
        ]
        host_params = {
            "U": 0,
            "h_up": hopping,
            "h_down": hopping,
            "mu_up": 0,
            "mu_down": 0,
        }
        proposal = {"representation": "determinant", "route": "determinantal_positivity"}
        res = verify_bqnf_fsign(host_params, proposal, hamiltonian_type="c3_triangular")
        self.assertEqual(res.terminal, "DeterminantalPositivity")
        self.assertEqual(res.action, "Preserve")
        self.assertTrue(res.admitted)
        self.assertTrue(res.condition_checks.get("zero_interaction"))

    def test_determinantal_positivity_attractive_hubbard_balanced(self) -> None:
        """Determinantal route: U < 0 attractive Hubbard with identical spin matrices and equal chemical potentials."""
        hopping = [
            [0, -1, -1],
            [-1, 0, -1],
            [-1, -1, 0],
        ]
        host_params = {
            "U": -2,
            "h_up": hopping,
            "h_down": hopping,
            "mu_up": 0,
            "mu_down": 0,
        }
        proposal = {"representation": "determinant", "route": "determinantal_positivity"}
        res = verify_bqnf_fsign(host_params, proposal, hamiltonian_type="c3_triangular")
        self.assertEqual(res.terminal, "DeterminantalPositivity")
        self.assertEqual(res.action, "Preserve")
        self.assertTrue(res.admitted)
        self.assertTrue(res.condition_checks.get("attractive_interaction"))
        self.assertTrue(res.condition_checks.get("identical_real_spin_matrices"))

    def test_determinantal_positivity_refused_unbalanced_chemical_potentials(self) -> None:
        """Determinantal route refused: U < 0 with unequal chemical potentials violates determinant squaring."""
        hopping = [[0, -1], [-1, 0]]
        host_params = {
            "U": -2,
            "h_up": hopping,
            "h_down": hopping,
            "mu_up": 1,  # Unbalanced chemical potential
            "mu_down": 0,
        }
        proposal = {"representation": "determinant", "route": "determinantal_positivity"}
        res = verify_bqnf_fsign(host_params, proposal, hamiltonian_type="hubbard")
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.action, "Refuse")
        self.assertFalse(res.admitted)
        self.assertEqual(res.status, "Refused_DeterminantHypotheses")

    def test_determinantal_positivity_refused_unbalanced_spin_matrices(self) -> None:
        """Determinantal route refused: U < 0 with h_up != h_down violates determinant squaring."""
        h_up = [[0, -1], [-1, 0]]
        h_down = [[0, -2], [-2, 0]]  # Asymmetric hopping
        host_params = {
            "U": -2,
            "h_up": h_up,
            "h_down": h_down,
            "mu_up": 0,
            "mu_down": 0,
        }
        proposal = {"representation": "determinant", "route": "determinantal_positivity"}
        res = verify_bqnf_fsign(host_params, proposal, hamiltonian_type="hubbard")
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.action, "Refuse")
        self.assertFalse(res.admitted)
        self.assertEqual(res.status, "Refused_DeterminantHypotheses")

    def test_determinantal_positivity_refused_missing_hypotheses(self) -> None:
        """Determinantal route refused: missing interaction U or spin matrices fails closed."""
        host_params = {"hamiltonian_type": "hubbard"}
        proposal = {"representation": "determinant", "route": "determinantal_positivity"}
        res = verify_bqnf_fsign(host_params, proposal, hamiltonian_type="hubbard")
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.status, "Refused_MissingDeterminantHypotheses")

    # -------------------------------------------------------------------------
    # Route 3: Exact Cancellation via Verified 4-Axiom Involution
    # -------------------------------------------------------------------------

    def test_exact_cancellation_finite_toy_involution_all_four_laws(self) -> None:
        """ExactCancellation route: verified 4-axiom involution witness cancels negative weights."""
        host_params = {
            "configuration_weights": {
                "negative": "-1/2",
                "positive": "1/2",
                "residue": 2,
            }
        }
        proposal = {
            "representation": "finite_signed",
            "route": "exact_cancellation",
            "xi_witness": {"pairs": {"negative": "positive", "positive": "negative"}},
        }
        res = verify_bqnf_fsign(host_params, proposal)
        self.assertEqual(res.terminal, "ExactCancellation")
        self.assertEqual(res.action, "Repair")
        self.assertTrue(res.admitted)
        checks = res.condition_checks
        self.assertTrue(checks["involution_law"])
        self.assertTrue(checks["fixed_point_free"])
        self.assertTrue(checks["sign_reversing"])
        self.assertTrue(checks["weight_preserving"])
        self.assertTrue(checks["negative_coverage"])

    def test_exact_cancellation_refused_identity_pseudo_witness(self) -> None:
        """ExactCancellation refused: identity mapping (Xi(x) = x) detected as hallucinated proof."""
        host_params = {
            "hamiltonian_matrix": [[0, -1], [-1, 0]],
        }
        proposal = {"xi_witness": {"mapping": "identity"}}
        gate = BqnfFsignCertificateGate("stoquastic", host_params)
        res = gate.verify_sign_free(proposal)
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.action, "Refuse")
        self.assertFalse(res.admitted)
        self.assertEqual(res.status, "Refused_UnverifiedInvolution_IdentityNotSignReversing")
        self.assertTrue(res.hallucination_detected)

    def test_exact_cancellation_refused_fixed_point(self) -> None:
        """ExactCancellation refused: involution has fixed point Xi(x) == x."""
        host_params = {"configuration_weights": {"c1": "-1/2", "c2": "1/2"}}
        # Fixed point on c1
        proposal = {
            "representation": "finite_signed",
            "route": "exact_cancellation",
            "xi_witness": {"pairs": {"c1": "c1", "c2": "c2"}},
        }
        res = verify_bqnf_fsign(host_params, proposal)
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.status, "Refused_UnverifiedInvolution_FailedLaws")
        self.assertFalse(res.condition_checks["fixed_point_free"])

    def test_exact_cancellation_refused_same_sign_pairing(self) -> None:
        """ExactCancellation refused: pairs positive configuration with positive configuration."""
        host_params = {"configuration_weights": {"pos1": "1/2", "pos2": "1/2", "neg1": "-1/2"}}
        proposal = {
            "representation": "finite_signed",
            "route": "exact_cancellation",
            "xi_witness": {"pairs": {"pos1": "pos2", "pos2": "pos1"}},
        }
        res = verify_bqnf_fsign(host_params, proposal)
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.status, "Refused_UnverifiedInvolution_FailedLaws")
        self.assertFalse(res.condition_checks["sign_reversing"])

    def test_exact_cancellation_refused_weight_mismatch(self) -> None:
        """ExactCancellation refused: paired configurations have different absolute weights."""
        host_params = {"configuration_weights": {"neg": "-1/2", "pos": "1/4"}}
        proposal = {
            "representation": "finite_signed",
            "route": "exact_cancellation",
            "xi_witness": {"pairs": {"neg": "pos", "pos": "neg"}},
        }
        res = verify_bqnf_fsign(host_params, proposal)
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.status, "Refused_UnverifiedInvolution_FailedLaws")
        self.assertFalse(res.condition_checks["weight_preserving"])

    def test_exact_cancellation_refused_unpaired_negative_residue(self) -> None:
        """ExactCancellation refused: negative configuration exists that is not covered by pairs map."""
        host_params = {
            "configuration_weights": {
                "neg1": "-1/2",
                "pos1": "1/2",
                "neg_unpaired": "-1/4",  # Left uncovered
            }
        }
        proposal = {
            "representation": "finite_signed",
            "route": "exact_cancellation",
            "xi_witness": {"pairs": {"neg1": "pos1", "pos1": "neg1"}},
        }
        res = verify_bqnf_fsign(host_params, proposal)
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.status, "Refused_UnverifiedInvolution_FailedLaws")
        self.assertFalse(res.condition_checks["negative_coverage"])

    def test_exact_cancellation_refused_open_carrier(self) -> None:
        """ExactCancellation refused: involution pairs target configuration IDs outside host weights."""
        host_params = {"configuration_weights": {"neg": "-1/2"}}
        proposal = {
            "representation": "finite_signed",
            "route": "exact_cancellation",
            "xi_witness": {"pairs": {"neg": "phantom_id", "phantom_id": "neg"}},
        }
        res = verify_bqnf_fsign(host_params, proposal)
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.status, "Refused_UnverifiedInvolution_Carrier")

    # -------------------------------------------------------------------------
    # Route 4: Open Gauge Obstruction (Alternating-Site Gauge)
    # -------------------------------------------------------------------------

    def test_open_gauge_obstruction_c3_odd_cycle(self) -> None:
        """OpenGaugeObstruction route: C3 triangular loop contains certified odd cycle in declared bonds."""
        host_params = {
            "t": 1,
            "U": 2,
            "beta": "1/4",
            "mu": 0,
            "bonds": [(0, 1), (1, 2), (2, 0)],
        }
        proposal = {
            "move_type": "OPEN_SIGN_OBSTRUCTION",
            "obstruction_witness": {
                "type": "alternating_site_gauge",
                "cycle": [0, 1, 2],
            },
        }
        gate = BqnfFsignCertificateGate("c3_triangular", host_params)
        res = gate.verify_proposal_item(proposal)
        self.assertEqual(res.terminal, "OpenGaugeObstruction")
        self.assertEqual(res.action, "Quarantine")
        self.assertTrue(res.admitted)
        self.assertTrue(res.condition_checks.get("odd_cycle_in_declared_graph"))

    def test_open_gauge_obstruction_refused_even_cycle(self) -> None:
        """Gauge obstruction refused: even cycle (e.g. 4-ring) does not frustrate alternating gauge."""
        host_params = {
            "bonds": [(0, 1), (1, 2), (2, 3), (3, 0)],
        }
        proposal = {
            "move_type": "OPEN_SIGN_OBSTRUCTION",
            "obstruction_witness": {
                "type": "alternating_site_gauge",
                "cycle": [0, 1, 2, 3],  # Even length
            },
        }
        gate = BqnfFsignCertificateGate("c4_square", host_params)
        res = gate.verify_proposal_item(proposal)
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.status, "Refused_UnverifiedObstruction")

    def test_open_gauge_obstruction_refused_cycle_not_in_bonds(self) -> None:
        """Gauge obstruction refused: supplied cycle edges do not belong to host graph."""
        host_params = {
            "bonds": [(0, 1), (1, 2)],  # Missing edge (2, 0)
        }
        proposal = {
            "move_type": "OPEN_SIGN_OBSTRUCTION",
            "obstruction_witness": {
                "type": "alternating_site_gauge",
                "cycle": [0, 1, 2],
            },
        }
        gate = BqnfFsignCertificateGate("line_graph", host_params)
        res = gate.verify_proposal_item(proposal)
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.status, "Refused_UnverifiedObstruction")

    # -------------------------------------------------------------------------
    # Route 5: Open Sign Obstruction (Integrated Sequence Gap on C3)
    # -------------------------------------------------------------------------

    def test_open_sign_obstruction_c3_integrated_path_gap(self) -> None:
        """OpenSignObstruction route: C3 cluster with verified rational path gap on 64-state carrier."""
        host_params = {
            "t": 1,
            "U": 2,
            "beta": Fraction(1, 4),
            "mu": 0,
            "bonds": [(0, 1), (1, 2), (2, 0)],
        }
        proposal = {
            "move_type": "OPEN_SIGN_OBSTRUCTION",
            "obstruction_witness": {"type": "c3_integrated_path_gap"},
        }
        gate = BqnfFsignCertificateGate("c3_triangular", host_params)
        res = gate.verify_proposal_item(proposal)
        self.assertEqual(res.terminal, "OpenSignObstruction")
        self.assertEqual(res.action, "Quarantine")
        self.assertTrue(res.admitted)
        self.assertTrue(res.condition_checks.get("integrated_path_gap"))
        self.assertTrue(res.details.get("gap_certified"))

    def test_open_sign_obstruction_refused_mismatched_parameters(self) -> None:
        """OpenSignObstruction refused: parameters deviate from verified C3 carrier."""
        host_params = {
            "t": 1,
            "U": 5,  # Mismatched interaction
            "beta": Fraction(1, 4),
            "mu": 0,
        }
        proposal = {
            "move_type": "OPEN_SIGN_OBSTRUCTION",
            "obstruction_witness": {"type": "c3_integrated_path_gap"},
        }
        gate = BqnfFsignCertificateGate("c3_triangular", host_params)
        res = gate.verify_proposal_item(proposal)
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.status, "Refused_UnverifiedObstruction")

    # -------------------------------------------------------------------------
    # Route 6: Adversarial Refusals, Zero-Float Law & Barrier Non-Claims
    # -------------------------------------------------------------------------

    def test_refused_prose_masquerading_as_evidence(self) -> None:
        """Generic complexity claim ('Repulsive Hubbard is NP-hard') is refused without instance witness."""
        host_params = {"U": 2}
        proposal = {
            "move_type": "OPEN_SIGN_OBSTRUCTION",
            "reason": "Repulsive Hubbard is NP-hard",
        }
        gate = BqnfFsignCertificateGate("repulsive_hubbard", host_params)
        res = gate.verify_proposal_item(proposal)
        self.assertEqual(res.terminal, "Refused")
        self.assertEqual(res.action, "Refuse")
        self.assertFalse(res.admitted)
        self.assertEqual(res.status, "Refused_UnverifiedObstruction")

    def test_zero_float_law_rejection_in_matrix(self) -> None:
        """Zero-Float Law: passing python float in Hamiltonian matrix raises FloatContaminationRefusal."""
        host_params = {
            "hamiltonian_matrix": [[0.0, -1.0], [-1.0, 0.0]],  # Floats forbidden
        }
        proposal = {"route": "positivity"}
        with self.assertRaises(FloatContaminationRefusal) as ctx:
            verify_bqnf_fsign(host_params, proposal, hamiltonian_type="stoquastic")
        self.assertIn("FloatContaminationRefusal", str(ctx.exception))

    def test_zero_float_law_rejection_in_weights(self) -> None:
        """Zero-Float Law: passing python float in configuration weights raises FloatContaminationRefusal."""
        host_params = {
            "configuration_weights": {"c1": 0.5},  # Float forbidden
        }
        proposal = {
            "representation": "finite_signed",
            "route": "exact_cancellation",
            "xi_witness": {"pairs": {"c1": "c2"}},
        }
        with self.assertRaises(FloatContaminationRefusal) as ctx:
            verify_bqnf_fsign(host_params, proposal)
        self.assertIn("FloatContaminationRefusal", str(ctx.exception))

    def test_adversarial_barrier_and_non_claims(self) -> None:
        """Verify contract non-claims: no Troyer-Wiese NP-hard barrier bypass claimed."""
        contract_path = _CONTRACTS_DIR / "nf.physics.bqnf_fsign.yaml"
        with open(contract_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        non_claims = data["purpose"]["non_claims"]
        self.assertTrue(any("troyer-wiese" in nc.lower() for nc in non_claims))
        self.assertTrue(any("authorityeffect none" in nc.lower() for nc in non_claims))


class TestCrossContractEvaluationReconciliation(unittest.TestCase):
    """End-to-end reconciliation across ASRF and BQNF-FSIGN contracts."""

    def test_dual_contract_runtime_pipeline_execution(self) -> None:
        """Pipeline executing both ASRF and BQNF-FSIGN preserves typed terminal routing."""
        # 1. Execute ASRF step
        asrf_step = verify_asrf(
            caller_hash="verification_agent_v1",
            target_hash="fock_space_state_64",
            call_graph={"verification_agent_v1": ["fock_space_state_64"]},
        )
        self.assertEqual(asrf_step.terminal, "Accept")
        self.assertEqual(asrf_step.action, "Preserve")

        # 2. Execute BQNF-FSIGN step on the verified fock state
        bqnf_step = verify_bqnf_fsign(
            host_parameters={"hamiltonian_matrix": [[0, -1], [-1, 0]]},
            proposal={"route": "positivity"},
            hamiltonian_type="stoquastic",
        )
        self.assertEqual(bqnf_step.terminal, "Positivity")
        self.assertEqual(bqnf_step.action, "Preserve")

        # 3. Assert typed routing consistency
        allowed_actions = {"Preserve", "Repair", "Quarantine", "Refuse"}
        self.assertIn(asrf_step.action, allowed_actions)
        self.assertIn(bqnf_step.action, allowed_actions)


if __name__ == "__main__":
    unittest.main()
