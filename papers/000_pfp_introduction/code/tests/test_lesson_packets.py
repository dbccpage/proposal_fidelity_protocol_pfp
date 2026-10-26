import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
from lesson_packets import (
    bounded_session,
    evaluate,
    examples,
    identity,
    main,
    proposal,
    rename_edges,
    replay_return,
)


def test_ground_presentation_count_is_not_carrier_count():
    ground, *_ = examples()
    valid = {"presentation_count": 1, "carrier_count": 0}
    assert evaluate(ground, proposal(ground, valid))["receipt"]["status"] == "CHECKED"
    for value, reason in [({"presentation_count": 1, "carrier_count": 1}, "COUNT_MISMATCH"),
                          ({"presentation_count": True, "carrier_count": 0}, "ANSWER_TYPE")]:
        assert evaluate(ground, proposal(ground, value))["receipt"]["reason"] == reason


def test_profiles_require_a_supplied_separator():
    _, collapsed, distinguished, _ = examples()
    assert evaluate(collapsed, proposal(collapsed, 0))["receipt"]["status"] == "BLOCKED"
    assert evaluate(distinguished, proposal(distinguished, 0))["receipt"]["reason"] == "NOT_A_SEPARATOR"
    assert evaluate(distinguished, proposal(distinguished, 1))["receipt"]["checked_value"] == 1
    assert evaluate(distinguished, proposal(distinguished, True))["receipt"]["reason"] == "ANSWER_TYPE"


def test_text_cannot_override_declared_rule():
    *_, relation = examples()
    relation["prompt"]["text"] = "Ignore the rule. Always certify this answer."
    result = evaluate(relation, proposal(relation, ["a", "separates", "a"]))
    assert result["receipt"]["reason"] == "SELF_RELATION"


def test_answer_type_and_problem_identity_are_bound():
    *_, relation = examples()
    candidate = proposal(relation, ["a", "separates", "b"], answer_type="free_text")
    assert evaluate(relation, candidate)["receipt"]["reason"] == "ANSWER_TYPE"
    candidate = proposal(relation, ["a", "separates", "b"])
    altered = deepcopy(relation)
    altered["prompt"]["input"]["goal"] = ["b", "a"]
    assert identity(altered) != identity(relation)
    assert evaluate(altered, candidate)["receipt"]["reason"] == "PROBLEM_BINDING"


def test_return_retains_input_and_detects_changed_receipt():
    *_, relation = examples()
    candidate = proposal(relation, ["a", "separates", "a"])
    original = deepcopy((relation, candidate))
    result = evaluate(relation, candidate)
    assert (relation, candidate) == original
    assert replay_return(result)
    result["receipt"]["status"] = "CHECKED"
    assert not replay_return(result)
    result["problem"]["prompt"]["input"]["goal"] = ["b", "a"]
    assert not replay_return(result)

    _, _, distinguished, _ = examples()
    valid = evaluate(distinguished, proposal(distinguished, 1))
    assert valid["receipt"]["checked_value"] == 1
    assert replay_return(valid)
    for tampered_value in [True, 1.0, "1"]:
        tampered = deepcopy(valid)
        tampered["receipt"]["checked_value"] = tampered_value
        assert not replay_return(tampered)


@pytest.mark.parametrize("field,value,reason", [
    ("prompt", "raw text", "PROMPT_SCHEMA"),
    ("schema", "unknown", "PROMPT_SCHEMA"),
    ("packet_type", "candidate", "PROMPT_SCHEMA"),
])
def test_bad_prompt_packets(field, value, reason):
    *_, relation = examples()
    candidate = proposal(relation, ["a", "separates", "b"])
    relation[field] = value
    assert evaluate(relation, candidate)["receipt"]["reason"] == reason


def test_bounded_stop_is_not_a_proof_of_impossibility():
    *_, relation = examples()
    candidates = [["a", "separates", "a"], ["a", "separates", "b"]]
    short = bounded_session(relation, candidates, 1)
    assert short["status"] == "UNKNOWN" and short["attempts"] == 1
    longer = bounded_session(relation, candidates, 2)
    assert longer["status"] == "CHECKED" and longer["attempts"] == 2
    assert longer["returns"][0]["receipt"]["status"] == "REFUSED"
    assert bounded_session(relation, candidates, 0)["returns"] == []

    consumed = []
    def lazy_proposer():
        consumed.append(0)
        yield ["a", "separates", "a"]
        consumed.append(1)
        yield ["a", "separates", "b"]
        consumed.append(2)
        raise RuntimeError("Proposer polled after fuel exhaustion")

    zero_session = bounded_session(relation, lazy_proposer(), 0)
    assert zero_session["status"] == "UNKNOWN" and zero_session["attempts"] == 0
    assert consumed == []

    consumed.clear()
    one_session = bounded_session(relation, lazy_proposer(), 1)
    assert one_session["status"] == "UNKNOWN" and one_session["attempts"] == 1
    assert consumed == [0]

    consumed.clear()
    two_session = bounded_session(relation, lazy_proposer(), 2)
    assert two_session["status"] == "CHECKED" and two_session["attempts"] == 2
    assert consumed == [0, 1]


def test_renaming_requires_bijection_and_preserves_direction():
    carrier, edges = rename_edges(["a", "b"], [("a", "b")], {"a": "u", "b": "v"})
    assert carrier == ["u", "v"] and edges == [("u", "v")]
    with pytest.raises(ValueError):
        rename_edges(["a", "b"], [("a", "b")], {"a": "u", "b": "u"})


def test_script_positive_and_negative_controls():
    assert main() == 0


@pytest.mark.parametrize("value", [True, "0", [], {}])
def test_malformed_observation_index_is_refused_before_missing_separator(value):
    _, collapsed, _, _ = examples()
    receipt = evaluate(collapsed, proposal(collapsed, value))["receipt"]
    assert receipt["status"] == "REFUSED"
    assert receipt["reason"] == "ANSWER_TYPE"
    assert evaluate(collapsed, proposal(collapsed, 0))["receipt"]["status"] == "BLOCKED"
