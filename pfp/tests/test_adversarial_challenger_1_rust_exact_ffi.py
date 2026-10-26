"""Empirical Adversarial Stress Suite: Sovereign Rust Host, Exact Math & FFI Boundaries.

Authored by Challenger 1 (teamwork_preview_challenger).
Validates:
1. Exact Rational / Zero-Float Stress Testing (high precision, negative coords, zero denominators, _to_exact_triad_ints, math.lcm).
2. FFI Boundary & Native Binary Stress Testing (omega_symbol_game.exe fail-closed on malformed JSON, missing fields, unregistered adapters, out-of-bounds parameters, zero panics).
3. Simplicial Homology & Nilpotency Verification (d_{k-1} o d_k = 0 on higher simplices up to dimension 6, non-closed boundary rejection).

AuthorityEffect: None (const).
"""

from __future__ import annotations

import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path
import pytest

from omega_engine_operations.domain.rop.result import Err, Ok
from omega_engine_operating_system.adapters.rust_host.ffi import (
    RUNTIME_OUTCOME_SCHEMA,
    RUNTIME_REQUEST_SCHEMA,
    locate_host_binary,
)
from omega_engine_pfp.domain.exact.q import Q
from omega_engine_pfp.domain.solvers.retraction import (
    ObstructionScore,
    _to_exact_triad_ints,
)
from omega_engine_pfp.ffi import RustSymbolGameHost, get_default_host


# ============================================================================
# Helpers
# ============================================================================

def _get_raw_binary() -> Path:
    """Resolve the native omega_symbol_game binary directly."""
    located = locate_host_binary()
    assert isinstance(located, Ok), f"Binary location failed: {located}"
    return located.value.binary


def _run_raw_process(args: list[str], stdin_bytes: bytes) -> subprocess.CompletedProcess:
    """Run the raw native host process with exact stdin bytes."""
    binary = _get_raw_binary()
    return subprocess.run(
        [str(binary), *args],
        input=stdin_bytes,
        capture_output=True,
        timeout=15.0,
        check=False,
    )


def _invoke_raw_runtime(action: str, payload: dict, schema: str = RUNTIME_REQUEST_SCHEMA) -> dict:
    """Send an invoke request and parse stdout as JSON."""
    req = {
        "schema_version": schema,
        "action": action,
        "payload": payload,
    }
    input_bytes = json.dumps(req).encode("utf-8")
    proc = _run_raw_process(["invoke"], input_bytes)
    assert proc.returncode == 0, f"Process exited {proc.returncode}: stderr={proc.stderr.decode('utf-8', errors='replace')}"
    return json.loads(proc.stdout.decode("utf-8"))


# ============================================================================
# Dimension 1: Exact Rational / Zero-Float Stress Testing
# ============================================================================

