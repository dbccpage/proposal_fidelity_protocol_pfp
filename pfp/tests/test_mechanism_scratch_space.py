"""C006 host-state projection controls; these are not a matched model campaign."""

import base64
import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from omega_engine_pfp.infrastructure.mechanism_scratch_space import (
    HostScratchLedger,
    prepare_scratch_cut_turn,
    stationary_cut_binding,
    stationary_repeat,
)


PROTOCOL = Path(__file__).resolve().parents[2] / (
    "omega_engine_pfp/tests/demo_004/a_mechanism/"
    "c006_host_scratch_space_vs_cot.md"
)
CLAIMS = {"a->b": 1, "b->c": 2, "c->a": 3, "b->d": 1, "d->a": 2, "c->d": 1}
BOARD_BYTES = json.dumps({"vertices": ["a", "b", "c", "d"], "claims": CLAIMS,
                         "weights": {edge: 1 for edge in CLAIMS}}, sort_keys=True).encode()


def ledger(**kwargs):
    return HostScratchLedger.from_host(
        board_bytes=BOARD_BYTES,
        claims=kwargs.pop("claims", CLAIMS),
        asserted_edges=tuple(CLAIMS),
        phi1=kwargs.pop("phi1", 8),
        cycle_residuals={"cycle_1": 0, "cycle_2": 3, "cycle_3": 5},
        closed_chords=("c->a",),
        **kwargs,
    )


def turn(state, **kwargs):
    return prepare_scratch_cut_turn(
        state,
        protocol_path=PROTOCOL,
        protocol_sha256=kwargs.pop("protocol_sha256", sha256(PROTOCOL.read_bytes()).hexdigest()),
        task_id="C006-public-K4",
        attempt_id=kwargs.pop("attempt_id", "turn-2"),
        **kwargs,
    )


def raw_reply(prepared, claims=CLAIMS):
    return json.dumps({
        "task_id": prepared.binding["task_id"],
        "attempt_id": prepared.binding["attempt_id"],
        "input_sha256": prepared.binding["input_sha256"],
        "answer": {"move": "CUT", "claims": claims},
    }).encode()


def test_am4_repeat_requires_same_candidate_same_host_state_and_stationary_result():
    state = ledger()
    prior = stationary_cut_binding(state, CLAIMS, observed_phi1=8)
    assert stationary_repeat(state, dict(reversed(list(CLAIMS.items()))), prior)
    changed_cut = {**CLAIMS, "b->d": 0}
    assert not stationary_repeat(state, changed_cut, prior)
    changed_state = ledger(claims={**CLAIMS, "a->b": 2})
    assert not stationary_repeat(changed_state, CLAIMS, prior)
    changed_board = replace(state, board_sha256="f" * 64)
    assert not stationary_repeat(changed_board, CLAIMS, prior)
    with pytest.raises(ValueError, match="NOT_STATIONARY"):
        stationary_cut_binding(state, CLAIMS, observed_phi1=7)


def test_history_and_detector_counters_do_not_change_mathematical_state_binding():
    state = ledger()
    prior = stationary_cut_binding(state, CLAIMS, observed_phi1=8)
    later = replace(state, stationary_counter=1, last_move_sha256=prior.cut_sha256,
                    last_two_turns=("host says stationary",))
    assert later.state_sha256 == state.state_sha256
    assert stationary_repeat(later, CLAIMS, prior)


def test_zero_defect_is_a_benign_control_not_an_obstructed_stationary_repeat():
    state = ledger(phi1=0)
    with pytest.raises(ValueError, match="NOT_STATIONARY"):
        stationary_cut_binding(state, CLAIMS, observed_phi1=0)


def test_ledger_reaches_real_pfp_prompt_without_hidden_targets_or_full_history():
    claims = dict(CLAIMS)
    history = ["older-turn-secret", "recent ASSERT", "recent stationary CUT"]
    state = ledger(claims=claims, last_two_turns=history)
    claims["b->d"] = 999
    history[-1] = "changed outside host"
    prepared = turn(state)
    context = prepared.task.case["context"]
    assert context["host_scratch"]["current_claims"] == CLAIMS
    assert context["host_scratch"]["last_two_turns"] == ["recent ASSERT", "recent stationary CUT"]
    assert context["protocol_sha256"] == sha256(PROTOCOL.read_bytes()).hexdigest()
    assert context["host_state_sha256"] == state.state_sha256
    assert "recent stationary CUT" in prepared.prompt.user
    assert "older-turn-secret" not in prepared.prompt.user
    for forbidden in ("recommended_cut", "target_chord", "repaired_cochain", "oracle_answer"):
        assert forbidden not in prepared.prompt.user
    assert '"b->d": -3' not in prepared.prompt.user
    assert '"c->d": -5' not in prepared.prompt.user


