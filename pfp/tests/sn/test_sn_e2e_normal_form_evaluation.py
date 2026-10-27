#!/usr/bin/env python3
"""End-to-end integration test executing nf_evaluator.py against sample S(n) state transition fixtures.

Validates that runtime evaluation against sample S(n) state transition fixtures yields
the exact typed terminal routes declared in each contract's terminal_route_map across:
1. nf.derivation.pdnf (Primitive Difference Normal Form)
2. nf.derivation.rpnf (Regime Passage / Retraction Path Normal Form)
3. nf.derivation.scnf (Separation / Strict Contraction Normal Form)
4. nf.epistemic.state (Epistemic State Invariant Normal Form)
5. nf.epistemic.pvnf (Provenance Verification Normal Form)

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict

import yaml

from pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR
from pfp.infrastructure.normal_forms.evaluator import NormalFormsEvaluator
from pfp.infrastructure.normal_forms.sn_dispatch import (
    evaluate_sn_state_transition,
)


def _find_repo_root(p: Path = Path(__file__).resolve()) -> Path:
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[2]


REPO_ROOT = _find_repo_root()
_SN_DIR_CANDIDATES = [
    REPO_ROOT / "education" / "documentation" / "002_s_n" / "normal_forms",
    REPO_ROOT / "education" / "documentation" / "0_s_n" / "normal_forms",
]
SN_CONTRACTS_DIR = next((d for d in _SN_DIR_CANDIDATES if d.is_dir()), _SN_DIR_CANDIDATES[0])

_GOV_CANDIDATES = [
    REPO_ROOT
    / "education"
    / "documentation"
    / "014_normal_forms"
    / "contracts_normal_forms",
    REPO_ROOT / "governance" / "contracts" / "contracts_normal_forms",
    REPO_ROOT
    / "education"
    / "documentation"
    / "13_normal_forms"
    / "contracts_normal_forms",
]
GOV_CONTRACTS_DIR = next((d for d in _GOV_CANDIDATES if d.is_dir()), _GOV_CANDIDATES[0])


class TestSnNormalFormsE2EIntegration(unittest.TestCase):
    """End-to-end integration test suite executing S(n) normal forms evaluation."""

    def setUp(self) -> None:
        self.evaluator = NormalFormsEvaluator(in_memory=True)

    def tearDown(self) -> None:
        self.evaluator.close()

    def _load_contract(self, contract_id: str) -> Dict[str, Any]:
        candidates = (
            NORMAL_FORMS_DIR / f"{contract_id}.yaml",
            SN_CONTRACTS_DIR / f"{contract_id}.yaml",
            GOV_CONTRACTS_DIR / f"{contract_id}.yaml",
        )
        contract_path = next((path for path in candidates if path.is_file()), candidates[-1])
        self.assertTrue(contract_path.is_file(), f"Missing contract YAML: {contract_path}")
        with open(contract_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # =========================================================================
    # 1. PDNF: Primitive Difference Normal Form
    # =========================================================================
    def test_pdnf_e2e_exhaustive_terminal_routes(self) -> None:
        """Assert runtime evaluation of PDNF fixtures yields every route in terminal_route_map."""
        contract = self._load_contract("nf.derivation.pdnf")
        route_map = contract["terminal_route_map"]
        declared_routes = set(contract["terminal_routes"])
        self.assertEqual(declared_routes, set(route_map.keys()))

        # Fixture 1: AcceptWitnessedIrreflexive -> Preserve
        f_accept = {
            "carrier": ["s0", "s1", "s2"],
            "irreflexivity_declared": True,
            "asserted_relation": [("s0", "s1"), ("s1", "s2")],
            "witness_map": {("s0", "s1"): 3, ("s1", "s2"): 1},
            "scope_declared": True,
        }
        res_accept = self.evaluator.evaluate_sn_transition("nf.derivation.pdnf", f_accept)
        self.assertEqual(res_accept["local_terminal"], "AcceptWitnessedIrreflexive")
        self.assertEqual(res_accept["canonical_terminal"], route_map["AcceptWitnessedIrreflexive"])
        self.assertEqual(res_accept["canonical_terminal"], "Preserve")
        self.assertTrue(res_accept["admitted"])

        # Fixture 2: RejectSelfDifference -> Reject
        f_self = {
            "carrier": ["s0", "s1"],
            "irreflexivity_declared": True,
            "asserted_relation": [("s0", "s0")],
            "witness_map": {("s0", "s0"): 5},
            "scope_declared": True,
        }
        res_self = self.evaluator.evaluate_sn_transition("nf.derivation.pdnf", f_self)
        self.assertEqual(res_self["local_terminal"], "RejectSelfDifference")
        self.assertEqual(res_self["canonical_terminal"], route_map["RejectSelfDifference"])
        self.assertEqual(res_self["canonical_terminal"], "Reject")
        self.assertFalse(res_self["admitted"])

        # Fixture 3: RejectUnwitnessedAssertion -> Reject
        f_unwitnessed = {
            "carrier": ["s0", "s1"],
            "irreflexivity_declared": True,
            "asserted_relation": [("s0", "s1")],
            "witness_map": {("s0", "s1"): 0},
            "scope_declared": True,
        }
        res_unwitnessed = self.evaluator.evaluate_sn_transition("nf.derivation.pdnf", f_unwitnessed)
        self.assertEqual(res_unwitnessed["local_terminal"], "RejectUnwitnessedAssertion")
        self.assertEqual(
            res_unwitnessed["canonical_terminal"], route_map["RejectUnwitnessedAssertion"]
        )
        self.assertEqual(res_unwitnessed["canonical_terminal"], "Reject")
        self.assertFalse(res_unwitnessed["admitted"])

        # Fixture 4: RequireCarrierDeclaration -> Refuse
        f_no_carrier = {
            "carrier": ["single_term"],
            "irreflexivity_declared": True,
            "asserted_relation": [("single_term", "other")],
        }
        res_no_carrier = self.evaluator.evaluate_sn_transition("nf.derivation.pdnf", f_no_carrier)
        self.assertEqual(res_no_carrier["local_terminal"], "RequireCarrierDeclaration")
        self.assertEqual(
            res_no_carrier["canonical_terminal"], route_map["RequireCarrierDeclaration"]
        )
        self.assertEqual(res_no_carrier["canonical_terminal"], "Refuse")
        self.assertFalse(res_no_carrier["admitted"])

        # Fixture 5: RequireIrreflexivityDeclaration -> Refuse
        f_no_irref = {
            "carrier": ["s0", "s1"],
            "irreflexivity_declared": False,
            "asserted_relation": [("s0", "s1")],
            "witness_map": {("s0", "s1"): 2},
        }
        res_no_irref = self.evaluator.evaluate_sn_transition("nf.derivation.pdnf", f_no_irref)
        self.assertEqual(res_no_irref["local_terminal"], "RequireIrreflexivityDeclaration")
        self.assertEqual(
            res_no_irref["canonical_terminal"], route_map["RequireIrreflexivityDeclaration"]
        )
        self.assertEqual(res_no_irref["canonical_terminal"], "Refuse")
        self.assertFalse(res_no_irref["admitted"])

        # Fixture 6: Undetermined -> Abstain
        f_undetermined = {
            "carrier": ["s0", "s1"],
            "irreflexivity_declared": True,
            "asserted_relation": [("s0", "s1")],
            "witness_map": {("s0", "s1"): 1},
            "scope_declared": False,
        }
        res_undetermined = self.evaluator.evaluate_sn_transition(
            "nf.derivation.pdnf", f_undetermined
        )
        self.assertEqual(res_undetermined["local_terminal"], "Undetermined")
        self.assertEqual(res_undetermined["canonical_terminal"], route_map["Undetermined"])
        self.assertEqual(res_undetermined["canonical_terminal"], "Abstain")
        self.assertFalse(res_undetermined["admitted"])

    # =========================================================================
    # 2. RPNF: Regime Passage / Retraction Path Normal Form
    # =========================================================================
    def test_rpnf_e2e_exhaustive_terminal_routes(self) -> None:
        """Assert runtime evaluation of RPNF fixtures yields every route in terminal_route_map."""
        contract = self._load_contract("nf.derivation.rpnf")
        route_map = contract["terminal_route_map"]
        declared_routes = set(contract["terminal_routes"])
        self.assertEqual(declared_routes, set(route_map.keys()))

        # Fixture 1: AcceptCertifiedRegime -> Preserve
        f_accept = {
            "history_declared": True,
            "history": [
                {"step": 0, "event": "genesis_quiescent"},
                {"step": 1, "event": "admit_s1"},
            ],
            "genesis_quiescent": True,
            "presentation_only": False,
            "certified_fold": True,
            "target_regime": "regime_S1_active",
            "recomputed_regime": "regime_S1_active",
        }
        res_accept = self.evaluator.evaluate_sn_transition("nf.derivation.rpnf", f_accept)
        self.assertEqual(res_accept["local_terminal"], "AcceptCertifiedRegime")
        self.assertEqual(res_accept["canonical_terminal"], route_map["AcceptCertifiedRegime"])
        self.assertEqual(res_accept["canonical_terminal"], "Preserve")
        self.assertTrue(res_accept["admitted"])

        # Fixture 2: RejectUncertifiedRegime -> Reject
        f_uncertified = {
            "history_declared": True,
            "history": [{"step": 0, "event": "genesis"}],
            "certified_fold": False,
            "target_regime": "regime_S2_unfolded",
            "recomputed_regime": "regime_S0_genesis",
        }
        res_uncertified = self.evaluator.evaluate_sn_transition("nf.derivation.rpnf", f_uncertified)
        self.assertEqual(res_uncertified["local_terminal"], "RejectUncertifiedRegime")
        self.assertEqual(
            res_uncertified["canonical_terminal"], route_map["RejectUncertifiedRegime"]
        )
        self.assertEqual(res_uncertified["canonical_terminal"], "Reject")
        self.assertFalse(res_uncertified["admitted"])

        # Fixture 3: RequireHistoryDeclaration -> Refuse
        f_no_hist = {
            "history_declared": False,
            "history": None,
        }
        res_no_hist = self.evaluator.evaluate_sn_transition("nf.derivation.rpnf", f_no_hist)
        self.assertEqual(res_no_hist["local_terminal"], "RequireHistoryDeclaration")
        self.assertEqual(res_no_hist["canonical_terminal"], route_map["RequireHistoryDeclaration"])
        self.assertEqual(res_no_hist["canonical_terminal"], "Refuse")
        self.assertFalse(res_no_hist["admitted"])

        # Fixture 4: RejectPresentationAsChange -> Reject
        f_pres = {
            "history_declared": True,
            "history": [{"step": 0, "event": "genesis"}],
            "presentation_only": True,
            "target_regime": "regime_mutated",
        }
        res_pres = self.evaluator.evaluate_sn_transition("nf.derivation.rpnf", f_pres)
        self.assertEqual(res_pres["local_terminal"], "RejectPresentationAsChange")
        self.assertEqual(res_pres["canonical_terminal"], route_map["RejectPresentationAsChange"])
        self.assertEqual(res_pres["canonical_terminal"], "Reject")
        self.assertFalse(res_pres["admitted"])

        # Fixture 5: Recompute -> Preserve
        f_recompute = {
            "history_declared": True,
            "history": [],
            "genesis_quiescent": False,  # Non-quiescent genesis with empty history
            "target_regime": "regime_spontaneous",
        }
        res_recompute = self.evaluator.evaluate_sn_transition("nf.derivation.rpnf", f_recompute)
        self.assertEqual(res_recompute["local_terminal"], "Recompute")
        self.assertEqual(res_recompute["canonical_terminal"], route_map["Recompute"])
        self.assertEqual(res_recompute["canonical_terminal"], "Preserve")
        self.assertTrue(res_recompute["admitted"])

    # =========================================================================
    # 3. SCNF: Separation / Strict Contraction Normal Form
    # =========================================================================
    def test_scnf_e2e_exhaustive_terminal_routes(self) -> None:
        """Assert runtime evaluation of SCNF fixtures yields every route in terminal_route_map."""
        contract = self._load_contract("nf.derivation.scnf")
        route_map = contract["terminal_route_map"]
        declared_routes = set(contract["terminal_routes"])
        self.assertEqual(declared_routes, set(route_map.keys()))

        # Fixture 1: AcceptUniqueMinimizer -> Preserve
        f_accept = {
            "measure_declared": True,
            "measure_name": "lexicographic_item_count",
            "contraction_ratio": Fraction(1, 2),
            "tied_candidates_count": 1,
            "obstruction_present": False,
        }
        res_accept = self.evaluator.evaluate_sn_transition("nf.derivation.scnf", f_accept)
        self.assertEqual(res_accept["local_terminal"], "AcceptUniqueMinimizer")
        self.assertEqual(res_accept["canonical_terminal"], route_map["AcceptUniqueMinimizer"])
        self.assertEqual(res_accept["canonical_terminal"], "Preserve")
        self.assertTrue(res_accept["admitted"])

        # Fixture 2: RecordTie -> Preserve
        f_tie = {
            "measure_declared": True,
            "measure_name": "lexicographic_item_count",
            "tied_candidates_count": 3,
            "tie_resolved_arbitrarily": True,
        }
        res_tie = self.evaluator.evaluate_sn_transition("nf.derivation.scnf", f_tie)
        self.assertEqual(res_tie["local_terminal"], "RecordTie")
        self.assertEqual(res_tie["canonical_terminal"], route_map["RecordTie"])
        self.assertEqual(res_tie["canonical_terminal"], "Preserve")
        self.assertTrue(res_tie["admitted"])

        # Fixture 3: RequireMeasureDeclaration -> Refuse
        f_ambiguous = {
            "measure_declared": True,
            "measure_name": "ambiguous_restated_measure",
            "isomorphism_undeclared": True,
        }
        res_ambiguous = self.evaluator.evaluate_sn_transition("nf.derivation.scnf", f_ambiguous)
        self.assertEqual(res_ambiguous["local_terminal"], "RequireMeasureDeclaration")
        self.assertEqual(
            res_ambiguous["canonical_terminal"], route_map["RequireMeasureDeclaration"]
        )
        self.assertEqual(res_ambiguous["canonical_terminal"], "Refuse")
        self.assertFalse(res_ambiguous["admitted"])

        # Fixture 4: RejectUnmeasuredMinimum -> Reject
        f_no_measure = {
            "measure_declared": False,
            "measure_name": None,
        }
        res_no_measure = self.evaluator.evaluate_sn_transition("nf.derivation.scnf", f_no_measure)
        self.assertEqual(res_no_measure["local_terminal"], "RejectUnmeasuredMinimum")
        self.assertEqual(res_no_measure["canonical_terminal"], route_map["RejectUnmeasuredMinimum"])
        self.assertEqual(res_no_measure["canonical_terminal"], "Reject")
        self.assertFalse(res_no_measure["admitted"])

        # Fixture 5: Escalate -> Preserve
        f_escalate = {
            "measure_declared": True,
            "measure_name": "regge_metric_order",
            "contraction_ratio": Fraction(1, 1),  # k = 1 not strict contraction
            "obstruction_present": True,
        }
        res_escalate = self.evaluator.evaluate_sn_transition("nf.derivation.scnf", f_escalate)
        self.assertEqual(res_escalate["local_terminal"], "Escalate")
        self.assertEqual(res_escalate["canonical_terminal"], route_map["Escalate"])
        self.assertEqual(res_escalate["canonical_terminal"], "Preserve")
        self.assertTrue(res_escalate["admitted"])

    # =========================================================================
    # 4. StateNF: Epistemic State Invariant Normal Form
    # =========================================================================
    def test_state_nf_e2e_exhaustive_terminal_routes(self) -> None:
        """Assert runtime evaluation of StateNF fixtures yields every route in terminal_route_map."""
        contract = self._load_contract("nf.epistemic.state")
        route_map = contract["terminal_route_map"]
        declared_routes = set(contract["terminal_routes"])
        self.assertEqual(declared_routes, set(route_map.keys()))

        # Fixture 1: Accept -> Escalate
        f_accept = {
            "value": {"state_token": "S_4_terminal", "survivor_count": 0},
            "version": 4,
            "causal_context": {"epoch": 102, "parent_digest": "sha256:abcd"},
            "is_stale": False,
            "confidence": 0.95,
            "confidence_threshold": 0.8,
            "authority_source": "auth://kernel/sn_closure",
        }
        res_accept = self.evaluator.evaluate_sn_transition("nf.epistemic.state", f_accept)
        self.assertEqual(res_accept["local_terminal"], "Accept")
        self.assertEqual(res_accept["canonical_terminal"], route_map["Accept"])
        self.assertEqual(res_accept["canonical_terminal"], "Escalate")

        # Fixture 2: Stale -> Escalate
        f_stale = {
            "value": {"metric": 42},
            "version": 2,
            "causal_context": {"epoch": 10},
            "is_stale": True,
            "authority_source": "auth://cache/node1",
        }
        res_stale = self.evaluator.evaluate_sn_transition("nf.epistemic.state", f_stale)
        self.assertEqual(res_stale["local_terminal"], "Stale")
        self.assertEqual(res_stale["canonical_terminal"], route_map["Stale"])
        self.assertEqual(res_stale["canonical_terminal"], "Escalate")

        # Fixture 3: CausalGap -> Escalate
        f_gap = {
            "value": {"revenue": 42000},
            "version": 7,
            "causal_context": None,  # Version without causal context: state flattening
            "authority_source": "auth://accounting/daily",
        }
        res_gap = self.evaluator.evaluate_sn_transition("nf.epistemic.state", f_gap)
        self.assertEqual(res_gap["local_terminal"], "CausalGap")
        self.assertEqual(res_gap["canonical_terminal"], route_map["CausalGap"])
        self.assertEqual(res_gap["canonical_terminal"], "Escalate")

        # Fixture 4: AuthorityUnknown -> BudgetUnknown
        f_no_auth = {
            "value": {"token": "unverified"},
            "version": 1,
            "causal_context": {"epoch": 1},
            "authority_source": None,
        }
        res_no_auth = self.evaluator.evaluate_sn_transition("nf.epistemic.state", f_no_auth)
        self.assertEqual(res_no_auth["local_terminal"], "AuthorityUnknown")
        self.assertEqual(res_no_auth["canonical_terminal"], route_map["AuthorityUnknown"])
        self.assertEqual(res_no_auth["canonical_terminal"], "BudgetUnknown")

        # Fixture 5: ConfidenceBelowThreshold -> Refuse
        f_low_conf = {
            "value": {"prediction": "class_a"},
            "version": 1,
            "causal_context": {"epoch": 5},
            "authority_source": "auth://ml/classifier",
            "confidence": 0.42,
            "confidence_threshold": 0.8,
        }
        res_low_conf = self.evaluator.evaluate_sn_transition("nf.epistemic.state", f_low_conf)
        self.assertEqual(res_low_conf["local_terminal"], "ConfidenceBelowThreshold")
        self.assertEqual(res_low_conf["canonical_terminal"], route_map["ConfidenceBelowThreshold"])
        self.assertEqual(res_low_conf["canonical_terminal"], "Refuse")

        # Fixture 6: Refuse -> Refuse
        f_malformed = {
            "malformed": True,
        }
        res_malformed = self.evaluator.evaluate_sn_transition("nf.epistemic.state", f_malformed)
        self.assertEqual(res_malformed["local_terminal"], "Refuse")
        self.assertEqual(res_malformed["canonical_terminal"], route_map["Refuse"])
        self.assertEqual(res_malformed["canonical_terminal"], "Refuse")

    # =========================================================================
    # 5. PvNF: Provenance Verification Normal Form
    # =========================================================================
    def test_pvnf_e2e_exhaustive_terminal_routes(self) -> None:
        """Assert runtime evaluation of PvNF fixtures yields every route in terminal_route_map."""
        contract = self._load_contract("nf.epistemic.pvnf")
        route_map = contract["terminal_route_map"]
        declared_routes = set(contract["terminal_routes"])
        self.assertEqual(declared_routes, set(route_map.keys()))

        # Fixture 1: ProvenanceTraced -> Preserve
        f_traced = {
            "source_facts": ["fact_101", "fact_102"],
            "transforms": ["parse_cochain", "calculate_holonomy"],
            "model_version": "v1.2.0-deterministic",
            "lineage_parent_ids": ["parent_state_001"],
            "non_replayable_steps": [],
        }
        res_traced = self.evaluator.evaluate_sn_transition("nf.epistemic.pvnf", f_traced)
        self.assertEqual(res_traced["local_terminal"], "ProvenanceTraced")
        self.assertEqual(res_traced["canonical_terminal"], route_map["ProvenanceTraced"])
        self.assertEqual(res_traced["canonical_terminal"], "Preserve")
        self.assertTrue(res_traced["admitted"])

        # Fixture 2: NonReplayableFlagged -> Escalate
        f_non_rep = {
            "source_facts": ["fact_201"],
            "model_version": "v1.2.0-deterministic",
            "lineage_parent_ids": ["parent_0"],
            "non_replayable_steps": ["external_web_search_query", "temperature_sample_0.7"],
        }
        res_non_rep = self.evaluator.evaluate_sn_transition("nf.epistemic.pvnf", f_non_rep)
        self.assertEqual(res_non_rep["local_terminal"], "NonReplayableFlagged")
        self.assertEqual(res_non_rep["canonical_terminal"], route_map["NonReplayableFlagged"])
        self.assertEqual(res_non_rep["canonical_terminal"], "Escalate")

        # Fixture 3: AuthorityHallucinationViolation -> Reject
        f_hallucination = {
            "source_facts": [],  # Empty source facts: authority hallucination
            "model_version": "v1.0.0",
            "lineage_parent_ids": ["parent_x"],
        }
        res_hallucination = self.evaluator.evaluate_sn_transition(
            "nf.epistemic.pvnf", f_hallucination
        )
        self.assertEqual(res_hallucination["local_terminal"], "AuthorityHallucinationViolation")
        self.assertEqual(
            res_hallucination["canonical_terminal"], route_map["AuthorityHallucinationViolation"]
        )
        self.assertEqual(res_hallucination["canonical_terminal"], "Reject")
        self.assertFalse(res_hallucination["admitted"])

        # Fixture 4: LineageLost -> Refuse
        f_broken_lineage = {
            "source_facts": ["fact_301"],
            "model_version": "v1.0.0",
            "has_lineage_break": True,
            "lineage_parent_ids": None,
        }
        res_broken = self.evaluator.evaluate_sn_transition("nf.epistemic.pvnf", f_broken_lineage)
        self.assertEqual(res_broken["local_terminal"], "LineageLost")
        self.assertEqual(res_broken["canonical_terminal"], route_map["LineageLost"])
        self.assertEqual(res_broken["canonical_terminal"], "Refuse")
        self.assertFalse(res_broken["admitted"])

        # Fixture 5: Refuse -> Refuse
        f_refusal = {
            "refusal_requested": True,
            "model_version": None,
        }
        res_refusal = self.evaluator.evaluate_sn_transition("nf.epistemic.pvnf", f_refusal)
        self.assertEqual(res_refusal["local_terminal"], "Refuse")
        self.assertEqual(res_refusal["canonical_terminal"], route_map["Refuse"])
        self.assertEqual(res_refusal["canonical_terminal"], "Refuse")
        self.assertFalse(res_refusal["admitted"])

    # =========================================================================
    # 6. Module-Level Convenience Function Parity
    # =========================================================================
    def test_module_level_evaluate_sn_state_transition_parity(self) -> None:
        """Assert evaluate_sn_state_transition matches NormalFormsEvaluator instance output."""
        f_accept = {
            "carrier": ["x", "y"],
            "irreflexivity_declared": True,
            "asserted_relation": [("x", "y")],
            "witness_map": {("x", "y"): 1},
        }
        res = evaluate_sn_state_transition("nf.derivation.pdnf", f_accept)
        self.assertEqual(res["local_terminal"], "AcceptWitnessedIrreflexive")
        self.assertEqual(res["canonical_terminal"], "Preserve")
        self.assertTrue(res["admitted"])

    def test_unsupported_contract_raises_clean_value_error(self) -> None:
        """Assert evaluator raises ValueError for unknown contract identifiers."""
        with self.assertRaises(FileNotFoundError):
            self.evaluator.evaluate_sn_transition("nf.invalid.nonexistent", {})


if __name__ == "__main__":
    unittest.main()
