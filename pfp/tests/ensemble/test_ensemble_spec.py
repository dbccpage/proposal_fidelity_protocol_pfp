"""Tests for Multi-Model Allosteric Ensembles (U20).

Enforces:
- <=70B parameter ceiling refusal for any model.
- Lineage cap refusal for over-represented base model families.
- Exact rational reproduction of the Hill quorum witness table:
  1 vote -> QUIESCENT (1/17)
  2 votes -> UNKNOWN (1/2)
  3 votes -> ACTIVATE (81/97)
- Calibration matrix (joint error rate, marginal product, Cohen's kappa) and Neff.
AuthorityEffect: None.
"""
from __future__ import annotations

from fractions import Fraction
import pytest

from pfp.domain.ensemble.models import (
    EnsembleRole,
    EnsembleSpec,
    ModelRef,
    compute_ensemble_calibration,
)


def _build_valid_members() -> tuple[ModelRef, ...]:
    return (
        ModelRef(model_id="meta-llama/llama-3.3-70b-instruct", total_params_b=70.0, lineage="llama"),
        ModelRef(model_id="qwen/qwen-2.5-32b-instruct", total_params_b=32.0, lineage="qwen"),
        ModelRef(model_id="mistralai/mistral-small-24b-instruct", total_params_b=24.0, lineage="mistral"),
    )


def test_ensemble_refuses_members_exceeding_70b_ceiling() -> None:
    """Invariant (U20):

    Ensemble construction refuses any member exceeding the 70B parameter ceiling.
    """
    valid = _build_valid_members()
    spec = EnsembleSpec(members=valid, role=EnsembleRole.VERIFY)
    assert len(spec.members) == 3

    # 72B member (e.g. qwen/qwen-2.5-72b-instruct) must be refused
    m_72b = ModelRef(model_id="qwen/qwen-2.5-72b-instruct", total_params_b=72.0, lineage="qwen_72b")
    with pytest.raises(ValueError, match="exceeds the 70.0B parameter ceiling"):
        EnsembleSpec(members=(m_72b,), role=EnsembleRole.VERIFY)

    # 235B member (e.g. qwen/qwen3-235b-a22b) must be refused
    m_235b = ModelRef(model_id="qwen/qwen3-235b-a22b", total_params_b=235.0, lineage="qwen_giant")
    with pytest.raises(ValueError, match="exceeds the 70.0B parameter ceiling"):
        EnsembleSpec(members=(m_235b,), role=EnsembleRole.VERIFY)


def test_ensemble_refuses_lineage_count_exceeding_cap() -> None:
    """Invariant (U20):

    Ensemble construction refuses any lineage count exceeding max_members_per_lineage.
    """
    # Two models sharing base Llama lineage (e.g. base Llama-70B and DeepSeek distill onto Llama)
    llama_base = ModelRef(model_id="meta-llama/llama-3.3-70b-instruct", total_params_b=70.0, lineage="llama")
    llama_distill = ModelRef(
        model_id="deepseek-ai/deepseek-r1-distill-llama-70b", total_params_b=70.0, lineage="llama"
    )

    with pytest.raises(ValueError, match="Lineage 'llama' has 2 members, exceeding the cap of 1"):
        EnsembleSpec(
            members=(llama_base, llama_distill),
            role=EnsembleRole.VERIFY,
            max_members_per_lineage=1,
        )

    # With cap = 2, it is admitted
    spec_cap2 = EnsembleSpec(
        members=(llama_base, llama_distill),
        role=EnsembleRole.VERIFY,
        max_members_per_lineage=2,
    )
    assert len(spec_cap2.members) == 2


def test_exact_allosteric_quorum_witness_reproduction() -> None:
    """Witness Test (U20):

    With n = 4, Kd = 2, activation 7/10 and quiescence 1/10:
    - 0 votes: H(0) = 0 -> QUIESCENT
    - 1 vote:  H(1) = 1/17 <= 1/10 -> QUIESCENT
    - 2 votes: H(2) = 16/32 = 1/2 -> UNKNOWN
    - 3 votes: H(3) = 81/97 >= 7/10 -> ACTIVATE
    """
    spec = EnsembleSpec(members=_build_valid_members(), role=EnsembleRole.VERIFY)

    state_0, resp_0 = spec.evaluate_quorum(0)
    assert state_0 == "QUIESCENT"
    assert resp_0 == Fraction(0, 1)

    state_1, resp_1 = spec.evaluate_quorum(1)
    assert state_1 == "QUIESCENT"
    assert resp_1 == Fraction(1, 17)

    state_2, resp_2 = spec.evaluate_quorum(2)
    assert state_2 == "UNKNOWN"
    assert resp_2 == Fraction(1, 2)

    state_3, resp_3 = spec.evaluate_quorum(3)
    assert state_3 == "ACTIVATE"
    assert resp_3 == Fraction(81, 97)


def test_mutation_kill_gate_premature_activation() -> None:
    """Mutation Kill Gate (U20):

    If activation threshold is lowered to > quiescence (1/10),
    2 votes (1/2) prematurely activates, turning the witness RED.
    """
    spec = EnsembleSpec(members=_build_valid_members(), role=EnsembleRole.VERIFY)
    _, resp_2 = spec.evaluate_quorum(2)

    # Under true gate, 2 votes is strictly UNKNOWN
    state_2, _ = spec.evaluate_quorum(2)
    assert state_2 == "UNKNOWN"
    assert state_2 != "ACTIVATE"

    # Mutated check: if threshold were 1/10
    mutated_floor = Fraction(1, 10)
    assert resp_2 > mutated_floor  # 1/2 > 1/10, so mutation would falsely activate


def test_pairwise_correlation_and_neff_computation() -> None:
    """Verify calibration matrix calculation and effective verifier count Neff."""
    # 10 test cases
    # Model A and Model B make identical errors on cases 0 and 1 (correlated)
    # Model C makes error only on case 5 (largely independent)
    eval_results = {
        "model_a": [False, False, True, True, True, True, True, True, True, True],
        "model_b": [False, False, True, True, True, True, True, True, True, True],
        "model_c": [True, True, True, True, True, False, True, True, True, True],
    }

    reports, neff = compute_ensemble_calibration(eval_results)
    assert len(reports) == 3  # (A, B), (A, C), (B, C)

    ab_report = next(r for r in reports if r.model_a == "model_a" and r.model_b == "model_b")
    assert ab_report.joint_error_rate == 0.2
    assert ab_report.marginal_error_product == 0.04
    assert ab_report.cohens_kappa == 1.0  # Perfect agreement

    # Due to A and B having perfect agreement, effective verifier count is penalized (Neff < 3)
    assert neff < 3.0
    assert neff >= 1.0
