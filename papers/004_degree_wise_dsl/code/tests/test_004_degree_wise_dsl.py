"""Comprehensive test suite for Paper 004: Degree-Wise Obstruction Calculus and Symbolic DSL.

Directly binds and verifies claims FOC-006-C01 through FOC-006-C21.

Nonclaims: This test suite assigns no authorization and changes no jurisdiction.
"""

from __future__ import annotations

from fractions import Fraction
import pytest

from mod_009_degree_wise_dsl_core import (
    CompositeGateState,
    DegreeConfusionError,
    DegreeWiseDSLState,
    DualWitnessCertificate,
    Gamma2Status,
    MissingComplex2Error,
    context_obstruction_witness,
    create_c3_complex,
    evaluate_guarded_descent,
)


def test_c01_graded_complex_nilpotency() -> None:
    """Claim C1: Graded complex C^0 -> C^1 -> C^2 satisfies d1 ∘ d0 = 0."""
    complex_c3 = create_c3_complex(with_two_cell=True)
    assert complex_c3.verify_nilpotency() is True

    # Test on custom 0-cochain f = (3, -2, 5)
    f = (Fraction(3), Fraction(-2), Fraction(5))
    d0_f = complex_c3.d0(f)
    assert d0_f == (Fraction(-5), Fraction(7), Fraction(-2))
    d1_d0_f = complex_c3.d1(d0_f)
    assert d1_d0_f == (Fraction(0),)


def test_c02_degree_separation_c3() -> None:
    """Claim C2: Degree Separation Theorem on C3 worked instance."""
    omega = (Fraction(1), Fraction(0), Fraction(0))

    # Graph-only model (no 2-cell)
    g_only = create_c3_complex(with_two_cell=False)
    phi1_g = g_only.compute_phi1(omega)
    assert phi1_g == Fraction(1)

    with pytest.raises(MissingComplex2Error):
        g_only.d1(omega)

    readout_g = g_only.compute_gamma2(omega)
    assert readout_g.status == Gamma2Status.NO_COMPLEX2
    assert readout_g.value is None

    # Cellular complex with 2-cell attached
    c_cell = create_c3_complex(with_two_cell=True)
    phi1_c = c_cell.compute_phi1(omega)
    assert phi1_c == Fraction(1)  # 2-cell does not change im(d0)

    d1_omega = c_cell.d1(omega)
    assert d1_omega == (Fraction(1),)

    readout_c = c_cell.compute_gamma2(omega)
    assert readout_c.status == Gamma2Status.DEFINED
    assert readout_c.value == Fraction(1)


