"""Unit tests for S(n) Tower Core Stages (Track 000).

AuthorityEffect: None.
"""

from __future__ import annotations

from omega_engine_pfp.domain.sn_tower.sn_core import (
    S0Ground,
    S1Supply,
    S2Collapse,
    S3Separation,
    S4Orbit,
    S5Continuation,
    S6Descent,
)


def test_s0_ground_inertia():
    s0 = S0Ground()
    assert s0.verify_inertia() is True
    assert s0.s_0 == 0
    assert len(s0.v_0) == 0
    assert len(s0.w_0_active) == 0


def test_s1_supply_subsingleton():
    s1 = S1Supply()
    assert s1.verify_subsingleton("a") is True
    assert s1.verify_subsingleton("b") is True
    assert s1.supply_mark("x") == {"x"}
    assert s1.s_1 == 1


def test_s2_collapse_permutation_action():
    s2 = S2Collapse()
    pair = ("alpha", "beta")
    assert s2.permute_pair(pair) == ("beta", "alpha")
    assert s2.verify_set_equivalence("a", "b") is True
    assert s2.s_2 == 1


def test_s3_separation_cost_floor():
    s3 = S3Separation()
    assert s3.verify_separation("a", "b") is True
    assert s3.verify_separation("a", "a") is False
    assert s3.coboundary_delta(0, 1) == 1
    assert s3.coboundary_delta(1, 0) == -1
    assert s3.cost_floor == 2
    assert s3.s_3 == 1


def test_s4_orbit_closure():
    s4 = S4Orbit()
    vertices = ["v0", "v1", "v2", "v3"]
    edges = s4.complete_edges(vertices)
    assert len(edges) == 6
    assert s4.verify_orbit_closure(vertices) is True
    assert s4.s_4 == 0


def test_s5_continuation_demand():
    s5 = S5Continuation()
    assert s5.verify_continuation_demand() is True
    assert s5.assert_endogenous_inertia({"m1", "m2"}) is True
    assert s5.s_5 == 1
    assert s5.ob_1_active is True


def test_s6_descent_identity_and_status():
    s6 = S6Descent(s_6=1, delta_n=2)
    assert s6.verify_retraction_identity([0, 1, 2, 5, 10]) is True
    assert s6.descent_status() == "NON_DESCENT"

    s6_closed = S6Descent(s_6=0, delta_n=0)
    assert s6_closed.descent_status() == "DESCENT"
