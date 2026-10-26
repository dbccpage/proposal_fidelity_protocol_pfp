"""
test_m2_attention_hook.py — Targeted Unit Tests for Milestone 2 Attention Masking Hook.

Verifies:
1. Attention mask tensor zeroing across heads/layers (2D, 3D, 4D, 5D, layer lists).
2. Fixed position_ids invariant (torch.arange(seq_len) preserved, shifts rejected).
3. Character offset mapping without token-ID collisions (fluff tokens isolated by coordinate containment).
4. Two-Signal Danger Gate decisions under strict Zero-Float Law (fractions.Fraction, float raises TypeError).
5. BudgetController micro-USD tracking and ceiling enforcement (< $0.05 target, $0.25 hard kill ceiling).
6. F-null arm invariance (mask unchanged when fluff empty, intervention None, or gate unconfirmed).
7. Refusal on non-eager attention implementations (FlashAttention/vLLM/SDPA).
"""

from __future__ import annotations

from fractions import Fraction
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")

from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.attention_hook import (
    DEFAULT_DANGER_TAU,
    HARD_KILL_CEILING_MICROUSD,
    TARGET_BUDGET_MICROUSD,
    MechanismBudgetController,
    NonEagerAttentionRefusal,
    PositionIdsInvariantViolation,
    apply_distractor_key_mask,
    attention_mass_masking_decision,
    build_fixed_position_ids,
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
# 1. Attention Mask Zeroing Across Heads and Layers
# ==============================================================================


class TestAttentionMaskZeroing:
    """Tests zeroing of distractor key positions across 2D, 3D, 4D, and multi-layer masks."""

    def test_zeroing_2d_tensor(self):
        """2D mask [batch, seq_len] zeroed at specified fluff positions."""
        batch_size, seq_len = 2, 8
        mask = torch.ones((batch_size, seq_len), dtype=torch.long)
        fluff_positions = [2, 5]

        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=fluff_positions,
            danger_gate_decision=DangerDecision.QUARANTINED,
        )

        assert masked.shape == (batch_size, seq_len)
        for b in range(batch_size):
            for pos in range(seq_len):
                if pos in fluff_positions:
                    assert masked[b, pos].item() == 0
                else:
                    assert masked[b, pos].item() == 1

    def test_zeroing_3d_tensor(self):
        """3D mask [batch, query_len, key_len] zeroed at key positions across all queries."""
        batch_size, query_len, key_len = 2, 6, 6
        mask = torch.ones((batch_size, query_len, key_len), dtype=torch.long)
        fluff_positions = [1, 4]

        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=fluff_positions,
            danger_gate_decision=DangerDecision.DEFENSIVE_LOCKDOWN,
        )

        assert masked.shape == (batch_size, query_len, key_len)
        # All query rows must have 0 for keys 1 and 4
        assert (masked[:, :, [1, 4]] == 0).all()
        # Non-fluff keys remain 1
        assert (masked[:, :, [0, 2, 3, 5]] == 1).all()

    def test_zeroing_4d_tensor_across_all_heads(self):
        """4D mask [batch, heads, query_len, key_len] zeroed across ALL attention heads."""
        batch_size, num_heads, query_len, key_len = 2, 4, 8, 8
        mask = torch.ones((batch_size, num_heads, query_len, key_len), dtype=torch.long)
        fluff_positions = [3, 6]

        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=fluff_positions,
            danger_gate_decision=DangerDecision.QUARANTINED,
        )

        assert masked.shape == (batch_size, num_heads, query_len, key_len)
        # Every head, every query row has 0 for key positions 3 and 6
        for h in range(num_heads):
            assert (masked[:, h, :, [3, 6]] == 0).all()
            assert (masked[:, h, :, [0, 1, 2, 4, 5, 7]] == 1).all()

    def test_zeroing_5d_tensor_across_all_layers(self):
        """5D mask [layers, batch, heads, query_len, key_len] zeroed across ALL layers."""
        layers, batch, heads, seq = 6, 1, 2, 5
        mask = torch.ones((layers, batch, heads, seq, seq), dtype=torch.long)
        fluff_positions = [2]

        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=fluff_positions,
            danger_gate_decision=DangerDecision.QUARANTINED,
        )

        assert masked.shape == (layers, batch, heads, seq, seq)
        assert (masked[:, :, :, :, 2] == 0).all()
        assert (masked[:, :, :, :, [0, 1, 3, 4]] == 1).all()

    def test_zeroing_list_of_layer_masks(self):
        """List of per-layer masks (standard HF layer tuple/list) zeroed per layer."""
        num_layers = 12
        layers = [torch.ones((1, 4, 6, 6), dtype=torch.long) for _ in range(num_layers)]
        fluff_positions = [1, 3]

        masked_layers = apply_distractor_key_mask(
            attention_mask=layers,
            fluff_positions=fluff_positions,
            danger_gate_decision=DangerDecision.QUARANTINED,
        )

        assert len(masked_layers) == num_layers
        for l_idx, l_mask in enumerate(masked_layers):
            assert (l_mask[:, :, :, [1, 3]] == 0).all()
            assert (l_mask[:, :, :, [0, 2, 4, 5]] == 1).all()

    def test_floating_point_additive_mask(self):
        """Floating point additive mask sets masked positions to minimum finfo value."""
        mask = torch.zeros((1, 1, 6, 6), dtype=torch.float32)
        # Add negative bias to future positions (causal triangular)
        for i in range(6):
            for j in range(i + 1, 6):
                mask[0, 0, i, j] = -10000.0

        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[2],
            danger_gate_decision=DangerDecision.QUARANTINED,
        )

        min_val = torch.finfo(torch.float32).min
        assert (masked[:, :, :, 2] == min_val).all()


