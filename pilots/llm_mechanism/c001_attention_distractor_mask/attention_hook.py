"""
attention_hook.py — Distractor-Key Attention Masking Hook and Two-Signal Danger Gate.

Implements Milestone 2 requirements for Symbol Game Mechanism Challenge C001:
1. Attention Mask Intervention (`apply_distractor_key_mask`):
   - Accepts 2D/3D/4D/5D attention mask, prompt token IDs, distractor token positions (`fluff_positions`),
     and danger gate decision.
   - Zeroes attention mask at `fluff_positions` across layers and heads for intervened keys.
   - Strictly enforces that `position_ids` remain unchanged (`position_ids = torch.arange(seq_len)`
     or integer list invariant).
   - F-null arm validation: when `fluff_positions` is empty, or intervention is None, or the
     decision does not authorize masking, the mask is unchanged and preserves baseline output exactly.
   - Refuses non-eager attention (requires `attn_implementation="eager"`; raises NonEagerAttentionRefusal
     on fused kernels like FlashAttention, SDPA, vLLM).
2. Character Offset Mapping integration:
   - `resolve_fluff_positions(prompt_text, distractor_spans, tokenizer=None, offset_mapping=None)`:
     Ensures coordinate containment (`d_start <= t_start and t_end <= d_end`) without any token-ID matching.
3. Masking decisions (corrected 2026-09-29):
   - `evaluate_danger_gate` uses the Epistemic Immune System's two-signal gate
     (`eis.domain.danger_gate.TwoSignalDangerGate.evaluate_independent`).
     Signal 1 is the distractor-span detector (`len(fluff_positions) > 0`). The only independent
     Signal 2 is a host verifier's refusal of the unmasked turn (`host_refusal=True`, observed by
     `c001-host-verifier`). Signal 2 alone does not authorize masking.
   - The distractor attention mass is measured on the very positions Signal 1 selected, so it cannot
     be a second signal: `evaluate_danger_gate` refuses it as TWO_SIGNAL_COLLAPSE
     (`SignalIndependenceRefusal`) when it exceeds tau and no host refusal is given.
   - `attention_mass_masking_decision` is the experiment's single-signal rule, named as such: mask
     when the distractor attention mass exceeds tau. It makes no two-signal claim.
   - Strict Zero-Float Law: uses `fractions.Fraction` for all ratios and thresholds (floats raise TypeError).
4. Pre-dispatch Budget Controller:
   - Integrates with `adversary.domain.providers.budget.BudgetController`.
   - Sets target spend < $0.05 (50,000 micro-USD) and hard kill ceiling $0.25 (250,000 micro-USD).
   - Local PyTorch/Python solvers bill 0 micro-USD ($0.00). Any remote route is validated fail-closed prior to dispatch.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import re
from fractions import Fraction
from typing import Any, List, Optional, Sequence, Tuple, Union

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

from eis.domain.danger_gate import (
    DangerEvaluationResult,
    TwoSignalDangerGate,
)
from eis.domain.danger_signals import (
    SignalIndependenceRefusal,
)
from eis.domain.value_objects import (
    DangerDecision,
    DangerSeverity,
    Signal1Match,
    Signal2Danger,
)
from adversary.domain.providers.budget import BudgetController
from adversary.domain.providers.types import BudgetExceeded, BudgetReceipt

# Canonical budget limits in integer micro-USD
TARGET_BUDGET_MICROUSD: int = 50_000  # $0.05 target spend
HARD_KILL_CEILING_MICROUSD: int = 250_000  # $0.25 hard kill ceiling
DEFAULT_DANGER_TAU: Fraction = Fraction(1, 20)  # tau = 0.05 in exact rational
DISTRACTOR_DETECTOR_ID = "c001-distractor-span-resolver"
HOST_VERIFIER_OBSERVER_ID = "c001-host-verifier"
_MASKING_DECISIONS = (DangerDecision.QUARANTINED, DangerDecision.DEFENSIVE_LOCKDOWN)


class NonEagerAttentionRefusal(ValueError):
    """Refusal raised when attention implementation is not 'eager' (e.g. FlashAttention/vLLM)."""


class PositionIdsInvariantViolation(ValueError):
    """Raised when position_ids invariant is violated (shifted, compressed, or altered positions)."""


def _assert_zero_float(val: Any, field_name: str) -> None:
    """Strictly enforces Zero-Float Law: floats raise TypeError."""
    if isinstance(val, float):
        raise TypeError(
            f"ZERO-FLOAT Invariant violated on {field_name}: float values are strictly forbidden; "
            "use fractions.Fraction or Q"
        )


def resolve_fluff_positions(
    prompt_text: str,
    distractor_spans: Sequence[Tuple[int, int]],
    tokenizer: Any = None,
    offset_mapping: Any = None,
) -> List[int]:
    """Resolves distractor token positions via character coordinate containment.

    STRICT INVARIANT: Token-ID matching is strictly prohibited!
    Tokens are identified purely by character coordinate containment:
    d_start <= t_start and t_end <= d_end, with t_start < t_end.

    Args:
        prompt_text: Full prompt string.
        distractor_spans: Sequence of (start_char, end_char) intervals.
        tokenizer: Optional tokenizer instance.
        offset_mapping: Optional precomputed list of (start, end) offsets or torch.Tensor.

    Returns:
        Sorted list of unique token position indices contained within distractor spans.
    """
    if not distractor_spans:
        return []

    # 1. Use explicit offset_mapping if provided
    raw_mapping = offset_mapping

    # 2. Otherwise query tokenizer if provided
    if raw_mapping is None and tokenizer is not None:
        if callable(tokenizer):
            try:
                enc = tokenizer(prompt_text, return_offsets_mapping=True)
                if isinstance(enc, dict) and "offset_mapping" in enc:
                    raw_mapping = enc["offset_mapping"]
                elif hasattr(enc, "offset_mapping"):
                    raw_mapping = getattr(enc, "offset_mapping")
            except Exception:
                pass

    # 3. Process raw_mapping if found
    if raw_mapping is not None:
        if torch is not None and isinstance(raw_mapping, torch.Tensor):
            raw_mapping = raw_mapping.tolist()

        # Handle batch dimension if present (e.g. [[(0, 5), (6, 10)]])
        if (
            isinstance(raw_mapping, (list, tuple))
            and len(raw_mapping) > 0
            and isinstance(raw_mapping[0], (list, tuple))
            and len(raw_mapping[0]) > 0
            and isinstance(raw_mapping[0][0], (list, tuple))
        ):
            raw_mapping = raw_mapping[0]

        fluff_positions: List[int] = []
        for idx, span in enumerate(raw_mapping):
            if not isinstance(span, (list, tuple)) or len(span) < 2:
                continue
            t_start, t_end = span[0], span[1]
            if t_start >= t_end:
                # Skip zero-width tokens or special tokens with offset (0, 0)
                continue
            if any(d_start <= t_start and t_end <= d_end for d_start, d_end in distractor_spans):
                fluff_positions.append(idx)
        return sorted(list(set(fluff_positions)))

    # 4. Fallback: regex non-whitespace tokenizer
    tokens = list(re.finditer(r"\S+", prompt_text))
    fluff_positions = []
    for idx, match in enumerate(tokens):
        t_start, t_end = match.start(), match.end()
        if any(d_start <= t_start and t_end <= d_end for d_start, d_end in distractor_spans):
            fluff_positions.append(idx)
    return sorted(list(set(fluff_positions)))


def build_fixed_position_ids(
    seq_len: int,
    batch_size: int = 1,
    device: Any = None,
    dtype: Any = None,
) -> Any:
    """Constructs invariant position_ids: position_ids = torch.arange(seq_len)."""
    if torch is not None:
        pos = torch.arange(seq_len, device=device, dtype=dtype or torch.long)
        if batch_size > 1:
            return pos.unsqueeze(0).expand(batch_size, -1)
        return pos.unsqueeze(0)
    return [list(range(seq_len)) for _ in range(batch_size)]


def verify_position_ids_invariant(position_ids: Any, seq_len: Optional[int] = None) -> bool:
    """Verifies that position_ids strictly follow the arange(seq_len) invariant.

    Raises:
        PositionIdsInvariantViolation: if position_ids are shifted, altered, or non-monotonic.
    """
    if position_ids is None:
        raise PositionIdsInvariantViolation(
            "position_ids is None; fixed position_ids are required."
        )

    if torch is not None and isinstance(position_ids, torch.Tensor):
        if seq_len is not None and position_ids.shape[-1] != seq_len:
            raise PositionIdsInvariantViolation(
                f"Position IDs length mismatch: expected {seq_len}, got {position_ids.shape[-1]}"
            )
        # Check against torch.arange along the last dimension
        expected_len = position_ids.shape[-1]
        expected = torch.arange(expected_len, device=position_ids.device, dtype=position_ids.dtype)
        if position_ids.ndim == 2:
            for b in range(position_ids.shape[0]):
                if not torch.equal(position_ids[b], expected):
                    raise PositionIdsInvariantViolation(
                        f"Position IDs altered at batch {b}: expected {expected.tolist()}, "
                        f"got {position_ids[b].tolist()}"
                    )
        elif position_ids.ndim == 1:
            if not torch.equal(position_ids, expected):
                raise PositionIdsInvariantViolation(
                    f"Position IDs altered: expected {expected.tolist()}, got {position_ids.tolist()}"
                )
        return True

    if isinstance(position_ids, (list, tuple)):
        # Handle 1D or 2D list
        if len(position_ids) > 0 and isinstance(position_ids[0], (list, tuple)):
            for b, row in enumerate(position_ids):
                expected = list(range(len(row)))
                if seq_len is not None and len(row) != seq_len:
                    raise PositionIdsInvariantViolation(
                        f"Position IDs length mismatch at batch {b}: expected {seq_len}, got {len(row)}"
                    )
                if list(row) != expected:
                    raise PositionIdsInvariantViolation(
                        f"Position IDs altered at batch {b}: expected {expected}, got {list(row)}"
                    )
        else:
            expected = list(range(len(position_ids)))
            if seq_len is not None and len(position_ids) != seq_len:
                raise PositionIdsInvariantViolation(
                    f"Position IDs length mismatch: expected {seq_len}, got {len(position_ids)}"
                )
            if list(position_ids) != expected:
                raise PositionIdsInvariantViolation(
                    f"Position IDs altered: expected {expected}, got {list(position_ids)}"
                )
        return True

    raise PositionIdsInvariantViolation(
        f"Unsupported position_ids type: {type(position_ids).__name__}"
    )


def _exact(value: Any, field_name: str) -> Fraction:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be Fraction, int, or str, got bool")
    if isinstance(value, (int, str)):
        return Fraction(value)
    if isinstance(value, Fraction):
        return value
    if hasattr(value, "num") and hasattr(value, "den"):
        return Fraction(getattr(value, "num"), getattr(value, "den"))
    raise TypeError(f"{field_name} must be Fraction, int, or str, got {type(value).__name__}")


def evaluate_danger_gate(
    fluff_positions: Sequence[int],
    attention_mass: Union[Fraction, int, str, None] = None,
    host_refusal: bool = False,
    tau: Union[Fraction, int, str] = DEFAULT_DANGER_TAU,
    evidence_digest: str = "sha256:" + "0" * 64,
) -> DangerEvaluationResult:
    """The OEEIS two-signal gate for one turn, with an independent Signal 2 only.

    Signal 1: the distractor-span detector found positions (`len(fluff_positions) > 0`).
    Signal 2: a host verifier refused the unmasked turn (`host_refusal=True`).

    The distractor attention mass is measured on the positions Signal 1 selected,
    so it is not independent of Signal 1. When it exceeds tau and there is no host
    refusal, the gate refuses with `SignalIndependenceRefusal` (TWO_SIGNAL_COLLAPSE)
    rather than report two signals. Use `attention_mass_masking_decision` for the
    experiment's single-signal masking rule.

    Returns:
        The OEEIS DangerEvaluationResult.
    """
    _assert_zero_float(attention_mass, "attention_mass")
    _assert_zero_float(tau, "tau")
    tau_frac = _exact(tau, "tau")
    mass_frac: Optional[Fraction] = None
    if attention_mass is not None:
        mass_frac = _exact(attention_mass, "attention_mass")
    if type(host_refusal) is not bool:
        raise TypeError("host_refusal must be an exact bool")

    signal1_matches: List[Signal1Match] = []
    if len(fluff_positions) > 0:
        signal1_matches.append(
            Signal1Match(
                epitope_name="distractor_fluff_span",
                pattern_matched=f"{len(fluff_positions)} distractor tokens",
                confidence=1.0,
                offset=int(fluff_positions[0]),
            )
        )

    signal2: Optional[Signal2Danger] = None
    if host_refusal:
        signal2 = Signal2Danger(
            danger_type="REPLAY_FAILURE",
            severity=DangerSeverity.CRITICAL,
            defect_count=1,
            evidence_digest=evidence_digest,
            observer_id=HOST_VERIFIER_OBSERVER_ID,
        )
    elif mass_frac is not None and mass_frac > tau_frac:
        raise SignalIndependenceRefusal(
            "TWO_SIGNAL_COLLAPSE",
            f"the distractor attention mass {mass_frac} > tau {tau_frac} is measured on the "
            "fluff positions Signal 1 selected; it cannot be the second signal",
        )

    return TwoSignalDangerGate.evaluate_independent(
        signal1_matches,
        signal2,
        detector_id=DISTRACTOR_DETECTOR_ID,
        detector_predicates=frozenset(),
        offsets_are_content=False,
    )


class MaskingDecision:
    """A single-signal masking decision. It is not a two-signal immune decision."""

    __slots__ = ("authorized", "rule", "rationale")

    def __init__(self, authorized: bool, rule: str, rationale: str) -> None:
        if type(authorized) is not bool:
            raise TypeError("authorized must be an exact bool")
        self.authorized = authorized
        self.rule = rule
        self.rationale = rationale

    def __repr__(self) -> str:
        return f"MaskingDecision(authorized={self.authorized!r}, rule={self.rule!r})"


def attention_mass_masking_decision(
    fluff_positions: Sequence[int],
    attention_mass: Union[Fraction, int, str],
    tau: Union[Fraction, int, str] = DEFAULT_DANGER_TAU,
) -> MaskingDecision:
    """The experiment's rule: mask when the distractor attention mass exceeds tau.

    One signal (the attention mass on the detected distractor positions),
    compared exactly. Named as a threshold rule, not a danger gate.
    """
    _assert_zero_float(attention_mass, "attention_mass")
    _assert_zero_float(tau, "tau")
    if attention_mass is None:
        raise TypeError("attention_mass is required")
    tau_frac = _exact(tau, "tau")
    mass_frac = _exact(attention_mass, "attention_mass")
    authorized = len(fluff_positions) > 0 and mass_frac > tau_frac
    return MaskingDecision(
        authorized=authorized,
        rule="ATTENTION_MASS_THRESHOLD",
        rationale=(
            f"single signal: distractor attention mass {mass_frac} "
            f"{'>' if mass_frac > tau_frac else '<='} tau {tau_frac} on "
            f"{len(fluff_positions)} detected position(s); not a two-signal immune decision"
        ),
    )


def is_masking_authorized(
    decision: Union[DangerEvaluationResult, MaskingDecision, DangerDecision, str, None],
) -> bool:
    """Whether a decision authorizes distractor-key masking.

    An OEEIS gate result authorizes masking only when it is QUARANTINED or
    DEFENSIVE_LOCKDOWN (both signals present); a `MaskingDecision` when its
    single-signal rule fired.
    """
    if decision is None:
        return False
    if isinstance(decision, MaskingDecision):
        return decision.authorized
    if isinstance(decision, DangerEvaluationResult):
        return decision.decision in _MASKING_DECISIONS
    if isinstance(decision, DangerDecision):
        return decision in _MASKING_DECISIONS
    if isinstance(decision, str):
        return decision.upper() in ("QUARANTINED", "DEFENSIVE_LOCKDOWN")
    return False


def apply_distractor_key_mask(
    attention_mask_or_model: Any = None,
    prompt_token_ids: Any = None,
    attention_mask: Any = None,
    fluff_positions: Sequence[int] = (),
    danger_gate_decision: Union[
        DangerEvaluationResult, MaskingDecision, DangerDecision, str, None
    ] = None,
    *,
    model: Any = None,
    input_ids: Any = None,
    intervention: Optional[str] = "distractor_key_mask",
    attn_implementation: str = "eager",
    position_ids: Any = None,
    mask_value: Any = None,
    inplace: bool = False,
    return_position_ids: bool = False,
) -> Any:
    """Applies distractor-key attention masking across heads and layers on eager attention.

    Invariants:
    1. Zeroes attention mask at fluff_positions across layers and heads for intervened keys.
    2. Strictly enforces that position_ids remain unchanged (torch.arange(seq_len)).
    3. F-null arm validation: when fluff_positions is empty, intervention is None, or danger gate
       decision is not in (QUARANTINED, DEFENSIVE_LOCKDOWN), mask is unchanged and preserves
       baseline output exactly.
    4. Refuses non-eager attention (requires attn_implementation="eager"; raises NonEagerAttentionRefusal
       on FlashAttention/vLLM).

    Args:
        attention_mask_or_model: 2D/3D/4D/5D mask tensor or HuggingFace model.
        prompt_token_ids: Optional sequence of token IDs.
        attention_mask: Optional explicit attention mask tensor if model passed as first arg.
        fluff_positions: Sequence of distractor token positions to mask.
        danger_gate_decision: Danger gate decision (mask applied only if QUARANTINED or DEFENSIVE_LOCKDOWN).
        model: Optional model instance.
        input_ids: Optional alias for prompt_token_ids.
        intervention: Intervention name ("distractor_key_mask" or None for F-null arm).
        attn_implementation: Attention implementation string (must be "eager").
        position_ids: Optional position_ids tensor to verify against the fixed arange invariant.
        mask_value: Value used to zero keys (defaults to 0 or finfo min for float additive masks).
        inplace: If True, modifies attention_mask in-place; else clones.
        return_position_ids: If True, returns (masked_attention_mask, position_ids).

    Returns:
        Masked attention_mask tensor (with .position_ids attached), or (mask, position_ids) if return_position_ids=True.
    """
    # 1. Resolve model & check attention implementation
    actual_model = model
    actual_mask = attention_mask

    if actual_model is None and attention_mask_or_model is not None:
        if hasattr(attention_mask_or_model, "config") or hasattr(
            attention_mask_or_model, "parameters"
        ):
            actual_model = attention_mask_or_model
        else:
            if actual_mask is None:
                actual_mask = attention_mask_or_model

    if (
        actual_mask is None
        and attention_mask_or_model is not None
        and actual_model is not attention_mask_or_model
    ):
        actual_mask = attention_mask_or_model

    # Check model config for non-eager implementation
    if actual_model is not None and hasattr(actual_model, "config"):
        cfg = getattr(actual_model, "config")
        cfg_impl = getattr(cfg, "_attn_implementation", None) or getattr(
            cfg, "attn_implementation", None
        )
        if cfg_impl is not None and cfg_impl != "eager":
            raise NonEagerAttentionRefusal(
                f"Refusal: Distractor-key attention masking requires attn_implementation='eager', "
                f"got '{cfg_impl}' in model config. Fused kernels (FlashAttention, SDPA, vLLM) cannot zero individual keys."
            )

    # Check explicit attn_implementation argument
    if attn_implementation != "eager":
        raise NonEagerAttentionRefusal(
            f"Refusal: Distractor-key attention masking requires attn_implementation='eager', "
            f"got '{attn_implementation}'. Fused kernels (FlashAttention, SDPA, vLLM) cannot zero individual keys."
        )

    if actual_mask is None:
        raise ValueError("attention_mask must be provided (got None)")

    # 2. Determine sequence length
    seq_len = 0
    if torch is not None and isinstance(actual_mask, torch.Tensor):
        seq_len = actual_mask.shape[-1]
    elif isinstance(actual_mask, (list, tuple)):
        curr = actual_mask
        while (
            isinstance(curr, (list, tuple)) and len(curr) > 0 and isinstance(curr[0], (list, tuple))
        ):
            curr = curr[0]
        seq_len = len(curr)

    # 3. Position IDs verification and construction
    if position_ids is not None:
        verify_position_ids_invariant(position_ids, seq_len=seq_len)
        effective_position_ids = position_ids
    else:
        if torch is not None and isinstance(actual_mask, torch.Tensor):
            batch_size = actual_mask.shape[0] if actual_mask.ndim >= 2 else 1
            effective_position_ids = (
                torch.arange(
                    seq_len,
                    dtype=torch.long,
                    device=actual_mask.device,
                )
                .unsqueeze(0)
                .expand(batch_size, -1)
            )
        else:
            effective_position_ids = list(range(seq_len))

    # 4. F-null arm and Gate Authorization checks
    # Condition A: intervention is None or "none" -> baseline arm
    if intervention is None or str(intervention).lower() == "none":
        if torch is not None and isinstance(actual_mask, torch.Tensor):
            try:
                actual_mask.position_ids = effective_position_ids
            except Exception:
                pass
        if return_position_ids:
            return actual_mask, effective_position_ids
        return actual_mask

    # Condition B: fluff_positions is empty -> baseline output preserved
    if not fluff_positions or len(fluff_positions) == 0:
        if torch is not None and isinstance(actual_mask, torch.Tensor):
            try:
                actual_mask.position_ids = effective_position_ids
            except Exception:
                pass
        if return_position_ids:
            return actual_mask, effective_position_ids
        return actual_mask

    # Condition C: Gate Authorization - masking strictly requires affirmative danger gate authorization
    # When danger_gate_decision is None or unauthorized, the mask remains unedited (baseline / F-null)
    if not is_masking_authorized(danger_gate_decision):
        if torch is not None and isinstance(actual_mask, torch.Tensor):
            try:
                actual_mask.position_ids = effective_position_ids
            except Exception:
                pass
        if return_position_ids:
            return actual_mask, effective_position_ids
        return actual_mask

    # 5. Apply Zeroing Intervention
    mask_to_edit = (
        actual_mask
        if inplace
        else (
            actual_mask.clone()
            if (torch is not None and isinstance(actual_mask, torch.Tensor))
            else copy.deepcopy(actual_mask)
        )
    )

    fluff_indices = list(fluff_positions)

    if torch is not None and isinstance(mask_to_edit, torch.Tensor):
        # Determine appropriate zero/mask value
        if mask_value is not None:
            val = mask_value
        elif torch.is_floating_point(mask_to_edit) and (mask_to_edit < 0).any():
            val = torch.finfo(mask_to_edit.dtype).min
        elif torch.is_floating_point(mask_to_edit):
            val = 0.0
        else:
            val = 0

        # Zero key positions based on tensor dimensionality
        # 1D: [seq_len]
        if mask_to_edit.ndim == 1:
            mask_to_edit[fluff_indices] = val
        # 2D: [batch, seq_len]
        elif mask_to_edit.ndim == 2:
            mask_to_edit[:, fluff_indices] = val
        # 3D: [batch, query, key] or [batch, heads, seq]
        elif mask_to_edit.ndim == 3:
            mask_to_edit[:, :, fluff_indices] = val
        # 4D: [batch, heads, query, key] or [batch, 1, query, key]
        elif mask_to_edit.ndim == 4:
            mask_to_edit[:, :, :, fluff_indices] = val
        # 5D: [layers, batch, heads, query, key]
        elif mask_to_edit.ndim == 5:
            mask_to_edit[:, :, :, :, fluff_indices] = val
        else:
            mask_to_edit[..., fluff_indices] = val

        try:
            mask_to_edit.position_ids = effective_position_ids
        except Exception:
            pass

    elif isinstance(mask_to_edit, (list, tuple)):
        # List of layer masks or nested list
        if len(mask_to_edit) > 0 and isinstance(
            mask_to_edit[0], (torch.Tensor if torch else (), list, tuple)
        ):
            for layer_mask in mask_to_edit:
                apply_distractor_key_mask(
                    attention_mask=layer_mask,
                    fluff_positions=fluff_positions,
                    danger_gate_decision=danger_gate_decision,
                    intervention=intervention,
                    attn_implementation=attn_implementation,
                    position_ids=position_ids,
                    mask_value=mask_value,
                    inplace=True,
                    return_position_ids=False,
                )
        else:
            # 1D list of ints/floats
            for p in fluff_indices:
                if 0 <= p < len(mask_to_edit):
                    mask_to_edit[p] = 0

    if return_position_ids:
        return mask_to_edit, effective_position_ids
    return mask_to_edit


class MechanismBudgetController:
    """Pre-dispatch budget controller enforcing sub-$0.05 target and $0.25 hard kill ceiling.

    Integrates with adversary.domain.providers.budget.BudgetController.
    - Local PyTorch/Python solvers bill exactly 0 micro-USD ($0.00).
    - Remote routes validate budget fail-closed prior to dispatch.
    - Breaches above hard_kill_ceiling_microusd raise BudgetExceeded.
    """

    def __init__(
        self,
        hard_kill_ceiling_microusd: int = HARD_KILL_CEILING_MICROUSD,
        target_budget_microusd: int = TARGET_BUDGET_MICROUSD,
    ) -> None:
        if type(hard_kill_ceiling_microusd) is not int or hard_kill_ceiling_microusd <= 0:
            raise ValueError("hard_kill_ceiling_microusd must be a positive exact integer")
        if type(target_budget_microusd) is not int or target_budget_microusd <= 0:
            raise ValueError("target_budget_microusd must be a positive exact integer")
        if target_budget_microusd > hard_kill_ceiling_microusd:
            raise ValueError("target_budget_microusd cannot exceed hard_kill_ceiling_microusd")

        self._hard_ceiling: int = hard_kill_ceiling_microusd
        self._target: int = target_budget_microusd
        self._inner_controller: BudgetController = BudgetController(
            limit_microusd=hard_kill_ceiling_microusd
        )
        self._local_calls: int = 0
        self._remote_calls: int = 0
        self._manual_spent_microusd: int = 0

    @property
    def hard_kill_ceiling_microusd(self) -> int:
        return self._hard_ceiling

    @property
    def target_budget_microusd(self) -> int:
        return self._target

    @property
    def spent_microusd(self) -> int:
        return self._inner_controller.spent_microusd + self._manual_spent_microusd

    @property
    def remaining_microusd(self) -> int:
        return max(0, self._hard_ceiling - self.spent_microusd)

    @property
    def local_calls(self) -> int:
        return self._local_calls

    @property
    def remote_calls(self) -> int:
        return self._remote_calls

    @property
    def is_within_target(self) -> bool:
        return self.spent_microusd < self._target

    @property
    def is_killed(self) -> bool:
        return self.spent_microusd >= self._hard_ceiling

    @property
    def inner_controller(self) -> BudgetController:
        return self._inner_controller

    def charge_local(self, description: str = "local_pytorch_eager_hook") -> int:
        """Charges a local PyTorch/Python solver invocation at exactly 0 micro-USD ($0.00)."""
        self.validate_pre_dispatch(0)
        self._local_calls += 1
        return 0

    def validate_pre_dispatch(self, cost_microusd: int) -> None:
        """Fail-closed pre-dispatch check. Raises BudgetExceeded before dispatch if ceiling breached."""
        if type(cost_microusd) is not int or cost_microusd < 0:
            raise ValueError("cost_microusd must be a non-negative integer")
        projected = self.spent_microusd + cost_microusd
        if projected > self._hard_ceiling:
            raise BudgetExceeded(
                requested=projected,
                limit=self._hard_ceiling,
                message=(
                    f"Hard kill ceiling reached: projected spend {projected} micro-USD "
                    f"exceeds ceiling {self._hard_ceiling} micro-USD ($0.25 ceiling)"
                ),
            )

    def charge_microusd(self, cost_microusd: int, route: str = "remote_route") -> int:
        """Pre-validates and charges cost in micro-USD. Raises BudgetExceeded if ceiling exceeded."""
        self.validate_pre_dispatch(cost_microusd)
        self._manual_spent_microusd += cost_microusd
        self._remote_calls += 1
        return self.spent_microusd

    def charge_quote(self, model: str, quote: Any) -> BudgetReceipt:
        """Delegates to internal BudgetController.charge with PriceQuoteV1."""
        cost = quote.cost_microusd
        self.validate_pre_dispatch(cost)
        receipt = self._inner_controller.charge(model, quote)
        self._remote_calls += 1
        return receipt
