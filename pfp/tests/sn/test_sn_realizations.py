"""Unit tests for S(n) Formal Mathematical Realizations (Track 010).

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from omega_engine_pfp.domain.sn_tower.sn_realizations import (
    AdjunctionCochain,
    AutopoieticAudit,
    DaggerArrow,
    DialectProjection,
    DiscreteHodge,
    FilteredIndObject,
    HashimotoGraph,
    Polygraph2,
    RGBChannel,
    Simplex1,
    Simplicial1Skeleton,
    authority_filter,
    bounded_exists,
    bounded_forall,
    debruijn_shift,
    irreflexive_cut,
)


def test_simplex1_boundary_and_reversal():
    s = Simplex1("a", "b")
    assert s.boundary() == {"b": 1, "a": -1}
    s_rev = s.reverse()
    assert s_rev.boundary() == {"a": 1, "b": -1}


def test_simplicial_1_skeleton():
    skel = Simplicial1Skeleton(5)
    assert skel.verify_edge_count() is True
    assert len(skel.generate_edges()) == 10


def test_irreflexive_cut_boundary():
    assert irreflexive_cut("node1", "node2") is True
    with pytest.raises(ValueError, match="Irreflexive violation"):
        irreflexive_cut("node1", "node1")


def test_bounded_quantifiers():
    carrier = {2, 4, 6, 8}
    assert bounded_forall(carrier, lambda x: x % 2 == 0) is True
    assert bounded_forall(carrier, lambda x: x > 5) is False
    assert bounded_exists(carrier, lambda x: x == 6) is True
    assert bounded_exists(carrier, lambda x: x == 5) is False


def test_polygraph2_confluence():
    assert Polygraph2.normal_form("<><><><>") == "<>"
    assert Polygraph2.normal_form("<>" * 6) == "<>"


def test_adjunction_cochain():
    assert AdjunctionCochain.verify_counit([-100, 0, 42, 999]) is True


def test_dagger_arrow_involution():
    arr = DaggerArrow("X", "Y", "morphism")
    assert arr.verify_double_dagger() is True
    dagger = arr.dagger()
    assert dagger.src == "Y"
    assert dagger.tgt == "X"
    assert dagger.label == "morphism^dagger"
    double_dagger = dagger.dagger()
    assert double_dagger.label == "morphism"


def test_debruijn_shift_dynamics():
    assert debruijn_shift("010", "1") == "101"
    assert debruijn_shift("101", "0") == "010"


def test_authority_filter_quarantine():
    assert authority_filter("proposal") == "RED"
    assert authority_filter("verified_solver") == "BLUE"
    assert authority_filter("human_signoff") == "GREEN"
    with pytest.raises(ValueError, match="Unknown stage"):
        authority_filter("untracked_stage")


def test_rgb_channel_firewall():
    rgb = RGBChannel()
    rgb.propose_red("claim_1", "speculative proposal")
    assert "claim_1" in rgb.red
    assert "claim_1" not in rgb.green

    # Verification passes
    passed = rgb.verify_blue("claim_1", lambda: 3 * 3 == 9)
    assert passed is True
    assert "claim_1" in rgb.green
    assert rgb.is_promoted_to_genesis("claim_1") is False

    # Verification fails
    rgb.propose_red("bad_claim", "invalid")
    failed = rgb.verify_blue("bad_claim", lambda: False)
    assert failed is False
    assert "bad_claim" not in rgb.green


def test_filtered_ind_object():
    valid_sequence = [set(range(i)) for i in range(1, 6)]
    ind = FilteredIndObject(valid_sequence)
    assert ind.verify_finite_filtration() is True

    # Non-nested violates inclusion
    invalid_sequence = [{1, 2}, {3, 4}]
    ind_bad = FilteredIndObject(invalid_sequence)
    assert ind_bad.verify_finite_filtration() is False


def test_dialect_projection():
    assert DialectProjection.verify_non_empty() is True
    assert DialectProjection.get_projection("Diff") == "Spencer-Brown Distinction"
    assert DialectProjection.get_projection("Carrier") == "Finite Ground Set"


def test_discrete_hodge():
    assert DiscreteHodge.verify_dimension_sum(1, 1, 1, 3) is True
    assert DiscreteHodge.verify_dimension_sum(2, 2, 1, 5) is True
    assert DiscreteHodge.verify_dimension_sum(1, 1, 1, 4) is False


def test_hashimoto_graph():
    hg = HashimotoGraph(num_vertices=4, num_undirected_edges=6)
    assert hg.num_directed_edges == 12


def test_autopoietic_audit():
    state = {"rule_count": 25, "active": True}
    receipt = AutopoieticAudit.reflect_audit(state)
    assert receipt["status"] == "AUDIT_PASS"
    assert receipt["inspected_rules"] == 25
    assert state["rule_count"] == 25  # Zero mutation
