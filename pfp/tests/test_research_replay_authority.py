"""Research-to-replay preserves the v1 wire identity and refuses promotion."""

import hashlib
import json

import pytest

from governance.contracts import AuthorityEffect
from pfp.domain.entities.research_packets import ResearchStepPacket


def _step():
    return ResearchStepPacket("a" * 64, "b" * 64, 2, 3)


def test_research_step_replays_with_exact_v1_none_and_causal_bindings():
    trace = _step().to_replay_trace("c" * 64, "evidence_only_human_review_required")
    expected = {
        "schema_version": "core.replay_trace.v1", "paper_sha256": "a" * 64,
        "proposal_sha256": "b" * 64, "gate_receipt_sha256": "c" * 64,
        "loop_pass": 2, "step_index": 3,
        "status": "evidence_only_human_review_required", "authority_effect": "none",
    }
    raw = json.dumps(expected, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    assert trace.canonical_payload() == expected
    assert trace.canonical_bytes() == raw
    assert trace.replay_hash == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("effect", [AuthorityEffect.EvidenceOnly, AuthorityEffect.StateTransition, "none"])
def test_conversion_revalidates_mutated_authority_instead_of_erasing_it(effect):
    step = _step()
    step.authority_effect = effect
    with pytest.raises(ValueError, match="research step packets must carry AuthorityEffect::None"):
        step.to_replay_trace("c" * 64, "human_review")


def test_conversion_does_not_erase_a_mutated_causal_identity():
    step = _step()
    step.proposal_sha256 = "not-a-digest"
    with pytest.raises(ValueError, match="proposal_sha256"):
        step.to_replay_trace("c" * 64, "human_review")
