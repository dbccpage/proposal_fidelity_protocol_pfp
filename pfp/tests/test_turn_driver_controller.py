"""Tests for TurnDriverController, strict descent gating, and cemetery routing (U05).

Validates:
- Next prompt generation from engine state.
- Strict descent acceptance and ddc_trace.jsonl logging.
- Non-descending candidate refusal and cemetery.jsonl logging.
- Malformed candidate refusal and cemetery.jsonl logging.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from pfp.controllers.turn_driver_controller import (
    DriverMovePacket,
    EngineTurnStateV1,
    PromptPolicyV1,
    TurnDriverController,
)


@pytest.fixture
def turn_driver_env(tmp_path: Path):
    trace_dir = tmp_path / "traces"
    state = EngineTurnStateV1(
        round_seq=0,
        specification_digest="spec_abc_123",
        current_phi1=5,
        current_gamma2=2,
        open_defect_count=7,
        previous_code=None,
        previous_diff=None,
        open_obligations=["repair_boundary_deficit"],
        promoted_operands=["operand_homology"],
    )
    policy = PromptPolicyV1(
        regime_id="a" * 64,
        regime_kind="SYMBOL_GAME_ROUND",
        admitted_constructors=["repair_edge"],
        kill_conditions=["budget_exhausted"],
        required_reply_fields=["candidate_id", "proposed_diff"],
        max_tokens=2048,
    )
    controller = TurnDriverController(trace_dir=trace_dir, state=state, policy=policy)
    return controller, trace_dir


def test_turn_driver_next_prompt(turn_driver_env):
    controller, _ = turn_driver_env
    res = controller.next_prompt()
    assert res.is_ok, res.unwrap_err()
    artifact = res.unwrap()
    assert artifact["regime_kind"] == "SYMBOL_GAME_ROUND"
    assert artifact["regime_id"] == controller.policy.regime_id
    assert artifact["authority_effect"] == "None"
    assert len(artifact["prompt_artifact_id"]) == 64
    assert artifact == controller.next_prompt().unwrap()


@pytest.mark.parametrize(("field", "value"), [
    ("specification_digest", "different_specification"),
    ("previous_code", "fn previous() {}"),
    ("cemetery_count", 1),
])
def test_same_round_state_changes_have_distinct_native_prompt_ids(turn_driver_env, field, value):
    controller, _ = turn_driver_env
    original = controller.next_prompt().unwrap()
    controller.state = replace(controller.state, **{field: value})
    changed = controller.next_prompt().unwrap()
    assert original["prompt_artifact_id"] != changed["prompt_artifact_id"]


@pytest.mark.parametrize(("field", "value"), [
    ("regime_id", "b" * 64),
    ("max_tokens", 2049),
    ("required_reply_fields", ["SUMMARY"]),
])
def test_policy_configuration_changes_identity_without_changing_body(turn_driver_env, field, value):
    controller, _ = turn_driver_env
    original = controller.next_prompt().unwrap()
    controller.policy = replace(controller.policy, **{field: value})
    changed = controller.next_prompt().unwrap()
    assert original["prompt_body_sha256"] == changed["prompt_body_sha256"]
    assert original["prompt_artifact_id"] != changed["prompt_artifact_id"]
    assert changed["regime_id"] == controller.policy.regime_id


def test_effective_policy_sets_and_defaults_have_one_identity(turn_driver_env):
    controller, _ = turn_driver_env
    controller.policy.kill_conditions = []
    controller.policy.required_reply_fields = []
    original = controller.next_prompt().unwrap()
    controller.policy.admitted_constructors *= 2
    controller.policy.kill_conditions = original["kill_conditions"] * 2
    controller.policy.required_reply_fields = list(reversed(original["required_reply_fields"]))
    assert controller.next_prompt().unwrap() == original


@pytest.mark.parametrize(("field", "value"), [
    ("regime_id", "opaque_regime"),
    ("regime_id", "A" * 64),
    ("regime_kind", " "),
    ("required_reply_fields", ["bad\nfield"]),
    ("max_tokens", 0),
    ("max_tokens", True),
    ("max_tokens", {"$serde_json::private::Number": "4096"}),
    ("max_tokens", 1_048_577),
])
def test_native_prompt_refusals_reach_the_controller_with_complete_evidence(
    turn_driver_env, field, value
):
    controller, trace_dir = turn_driver_env
    controller.policy = replace(controller.policy, **{field: value})
    result = controller.next_prompt()
    assert result.is_err
    refusal = result.unwrap_err()
    assert refusal.code == "TURN_DRIVER_PROMPT_INVALID"
    outcome = json.loads(dict(refusal.details)["native_outcome"])
    assert outcome["success"] is False and outcome["result"] is None
    assert outcome["authority_effect"] == "None"
    assert outcome["error"].startswith("TURN_DRIVER_PROMPT_INVALID:")
    assert not list(trace_dir.glob("*.jsonl"))


def test_rendered_body_normalizes_line_endings_while_state_provenance_stays_bound(turn_driver_env):
    import hashlib

    controller, _ = turn_driver_env
    controller.state.previous_diff = "+ λ🙂\r\n- x\r"
    original = controller.next_prompt().unwrap()
    body = (
        "# Symbol Game Specification Digest\n\nSpec Hash: spec_abc_123\nRound: 0\n\n"
        "## Previous Code Diff\n```diff\n+ λ🙂\n- x\n\n```\n\n"
        "## Open Obligations\n- repair_boundary_deficit\n\n"
        "## Active Promoted Operands\n- Operand: operand_homology\n\n"
    ).encode("utf-8")
    assert original["prompt_body_sha256"] == hashlib.sha256(body).hexdigest()
    assert original["prompt_body_byte_count"] == len(body)
    controller.state.previous_diff = "+ λ🙂\n- x\n"
    changed = controller.next_prompt().unwrap()
    assert changed["prompt_body_sha256"] == original["prompt_body_sha256"]
    assert changed["prompt_artifact_id"] != original["prompt_artifact_id"]


def test_real_native_driver_matches_independent_python_canonical_golden(tmp_path):
    """Golden digest comes from Python canonical framing and a literal LF body."""
    import subprocess

    state = EngineTurnStateV1(
        round_seq=7, specification_digest="spec_digest_abc123", current_phi1=5,
        current_gamma2=2, open_defect_count=7, previous_code="fn old() {}",
        previous_diff="+fn new() {}\n", open_obligations=["obs_1", "obs_2"],
        promoted_operands=["operand_a", "operand_b"], cemetery_count=1,
    )
    policy = PromptPolicyV1(
        regime_id="a" * 64, regime_kind="SYMBOL_GAME_ROUND",
        admitted_constructors=["repair_edge", "replace_edge"],
        kill_conditions=["budget_exceeded", "invalid_shape"],
        required_reply_fields=["candidate_id", "proposed_diff"], max_tokens=4096,
    )
    controller = TurnDriverController(tmp_path / "traces", state, policy)
    artifact = controller.next_prompt().unwrap()
    assert artifact["prompt_artifact_id"] == (
        "d21f32788892816f021af26c94e4619b4024b3469737c45646649d2dab46c4db"
    )
    assert artifact["prompt_body_sha256"] == (
        "3b73bddba3e289a2c212a6c358ac5ffdff542c44bf57ca8b8cc28a938f245688"
    )
    assert artifact["prompt_body_byte_count"] == 233
    envelope = {
        "payload": {
            "policy": dict(reversed(policy.to_dict().items())),
            "state": dict(reversed(state.to_dict().items())),
        },
        "action": "turn_driver_next_prompt",
        "schema_version": "core.symbol-game.runtime-request.v1",
    }
    output = subprocess.run(
        [str(controller.host.binary_path), "invoke"],
        input=json.dumps(envelope).encode("utf-8"), capture_output=True,
        timeout=5, check=False,
    )
    assert output.returncode == 0, output.stderr
    outcome = json.loads(output.stdout)
    assert outcome["success"] is True and outcome["authority_effect"] == "None"
    assert outcome["result"] == artifact


def test_turn_driver_step_strict_descent_and_cemetery_routing(turn_driver_env):
    controller, trace_dir = turn_driver_env

    # 1. Improving candidate: Phi1 5 -> 3, Gamma2 2 -> 2 (strict decrease on Phi1)
    cand_improving = DriverMovePacket(
        candidate_id="cand_improving_01",
        proposed_diff="--- a\n+++ a\n@@ -1 +1 @@\n-defect\n+clean",
        declared_phi1=3,
        declared_gamma2=2,
        summary="Discharged 2 boundary defects",
    )

    res1 = controller.step(cand_improving)
    assert res1.is_ok, res1.unwrap_err()
    new_state = res1.unwrap()
    assert new_state.round_seq == 1
    assert new_state.current_phi1 == 3
    assert new_state.current_gamma2 == 2
    assert new_state.open_defect_count == 5

    # Check ddc_trace.jsonl has 1 row
    ddc_trace_file = trace_dir / "ddc_trace.jsonl"
    assert ddc_trace_file.exists()
    trace_lines = [json.loads(line) for line in ddc_trace_file.read_text("utf-8").strip().splitlines()]
    assert len(trace_lines) == 1
    assert trace_lines[0]["seq"] == 0
    assert trace_lines[0]["actor"] == "cand_improving_01"

    # 2. Non-improving candidate: Phi1 3 -> 3, Gamma2 2 -> 2 (zero strict decrease)
    # MUST BE REJECTED TO CEMETERY!
    cand_stagnant = DriverMovePacket(
        candidate_id="cand_stagnant_02",
        proposed_diff="--- a\n+++ a\n@@ -1 +1 @@\n-no\n+progress",
        declared_phi1=3,
        declared_gamma2=2,
        summary="No progress made",
    )

    res2 = controller.step(cand_stagnant)
    assert res2.is_err
    assert res2.unwrap_err().code == "RejectedNonDescent"
    # State MUST NOT advance!
    assert controller.state.round_seq == 1
    assert controller.state.cemetery_count == 1

    # Check cemetery.jsonl has 1 row
    cemetery_file = trace_dir / "cemetery.jsonl"
    assert cemetery_file.exists()
    cemetery_lines = [json.loads(line) for line in cemetery_file.read_text("utf-8").strip().splitlines()]
    assert len(cemetery_lines) == 1
    assert cemetery_lines[0]["candidate_id"] == "cand_stagnant_02"
    assert cemetery_lines[0]["rejection_reason"] == "NON_DESCENDING_CANDIDATE"

    # 3. Malformed candidate: empty diff
    cand_malformed = DriverMovePacket(
        candidate_id="cand_empty_03",
        proposed_diff="",
        declared_phi1=1,
        declared_gamma2=1,
        summary="Empty diff",
    )

    res3 = controller.step(cand_malformed)
    assert res3.is_err
    assert res3.unwrap_err().code == "RejectedMalformed"
    assert controller.state.round_seq == 1
    assert controller.state.cemetery_count == 2

    # Cemetery now has 2 rows
    cemetery_lines = [json.loads(line) for line in cemetery_file.read_text("utf-8").strip().splitlines()]
    assert len(cemetery_lines) == 2
    assert cemetery_lines[1]["candidate_id"] == "cand_empty_03"
    assert cemetery_lines[1]["rejection_reason"] == "MALFORMED_EMPTY_DIFF"