class TestExactRationalZeroFloatStress:
    """Empirical stress-testing of exact rational arithmetic and scaling invariants."""

    def test_high_precision_rational_arithmetic_without_floats(self):
        """High-precision rationals with large numerators/denominators compute exact results."""
        # 60-digit integer numerators and denominators
        n1 = 10**60 + 1
        d1 = 10**60 + 7
        n2 = 10**60 + 13
        d2 = 10**60 + 19

        q1 = Q(n1, d1)
        q2 = Q(n2, d2)

        # Exact addition: (n1*d2 + n2*d1) / (d1*d2)
        q_sum = q1 + q2
        expected_num = n1 * d2 + n2 * d1
        expected_den = d1 * d2
        common = math.gcd(expected_num, expected_den)
        assert q_sum.num == expected_num // common
        assert q_sum.den == expected_den // common

        # Exact multiplication
        q_prod = q1 * q2
        p_num = n1 * n2
        p_den = d1 * d2
        p_gcd = math.gcd(p_num, p_den)
        assert q_prod.num == p_num // p_gcd
        assert q_prod.den == p_den // p_gcd

        # Verify no float conversion occurred
        assert isinstance(q_sum.num, int)
        assert isinstance(q_sum.den, int)
        assert q_sum.den != 0

    def test_negative_rational_coordinates_exactness(self):
        """Negative coordinates in rationals maintain canonical sign conventions."""
        q_neg = Q(-7, 13)
        assert q_neg.num == -7
        assert q_neg.den == 13

        # Q enforces positive denominator: negative denominator raises ExactError
        from omega_engine_pfp.domain.exact.errors import ExactError

        with pytest.raises(ExactError) as exc_info:
            Q(7, -13)
        assert exc_info.value.code == "RR-DENOMINATOR"

        # Python Fraction normalizes negative denominator to numerator
        frac = Fraction(7, -13)
        assert frac.numerator == -7
        assert frac.denominator == 13

    def test_zero_denominator_rejected(self):
        """Constructing rationals with zero denominator is strictly rejected."""
        from omega_engine_pfp.domain.exact.errors import ExactError

        with pytest.raises(ExactError) as exc_info:
            Q(1, 0)
        assert exc_info.value.code == "RR-DENOMINATOR"

        with pytest.raises(ZeroDivisionError):
            Fraction(1, 0)

    def test_to_exact_triad_ints_normal_scaling(self):
        """_to_exact_triad_ints accurately computes LCM scale and preserves integer values."""
        score_a = ObstructionScore(
            gamma_2=Fraction(3, 4),
            phi_1=Fraction(5, 6),
            active_count=2,
            active_obstruction_ids=("obs_1", "obs_2"),
        )
        score_b = ObstructionScore(
            gamma_2=Fraction(1, 2),
            phi_1=Fraction(2, 3),
            active_count=1,
            active_obstruction_ids=("obs_1",),
        )

        triad_a, triad_b = _to_exact_triad_ints(score_a, score_b)

        # Denominators: gamma: (4, 2) -> lcm 4; phi: (6, 3) -> lcm 6; overall scale = lcm(4, 6) = 12
        assert triad_a["gamma_2"] == int(Fraction(3, 4) * 12) == 9
        assert triad_a["phi_1"] == int(Fraction(5, 6) * 12) == 10
        assert triad_a["defect_count"] == 2

        assert triad_b["gamma_2"] == int(Fraction(1, 2) * 12) == 6
        assert triad_b["phi_1"] == int(Fraction(2, 3) * 12) == 8
        assert triad_b["defect_count"] == 1

    def test_to_exact_triad_ints_large_coprime_denominators(self):
        """_to_exact_triad_ints scales huge denominators accurately without precision loss."""
        # Large powers of 2 and 3: 2^40 and 3^30
        d_a = 2**40
        d_b = 3**30
        score_a = ObstructionScore(
            gamma_2=Fraction(1, d_a),
            phi_1=Fraction(1, d_a),
            active_count=0,
            active_obstruction_ids=(),
        )
        score_b = ObstructionScore(
            gamma_2=Fraction(1, d_b),
            phi_1=Fraction(1, d_b),
            active_count=0,
            active_obstruction_ids=(),
        )

        triad_a, triad_b = _to_exact_triad_ints(score_a, score_b)

        # scale = d_a * d_b > 2^64
        scale = d_a * d_b
        assert scale > 2**64
        assert triad_a["gamma_2"] == d_b
        assert triad_a["phi_1"] == d_b
        assert triad_b["gamma_2"] == d_a
        assert triad_b["phi_1"] == d_a

    def test_triad_u64_boundary_rejection_over_ffi(self):
        """When scaled integers exceed u64::MAX or are negative, native Rust fails closed with typed error."""
        # Value exceeding u64::MAX (2^64 - 1 = 18446744073709551615)
        overflow_val = 2**65
        payload = {
            "before": {"gamma_2": overflow_val, "phi_1": 10, "defect_count": 0},
            "after": {"gamma_2": 5, "phi_1": 5, "defect_count": 0},
        }
        res = _invoke_raw_runtime("retraction_turn", payload)
        assert res["success"] is False
        assert "invalid retraction_turn input" in res["error"]
        assert res["authority_effect"] == "None"

        # Negative value (DescentTriad expects unsigned u64)
        neg_payload = {
            "before": {"gamma_2": -1, "phi_1": 10, "defect_count": 0},
            "after": {"gamma_2": 5, "phi_1": 5, "defect_count": 0},
        }
        res_neg = _invoke_raw_runtime("retraction_turn", neg_payload)
        assert res_neg["success"] is False
        assert "invalid retraction_turn input" in res_neg["error"]

    def test_exact_determinant_hilbert_matrix_zero_float_precision(self):
        """Exact rational determinant of 4x4 Hilbert matrix is 1/6048000 and 5x5 is 1/28934016000."""
        # H_4: H[i, j] = 1 / (i + j + 1)
        hilbert_4 = {
            "matrix": {
                "rows": [
                    ["1", "1/2", "1/3", "1/4"],
                    ["1/2", "1/3", "1/4", "1/5"],
                    ["1/3", "1/4", "1/5", "1/6"],
                    ["1/4", "1/5", "1/6", "1/7"],
                ]
            }
        }
        res_4 = _invoke_raw_runtime("exact_determinant", hilbert_4)
        assert res_4["success"] is True, f"Error: {res_4.get('error')}"
        assert res_4["result"]["determinant"] == "1/6048000"

        # H_5: H[i, j] = 1 / (i + j + 1) for i, j in 0..4
        hilbert_5 = {
            "matrix": {
                "rows": [
                    ["1", "1/2", "1/3", "1/4", "1/5"],
                    ["1/2", "1/3", "1/4", "1/5", "1/6"],
                    ["1/3", "1/4", "1/5", "1/6", "1/7"],
                    ["1/4", "1/5", "1/6", "1/7", "1/8"],
                    ["1/5", "1/6", "1/7", "1/8", "1/9"],
                ]
            }
        }
        res_5 = _invoke_raw_runtime("exact_determinant", hilbert_5)
        assert res_5["success"] is True, f"Error: {res_5.get('error')}"
        assert res_5["result"]["determinant"] == "1/266716800000"
        assert res_5["authority_effect"] == "None"


