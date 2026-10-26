"""Original C006 session rules against the real native weighted L1 boundary.

Replies here are declared deterministic test fixtures, never model trials.
"""
import base64
import copy
import json

import pytest

from omega_engine_pfp.infrastructure.mechanism_sessions import (
    exact_baseline, prepare_session_turn, replay_session, session_result, start_session, submit_session_turn,
)


BOARD = dict(case_id="round5-K4-diagnostic", nodes=["a", "b", "c", "d"],
    edges=[["a", "b"], ["b", "c"], ["c", "a"], ["b", "d"], ["d", "a"], ["c", "d"]],
    claims={"a->b": 1, "b->c": 2, "c->a": 3, "b->d": 1, "d->a": 2, "c->d": 1},
    weights={edge: 1 for edge in ("a->b", "b->c", "c->a", "b->d", "d->a", "c->d")})
PROTOCOL_SHA = "e1cf2e0fd816ad060c534f3aad8facc16e7c6d5d8cf5c7bd9bffa2ffd33635fb"


def start(**options):
    return start_session(copy.deepcopy(BOARD), run_id="C006-test", protocol_sha256=PROTOCOL_SHA,
        detector_firing_share="1", **options)


def raw(state, answer):
    turn = prepare_session_turn(state)
    return json.dumps({key: turn.binding[key] for key in
        ("task_id", "attempt_id", "input_sha256")} | {"answer": answer}).encode()


def move(state, answer):
    return submit_session_turn(state, raw(state, answer))


def test_real_native_phi1_and_fuel_are_not_the_historical_cycle_sum():
    state = start()
    assert state["measurement"]["phi1"] == "6"
    assert state["cycle_rank"] == 3 and state["fuel"] == 15
    assert state["measurement"]["native_outcome"]["result"]["certificate_verified"] is True
    doubled = copy.deepcopy(BOARD)
    doubled["weights"] = {key: 2 for key in doubled["weights"]}
    assert start_session(doubled, run_id="weighted", protocol_sha256=PROTOCOL_SHA)["measurement"]["phi1"] == "12"


def test_stationary_partial_chord_closure_is_rejected_then_observed_not_admitted():
    state = start()
    candidate = {key: str(value) for key, value in state["claims"].items()}
    candidate["c->a"] = "-3"
    first = move(state, dict(move="CUT", claims=candidate))
    assert first["claims"] == state["claims"]
    assert first["transcript"][-1]["outcome"]["reason"] == "NO_STRICT_DESCENT"
    assert first["measurement"]["phi1"] == "6"
    assert first["transcript"][-1]["outcome"]["am4"] is None
    second = move(first, dict(move="CUT", claims=candidate))
    assert second["transcript"][-1]["outcome"]["am4"] == "AM-4-STATIONARY-REPEAT"
    assert second["terminal"] is None and len(second["transcript"]) == 2


def test_zero_cut_needs_a_separate_valid_submitted_verify_potential():
    state = start()
    zero = {key: "0" for key in BOARD["claims"]}
    cut = move(state, dict(move="CUT", claims=zero))
    assert cut["measurement"]["phi1"] == "0" and cut["terminal"] is None
    wrong = move(cut, dict(move="VERIFY", potential={"a": "1", "b": "0", "c": "0", "d": "0"}))
    assert wrong["terminal"] is None
    assert wrong["transcript"][-1]["outcome"]["reason"] == "INVALID_POTENTIAL"
    done = move(wrong, dict(move="VERIFY", potential={node: "0" for node in BOARD["nodes"]}))
    assert done["terminal"] == "ACCEPTED_ZERO_DEFECT"
    assert session_result(done)["status"] == "SOLVED"
    assert session_result(cut)["status"] == "UNKNOWN"
    assert len(done["transcript"]) == 3
    assert replay_session(done)["terminal"] == "ACCEPTED_ZERO_DEFECT"
    assert replay_session(done)["provider_calls"] == 0
    assert replay_session(json.loads(json.dumps(done)))["terminal"] == "ACCEPTED_ZERO_DEFECT"
    with pytest.raises(ValueError, match="SESSION_TERMINAL"):
        prepare_session_turn(done)


def test_positive_defect_cannot_verify_even_with_a_native_solver_potential():
    state = start()
    attempted = move(state, dict(move="VERIFY", potential={node: "0" for node in BOARD["nodes"]}))
    assert attempted["terminal"] is None
    assert attempted["transcript"][-1]["outcome"]["reason"] == "NONZERO_DEFECT"


def test_assert_cannot_change_claims_and_lift_contains_structure_not_repairs():
    state = start()
    bad = move(state, dict(move="ASSERT", edge="a->b", value="2"))
    assert bad["asserted_edges"] == [] and bad["claims"] == state["claims"]
    good = move(bad, dict(move="ASSERT", edge="a->b", value="1"))
    assert good["asserted_edges"] == ["a->b"]
    lifted = move(good, dict(move="LIFT_REQUEST"))
    outcome = lifted["transcript"][-1]["outcome"]
    assert len(outcome["cycles"]) == 3
    assert lifted["claims"] == state["claims"]
    prompt = prepare_session_turn(lifted).prompt.user
    for field in ("native_outcome", "dual", "repair", "optimal_potential", "recommended_cut"):
        assert '"'+field+'"' not in prompt


def test_reassertion_is_bookkeeping_not_progress_or_a_new_protocol_rejection():
    first = move(start(), dict(move="ASSERT", edge="b->c", value="2"))
    again = move(first, dict(move="ASSERT", edge="b->c", value="2"))
    assert again["claims"] == first["claims"] and again["asserted_edges"] == first["asserted_edges"]
    assert again["transcript"][-1]["outcome"]["reason"] == "ASSERT_ALREADY_RECORDED"
    assert again["transcript"][-1]["pfp"]["status"] == "HOST_ACCEPTED"
    assert len(again["transcript"]) == 2
    assert "already asserted" in prepare_session_turn(again).prompt.user


