"""Operad Pre-Miner provider component.

Runs sequential checked proposals via the caller's existing PFP/accounting boundary to
extract preliminary domain invariants, morphism DAG skeletons, rational bounds,
and failure patterns before committing higher-tier tokens.

AuthorityEffect: None.
Firewall: stated region only; mints no execution authority.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from adversary.domain.providers.types import CandidateRequest, ProviderConfigError, ProviderError
from pfp.infrastructure.pilot_matrix import complete_pilot_turn

DEFAULT_MINER_MODELS = [
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "liquid/lfm-2.5-2.6b:free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "thinkingmachines/inkling:free",
    "thinkingmachines/inkling-small:free",
    "dots-studio/dots-3-note-preview:free",
    "nvidia/nemotron-3.5-super-vl:free",
]

CHEAP_FALLBACK_MODELS = [
    "meta-llama/llama-3.1-8b-instruct",
    "qwen/qwen-2.5-7b-instruct",
    "deepseek/deepseek-chat",
    "openai/gpt-4o-mini",
]


@dataclass
class MinerRole:
    miner_id: str
    name: str
    target_layer: str
    prompt_instruction: str
    model: str


@dataclass
class MinerResult:
    miner_id: str
    name: str
    target_layer: str
    model: str
    content: str
    latency_s: float
    status: str
    tokens: dict[str, int | None] = field(default_factory=dict)
    cost_usd: float | None = None
    pfp_turn: dict[str, Any] | None = None


@dataclass
class OperadPreMinerReport:
    target_name: str
    total_latency_s: float
    total_tokens: int | None
    total_cost_usd: float | None
    miner_results: list[MinerResult]
    synthesized_operad_prompt: str


def call_openrouter_miner(
    api_key: str,
    models: list[str],
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 400,
    timeout: float = 30.0,
    *, gateway=None, task_id: str | None = None, attempt_id: str | None = None,
) -> tuple[str, str, dict[str, int | None], float, float | None]:
    """Compatibility tuple over one actual PFP turn; never retries or falls back.

    ``api_key`` and ``timeout`` remain accepted for source compatibility. The
    enclosing gateway owns credentials, timeout and the continuing allowance.
    """
    turn = _mine_turn(gateway, models, system_prompt, user_prompt, max_tokens, task_id, attempt_id)
    if not turn['ok'] or turn['stop']:
        raise ProviderError(turn['error'] or 'PFP_MINER_REFUSED')
    return turn['content'], turn.get('model') or models[0], _tokens(turn), turn['elapsed'], turn['usage'].get('cost')


def _mine_turn(gateway, models, system, user, max_tokens, task_id, attempt_id):
    if gateway is None:
        raise ProviderConfigError('PFP_ACCOUNTED_GATEWAY_REQUIRED')
    if type(models) is not list or len(models) != 1 or type(models[0]) is not str or not models[0].strip():
        raise ProviderConfigError('EXPLICIT_MODEL_REQUIRED: no implicit miner fallback')
    if any(type(value) is not str or not value.strip() for value in (task_id, attempt_id)):
        raise ProviderConfigError('PFP_TASK_BINDING_REQUIRED')
    return complete_pilot_turn(gateway, CandidateRequest(system=system, user=user), model=models[0],
        task_id=task_id, attempt_id=attempt_id, max_tokens=max_tokens,
        answer_schema={'type': 'string', 'minLength': 1})


def _tokens(turn):
    usage = turn['usage']
    prompt, completion = usage.get('prompt_tokens'), usage.get('completion_tokens')
    return {'prompt_tokens': prompt, 'completion_tokens': completion,
        'total_tokens': prompt + completion if type(prompt) is int and type(completion) is int else None}


def build_10_mub6_miner_swarm(available_models: list[str]) -> list[MinerRole]:
    """Build configuration for 10 specialized operad miners targeting MUB-6."""
    models = (available_models + DEFAULT_MINER_MODELS)[:10]

    return [
        MinerRole(
            miner_id="miner_01",
            name="Environment Ring Extractor",
            target_layer="Layer 0 (Environment)",
            prompt_instruction=(
                "Identify the exact algebraic ring, field extension, and quotient ideal for the MUB(6) problem. "
                "Specify whether cyclotomic field Q(zeta_3) or Gaussian rationals Q(i) are required. "
                "Keep answer concise and state only the mathematical ring and invariants."
            ),
            model=models[0],
        ),
        MinerRole(
            miner_id="miner_02",
            name="Finite Fixtures & Matrix Carrier Extractor",
            target_layer="Layer 0 (Environment)",
            prompt_instruction=(
                "Specify the finite matrix dimension d=6, the standard basis C^6, and the Weyl-Heisenberg displacement "
                "operators for dimension 6 = 2 * 3. State the ray-overlap equation |<psi_j|phi_k>|^2 = 1/6 in exact rationals."
            ),
            model=models[1],
        ),
        MinerRole(
            miner_id="miner_03",
            name="Morphism Tree - Direct Derivation Chain",
            target_layer="Layer 1 (TreeSkeleton)",
            prompt_instruction=(
                "Construct the forward morphism composition tree for proving or disproving 4 MUBs in d=6: "
                "Op_basis_init -> Op_gram_matrix -> Op_equiangular_check -> Op_orthogonality_constraint. "
                "Format as a concise DAG."
            ),
            model=models[2],
        ),
        MinerRole(
            miner_id="miner_04",
            name="Morphism Tree - Obstruction & Contradiction Chain",
            target_layer="Layer 1 (TreeSkeleton)",
            prompt_instruction=(
                "Construct the obstruction / counter-example morphism chain: "
                "Op_assume_4_mubs -> Op_projector_sum -> Op_rank_deficiency_check -> Op_cohomology_defect. "
                "Where does the 2x3 composite dimension block simultaneous unbiasedness?"
            ),
            model=models[3],
        ),
        MinerRole(
            miner_id="miner_05",
            name="Paratope Refusal & False Refusal Auditor",
            target_layer="Antibodies / Immunization",
            prompt_instruction=(
                "Identify false refusal risks: what overzealous safety or loop antibodies might reject MUB(6) queries? "
                "(e.g., flagging 'unsolvable mathematical conjecture' or 'infinite search space'). "
                "Provide an idiotypic anti-antibody rule: beta_mub6_finite_carrier."
            ),
            model=models[4],
        ),
        MinerRole(
            miner_id="miner_06",
            name="Anti-Pattern Hunter",
            target_layer="Patterns / Anti-Patterns",
            prompt_instruction=(
                "List 3 critical mathematical anti-patterns when tackling MUB(6): "
                "1. AP_FLOAT_APPROXIMATION (using 0.166667 instead of exact 1/6). "
                "2. AP_PRIME_POWER_CONFLATION (assuming prime-power Galois field constructions work in composite d=6). "
                "3. AP_TRUNCATED_BASIS_LEAK."
            ),
            model=models[5],
        ),
        MinerRole(
            miner_id="miner_07",
            name="Helpful Pattern & Lemma Miner",
            target_layer="Patterns / Helpful Patterns",
            prompt_instruction=(
                "Extract 2 helpful mathematical patterns or lemmas for MUB(6): "
                "1. HP_WEIR_FOURIER_DECOMPOSITION (factoring across 2 and 3-dimensional sub-alphabets). "
                "2. HP_PROJECTOR_GRAM_EIGENVALUE_BOUNDS (Tr(P_i P_j) = 1/6)."
            ),
            model=models[6],
        ),
        MinerRole(
            miner_id="miner_08",
            name="SpanTable Rational Invariants Miner",
            target_layer="Layer 2 (SpanTable)",
            prompt_instruction=(
                "Provide the exact rational constants for MUB(6) SpanTable: "
                "Dimension d = 6, Ray overlap = 1/6, Inner product modulus = 1/sqrt(6), "
                "Max Known Bases = 3, Hypothetical Full Set = 7, Tested Candidate Target = 4. "
                "Return as a typed key-value table."
            ),
            model=models[7],
        ),
        MinerRole(
            miner_id="miner_09",
            name="Automorphism & Gauge Symmetry Extractor",
            target_layer="Layer 2 (SpanTable)",
            prompt_instruction=(
                "Identify the continuous and discrete symmetry groups of MUB(6): "
                "Global U(1) phase invariance, Permutation group S_6, and diagonal phasing. "
                "How do these reduce the search degrees of freedom?"
            ),
            model=models[8],
        ),
        MinerRole(
            miner_id="miner_10",
            name="Deadlock & Dead-End Pre-Scanner",
            target_layer="Pre-Scan / Failure Forecast",
            prompt_instruction=(
                "Identify the exact point of inevitable failure or non-closure in attempting to construct a 4th MUB in d=6. "
                "Why do standard Zauner or Heisenberg-Weyl orbits fail for d=6? "
                "Give a 3-bullet pre-mortem before stage 1 execution."
            ),
            model=models[9],
        ),
    ]


def synthesize_operad_prompt(target_name: str, results: list[MinerResult]) -> str:
    """Synthesize mined reconnaissance into a 3-Layer Operad prompt."""
    layer_0 = [r.content for r in results if r.target_layer == "Layer 0 (Environment)"]
    layer_1 = [r.content for r in results if r.target_layer == "Layer 1 (TreeSkeleton)"]
    layer_2 = [r.content for r in results if r.target_layer == "Layer 2 (SpanTable)"]
    antibodies = [r.content for r in results if "Antibodies" in r.target_layer or "Patterns" in r.target_layer]
    pre_scan = [r.content for r in results if "Pre-Scan" in r.target_layer]

    prompt = f"""[TASK DESCRIPTION: PRE-MINED 3-LAYER OPERAD PROMPT]