def test_checked_raw_cut_is_bound_but_not_mistaken_for_a_mathematical_success():
    prepared = turn(ledger())
    raw = raw_reply(prepared)
    checked = prepared.check(raw)
    assert checked["schema_valid"]
    assert checked["status"] == "PROVIDER_COMPLETED"
    assert checked["evidence_grade"] == "UNVERIFIED"
    assert base64.b64decode(checked["raw_reply_base64"]) == raw
    assert prepared.replay(checked) == checked  # no gateway or provider exists in this adapter
    assert not turn(ledger(), attempt_id="turn-3").check(raw)["schema_valid"]
    with pytest.raises(ValueError, match="REPLAY_BINDING_MISMATCH"):
        turn(ledger(claims={**CLAIMS, "b->d": 0})).replay(checked)


@pytest.mark.parametrize("replacement", [True, 1.5, "1"])
def test_full_cut_refuses_coercion_in_host_binding_and_actual_reply(replacement):
    state = ledger()
    cut = {**CLAIMS, "a->b": replacement}
    with pytest.raises(ValueError, match="EXACT_INTEGER"):
        stationary_cut_binding(state, cut, observed_phi1=8)
    assert not turn(state).check(raw_reply(turn(state), cut))["schema_valid"]


def test_cut_must_cover_exact_board_edges():
    state = ledger()
    for bad_cut in ({"a->b": 1}, {**CLAIMS, "x->y": 0}):
        with pytest.raises(ValueError, match="FULL_CUT"):
            stationary_cut_binding(state, bad_cut, observed_phi1=8)
        assert not turn(state).check(raw_reply(turn(state), bad_cut))["schema_valid"]


def test_protocol_pin_mismatch_refuses_before_prompt_preparation():
    with pytest.raises(ValueError, match="C006_PROTOCOL_SOURCE_MISMATCH"):
        turn(ledger(), protocol_sha256="0" * 64)


def test_malformed_raw_bytes_and_undeclared_cut_fields_are_not_coerced():
    prepared = turn(ledger())
    assert not prepared.check(b"not json")["schema_valid"]
    payload = json.loads(raw_reply(prepared))
    payload["answer"]["claimed_phi1"] = 0
    assert not prepared.check(json.dumps(payload).encode())["schema_valid"]


def test_consumed_raw_cut_emits_am4_observation_without_faking_host_acceptance():
    from omega_engine_pfp.infrastructure.mechanism_scratch_space import check_scratch_cut_turn

    state = ledger()
    prepared = turn(state)
    prior = stationary_cut_binding(state, CLAIMS, observed_phi1=8)
    checked = check_scratch_cut_turn(prepared, state, raw_reply(prepared), previous=prior)
    assert checked["scratch_observation"]["code"] == "AM-4-STATIONARY-REPEAT"
    assert checked["scratch_observation"]["suggested_action"] == "REQUEST_DIFFERENT_CANDIDATE_OR_LIFT"
    assert checked["status"] == "PROVIDER_COMPLETED"
    assert checked["evidence_grade"] == "UNVERIFIED"
    changed = ledger(claims={**CLAIMS, "b->d": 0})
    fresh = turn(changed)
    assert check_scratch_cut_turn(fresh, changed, raw_reply(fresh), previous=prior)["scratch_observation"] is None
    with pytest.raises(ValueError, match="SCRATCH_TURN_STATE_MISMATCH"):
        check_scratch_cut_turn(prepared, changed, raw_reply(prepared), previous=prior)


def test_real_existing_finite_cochain_checker_rejects_bad_cut_and_checks_zero_control():
    from fractions import Fraction

    from omega_engine_pfp.domain.solvers.simplicial_cochain import CochainCarrier, Simplicial1Cochain
    from omega_engine_pfp.infrastructure.mechanism_scratch_space import check_scratch_cut_turn

    state = ledger()
    prepared = turn(state)
    carrier = CochainCarrier("C006-K4", ("a", "b", "c", "d"),
                             tuple(tuple(edge.split("->")) for edge in CLAIMS), ())
    tree, chords = carrier.find_spanning_tree()
    cycles = carrier.find_fundamental_cycles(tree, chords)

    def zero_check(_case, answer):
        cochain = Simplicial1Cochain({tuple(edge.split("->")): Fraction(value)
                                    for edge, value in answer["claims"].items()})
        return all(cochain.evaluate_cycle_holonomy(cycle) == 0 for cycle in cycles)

    bad = check_scratch_cut_turn(prepared, state, raw_reply(prepared), judges=(("cycle-zero", zero_check),))
    assert bad["status"] == "PROVIDER_COMPLETED"
    assert bad["failure_class"] == "CERTIFICATE"
    # Explicit host test control only; these target values never enter the brief.
    potentials = {"a": 0, "b": 1, "c": 3, "d": -2}
    zero = {edge: potentials[v] - potentials[u] for edge in CLAIMS for u, v in [edge.split("->")]}
    good = check_scratch_cut_turn(prepared, state, raw_reply(prepared, zero), judges=(("cycle-zero", zero_check),))
    assert good["status"] == "HOST_ACCEPTED"
    assert good["evidence_grade"] == "TASK_CHECKED"
    assert "ACCEPTED_ZERO_DEFECT" not in good  # not the original full-session VERIFY terminal