@pytest.mark.parametrize("bad", [True, 0.5, "1/1"])
def test_malformed_cut_counts_a_turn_but_never_coerces_or_mutates(bad):
    state = start()
    candidate = {key: "0" for key in BOARD["claims"]} | {"a->b": bad}
    original = raw(state, dict(move="CUT", claims=candidate))
    checked = submit_session_turn(state, original)
    assert checked["claims"] == state["claims"]
    assert checked["transcript"][-1]["outcome"]["reason"] == "TASK_ENVELOPE"
    assert base64.b64decode(checked["transcript"][-1]["pfp"]["raw_reply_base64"]) == original


def test_unparseable_calls_spend_fuel_until_original_survivor_terminal():
    state = start()
    for _ in range(state["fuel"]):
        state = submit_session_turn(state, b"not a JSON response")
    assert state["terminal"] == "SURVIVOR_OBSTRUCTION"
    assert len(state["transcript"]) == 15
    assert replay_session(state)["terminal"] == "SURVIVOR_OBSTRUCTION"


def test_matched_ledger_history_and_prose_arms_expose_same_current_host_facts():
    states = [start(arm=arm) for arm in ("ledger", "history", "prose")]
    facts = [prepare_session_turn(state).task.case["context"]["host_facts"] for state in states]
    assert facts[0] == facts[1] == facts[2]
    for state in states:
        assert "recommended_cut" not in prepare_session_turn(state).prompt.user


def test_changed_raw_candidate_or_claimed_measurement_breaks_replay():
    state = move(start(), dict(move="LIFT_REQUEST"))
    changed = copy.deepcopy(state)
    changed["measurement"]["phi1"] = "0"
    with pytest.raises(ValueError, match="SESSION_STATE_MISMATCH"):
        replay_session(changed)
    changed = copy.deepcopy(state)
    changed["transcript"][0]["pfp"]["raw_reply_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="REPLAY_RAW_MISMATCH"):
        replay_session(changed)


def test_board_unknown_coordinates_nonintegers_and_disconnection_refuse():
    for field, bad in (("claims", {"a->b": True}), ("weights", {"a->b": 0})):
        board = copy.deepcopy(BOARD)
        board[field].update(bad)
        with pytest.raises(ValueError):
            start_session(board, run_id="bad", protocol_sha256=PROTOCOL_SHA)
    board = copy.deepcopy(BOARD)
    board["claims"]["a->x"] = 1
    with pytest.raises(ValueError):
        start_session(board, run_id="bad", protocol_sha256=PROTOCOL_SHA)


def test_changed_host_state_cannot_fire_stationary_repeat_and_treg_spends_no_extra_turn():
    state = start_session(copy.deepcopy(BOARD), run_id="suspension", protocol_sha256=PROTOCOL_SHA,
                          detector_firing_share="0")
    same = dict(move="CUT", claims={key: str(value) for key, value in BOARD["claims"].items()})
    first = move(state, same)
    asserted = move(first, dict(move="ASSERT", edge="a->b", value="1"))
    near_miss = move(asserted, same)
    assert near_miss["transcript"][-1]["outcome"]["am4"] is None
    fired = move(near_miss, same)
    assert fired["detector_suspended"] is True and fired["detector_firings"] == 1
    suspended = move(fired, same)
    assert suspended["transcript"][-1]["outcome"]["am4"] is None
    assert len(suspended["transcript"]) == 5
    assert replay_session(suspended)["turns"] == 5


def test_history_retains_prior_public_facts_and_all_arms_hide_solver_outputs():
    state = move(start(arm="history"), dict(move="LIFT_REQUEST"))
    context = prepare_session_turn(state).task.case["context"]
    assert context["history"][0]["host_facts"]["phi1"] == "6"
    assert "native_outcome" not in json.dumps(context)
    assert "potential" not in json.dumps(context)


def test_native_unverified_or_independently_invalid_measurements_are_not_admitted():
    class Refused:
        def solve(self, _case):
            return dict(status="UNKNOWN", refusal="NATIVE_CERTIFICATE_NOT_VERIFIED")

    with pytest.raises(ValueError, match="C006_NATIVE_UNAVAILABLE"):
        start_session(copy.deepcopy(BOARD), run_id="refused", protocol_sha256=PROTOCOL_SHA, native=Refused())

    state = start()

    class Invalid:
        def solve(self, _case):
            return dict(status="SOLVED", phi1="0", potential={node: "0" for node in BOARD["nodes"]},
                        repair={}, dual={})

    result = submit_session_turn(state, raw(state, dict(move="VERIFY", potential={node: "0" for node in BOARD["nodes"]})),
                                 native=Invalid())
    assert result["terminal"] == "EXECUTION_UNAVAILABLE"
    assert result["measurement"]["phi1"] == "6"
    assert result["transcript"][-1]["outcome"]["reason"] == "C006_INDEPENDENT_CERTIFICATE_REFUSED"


def test_exact_nearest_coboundary_baseline_is_a_separate_zero_model_control():
    result = exact_baseline(copy.deepcopy(BOARD), protocol_sha256=PROTOCOL_SHA)
    assert result["executor"] == "NO_LLM" and result["provider_calls"] == 0 and result["turns"] == "0"
    assert result["status"] == "SOLVED" and result["phi1_final"] == "0"
    assert sum(abs(int(result["final_cochain"][key]) - value) for key, value in BOARD["claims"].items()) == 6
