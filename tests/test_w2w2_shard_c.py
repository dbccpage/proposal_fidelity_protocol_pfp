"""
Executable verification for Window 2 Wave 2 Shard C Derivations (Note 003).

Derivations verified:
- AUDIT-N003-008: C3 worked replay (ATL-N003-008)
- AUDIT-N003-010: Local constructibility does not determine acceptance (ATL-N003-010)
- AUDIT-N003-011: Context replacement invariance (ATL-N003-011)
- AUDIT-N003-015: Context coordinate does not create a factor, preserving RHT-C05 (ATL-N003-015)

AuthorityEffect: None.
"""

import sys
from fractions import Fraction
from pathlib import Path

import pytest

# Ensure access to the archive module without modifying original sources
REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_MODULE_DIR = REPO_ROOT / "atlas/archive/non_pfp/003_degree_wise_dsl/code"
if str(ARCHIVE_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_MODULE_DIR))

from mod_009_degree_wise_dsl_core import (  # noqa: E402
    CompositeGateState,
    DegreeWiseDSLState,
    Gamma2Status,
    MissingComplex2Error,
    context_obstruction_witness,
    create_c3_complex,
)

# ============================================================================
# AUDIT-N003-008: C3 Worked Replay (ATL-N003-008)
# ============================================================================


def test_audit_n003_008_worked_replay_c3_with_and_without_two_cell_positive() -> None:
    """Evaluate C3 worked replay with and without 2-cell attached.

    Verifies:
    1. Phi_1 = 1 regardless of 2-cell attachment.
    2. Gamma_2 is undefined without 2-cell (NO_COMPLEX2 status, value is None).
    3. Gamma_2 = 1 when 2-cell is attached, giving closure ratio R_cl = 1.
    """
    omega = (Fraction(1, 1), Fraction(0, 1), Fraction(0, 1))

    # Configuration without 2-cell
    c_no_cell = create_c3_complex(with_two_cell=False)
    phi1_no_cell = c_no_cell.compute_phi1(omega)
    gamma2_no_cell = c_no_cell.compute_gamma2(omega)

    assert phi1_no_cell == Fraction(1, 1)
    assert gamma2_no_cell.status == Gamma2Status.NO_COMPLEX2
    assert gamma2_no_cell.value is None

    # Configuration with 2-cell
    c_with_cell = create_c3_complex(with_two_cell=True)
    phi1_with_cell = c_with_cell.compute_phi1(omega)
    gamma2_with_cell = c_with_cell.compute_gamma2(omega)

    assert phi1_with_cell == Fraction(1, 1)
    assert gamma2_with_cell.status == Gamma2Status.DEFINED
    assert gamma2_with_cell.value == Fraction(1, 1)

    # Closure ratio R_cl = Gamma_2 / Phi_1
    r_cl = gamma2_with_cell.value / phi1_with_cell
    assert r_cl == Fraction(1, 1)


def test_audit_n003_008_negative_control_phi1_invariant_to_two_cell() -> None:
    """Negative control: Phi_1 carries zero information about 2-cell existence.

    Attaching or removing a 2-cell leaves the 1-skeleton coboundary d0 unchanged,
    so Phi_1 is strictly equal across both configurations for all test cochains.
    Direct d1 evaluation on the 1-graph must raise MissingComplex2Error.
    """
    c_no_cell = create_c3_complex(with_two_cell=False)
    c_with_cell = create_c3_complex(with_two_cell=True)

    test_cochains = [
        (Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        (Fraction(2, 1), Fraction(1, 1), Fraction(0, 1)),
        (Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
        (Fraction(-1, 1), Fraction(1, 1), Fraction(0, 1)),
    ]

    for cochain in test_cochains:
        assert c_no_cell.compute_phi1(cochain) == c_with_cell.compute_phi1(cochain)

    # Calling d1 on complex lacking 2-cells must fail with typed error
    with pytest.raises(MissingComplex2Error):
        c_no_cell.d1((Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)))


# ============================================================================
# AUDIT-N003-010: Local Constructibility Does Not Determine Acceptance (ATL-N003-010)
# ============================================================================


def test_audit_n003_010_local_constructible_not_acceptance_positive() -> None:
    """Positive witness: identical local data maps to distinct acceptance authority.

    State A and State B have identical local fingerprints ((1, 0, 0), True),
    but differ in eval gating:
    - State A (eval_authorized = False) yields acceptanceAuthorized = False.
    - State B (eval_authorized = True) yields acceptanceAuthorized = True.
    By fiber constancy, acceptance authority does not factor through local constructibility.
    """
    state_a = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
    )
    state_b = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
    )

    # Local fingerprints are identical
    fp_a = state_a.local_fingerprint()
    fp_b = state_b.local_fingerprint()
    assert fp_a == fp_b == ((Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)), True)

    # Global gated readouts differ under eval gating
    gamma2_a, auth_a = state_a.global_gated_readout(eval_authorized=False)
    gamma2_b, auth_b = state_b.global_gated_readout(eval_authorized=True)

    assert gamma2_a == Fraction(1, 1)
    assert auth_a is False
    assert gamma2_b == Fraction(1, 1)
    assert auth_b is True

    # Functional non-factorization witness:
    # fp_a == fp_b but (gamma2_a, auth_a) != (gamma2_b, auth_b)
    assert (gamma2_a, auth_a) != (gamma2_b, auth_b)


