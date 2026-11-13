"""Unit and mutation tests for DDC Poset Trace, Symbol Game Down-Maps, and Top 10 Theorems.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
import pytest

from exact import exact_equal
from exactsym import Matrix
from covering_edge_poset import FinitePoset
from restriction_system import RestrictionSystem, RestrictionMap
from ddc_poset_trace import DDCRune, DDCPosetTraceLogger, DDCPosetCommutator
from symbol_game_downmap import (
    GENESIS_COST_TWO_FLOOR,
    SymbolGameDownMap,
    ProtectedDistinction,
)


def test_ddc_trace_logging_and_word_extraction():
    """Verify DDC 8-letter trace logger produces append-only step receipts and word."""
    poset = FinitePoset(elements=["0", "1", "2"], relations=[("0", "1"), ("1", "2")])
    logger = DDCPosetTraceLogger(poset)

    logger.log_step(DDCRune.E, source="0", defect=Fraction(0))
    logger.log_step(DDCRune.R, source="1", target="0", defect=Fraction(0))
    logger.log_step(DDCRune.C, source="1", target="0", defect=Fraction(1, 2))
    logger.log_step(DDCRune.T, source="0", defect=Fraction(0), authorized=True)

    assert logger.extract_word() == "ERCT"
    assert logger.total_accumulated_defect() == Fraction(1, 2)
    assert len(logger.steps) == 4


def test_ddc_diamond_commutator_flat_vs_curved():
    """Verify Theorem 4.6: DDC diamond commutator evaluates to zero on flat and non-zero on curved."""
    # Diamond poset: bottom < b1, b2 < top
    # 0 < 1, 2 < 3
    poset = FinitePoset(
        elements=["0", "1", "2", "3"],
        relations=[("0", "1"), ("0", "2"), ("1", "3"), ("2", "3")]
    )
    dims = {"0": 1, "1": 1, "2": 1, "3": 1}

    # Flat diamond: r_{1,0} * r_{3,1} = 2 * 3 = 6; r_{2,0} * r_{3,2} = 6 * 1 = 6
    r_31 = RestrictionMap(source="3", target="1", matrix=Matrix([[3]]))
    r_10 = RestrictionMap(source="1", target="0", matrix=Matrix([[2]]))
    r_32 = RestrictionMap(source="3", target="2", matrix=Matrix([[1]]))
    r_20 = RestrictionMap(source="2", target="0", matrix=Matrix([[6]]))
    r_30 = RestrictionMap(source="3", target="0", matrix=Matrix([[6]]))

    sys_flat = RestrictionSystem(poset, dims, [r_31, r_10, r_32, r_20, r_30])
    test_vec = Matrix([[5]])

    res_flat = DDCPosetCommutator.evaluate_diamond_commutator(
        sys_flat, bottom="0", branch1="1", branch2="2", top="3", test_vector=test_vec
    )
    assert res_flat["is_commuting"] is True
    assert res_flat["l1_defect_norm"] == Fraction(0)

    # Curved diamond: mutate r_{2,0} from 6 to 7 => 6 * 5 - 7 * 5 = 30 - 35 = -5
    r_20_curved = RestrictionMap(source="2", target="0", matrix=Matrix([[7]]))
    sys_curved = RestrictionSystem(poset, dims, [r_31, r_10, r_32, r_20_curved, r_30])

    res_curved = DDCPosetCommutator.evaluate_diamond_commutator(
        sys_curved, bottom="0", branch1="1", branch2="2", top="3", test_vector=test_vec
    )
    assert res_curved["is_commuting"] is False
    assert res_curved["l1_defect_norm"] == Fraction(5)


def test_symbol_game_downmap_distinction_collapse_and_loss_ledger():
    """Verify Theorem 4.7: down-map collapsing distinctions forces ||K||_1 >= k * mu_1."""
    tower = SymbolGameDownMap(stages=["S0", "S1", "S2"])
    tower.declare_protected_distinction("tok_alpha", "tok_beta", "Protected gauge separation")
    tower.declare_protected_distinction("tok_gamma", "tok_delta", "Protected parity distinction")

    active_tokens = ["tok_alpha", "tok_beta", "tok_gamma", "tok_delta"]

    # 1. Faithful downmap: preserves both pairs
    faithful_fn = lambda x: x
    loss_faithful = tower.evaluate_downmap_collapse("S2", "S1", faithful_fn, active_tokens)
    assert loss_faithful.loss_count == 0
    assert loss_faithful.loss_cost_mu1 == Fraction(0)

    # 2. Defective downmap: collapses tok_alpha and tok_beta to "merged_1", and tok_gamma, tok_delta to "merged_2"
    def collapsing_fn(x: str) -> str:
        if x in ("tok_alpha", "tok_beta"):
            return "merged_1"
        return "merged_2"

    loss_collapsed = tower.evaluate_downmap_collapse("S2", "S1", collapsing_fn, active_tokens)
    assert loss_collapsed.loss_count == 2
    # Floor: 2 * mu_1 = 2 * 2 = 4
    assert loss_collapsed.loss_cost_mu1 == Fraction(4)

    # Verify Theorem 4.7 bound:
    # A true curvature norm of 5 satisfies the floor (5 >= 4)
    chk_valid = SymbolGameDownMap.verify_antimorphic_curvature_lower_bound(loss_collapsed, Fraction(5))
    assert chk_valid["satisfied"] is True
    assert chk_valid["duality_surplus"] == Fraction(1)

    # An adversary claiming ||K|| = 3 is refuted!
    chk_refuted = SymbolGameDownMap.verify_antimorphic_curvature_lower_bound(loss_collapsed, Fraction(3))
    assert chk_refuted["satisfied"] is False
    assert chk_refuted["duality_surplus"] == Fraction(-1)


def test_adversarial_mutation_catches_defect_whitewash():
    """Mutation attack: attempting to whitewash distinction collapse by omitting protected pairs fails."""
    tower = SymbolGameDownMap(stages=["S0", "S1"])
    tower.declare_protected_distinction("x", "y", "Vital separation")

    collapsing_fn = lambda t: "collapsed"
    loss = tower.evaluate_downmap_collapse("S1", "S0", collapsing_fn, ["x", "y"])

    # If verifier uses 0 floor instead of mu_1 = 2, mutation is detected
    assert loss.loss_cost_mu1 == GENESIS_COST_TWO_FLOOR
    assert loss.loss_cost_mu1 > Fraction(0)
