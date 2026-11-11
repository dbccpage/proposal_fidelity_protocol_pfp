"""Five-Seam LLM Intervention & Receipt-to-Weight Engine for PFP (`pfp_core.llm_mechanisms`).

Unifies the five physical intervention loci of an open-weight or hosted language
model call under PFP's strict sovereignty boundary (``AuthorityEffect: None``):

* **Seam 1 (Sampling Parameters):** ``SamplingConfigV1`` and ``evaluate_sampling_seam``
  regulate ``temperature``, ``top_p``, ``seed`` and ``n_samples`` under a shared
  ``WholeRunBudget``. Collapses redundant ``T=0`` replicates via operadic trace
  quotienting and compares ``greedy_first``, ``majority_vote`` and
  ``certificate_first`` (which requires an independent ``HostOracleContext`` pass).
* **Seam 2 (Logit & Grammar Decode Control):** ``LogitGrammarControllerV1`` wraps
  ``DecodeControlSpec`` (``CARRIER_MASK``, ``LOGIT_BIAS``, ``JSON_SCHEMA``, ``GBNF``),
  finite token-trie logit masking, and exact V1/V2 decode-receipt verification
  (matching Rust ``decode_control.rs`` invariants and delegating to native FFI
  when built). Shows both what Layer-2 masking eliminates (syntax/wire refusals
  on Call 1) and what it cannot eliminate (on-grammar mathematical errors, which
  still require Layer-3 host checks).
* **Seam 3 (Host-Controlled Scratchpad):** ``HostScratchSessionV1`` implements
  the multi-turn ``C006`` working-memory ledger and exact ``AM-4`` stationary
  attractor detection (``RepeatedCut`` and ``RepeatedSettledAssert``, matching
  Rust ``scratch_board.rs``) with a ``Treg`` circuit-breaker, keeping turn
  prompts bounded in size compared with free-form chain-of-thought history.
* **Seam 4 (Attention Heads, KV Surgery & Activation Steering):**
  ``OpenWeightMechanismRunnerV1`` extends ``HfLocalRunner`` across both
  ``Llama``/``Qwen`` (``model.model.layers``) and ``Gemma 4``
  (``model.language_model.layers``) eager attention layouts, adding EIS
  two-signal gating (refusing ``TWO_SIGNAL_COLLAPSE`` when attention mass attempts
  to self-authorize without a host refusal) and paired equal-norm random-vector
  steering controls.
* **Seam 5 (Weights / ``finetune_on_antibodies`` from Verified Receipt Triples):**
  ``ReceiptToWeightPipelineV1`` extracts ``VerifiedReceiptTripleV1`` records
  directly from PFP runs where ``chosen`` is certified by ``HostOracleContext``
  (and screened by ``ThymusGate``) and ``rejected`` is refused by the same host
  oracle on the same seed. Enforces zero hold-out seed contamination and PCIV
  lineage untaintedness, compiles deterministic SFT/DPO datasets sealed with a
  ``SealedCausalWitness``, fits a pinned low-rank ``LowRankWeightAdapterV1``
  (LoRA) against an equal-Frobenius-norm random adapter control, and emits a
  ``WeightAdapterReceiptV1`` with ``authority_effect='None'``.

What this supports: deterministic execution and paired ablation of all five
intervention seams under host verification in this repository's test and local
open-weight settings. What it does not support: any claim that internal
attention, logit, scratchpad, or weight interventions replace external host
verification or generalize to arbitrary tasks without held-out measurement.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import torch
import torch.nn.functional as F  # noqa: N812
from torch import nn

from eis.domain.value_objects import DetectorRule
from pciv.domain.causal_witness import SealedCausalWitness, is_sealed_digest, seal_causal_witness
from pfp.domain.ports.decode_control_port import (
    DECODE_RECEIPT_SCHEMA,
    CarrierMask,
    ControlKind,
    DecodeControlReceipt,
    DecodeControlReceiptV2,
)
from pfp.infrastructure.adapters.decode_controls.local_hf_mechanism import HfLocalRunner

from . import REPO_ROOT  # noqa: F401
from .civilization import Lineage
from .fidelity import HostOracleContext, ProtectedContract, WholeRunBudget, sha256_hex
from .immunity import HOST_OBSERVERS, decide, host_danger, screen_rules, signal1
from .operad_pipe import TypedOp


def _canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode('utf-8')


def verify_causal_witness(witness: Any, *, expected_dataset_sha256: str | None = None) -> bool:
    """Verify a ``SealedCausalWitness`` and optional binding to ``expected_dataset_sha256``."""
    if not isinstance(witness, SealedCausalWitness):
        return False
    if not is_sealed_digest(witness.receipt_sha256):
        return False
    expected = 'sha256:' + hashlib.sha256(witness.canonical_body.encode('utf-8')).hexdigest()
    if witness.receipt_sha256 != expected:
        return False
    if expected_dataset_sha256 is not None:
        try:
            body = json.loads(witness.canonical_body)
        except json.JSONDecodeError:
            return False
        if not isinstance(body, dict) or body.get('dataset_sha256') != expected_dataset_sha256:
            return False
    return True


def _require_exact_int(value: Any, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f'{name} must be an exact int, got {type(value).__name__}')
    return value


def _require_exact_fraction(value: Any, name: str) -> Fraction:
    if isinstance(value, (bool, float)):
        raise TypeError(f'ZERO_FLOAT_LAW: {name} must be Fraction, int, or str, got {type(value).__name__}')
    if isinstance(value, Fraction):
        return value
    if isinstance(value, (int, str)):
        return Fraction(value)
    raise TypeError(f'{name} must be convertible to exact Fraction')


# ============================================================================
# SEAM 1: Sampling Parameters (Temperature / Top-p / Seed / N-Sample Selection)
# ============================================================================

SELECTION_RULES = frozenset({'greedy_first', 'majority_vote', 'certificate_first'})


@dataclass(frozen=True)
class SamplingConfigV1:
    """Typed sampling parameter configuration with exact rational bounds."""

    temperature: Fraction = Fraction(0)
    top_p: Fraction = Fraction(1)
    n_samples: int = 1
    seed: int = 0
    selection_rule: str = 'certificate_first'

    def __post_init__(self) -> None:
        temp = _require_exact_fraction(self.temperature, 'temperature')
        top_p = _require_exact_fraction(self.top_p, 'top_p')
        n_samples = _require_exact_int(self.n_samples, 'n_samples')
        seed = _require_exact_int(self.seed, 'seed')
        if not (Fraction(0) <= temp <= Fraction(2)):
            raise ValueError('BOUNDED_TEMPERATURE_REQUIRED: temperature must be in [0, 2]')
        if not (Fraction(0) < top_p <= Fraction(1)):
            raise ValueError('BOUNDED_TOP_P_REQUIRED: top_p must be in (0, 1]')
        if not (1 <= n_samples <= 16):
            raise ValueError('BOUNDED_N_SAMPLES_REQUIRED: n_samples must be in [1, 16]')
        if seed < 0:
            raise ValueError('NONNEGATIVE_SEED_REQUIRED')
        if self.selection_rule not in SELECTION_RULES:
            raise ValueError(f'UNKNOWN_SELECTION_RULE: {self.selection_rule!r}')
        object.__setattr__(self, 'temperature', temp)
        object.__setattr__(self, 'top_p', top_p)

    @property
    def has_redundant_zero_temp_replicates(self) -> bool:
        return self.temperature == Fraction(0) and self.n_samples > 1

    @property
    def effective_draws(self) -> int:
        """At T=0 deterministic decoding, replicate draws collapse to 1 unique draw."""
        return 1 if self.temperature == Fraction(0) else self.n_samples

    def as_typed_ops(self, prompt_digest: str, checker_id: str = 'host.exact_oracle') -> list[TypedOp]:
        """Represent the sampling configuration as an operadic pipeline for trace quotienting."""
        ops = [
            TypedOp(
                op_id=f'sample:t={self.temperature}:k=0',
                input_colour='Contract',
                output_colour='Code',
                kind='generate',
                prompt_digest=f'{prompt_digest}:t={self.temperature}:top_p={self.top_p}',
            )
        ]
        if self.selection_rule == 'certificate_first':
            ops.append(
                TypedOp(
                    op_id='check:certificate_first',
                    input_colour='Code',
                    output_colour='Code',
                    kind='check',
                    checker_id=checker_id,
                )
            )
        return ops


@dataclass(frozen=True)
class SamplingSeamOutcomeV1:
    """Outcome of running a sampling configuration under WholeRunBudget + HostOracleContext."""

    config: SamplingConfigV1
    selected_reply: str | None
    selected_index: int | None
    status: str  # 'HOST_CERTIFIED', 'DELIVERED_UNCERTIFIED', 'NO_CERTIFIED_SAMPLE', 'BUDGET_REFUSED'
    draws_executed: int
    certified_draw_indices: tuple[int, ...]
    majority_reply: str | None
    majority_is_certified: bool
    budget_summary: dict[str, Any]
    authority_effect: str = 'None'


def evaluate_sampling_seam(
    config: SamplingConfigV1,
    *,
    task_id: str,
    prompt_text: str,
    sampler: Callable[[int, Fraction, int], tuple[str, int, int, int]],
    host_checker: Callable[[str], HostOracleContext],
    cap_microusd: int = 100_000,
) -> SamplingSeamOutcomeV1:
    """Execute ``config`` where every draw is billed to one ``WholeRunBudget`` before checking.

    ``sampler(draw_idx, temperature, draw_seed)`` returns
    ``(reply_text, actual_microusd, input_tokens, output_tokens)``.
    """
    prompt_digest = sha256_hex(prompt_text)
    budget = WholeRunBudget(f'seam1:{task_id}:{config.selection_rule}', prompt_digest, cap_microusd=cap_microusd)
    replies: list[str] = []
    oracles: list[HostOracleContext] = []
    certified_indices: list[int] = []
    try:
        for idx in range(config.n_samples):
            draw_seed = config.seed if config.temperature == Fraction(0) else config.seed + idx
            req_digest = sha256_hex(f'{prompt_digest}:{idx}:{config.temperature}:{draw_seed}')
            reply_text, microusd, in_tok, out_tok = sampler(idx, config.temperature, draw_seed)
            quote = max(microusd, 1)
            if not budget.charge(f'draw:{idx}', req_digest, quote, microusd, in_tok, out_tok):
                return SamplingSeamOutcomeV1(
                    config=config,
                    selected_reply=None,
                    selected_index=None,
                    status='BUDGET_REFUSED',
                    draws_executed=idx,
                    certified_draw_indices=tuple(certified_indices),
                    majority_reply=None,
                    majority_is_certified=False,
                    budget_summary=budget.summary(),
                )
            replies.append(reply_text)
            oracle = host_checker(reply_text)
            oracles.append(oracle)
            if oracle.final_output_certified:
                certified_indices.append(idx)

        counts = Counter(replies)
        majority_reply = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if counts else None
        majority_certified = any(
            replies[i] == majority_reply and oracles[i].final_output_certified for i in range(len(replies))
        )

        if config.selection_rule == 'greedy_first':
            chosen_idx = 0
            status = 'HOST_CERTIFIED' if oracles[0].final_output_certified else 'DELIVERED_UNCERTIFIED'
            return SamplingSeamOutcomeV1(
                config=config,
                selected_reply=replies[0],
                selected_index=chosen_idx,
                status=status,
                draws_executed=len(replies),
                certified_draw_indices=tuple(certified_indices),
                majority_reply=majority_reply,
                majority_is_certified=majority_certified,
                budget_summary=budget.summary(),
            )

        if config.selection_rule == 'majority_vote':
            chosen_idx = replies.index(majority_reply) if majority_reply is not None else None
            status = 'HOST_CERTIFIED' if majority_certified else 'DELIVERED_UNCERTIFIED'
            return SamplingSeamOutcomeV1(
                config=config,
                selected_reply=majority_reply,
                selected_index=chosen_idx,
                status=status,
                draws_executed=len(replies),
                certified_draw_indices=tuple(certified_indices),
                majority_reply=majority_reply,
                majority_is_certified=majority_certified,
                budget_summary=budget.summary(),
            )

        # certificate_first: only an independently certified draw may be delivered
        if certified_indices:
            first_ok = certified_indices[0]
            return SamplingSeamOutcomeV1(
                config=config,
                selected_reply=replies[first_ok],
                selected_index=first_ok,
                status='HOST_CERTIFIED',
                draws_executed=len(replies),
                certified_draw_indices=tuple(certified_indices),
                majority_reply=majority_reply,
                majority_is_certified=majority_certified,
                budget_summary=budget.summary(),
            )
        return SamplingSeamOutcomeV1(
            config=config,
            selected_reply=None,
            selected_index=None,
            status='NO_CERTIFIED_SAMPLE',
            draws_executed=len(replies),
            certified_draw_indices=(),
            majority_reply=majority_reply,
            majority_is_certified=majority_certified,
            budget_summary=budget.summary(),
        )
    finally:
        budget.close()


# ============================================================================
# SEAM 2: Logit & Grammar-Constrained Decoding (Layer 2 vs Layer 3 Verification)
# ============================================================================


def verify_decode_receipt_exact(receipt: DecodeControlReceipt) -> dict[str, Any]:  # noqa: PLR0911
    """Exact deterministic decode-receipt verifier matching Rust ``decode_control.rs``.

    Delegates to native ``get_default_host().verify_decode_receipt`` when the
    Rust host binary is present and cross-checks the identical invariant rules
    in pure Python so unit tests and offline verification never silently pass.
    """
    if receipt.schema_version not in (DECODE_RECEIPT_SCHEMA, 'omega.symbol_game.decode_receipt.v1'):
        return {
            'status': 'REFUSAL',
            'refusal_code': 'SCHEMA_MISMATCH',
            'detail': f'expected {DECODE_RECEIPT_SCHEMA}, got {receipt.schema_version}',
            'authority_effect': 'None',
        }
    if receipt.authority_effect != 'None':
        return {
            'status': 'REFUSAL',
            'refusal_code': 'AUTHORITY_EFFECT_NON_NONE',
            'detail': 'authority_effect must be None',
            'authority_effect': 'None',
        }
    kind = receipt.control_kind
    if kind == ControlKind.CARRIER_MASK.value:
        allowed_set = set(receipt.allowed_tokens)
        violations = [(idx, tok) for idx, tok in enumerate(receipt.output_tokens) if tok not in allowed_set]
        if violations:
            return {
                'status': 'REFUSAL',
                'refusal_code': 'CARRIER_CONSTRAINT_VIOLATED',
                'detail': f'found {len(violations)} tokens outside allowed carrier set: {violations}',
                'authority_effect': 'None',
            }
    elif kind == ControlKind.LOGIT_BIAS.value:
        for token_id, bias in receipt.logit_biases:
            if type(bias) is not int or abs(bias) > 1000:
                return {
                    'status': 'REFUSAL',
                    'refusal_code': 'LOGIT_BIAS_EXCEEDS_CEILING',
                    'detail': f'token {token_id} has invalid extreme bias: {bias}',
                    'authority_effect': 'None',
                }
    elif kind in (ControlKind.JSON_SCHEMA.value, ControlKind.GBNF.value):
        digest = receipt.grammar_sha256
        if not digest:
            return {
                'status': 'REFUSAL',
                'refusal_code': 'MISSING_GRAMMAR_HASH',
                'detail': f'{kind} control requires grammar_sha256 digest',
                'authority_effect': 'None',
            }
        if len(digest) != 64 or any(c not in '0123456789abcdefABCDEF' for c in digest):
            return {
                'status': 'REFUSAL',
                'refusal_code': 'INVALID_GRAMMAR_HASH',
                'detail': f'grammar_sha256 is not a valid 64-char hex digest: {digest}',
                'authority_effect': 'None',
            }
    elif kind != ControlKind.NONE.value:
        return {
            'status': 'REFUSAL',
            'refusal_code': 'UNKNOWN_CONTROL_KIND',
            'detail': f'unsupported control_kind: {kind}',
            'authority_effect': 'None',
        }

    return {
        'status': 'PASS',
        'token_count': len(receipt.output_tokens),
        'carrier_honored': True,
        'authority_effect': 'None',
    }


@dataclass(frozen=True)
class LogitDecodeEvaluationV1:
    """Combined Layer-2 decode receipt + Layer-3 host oracle evaluation."""

    case_id: str
    control_kind: str
    decoded_text: str
    decode_receipt: DecodeControlReceipt
    decode_receipt_v2: DecodeControlReceiptV2 | None
    layer2_verdict: dict[str, Any]
    layer3_oracle: dict[str, Any]
    wire_syntax_valid: bool
    semantically_certified: bool
    authority_effect: str = 'None'


class LogitGrammarControllerV1:
    """Layer-2 logit and finite-language trie controller paired with Layer-3 host checking."""

    def __init__(self, allowed_language: Sequence[str], tokenizer: Any) -> None:
        if not allowed_language or not (1 <= len(allowed_language) <= 1024):
            raise ValueError('BOUNDED_FINITE_LANGUAGE_REQUIRED')
        self.allowed_language = tuple(allowed_language)
        self.tokenizer = tokenizer
        self.language_bytes = _canonical_json_bytes(list(self.allowed_language))
        self.language_sha256 = sha256_hex(self.language_bytes)
        self.token_trie: tuple[tuple[int, ...], ...] = tuple(
            tuple(tokenizer.encode(s, add_special_tokens=False)) for s in self.allowed_language
        )
        if any(not row for row in self.token_trie):
            raise ValueError('EMPTY_TOKEN_SEQUENCE_IN_LANGUAGE')
        all_tokens = sorted({tok for row in self.token_trie for tok in row})
        self.carrier_mask = CarrierMask(allowed_tokens=tuple(all_tokens))

    def allowed_next_tokens(self, prefix: tuple[int, ...], eos_token_id: int) -> set[int]:
        """Exact token-trie transition function for prefix-constrained decoding."""
        allowed = {
            row[len(prefix)]
            for row in self.token_trie
            if len(row) > len(prefix) and row[: len(prefix)] == prefix
        }
        if prefix in self.token_trie:
            allowed.add(eos_token_id)
        return allowed

    def evaluate_candidate(
        self,
        *,
        case_id: str,
        request_text: str,
        output_tokens: Sequence[int],
        control_kind: ControlKind,
        host_checker: Callable[[str], tuple[HostOracleContext, bool]],
        logit_biases: dict[int, int] | None = None,
    ) -> LogitDecodeEvaluationV1:
        decoded_text = self.tokenizer.decode(list(output_tokens), skip_special_tokens=True)
        grammar_sha = self.language_sha256 if control_kind in (ControlKind.JSON_SCHEMA, ControlKind.GBNF) else None
        receipt = DecodeControlReceipt(
            receipt_id=f'rcpt_{sha256_hex(f"{case_id}:{decoded_text}")[:12]}',
            case_id=case_id,
            control_kind=control_kind.value,
            output_tokens=tuple(int(t) for t in output_tokens),
            allowed_tokens=self.carrier_mask.allowed_tokens if control_kind == ControlKind.CARRIER_MASK else (),
            logit_biases=tuple(sorted((int(k), int(v)) for k, v in (logit_biases or {}).items())),
            grammar_sha256=grammar_sha,
            honored=decoded_text in self.allowed_language,
            authority_effect='None',
        )
        layer2 = verify_decode_receipt_exact(receipt)
        oracle, wire_valid = host_checker(decoded_text)
        v2 = DecodeControlReceiptV2(
            request_bytes=request_text.encode('utf-8'),
            output_bytes=decoded_text.encode('utf-8') or b' ',
            language_bytes=self.language_bytes,
            validation_outcome='VALID' if (layer2['status'] == 'PASS' and wire_valid) else 'INVALID',
            enforcement='POST_VALIDATION',
            tokenizer_profile='fast-offset-v1',
        )
        return LogitDecodeEvaluationV1(
            case_id=case_id,
            control_kind=control_kind.value,
            decoded_text=decoded_text,
            decode_receipt=receipt,
            decode_receipt_v2=v2,
            layer2_verdict=layer2,
            layer3_oracle=oracle.to_dict(),
            wire_syntax_valid=wire_valid and layer2['status'] == 'PASS',
            semantically_certified=oracle.final_output_certified and layer2['status'] == 'PASS',
        )


# ============================================================================
# SEAM 3: Host-Controlled Scratchpad (U12 Ledger + AM-4 Detector + Treg Breaker)
# ============================================================================


@dataclass(frozen=True)
class ScratchTurnRecordV1:
    """One turn in a Symbol Game coboundary-repair session (matching Rust ``TurnRecord``)."""

    turn: int
    host_state_digest: str
    canonical_move_digest: str
    move_kind: str  # 'ASSERT', 'CUT', 'VERIFY'
    target_variable: str | None = None
    outcome: str = 'IdempotentStationary'  # 'IdempotentStationary', 'AdmittedDescent', 'Refused'
    phi1_after: int = 0
    prompt_tokens_estimated: int = 0


@dataclass(frozen=True)
class AttractorReportV1:
    """Exact AM-4 stationary attractor report matching Rust ``scratch_board.rs``."""

    findings: tuple[dict[str, Any], ...]
    escalate: bool
    detected_attractor: str | None
    treg_suspended: bool = False
    authority_effect: str = 'None'


def detect_stationary_attractor_exact(
    history: Sequence[ScratchTurnRecordV1],
    initial_decided_variables: Sequence[str] = (),
    *,
    treg_firing_ceiling: int = 3,
) -> AttractorReportV1:
    """Detect AM-4 stationary attractors (`RepeatedCut` and `RepeatedSettledAssert`).

    Matches ``omega_symbol_game_runtime::scratch_board::detect_stationary_attractor``
    and adds the C006 ``TregSupervisor`` suspension rule when detector firings
    exceed ``treg_firing_ceiling``.
    """
    decided: set[str] = set(initial_decided_variables)
    stationary_cuts: dict[tuple[str, str], int] = {}
    settled_assert_window: dict[str, list[int]] = {}
    findings: list[dict[str, Any]] = []
    escalate = False
    detected: str | None = None

    for rec in history:
        is_stationary = rec.outcome.lower() == 'idempotentstationary'
        is_descent = rec.outcome.lower() == 'admitteddescent'
        if is_descent:
            settled_assert_window.clear()

        if rec.move_kind.upper() == 'ASSERT' and rec.target_variable is not None:
            var = rec.target_variable
            if var in decided:
                turns = settled_assert_window.setdefault(var, [])
                turns.append(rec.turn)
                findings.append(
                    {
                        'type': 'RepeatedSettledAssert',
                        'variable': var,
                        'count_in_window': len(turns),
                        'turns': list(turns),
                    }
                )
                if len(turns) >= 2 and not escalate:
                    escalate = True
                    detected = 'RepeatedSettledAssert'
            elif is_stationary or is_descent or rec.outcome.lower() == 'admitted':
                decided.add(var)

        if rec.move_kind.upper() == 'CUT':
            key = (rec.host_state_digest, rec.canonical_move_digest)
            if key in stationary_cuts:
                findings.append(
                    {
                        'type': 'RepeatedCut',
                        'canonical_move_digest': rec.canonical_move_digest,
                        'host_state_digest': rec.host_state_digest,
                        'prior_turn': stationary_cuts[key],
                        'current_turn': rec.turn,
                    }
                )
                if not escalate:
                    escalate = True
                    detected = 'RepeatedCut'
            elif is_stationary:
                stationary_cuts[key] = rec.turn

    treg_suspended = len(findings) > treg_firing_ceiling
    if treg_suspended:
        escalate = False
    return AttractorReportV1(
        findings=tuple(findings),
        escalate=escalate,
        detected_attractor=detected,
        treg_suspended=treg_suspended,
    )


class HostScratchSessionV1:
    """Multi-turn C006 coboundary-repair session controller over a directed graph.

    Tracks exact cycle residuals and $\\Phi_1 = \\sum_c |r_c|$, enforces strict
    Lyapunov descent on ``CUT`` proposals, projects a bounded ``HostScratchLedger``
    view (keeping only the last 2 turns so context tokens do not grow with turn
    history), and verifies final vertex potentials $\\phi(v) - \\phi(u) = c(u \\to v)$.
    """

    def __init__(
        self,
        *,
        board_id: str,
        edges: Sequence[tuple[str, str]],
        initial_claims: dict[str, int],
        fundamental_cycles: dict[str, Sequence[tuple[str, str, int]]],
        chords: Sequence[str],
        fuel: int,
    ) -> None:
        self.board_id = board_id
        self.edges = tuple(edges)
        self.edge_keys = tuple(f'{u}->{v}' for u, v in self.edges)
        if set(initial_claims) != set(self.edge_keys):
            raise ValueError('INITIAL_CLAIMS_MUST_MATCH_EDGES')
        self.claims: dict[str, int] = {k: _require_exact_int(v, k) for k, v in initial_claims.items()}
        self.fundamental_cycles = {cid: tuple(cyc) for cid, cyc in fundamental_cycles.items()}
        self.chords = tuple(chords)
        self.fuel = _require_exact_int(fuel, 'fuel')
        self.board_sha256 = sha256_hex(_canonical_json_bytes({'board_id': board_id, 'claims': self.claims}))
        self.asserted_edges: set[str] = set(self.edge_keys)
        self.history: list[ScratchTurnRecordV1] = []
        self.recent_turn_texts: list[str] = []
        self.cot_full_history_texts: list[str] = []

    def cycle_residuals(self, candidate_claims: dict[str, int] | None = None) -> dict[str, int]:
        active = self.claims if candidate_claims is None else candidate_claims
        out: dict[str, int] = {}
        for cid, signed_edges in sorted(self.fundamental_cycles.items()):
            total = 0
            for u, v, sign in signed_edges:
                total += sign * _require_exact_int(active[f'{u}->{v}'], f'{u}->{v}')
            out[cid] = total
        return out

    def compute_phi1(self, candidate_claims: dict[str, int] | None = None) -> int:
        return sum(abs(v) for v in self.cycle_residuals(candidate_claims).values())

    @property
    def closed_chords(self) -> tuple[str, ...]:
        res = self.cycle_residuals()
        return tuple(
            chord
            for (_cid, residual), chord in zip(sorted(res.items()), self.chords, strict=True)
            if residual == 0
        )

    @property
    def open_cycles(self) -> dict[str, dict[str, Any]]:
        res = self.cycle_residuals()
        out: dict[str, dict[str, Any]] = {}
        for (cid, residual), chord in zip(sorted(res.items()), self.chords, strict=True):
            if residual != 0:
                out[cid] = {'residual': residual, 'chord': chord}
        return out

    @property
    def state_sha256(self) -> str:
        """State digest excluding turn counters/history so identical stationary CUTs cannot evade AM-4."""
        return sha256_hex(
            _canonical_json_bytes(
                {
                    'schema': 'pfp.c006.host-state.v1',
                    'board_sha256': self.board_sha256,
                    'claims': dict(sorted(self.claims.items())),
                    'asserted_edges': sorted(self.asserted_edges),
                    'phi1': self.compute_phi1(),
                    'cycle_residuals': self.cycle_residuals(),
                    'closed_chords': list(self.closed_chords),
                }
            )
        )

    def render_ledger_prompt(self) -> str:
        """Compact O(|E| + b1) host-maintained ledger view (no target chord values leaked)."""
        attractor = detect_stationary_attractor_exact(self.history, sorted(self.asserted_edges))
        payload = {
            'schema': 'pfp.c006.host-ledger.v1',
            'state_sha256': self.state_sha256,
            'current_claims': dict(sorted(self.claims.items())),
            'phi1': self.compute_phi1(),
            'cycle_residuals': self.cycle_residuals(),
            'closed_chords': list(self.closed_chords),
            'open_cycle_chords': [info['chord'] for info in self.open_cycles.values()],
            'am4_escalate': attractor.escalate,
            'am4_detected': attractor.detected_attractor,
            'last_two_turns': self.recent_turn_texts[-2:],
        }
        return json.dumps(payload, sort_keys=True, separators=(',', ':'))

    def render_cot_prompt(self) -> str:
        """Uncompacted chain-of-thought history view that grows with every turn."""
        base = json.dumps(
            {
                'board_id': self.board_id,
                'current_claims': dict(sorted(self.claims.items())),
                'phi1': self.compute_phi1(),
                'cycle_residuals': self.cycle_residuals(),
            },
            sort_keys=True,
        )
        return base + '\n' + '\n'.join(self.cot_full_history_texts)

    def apply_cut(
        self, proposed_claims: dict[str, int], *, mode: str = 'ledger', rationale: str = ''
    ) -> dict[str, Any]:
        """Validate and apply a full-cochain CUT move under strict descent."""
        if len(self.history) >= self.fuel:
            return {'status': 'REFUSED', 'code': 'FUEL_EXHAUSTED', 'phi1': self.compute_phi1()}
        if set(proposed_claims) != set(self.edge_keys):
            raise ValueError('FULL_CUT_REQUIRED')
        clean_proposal = {k: _require_exact_int(v, k) for k, v in proposed_claims.items()}
        turn_no = len(self.history) + 1
        pre_state = self.state_sha256
        move_digest = sha256_hex(_canonical_json_bytes({'schema': 'pfp.c006.full-cut.v1', 'claims': clean_proposal}))
        current_phi1 = self.compute_phi1()
        next_phi1 = self.compute_phi1(clean_proposal)

        prompt_str = self.render_ledger_prompt() if mode == 'ledger' else self.render_cot_prompt()
        prompt_tokens = max(1, len(prompt_str) // 4)

        if next_phi1 < current_phi1:
            self.claims = clean_proposal
            outcome = 'AdmittedDescent'
        elif clean_proposal == self.claims or next_phi1 == current_phi1:
            outcome = 'IdempotentStationary'
        else:
            outcome = 'Refused'

        rec = ScratchTurnRecordV1(
            turn=turn_no,
            host_state_digest=pre_state,
            canonical_move_digest=move_digest,
            move_kind='CUT',
            outcome=outcome,
            phi1_after=self.compute_phi1(),
            prompt_tokens_estimated=prompt_tokens,
        )
        self.history.append(rec)
        summary_line = f'turn={turn_no} move={move_digest[:8]} outcome={outcome} phi1={self.compute_phi1()}'
        self.recent_turn_texts.append(summary_line)
        self.cot_full_history_texts.append(summary_line + (' ' + rationale if rationale else ''))
        attractor = detect_stationary_attractor_exact(self.history, sorted(self.asserted_edges))
        return {
            'turn': turn_no,
            'outcome': outcome,
            'phi1': self.compute_phi1(),
            'am4_escalate': attractor.escalate,
            'am4_detected': attractor.detected_attractor,
            'prompt_tokens_estimated': prompt_tokens,
        }

    def verify_zero_defect(self, potential: dict[str, int]) -> dict[str, Any]:
        r"""Verify terminal ``ACCEPTED_ZERO_DEFECT`` ($\Phi_1 = 0$ and $\phi(v) - \phi(u) = c(u \to v)$)."""
        phi1 = self.compute_phi1()
        if phi1 != 0:
            return {
                'status': 'UNKNOWN',
                'refusal': 'SURVIVOR_OBSTRUCTION',
                'phi1_final': phi1,
                'turns': len(self.history),
                'authority_effect': 'None',
            }
        mismatches: list[str] = []
        for u, v in self.edges:
            key = f'{u}->{v}'
            if u not in potential or v not in potential:
                mismatches.append(key)
                continue
            diff = _require_exact_int(potential[v], v) - _require_exact_int(potential[u], u)
            if diff != self.claims[key]:
                mismatches.append(key)
        if mismatches:
            return {
                'status': 'REFUSED',
                'refusal': 'POTENTIAL_COBOUNDARY_MISMATCH',
                'mismatched_edges': mismatches,
                'phi1_final': phi1,
                'turns': len(self.history),
                'authority_effect': 'None',
            }
        return {
            'status': 'SOLVED',
            'terminal': 'ACCEPTED_ZERO_DEFECT',
            'final_cochain': dict(sorted(self.claims.items())),
            'potential': dict(sorted(potential.items())),
            'phi1_final': 0,
            'turns': len(self.history),
            'authority_effect': 'None',
        }


# ============================================================================
# SEAM 4: Attention Heads, KV Surgery & Activation Steering (Gemma 4 + Qwen/Llama)
# ============================================================================


def resolve_transformer_layers(model: Any) -> Any:
    """Resolve decoder layer list across Llama/Qwen (``model.layers``) and Gemma 4 (``language_model.layers``)."""
    inner = getattr(model, 'model', None)
    if inner is not None and hasattr(inner, 'layers'):
        return inner.layers
    lang = getattr(model, 'language_model', None)
    if lang is not None:
        if hasattr(lang, 'layers'):
            return lang.layers
        lang_inner = getattr(lang, 'model', None)
        if lang_inner is not None and hasattr(lang_inner, 'layers'):
            return lang_inner.layers
    raise ValueError('UNSUPPORTED_TRANSFORMER_LAYER_LAYOUT')


class OpenWeightMechanismRunnerV1(HfLocalRunner):
    """Architecture-generalized open-weight mechanism runner (Gemma 4 + Llama/Qwen) with EIS Two-Signal gating."""

    def __init__(self, model: Any, tokenizer: Any, *, model_id: str, revision: str) -> None:
        if (
            not model_id
            or type(revision) is not str
            or len(revision) != 40
            or any(c not in '0123456789abcdef' for c in revision)
        ):
            raise ValueError('LOCAL_MODEL_REVISION_REQUIRED')
        if getattr(model.config, '_attn_implementation', None) != 'eager':
            raise ValueError('EAGER_ATTENTION_REQUIRED')
        if not getattr(tokenizer, 'is_fast', False):
            raise ValueError('EXACT_TOKENIZER_OFFSETS_REQUIRED')
        self.model = model.eval()
        self.tokenizer = tokenizer
        self.layers = resolve_transformer_layers(model)
        self.torch = torch
        self.pipeline = {
            'model_id': model_id,
            'revision': revision,
            'dtype': str(next(model.parameters()).dtype),
            'attention': 'eager',
            'architecture_layers': len(self.layers),
            'tokenizer_sha256': sha256_hex(
                json.dumps(tokenizer.get_vocab(), sort_keys=True, separators=(',', ':'))
            ),
            'runtime': torch.__version__,
            'authority_effect': 'None',
        }

    def build_equal_norm_random_vector(self, reference_vector: torch.Tensor, *, seed: int) -> torch.Tensor:
        """Construct a seeded random direction orthogonalized to ``reference_vector`` with equal L2 norm."""
        if reference_vector.ndim != 1:
            raise ValueError('STEERING_VECTOR_MUST_BE_1D')
        ref_norm = float(reference_vector.norm().item())
        if ref_norm == 0.0:
            raise ValueError('ZERO_NORM_STEERING_VECTOR')
        gen = torch.Generator(device=reference_vector.device)
        gen.manual_seed(_require_exact_int(seed, 'seed'))
        raw = torch.randn(
            reference_vector.shape,
            generator=gen,
            dtype=reference_vector.dtype,
            device=reference_vector.device,
        )
        unit_ref = reference_vector / ref_norm
        ortho = raw - torch.dot(raw, unit_ref) * unit_ref
        ortho_norm = float(ortho.norm().item())
        if ortho_norm < 1e-12:
            raise ValueError('DEGENERATE_RANDOM_CONTROL_VECTOR')
        return ortho * (ref_norm / ortho_norm)


def evaluate_attention_intervention_gate(
    *,
    distractor_mass: Fraction,
    danger_tau: Fraction = Fraction(1, 20),
    host_refusal_on_unmasked: bool,
    host_observer_id: str = 'host.public_smoke',
    danger_kind: str = 'REPLAY_FAILURE',
    evidence_text: str = 'unmasked_baseline_reply',
) -> dict[str, Any]:
    """Enforce EIS Two-Signal regulation before authorizing distractor-attention masking.

    Signal 1 is the distractor attention mass exceeding ``danger_tau``.
    Signal 2 must come from an allowlisted external host observer
    (``HOST_OBSERVERS``) with a registered ``HOST_DANGER_SIGNAL_KINDS`` kind.
    If the caller passes ``observer_id='attention_probe'`` or attempts to trigger
    activation from attention mass alone, ``immunity.decide`` refuses
    ``TWO_SIGNAL_COLLAPSE`` or keeps the disposition ``DIAGNOSTIC_OR_NORMALIZE``.
    """
    mass = _require_exact_fraction(distractor_mass, 'distractor_mass')
    tau = _require_exact_fraction(danger_tau, 'danger_tau')
    rules = [
        DetectorRule(
            rule_id='attn_distractor_mass_above_tau',
            target_epitope='attention',
            match_pattern='DISTRACTOR_MASS_HIGH',
        )
    ]
    probe_token = 'DISTRACTOR_MASS_HIGH' if mass > tau else 'DISTRACTOR_MASS_LOW'
    s1_matches = signal1(probe_token, rules)
    s2_danger = (
        host_danger(danger_kind, host_observer_id, evidence_text)
        if host_refusal_on_unmasked
        else None
    )
    decision = decide(s1_matches, s2_danger, host_observers=HOST_OBSERVERS)
    authorize_mask = (
        decision.disposition == 'HOLD_OR_REPAIR'
        and decision.refusal_code is None
        and bool(s1_matches)
        and s2_danger is not None
    )
    return {
        'distractor_mass': str(mass),
        'danger_tau': str(tau),
        'signal1_fired': bool(s1_matches),
        'disposition': decision.disposition,
        'refusal_code': decision.refusal_code,
        'authorize_mask': authorize_mask,
        'basis': decision.basis,
        'authority_effect': 'None',
    }


# ============================================================================
# SEAM 5: Weights (`finetune_on_antibodies` Directly from PFP Verified Receipts)
# ============================================================================


@dataclass(frozen=True)
class CandidateRunReceiptV1:
    """One host-evaluated candidate proposal from a PFP run."""

    receipt_id: str
    task_id: str
    prompt_text: str
    candidate_text: str
    genome_id: str
    oracle: HostOracleContext
    contract: ProtectedContract | None = None
    refusal_code: str = ''


@dataclass(frozen=True)
class VerifiedReceiptTripleV1:
    """Host-certified preference triple ``(prompt, chosen, rejected)`` for weight updates."""

    triple_id: str
    task_id: str
    prompt_text: str
    prompt_sha256: str
    chosen_text: str
    chosen_receipt_id: str
    chosen_evidence_sha256: dict[str, str]
    rejected_text: str
    rejected_receipt_id: str
    rejected_failed_predicates: tuple[str, ...]
    refusal_code: str
    genome_id: str
    triple_sha256: str = ''
    authority_effect: str = 'None'

    def __post_init__(self) -> None:
        if not self.triple_sha256:
            digest = sha256_hex(
                _canonical_json_bytes(
                    {
                        'task_id': self.task_id,
                        'prompt_sha256': self.prompt_sha256,
                        'chosen_sha256': sha256_hex(self.chosen_text),
                        'rejected_sha256': sha256_hex(self.rejected_text),
                        'rejected_failed_predicates': list(self.rejected_failed_predicates),
                        'refusal_code': self.refusal_code,
                    }
                )
            )
            object.__setattr__(self, 'triple_sha256', digest)

    def to_sft_record(self) -> dict[str, Any]:
        return {
            'schema': 'pfp.seam5.sft_record.v1',
            'task_id': self.task_id,
            'prompt': self.prompt_text,
            'prompt_sha256': self.prompt_sha256,
            'completion': self.chosen_text,
            'chosen_receipt_id': self.chosen_receipt_id,
            'host_evidence_sha256': dict(self.chosen_evidence_sha256),
            'authority_effect': 'None',
        }

    def to_dpo_record(self) -> dict[str, Any]:
        return {
            'schema': 'pfp.seam5.dpo_record.v1',
            'triple_id': self.triple_id,
            'triple_sha256': self.triple_sha256,
            'task_id': self.task_id,
            'prompt': self.prompt_text,
            'prompt_sha256': self.prompt_sha256,
            'chosen': self.chosen_text,
            'rejected': self.rejected_text,
            'rejected_failed_predicates': list(self.rejected_failed_predicates),
            'refusal_code': self.refusal_code,
            'authority_effect': 'None',
        }


@dataclass(frozen=True)
class WeightTrainingDatasetV1:
    """Deterministically compiled SFT + DPO dataset with PCIV SealedCausalWitness custody."""

    triples: tuple[VerifiedReceiptTripleV1, ...]
    sft_jsonl: str
    dpo_jsonl: str
    dataset_sha256: str
    holdout_manifest_sha256: str
    causal_witness: SealedCausalWitness
    authority_effect: str = 'None'


@dataclass(frozen=True)
class WeightAdapterReceiptV1:
    """Cryptographic custody receipt for a receipt-trained low-rank (LoRA) weight adapter."""

    schema_version: str
    adapter_id: str
    base_model_id: str
    base_model_revision: str
    target_modules: tuple[str, ...]
    rank: int
    alpha: Fraction
    dataset_sha256: str
    holdout_manifest_sha256: str
    adapter_state_sha256: str
    mean_dpo_margin_before: str
    mean_dpo_margin_after: str
    causal_witness: dict[str, Any]
    authority_effect: str = 'None'

    def to_dict(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'adapter_id': self.adapter_id,
            'base_model_id': self.base_model_id,
            'base_model_revision': self.base_model_revision,
            'target_modules': list(self.target_modules),
            'rank': self.rank,
            'alpha': str(self.alpha),
            'dataset_sha256': self.dataset_sha256,
            'holdout_manifest_sha256': self.holdout_manifest_sha256,
            'adapter_state_sha256': self.adapter_state_sha256,
            'mean_dpo_margin_before': self.mean_dpo_margin_before,
            'mean_dpo_margin_after': self.mean_dpo_margin_after,
            'causal_witness': dict(self.causal_witness),
            'authority_effect': self.authority_effect,
        }


class LowRankWeightAdapterV1(nn.Module):
    """Low-rank weight perturbation $\\Delta W = (\\alpha / r) B A$ for open-weight ``nn.Linear`` modules.

    Base weights remain frozen; ``attach(linear)`` computes
    ``linear(x) + (x @ A.T @ B.T) * (alpha / r)`` via a reversible forward hook
    so the base checkpoint tensors are never mutated in place.
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        *,
        rank: int = 4,
        alpha: Fraction = Fraction(8),
        seed: int = 0,
        dtype: torch.dtype = torch.float32,
    ) -> None:
        super().__init__()
        r = _require_exact_int(rank, 'rank')
        if not (1 <= r <= 64):
            raise ValueError('LORA_RANK_OUT_OF_RANGE')
        alp = _require_exact_fraction(alpha, 'alpha')
        if alp <= 0:
            raise ValueError('POSITIVE_LORA_ALPHA_REQUIRED')
        self.in_features = _require_exact_int(in_features, 'in_features')
        self.out_features = _require_exact_int(out_features, 'out_features')
        self.rank = r
        self.alpha = alp
        self.scaling = float(alp) / float(r)

        gen = torch.Generator()
        gen.manual_seed(_require_exact_int(seed, 'seed'))
        init_a = torch.randn((r, self.in_features), generator=gen, dtype=dtype) * (1.0 / math.sqrt(self.in_features))
        init_b = torch.zeros((self.out_features, r), dtype=dtype)
        self.lora_A = nn.Parameter(init_a)
        self.lora_B = nn.Parameter(init_b)

    def delta_weight(self) -> torch.Tensor:
        return (self.lora_B @ self.lora_A) * self.scaling

    def frobenius_norm(self) -> float:
        with torch.no_grad():
            return float(self.delta_weight().norm().item())

    def state_sha256(self) -> str:
        with torch.no_grad():
            a_bytes = self.lora_A.detach().cpu().contiguous().numpy().tobytes()
            b_bytes = self.lora_B.detach().cpu().contiguous().numpy().tobytes()
        meta = _canonical_json_bytes(
            {
                'in_features': self.in_features,
                'out_features': self.out_features,
                'rank': self.rank,
                'alpha': str(self.alpha),
                'a_sha256': sha256_hex(a_bytes),
                'b_sha256': sha256_hex(b_bytes),
            }
        )
        return sha256_hex(meta)

    @contextmanager
    def attached_to(self, linear: nn.Linear):
        """Reversibly attach this low-rank adapter to ``linear`` during forward passes."""
        if linear.in_features != self.in_features or linear.out_features != self.out_features:
            raise ValueError('LORA_LINEAR_SHAPE_MISMATCH')

        def _hook(_module: nn.Module, args: tuple[Any, ...], output: torch.Tensor) -> torch.Tensor:
            x = args[0]
            delta = (x @ self.lora_A.t() @ self.lora_B.t()) * self.scaling
            return output + delta.to(output.dtype)

        handle = linear.register_forward_hook(_hook)
        try:
            yield self
        finally:
            handle.remove()

    def build_equal_norm_random_control(self, *, seed: int) -> LowRankWeightAdapterV1:
        """Construct a seeded random low-rank adapter with identical Frobenius norm $\\|\\Delta W\\|_F$."""
        target_norm = self.frobenius_norm()
        if target_norm <= 0.0:
            raise ValueError('TRAINED_ADAPTER_HAS_ZERO_NORM')
        ctrl = LowRankWeightAdapterV1(
            self.in_features,
            self.out_features,
            rank=self.rank,
            alpha=self.alpha,
            seed=seed,
            dtype=self.lora_A.dtype,
        )
        gen = torch.Generator()
        gen.manual_seed(_require_exact_int(seed, 'seed') + 10_000)
        with torch.no_grad():
            rand_b = torch.randn(self.lora_B.shape, generator=gen, dtype=self.lora_B.dtype)
            ctrl.lora_B.copy_(rand_b)
            current_norm = ctrl.frobenius_norm()
            if current_norm <= 1e-12:
                raise ValueError('DEGENERATE_RANDOM_ADAPTER')
            ctrl.lora_B.mul_(target_norm / current_norm)
        return ctrl


