"""Discrete Coboundary Scoring Use Cases and Algorithms.

AuthorityEffect: None (const).
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping, Sequence

from ..domain.aggregates.llm_turn_run_root import (
    OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    REFUSAL_CONSEQUENTIAL_WITHOUT_PACKET,
    REFUSAL_MARKDOWN_CLAIM_INJECTION,
    REFUSAL_MODEL_VERDICT_UNTRUSTED,
    REFUSAL_POSITIVE_TERMINAL_NEEDS_REPLAY,
    REFUSAL_PROSE_PROMPT_REFUSED,
    REFUSAL_REFUSAL_ERASURE,
    REFUSAL_VERIFIED_PROPOSAL_FORBIDDEN,
)
from ..domain.entities.coboundary_score import (
    REFUSAL_EXACT_WITHOUT_DUAL,
    REFUSAL_ILLEGAL_PROPOSAL,
    REFUSAL_NEGATIVE_MAGNITUDE,
    CandidateProposal,
    CoboundaryScoreResult,
    ResidualDropV1,
)
from ..domain.ports.scoring_port import ScoringPort, get_default_scoring_port
from ..domain.shared_kernel.exact import Exact, NotExactError, coerce_exact, to_canonical_string

REFUSAL_AUTHORITY_NON_NONE = "AUTHORITY_EFFECT_NON_NONE"
REFUSAL_EXACT_WITHOUT_DUAL_WITNESS = "EXACT_WITHOUT_DUAL_WITNESS"
# The omega cochain arrived carrying a value that is not an exact rational.
# There is no exact residual to report, so the score refuses instead of
# converting at the boundary.
REFUSAL_INEXACT_COCHAIN = "INEXACT_COCHAIN"

KILL_CONDITION_MAP: dict[str, str] = {
    "F-01_inherited_meaning": REFUSAL_PROSE_PROMPT_REFUSED,
    "F-02_syntax_implies_semantic": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "F-03_untested_equality": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "F-04_ontology_smuggling": REFUSAL_PROSE_PROMPT_REFUSED,
    "F-05_silent_quotient": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "F-06_ungrounded_extension": REFUSAL_CONSEQUENTIAL_WITHOUT_PACKET,
    "F-07_phantom_convergence": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "F-08_scope_creep_as_progress": REFUSAL_CONSEQUENTIAL_WITHOUT_PACKET,
    "F-09_authority_from_model_output": REFUSAL_MODEL_VERDICT_UNTRUSTED,
    "F-10_refusal_erasure": REFUSAL_REFUSAL_ERASURE,
    "F-11_answer_shaped_prompting": REFUSAL_CONSEQUENTIAL_WITHOUT_PACKET,
    "F-12_model_output_implies_execution": REFUSAL_MODEL_VERDICT_UNTRUSTED,
    "F-13_receipt_without_evidence": REFUSAL_POSITIVE_TERMINAL_NEEDS_REPLAY,
    "F-14_markdown_claim_injection": REFUSAL_MARKDOWN_CLAIM_INJECTION,
    "F-15_verified_proposal_forbidden": REFUSAL_VERIFIED_PROPOSAL_FORBIDDEN,
    "F-16_exact_without_dual_witness": REFUSAL_EXACT_WITHOUT_DUAL_WITNESS,
    "F-17_coverage_as_proof": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "F-18_lean_toy_as_mechanized": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "F-19_continuum_from_finite": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "F-20_authority_promotion": REFUSAL_AUTHORITY_NON_NONE,
    "SYNTAX_VALID_IMPLIES_SEMANTIC_TRUE": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "MODEL_OUTPUT_IMPLIES_EXECUTION": REFUSAL_MODEL_VERDICT_UNTRUSTED,
    "AUTHORITY_PROMOTION": REFUSAL_AUTHORITY_NON_NONE,
    "RECEIPT_WITHOUT_REPLAYABLE_EVIDENCE": REFUSAL_POSITIVE_TERMINAL_NEEDS_REPLAY,
    "NO_TEST_IMPLIES_PROVED_SAME": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "ADMITTED_WHOLE_IMPLIES_DECOMPOSITION": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "CONTINUUM_FROM_FINITE": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "SYNTHETIC_CURVE": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "LEAN_TOY_AS_MECHANIZED": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "COVERAGE_AS_PROOF": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
    "DUAL_WITNESS_MISSING": REFUSAL_EXACT_WITHOUT_DUAL_WITNESS,
    "ONTOLOGY_SMUGGLING": REFUSAL_PROSE_PROMPT_REFUSED,
    "MARKDOWN_CLAIM_INJECTION": REFUSAL_MARKDOWN_CLAIM_INJECTION,
    "REFUSAL_ERASURE": REFUSAL_REFUSAL_ERASURE,
    "VERIFIED_PROPOSAL_FORBIDDEN": REFUSAL_VERIFIED_PROPOSAL_FORBIDDEN,
    "FORCED_A_FROM_EMPTY_REGIME": REFUSAL_PROSE_PROMPT_REFUSED,
    "ONE_RULE_BUNDLES_UNDECLARED_PRIMITIVES": OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED,
}

REGISTERED_KILL_CONDITIONS = frozenset(KILL_CONDITION_MAP)


class EvaluateCoboundaryScoreUseCase:
    """Evaluates candidate proposals under discrete coboundary scoring."""

    def execute(
        self,
        proposal: CandidateProposal,
        total_open_obstructions: int = 10,
    ) -> CoboundaryScoreResult:
        # Distinct ids, not tuple length. `CandidateProposal` now refuses
        # duplicates outright, but scoring is the thing that turns a count into
        # an exactness verdict, so it does not delegate that guard: three
        # copies of one id against three open obstructions used to report a
        # full drop and `is_exact_candidate` True after repairing one.
        claimed_count = len(set(proposal.repaired_obstruction_ids))
        # A proposal may claim more repairs than there are open obstructions.
        # `post_residual_norm` was already clamped at zero, but `residual_drop`
        # and `normalized_efficiency` were computed from the raw claim, so
        # `residual_drop` stopped equalling `prior - post` and an overclaim
        # outranked an honest proposal: three claimed repairs against one open
        # obstruction scored drop 3 and efficiency 3.0 where the honest
        # proposal scored 1 and 1.0. Clamping the effective count restores
        # `drop == prior - post` and removes the incentive to inflate.
        #
        # Counting is the weak part of this: the ids are not checked against
        # the open set, so a proposal naming obstructions that are not open
        # still scores. Scoring against the actual open-obstruction set rather
        # than a bare total is the real repair, and it needs this signature to
        # carry that set.
        eliminated_count = min(claimed_count, max(0, total_open_obstructions))
        # This is a cardinality of claimed open ids, not the Phi1 functional.
        remaining_count = max(Fraction(0), Fraction(total_open_obstructions - eliminated_count))

        is_exact = remaining_count == 0 and proposal.dual_witness_ref is not None

        cost = coerce_exact(proposal.structural_cost, field="structural_cost")
        efficiency = Fraction(eliminated_count, 1) / (Fraction(1, 1) + cost)

        return CoboundaryScoreResult(
            proposal_id=proposal.proposal_id,
            prior_residual_norm=Fraction(total_open_obstructions),
            post_residual_norm=remaining_count,
            residual_drop=Fraction(eliminated_count),
            structural_cost=cost,
            normalized_efficiency=efficiency,
            is_legal=True,
            is_exact_candidate=is_exact,
            dual_witness_ref=proposal.dual_witness_ref,
        )


def l1_float(values: Sequence[float]) -> float:
    return float(sum(abs(float(value)) for value in values))


def l1_rational(values: Sequence[Fraction]) -> Fraction:
    return sum((abs(value) for value in values), Fraction(0))


def mass_from_magnitudes(magnitudes: Mapping[str, float]) -> float:
    total = 0.0
    for key, value in magnitudes.items():
        if type(value) not in (float, int):
            raise TypeError(f"magnitude for {key!r} must be float/int")
        magnitude = float(value)
        if magnitude < 0:
            raise ValueError(REFUSAL_NEGATIVE_MAGNITUDE)
        total += magnitude
    return total


def mass_from_ids(ids: Sequence[str], *, unit: float = 1.0) -> float:
    return float(len(set(ids))) * float(unit)


def residual_drop_mass(
    omega_mass: float,
    residual_mass: float,
    *,
    cost: float = 0.0,
) -> tuple[float, float | None, float]:
    if omega_mass < 0 or residual_mass < 0:
        raise ValueError(REFUSAL_NEGATIVE_MAGNITUDE)
    if cost < 0:
        raise ValueError("cost must be nonnegative")
    delta = float(omega_mass) - float(residual_mass)
    relative = delta / omega_mass if omega_mass > 0 else None
    return delta, relative, delta / (1.0 + float(cost))


def residual_colour_from_mass(
    residual_mass: float,
    *,
    dual_witness_present: bool = False,
    open_ids: Sequence[str] = (),
) -> str:
    if residual_mass < 0:
        raise ValueError(REFUSAL_NEGATIVE_MAGNITUDE)
    if residual_mass == 0.0 and not set(open_ids):
        return "Exact" if dual_witness_present else "Closed"
    return "Open"


def set_delta(
    before: Sequence[str],
    after: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    before_set, after_set = set(before), set(after)
    return (
        tuple(sorted(before_set - after_set)),
        tuple(sorted(after_set - before_set)),
        tuple(sorted(before_set & after_set)),
    )


def residual_drop_from_ids(
    before_ids: Sequence[str],
    after_ids: Sequence[str],
    *,
    cost: float = 0.0,
    dual_witness_ref: str | None = None,
    dual_witness_present: bool | None = None,
    declared_colour: str | None = None,
    legal: bool = True,
    refusal_code: str | None = None,
    unit: float = 1.0,
) -> ResidualDropV1:
    has_dual = dual_witness_present if dual_witness_present is not None else bool(dual_witness_ref)
    if not legal:
        omega_mass = mass_from_ids(before_ids, unit=unit)
        return ResidualDropV1(
            omega_mass=omega_mass,
            residual_mass=omega_mass,
            delta=-float("inf"),
            relative_drop=0.0,
            eliminated_ids=(),
            opened_ids=(),
            retained_ids=tuple(sorted(set(before_ids))),
            cost=float(cost),
            efficiency=-float("inf"),
            residual_colour="Open",
            dual_witness_present=has_dual,
            legal=False,
            refusal_code=refusal_code or REFUSAL_ILLEGAL_PROPOSAL,
        )

    omega_mass = mass_from_ids(before_ids, unit=unit)
    residual_mass = mass_from_ids(after_ids, unit=unit)
    delta, relative, efficiency = residual_drop_mass(omega_mass, residual_mass, cost=cost)
    eliminated, opened, retained = set_delta(before_ids, after_ids)
    colour = residual_colour_from_mass(
        residual_mass,
        dual_witness_present=has_dual,
        open_ids=after_ids,
    )
    if declared_colour == "Exact" and declared_colour != colour and not has_dual:
        raise ValueError(REFUSAL_EXACT_WITHOUT_DUAL)
    return ResidualDropV1(
        omega_mass=omega_mass,
        residual_mass=residual_mass,
        delta=delta,
        relative_drop=relative,
        eliminated_ids=eliminated,
        opened_ids=opened,
        retained_ids=retained,
        cost=float(cost),
        efficiency=efficiency,
        residual_colour=colour,
        dual_witness_present=has_dual,
        legal=True,
        refusal_code=None,
    )


def magnitudes_from_ledger_active(active_obstructions: Mapping[str, Any]) -> dict[str, float]:
    result: dict[str, float] = {}
    for obstruction_id, value in active_obstructions.items():
        if isinstance(value, (int, float)):
            result[obstruction_id] = float(value)
        elif isinstance(value, Mapping) and "magnitude" in value:
            result[obstruction_id] = float(value["magnitude"])
        elif hasattr(value, "magnitude"):
            result[obstruction_id] = float(value.magnitude)
        else:
            result[obstruction_id] = 1.0
    return result


def residual_drop_from_ledger_maps(
    before_map: Mapping[str, float],
    after_map: Mapping[str, float],
    *,
    cost: float = 0.0,
    dual_witness_ref: str | None = None,
    dual_witness_present: bool | None = None,
) -> ResidualDropV1:
    has_dual = dual_witness_present if dual_witness_present is not None else bool(dual_witness_ref)
    omega_mass = mass_from_magnitudes(before_map)
    residual_mass = mass_from_magnitudes(after_map)
    delta, relative, efficiency = residual_drop_mass(omega_mass, residual_mass, cost=cost)
    eliminated, opened, retained = set_delta(tuple(before_map), tuple(after_map))
    colour = residual_colour_from_mass(
        residual_mass,
        dual_witness_present=has_dual,
        open_ids=tuple(after_map),
    )
    return ResidualDropV1(
        omega_mass=omega_mass,
        residual_mass=residual_mass,
        delta=delta,
        relative_drop=relative,
        eliminated_ids=eliminated,
        opened_ids=opened,
        retained_ids=retained,
        cost=float(cost),
        efficiency=efficiency,
        residual_colour=colour,
        dual_witness_present=has_dual,
        legal=True,
        refusal_code=None,
    )


def rank_by_efficiency(scored_candidates: Sequence[ResidualDropV1]) -> list[ResidualDropV1]:
    return sorted(
        (result for result in scored_candidates if result.legal),
        key=lambda result: (
            result.efficiency if not math.isnan(result.efficiency) else -float("inf"),
            -result.cost,
        ),
        reverse=True,
    )


def _illegal_score(
    proposal: CandidateProposal,
    prior_norm: int | Fraction,
    refusal_reason: str,
) -> CoboundaryScoreResult:
    norm = Fraction(prior_norm)
    cost = coerce_exact(proposal.structural_cost, field="structural_cost")
    return CoboundaryScoreResult(
        proposal_id=proposal.proposal_id,
        prior_residual_norm=norm,
        post_residual_norm=norm,
        residual_drop=Fraction(0),
        structural_cost=cost,
        normalized_efficiency=None,
        is_legal=False,
        refusal_reason=refusal_reason,
    )


def _proposal_wire(proposal: CandidateProposal) -> dict[str, Any]:
    return {
        "proposal_id": proposal.proposal_id,
        "repaired_obstruction_ids": list(proposal.repaired_obstruction_ids),
        "cochain_delta": [
            [key, to_canonical_string(value)] for key, value in proposal.cochain_delta
        ],
        "structural_cost": to_canonical_string(proposal.structural_cost),
        "kill_triggers": list(proposal.kill_triggers),
        "admitted_constructors_used": list(proposal.admitted_constructors_used),
        "dual_witness_ref": proposal.dual_witness_ref,
        "authority_effect": proposal.authority_effect,
    }


def _policy(
    known_kill_conditions: Mapping[str, str] | None,
    admitted_constructors: Sequence[str] | set[str] | frozenset[str] | None,
) -> dict[str, Any]:
    return {
        "known_kill_conditions": dict(
            KILL_CONDITION_MAP if known_kill_conditions is None else known_kill_conditions
        ),
        "admitted_constructors": sorted(admitted_constructors)
        if admitted_constructors is not None
        else None,
    }


def score_discrete_proposal(
    current_obstruction_ids: Sequence[str] | set[str] | frozenset[str],
    proposal: CandidateProposal,
    *,
    known_kill_conditions: Mapping[str, str] | None = None,
    admitted_constructors: frozenset[str] | set[str] | Sequence[str] | None = None,
    scoring_port: ScoringPort | None = None,
) -> CoboundaryScoreResult:
    port = scoring_port or get_default_scoring_port()
    result = port.invoke_scoring(
        "score_discrete_proposal",
        {
            "obstructions": sorted(set(current_obstruction_ids)),
            "proposal": _proposal_wire(proposal),
            **_policy(known_kill_conditions, admitted_constructors),
        },
    )
    return CoboundaryScoreResult.from_dict(result)


def score_cochain_proposal(
    omega_cochain: Mapping[str, Exact | int | str],
    proposal: CandidateProposal,
    *,
    known_kill_conditions: Mapping[str, str] | None = None,
    admitted_constructors: frozenset[str] | set[str] | Sequence[str] | None = None,
    scoring_port: ScoringPort | None = None,
) -> CoboundaryScoreResult:
    # Boundary normalization only; Rust owns every norm, subtraction and comparison.
    try:
        wire = {
            key: to_canonical_string(coerce_exact(value, field=f"omega_cochain[{key!r}]"))
            for key, value in omega_cochain.items()
        }
    except NotExactError as exc:
        return _illegal_score(proposal, Fraction(0), f"{REFUSAL_INEXACT_COCHAIN}: {exc}")
    port = scoring_port or get_default_scoring_port()
    result = port.invoke_scoring(
        "score_cochain_proposal",
        {
            "omega_cochain": wire,
            "proposal": _proposal_wire(proposal),
            **_policy(known_kill_conditions, admitted_constructors),
        },
    )
    return CoboundaryScoreResult.from_dict(result)


def rank_candidate_proposals(
    *args: Any, scoring_port: ScoringPort | None = None, **kwargs: Any
) -> list[CoboundaryScoreResult]:
    port = scoring_port or get_default_scoring_port()
    if len(args) == 1 and isinstance(args[0], Sequence):
        if kwargs:
            raise TypeError("rank of existing scores accepts no proposal policy")
        action = "rank_scored_candidates"
        payload = {"scores": [result.to_dict() for result in args[0]]}
        for score in payload["scores"]:
            for field in ("schema_version", "family", "authority_effect"):
                score.pop(field)
    elif len(args) == 2:
        action = "rank_candidate_proposals"
        payload = {
            "obstructions": sorted(set(args[0])),
            "proposals": [_proposal_wire(proposal) for proposal in args[1]],
            **_policy(
                kwargs.pop("known_kill_conditions", None), kwargs.pop("admitted_constructors", None)
            ),
        }
        if kwargs:
            raise TypeError(f"Unexpected ranking options: {sorted(kwargs)}")
    else:
        raise TypeError("Invalid arguments for rank_candidate_proposals")
    return [
        CoboundaryScoreResult.from_dict(result) for result in port.invoke_scoring(action, payload)
    ]


__all__ = [
    "EvaluateCoboundaryScoreUseCase",
    "KILL_CONDITION_MAP",
    "REGISTERED_KILL_CONDITIONS",
    "l1_float",
    "l1_rational",
    "magnitudes_from_ledger_active",
    "mass_from_ids",
    "mass_from_magnitudes",
    "rank_by_efficiency",
    "rank_candidate_proposals",
    "residual_colour_from_mass",
    "residual_drop_from_ids",
    "residual_drop_from_ledger_maps",
    "residual_drop_mass",
    "score_cochain_proposal",
    "score_discrete_proposal",
    "set_delta",
]
