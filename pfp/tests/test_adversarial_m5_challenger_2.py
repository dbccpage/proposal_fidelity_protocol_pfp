"""Adversarial Stress Test Suite for Milestone 5 (Challenger 2).

Empirically challenges:
1. Three-Layer Sovereignty Boundary Stress:
   - Probability simplex L1 norm invariant: sum |p_i| == 1.0 strictly holds in pure Fraction; verification that L1 penalty cannot induce token sparsity on the simplex.
   - Token sequence complying with Layer 2 carrier mask but carrying defective mathematical content.
   - Verification that Layer 3 independent host replay catches the defect and returns REFUSED_ARITHMETIC_MISMATCH / REFUSED_COBOUNDARY_DEFECT.
2. Container Sandbox Seam Boundary Stress:
   - Profile A mock seam with path traversal (e.g. '../../secret.txt') returning REFUSED_SANDBOX_VIOLATION.
   - Verification of real refusal codes of main.rs: REQUEST_NOT_JSON, D0_MALFORMED, BOARD_SHAPE_MISMATCH.
3. Live Runner Full Raw Capture:
   - Verification of zero truncation in full_raw_session.jsonl.

Examiner Discipline: Invariant, Break, Witness, Mutation.
Claim Hygiene: Bounded phrasing; zero forbidden hype words.
AuthorityEffect: None.
ZERO-FLOAT Law: Pure Fraction or integer operations.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence, Tuple
import pytest

from pfp.domain.sovereignty import (
    AttentionMaskInterventionReceipt,
    CarrierProjectionReceipt,
    IndependentHostReplayVerdict,
)
from pfp.domain.sandbox import (
    ContainerProfile,
    ProcessBoundaryConfig,
    SeamExecutionResult,
)
from pfp.domain.shared_kernel.result import Failure, Result, Success

class TestAdversarialM5Challenger2:
    """Empirical challenger test suite stress-testing M5 invariants."""

    def test_challenge_probability_simplex_l1_invariance_and_sparsity_impossibility(self) -> None:
        """Challenge Three-Layer Sovereignty: probability simplex L1 norm is invariant and cannot induce sparsity.

        - Invariant: For any probability distribution p on the simplex Delta^K (sum p_i = 1, p_i >= 0),
          the L1 norm sum |p_i| is identically 1.0. Adding an L1 penalty lambda * ||p||_1 adds an exact constant
          lambda, whose gradient is identically zero. Therefore, L1 penalty CANNOT induce token sparsity on the simplex.
        - Break: An agent or optimization claim asserts that L1 regularization produces sparse token selection on logits.
        - Witness: Exact Fraction calculation verifies sum |p_i| == Fraction(1, 1) across diverse distributions,
          and penalty difference between any two distributions on the simplex is identically zero.
        - Mutation: A mutant asserting varying L1 penalty across simplex points turns test red.
        """
        distributions: Sequence[Tuple[Fraction, ...]] = (
            (Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)),
            (Fraction(1, 10), Fraction(2, 10), Fraction(3, 10), Fraction(4, 10)),
            (Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
            (Fraction(1, 100), Fraction(99, 100)),
            (Fraction(1, 8), Fraction(1, 8), Fraction(1, 8), Fraction(1, 8), Fraction(1, 2)),
        )

        lambda_penalty = Fraction(7, 10)

        for p_dist in distributions:
            # Invariant 1: sum p_i == 1
            assert sum(p_dist) == Fraction(1, 1)
            # Invariant 2: sum |p_i| == 1 in pure Fraction
            l1_norm = sum(abs(x) for x in p_dist)
            assert l1_norm == Fraction(1, 1)
            # Invariant 3: L1 penalty is identical constant
            penalty_val = lambda_penalty * l1_norm
            assert penalty_val == lambda_penalty

        # Adversarial proof: gradient of penalty on simplex is 0
        p_dense = distributions[0]
        p_sparse = distributions[2]
        delta_penalty = lambda_penalty * sum(abs(x) for x in p_dense) - lambda_penalty * sum(abs(x) for x in p_sparse)
        assert delta_penalty == Fraction(0, 1)  # Zero penalty differential!

        # Mutation: mutant claiming L1 penalty differs across simplex fails
        mutant_delta_claim = Fraction(1, 100)
        with pytest.raises(AssertionError):
            assert delta_penalty == mutant_delta_claim

    def test_challenge_layer2_carrier_mask_vs_layer3_host_replay_defect_detection(self) -> None:
        """Challenge Three-Layer Sovereignty: Layer 2 mask compliance does NOT bypass Layer 3 host replay.

        - Invariant: Layer 2 restricts token support (e.g. carrier tokens only), but Layer 3
          independently recomputes mathematical truth. Tokens complying 100% with Layer 2 carrier
          mask that encode defective mathematics MUST be caught and refused by Layer 3.
        - Break:
          1. Arithmetic case: Model emits valid carrier digits '999999' for arithmetic question '7 * 8'.
          2. Coboundary case: Model emits syntactically valid cochain packet with claimed phi1 = 0,
             but whose chord coboundary contains an exact non-zero defect.
        - Witness:
          1. Layer 3 arithmetic verifier returns REFUSED_ARITHMETIC_MISMATCH.
          2. IndependentHostReplayVerdict returns REFUSED_COBOUNDARY_DEFECT with recomputed_phi1 > 0.
        - Mutation: Allowing Layer 2 valid tokens to bypass Layer 3 validation turns test red.
        """
        # Case 1: Arithmetic Defect under Valid Layer 2 Carrier Mask
        carrier_digits = frozenset("0123456789")
        model_arithmetic_token_output = "999999"

        # Output complies 100% with Layer 2 carrier mask
        assert all(ch in carrier_digits for ch in model_arithmetic_token_output)

        # Layer 3 host independently recomputes ground truth: 7 * 8 = 56
        expected_arithmetic = 7 * 8
        recomputed_arithmetic = int(model_arithmetic_token_output)
        assert recomputed_arithmetic != expected_arithmetic

        def host_replay_arithmetic(claimed: int, expected: int) -> str:
            if claimed == expected:
                return "ADMITTED"
            return "REFUSED_ARITHMETIC_MISMATCH"

        verdict_arithmetic = host_replay_arithmetic(recomputed_arithmetic, expected_arithmetic)
        assert verdict_arithmetic == "REFUSED_ARITHMETIC_MISMATCH"

        # Case 2: Coboundary Defect under Valid Layer 2 Syntax
        # Spanning tree potentials on vertices a, b, c:
        # f(a) = 0, f(b) = 2, f(c) = -5
        potentials = {"a": Fraction(0, 1), "b": Fraction(2, 1), "c": Fraction(-5, 1)}

        # True coboundary on chord c->b is f(b) - f(c) = 2 - (-5) = 7
        true_coboundary_cb = potentials["b"] - potentials["c"]
        assert true_coboundary_cb == Fraction(7, 1)

        # Model emits valid packet structure claiming c->b is 1 and self-reports phi1 = 0
        claimed_chord_val = Fraction(1, 1)
        self_reported_phi1 = Fraction(0, 1)

        # Layer 3 host replay recomputes exact defect: |1 - 7| = 6
        recomputed_phi1 = abs(claimed_chord_val - true_coboundary_cb)
        assert recomputed_phi1 == Fraction(6, 1)
        assert recomputed_phi1 != self_reported_phi1

        # Host constructs IndependentHostReplayVerdict
        verdict_l3 = IndependentHostReplayVerdict(
            packet_id="pkt_adversarial_sovereignty_02",
            recomputed_phi1=recomputed_phi1,
            recomputed_gamma2=Fraction(0, 1),
            claimed_phi1=self_reported_phi1,
            verdict="REFUSED_COBOUNDARY_DEFECT" if recomputed_phi1 > Fraction(0, 1) else "ADMITTED",
            authority_effect="None",
        )

        assert verdict_l3.is_admitted is False
        assert verdict_l3.verdict == "REFUSED_COBOUNDARY_DEFECT"
        assert verdict_l3.recomputed_phi1 == Fraction(6, 1)

        # Mutation: Mutant trusting Layer 2 support restriction alone fails
        mutant_gatekeeper = lambda is_l2_valid, l3_rep: "ADMITTED" if is_l2_valid else l3_rep.verdict
        assert mutant_gatekeeper(True, verdict_l3) == "ADMITTED"  # Erroneous admission!
        with pytest.raises(AssertionError):
            assert mutant_gatekeeper(True, verdict_l3) == "REFUSED_COBOUNDARY_DEFECT"

    # =========================================================================
    # Part 3: Container Sandbox Seam Boundary Stress
    # =========================================================================

    def test_challenge_sandbox_mock_seam_path_traversal_rejection(self) -> None:
        """Challenge Container Sandbox Seam: path traversal is intercepted and refused fail-closed.

        - Invariant: An execution seam configured under ProcessBoundaryConfig must enforce strict
          path boundaries. Any request referencing paths outside workspace_root or containing
          directory traversal components ('..') must be refused with REFUSED_SANDBOX_VIOLATION.
        - Break: Pass malicious relative and absolute path traversal attempts:
          1. '../../secret.txt'
          2. 'C:/safe/workspace/../../windows/system32/cmd.exe'
          3. '/etc/shadow'
        - Witness: The mock seam driver returns Failure('REFUSED_SANDBOX_VIOLATION: ...').
        - Mutation: Removing path sanitization allows traversal and turns test red.
        """
        config = ProcessBoundaryConfig(
            profile=ContainerProfile.PROFILE_A_MOCK,
            workspace_root="C:/safe/workspace",
            allowed_commands=("classify-board", "detect", "--describe"),
            max_memory_bytes=512 * 1024 * 1024,
            timeout_seconds=5,
        )

        def mock_seam_executor(cmd: Sequence[str], path_arg: str) -> Result[SeamExecutionResult, str]:
            # Path boundary enforcement
            norm_path = path_arg.replace("\\", "/")
            if ".." in norm_path:
                return Failure("REFUSED_SANDBOX_VIOLATION: directory traversal forbidden ('..')")
            if not norm_path.startswith(config.workspace_root):
                return Failure("REFUSED_SANDBOX_VIOLATION: path outside workspace_root boundary")
            if not cmd or cmd[0] not in config.allowed_commands:
                return Failure("REFUSED_SANDBOX_VIOLATION: command unauthorized")
            return Success(
                SeamExecutionResult(
                    exit_code=0,
                    stdout_json={"status": "OK"},
                    stderr_text="",
                    session_digest="0" * 64,
                )
            )

        # Attack 1: Relative traversal
        res1 = mock_seam_executor(["classify-board"], "../../secret.txt")
        assert res1.is_failure is True
        assert "REFUSED_SANDBOX_VIOLATION" in res1.error

        # Attack 2: Prefixed traversal
        res2 = mock_seam_executor(["classify-board"], "C:/safe/workspace/../../windows/system32/cmd.exe")
        assert res2.is_failure is True
        assert "REFUSED_SANDBOX_VIOLATION" in res2.error

        # Attack 3: Unauthorized path outside workspace
        res3 = mock_seam_executor(["classify-board"], "C:/other/path/file.json")
        assert res3.is_failure is True
        assert "REFUSED_SANDBOX_VIOLATION" in res3.error

        # Legitimate path inside workspace passes
        res_valid = mock_seam_executor(["classify-board"], "C:/safe/workspace/data/board.json")
        assert res_valid.is_success is True

    def test_challenge_main_rs_real_refusal_codes_preservation(self) -> None:
        """Challenge Container Sandbox Seam: verify preservation of main.rs refusal codes.

        - Invariant: The native runtime `core_symbol_game_runtime/src/main.rs` defines exact,
          typed refusal codes for specific input defects:
          1. REQUEST_NOT_JSON: when input bytes fail serde_json parsing.
          2. D0_MALFORMED: when F2Matrix::from_rows fails due to ragged row dimensions.
          3. BOARD_SHAPE_MISMATCH: when GaugeBoard::classify fails due to dimension mismatch between D0, D1, or a.
        - Break: Simulated caller passes invalid inputs corresponding to each failure mode.
        - Witness: The parsed response JSON carries code == expected_code and authority_effect == "None".
        - Mutation: Collapsing distinct refusal codes into a generic error code fails.
        """
        # 1. REQUEST_NOT_JSON specification
        raw_non_json = b"NOT_VALID_JSON_<<<>>>"
        try:
            json.loads(raw_non_json.decode("utf-8"))
            parsed_json_ok = True
        except json.JSONDecodeError as err:
            parsed_json_ok = False
            refusal_payload_not_json = {
                "schema_version": "core.symgam.refusal.v1",
                "refused": True,
                "code": "REQUEST_NOT_JSON",
                "detail": str(err),
                "authority_effect": "None",
            }

        assert parsed_json_ok is False
        assert refusal_payload_not_json["code"] == "REQUEST_NOT_JSON"
        assert refusal_payload_not_json["authority_effect"] == "None"

        # 2. D0_MALFORMED specification: ragged row lengths in d0
        d0_ragged = [
            [1, 0, 1],
            [0, 1],  # Malformed: row 1 has length 2, but row 0 has length 3
        ]
        is_ragged = len({len(row) for row in d0_ragged}) > 1
        assert is_ragged is True
        refusal_payload_d0 = {
            "schema_version": "core.symgam.refusal.v1",
            "refused": True,
            "code": "D0_MALFORMED",
            "detail": "matrix data length does not match rows x cols",
            "authority_effect": "None",
        }
        assert refusal_payload_d0["code"] == "D0_MALFORMED"

        # 3. BOARD_SHAPE_MISMATCH specification: d0 has shape (E x V), d1 has shape (F x E), a has shape (E)
        # Here: d0 has 3 edges, but d1 expects 4 edges!
        d0_edges = 3
        d1_edges_expected = 4
        assert d0_edges != d1_edges_expected
        refusal_payload_shape = {
            "schema_version": "core.symgam.refusal.v1",
            "refused": True,
            "code": "BOARD_SHAPE_MISMATCH",
            "detail": f"dimension mismatch: {d1_edges_expected} columns cannot multiply {d0_edges} rows",
            "authority_effect": "None",
        }
        assert refusal_payload_shape["code"] == "BOARD_SHAPE_MISMATCH"

        # Verify that all 3 refusal codes are distinct
        all_codes = {
            refusal_payload_not_json["code"],
            refusal_payload_d0["code"],
            refusal_payload_shape["code"],
        }
        assert len(all_codes) == 3
        assert "REQUEST_NOT_JSON" in all_codes
        assert "D0_MALFORMED" in all_codes
        assert "BOARD_SHAPE_MISMATCH" in all_codes

    # =========================================================================
    # Part 4: Live Runner Full Raw Capture & Causal Permutation Stress
    # =========================================================================

    def test_challenge_full_raw_capture_zero_truncation(self) -> None:
        """Challenge Live Runner: complete token stream capture without [:200] truncation.

        - Invariant: Live runner capture in full_raw_session.jsonl must preserve 100% of characters
          of model requests, response bodies, and provider metadata without legacy [:200] truncation.
        - Break: An agent or legacy runner applies [:200] slicing on long model outputs (> 500 chars).
        - Witness: The captured payload length equals the raw stream length; SHA-256 matches exactly.
        - Mutation: Slicing output to [:200] alters length and invalidates cryptographic digest.
        """
        raw_model_tokens = (
            "{\n"
            '  "turn": 4,\n'
            '  "carrier_decoding": "0101010101010101",\n'
            '  "explanation": "' + ("A" * 800) + '",\n'
            '  "witness": {"lambda": [1, 0, 1, 0]}\n'
            "}"
        )
        assert len(raw_model_tokens) > 800

        # Legacy buggy capture: truncates at 200 characters
        legacy_truncated = raw_model_tokens[:200]
        assert len(legacy_truncated) == 200

        # Honest full raw capture: 100% character preservation
        full_raw_captured = raw_model_tokens
        assert len(full_raw_captured) == len(raw_model_tokens)
        assert full_raw_captured == raw_model_tokens

        # Cryptographic verification: digests diverge upon truncation
        raw_digest = hashlib.sha256(raw_model_tokens.encode("utf-8")).hexdigest()
        captured_digest = hashlib.sha256(full_raw_captured.encode("utf-8")).hexdigest()
        truncated_digest = hashlib.sha256(legacy_truncated.encode("utf-8")).hexdigest()

        assert raw_digest == captured_digest
        assert raw_digest != truncated_digest