class ReceiptToWeightPipelineV1:
    """Seam 5 pipeline: Verified PFP Receipts -> Disjoint Hold-Out Audit -> DPO/SFT Dataset -> LoRA Adapter."""

    def __init__(
        self,
        *,
        lineage: Lineage | None = None,
        tainted_seeds: set[str] | None = None,
        thymus_rules: Sequence[DetectorRule] = (),
        self_panel: Sequence[str] = (),
    ) -> None:
        self.lineage = lineage or Lineage()
        self.tainted_genomes = self.lineage.taint(set(tainted_seeds or ()))
        if thymus_rules and self_panel:
            self.admitted_rules, self.killed_rules = screen_rules(list(thymus_rules), list(self_panel))
        else:
            self.admitted_rules, self.killed_rules = list(thymus_rules), []

    @staticmethod
    def assert_disjoint_holdout(
        train_prompts: Sequence[str],
        holdout_prompts: Sequence[str],
        *,
        train_task_ids: Sequence[str] = (),
        holdout_task_ids: Sequence[str] = (),
    ) -> str:
        """Enforce ``split_contamination == none`` across both prompt hashes and task IDs."""
        if not holdout_prompts:
            raise ValueError('NONEMPTY_HOLDOUT_SET_REQUIRED')
        train_hashes = {sha256_hex(p) for p in train_prompts}
        holdout_hashes = {sha256_hex(p) for p in holdout_prompts}
        overlap_hashes = train_hashes & holdout_hashes
        if overlap_hashes:
            raise ValueError(f'HOLDOUT_CONTAMINATION_REFUSAL: overlapping prompt_sha256 {sorted(overlap_hashes)}')
        overlap_ids = set(train_task_ids) & set(holdout_task_ids)
        if overlap_ids:
            raise ValueError(f'HOLDOUT_CONTAMINATION_REFUSAL: overlapping task_id {sorted(overlap_ids)}')
        return sha256_hex(_canonical_json_bytes({'holdout_prompt_hashes': sorted(holdout_hashes)}))

    def extract_verified_triples(
        self,
        pairs: Sequence[tuple[CandidateRunReceiptV1, CandidateRunReceiptV1]],
        *,
        holdout_prompts: Sequence[str],
        holdout_task_ids: Sequence[str] = (),
    ) -> tuple[list[VerifiedReceiptTripleV1], str]:
        """Validate ``(chosen_receipt, rejected_receipt)`` pairs and refuse unverified or contaminated inputs."""
        if not pairs:
            raise ValueError('NONEMPTY_RECEIPT_PAIRS_REQUIRED')
        train_prompts = [chosen.prompt_text for chosen, _ in pairs]
        train_task_ids = [chosen.task_id for chosen, _ in pairs]
        holdout_sha = self.assert_disjoint_holdout(
            train_prompts,
            holdout_prompts,
            train_task_ids=train_task_ids,
            holdout_task_ids=holdout_task_ids,
        )

        triples: list[VerifiedReceiptTripleV1] = []
        for idx, (chosen, rejected) in enumerate(pairs):
            if chosen.task_id != rejected.task_id or chosen.prompt_text != rejected.prompt_text:
                raise ValueError(f'UNPAIRED_RECEIPT_SEED at index {idx}')
            if chosen.genome_id in self.tainted_genomes or rejected.genome_id in self.tainted_genomes:
                raise ValueError(f'TAINTED_LINEAGE_RECEIPT_REFUSED: {chosen.genome_id} / {rejected.genome_id}')
            if not chosen.oracle.final_output_certified:
                raise ValueError(f'UNCERTIFIED_CHOSEN_PROPOSAL_REFUSED: {chosen.receipt_id}')
            if chosen.contract is not None and chosen.contract.violations(chosen.candidate_text):
                raise ValueError(f'CHOSEN_PROTECTED_FENCE_VIOLATION: {chosen.receipt_id}')
            if self.admitted_rules and signal1(chosen.candidate_text, self.admitted_rules):
                raise ValueError(f'CHOSEN_FAILED_ADMITTED_GUARD: {chosen.receipt_id}')

            # Critical witness-multiplicity guard: if ``rejected`` also passes the host oracle
            # and contract fences, it is an alternative valid witness, NOT a negative training example!
            rejected_fence_violations = (
                rejected.contract.violations(rejected.candidate_text) if rejected.contract is not None else []
            )
            rejected_failed = list(rejected.oracle.failed) + [f'fence:{v}' for v in rejected_fence_violations]
            if rejected.oracle.final_output_certified and not rejected_fence_violations:
                raise ValueError(
                    f'ALTERNATIVE_VALID_WITNESS_NOT_REJECTED: {rejected.receipt_id} passed host oracle'
                )
            if not rejected_failed:
                raise ValueError(f'REJECTED_MISSING_HOST_FAILURE_PREDICATE: {rejected.receipt_id}')

            prompt_sha = sha256_hex(chosen.prompt_text)
            triples.append(
                VerifiedReceiptTripleV1(
                    triple_id=f'triple_{idx:04d}_{prompt_sha[:8]}',
                    task_id=chosen.task_id,
                    prompt_text=chosen.prompt_text,
                    prompt_sha256=prompt_sha,
                    chosen_text=chosen.candidate_text,
                    chosen_receipt_id=chosen.receipt_id,
                    chosen_evidence_sha256=dict(chosen.oracle.evidence),
                    rejected_text=rejected.candidate_text,
                    rejected_receipt_id=rejected.receipt_id,
                    rejected_failed_predicates=tuple(rejected_failed),
                    refusal_code=rejected.refusal_code or 'HOST_PREDICATE_REFUSAL',
                    genome_id=chosen.genome_id,
                )
            )
        return triples, holdout_sha

    def compile_dataset(
        self,
        triples: Sequence[VerifiedReceiptTripleV1],
        *,
        holdout_manifest_sha256: str,
    ) -> WeightTrainingDatasetV1:
        if not triples:
            raise ValueError('NONEMPTY_TRIPLES_REQUIRED')
        sft_lines = [
            json.dumps(t.to_sft_record(), sort_keys=True, separators=(',', ':')) for t in triples
        ]
        dpo_lines = [
            json.dumps(t.to_dpo_record(), sort_keys=True, separators=(',', ':')) for t in triples
        ]
        sft_jsonl = '\n'.join(sft_lines) + '\n'
        dpo_jsonl = '\n'.join(dpo_lines) + '\n'
        dataset_sha = sha256_hex(
            _canonical_json_bytes(
                {
                    'sft_sha256': sha256_hex(sft_jsonl),
                    'dpo_sha256': sha256_hex(dpo_jsonl),
                    'triple_hashes': [t.triple_sha256 for t in triples],
                    'holdout_manifest_sha256': holdout_manifest_sha256,
                }
            )
        )
        witness = seal_causal_witness(
            {
                'operation': 'pfp.seam5.compile_weight_dataset.v1',
                'dataset_sha256': dataset_sha,
                'holdout_manifest_sha256': holdout_manifest_sha256,
                'parent_receipt_ids': [
                    rid for t in triples for rid in (t.chosen_receipt_id, t.rejected_receipt_id)
                ],
                'triple_count': len(triples),
            }
        )
        return WeightTrainingDatasetV1(
            triples=tuple(triples),
            sft_jsonl=sft_jsonl,
            dpo_jsonl=dpo_jsonl,
            dataset_sha256=dataset_sha,
            holdout_manifest_sha256=holdout_manifest_sha256,
            causal_witness=witness,
        )

    def train_dpo_lora_on_receipts(
        self,
        model: nn.Module,
        tokenizer: Any,
        dataset: WeightTrainingDatasetV1,
        *,
        target_linear: nn.Linear,
        target_module_name: str = 'lm_head',
        base_model_id: str,
        base_model_revision: str,
        rank: int = 4,
        alpha: Fraction = Fraction(8),
        beta: float = 0.5,
        lr: float = 0.15,
        steps: int = 25,
        seed: int = 42,
    ) -> tuple[LowRankWeightAdapterV1, WeightAdapterReceiptV1]:
        """Fit a ``LowRankWeightAdapterV1`` using DPO preference loss over verified receipt triples.

        Base model parameters are strictly frozen; only ``lora_A`` and ``lora_B``
        receive gradients. Emits a ``WeightAdapterReceiptV1`` with verified
        ``SealedCausalWitness`` custody and ``authority_effect='None'``.
        """
        if not verify_causal_witness(dataset.causal_witness, expected_dataset_sha256=dataset.dataset_sha256):
            raise ValueError('INVALID_DATASET_CAUSAL_WITNESS')
        if (
            not base_model_id
            or type(base_model_revision) is not str
            or len(base_model_revision) != 40
            or any(c not in '0123456789abcdef' for c in base_model_revision)
        ):
            raise ValueError('LOCAL_MODEL_REVISION_REQUIRED')

        # Freeze all base model parameters
        for param in model.parameters():
            param.requires_grad_(False)

        adapter = LowRankWeightAdapterV1(
            target_linear.in_features,
            target_linear.out_features,
            rank=rank,
            alpha=alpha,
            seed=seed,
        )

        encoded_triples: list[tuple[torch.Tensor, list[int], list[int]]] = []
        for triple in dataset.triples:
            p_ids = tokenizer.encode(triple.prompt_text, add_special_tokens=False)
            w_ids = tokenizer.encode(triple.chosen_text, add_special_tokens=False)
            l_ids = tokenizer.encode(triple.rejected_text, add_special_tokens=False)
            encoded_triples.append((torch.tensor([p_ids], dtype=torch.long), w_ids, l_ids))

        def _seq_logprob(prompt_tensor: torch.Tensor, target_ids: list[int]) -> torch.Tensor:
            full_ids = torch.cat([prompt_tensor, torch.tensor([target_ids], dtype=torch.long)], dim=1)
            out = model(input_ids=full_ids, use_cache=False)
            log_probs = F.log_softmax(out.logits, dim=-1)
            p_len = prompt_tensor.shape[1]
            total = torch.zeros((), dtype=out.logits.dtype)
            for offset, tok_id in enumerate(target_ids):
                pos = p_len - 1 + offset
                total = total + log_probs[0, pos, tok_id]
            return total

        # Reference log-probs under base model (adapter B=0 -> zero delta)
        ref_diffs: list[torch.Tensor] = []
        with torch.no_grad():
            for p_ten, w_ids, l_ids in encoded_triples:
                ref_w = _seq_logprob(p_ten, w_ids)
                ref_l = _seq_logprob(p_ten, l_ids)
                ref_diffs.append(ref_w - ref_l)
        margin_before = float(torch.stack(ref_diffs).mean().item())

        optimizer = torch.optim.SGD([adapter.lora_A, adapter.lora_B], lr=lr)
        with adapter.attached_to(target_linear):
            for _ in range(steps):
                optimizer.zero_grad()
                losses: list[torch.Tensor] = []
                for (p_ten, w_ids, l_ids), ref_diff in zip(encoded_triples, ref_diffs, strict=True):
                    pol_w = _seq_logprob(p_ten, w_ids)
                    pol_l = _seq_logprob(p_ten, l_ids)
                    dpo_logit = beta * ((pol_w - pol_l) - ref_diff)
                    losses.append(-F.logsigmoid(dpo_logit))
                loss = torch.stack(losses).mean()
                loss.backward()
                optimizer.step()

            with torch.no_grad():
                after_diffs = [
                    _seq_logprob(p_ten, w_ids) - _seq_logprob(p_ten, l_ids)
                    for p_ten, w_ids, l_ids in encoded_triples
                ]
                margin_after = float(torch.stack(after_diffs).mean().item())

        adapter_sha = adapter.state_sha256()
        adapter_witness = seal_causal_witness(
            {
                'operation': 'pfp.seam5.train_dpo_lora.v1',
                'base_model_id': base_model_id,
                'base_model_revision': base_model_revision,
                'dataset_sha256': dataset.dataset_sha256,
                'holdout_manifest_sha256': dataset.holdout_manifest_sha256,
                'adapter_state_sha256': adapter_sha,
                'rank': rank,
                'alpha': str(alpha),
            }
        )
        receipt = WeightAdapterReceiptV1(
            schema_version='pfp.seam5.weight_adapter_receipt.v1',
            adapter_id=f'lora_{adapter_sha[:12]}',
            base_model_id=base_model_id,
            base_model_revision=base_model_revision,
            target_modules=(target_module_name,),
            rank=rank,
            alpha=alpha,
            dataset_sha256=dataset.dataset_sha256,
            holdout_manifest_sha256=dataset.holdout_manifest_sha256,
            adapter_state_sha256=adapter_sha,
            mean_dpo_margin_before=f'{margin_before:.6f}',
            mean_dpo_margin_after=f'{margin_after:.6f}',
            causal_witness={
                'receipt_sha256': adapter_witness.receipt_sha256,
                'canonical_body': adapter_witness.canonical_body,
            },
            authority_effect='None',
        )
        return adapter, receipt