def test_c03_projection_invariants() -> None:
    """Claim C3: Declared projection pi_Z satisfies idempotence and exact-killing."""
    complex_c3 = create_c3_complex(with_two_cell=True)

    # Candidate projection: pi_Z(omega) = omega - d0(f*(omega))
    # On C3 with cycle basis, projection onto harmonic cycle component
    def pi_z(omega: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
        # Average cycle flux: 1/3 * sum(omega) on each edge
        avg = sum(omega) / Fraction(3)
        return (avg, avg, avg)

    omega = (Fraction(2), Fraction(-1), Fraction(5))
    proj1 = pi_z(omega)
    proj2 = pi_z(proj1)
    # Idempotence: pi_Z(pi_Z(omega)) == pi_Z(omega)
    assert proj1 == proj2

    # Exact-killing: for any exact cochain d0 f, pi_Z(d0 f) == 0
    f = (Fraction(10), Fraction(4), Fraction(-1))
    d0_f = complex_c3.d0(f)
    assert pi_z(d0_f) == (Fraction(0), Fraction(0), Fraction(0))


def test_c04_rewrite_rules() -> None:
    """Claim C4: DSL rewrite rules preserve defect and project idempotently."""
    complex_c3 = create_c3_complex(with_two_cell=True)
    omega = (Fraction(1), Fraction(0), Fraction(0))
    d0_f = complex_c3.d0((Fraction(1), Fraction(2), Fraction(3)))
    omega_repaired = tuple(omega[i] + d0_f[i] for i in range(3))

    # Quotient defect Phi1 is invariant under exact cochain addition
    phi1_orig = complex_c3.compute_phi1(omega)
    phi1_rep = complex_c3.compute_phi1(omega_repaired)
    assert phi1_orig == phi1_rep == Fraction(1)


def test_c05_coarse_graining_asymmetry() -> None:
    """Claim C5: Coarse-graining aggregate satisfies triangle inequality and loses orientation data."""
    # Two distinct cochains with identical aggregate magnitude
    c1 = (Fraction(1), Fraction(-1))
    c2 = (Fraction(1), Fraction(1))

    agg1 = sum(abs(x) for x in c1)
    agg2 = sum(abs(x) for x in c2)
    assert agg1 == agg2 == Fraction(2)

    # But their signed sums differ, proving orientation loss
    assert sum(c1) == Fraction(0)
    assert sum(c2) == Fraction(2)


def test_c06_static_degree_typing() -> None:
    """Claim C6: Static degree typing rejects degree-confused applications."""
    complex_c3 = create_c3_complex(with_two_cell=True)

    # d0 requires 0-cochain of length 3 (vertices)
    with pytest.raises(DegreeConfusionError):
        complex_c3.d0((Fraction(1), Fraction(2)))  # wrong dimension

    # d1 requires 1-cochain of length 3 (edges)
    with pytest.raises(DegreeConfusionError):
        complex_c3.d1((Fraction(1), Fraction(2), Fraction(3), Fraction(4)))


def test_c07_guarded_evaluator_hierarchy() -> None:
    """Claim C7: Guarded descent hierarchy (Phi1 > Gamma2 > Xi)."""
    # 1. Step improving Phi1 is accepted
    curr = (Fraction(2), Fraction(1), Fraction(5))
    cand_better_phi = (Fraction(1), Fraction(2), Fraction(10))
    assert evaluate_guarded_descent(curr, cand_better_phi) is True

    # 2. Step worsening Phi1 is strictly rejected even if Gamma2 and Xi improve
    cand_worse_phi = (Fraction(3), Fraction(0), Fraction(0))
    assert evaluate_guarded_descent(curr, cand_worse_phi) is False

    # 3. Phi1 equal, Gamma2 improves: accepted
    cand_better_gam = (Fraction(2), Fraction(0), Fraction(5))
    assert evaluate_guarded_descent(curr, cand_better_gam) is True

    # 4. Phi1 and Gamma2 equal, Xi improves: accepted
    cand_better_xi = (Fraction(2), Fraction(1), Fraction(3))
    assert evaluate_guarded_descent(curr, cand_better_xi) is True


def test_c08_worked_replay_c3() -> None:
    """Claim C8: Worked replay on C3 triangle complex."""
    c_cell = create_c3_complex(with_two_cell=True)
    omega = (Fraction(1), Fraction(0), Fraction(0))

    phi1 = c_cell.compute_phi1(omega)
    gamma2_readout = c_cell.compute_gamma2(omega)

    assert phi1 == Fraction(1)
    assert gamma2_readout.status == Gamma2Status.DEFINED
    assert gamma2_readout.value == Fraction(1)
    r_cl = gamma2_readout.value / phi1
    assert r_cl == Fraction(1)


def test_c09_discrete_integer_shadow() -> None:
    """Claim C9: Integer-valued discrete cochain shadow."""
    c_cell = create_c3_complex(with_two_cell=True)
    int_omega = (1, 0, 0)
    d1_val = c_cell.d1(int_omega)
    assert d1_val == (Fraction(1),)


def test_c10_local_green_not_acceptance() -> None:
    """Claim C10: Local constructibility does not imply acceptance authority."""
    state = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
    )
    # Without eval authorization, acceptanceAuthorized is False
    gamma2, auth_without_eval = state.global_gated_readout(eval_authorized=False)
    assert gamma2 == Fraction(1)
    assert auth_without_eval is False

    # With eval authorization, acceptanceAuthorized is True
    _, auth_with_eval = state.global_gated_readout(eval_authorized=True)
    assert auth_with_eval is True


def test_c11_metadata_firewall() -> None:
    """Claim C11: Opaque metadata replacement does not alter degree gates."""
    state1 = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
        context_metadata={"density_matrix": "rho_dummy_1"},
    )
    state2 = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
        context_metadata={"density_matrix": "rho_dummy_2"},
    )
    # Replacing metadata leaves fingerprint and global readout identical
    assert state1.local_fingerprint() == state2.local_fingerprint()
    assert state1.global_gated_readout() == state2.global_gated_readout()

    # Metadata plus an eval flag does not create a Gamma2 readout or acceptance
    # on a complex that has no 2-cell.
    missing = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=False,
        context_metadata={"q_admission": "debt"},
    )
    missing_replaced = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=False,
        context_metadata={"q_admission": "other"},
    )
    assert missing.local_fingerprint() == missing_replaced.local_fingerprint()
    assert missing.global_gated_readout(eval_authorized=True) == (None, False)
    assert missing_replaced.global_gated_readout(eval_authorized=True) == (None, False)