def test_audit_n003_010_negative_control_unauthorized_acceptance_rejection() -> None:
    """Negative control: eval_authorized = False strictly rejects acceptance.

    Tests that regardless of non-zero curvature Gamma_2, acceptance authority
    cannot be granted without explicit eval authorization.
    """
    state = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(3, 1), Fraction(2, 1), Fraction(1, 1)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
    )

    gamma2_val, auth = state.global_gated_readout(eval_authorized=False)
    assert gamma2_val == Fraction(6, 1)
    assert auth is False

    # Also check complex lacking 2-cells: eval_authorized=True cannot accept when Gamma_2 is None
    missing_two_cell_state = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=False,
    )
    gamma2_none, auth_none = missing_two_cell_state.global_gated_readout(eval_authorized=True)
    assert gamma2_none is None
    assert auth_none is False


# ============================================================================
# AUDIT-N003-011: Context Replacement Invariance (ATL-N003-011)
# ============================================================================


def test_audit_n003_011_context_replacement_invariance_positive() -> None:
    """Positive test: replacing opaque context metadata preserves fingerprint and readout.

    State 1 and State 2 differ only in context_metadata. Both the local fingerprint
    and the global gated readout are strictly identical.
    """
    state_1 = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
        context_metadata={"token": "alpha", "session": 101, "weight": 42},
    )
    state_2 = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
        context_metadata={"token": "beta", "session": 999, "extra_flag": True},
    )

    assert state_1.local_fingerprint() == state_2.local_fingerprint()
    assert state_1.global_gated_readout(eval_authorized=True) == state_2.global_gated_readout(eval_authorized=True)
    assert state_1.global_gated_readout(eval_authorized=False) == state_2.global_gated_readout(eval_authorized=False)


def test_audit_n003_011_context_cannot_create_gamma2_on_graph_positive() -> None:
    """Positive test: context metadata cannot synthesize a Gamma_2 readout on a 1-graph.

    On a complex with has_two_cell=False, injecting context metadata (e.g. q_admission debt)
    does not create a Gamma_2 value; Gamma_2 remains None.
    """
    graph_state = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=False,
        context_metadata={"q_admission": "debt", "synthesize_gamma2": True},
    )

    gamma2_val, auth = graph_state.global_gated_readout(eval_authorized=True)
    assert gamma2_val is None
    assert auth is False