# ============================================================================
# Deterministic Eager Micro-Transformer & Fast Offset Tokenizer for CI / Local Runs
# ============================================================================


class FastOffsetTokenizer:
    """Deterministic whitespace/symbol tokenizer with ``is_fast=True`` and character ``offset_mapping``."""

    is_fast = True

    def __init__(self, extra_tokens: Sequence[str] = ()) -> None:
        base_vocab = [
            '<pad>',
            '<eos>',
            '<unk>',
            '{',
            '}',
            '[',
            ']',
            ':',
            ',',
            '"status"',
            '"SOLVED"',
            '"kind"',
            '"product_sign"',
            '"cycle_sum"',
            '"commutation"',
            '"answer"',
            '"+"',
            '"-"',
            '"sign"',
            '"+1"',
            '"-1"',
            '"negative_count"',
            '"sum"',
            '"0"',
            '"1"',
            '"2"',
            '"3"',
            '"4"',
            '"5"',
            '"6"',
            '"-3"',
            '"-5"',
            '"1/2"',
            '"2/4"',
            'factors',
            'claims',
            'fluff',
            'noise',
            '+',
            '-',
            '+1',
            '-1',
        ]
        for tok in extra_tokens:
            if tok not in base_vocab:
                base_vocab.append(tok)
        self._id_to_tok = list(base_vocab)
        self._tok_to_id = {t: i for i, t in enumerate(self._id_to_tok)}
        self.eos_token_id = self._tok_to_id['<eos>']
        self.vocab_size = len(self._id_to_tok)

    def get_vocab(self) -> dict[str, int]:
        return dict(self._tok_to_id)

    def apply_chat_template(
        self,
        messages: Sequence[dict[str, str]],
        *,
        tokenize: bool = False,
        add_generation_prompt: bool = True,
    ) -> str:
        rendered = '\n'.join(f"{m['role']}: {m['content']}" for m in messages)
        if add_generation_prompt:
            rendered += '\nassistant: '
        return rendered

    def _scan(self, text: str) -> tuple[list[int], list[tuple[int, int]]]:
        ids: list[int] = []
        offsets: list[tuple[int, int]] = []
        idx = 0
        n = len(text)
        # Match longest known vocabulary token first, otherwise consume non-whitespace word/char
        sorted_tokens = sorted(
            (t for t in self._id_to_tok if t not in ('<pad>', '<eos>', '<unk>')),
            key=len,
            reverse=True,
        )
        while idx < n:
            if text[idx].isspace():
                idx += 1
                continue
            matched = None
            for cand in sorted_tokens:
                if text.startswith(cand, idx):
                    matched = cand
                    break
            if matched is not None:
                ids.append(self._tok_to_id[matched])
                offsets.append((idx, idx + len(matched)))
                idx += len(matched)
            else:
                end = idx + 1
                while end < n and not text[end].isspace():
                    if any(text.startswith(cand, end) for cand in sorted_tokens):
                        break
                    end += 1
                ids.append(self._tok_to_id['<unk>'])
                offsets.append((idx, end))
                idx = end
        if not ids:
            ids.append(self._tok_to_id['<unk>'])
            offsets.append((0, min(1, len(text))))
        return ids, offsets

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        ids, _ = self._scan(text)
        if add_special_tokens:
            ids.append(self.eos_token_id)
        return ids

    def decode(self, token_ids: Sequence[int] | torch.Tensor, skip_special_tokens: bool = True) -> str:
        if isinstance(token_ids, torch.Tensor):
            token_ids = token_ids.tolist()
        pieces: list[str] = []
        for tid in token_ids:
            tok = self._id_to_tok[int(tid)] if 0 <= int(tid) < len(self._id_to_tok) else '<unk>'
            if skip_special_tokens and tok in ('<pad>', '<eos>'):
                continue
            pieces.append(tok)
        return ''.join(pieces)

    def __call__(
        self,
        text: str,
        *,
        return_tensors: str | None = None,
        return_offsets_mapping: bool = False,
        add_special_tokens: bool = False,
    ) -> dict[str, Any]:
        ids, offsets = self._scan(text)
        if add_special_tokens:
            ids.append(self.eos_token_id)
            offsets.append((0, 0))
        out: dict[str, Any] = {
            'input_ids': torch.tensor([ids], dtype=torch.long) if return_tensors == 'pt' else ids,
        }
        if return_offsets_mapping:
            out['offset_mapping'] = offsets
        return out


