"""Unit tests for CODA-CS-Q Engine Façade and Re-exported Procedures.

Validates that coda_cs_q_engine serves as a clean backwards-compatible façade
over coda_cs_q_bridge_core, verifying re-exports, aliases, helper entry points,
and core mathematical workflows.

AuthorityEffect: None.
"""

from __future__ import annotations

import math

import pytest
from coda_cs_q_engine import (
    BRIDGE_ADMISSIBLE_8_STEPS,
    BRIDGE_PACKET_14_SCHEMA_FIELDS,
    BridgePacket14Tuple,
    BridgePacketCore,
    BridgeResidualTaxonomy,
    CofinalShadowTower,
    GeneratorSemigroupAdapter,
    HigherQueryFamily,
    NamedTerminalizers,
    ProfileFactorizationSolver,
    ProfileFiberQuotient,
    QueryProbe,
    ShadowNode,
    run_coda_cs_q_bridge_demo,
    run_engine_selfcheck,
    run_gttc_q_bridge_demo,
    terminals_agree,
)


def test_engine_reexports_and_constants() -> None:
    """Verify that expected schema constants and aliases are present."""
    assert len(BRIDGE_ADMISSIBLE_8_STEPS) == 8
    assert len(BRIDGE_PACKET_14_SCHEMA_FIELDS) == 14
    assert BridgePacket14Tuple is BridgePacketCore
    assert run_gttc_q_bridge_demo is run_coda_cs_q_bridge_demo


def test_tower_and_profile_facade() -> None:
    """Test tower construction and profile evaluation through engine exports."""
    nodes: list[ShadowNode[int]] = [ShadowNode("lambda_0", 1), ShadowNode("lambda_1", 2)]
    projectors = {
        "lambda_0": lambda x: x % 3,
        "lambda_1": lambda x: x % 5,
    }
    transitions = {
        ("lambda_1", "lambda_0"): lambda a1: a1 % 3,
    }
    tower = CofinalShadowTower(nodes, projectors, transitions)
    prof_15 = tower.evaluate_profile(15)
    assert prof_15 == (0, 0)
    assert tower.verify_tower_coherence(15) is True


def test_engine_factorization_equivalence_success() -> None:
    """CSQ-T1 factor exists if and only if query is fibre constant."""
    nodes: list[ShadowNode[int]] = [ShadowNode("l0", 1)]
    projectors = {"l0": lambda x: x % 4}
    tower = CofinalShadowTower(nodes, projectors, {})
    domain = list(range(16))
    query: QueryProbe[int, int] = QueryProbe("q_sq", 1, lambda x: (x % 4) ** 2)

    solver = ProfileFactorizationSolver(tower, query, domain)
    success, q_bar, err = solver.solve_factorization()
    assert success is True
    assert err is None
    assert q_bar is not None
    assert query.evaluate(5) == 1
    assert q_bar((1,)) == 1


def test_engine_factorization_equivalence_counterexample() -> None:
    """CSQ-T1 non-fibre constant query refuses factor and exhibits violation."""
    nodes: list[ShadowNode[int]] = [ShadowNode("l0", 1)]
    projectors = {"l0": lambda x: x % 4}
    tower = CofinalShadowTower(nodes, projectors, {})
    domain = list(range(16))
    query: QueryProbe[int, int] = QueryProbe("q_identity", 1, lambda x: x)

    solver = ProfileFactorizationSolver(tower, query, domain)
    success, q_bar, err = solver.solve_factorization()
    assert success is False
    assert q_bar is None
    assert err is not None
    assert "Fiber constancy violation" in err


