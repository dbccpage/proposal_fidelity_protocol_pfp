"""Unit tests for Prompt Civilization demographic tiers and admission firewall.

AuthorityEffect: None.
"""

from fractions import Fraction

import pytest

from omega_engine_prompt_civilization.domain.models import (
    CivilizationPrompt,
    CivilizationState,
    PopulationTier,
    UnauthorizedAdmissionError,
)


def test_civilization_wild_registration():
    state = CivilizationState()
    prompt = state.register_wild_prompt("p1", "instruction text")
    assert prompt.prompt_id == "p1"
    assert prompt.tier == PopulationTier.WILD
    assert prompt.pagerank_score == Fraction(0, 1)
    assert prompt.authority_effect == "None"


def test_civilization_candidate_promotion():
    state = CivilizationState()
    state.register_wild_prompt("p1", "instruction text")
    dec = state.promote_to_candidate("p1", pagerank_score=Fraction(3, 10))
    assert dec.from_tier == PopulationTier.WILD
    assert dec.to_tier == PopulationTier.CANDIDATE
    assert not dec.is_admitted
    assert state.prompts["p1"].pagerank_score == Fraction(3, 10)


def test_civilization_reviewed_promotion():
    state = CivilizationState()
    state.register_wild_prompt("p1", "instruction text")
    state.promote_to_candidate("p1")
    dec = state.promote_to_reviewed("p1")
    assert dec.to_tier == PopulationTier.REVIEWED
    assert not dec.is_admitted


def test_civilization_admitted_requires_cryptographic_signature():
    state = CivilizationState()
    state.register_wild_prompt("p1", "instruction text")
    state.promote_to_candidate("p1")
    state.promote_to_reviewed("p1")

    # Unsigned or invalid signature must be rejected with UnauthorizedAdmissionError
    with pytest.raises(UnauthorizedAdmissionError):
        state.promote_to_admitted("p1", operator_signature=None)

    with pytest.raises(UnauthorizedAdmissionError):
        state.promote_to_admitted("p1", operator_signature="forged_signature")

    # F1 (P0 Security): prefix spoofing and forged tokens MUST be refused
    with pytest.raises(UnauthorizedAdmissionError):
        state.promote_to_admitted("p1", operator_signature="SIG_HUMAN_OPERATOR_forged")

    with pytest.raises(UnauthorizedAdmissionError):
        state.promote_to_admitted("p1", operator_signature="sig:ed25519:forged")

    with pytest.raises(UnauthorizedAdmissionError):
        state.promote_to_admitted("p1", operator_signature="sig:ed25519:" + ("ab" * 64))
    assert state.prompts["p1"].tier is PopulationTier.REVIEWED
    assert state.prompts["p1"].authority_effect == "None"


def test_civilization_zero_float_enforcement():
    with pytest.raises(TypeError, match="Zero-Float"):
        CivilizationPrompt(
            prompt_id="p_bad",
            content="test",
            tier=PopulationTier.WILD,
            pagerank_score=0.75,  # type: ignore
        )


def test_civilization_cemetery_refusal():
    state = CivilizationState()
    state.register_wild_prompt("p1", "malicious payload")
    dec = state.promote_to_cemetery("p1", reason="Malicious prompt injection attempt")
    assert dec.to_tier == PopulationTier.CEMETERY
    assert not dec.is_admitted
    assert state.prompts["p1"].tier == PopulationTier.CEMETERY
