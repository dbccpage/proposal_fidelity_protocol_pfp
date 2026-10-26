"""Test Arm Configuration Difference (U25).

Enforces that Arm A (Glyph Packet) and Arm C (Plain Text) differ in
strictly one configuration key: 'representation'.
AuthorityEffect: None.
"""
from __future__ import annotations

import pytest

from omega_engine_pfp.domain.representation.models import (
    ARM_A_CONFIG,
    ARM_C_CONFIG,
    get_arm_config,
)


def _compute_differing_keys(config_a: dict, config_c: dict) -> set[str]:
    all_keys = set(config_a.keys()) | set(config_c.keys())
    return {k for k in all_keys if config_a.get(k) != config_c.get(k)}


def test_arm_a_and_arm_c_differ_in_strictly_one_key() -> None:
    """Invariant (U25):

    Arm A and Arm C differ in strictly one key: 'representation'.
    All other keys (controller, prompt_regime, grammar_strength, carrier_mask, authority_effect)
    MUST be identical.
    """
    arm_a = get_arm_config("ARM_A")
    arm_c = get_arm_config("ARM_C")

    differing = _compute_differing_keys(arm_a, arm_c)
    assert differing == {"representation"}, f"Expected diff only in 'representation', got {differing}"

    assert arm_a["representation"] == "GLYPH_PACKET"
    assert arm_c["representation"] == "PLAIN_TEXT"

    # Inward invariant assertions
    assert arm_a["controller"] == arm_c["controller"]
    assert arm_a["prompt_regime"] == arm_c["prompt_regime"]
    assert arm_a["grammar_strength"] == arm_c["grammar_strength"]
    assert arm_a["carrier_mask"] == arm_c["carrier_mask"]
    assert arm_a["authority_effect"] == "None"
    assert arm_c["authority_effect"] == "None"


def test_mutation_kill_gate_additional_differing_key_fails() -> None:
    """Mutation Kill Gate (U25):

    If an arm configuration alters controller or prompt regime in addition to representation,
    the invariant gate MUST fail.
    """
    mutated_c = dict(ARM_C_CONFIG)
    mutated_c["controller"] = "UNFENCED_CONTROLLER"

    differing = _compute_differing_keys(ARM_A_CONFIG, mutated_c)
    assert len(differing) == 2
    assert differing != {"representation"}


def test_get_arm_config_rejects_unknown_arm() -> None:
    """Verify get_arm_config raises KeyError on invalid arm identifier."""
    with pytest.raises(KeyError, match="Unknown arm_id"):
        get_arm_config("ARM_Z_INVALID")