# ============================================================================
# Dimension 2: FFI Boundary & Native Binary Stress Testing
# ============================================================================

class TestFfiBoundaryAndNativeBinaryStress:
    """Adversarial testing of the native omega_symbol_game.exe process boundary."""

    def test_raw_binary_malformed_json_fails_closed(self):
        """Direct invocation with completely malformed JSON exits with error and zero panics."""
        malformed_inputs = [
            b"",
            b"{",
            b"{invalid json: 123}",
            b"\"a bare string\"",
            b"12345",
            b"null",
            b"[1, 2, 3]",
            b"\xff\xfe\xfd",  # Invalid UTF-8
        ]
        for bad_input in malformed_inputs:
            proc = _run_raw_process(["invoke"], bad_input)
            # The process must exit non-zero (refusal at boundary)
            assert proc.returncode != 0, f"Expected non-zero exit for input {bad_input!r}"
            stderr = proc.stderr.decode("utf-8", errors="replace")
            # Crucial: NO unhandled panics or stack traces
            assert "panicked at" not in stderr, f"Host panicked on malformed input: {stderr}"

    def test_schema_mismatch_refused_with_typed_error(self):
        """Request with wrong schema version returns typed error JSON."""
        res = _invoke_raw_runtime(
            action="canonical_wire",
            payload={"test": 1},
            schema="invalid.schema.version.v99",
        )
        assert res["schema_version"] == RUNTIME_OUTCOME_SCHEMA
        assert res["success"] is False
        assert "RUNTIME_REQUEST_SCHEMA_MISMATCH" in res["error"]
        assert res["authority_effect"] == "None"

    def test_unregistered_runtime_action_refused(self):
        """Invoking an unregistered action returns typed refusal."""
        hostile_actions = [
            "unregistered_bogus_action",
            "DROP TABLE users;",
            "../../../etc/passwd",
            "",
            "coda_unknown_subroutine",
        ]
        for action in hostile_actions:
            res = _invoke_raw_runtime(action=action, payload={})
            assert res["success"] is False
            assert "unsupported runtime action" in res["error"]
            assert res["authority_effect"] == "None"

    def test_missing_required_payload_fields(self):
        """Payload missing mandatory fields returns typed deserialization error."""
        # exact_determinant requires 'matrix'
        res = _invoke_raw_runtime("exact_determinant", {})
        assert res["success"] is False
        assert "invalid matrix input" in res["error"]

        # verify_l1_certificate requires 'matrix', 'omega', 'p', 'y'
        res_l1 = _invoke_raw_runtime("verify_l1_certificate", {"matrix": []})
        assert res_l1["success"] is False
        assert "invalid rational input" in res_l1["error"]

    def test_out_of_bounds_parameters_in_exact_linear_algebra(self):
        """Non-square matrices, zero divisions, or invalid dimensions refuse cleanly."""
        # Non-square matrix for determinant (2 rows, 3 cols)
        non_square = {
            "matrix": {
                "rows": [
                    ["1", "2", "3"],
                    ["4", "5", "6"],
                ]
            }
        }
        res = _invoke_raw_runtime("exact_determinant", non_square)
        assert res["success"] is False
        assert "not square" in res["error"]

        # Malformed rational string in matrix
        malformed_rational = {
            "matrix": {
                "rows": [
                    ["1/0", "2"],
                    ["3", "4"],
                ]
            }
        }
        res_zero = _invoke_raw_runtime("exact_determinant", malformed_rational)
        assert res_zero["success"] is False

    def test_input_size_ceiling_enforcement(self):
        """Inputs exceeding MAX_RUNTIME_REQUEST_BYTES (65,536 bytes) are refused at process seam."""
        # Construct an oversized request: 70 KB of padding in payload
        oversized_req = {
            "schema_version": RUNTIME_REQUEST_SCHEMA,
            "action": "canonical_wire",
            "payload": {"padding": "X" * 70_000},
        }
        raw_bytes = json.dumps(oversized_req).encode("utf-8")
        assert len(raw_bytes) > 65_536

        proc = _run_raw_process(["invoke"], raw_bytes)
        assert proc.returncode != 0
        stderr = proc.stderr.decode("utf-8", errors="replace")
        assert "RUNTIME_REQUEST_TOO_LARGE" in stderr
        assert "panicked at" not in stderr

    def test_undeclared_fields_in_runtime_request_rejected(self):
        """Requests with undeclared fields fail deserialization due to deny_unknown_fields."""
        rogue_req = {
            "schema_version": RUNTIME_REQUEST_SCHEMA,
            "action": "canonical_wire",
            "payload": {},
            "unauthorized_extra_key": "malicious_injection",
        }
        proc = _run_raw_process(["invoke"], json.dumps(rogue_req).encode("utf-8"))
        assert proc.returncode != 0
        stderr = proc.stderr.decode("utf-8", errors="replace")
        assert "unknown field" in stderr or "unauthorized_extra_key" in stderr
        assert "panicked at" not in stderr

    def test_carrier_manifest_mode_malformed_input_rejected(self):
        """--derive-carrier-manifest mode rejects malformed bytes with non-zero exit and zero panics."""
        proc = _run_raw_process(["--derive-carrier-manifest"], b"garbage carrier data")
        assert proc.returncode != 0
        stderr = proc.stderr.decode("utf-8", errors="replace")
        assert "panicked at" not in stderr

    def test_classify_board_mode_malformed_input_rejected(self):
        """classify-board mode rejects invalid JSON with non-zero exit and zero panics."""
        proc = _run_raw_process(["classify-board"], b'{"invalid": true}')
        assert proc.returncode != 0
        stderr = proc.stderr.decode("utf-8", errors="replace")
        assert "panicked at" not in stderr