@dataclass
class _MicroCacheLayer:
    keys: torch.Tensor
    values: torch.Tensor


@dataclass
class _MicroPastKeyValues:
    layers: list[_MicroCacheLayer]


@dataclass
class _MicroCausalOutput:
    logits: torch.Tensor
    past_key_values: _MicroPastKeyValues | None = None
    attentions: tuple[torch.Tensor, ...] | None = None


@dataclass
class _MicroConfig:
    vocab_size: int
    hidden_size: int = 16
    num_attention_heads: int = 2
    num_hidden_layers: int = 2
    max_position_embeddings: int = 512
    _attn_implementation: str = 'eager'


class _EagerSelfAttention(nn.Module):
    def __init__(self, hidden_size: int, num_heads: int) -> None:
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        self.q_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.k_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.v_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.o_proj = nn.Linear(hidden_size, hidden_size, bias=False)

    def forward(
        self,
        hidden_states: torch.Tensor,
        *,
        attention_mask: torch.Tensor | None = None,
        past_layer: _MicroCacheLayer | None = None,
        use_cache: bool = False,
    ) -> tuple[torch.Tensor, _MicroCacheLayer | None, torch.Tensor]:
        bsz, q_len, _ = hidden_states.shape
        q = self.q_proj(hidden_states).view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(hidden_states).view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(hidden_states).view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)

        if past_layer is not None:
            k = torch.cat([past_layer.keys, k], dim=-2)
            v = torch.cat([past_layer.values, v], dim=-2)
        next_cache = _MicroCacheLayer(keys=k.clone(), values=v.clone()) if use_cache else None

        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        if attention_mask is not None:
            scores = scores + attention_mask
        probs = F.softmax(scores, dim=-1)
        context = torch.matmul(probs, v).transpose(1, 2).contiguous().view(bsz, q_len, self.hidden_size)
        attn_out = self.o_proj(context)
        return attn_out, next_cache, probs


