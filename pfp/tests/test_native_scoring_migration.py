"""Regression checks for native scoring delegation. AuthorityEffect: None."""

from fractions import Fraction

import pytest

from pfp.domain.entities.coboundary_score import CandidateProposal
from pfp.domain.ports import scoring_port as registry
from pfp.domain.ports.scoring_port import NativeScoringRefusal
from pfp.infrastructure.adapters.scoring_rust import RustScoringAdapter
from pfp.use_cases.research import (
    ResearchClaimVerifierUnavailable,
    VerifyResearchClaimUseCase,
)
from pfp.use_cases.scoring import (
    rank_candidate_proposals,
    score_cochain_proposal,
    score_discrete_proposal,
)


def test_missing_port_refuses_without_python_calculation(monkeypatch):
    monkeypatch.setattr(registry, "_DEFAULT_PORT", None)
    with pytest.raises(NativeScoringRefusal) as exc:
        score_discrete_proposal(("x",), CandidateProposal("p"))
    assert exc.value.code == "SCORING_PORT_UNAVAILABLE"


def test_native_exact_residual_policy_and_total_order():
    port = RustScoringAdapter()
    proposal = CandidateProposal(
        "tiny", cochain_delta=(("x", Fraction(1)),), dual_witness_ref="a" * 64
    )
    score = score_cochain_proposal({"x": Fraction(10**30 + 1, 10**30)}, proposal, scoring_port=port)
    assert score.post_residual_norm == Fraction(1, 10**30)
    assert not score.is_exact_candidate
    assert port.last_outcome["action"] == "score_cochain_proposal"
    killed = score_discrete_proposal(
        ("x",),
        CandidateProposal("bad", kill_triggers=("blocked",)),
        known_kill_conditions={"blocked": "DECLARED_REFUSAL"},
        scoring_port=port,
    )
    assert killed.refusal_reason == "DECLARED_REFUSAL"
    allowed = score_discrete_proposal(
        ("x",),
        CandidateProposal("ok", kill_triggers=("unknown",)),
        known_kill_conditions={},
        scoring_port=port,
    )
    assert allowed.is_legal
    ranked = rank_candidate_proposals([killed, score, allowed], scoring_port=port)
    assert ranked[-1].proposal_id == "bad"
    assert ranked[0].proposal_id == "tiny"
    assert port.last_outcome["action"] == "rank_scored_candidates"


def test_host_failure_is_typed_and_retains_outcome():
    from operations.domain.rop.result import Ok

    class RefusingHost:
        def invoke_runtime(self, action, payload):
            return Ok(
                {"action": action, "success": False, "error": "NO_NATIVE_PORT", "result": None}
            )

    adapter = RustScoringAdapter(RefusingHost())
    with pytest.raises(NativeScoringRefusal) as exc:
        score_discrete_proposal(("x",), CandidateProposal("p"), scoring_port=adapter)
    assert exc.value.code == "NATIVE_SCORING_REFUSED"
    assert adapter.last_outcome["error"] == "NO_NATIVE_PORT"


def test_research_claim_is_not_licensed_by_unchecked_bundle():
    with pytest.raises(ResearchClaimVerifierUnavailable) as exc:
        VerifyResearchClaimUseCase().execute(object(), object())
    assert exc.value.code == "RESEARCH_CLAIM_VERIFIER_UNAVAILABLE"