def test_engine_8_step_admission() -> None:
    """Audit 8-step admission procedure through engine façade."""
    nodes: list[ShadowNode[int]] = [ShadowNode("l0", 1)]
    projectors = {"l0": lambda x: x % 2}
    tower = CofinalShadowTower(nodes, projectors, {})
    domain = [0, 1, 2, 3]
    query: QueryProbe[int, bool] = QueryProbe("q_even", 1, lambda x: (x % 2) == 0)

    packet = BridgePacketCore(
        packet_id="B_q_test_facade_001",
        tower=tower,
        domain=domain,
        query=query,
    )
    audit = packet.audit_8_step_admission()
    assert audit["is_admissible"] is True
    assert audit["status"] == "BOUNDED_EVALUATION_SCOPE"
    assert audit["steps"]["5_profile_factorization"] is True
    assert audit["steps"]["8_terminal_conservativity"] is True
    assert audit["step8_status"] == "FINITE_DOMAIN_QUERY_VIA_QBAR_PROF"


def test_engine_terminal_conservativity_open_when_factorization_fails() -> None:
    """When factorization fails and no named terminals are provided, step 8 is OPEN."""
    nodes: list[ShadowNode[int]] = [ShadowNode("l0", 1)]
    projectors = {"l0": lambda x: x % 4}
    tower = CofinalShadowTower(nodes, projectors, {})
    domain = list(range(16))
    query: QueryProbe[int, int] = QueryProbe("q_identity", 1, lambda x: x)
    packet = BridgePacketCore(
        packet_id="B_q_open_facade",
        tower=tower,
        domain=domain,
        query=query,
    )
    audit = packet.audit_8_step_admission()
    assert audit["steps"]["5_profile_factorization"] is False
    assert audit["steps"]["8_terminal_conservativity"] is False
    assert audit["step8_status"] == "OPEN_NOT_IMPLEMENTED"
    assert "Not derived from step5" in (audit["step8_detail"] or "")


def test_engine_step8_not_silently_step5_and_step2() -> None:
    """step8 is not step5 ∧ step2 when tower is incoherent but factorization holds."""
    nodes: list[ShadowNode[int]] = [ShadowNode("l0", 1), ShadowNode("l1", 2)]
    projectors = {
        "l0": lambda x: x % 2,
        "l1": lambda x: x % 2,
    }
    transitions = {("l1", "l0"): lambda a1: (a1 + 1) % 2}
    tower = CofinalShadowTower(nodes, projectors, transitions)
    domain = [0, 1, 2, 3]
    query: QueryProbe[int, int] = QueryProbe("q_parity", 1, lambda x: x % 2)
    packet = BridgePacketCore(
        packet_id="B_q_step8_facade_indep",
        tower=tower,
        domain=domain,
        query=query,
    )
    audit = packet.audit_8_step_admission()
    step2 = audit["steps"]["2_tower_coherence"]
    step5 = audit["steps"]["5_profile_factorization"]
    step8 = audit["steps"]["8_terminal_conservativity"]
    assert step2 is False
    assert step5 is True
    assert step8 is True
    assert step8 != (step5 and step2)
    assert audit["step8_status"] == "FINITE_DOMAIN_QUERY_VIA_QBAR_PROF"


def test_engine_terminals_agree_helper() -> None:
    """Check terminals_agree helper with matching and mismatching functions."""
    domain = [0, 1, 2, 3]
    ok, detail = terminals_agree(domain, lambda x: x % 2, lambda x: x % 2)
    assert ok is True
    assert detail is None
    bad, detail_bad = terminals_agree(domain, lambda x: x, lambda x: x % 2)
    assert bad is False
    assert detail_bad is not None
    assert "Terminal mismatch" in detail_bad