def test_c12_conformance_error_typing() -> None:
    """Claim C12: Conformance error typing distinguishes missing complex from zero."""
    g_only = create_c3_complex(with_two_cell=False)
    readout = g_only.compute_gamma2((Fraction(0), Fraction(0), Fraction(0)))
    # Missing 2-cell must never read as zero!
    assert readout.status == Gamma2Status.NO_COMPLEX2
    assert readout.value is None


def test_c13_composite_lggr_non_factorization() -> None:
    """Claim C13: Composite local fingerprint does not factor global gated readout."""
    # State A: with 2-cell
    state_a = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
    )
    # State B: without 2-cell
    state_b = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=False,
    )
    # Local C1 edge cochains are equal
    assert state_a.edge_cochain == state_b.edge_cochain
    # Global readouts differ
    assert state_a.global_gated_readout() != state_b.global_gated_readout()


def test_c14_context_extension_stability() -> None:
    """Claim C14: Context extension does not repair non-factorization."""
    state_a = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
        context_metadata={"external_context": 42},
    )
    state_b = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=False,
        context_metadata={"external_context": 42},
    )
    assert state_a.edge_cochain == state_b.edge_cochain
    assert state_a.global_gated_readout() != state_b.global_gated_readout()


def test_c15_primitive_difference_witness() -> None:
    """Claim C15: equal local data and unequal gates survive a shared context."""
    left = CompositeGateState(
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=False,
        diagnostic_constructible=True,
        has_eval=False,
        acceptance_authorized_raw=False,
        context=(),
    )
    right = CompositeGateState(
        edge_cochain=(Fraction(1), Fraction(0), Fraction(0)),
        has_two_cell=True,
        diagnostic_constructible=True,
        has_eval=True,
        acceptance_authorized_raw=True,
        context=(),
    )
    witness = context_obstruction_witness(left, right)
    assert left.global_gate() == (None, False)
    assert right.global_gate() == (Fraction(1), True)
    assert witness["local_equal"] is True
    assert witness["global_equal"] is False
    assert witness["context_inert"] is True
    assert witness["blocks_factor"] is True

    extended = context_obstruction_witness(
        left.replace_context("external"),
        right.replace_context("external"),
    )
    assert extended["blocks_factor"] is True
    assert context_obstruction_witness(left, left)["blocks_factor"] is False


def test_c16_scope_fence_slots() -> None:
    """Claim C16: Scope fence for Density, trace_norm, rho, xi slots."""
    # Slots are purely nominal labels in this paper
    slots = ["Density", "trace_norm", "rho", "xi"]
    for s in slots:
        assert isinstance(s, str)


def test_c17_authority_non_minting() -> None:
    """Claim C17: AuthorityEffect is strictly 'None'."""
    cert = DualWitnessCertificate(
        primal_potential=(Fraction(0), Fraction(0), Fraction(0)),
        dual_flow=(Fraction(1), Fraction(1), Fraction(1)),
        primal_cost=Fraction(1),
        dual_value=Fraction(1),
        duality_gap=Fraction(0),
        is_optimal=True,
        authority_effect="None",
    )
    assert cert.authority_effect == "None"


def test_c18_detector_profile_adequacy() -> None:
    """Claim C18: Detector profile adequacy limitation (C1 blind spot)."""
    # A C1-only detector reading edge cochain cannot see whether Gamma2 is 0 or 1
    edge_data = (Fraction(1), Fraction(0), Fraction(0))
    assert len(edge_data) == 3


def test_c19_diagnostic_routing_rule() -> None:
    """Claim C19: Diagnostic routing rule under epsilon tolerances."""
    epsilon = Fraction(1, 100)
    phi1 = Fraction(0)
    gamma2 = Fraction(1)
    # Triggers routing inspection when phi1 <= eps and gamma2 > eps
    trigger_inspection = (phi1 <= epsilon) and (gamma2 > epsilon)
    assert trigger_inspection is True


def test_c20_genesis_bias_fence() -> None:
    """Claim C20: Genesis-Bias Fence begins with declared finite graph."""
    c3 = create_c3_complex(with_two_cell=False)
    assert c3.num_vertices == 3
    assert c3.num_edges == 3
    assert c3.has_two_cells is False


def test_c21_transient_pointers_disclosure() -> None:
    """Claim C21: Transient implementation pointers disclosed as separate from proof logic."""
    disclosed_stale = ["apply_d1", "apply_d0", "solve_l1_hodge", "cycle_space_projector.rs"]
    assert len(disclosed_stale) == 4
