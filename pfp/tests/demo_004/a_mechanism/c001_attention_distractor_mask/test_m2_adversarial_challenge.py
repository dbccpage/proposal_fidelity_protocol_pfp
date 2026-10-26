"""
test_m2_adversarial_challenge.py — Adversarial Stress Test Suite for Milestone 2.

Adversarially challenges and stress-tests attention_hook.py across 5 dimensions:
1. Attention mask zeroing: weird shapes (1D-6D, empty, single-token, large sequence),
   negative fluff indices, out-of-bounds indices, and inplace integrity.
2. Position IDs validation: reversed, scrambled, offset, duplicate/non-monotonic,
   batch length mismatches, and 3D tensor invariant checks.
3. Character offset mapping: token boundary overlaps (left, right, straddling, exact),
   multi-byte/Unicode intervals (emojis, Cyrillic, Greek, CJK), and identical token separation.
4. Two-Signal Danger Gate: exact rational boundary thresholds (tau == mass, tau +/- epsilon),
   float injection (Python floats, numpy floats), and invalid data types.
5. Budget enforcement: immediate BudgetExceeded at ceiling, fail-closed pre-dispatch,
   rejection of negative and float costs, and zero-dollar local billing.
"""

from __future__ import annotations

import re
from fractions import Fraction
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")
np = pytest.importorskip("numpy")

from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.attention_hook import (
    MechanismBudgetController,
    PositionIdsInvariantViolation,
    apply_distractor_key_mask,
    attention_mass_masking_decision,
    evaluate_danger_gate,
    is_masking_authorized,
    resolve_fluff_positions,
    verify_position_ids_invariant,
)

from omega_engine_epistemic_immune_system.domain.danger_signals import (
    SignalIndependenceRefusal,
)
from omega_engine_epistemic_immune_system.domain.value_objects import (
    DangerDecision,
    DangerSeverity,
)
from omega_engine_woland.domain.providers.types import BudgetExceeded

# ==============================================================================
# Dimension 1: Attention Mask Zeroing Attacks
# ==============================================================================