# ==============================================================================
# 2. Fixed Position IDs Invariant
# ==============================================================================


class TestPositionIdsInvariant:
    """Verifies that position_ids remain torch.arange(seq_len) and reject alterations."""

    def test_build_fixed_position_ids(self):
        """build_fixed_position_ids generates arange(seq_len) tensor."""
        pos = build_fixed_position_ids(seq_len=10, batch_size=2)
        assert pos.shape == (2, 10)
        expected = torch.arange(10).unsqueeze(0).expand(2, -1)
        assert torch.equal(pos, expected)

    def test_verify_position_ids_valid(self):
        """verify_position_ids_invariant succeeds on unaltered positions."""
        pos = torch.arange(12).unsqueeze(0)
        assert verify_position_ids_invariant(pos, seq_len=12) is True

    def test_verify_position_ids_shifted_fails(self):
        """Shifting or dropping token positions raises PositionIdsInvariantViolation."""
        shifted = torch.tensor([[0, 1, 2, 4, 5]])  # 3 dropped
        with pytest.raises(PositionIdsInvariantViolation, match="Position IDs altered"):
            verify_position_ids_invariant(shifted)

        permuted = torch.tensor([[1, 0, 2, 3]])
        with pytest.raises(PositionIdsInvariantViolation, match="Position IDs altered"):
            verify_position_ids_invariant(permuted)

    def test_apply_mask_preserves_position_ids_attribute(self):
        """Masked tensor attaches invariant position_ids equal to torch.arange(seq_len)."""
        mask = torch.ones((1, 8), dtype=torch.long)
        masked, pos_ids = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[2],
            danger_gate_decision=DangerDecision.QUARANTINED,
            return_position_ids=True,
        )
        assert hasattr(masked, "position_ids")
        expected = torch.arange(8).unsqueeze(0)
        assert torch.equal(pos_ids, expected)
        assert torch.equal(masked.position_ids, expected)

    def test_apply_mask_with_invalid_position_ids_raises(self):
        """Passing an altered position_ids tensor raises PositionIdsInvariantViolation."""
        mask = torch.ones((1, 5), dtype=torch.long)
        bad_pos = torch.tensor([[0, 1, 3, 4, 5]])
        with pytest.raises(PositionIdsInvariantViolation):
            apply_distractor_key_mask(
                attention_mask=mask,
                fluff_positions=[2],
                danger_gate_decision=DangerDecision.QUARANTINED,
                position_ids=bad_pos,
            )


# ==============================================================================
# 3. Character Offset Mapping Without Token-ID Collisions
# ==============================================================================


