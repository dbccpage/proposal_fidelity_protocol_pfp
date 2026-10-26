"""C007 host contracts with declared scripted replies, never model trials."""

import base64
import copy
import json

import pytest

from omega_engine_pfp.infrastructure.context_compaction_sessions import (
    constraint_retention,
    prepare_compaction_turn,
    replay_compaction_session,
    start_compaction_session,
    submit_compaction_turn,
)

PROTOCOL = "a" * 64


def schedule(turns=30):
    events = [{"kind": "continue"} for _ in range(turns)]
    potential = {"a": 0, "b": 4, "c": -3}
    constraints = [
        dict(id="s1:ab", u="a", v="b", claim=4, repairable=False),
        dict(id="s1:bc", u="b", v="c", claim=-7, repairable=False),
        dict(id="s1:ca", u="c", v="a", claim=2, repairable=True),
    ]
    events[0] = dict(kind="release", stage=1, constraints=constraints)
    for stage in range(2, 7):
        node = "n" + str(stage)
        potential[node] = stage * (-1 if stage % 2 else 1)
        records = [
            dict(id=f"s{stage}:tree", u="c", v=node, claim=potential[node] + 3, repairable=False),
            dict(id=f"s{stage}:chord", u="a", v=node, claim=potential[node] + 2, repairable=True),
        ]
        events[(stage - 1) * (turns // 6)] = dict(kind="release", stage=stage, constraints=records)
    status = [i for i in range(1, turns - 1) if events[i]["kind"] == "continue"][:8]
    for index in status:
        events[index] = dict(kind="status", restatements=[copy.deepcopy(constraints[0])])
    # A schema-valid typo must never replace the immutable declaration.
    events[status[3]]["restatements"][0]["claim"] = 5
    return events, potential


def test_incomplete_stage_schedule_refuses_before_native():
    events, _ = schedule()
    events[25] = dict(kind="continue")
    with pytest.raises(ValueError, match="REQUIRES_SIX_STAGES"):
        start_compaction_session(events, run_id="missing-stage", protocol_sha256=PROTOCOL)


def raw(state, answer):
    turn = prepare_compaction_turn(state)
    return json.dumps({**{k: turn.binding[k] for k in ("task_id", "attempt_id", "input_sha256")},
                       "answer": answer}).encode()


def exact_cut(state, potential):
    return dict(move="CUT", claims={key: str(potential[row["v"]] - potential[row["u"]])
                                    for key, row in state["constraints"].items()})


@pytest.mark.parametrize("arm", ["ledger", "history", "prose"])
def test_real_thirty_turn_union_protects_early_constraints_and_replays(arm):
    events, potential = schedule()
    state = start_compaction_session(events, run_id="long-control", protocol_sha256=PROTOCOL, arm=arm)
    first = prepare_compaction_turn(state).prompt.user
    assert "s1:ab" in first and "s6:tree" not in first
    for index in range(30):
        assert constraint_retention(state) == 1
        answer = (dict(move="VERIFY", potential={n: str(potential[n]) for n in potential})
                  if index == 29 else exact_cut(state, potential))
        state = submit_compaction_turn(state, raw(state, answer))
    assert state["terminal"] == "ACCEPTED_ZERO_DEFECT"
    assert state["violations"] == 0 and len(state["transcript"]) == 30
    assert any(row["host_event"]["refusal"] == "FALSE_RESTATEMENT_REFUSED" for row in state["transcript"])
    assert state["constraints"]["s1:ab"]["claim"] == 4
    assert replay_compaction_session(json.loads(json.dumps(state))) == dict(
        terminal="ACCEPTED_ZERO_DEFECT", turns=30, violations=0, provider_calls=0)


def test_exact_union_cannot_erase_a_protected_edit_or_complete_before_final_stage():
    events, potential = schedule()
    state = start_compaction_session(events, run_id="protected", protocol_sha256=PROTOCOL)
    proposed = exact_cut(state, potential)
    proposed["claims"]["s1:ab"] = "5"
    changed = submit_compaction_turn(state, raw(state, proposed))
    assert changed["violations"] == 1
    assert changed["claims"]["s1:ab"] == 4
    assert changed["transcript"][-1]["outcome"]["reason"] == "CONSTRAINT_EDIT"
    state = submit_compaction_turn(state, raw(state, exact_cut(state, potential)))
    verify = dict(move="VERIFY", potential={n: str(potential[n]) for n in ("a", "b", "c")})
    state = submit_compaction_turn(state, raw(state, verify))
    assert state["terminal"] is None
    assert state["transcript"][-1]["outcome"]["reason"] == "FUTURE_CONSTRAINTS_PENDING"


def test_48_turn_fuel_keeps_malformed_raw_replies_and_never_claims_acceptance():
    events, _ = schedule(48)
    state = start_compaction_session(events, run_id="malformed", protocol_sha256=PROTOCOL)
    for _ in range(48):
        state = submit_compaction_turn(state, b"not an envelope")
    assert state["terminal"] == "FUEL_EXHAUSTED"
    assert all(base64.b64decode(row["pfp"]["raw_reply_base64"]) == b"not an envelope" for row in state["transcript"])
    assert replay_compaction_session(state)["turns"] == 48


@pytest.mark.parametrize("fault", ["short", "identity", "bool_claim", "disjoint", "restatement", "kv"])
def test_invalid_host_contract_refuses_before_native_execution(fault):
    events, _ = schedule()
    options = {}
    if fault == "short":
        events.pop()
    elif fault == "identity":
        events[5]["constraints"][0]["id"] = "s1:ab"
    elif fault == "bool_claim":
        events[0]["constraints"][0]["claim"] = True
    elif fault == "disjoint":
        for row in events[5]["constraints"]:
            row["u"] = "outside"
    elif fault == "restatement":
        events[1]["restatements"][0]["id"] = "unknown"
    else:
        options["arm"] = "kv-reuse"

    class NeverNative:
        def solve(self, case):
            pytest.fail("Invalid schedule reached native execution")

    with pytest.raises(ValueError):
        start_compaction_session(events, run_id="invalid", protocol_sha256=PROTOCOL, native=NeverNative(), **options)


def test_state_or_declared_constraint_mutation_cannot_replay_as_original():
    events, potential = schedule()
    state = start_compaction_session(events, run_id="custody", protocol_sha256=PROTOCOL)
    state = submit_compaction_turn(state, raw(state, exact_cut(state, potential)))
    changed = copy.deepcopy(state)
    changed["constraints"]["s1:ab"]["claim"] = 5
    with pytest.raises(ValueError, match="COMPACTION_STATE_MISMATCH"):
        replay_compaction_session(changed)
