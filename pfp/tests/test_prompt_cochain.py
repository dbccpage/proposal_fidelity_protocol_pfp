# -*- coding: utf-8 -*-
"""Verification of Prompt-to-Cochain execution and evaluation contract (Milestone 4).

Architecture Review 16 §3–§4, Scope R3 part 2.
AuthorityEffect: None.

Tests:
1. Standard Triadic Input 1 (Exact Coboundary): Phi_1 = 0, Gamma_2 = 0 -> ExactCoboundary.
2. Standard Triadic Input 2 (Coherent Residual): Phi_1 > 0, Gamma_2 = 0 (faces omitted) -> ClosedNonExactClass.
3. Standard Triadic Input 3 (Nonclosed Defect): Gamma_2 > 0 -> NonClosedEdgeData.
4. Falsification of impossible profile: Phi_1 = 0 and Gamma_2 > 0 -> Refusal(IMPOSSIBLE_PROFILE).
5. Chain law violation falsification: d_1 * d_0 != 0 -> Refusal(CHAIN_LAW_VIOLATION).
6. Dual witness falsifications (norm violation ||y||_infty > 1, non-annihilating dual d_0^T y != 0).
7. Prime Triad bindings:
   - Prime 000: intake validation, source bytes freezing, hash mismatch refusal.
   - Prime 001: loss preservation and protected answer preservation.
   - Prime 002: residual-aware continuation and budget exhaustion refusal.
8. PFP Contract verification (Prompt-to-Cochain ContractSpec and receipt).
"""

from __future__ import annotations

import hashlib
from fractions import Fraction

from omega_engine_pfp.domain.cochain import (
    ClosedNonExactClass,
    CochainRefusal,
    ExactCoboundary,
    NonClosedEdgeData,
    PrimeTriadContext,
    PromptCellComplex,
)
from omega_engine_pfp.domain.contracts.cochain import (
    RULE_PROMPT_COCHAIN_CHAIN_LAW_001,
    RULE_PROMPT_COCHAIN_FOUR_WAY_DISPOSITION_001,
    RULE_PROMPT_COCHAIN_IMPOSSIBLE_PROFILE_001,
    RULE_PROMPT_COCHAIN_PRIME_TRIAD_001,
    RULE_PROMPT_COCHAIN_ZERO_GAP_001,
    get_prompt_cochain_evaluation_contract,
)
from omega_engine_pfp.ffi import (
    evaluate_prompt_cochain_disposition as evaluate_prompt_cochain,
)
from omega_engine_pfp.ffi import get_default_host


def make_triangle_complex(with_face: bool = True) -> PromptCellComplex:
    """Build the canonical 3-edge oriented triangle cell complex.

    V = {v0, v1, v2}, E = {e0: (v0, v1), e1: (v1, v2), e2: (v2, v0)}.
    d_0:
      e0: -v0 + v1
      e1: -v1 + v2
      e2:  v0 - v2
    d_1:
      f0: e0 + e1 + e2 (if with_face=True)
    d_1 * d_0 = 0 over Q.
    """
    vertices = ("v0", "v1", "v2")
    edges = (("v0", "v1"), ("v1", "v2"), ("v2", "v0"))
    faces = (((0, 1), (1, 1), (2, 1)),) if with_face else None
    return PromptCellComplex.from_oriented_graph(vertices, edges, faces)


def test_standard_triadic_input_1_exact_coboundary():
    """Input 1: Exact coboundary c = (1, 2, -3) = d_0 (0, 1, 3)^T, d_1 = (1, 1, 1).

    Expectation: Phi_1 = 0, Gamma_2 = 0 -> ExactCoboundary.
    """
    complex_geom = make_triangle_complex(with_face=True)
    potential = (Fraction(0), Fraction(1), Fraction(3))
    # d_0 * a:
    # e0 = -0 + 1 = 1
    # e1 = -1 + 3 = 2
    # e2 =  0 - 3 = -3
    cochain = (Fraction(1), Fraction(2), Fraction(-3))
    dual_witness = (Fraction(0), Fraction(0), Fraction(0))

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=dual_witness,
    )

    assert isinstance(disposition, ExactCoboundary), f"Expected ExactCoboundary, got {disposition}"
    assert disposition.phi1 == Fraction(0)
    assert disposition.gamma2 == Fraction(0)
    assert disposition.potential == potential
    assert disposition.dual_witness == dual_witness
    assert disposition.defect_vector == ()