# ============================================================================
# Dimension 3: Simplicial Homology & Nilpotency Verification
# ============================================================================

class TestSimplicialHomologyNilpotency:
    """Empirical verification of simplicial boundary operator nilpotency d_{k-1} o d_k = 0."""

    @pytest.mark.parametrize(
        ("dim", "vertices"),
        [
            (2, [0, 1, 2]),                     # 2-simplex (triangle)
            (3, [0, 1, 2, 3]),                  # 3-simplex (tetrahedron)
            (4, [0, 1, 2, 3, 4]),               # 4-simplex
            (5, [0, 1, 2, 3, 4, 5]),            # 5-simplex
            (6, [0, 1, 2, 3, 4, 5, 6]),         # 6-simplex
        ],
    )
    def test_boundary_nilpotency_on_higher_simplices(self, dim: int, vertices: list[int]):
        """For full simplices up to dimension 6, d_{k-1} o d_k = 0 holds identically for all k >= 2."""
        payload = {"simplices": [vertices]}
        res = _invoke_raw_runtime("exact_verify_simplicial_boundary_law", payload)
        assert res["success"] is True, f"Failed at dim {dim}: {res.get('error')}"
        result = res["result"]
        assert result["max_dimension"] == dim
        assert result["boundary_law_verified"] is True

        compositions = result["compositions"]
        assert len(compositions) == dim - 1  # degrees 2 ..= dim

        for comp in compositions:
            k = comp["degree"]
            assert comp["is_zero"] is True, f"Degree {k} boundary composition d_{k-1} o d_k was NOT zero!"
            assert comp["rows"] > 0
            assert comp["cols"] > 0

    def test_euler_characteristic_simplex_invariants(self):
        """The Euler characteristic of an n-simplex equals 1: chi = sum_{k=0}^n (-1)^k C(n+1, k+1) = 1."""
        for n in range(2, 7):
            vertices = list(range(n + 1))
            res = _invoke_raw_runtime("exact_verify_simplicial_boundary_law", {"simplices": [vertices]})
            assert res["success"] is True
            # Standard n-simplex is contractible, so chi == 1
            assert res["result"]["euler_characteristic"] == 1, f"Chi for {n}-simplex was {res['result']['euler_characteristic']}"

    def test_boundary_closed_verification_closed_triangle(self):
        """A closed 1-cycle face boundary satisfies net zero vertex incidence."""
        # Triangle cycle: 0 -> 1, 1 -> 2, 2 -> 0
        closed_cycle = [
            (0, 1, 1),
            (1, 2, 1),
            (2, 0, 1),
        ]
        res = _invoke_raw_runtime("exact_verify_boundary_closed", {"faces": [closed_cycle]})
        assert res["success"] is True
        assert res["result"]["boundary_closed"] is True

    def test_boundary_closed_verification_open_chain_rejected(self):
        """An open 1-chain has non-zero net vertex boundary and correctly fails validation."""
        # Open path: 0 -> 1, 1 -> 2 (missing 2 -> 0)
        open_chain = [
            (0, 1, 1),
            (1, 2, 1),
        ]
        res = _invoke_raw_runtime("exact_verify_boundary_closed", {"faces": [open_chain]})
        assert res["success"] is True
        assert res["result"]["boundary_closed"] is False

    def test_boundary_closed_verification_twisted_orientation_rejected(self):
        """A cycle with twisted edge orientations has non-zero net boundary and fails validation."""
        # 0 -> 1 (sign +1), 1 -> 2 (sign +1), 0 -> 2 (sign +1: orientation points to 2, so 2 has net +2, 0 has net -2)
        twisted_cycle = [
            (0, 1, 1),
            (1, 2, 1),
            (0, 2, 1),
        ]
        res = _invoke_raw_runtime("exact_verify_boundary_closed", {"faces": [twisted_cycle]})
        assert res["success"] is True
        assert res["result"]["boundary_closed"] is False

    def test_boundary_closed_verification_multi_face_complex(self):
        """Multi-face complexes correctly report false if any individual face fails boundary closure."""
        face1_closed = [(0, 1, 1), (1, 2, 1), (2, 0, 1)]
        face2_closed = [(2, 3, 1), (3, 4, 1), (4, 2, 1)]
        face3_open = [(0, 4, 1), (4, 5, 1)]  # Open

        # All closed
        res_all_closed = _invoke_raw_runtime("exact_verify_boundary_closed", {"faces": [face1_closed, face2_closed]})
        assert res_all_closed["result"]["boundary_closed"] is True

        # One open
        res_one_open = _invoke_raw_runtime("exact_verify_boundary_closed", {"faces": [face1_closed, face2_closed, face3_open]})
        assert res_one_open["result"]["boundary_closed"] is False

    def test_boundary_nilpotency_on_7_simplex(self):
        """Simplicial boundary nilpotency holds on 7-simplex across degrees 2 to 7."""
        payload = {"simplices": [list(range(8))]}
        res = _invoke_raw_runtime("exact_verify_simplicial_boundary_law", payload)
        assert res["success"] is True
        result = res["result"]
        assert result["max_dimension"] == 7
        assert result["boundary_law_verified"] is True
        assert len(result["compositions"]) == 6  # degrees 2 ..= 7
        for comp in result["compositions"]:
            assert comp["is_zero"] is True

    def test_boundary_nilpotency_on_disjoint_simplices(self):
        """Disjoint union of simplices satisfies d_{k-1} o d_k = 0 across all components."""
        payload = {"simplices": [[0, 1, 2, 3], [4, 5, 6, 7]]}
        res = _invoke_raw_runtime("exact_verify_simplicial_boundary_law", payload)
        assert res["success"] is True
        result = res["result"]
        assert result["boundary_law_verified"] is True
        # For two disjoint 3-simplices, chi = chi(S_1) + chi(S_2) = 1 + 1 = 2
        assert result["euler_characteristic"] == 2
        for comp in result["compositions"]:
            assert comp["is_zero"] is True

    def test_duplicate_vertex_simplex_rejected(self):
        """Simplices with duplicate vertices are rejected cleanly."""
        payload = {"simplices": [[0, 1, 1]]}
        res = _invoke_raw_runtime("exact_verify_simplicial_boundary_law", payload)
        assert res["success"] is False
        assert "invalid simplex" in res["error"] or "DuplicateVertex" in res["error"]
        assert res["authority_effect"] == "None"

    def test_empty_simplex_list_yields_trivial_verified_report(self):
        """Empty simplices list returns a valid trivial report with zero dimension and verified=True."""
        payload = {"simplices": []}
        res = _invoke_raw_runtime("exact_verify_simplicial_boundary_law", payload)
        assert res["success"] is True
        assert res["result"]["boundary_law_verified"] is True
        assert res["result"]["max_dimension"] == 0