def test_engine_named_terminalizers_agree_and_disagree() -> None:
    """Named terminalizers matching vs mismatching in engine packet audit."""
    nodes: list[ShadowNode[int]] = [ShadowNode("l0", 1)]
    projectors = {"l0": lambda x: x % 2}
    tower = CofinalShadowTower(nodes, projectors, {})
    domain = [0, 1, 2, 3]
    query: QueryProbe[int, int] = QueryProbe("q_parity", 1, lambda x: x % 2)

    # Agree
    named_ok: NamedTerminalizers[int, int] = NamedTerminalizers(
        tau_q=lambda x: x % 2,
        tau_coda_cs=lambda x: x % 2,
    )
    pkt_ok = BridgePacketCore(
        packet_id="B_ok",
        tower=tower,
        domain=domain,
        query=query,
        named_terminals=named_ok,
    )
    assert pkt_ok.audit_8_step_admission()["is_admissible"] is True

    # Disagree
    named_bad: NamedTerminalizers[int, int] = NamedTerminalizers(
        tau_q=lambda x: x % 2,
        tau_coda_cs=lambda x: 1 - (x % 2),
    )
    pkt_bad = BridgePacketCore(
        packet_id="B_bad",
        tower=tower,
        domain=domain,
        query=query,
        named_terminals=named_bad,
    )
    audit_bad = pkt_bad.audit_8_step_admission()
    assert audit_bad["is_admissible"] is False
    assert audit_bad["step8_status"] == "NAMED_TERMINALIZERS_DISAGREE"


def test_engine_generator_semigroups() -> None:
    """Test generator semigroup adapter methods."""
    def f(x: float) -> float:
        return x ** 2

    t_val = GeneratorSemigroupAdapter.translation_step(f, 3.0, 0.1)
    assert math.isclose(t_val, 9.61, rel_tol=1e-5)
    comp = GeneratorSemigroupAdapter.action_composition(1.5, 2.5)
    assert math.isclose(comp, 4.0)


def test_engine_residual_taxonomy() -> None:
    """Test 7-class residual taxonomy through engine export."""
    residuals = BridgeResidualTaxonomy.classify_residual(
        profile_factored=False,
        tower_coherent=True,
        terminal_conserved=False,
        authority_effect="None",
    )
    assert any("R_factor" in r for r in residuals)
    assert any("R_cons" in r for r in residuals)

    res_overclaim = BridgeResidualTaxonomy.classify_residual(
        profile_factored=True,
        tower_coherent=True,
        terminal_conserved=True,
        authority_effect="GlobalGreen",
    )
    assert any("R_overclaim" in r for r in res_overclaim)


def test_engine_fiber_quotient_and_higher_query_family() -> None:
    """Test quotient fibers and higher query families."""
    nodes: list[ShadowNode[int]] = [ShadowNode("l0", 1)]
    tower = CofinalShadowTower(nodes, {"l0": lambda x: x % 2}, {})
    domain = [0, 1, 2, 3]
    quot = ProfileFiberQuotient(tower, domain)
    assert quot.num_fibers() == 2

    q_parity: QueryProbe[int, int] = QueryProbe("parity", 1, lambda x: x % 2)
    q_id: QueryProbe[int, int] = QueryProbe("id", 1, lambda x: x)
    q_high: QueryProbe[int, int] = QueryProbe("high", 5, lambda x: x % 2)

    # Degree 5 exceeds bound 2 -> raises ValueError
    with pytest.raises(ValueError, match="exceeds family bound"):
        HigherQueryFamily(max_degree=2, queries=[q_parity, q_id, q_high])

    family_ok = HigherQueryFamily(max_degree=2, queries=[q_parity])
    all_const, failures = family_ok.verify_family_fiber_constancy(quot)
    assert all_const is True
    assert len(failures) == 0

    family_fail = HigherQueryFamily(max_degree=2, queries=[q_id])
    all_const_fail, failures_fail = family_fail.verify_family_fiber_constancy(quot)
    assert all_const_fail is False
    assert len(failures_fail) == 1


def test_engine_demo_and_selfcheck() -> None:
    """Test run_engine_selfcheck and run_coda_cs_q_bridge_demo."""
    assert run_engine_selfcheck() is True
    demo = run_coda_cs_q_bridge_demo()
    assert demo["is_admissible"] is True
    assert demo["is_cochain_exact"] is True
    assert demo["quotient_distance"] == 0