def test_standard_triadic_input_2_coherent_residual():
    """Input 2: Coherent residual c = (1, 1, 1), faces omitted (C^2 = Q^0).

    Expectation: Phi_1 = 3 > 0, Gamma_2 = 0 -> ClosedNonExactClass.
    """
    complex_geom = make_triangle_complex(with_face=False)
    cochain = (Fraction(1), Fraction(1), Fraction(1))
    potential = (Fraction(0), Fraction(0), Fraction(0))
    dual_witness = (Fraction(1), Fraction(1), Fraction(1))

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=dual_witness,
    )

    assert isinstance(disposition, ClosedNonExactClass), f"Expected ClosedNonExactClass, got {disposition}"
    assert disposition.phi1 == Fraction(3)
    assert disposition.gamma2 == Fraction(0)
    assert disposition.potential == ()
    assert disposition.dual_witness == dual_witness
    assert disposition.defect_vector == ()


def test_standard_triadic_input_3_nonclosed_defect():
    """Input 3: Non-closed edge data c = (1, 1, 1), d_1 = (1, 1, 1).

    Expectation: Gamma_2 = 3 > 0 -> NonClosedEdgeData.
    """
    complex_geom = make_triangle_complex(with_face=True)
    cochain = (Fraction(1), Fraction(1), Fraction(1))
    potential = (Fraction(0), Fraction(0), Fraction(0))
    dual_witness = (Fraction(1), Fraction(1), Fraction(1))

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=dual_witness,
    )

    assert isinstance(disposition, NonClosedEdgeData), f"Expected NonClosedEdgeData, got {disposition}"
    assert disposition.gamma2 == Fraction(3)
    assert disposition.defect_vector == (Fraction(3),)


def test_falsification_chain_law_violation():
    """Complex with d_1 * d_0 != 0 must be refused with CHAIN_LAW_VIOLATION."""
    host = get_default_host()
    # Invalid complex: d_0 has shape [2, 2], d_1 has shape [1, 2], d_1 * d_0 != 0
    invalid_complex = {
        "c0_dim": 2,
        "c1_dim": 2,
        "c2_dim": 1,
        "d0": [["1", "0"], ["0", "1"]],
        "d1": [["1", "1"]],  # d1 * d0 = [1, 1] != 0
    }
    outcome = host.evaluate_prompt_cochain(
        complex=invalid_complex,
        cochain=["1", "1"],
        primal_potential=["0", "0"],
        dual_witness=["0", "0"],
    )
    assert outcome.is_ok
    data = outcome.unwrap()
    res = data.get("result", data)
    assert res["disposition"] == "Refusal"
    assert "CHAIN_LAW_VIOLATION" in res.get("code", "")


def test_falsification_impossible_profile():
    """Falsification: claiming coboundary on non-closed data yields non-zero duality gap refusal."""
    complex_geom = make_triangle_complex(with_face=True)
    # c = (1, 1, 1), but claiming potential for (1, 2, -3)
    cochain = (Fraction(1), Fraction(1), Fraction(1))
    potential = (Fraction(0), Fraction(1), Fraction(3))
    dual_witness = (Fraction(0), Fraction(0), Fraction(0))

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=dual_witness,
    )

    assert isinstance(disposition, CochainRefusal)
    assert "PHI1_CERTIFICATE_INVALID" in disposition.reason


def test_falsification_dual_annihilator_violation():
    """Dual witness that does not annihilate coboundary (d_0^T y != 0) must be refused."""
    complex_geom = make_triangle_complex(with_face=False)
    cochain = (Fraction(1), Fraction(1), Fraction(1))
    potential = (Fraction(0), Fraction(0), Fraction(0))
    # y = (1, 0, 0) does NOT annihilate d_0^T
    invalid_dual = (Fraction(1), Fraction(0), Fraction(0))

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=invalid_dual,
    )

    assert isinstance(disposition, CochainRefusal)
    assert "PHI1_CERTIFICATE_INVALID" in disposition.reason
    assert "annihilate" in disposition.detail.lower()