def test_audit_n003_011_negative_control_structural_mutation_changes_fingerprint() -> None:
    """Negative control: mutating structural cochain data alters local fingerprint.

    While metadata replacement preserves fingerprints, structural cochain mutations
    are reliably detected.
    """
    shared_metadata = {"immutable_key": "constant_val"}
    base_state = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
        context_metadata=shared_metadata,
    )
    mutated_state = DegreeWiseDSLState(
        carrier_name="C3",
        edge_cochain=(Fraction(2, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        two_cell_incidence=((1, 1, 1),),
        context_metadata=shared_metadata,
    )

    assert base_state.local_fingerprint() != mutated_state.local_fingerprint()


# ============================================================================
# AUDIT-N003-015: Context Coordinate Does Not Create a Factor (ATL-N003-015)
# Preserves Lineage: RHT-C05
# ============================================================================


def test_audit_n003_015_context_extension_blocks_factor_positive() -> None:
    """Positive test: shared context extension preserves non-factorization witness.

    Extends RHT-C05 quotient descent obstruction to shared context product spaces.
    Evaluates context_obstruction_witness on base states and context-extended states.
    """
    left = CompositeGateState(
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=False,
        diagnostic_constructible=True,
        has_eval=False,
        acceptance_authorized_raw=False,
        context=(),
    )
    right = CompositeGateState(
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        diagnostic_constructible=True,
        has_eval=True,
        acceptance_authorized_raw=True,
        context=(),
    )

    # Base witness verification
    base_witness = context_obstruction_witness(left, right)
    assert left.global_gate() == (None, False)
    assert right.global_gate() == (Fraction(1, 1), True)
    assert base_witness["local_equal"] is True
    assert base_witness["global_equal"] is False
    assert base_witness["context_inert"] is True
    assert base_witness["blocks_factor"] is True

    # Extend with arbitrary shared context coordinate
    shared_context = {"tag": "external_context_coord_42", "depth": 7}
    left_ext = left.replace_context(shared_context)
    right_ext = right.replace_context(shared_context)

    extended_witness = context_obstruction_witness(left_ext, right_ext)
    assert extended_witness["local_equal"] is True
    assert extended_witness["global_equal"] is False
    assert extended_witness["context_inert"] is True
    assert extended_witness["blocks_factor"] is True


def test_audit_n003_015_identity_control_negative() -> None:
    """Negative control: identical states on same fiber do not block factorization.

    When left == right, global readouts match (global_equal = True), so blocks_factor
    evaluates to False.
    """
    state = CompositeGateState(
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        diagnostic_constructible=True,
        has_eval=True,
        acceptance_authorized_raw=True,
        context="ctx_token_99",
    )

    witness = context_obstruction_witness(state, state)
    assert witness["local_equal"] is True
    assert witness["global_equal"] is True
    assert witness["blocks_factor"] is False


def test_audit_n003_015_differing_local_fingerprint_negative() -> None:
    """Negative control: differing local fingerprints do not block factorization.

    Fiber constancy blocks factorization only when states reside on the same fiber
    (local_equal = True). When local fingerprints differ, blocks_factor is False.
    """
    left = CompositeGateState(
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        diagnostic_constructible=True,
        has_eval=True,
        acceptance_authorized_raw=True,
    )
    right = CompositeGateState(
        edge_cochain=(Fraction(2, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        diagnostic_constructible=True,
        has_eval=False,
        acceptance_authorized_raw=False,
    )

    witness = context_obstruction_witness(left, right)
    assert witness["local_equal"] is False
    assert witness["blocks_factor"] is False


def test_audit_n003_015_preserves_rht_c05_lineage_contract() -> None:
    """Lineage preservation test: confirms RHT-C05 fiber-constancy quotient contract.

    RHT-C05 establishes that descent of an observable to a quotient requires
    constancy on fibers. We verify that attaching an arbitrary shared context coordinate
    c preserves this fiber non-constancy condition.
    """
    # Base states on carrier C3
    x1 = CompositeGateState(
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=False,
        diagnostic_constructible=True,
        has_eval=False,
        acceptance_authorized_raw=False,
    )
    x2 = CompositeGateState(
        edge_cochain=(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
        has_two_cell=True,
        diagnostic_constructible=True,
        has_eval=True,
        acceptance_authorized_raw=True,
    )

    # Lineage check: x1 and x2 are on the same local fiber
    assert x1.local_fingerprint() == x2.local_fingerprint()
    # But differ in global readout
    assert x1.global_gate() != x2.global_gate()

    # For multiple distinct shared context coordinates, fiber constancy remains violated
    context_samples = [None, 0, 42, "omega", ("structured", "context", 123)]
    for ctx in context_samples:
        x1_ctx = x1.replace_context(ctx)
        x2_ctx = x2.replace_context(ctx)

        witness = context_obstruction_witness(x1_ctx, x2_ctx)
        assert witness["local_equal"] is True
        assert witness["global_equal"] is False
        assert witness["blocks_factor"] is True