class TestCharacterOffsetMapping:
    """Verifies that distractor positions are resolved exclusively by coordinate containment."""

    def test_no_token_id_collision_on_identical_tokens(self):
        """Claim digit '7' is NOT masked even though distractor contains identical digit '7'."""
        prompt = "Claim: A - B = 7. Distractor note: 7 is a lucky number and giraffe is tall."
        # Character indices:
        # "Claim: A - B = 7." -> index 16 is the first '7'
        # Distractor span covers "Distractor note: 7 is a lucky number and giraffe is tall."
        d_start = prompt.index("Distractor note:")
        d_end = len(prompt)
        distractor_spans = [(d_start, d_end)]

        # Mock tokenization with offsets
        # Tokens: ["Claim:", "A", "-", "B", "=", "7.", "Distractor", "note:", "7", "is", "a", "lucky", "number", "and", "giraffe", "is", "tall."]
        words = prompt.split()
        offset_mapping = []
        cur = 0
        for w in words:
            start = prompt.index(w, cur)
            end = start + len(w)
            offset_mapping.append((start, end))
            cur = end

        # Locate which index has claim '7.' and which has distractor '7'
        claim_7_idx = words.index("7.")
        distractor_7_idx = [i for i, w in enumerate(words) if w == "7"][0]

        fluff_positions = resolve_fluff_positions(
            prompt_text=prompt,
            distractor_spans=distractor_spans,
            offset_mapping=offset_mapping,
        )

        # Invariant: Claim 7 is NOT in fluff, Distractor 7 IS in fluff
        assert claim_7_idx not in fluff_positions, (
            "Claim digit was incorrectly classified as distractor!"
        )
        assert distractor_7_idx in fluff_positions, "Distractor digit was not resolved!"

    def test_coordinate_containment_exact_boundaries(self):
        """Tokens inside [d_start, d_end] are included; outside or overlapping boundary are excluded."""
        text = "ABC DEF GHI JKL MNO"
        # Spans covering "DEF GHI" -> chars [4, 11]
        spans = [(4, 11)]
        offset_mapping = [(0, 3), (4, 7), (8, 11), (12, 15), (16, 19)]

        fluff = resolve_fluff_positions(text, spans, offset_mapping=offset_mapping)
        assert fluff == [1, 2]  # "DEF" and "GHI"

    def test_empty_distractor_spans_returns_empty(self):
        """Empty distractor spans returns empty fluff list."""
        fluff = resolve_fluff_positions("Any text here", distractor_spans=[])
        assert fluff == []

    def test_tokenizer_callable_integration(self):
        """Tokenizer callable returning offset_mapping is correctly queried."""

        class MockTokenizer:
            def __call__(self, text: str, return_offsets_mapping: bool = True):
                return {"offset_mapping": [(0, 5), (6, 10), (11, 15)]}

        spans = [(6, 10)]
        fluff = resolve_fluff_positions("alpha beta gamma", spans, tokenizer=MockTokenizer())
        assert fluff == [1]


# ==============================================================================
# 4. Two-Signal Danger Gate under Strict Zero-Float Law
# ==============================================================================