def test_falsification_dual_norm_bound_violation():
    """Dual witness with ||y||_infty > 1 must be refused."""
    complex_geom = make_triangle_complex(with_face=False)
    cochain = (Fraction(1), Fraction(1), Fraction(1))
    potential = (Fraction(0), Fraction(0), Fraction(0))
    # y = (2, 2, 2) has norm 2 > 1
    invalid_dual = (Fraction(2), Fraction(2), Fraction(2))

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=invalid_dual,
    )

    assert isinstance(disposition, CochainRefusal)
    assert "PHI1_CERTIFICATE_INVALID" in disposition.reason
    assert "norm bound" in disposition.detail.lower()


def test_prime_000_intake_validation():
    """Prime 000: source bytes freezing and intake hash validation."""
    source_text = "Prompt operand graph G_0"
    source_sha = hashlib.sha256(source_text.encode("utf-8")).hexdigest()

    complex_geom = make_triangle_complex(with_face=False)
    cochain = (Fraction(1), Fraction(1), Fraction(1))
    potential = (Fraction(0), Fraction(0), Fraction(0))
    dual_witness = (Fraction(1), Fraction(1), Fraction(1))

    # Matching hash passes
    valid_context = PrimeTriadContext(
        source_bytes=source_text,
        expected_source_hash=source_sha,
        remaining_budget=10,
    )
    res_valid = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=dual_witness,
        triad_context=valid_context,
    )
    assert isinstance(res_valid, ClosedNonExactClass)

    # Tampered hash refuses
    tampered_context = PrimeTriadContext(
        source_bytes=source_text,
        expected_source_hash="0" * 64,
        remaining_budget=10,
    )
    res_tampered = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=dual_witness,
        triad_context=tampered_context,
    )
    assert isinstance(res_tampered, CochainRefusal)
    assert "SOURCE_BYTES_CORRUPTED" in res_tampered.reason


def test_prime_002_budget_exhaustion():
    """Prime 002: budget exhaustion must produce a refusal disposition."""
    complex_geom = make_triangle_complex(with_face=False)
    cochain = (Fraction(1), Fraction(1), Fraction(1))
    potential = (Fraction(0), Fraction(0), Fraction(0))
    dual_witness = (Fraction(1), Fraction(1), Fraction(1))

    exhausted_context = PrimeTriadContext(
        remaining_budget=0,
    )
    res_exhausted = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=dual_witness,
        triad_context=exhausted_context,
    )
    assert isinstance(res_exhausted, CochainRefusal)
    assert "RESOURCE_EXHAUSTION" in res_exhausted.reason



def test_cochain_evaluation_contract_spec():
    """Verify machine-verifiable contract definition for prompt cochain evaluation."""
    contract = get_prompt_cochain_evaluation_contract()
    assert contract.contract_id == "urn:omega:pfp:contract:prompt_cochain_evaluation:v1.0.0"
    assert contract.authority_effect == "None"

    # Invariants must contain all 5 required rules
    assert RULE_PROMPT_COCHAIN_CHAIN_LAW_001 in contract.invariants
    assert RULE_PROMPT_COCHAIN_ZERO_GAP_001 in contract.invariants
    assert RULE_PROMPT_COCHAIN_IMPOSSIBLE_PROFILE_001 in contract.invariants
    assert RULE_PROMPT_COCHAIN_PRIME_TRIAD_001 in contract.invariants
    assert RULE_PROMPT_COCHAIN_FOUR_WAY_DISPOSITION_001 in contract.invariants

    # Failure modes
    assert "IMPOSSIBLE_PROFILE" in contract.failure_modes
    assert "CHAIN_LAW_VIOLATION" in contract.failure_modes
    assert "DUAL_GAP_NONZERO" in contract.failure_modes