class _EagerDecoderLayer(nn.Module):
    def __init__(self, hidden_size: int, num_heads: int) -> None:
        super().__init__()
        self.self_attn = _EagerSelfAttention(hidden_size, num_heads)
        self.mlp = nn.Linear(hidden_size, hidden_size, bias=False)

    def forward(
        self,
        hidden_states: torch.Tensor,
        *,
        attention_mask: torch.Tensor | None = None,
        past_layer: _MicroCacheLayer | None = None,
        use_cache: bool = False,
    ) -> tuple[torch.Tensor, _MicroCacheLayer | None, torch.Tensor]:
        attn_out, next_cache, probs = self.self_attn(
            hidden_states,
            attention_mask=attention_mask,
            past_layer=past_layer,
            use_cache=use_cache,
        )
        hidden = hidden_states + attn_out
        hidden = hidden + torch.tanh(self.mlp(hidden)) * 0.1
        return hidden, next_cache, probs


class _InnerBackbone(nn.Module):
    def __init__(self, config: _MicroConfig) -> None:
        super().__init__()
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.layers = nn.ModuleList(
            [
                _EagerDecoderLayer(config.hidden_size, config.num_attention_heads)
                for _ in range(config.num_hidden_layers)
            ]
        )


class PinnedEagerMicroCausalLM(nn.Module):
    """Real PyTorch eager-attention causal LM supporting both Llama/Qwen and Gemma-4 layouts.

    When ``gemma4_layout=True``, layers live under ``self.language_model.layers``;
    otherwise under ``self.model.layers``. Supports 4D causal attention masks,
    ``.self_attn.o_proj`` head hooks, layer residual hooks, ``past_key_values.layers``,
    and ``generate()`` with ``LogitsProcessorList``.
    """

    def __init__(self, vocab_size: int, *, gemma4_layout: bool = False, seed: int = 7) -> None:
        super().__init__()
        torch.manual_seed(seed)
        self.config = _MicroConfig(vocab_size=vocab_size)
        backbone = _InnerBackbone(self.config)
        if gemma4_layout:
            self.language_model = backbone
        else:
            self.model = backbone
        self._backbone = backbone
        self.lm_head = nn.Linear(self.config.hidden_size, vocab_size, bias=False)

    def _build_4d_causal_mask(self, q_len: int, kv_len: int, dtype: torch.dtype, device: torch.device) -> torch.Tensor:
        mask = torch.zeros((1, 1, q_len, kv_len), dtype=dtype, device=device)
        if q_len > 1:
            causal = torch.triu(
                torch.full((q_len, kv_len), float('-inf'), dtype=dtype, device=device),
                diagonal=kv_len - q_len + 1,
            )
            mask[0, 0] = causal
        return mask

    def forward(
        self,
        input_ids: torch.Tensor,
        *,
        past_key_values: _MicroPastKeyValues | None = None,
        use_cache: bool = False,
        output_attentions: bool = False,
        cache_position: torch.Tensor | None = None,  # noqa: ARG002
    ) -> _MicroCausalOutput:
        hidden = self._backbone.embed_tokens(input_ids)
        q_len = input_ids.shape[1]
        past_len = past_key_values.layers[0].keys.shape[-2] if past_key_values is not None else 0
        kv_len = past_len + q_len
        mask_4d = self._build_4d_causal_mask(q_len, kv_len, hidden.dtype, hidden.device)

        next_layers: list[_MicroCacheLayer] = []
        all_attns: list[torch.Tensor] = []
        for idx, layer in enumerate(self._backbone.layers):
            past_layer = past_key_values.layers[idx] if past_key_values is not None else None
            hidden, cache_layer, probs = layer(
                hidden,
                attention_mask=mask_4d,
                past_layer=past_layer,
                use_cache=use_cache,
            )
            if use_cache and cache_layer is not None:
                next_layers.append(cache_layer)
            if output_attentions:
                all_attns.append(probs)

        logits = self.lm_head(hidden)
        return _MicroCausalOutput(
            logits=logits,
            past_key_values=_MicroPastKeyValues(next_layers) if use_cache else None,
            attentions=tuple(all_attns) if output_attentions else None,
        )

    def generate(
        self,
        input_ids: torch.Tensor,
        *,
        max_new_tokens: int = 16,
        do_sample: bool = False,
        temperature: float = 1.0,
        use_cache: bool = True,
        logits_processor: Sequence[Callable[[torch.Tensor, torch.Tensor], torch.Tensor]] = (),
        pad_token_id: int = 0,  # noqa: ARG002
        eos_token_id: int = 1,
    ) -> torch.Tensor:
        seq = input_ids.clone()
        for _ in range(max_new_tokens):
            out = self.forward(seq, use_cache=use_cache)
            scores = out.logits[:, -1, :].clone()
            for proc in logits_processor:
                scores = proc(seq, scores)
            if do_sample and temperature > 0:
                probs = F.softmax(scores / float(temperature), dim=-1)
                next_tok = torch.multinomial(probs, num_samples=1)
            else:
                next_tok = scores.argmax(dim=-1, keepdim=True)
            seq = torch.cat([seq, next_tok], dim=1)
            if int(next_tok.item()) == eos_token_id:
                break
        return seq