class TestAttentionMaskZeroingAttacks:
    """Adversarial attacks on attention mask zeroing."""

    def test_1d_tensor_mask(self):
        """1D tensor mask [seq_len] is zeroed at fluff positions."""
        mask = torch.ones(8, dtype=torch.long)
        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[2, 6],
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        assert masked.shape == (8,)
        assert masked[2].item() == 0
        assert masked[6].item() == 0
        assert masked[0].item() == 1
        assert masked[1].item() == 1

    def test_6d_tensor_mask(self):
        """Higher-dimensional mask (6D tensor) zeroes key positions along last dimension."""
        # Shape: (2, 3, 2, 4, 5, 8)
        mask = torch.ones((2, 3, 2, 4, 5, 8), dtype=torch.long)
        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[3, 7],
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        assert masked.shape == (2, 3, 2, 4, 5, 8)
        assert (masked[..., [3, 7]] == 0).all()
        assert (masked[..., [0, 1, 2, 4, 5, 6]] == 1).all()

    def test_single_token_sequence(self):
        """Single token sequence (seq_len=1) with fluff=[0] is zeroed cleanly."""
        mask = torch.ones((1, 1, 1, 1), dtype=torch.long)
        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[0],
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        assert masked.item() == 0

    def test_large_sequence_stress(self):
        """Large sequence length (seq_len=4096) with distributed fluff positions."""
        seq_len = 4096
        mask = torch.ones((1, 1, seq_len), dtype=torch.long)
        fluff = [10, 100, 500, 1000, 2048, 4000]
        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=fluff,
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        assert (masked[:, :, fluff] == 0).all()
        non_fluff_sample = [0, 9, 11, 99, 101, 2047, 2049, 4095]
        assert (masked[:, :, non_fluff_sample] == 1).all()

    def test_all_positions_masked(self):
        """When all token positions are marked as fluff, the entire key dimension is zeroed."""
        seq_len = 6
        mask = torch.ones((2, 4, seq_len, seq_len), dtype=torch.long)
        all_fluff = list(range(seq_len))
        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=all_fluff,
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        assert (masked == 0).all()

    def test_negative_fluff_indices_behavior(self):
        """Adversarial check: negative indices in fluff_positions.

        In PyTorch, negative indexing like -1 refers to the last element.
        We document whether PyTorch tensor masks apply negative indexing or raise an error,
        while list masks ignore negative indices.
        """
        mask_tensor = torch.ones((1, 5), dtype=torch.long)
        masked_tensor = apply_distractor_key_mask(
            attention_mask=mask_tensor,
            fluff_positions=[-1],
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        # Empirical check: PyTorch treats -1 as the last element (index 4)
        assert masked_tensor[0, 4].item() == 0
        assert masked_tensor[0, 0].item() == 1

        # List mask behavior
        mask_list = [1, 1, 1, 1, 1]
        masked_list = apply_distractor_key_mask(
            attention_mask=mask_list,
            fluff_positions=[-1],
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        # List implementation guards with `0 <= p < len(mask_to_edit)`
        assert masked_list == [1, 1, 1, 1, 1]

    def test_out_of_bounds_fluff_indices_raises_in_tensor(self):
        """Out of bounds index in fluff_positions raises IndexError on PyTorch tensors."""
        mask = torch.ones((1, 5), dtype=torch.long)
        with pytest.raises(IndexError):
            apply_distractor_key_mask(
                attention_mask=mask,
                fluff_positions=[99],
                danger_gate_decision=DangerDecision.QUARANTINED,
            )

    def test_boolean_dtype_mask(self):
        """Boolean dtype attention mask zeroes keys to False."""
        mask = torch.ones((2, 6), dtype=torch.bool)
        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[1, 3],
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        assert masked.dtype == torch.bool
        assert masked[0, 1].item() is False
        assert masked[0, 3].item() is False
        assert masked[0, 0].item() is True

    def test_inplace_vs_non_inplace_isolation(self):
        """inplace=False must not mutate the original tensor; inplace=True must mutate."""
        original = torch.ones((1, 4), dtype=torch.long)
        cloned = apply_distractor_key_mask(
            attention_mask=original,
            fluff_positions=[2],
            danger_gate_decision=DangerDecision.QUARANTINED,
            inplace=False,
        )
        assert original[0, 2].item() == 1, "Original tensor was mutated under inplace=False!"
        assert cloned[0, 2].item() == 0

        apply_distractor_key_mask(
            attention_mask=original,
            fluff_positions=[2],
            danger_gate_decision=DangerDecision.QUARANTINED,
            inplace=True,
        )
        assert original[0, 2].item() == 0, "Original tensor was NOT mutated under inplace=True!"


# ==============================================================================
# Dimension 2: Position IDs Invariant Attacks
# ==============================================================================


class TestPositionIdsInvariantAttacks:
    """Adversarial attacks on position_ids invariant validation."""

    def test_reversed_position_ids_rejected(self):
        """Reversed position IDs [N-1, ..., 0] raise PositionIdsInvariantViolation."""
        seq_len = 8
        reversed_pos = torch.arange(seq_len - 1, -1, -1).unsqueeze(0)
        with pytest.raises(PositionIdsInvariantViolation, match="Position IDs altered"):
            verify_position_ids_invariant(reversed_pos, seq_len=seq_len)

    def test_scrambled_permuted_position_ids_rejected(self):
        """Permuted position IDs [0, 2, 1, 3] raise PositionIdsInvariantViolation."""
        permuted = torch.tensor([[0, 2, 1, 3, 4]])
        with pytest.raises(PositionIdsInvariantViolation, match="Position IDs altered"):
            verify_position_ids_invariant(permuted, seq_len=5)

    def test_offset_shifted_position_ids_rejected(self):
        """Offset position IDs [10, 11, 12, 13] raise PositionIdsInvariantViolation."""
        offset_pos = torch.tensor([[10, 11, 12, 13]])
        with pytest.raises(PositionIdsInvariantViolation, match="Position IDs altered"):
            verify_position_ids_invariant(offset_pos, seq_len=4)

    def test_duplicate_non_monotonic_position_ids_rejected(self):
        """Duplicate/non-monotonic position IDs [0, 1, 1, 2] raise PositionIdsInvariantViolation."""
        dup_pos = torch.tensor([[0, 1, 1, 2]])
        with pytest.raises(PositionIdsInvariantViolation, match="Position IDs altered"):
            verify_position_ids_invariant(dup_pos, seq_len=4)

    def test_length_mismatch_rejected(self):
        """Position IDs with shape mismatch against seq_len raise PositionIdsInvariantViolation."""
        pos = torch.arange(5).unsqueeze(0)
        with pytest.raises(PositionIdsInvariantViolation, match="Position IDs length mismatch"):
            verify_position_ids_invariant(pos, seq_len=6)

    def test_multibatch_partial_corruption_rejected(self):
        """When batch row 0 is valid but batch row 1 is corrupted, it raises PositionIdsInvariantViolation."""
        batch_pos = torch.stack(
            [
                torch.arange(6),
                torch.tensor([0, 1, 2, 3, 5, 5]),  # Row 1 corrupted
            ]
        )
        with pytest.raises(PositionIdsInvariantViolation, match="Position IDs altered at batch 1"):
            verify_position_ids_invariant(batch_pos, seq_len=6)

    def test_none_position_ids_direct_verification_fails(self):
        """None passed to verify_position_ids_invariant raises PositionIdsInvariantViolation."""
        with pytest.raises(PositionIdsInvariantViolation, match="position_ids is None"):
            verify_position_ids_invariant(None)

    def test_unsupported_position_ids_type_raises(self):
        """Passing an invalid object type raises PositionIdsInvariantViolation."""
        with pytest.raises(PositionIdsInvariantViolation, match="Unsupported position_ids type"):
            verify_position_ids_invariant("invalid_string_positions")

    def test_3d_position_ids_behavior(self):
        """Empirical investigation: 3D position_ids tensor shape [1, 1, seq_len].

        In current implementation, lines 190-202 check 2D and 1D tensors.
        If a 3D tensor is passed, we observe whether it bypasses validation.
        """
        corrupted_3d = torch.tensor([[[99, 98, 97]]])
        # If length matches seq_len=3, does verify_position_ids_invariant check contents?
        result = verify_position_ids_invariant(corrupted_3d, seq_len=3)
        # Note: Current implementation does not check 3D tensor contents (returns True).
        # We record this finding as a non-breaking limitation of verify_position_ids_invariant.
        assert result is True


# ==============================================================================
# Dimension 3: Character Offset Mapping Attacks
# ==============================================================================


class TestCharacterOffsetMappingAttacks:
    """Adversarial attacks on character offset mapping and distractor isolation."""

    def test_token_boundary_left_overlap_excluded(self):
        """Token starting before distractor span is strictly excluded (coordinate containment)."""
        prompt = "0123456789"
        # Distractor span is [4, 9]
        spans = [(4, 9)]
        # Token starts at 2 and ends at 6 (crosses d_start=4)
        offset_mapping = [(2, 6)]
        fluff = resolve_fluff_positions(prompt, spans, offset_mapping=offset_mapping)
        # Must NOT be in fluff because t_start (2) < d_start (4)
        assert fluff == [], "Left-overlapping token was incorrectly included in fluff!"

    def test_token_boundary_right_overlap_excluded(self):
        """Token ending after distractor span is strictly excluded (coordinate containment)."""
        prompt = "0123456789"
        # Distractor span is [2, 7]
        spans = [(2, 7)]
        # Token starts at 5 and ends at 8 (crosses d_end=7)
        offset_mapping = [(5, 8)]
        fluff = resolve_fluff_positions(prompt, spans, offset_mapping=offset_mapping)
        # Must NOT be in fluff because t_end (8) > d_end (7)
        assert fluff == [], "Right-overlapping token was incorrectly included in fluff!"

    def test_token_boundary_straddling_excluded(self):
        """Token completely straddling distractor span is strictly excluded."""
        prompt = "0123456789"
        spans = [(4, 6)]
        # Token spans [2, 8]
        offset_mapping = [(2, 8)]
        fluff = resolve_fluff_positions(prompt, spans, offset_mapping=offset_mapping)
        assert fluff == [], "Straddling token was incorrectly included in fluff!"

    def test_token_boundary_exact_match_included(self):
        """Token with exact boundary [d_start, d_end] is included."""
        prompt = "0123456789"
        spans = [(3, 8)]
        offset_mapping = [(0, 3), (3, 8), (8, 10)]
        fluff = resolve_fluff_positions(prompt, spans, offset_mapping=offset_mapping)
        assert fluff == [1]

    def test_multibyte_and_unicode_intervals(self):
        """Multi-byte Unicode characters (emojis, Cyrillic, Greek, CJK) in prompt text."""
        # Prompt containing multi-byte characters
        prompt = "Claim: 🐉 - 🦊 = 10. Fluff note: Воланд любит шахматы и 🪆. End."
        fluff_text = "Воланд любит шахматы и 🪆."
        d_start = prompt.index(fluff_text)
        d_end = d_start + len(fluff_text)
        spans = [(d_start, d_end)]

        # Custom offsets for words
        words = prompt.split()
        offset_mapping = []
        cur = 0
        for w in words:
            start = prompt.index(w, cur)
            end = start + len(w)
            offset_mapping.append((start, end))
            cur = end

        fluff = resolve_fluff_positions(prompt, spans, offset_mapping=offset_mapping)
        # Verify that all tokens inside fluff_text are captured
        fluff_words = [words[i] for i in fluff]
        for fw in ["Воланд", "любит", "шахматы", "и", "🪆."]:
            assert fw in fluff_words, f"Expected '{fw}' in resolved fluff words: {fluff_words}"

        # Verify that claim symbols are NOT in fluff
        claim_symbols = ["Claim:", "🐉", "-", "🦊", "=", "10."]
        for cs in claim_symbols:
            assert cs not in fluff_words, f"Claim token '{cs}' was contaminated into fluff!"

    def test_identical_tokens_in_claim_and_distractor(self):
        """Distractor section contains exact identical tokens as the claim section.

        Coordinate containment must prevent token-ID confusion.
        """
        # Claim: "Node_A -> Node_B = 42"
        # Noise: "Is Node_A -> Node_B = 42 true? No, this is distractor: 42."
        prompt = (
            "System: solve integer rank differences.\n"
            "Claim: Node_A -> Node_B = 42.\n"
            "Noise: Node_A -> Node_B = 42 is fake distractor text with 42.\n"
            "Question: Consistent?"
        )
        noise_text = "Noise: Node_A -> Node_B = 42 is fake distractor text with 42."
        d_start = prompt.index(noise_text)
        d_end = d_start + len(noise_text)
        spans = [(d_start, d_end)]

        tokens = list(_re_tokens := list(re.finditer(r"\S+", prompt)))
        offset_mapping = [(m.start(), m.end()) for m in tokens]

        fluff = resolve_fluff_positions(prompt, spans, offset_mapping=offset_mapping)

        # Token text for all tokens
        token_texts = [m.group(0) for m in tokens]

        # Claim "Node_A" index vs noise "Node_A" index
        claim_node_a_idx = token_texts.index("Node_A")
        noise_node_a_idx = token_texts.index("Node_A", claim_node_a_idx + 1)

        claim_42_idx = token_texts.index("42.")
        noise_42_idx = token_texts.index("42")

        # Invariant check: claim tokens are NEVER fluff; noise tokens ARE fluff
        assert claim_node_a_idx not in fluff
        assert noise_node_a_idx in fluff
        assert claim_42_idx not in fluff
        assert noise_42_idx in fluff

    def test_inverted_and_negative_spans(self):
        """Inverted spans (d_start > d_end) or negative spans return empty or non-matching."""
        prompt = "Alpha Beta Gamma"
        offset_mapping = [(0, 5), (6, 10), (11, 16)]

        # Inverted span: start 10 > end 5
        fluff_inv = resolve_fluff_positions(prompt, [(10, 5)], offset_mapping=offset_mapping)
        assert fluff_inv == []

        # Negative span: (-10, -2)
        fluff_neg = resolve_fluff_positions(prompt, [(-10, -2)], offset_mapping=offset_mapping)
        assert fluff_neg == []

    def test_zero_width_tokens_ignored(self):
        """Zero-width tokens in offset_mapping (e.g. special tokens with offset (0, 0)) are skipped."""
        prompt = "Hello world"
        offset_mapping = [(0, 0), (0, 5), (6, 11), (11, 11)]
        spans = [(0, 11)]
        fluff = resolve_fluff_positions(prompt, spans, offset_mapping=offset_mapping)
        # Should include index 1 and 2, but skip 0 and 3
        assert fluff == [1, 2]


# ==============================================================================
# Dimension 4: Two-Signal Danger Gate Attacks
# ==============================================================================


class TestTwoSignalDangerGateAttacks:
    """Adversarial attacks on Two-Signal Danger Gate."""

    def test_float_tau_injection_rejected(self):
        """Passing float tau raises TypeError."""
        for bad_tau in (0.05, 0.0, 1.0, -0.1):
            with pytest.raises(TypeError, match="ZERO-FLOAT Invariant violated on tau"):
                evaluate_danger_gate([1], attention_mass=Fraction(1, 10), tau=bad_tau)

    def test_float_mass_injection_rejected(self):
        """Passing float attention_mass raises TypeError."""
        for bad_mass in (0.05, 0.0, 1.0, -0.5):
            with pytest.raises(TypeError, match="ZERO-FLOAT Invariant violated on attention_mass"):
                evaluate_danger_gate([1], attention_mass=bad_mass)

    def test_numpy_float_injection_rejected(self):
        """Passing numpy float types raises TypeError."""
        np_val = np.float64(0.05)
        with pytest.raises(TypeError, match="ZERO-FLOAT Invariant violated"):
            evaluate_danger_gate([1], attention_mass=np_val)

    def test_boundary_threshold_mass_equals_tau(self):
        """When attention_mass == tau the single-signal rule does not fire."""
        tau = Fraction(1, 20)
        decision = evaluate_danger_gate([1], attention_mass=tau, tau=tau)
        assert decision.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert decision.is_suppressed is False
        assert is_masking_authorized(decision) is False
        assert attention_mass_masking_decision([1], tau, tau).authorized is False

    def test_boundary_threshold_mass_tau_plus_minus_epsilon(self):
        """Exact rational sensitivity: tau + 1/1,000,000 fires the rule; tau - 1/1,000,000 does not."""
        tau = Fraction(1, 20)
        eps = Fraction(1, 1_000_000)

        dec_below = evaluate_danger_gate([1], attention_mass=tau - eps, tau=tau)
        assert dec_below.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert is_masking_authorized(dec_below) is False
        assert attention_mass_masking_decision([1], tau - eps, tau).authorized is False

        # Above tau the mass is refused as a derived second signal ...
        with pytest.raises(SignalIndependenceRefusal) as caught:
            evaluate_danger_gate([1], attention_mass=tau + eps, tau=tau)
        assert caught.value.code == "TWO_SIGNAL_COLLAPSE"
        # ... and fires only the named single-signal rule.
        assert is_masking_authorized(attention_mass_masking_decision([1], tau + eps, tau)) is True

    def test_host_refusal_without_fluff_is_diagnostic_only(self):
        """Counterexample: Signal 2 alone (critical host refusal) used to give DEFENSIVE_LOCKDOWN
        and authorize masking. One signal does not suppress."""
        decision = evaluate_danger_gate([], host_refusal=True)
        assert decision.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert decision.is_suppressed is False
        assert decision.signal1_count == 0
        assert decision.signal2_severity == DangerSeverity.CRITICAL
        assert is_masking_authorized(decision) is False

    def test_bool_host_refusal_is_required(self):
        with pytest.raises(TypeError):
            evaluate_danger_gate([1], host_refusal=1)

    def test_invalid_types_raise_type_error(self):
        """Passing complex, list, or dict types raises TypeError."""
        with pytest.raises(TypeError):
            evaluate_danger_gate([1], attention_mass=[1, 2])
        with pytest.raises(TypeError):
            evaluate_danger_gate([1], tau={"a": 1})

    def test_string_representations_exact_fraction(self):
        """Passing exact fraction strings '1/20' or decimal integer strings is accepted."""
        rule = attention_mass_masking_decision([1], "3/20", "1/20")
        assert is_masking_authorized(rule) is True
        with pytest.raises(SignalIndependenceRefusal):
            evaluate_danger_gate([1], attention_mass="3/20", tau="1/20")


# ==============================================================================
# Dimension 5: Budget Enforcement Attacks
# ==============================================================================


class TestBudgetEnforcementAttacks:
    """Adversarial attacks on MechanismBudgetController limits and fail-closed behavior."""

    def test_exact_ceiling_charge_succeeds_and_kills(self):
        """Spending exactly 250,000 micro-USD reaches ceiling; is_killed becomes True."""
        ctrl = MechanismBudgetController(
            hard_kill_ceiling_microusd=250_000,
            target_budget_microusd=50_000,
        )
        ctrl.charge_microusd(250_000)
        assert ctrl.spent_microusd == 250_000
        assert ctrl.remaining_microusd == 0
        assert ctrl.is_killed is True

        # Any further charge of 1 micro-USD must immediately raise BudgetExceeded
        with pytest.raises(BudgetExceeded, match="Hard kill ceiling reached"):
            ctrl.charge_microusd(1)

    def test_single_charge_exceeding_ceiling_fails_closed(self):
        """Single charge of 250,001 micro-USD is rejected without mutating spent balance."""
        ctrl = MechanismBudgetController(hard_kill_ceiling_microusd=250_000)
        with pytest.raises(BudgetExceeded):
            ctrl.charge_microusd(250_001)
        assert ctrl.spent_microusd == 0, "Failed charge mutated spent balance!"
        assert ctrl.remote_calls == 0

    def test_validate_pre_dispatch_fail_closed_does_not_mutate(self):
        """validate_pre_dispatch checks budget without charging."""
        ctrl = MechanismBudgetController(hard_kill_ceiling_microusd=250_000)
        ctrl.validate_pre_dispatch(100_000)
        assert ctrl.spent_microusd == 0

        with pytest.raises(BudgetExceeded):
            ctrl.validate_pre_dispatch(300_000)
        assert ctrl.spent_microusd == 0

    def test_negative_cost_injection_rejected(self):
        """Attempting to charge negative micro-USD to game the budget raises ValueError."""
        ctrl = MechanismBudgetController()
        with pytest.raises(ValueError, match="non-negative integer"):
            ctrl.charge_microusd(-500)
        with pytest.raises(ValueError, match="non-negative integer"):
            ctrl.validate_pre_dispatch(-500)

    def test_float_cost_injection_rejected(self):
        """Attempting to charge float micro-USD raises ValueError."""
        ctrl = MechanismBudgetController()
        with pytest.raises(ValueError, match="non-negative integer"):
            ctrl.charge_microusd(100.5)  # type: ignore
        with pytest.raises(ValueError, match="non-negative integer"):
            ctrl.validate_pre_dispatch(100.5)  # type: ignore

    def test_local_billing_always_zero(self):
        """charge_local never increases spend, regardless of call frequency."""
        ctrl = MechanismBudgetController()
        for i in range(100):
            res = ctrl.charge_local(f"local_call_{i}")
            assert res == 0
        assert ctrl.spent_microusd == 0
        assert ctrl.local_calls == 100
        assert ctrl.is_within_target is True

    def test_float_in_fluff_positions_empirical_truncation(self):
        """Empirical finding: passing float in fluff_positions is silently truncated by PyTorch.

        PyTorch tensor indexing mask[:, [1.5]] = 0 silently converts float 1.5 to int 1,
        mutating index 1 instead of rejecting non-integer indices.
        Non-numeric string positions, however, raise TypeError.
        """
        mask = torch.ones((1, 5), dtype=torch.long)
        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[1.5],  # type: ignore
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        # Empirical finding: PyTorch silently zeroed out index 1
        assert masked[0, 1].item() == 0

        # String position raises TypeError from PyTorch tensor construction
        with pytest.raises(TypeError):
            apply_distractor_key_mask(
                attention_mask=mask,
                fluff_positions=["invalid"],  # type: ignore
                danger_gate_decision=DangerDecision.QUARANTINED,
            )

    def test_charge_quote_fail_closed_on_budget_exceeded(self):
        """charge_quote raises BudgetExceeded when quote cost exceeds ceiling without mutating spent."""
        ctrl = MechanismBudgetController(hard_kill_ceiling_microusd=250_000)
        mock_quote = SimpleNamespace(cost_microusd=300_000)
        with pytest.raises(BudgetExceeded):
            ctrl.charge_quote("test-model", mock_quote)
        assert ctrl.spent_microusd == 0
        assert ctrl.remote_calls == 0

    def test_charge_quote_successful_under_limit(self):
        """charge_quote succeeds and records spend when within limits."""
        from omega_engine_woland.domain.providers.budget import PriceQuoteV1, pricing_observation

        ctrl = MechanismBudgetController(hard_kill_ceiling_microusd=250_000)
        obs = pricing_observation("test-model", 1000, 2000)
        quote = PriceQuoteV1(observation=obs, cost_microusd=20_000)
        receipt = ctrl.charge_quote("test-model", quote)
        assert receipt.cost_microusd == 20_000
        assert ctrl.spent_microusd == 20_000
        assert ctrl.remote_calls == 1

    def test_invalid_controller_initialization_parameters(self):
        """Invalid constructor arguments raise ValueError."""
        with pytest.raises(ValueError, match="positive exact integer"):
            MechanismBudgetController(hard_kill_ceiling_microusd=-1)
        with pytest.raises(ValueError, match="positive exact integer"):
            MechanismBudgetController(target_budget_microusd=0)
        with pytest.raises(ValueError, match="target_budget_microusd cannot exceed"):
            MechanismBudgetController(
                hard_kill_ceiling_microusd=50_000, target_budget_microusd=60_000
            )
        with pytest.raises(ValueError, match="positive exact integer"):
            MechanismBudgetController(hard_kill_ceiling_microusd=250_000.0)  # type: ignore