class TestTwoSignalDangerGate:
    """Verifies Two-Signal Danger Gate with exact rational Fraction arithmetic."""

    def test_zero_float_law_raises_on_float_mass(self):
        """Float attention_mass strictly raises TypeError under Zero-Float Law."""
        with pytest.raises(TypeError, match="ZERO-FLOAT Invariant violated"):
            evaluate_danger_gate(fluff_positions=[1], attention_mass=0.08)

    def test_zero_float_law_raises_on_float_tau(self):
        """Float tau strictly raises TypeError under Zero-Float Law."""
        with pytest.raises(TypeError, match="ZERO-FLOAT Invariant violated"):
            evaluate_danger_gate(fluff_positions=[1], attention_mass=Fraction(1, 10), tau=0.05)

    def test_gate_decision_tolerated_when_no_signals(self):
        """Neither Signal 1 nor Signal 2 -> TOLERATED, not suppressed."""
        decision = evaluate_danger_gate(
            fluff_positions=[],
            attention_mass=Fraction(0, 1),
            host_refusal=False,
        )
        assert decision.decision == DangerDecision.TOLERATED
        assert decision.is_suppressed is False
        assert is_masking_authorized(decision) is False

    def test_gate_decision_diagnostic_only_signal1_alone(self):
        """Signal 1 present, attention mass <= tau -> DIAGNOSTIC_ONLY."""
        decision = evaluate_danger_gate(
            fluff_positions=[2, 4],
            attention_mass=Fraction(1, 40),  # 0.025 <= 0.05
            tau=DEFAULT_DANGER_TAU,  # 1/20 = 0.05
            host_refusal=False,
        )
        assert decision.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert decision.is_suppressed is False
        assert is_masking_authorized(decision) is False

    def test_attention_mass_is_not_a_second_signal(self):
        """Counterexample: attention mass on the fluff positions used to be Signal 2.

        It is measured on the positions Signal 1 selected, so the old gate counted
        one signal twice and returned QUARANTINED. Now the gate refuses it.
        """
        with pytest.raises(SignalIndependenceRefusal) as caught:
            evaluate_danger_gate(
                fluff_positions=[2, 4],
                attention_mass=Fraction(3, 20),  # 0.15 > 0.05
                tau=DEFAULT_DANGER_TAU,
                host_refusal=False,
            )
        assert caught.value.code == "TWO_SIGNAL_COLLAPSE"
        # The experiment's rule is a named single-signal threshold instead.
        rule = attention_mass_masking_decision([2, 4], Fraction(3, 20), DEFAULT_DANGER_TAU)
        assert rule.authorized is True and rule.rule == "ATTENTION_MASS_THRESHOLD"
        assert is_masking_authorized(rule) is True

    def test_gate_decision_quarantined_host_refusal(self):
        """Signal 1 + an independent host refusal of the unmasked turn -> QUARANTINED."""
        decision = evaluate_danger_gate(
            fluff_positions=[1],
            attention_mass=Fraction(0, 1),
            host_refusal=True,
        )
        assert decision.decision == DangerDecision.QUARANTINED
        assert decision.is_suppressed is True
        assert decision.signal2_severity == DangerSeverity.CRITICAL
        assert is_masking_authorized(decision) is True

    def test_host_refusal_alone_does_not_authorize_masking(self):
        """Counterexample: Signal 2 alone at CRITICAL used to give DEFENSIVE_LOCKDOWN and mask."""
        decision = evaluate_danger_gate(fluff_positions=[], host_refusal=True)
        assert decision.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert is_masking_authorized(decision) is False

    def test_exact_rational_boundary_tau(self):
        """Exact rational comparison at boundary tau for the single-signal rule."""
        tau = Fraction(1, 20)
        # Exactly equal to tau: mass <= tau -> not triggered
        assert attention_mass_masking_decision([1], tau, tau).authorized is False
        assert (
            evaluate_danger_gate([1], attention_mass=tau, tau=tau).decision
            == DangerDecision.DIAGNOSTIC_ONLY
        )
        # tau + 1/10000 -> the rule fires; the gate refuses the derived signal
        assert (
            attention_mass_masking_decision([1], tau + Fraction(1, 10000), tau).authorized is True
        )
        with pytest.raises(SignalIndependenceRefusal):
            evaluate_danger_gate([1], attention_mass=tau + Fraction(1, 10000), tau=tau)
        # No detected positions: nothing to mask.
        assert attention_mass_masking_decision([], Fraction(1, 2), tau).authorized is False


# ==============================================================================
# 5. BudgetController Micro-USD Tracking and Ceiling Enforcement
# ==============================================================================