Target: {target_name}
AuthorityEffect: None.
Constitutional Firewall: stated region only; mints no authority.
Untrusted research proposals. The pre-mined fence below is not admitted immune guidance.

================================================================================
LAYER 0: ENVIRONMENT & AMBIENT ALGEBRAIC DOMAIN
================================================================================
{"---".join(layer_0)}

================================================================================
LAYER 1: COMPOSITE MORPHISM TREE SKELETON (DAG)
================================================================================
{"---".join(layer_1)}

================================================================================
LAYER 2: SPANTABLE INVARIANTS & EXACT RATIONAL BOUNDS
================================================================================
{"---".join(layer_2)}

================================================================================
PRE-MINED IMMUNE FENCE (ANTIBODIES & ANTI-PATTERNS)
================================================================================
{"---".join(antibodies)}

================================================================================
PRE-SCAN OBSTRUCTION PROFILE (FAILURE PRE-MORTEM)
================================================================================
{"---".join(pre_scan)}
"""
    return prompt


def run_operad_pre_miner_swarm(
    target_name: str = "MUB-6 Target A4",
    max_workers: int = 10,
    preferred_models: list[str] | None = None,
    env_file: Path | str | None = None,
    *, gateway=None, task_id: str | None = None, max_tokens: int = 400,
) -> OperadPreMinerReport:
    """Run ordered proposals through one caller-owned PFP budget.

    ``max_workers`` and ``env_file`` are retained compatibility arguments; no
    scheduler or credential resolver is created here. One explicit model is
    required. A new model/fallback requires a separate caller decision.
    """
    if gateway is None:
        raise ProviderConfigError("PFP_ACCOUNTED_GATEWAY_REQUIRED")
    if not preferred_models or len(preferred_models) != 1:
        raise ProviderConfigError("EXPLICIT_MODEL_REQUIRED: no implicit miner fallback")
    if type(task_id) is not str or not task_id.strip():
        raise ProviderConfigError("PFP_TASK_BINDING_REQUIRED")
    model = preferred_models[0]
    roles = build_10_mub6_miner_swarm([model] * 10)
    results: list[MinerResult] = []
    started = time.perf_counter()
    stopped = False
    system = (
        "You are an Operad Pre-Miner in the Symbol Game swarm.\n"
        "AuthorityEffect: None.\n"
        "Return scoped research proposals, not established mathematical facts.\n"
        "State uncertainty and obligations; do not claim to settle MUB(6)."
    )
    for role in roles:
        if stopped:
            results.append(MinerResult(role.miner_id, role.name, role.target_layer,
                model, "Not dispatched after accounting/transport stop", 0.0,
                "NOT_RUN", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}, 0.0))
            continue
        turn = _mine_turn(gateway, [model], system, role.prompt_instruction,
            max_tokens, task_id, f"{task_id}:{role.miner_id}")
        stopped = bool(turn["stop"])
        results.append(MinerResult(role.miner_id, role.name, role.target_layer,
            turn.get("model") or model,
            turn["content"] or turn.get("error") or "", turn["elapsed"],
            "UNVERIFIED" if turn["ok"] and not stopped else "REFUSED",
            _tokens(turn), turn["usage"].get("cost"), turn))
    counts = [row.tokens.get("total_tokens") for row in results]
    costs = [row.cost_usd for row in results]
    return OperadPreMinerReport(
        target_name, time.perf_counter() - started,
        sum(counts) if all(type(value) is int for value in counts) else None,
        sum(costs) if all(value is not None for value in costs) else None,
        results, synthesize_operad_prompt(target_name, results),
    )


__all__ = [
    "CHEAP_FALLBACK_MODELS",
    "DEFAULT_MINER_MODELS",
    "MinerResult",
    "MinerRole",
    "OperadPreMinerReport",
    "build_10_mub6_miner_swarm",
    "call_openrouter_miner",
    "run_operad_pre_miner_swarm",
    "synthesize_operad_prompt",
]
