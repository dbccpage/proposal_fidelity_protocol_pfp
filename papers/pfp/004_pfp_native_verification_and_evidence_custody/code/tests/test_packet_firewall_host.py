"""
Tests for the packet firewall host and its three firewalls.
Reference: Paper 032 (PO-032).
"""

import hashlib

from packet_firewall_host import (
    DerivationStep,
    FirewallRefusalCode,
    PacketFirewallHost,
    PacketKernel,
)


def test_packet_kernel_deterministic_hash():
    """4-field packet kernel generates deterministic SHA-256 digest."""
    p1 = PacketKernel(contract="CONTRACT_SG_V1", task="T01", payload={"step": 1})
    p2 = PacketKernel(contract="CONTRACT_SG_V1", task="T01", payload={"step": 1})
    assert p1.compute_hash() == p2.compute_hash()
    assert len(p1.compute_hash()) == 64


def test_first_token_op_linter():
    """Every statement must begin with a declared operator."""
    host = PacketFirewallHost()

    ok, op = host.lint_first_token_op("ASSERT (a -> b) = 1")
    assert ok is True
    assert op == "ASSERT"

    # Undeclared op QED or LAND must fail
    ok_land, err_land = host.lint_first_token_op("LAND gamma")
    assert ok_land is False
    assert "undeclared" in err_land.lower()

    ok_qed, err_qed = host.lint_first_token_op("QED")
    assert ok_qed is False
    assert "undeclared" in err_qed.lower()


def test_fw_carrier_pinned_codepoints():
    """FW-CARRIER: detects and rejects codepoints outside the declared alphabet."""
    host = PacketFirewallHost()

    # Valid ASCII and Greek letters
    v_valid = host.check_fw_carrier("ASSERT alpha -> beta")
    assert v_valid.admitted is True

    # Invalid control character / unpinned symbol
    v_invalid = host.check_fw_carrier("ASSERT alpha \x07 bell")
    assert v_invalid.admitted is False
    assert v_invalid.refusal_code == FirewallRefusalCode.FW_CARRIER_VIOLATION


def test_fw_move_unpriced_axiom_refusal():
    """FW-MOVE: refuses derivation steps using unpriced or undeclared rules."""
    host = PacketFirewallHost()
    licensed_rules = {"R1_COMMUTE": {"cost": 1}}

    # Licensed rule
    step_valid = DerivationStep(
        op="REDUCE",
        position=0,
        rule_id="R1_COMMUTE",
        substitution={},
        pre_state_hash="dummy",
        post_state_hash="dummy",
        content="REDUCE R1",
    )
    v_valid = host.check_fw_move(step_valid, licensed_rules)
    assert v_valid.admitted is True

    # Unlicensed rule
    step_invalid = DerivationStep(
        op="REDUCE",
        position=0,
        rule_id="R99_SMUGGLED",
        substitution={},
        pre_state_hash="dummy",
        post_state_hash="dummy",
        content="REDUCE R99",
    )
    v_invalid = host.check_fw_move(step_invalid, licensed_rules)
    assert v_invalid.admitted is False
    assert v_invalid.refusal_code == FirewallRefusalCode.FW_MOVE_VIOLATION


def test_fw_replay_independent_host_verification():
    """FW-REPLAY: host re-executes rewrite and verifies pre/post digests fail-closed."""
    host = PacketFirewallHost()
    init_state = "abc"
    init_hash = hashlib.sha256(init_state.encode("utf-8")).hexdigest()

    def mock_apply(s: str, pos: int, rule: str, sub: dict) -> str:
        return s.replace("b", "x")

    expected_post = "axc"
    expected_post_hash = hashlib.sha256(expected_post.encode("utf-8")).hexdigest()

    # Valid step
    step_good = DerivationStep(
        op="CUT",
        position=1,
        rule_id="R_REP",
        substitution={},
        pre_state_hash=init_hash,
        post_state_hash=expected_post_hash,
        content="CUT b->x",
    )
    v_good = host.check_fw_replay(init_state, step_good, mock_apply)
    assert v_good.admitted is True

    # Forged post-hash
    step_forged = DerivationStep(
        op="CUT",
        position=1,
        rule_id="R_REP",
        substitution={},
        pre_state_hash=init_hash,
        post_state_hash="0000000000000000000000000000000000000000000000000000000000000000",
        content="CUT b->x",
    )
    v_bad = host.check_fw_replay(init_state, step_forged, mock_apply)
    assert v_bad.admitted is False
    assert v_bad.refusal_code == FirewallRefusalCode.FW_REPLAY_VIOLATION


def test_fw_carrier_pinned_alphabet_rejects_unpinned_codepoints():
    """FW-CARRIER: pinning alphabet to {a, b} strictly rejects z and Core."""
    host = PacketFirewallHost(carrier_alphabet={"a", "b"})

    # 'a' and 'b' with syntax spaces/arrows pass
    v_valid = host.check_fw_carrier("a -> b")
    assert v_valid.admitted is True

    # 'z' must be rejected
    v_z = host.check_fw_carrier("a -> z")
    assert v_z.admitted is False
    assert v_z.refusal_code == FirewallRefusalCode.FW_CARRIER_VIOLATION

    # 'Core' (Greek letter) must be rejected
    v_core = host.check_fw_carrier("a -> \u03a9")
    assert v_core.admitted is False
    assert v_core.refusal_code == FirewallRefusalCode.FW_CARRIER_VIOLATION

    # Strict payload check without syntax tolerance
    assert host.check_fw_payload_carrier("ab").admitted is True
    assert host.check_fw_payload_carrier("a b").admitted is False
    assert host.check_fw_payload_carrier("az").admitted is False