class TestBudgetControllerIntegration:
    """Verifies pre-dispatch budget control (< $0.05 target, $0.25 hard kill ceiling)."""

    def test_initial_budget_state(self):
        """Initial state has 0 spent, 250,000 remaining, within target."""
        ctrl = MechanismBudgetController()
        assert ctrl.spent_microusd == 0
        assert ctrl.remaining_microusd == HARD_KILL_CEILING_MICROUSD
        assert ctrl.target_budget_microusd == TARGET_BUDGET_MICROUSD
        assert ctrl.is_within_target is True
        assert ctrl.is_killed is False

    def test_local_pytorch_calls_bill_zero(self):
        """Local PyTorch hooks bill exactly 0 micro-USD ($0.00)."""
        ctrl = MechanismBudgetController()
        for _ in range(50):
            charged = ctrl.charge_local("local_qwen_mask_forward")
            assert charged == 0
        assert ctrl.spent_microusd == 0
        assert ctrl.local_calls == 50
        assert ctrl.is_within_target is True

    def test_target_spend_crossing(self):
        """Target spend < $0.05 (50,000 micro-USD) flagged when exceeded."""
        ctrl = MechanismBudgetController()
        ctrl.charge_microusd(40_000)
        assert ctrl.is_within_target is True
        assert ctrl.spent_microusd == 40_000

        ctrl.charge_microusd(15_000)
        assert ctrl.spent_microusd == 55_000
        assert ctrl.is_within_target is False  # Exceeded $0.05 target
        assert ctrl.is_killed is False  # Still below $0.25 ceiling

    def test_hard_kill_ceiling_enforcement(self):
        """Exceeding $0.25 hard kill ceiling (250,000 micro-USD) raises BudgetExceeded."""
        ctrl = MechanismBudgetController()
        ctrl.charge_microusd(240_000)
        assert ctrl.spent_microusd == 240_000
        assert ctrl.remaining_microusd == 10_000

        # Attempt to charge 15,000 micro-USD (projected 255,000 > 250,000)
        with pytest.raises(BudgetExceeded, match="Hard kill ceiling reached"):
            ctrl.charge_microusd(15_000)

        # Verify fail-closed state: spend remained at 240_000
        assert ctrl.spent_microusd == 240_000

    def test_validate_pre_dispatch_fail_closed(self):
        """Pre-dispatch validation halts prior to any external request."""
        ctrl = MechanismBudgetController()
        with pytest.raises(BudgetExceeded):
            ctrl.validate_pre_dispatch(300_000)


# ==============================================================================
# 6. F-Null Arm Invariance & Non-Eager Attention Refusal
# ==============================================================================


class TestFNullArmAndEagerRefusal:
    """Verifies baseline invariance under F-null conditions and eager attention refusal."""

    def test_f_null_empty_fluff_preserves_mask(self):
        """Empty fluff_positions leaves mask completely unchanged."""
        mask = torch.ones((1, 8), dtype=torch.long)
        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[],
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        assert torch.equal(masked, mask)

    def test_f_null_intervention_none_preserves_mask(self):
        """intervention=None leaves mask completely unchanged."""
        mask = torch.ones((1, 8), dtype=torch.long)
        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[2, 4],
            intervention=None,
            danger_gate_decision=DangerDecision.QUARANTINED,
        )
        assert torch.equal(masked, mask)

    def test_f_null_unauthorized_gate_preserves_mask(self):
        """DIAGNOSTIC_ONLY or TOLERATED gate decision leaves mask unchanged."""
        mask = torch.ones((1, 8), dtype=torch.long)
        masked = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[2, 4],
            danger_gate_decision=DangerDecision.DIAGNOSTIC_ONLY,
        )
        assert torch.equal(masked, mask)

        masked_tol = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[2, 4],
            danger_gate_decision=DangerDecision.TOLERATED,
        )
        assert torch.equal(masked_tol, mask)

    def test_f_null_danger_gate_decision_none_preserves_mask(self):
        """danger_gate_decision=None (missing gate evidence) leaves mask completely unchanged."""
        mask = torch.ones((1, 8), dtype=torch.long)
        masked_none = apply_distractor_key_mask(
            attention_mask=mask,
            fluff_positions=[2, 4],
            danger_gate_decision=None,
        )
        assert torch.equal(masked_none, mask)

    def test_refuses_non_eager_attention_string(self):
        """attn_implementation != 'eager' raises NonEagerAttentionRefusal."""
        mask = torch.ones((1, 4), dtype=torch.long)
        for non_eager in ("flash_attention_2", "sdpa", "vllm"):
            with pytest.raises(NonEagerAttentionRefusal, match="attn_implementation='eager'"):
                apply_distractor_key_mask(
                    attention_mask=mask,
                    fluff_positions=[1],
                    attn_implementation=non_eager,
                )

    def test_refuses_non_eager_model_config(self):
        """Model with non-eager config raises NonEagerAttentionRefusal."""
        mock_model = SimpleNamespace(
            config=SimpleNamespace(_attn_implementation="flash_attention_2")
        )
        mask = torch.ones((1, 4), dtype=torch.long)
        with pytest.raises(NonEagerAttentionRefusal, match="attn_implementation='eager'"):
            apply_distractor_key_mask(
                model=mock_model,
                attention_mask=mask,
                fluff_positions=[1],
            )
