"""Adversarial stress tests for Milestone 4: Prompt-to-Cochain Execution Contract.

Written by Challenger (teamwork_preview_challenger_m4_1) to empirically verify:
1. Non-nilpotent boundary complexes (d_1 * d_0 != 0) fail-closed with CHAIN_LAW_VIOLATION.
2. Dual witness violations:
   - ||y||_infty > 1 (including marginal excess 1 + 10^-50)
   - d_0^T y != 0 (including infinitesimal residual 10^-50)
   - Non-zero duality gap (slack or invalid dual witness)
3. Impossible profile defense: Phi_1 = 0 on non-closed data (Gamma_2 > 0) strictly refused.
4. Large fractions and high-precision BigRational arithmetic (100+ digit numerators/denominators).
5. Prime Triad bindings:
   - Prime 000: Corrupted source bytes, hash mismatches, multibyte UTF-8 source custody.
   - Prime 002: Zero budget, decremented budget exhaustion.
6. Zero-float & non-coercion invariants across FFI wire and Rust exact.rs.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from fractions import Fraction

from pfp.domain.cochain import (
    ClosedNonExactClass,
    CochainRefusal,
    ExactCoboundary,
    PrimeTriadContext,
    PromptCellComplex,
)
from pfp.ffi import (
    evaluate_prompt_cochain_disposition as evaluate_prompt_cochain,
)
from pfp.ffi import get_default_host


# =============================================================================
# Helper: Canonical 3-edge oriented triangle
# =============================================================================
def make_triangle_complex(with_face: bool = True) -> PromptCellComplex:
    vertices = ("v0", "v1", "v2")
    edges = (("v0", "v1"), ("v1", "v2"), ("v2", "v0"))
    faces = (((0, 1), (1, 1), (2, 1)),) if with_face else None
    return PromptCellComplex.from_oriented_graph(vertices, edges, faces)


# =============================================================================
# 1. NON-NILPOTENT BOUNDARY COMPLEXES (d_1 * d_0 != 0)
# =============================================================================
def test_adversarial_non_nilpotent_1x1():
    """Adversarial minimal non-nilpotent complex: d0=[[1]], d1=[[1]] -> d1*d0 = [[1]] != 0."""
    host = get_default_host()
    invalid_complex = {
        "c0_dim": 1,
        "c1_dim": 1,
        "c2_dim": 1,
        "d0": [["1"]],
        "d1": [["1"]],
    }
    outcome = host.evaluate_prompt_cochain(
        complex=invalid_complex,
        cochain=["1"],
        primal_potential=["0"],
        dual_witness=["0"],
    )
    assert outcome.is_ok
    data = outcome.unwrap()
    res = data.get("result", data)
    assert res["disposition"] == "Refusal"
    assert "CHAIN_LAW_VIOLATION" in res.get("code", "")


def test_adversarial_non_nilpotent_high_dimension():
    """Adversarial 4-vertex, 4-edge, 2-face complex with mismatched cycle signs."""
    host = get_default_host()
    # Cycle 0: e0 + e1 + e2 (valid boundary for triangle 0-1-2)
    # Cycle 1: e2 + e3 (not a cycle: d1 * d0 != 0)
    invalid_complex = {
        "c0_dim": 4,
        "c1_dim": 4,
        "c2_dim": 2,
        "d0": [
            ["-1", "1", "0", "0"],
            ["0", "-1", "1", "0"],
            ["1", "0", "-1", "0"],
            ["0", "0", "-1", "1"],
        ],
        "d1": [
            ["1", "1", "1", "0"],   # (d1 d0)_0 = [0, 0, 0, 0]
            ["0", "0", "1", "1"],   # (d1 d0)_1 = [1, 0, -2, 1] != 0
        ],
    }
    outcome = host.evaluate_prompt_cochain(
        complex=invalid_complex,
        cochain=["1", "1", "1", "1"],
        primal_potential=["0", "0", "0", "0"],
        dual_witness=["0", "0", "0", "0"],
    )
    assert outcome.is_ok
    data = outcome.unwrap()
    res = data.get("result", data)
    assert res["disposition"] == "Refusal"
    assert "CHAIN_LAW_VIOLATION" in res.get("code", "")


# =============================================================================
# 2. DUAL WITNESS VIOLATIONS: ||y||_infty <= 1 AND d_0^T y == 0
# =============================================================================
def test_adversarial_dual_norm_marginal_excess():
    """Dual witness with infinitesimal norm violation: y_0 = 1 + 10^-50 > 1."""
    complex_geom = make_triangle_complex(with_face=False)
    cochain = (Fraction(1), Fraction(1), Fraction(1))
    potential = (Fraction(0), Fraction(0), Fraction(0))
    # y = (1 + 1/10^50, 1, 1 - 1/10^50)
    # d0^T y = [- (1 + 1/10^50) + (1 - 1/10^50), ...] != 0, AND ||y||_inf = 1 + 10^-50 > 1
    tiny = Fraction(1, 10**50)
    invalid_dual = (Fraction(1) + tiny, Fraction(1), Fraction(1))

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=invalid_dual,
    )
    assert isinstance(disposition, CochainRefusal)
    assert "PHI1_CERTIFICATE_INVALID" in disposition.reason


def test_adversarial_dual_annihilator_infinitesimal_residual():
    """Dual witness that violates d_0^T y == 0 by 10^-50 while keeping ||y||_infty <= 1."""
    complex_geom = make_triangle_complex(with_face=False)
    cochain = (Fraction(1), Fraction(1), Fraction(1))
    potential = (Fraction(0), Fraction(0), Fraction(0))
    # y = (1, 1, 1 - 1/10^50), so ||y||_inf = 1 <= 1, but d0^T y != 0
    tiny = Fraction(1, 10**50)
    invalid_dual = (Fraction(1), Fraction(1), Fraction(1) - tiny)

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=invalid_dual,
    )
    assert isinstance(disposition, CochainRefusal)
    assert "PHI1_CERTIFICATE_INVALID" in disposition.reason
    assert "annihilate" in disposition.detail.lower() or "d0^t y != 0" in disposition.detail.lower()


def test_adversarial_dual_slack_non_zero_duality_gap():
    """Dual witness satisfies d_0^T y == 0 and ||y||_inf <= 1, but y^T c < ||c - d_0 a||_1."""
    complex_geom = make_triangle_complex(with_face=False)
    cochain = (Fraction(1), Fraction(1), Fraction(1))  # ||c||_1 = 3
    potential = (Fraction(0), Fraction(0), Fraction(0))
    # y = (1/2, 1/2, 1/2):
    # d0^T y = [-1/2 + 1/2, -1/2 + 1/2, -1/2 + 1/2] = [0, 0, 0] (Annihilates!)
    # ||y||_inf = 1/2 <= 1 (Feasible!)
    # y^T c = 1/2 + 1/2 + 1/2 = 3/2 != 3 = ||c - d0 a||_1 (Duality gap = 3/2 > 0!)
    slack_dual = (Fraction(1, 2), Fraction(1, 2), Fraction(1, 2))

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=slack_dual,
    )
    assert isinstance(disposition, CochainRefusal)
    assert "PHI1_CERTIFICATE_INVALID" in disposition.reason
    assert "duality gap" in disposition.detail.lower()


# =============================================================================
# 3. IMPOSSIBLE PROFILES (Phi_1 = 0, Gamma_2 > 0)
# =============================================================================
def test_adversarial_impossible_profile_forged_potential():
    """Attempt to claim ExactCoboundary on a non-closed cochain (Gamma_2 > 0)."""
    complex_geom = make_triangle_complex(with_face=True)
    # Cochain with non-zero face defect: d1 c = 3 != 0 -> Gamma_2 = 3
    cochain = (Fraction(1), Fraction(1), Fraction(1))
    # Attempt 1: Forged potential a = (0, 1, 3) which generates (1, 2, -3) != (1, 1, 1)
    forged_a = (Fraction(0), Fraction(1), Fraction(3))
    # Attempt 1 with zero dual witness claiming Phi_1 = 0
    zero_dual = (Fraction(0), Fraction(0), Fraction(0))

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=forged_a,
        dual_witness=zero_dual,
    )
    # Must fail-closed: either PHI1_CERTIFICATE_INVALID or IMPOSSIBLE_PROFILE
    assert isinstance(disposition, CochainRefusal)
    assert disposition.reason in ("PHI1_CERTIFICATE_INVALID", "IMPOSSIBLE_PROFILE")


# =============================================================================
# 4. LARGE FRACTIONS AND HIGH-PRECISION BIGRATIONAL ARITHMETIC
# =============================================================================
def test_adversarial_large_fractions_100_digits():
    """Stress test with 100-digit integers to ensure zero 64-bit overflow."""
    # Build large coprime integers
    numer1 = 10**100 + 7
    denom1 = 10**100 + 31
    numer2 = 10**100 + 13
    denom2 = 10**100 + 47

    f1 = Fraction(numer1, denom1)
    f2 = Fraction(numer2, denom2)

    # 2-vertex, 1-edge complex
    # d0 = [[-1, 1]]
    # potential a = (f1, f1 + f2)
    # c = d0 a = f2
    # y = (0)
    complex_geom = PromptCellComplex(
        v_count=2,
        e_count=1,
        f_count=0,
        d0_matrix=((Fraction(-1), Fraction(1)),),
    )
    cochain = (f2,)
    potential = (f1, f1 + f2)
    dual_witness = (Fraction(0),)

    disposition = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=cochain,
        primal_potential=potential,
        dual_witness=dual_witness,
    )

    assert isinstance(disposition, ExactCoboundary)
    assert disposition.phi1 == Fraction(0)
    assert disposition.gamma2 == Fraction(0)
    assert disposition.potential == potential
    assert disposition.dual_witness == dual_witness


# =============================================================================
# 5. PRIME TRIAD BINDINGS: PRIME 000, PRIME 001, PRIME 002
# =============================================================================
def test_adversarial_prime_000_multibyte_utf8_source():
    """Prime 000: Multi-byte UTF-8 source string with unicode symbols."""
    unicode_source = "Prompt Graph: 𝒪(x) → 𝒫(y) ⊗ 𝒞(z) [λ = 42.0]"
    sha = hashlib.sha256(unicode_source.encode("utf-8")).hexdigest()

    complex_geom = make_triangle_complex(with_face=False)
    complex_geom = PromptCellComplex(
        v_count=complex_geom.v_count,
        e_count=complex_geom.e_count,
        f_count=complex_geom.f_count,
        d0_matrix=complex_geom.d0_matrix,
        d1_matrix=complex_geom.d1_matrix,
        source_bytes_hash=sha,
    )

    valid_context = PrimeTriadContext(
        source_bytes=unicode_source,
        expected_source_hash=sha,
        remaining_budget=5,
    )
    res_valid = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=(Fraction(1), Fraction(1), Fraction(1)),
        primal_potential=(Fraction(0), Fraction(0), Fraction(0)),
        dual_witness=(Fraction(1), Fraction(1), Fraction(1)),
        triad_context=valid_context,
    )
    assert isinstance(res_valid, ClosedNonExactClass)

    # 1 byte bit-flip in source text
    corrupted_source = unicode_source[:-1] + "!"
    corrupted_context = PrimeTriadContext(
        source_bytes=corrupted_source,
        expected_source_hash=sha,
        remaining_budget=5,
    )
    res_corrupted = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=(Fraction(1), Fraction(1), Fraction(1)),
        primal_potential=(Fraction(0), Fraction(0), Fraction(0)),
        dual_witness=(Fraction(1), Fraction(1), Fraction(1)),
        triad_context=corrupted_context,
    )
    assert isinstance(res_corrupted, CochainRefusal)
    assert "SOURCE_BYTES_CORRUPTED" in res_corrupted.reason


def test_adversarial_prime_002_zero_budget():
    """Prime 002: Exactly zero budget halts with RESOURCE_EXHAUSTION."""
    complex_geom = make_triangle_complex(with_face=False)
    context = PrimeTriadContext(remaining_budget=0)

    res = evaluate_prompt_cochain(
        complex=complex_geom,
        cochain=(Fraction(1), Fraction(1), Fraction(1)),
        primal_potential=(Fraction(0), Fraction(0), Fraction(0)),
        dual_witness=(Fraction(1), Fraction(1), Fraction(1)),
        triad_context=context,
    )
    assert isinstance(res, CochainRefusal)
    assert "RESOURCE_EXHAUSTION" in res.reason


# =============================================================================
# 6. FFI WIRE ZERO-FLOAT & NON-COERCION INVARIANTS
# =============================================================================
def test_adversarial_ffi_wire_rejects_json_floats():
    """Direct FFI dispatch with JSON floating point values must be rejected by Rust host."""
    host = get_default_host()

    # Float in cochain
    res1 = host.evaluate_prompt_cochain(
        complex={"c0_dim": 2, "c1_dim": 1, "c2_dim": 0, "d0": [["-1", "1"]], "d1": []},
        cochain=[1.5],
        primal_potential=["0", "0"],
        dual_witness=["0"],
    )
    assert res1.is_ok
    data1 = res1.unwrap()
    assert not data1.get("success", True)
    assert "floating point JSON numbers not allowed" in data1.get("error", "")

    # Float in d0 matrix
    res2 = host.evaluate_prompt_cochain(
        complex={"c0_dim": 2, "c1_dim": 1, "c2_dim": 0, "d0": [[-1.0, 1.0]], "d1": []},
        cochain=["1"],
        primal_potential=["0", "0"],
        dual_witness=["0"],
    )
    assert res2.is_ok
    data2 = res2.unwrap()
    assert not data2.get("success", True)
    assert "floating point JSON numbers not allowed" in data2.get("error", "")

    # Float in dual witness
    res3 = host.evaluate_prompt_cochain(
        complex={"c0_dim": 2, "c1_dim": 1, "c2_dim": 0, "d0": [["-1", "1"]], "d1": []},
        cochain=["1"],
        primal_potential=["0", "0"],
        dual_witness=[0.5],
    )
    assert res3.is_ok
    data3 = res3.unwrap()
    assert not data3.get("success", True)
    assert "floating point JSON numbers not allowed" in data3.get("error", "")


def test_adversarial_ffi_wire_rejects_json_booleans():
    """Direct FFI dispatch with boolean values must be rejected by Rust host."""
    host = get_default_host()
    res = host.evaluate_prompt_cochain(
        complex={"c0_dim": 2, "c1_dim": 1, "c2_dim": 0, "d0": [["-1", "1"]], "d1": []},
        cochain=[True],
        primal_potential=["0", "0"],
        dual_witness=["0"],
    )
    assert res.is_ok
    data = res.unwrap()
    assert not data.get("success", True)
    assert "expected rational" in data.get("error", "")
    assert "got true" in data.get("error", "")
