"""Twenty-five distinct finite cochain controls; all are offline host fixtures."""

import json
from dataclasses import replace
from fractions import Fraction

import pytest

from omega_engine_pfp.domain.rewriting.finite_dpo import (
    FiniteACSet,
    Link,
    RewriteRefusal,
    apply_registered_rule,
    graph_digest,
)
from omega_engine_adversary.tests.pilots.acset_cochain_rewriting.checker import check_gradient
from omega_engine_adversary.tests.pilots.acset_cochain_rewriting.pilot import (
    check_reply,
    execute_proposal,
    fixture_case,
    fixture_proposal,
    graph,
    prepare,
    replace_edge_rule,
    replay_reply,
)


def single(weight: str = "2/1") -> FiniteACSet:
    return graph({"a": "0/1", "b": "2/1"}, (("e", "a", "b", weight),))


def assert_refusal(code: str, function, *args, **kwargs) -> None:
    with pytest.raises(RewriteRefusal) as caught:
        function(*args, **kwargs)
    assert caught.value.code == code


def test_single_oriented_edge_has_exact_gradient() -> None:
    state = single()
    checked = check_gradient(state, state)
    assert checked.accepted and checked.residuals == (("e", Fraction(0)),)


def test_reverse_orientation_requires_negative_weight() -> None:
    state = graph({"a": "0/1", "b": "2/1"}, (("e", "b", "a", "-2/1"),))
    assert check_gradient(state, state).accepted


def test_disconnected_components_and_isolated_vertex_are_preserved() -> None:
    state = graph({"a": "0/1", "b": "2/1", "c": "7/1", "d": "4/1", "isolated": "9/1"},
        (("ab", "a", "b", "2/1"), ("cd", "c", "d", "-3/1")))
    assert check_gradient(state, state).accepted


def test_rational_difference_is_exact() -> None:
    state = graph({"a": "1/2", "b": "4/3"}, (("e", "a", "b", "5/6"),))
    assert check_gradient(state, state).accepted


def test_self_loop_requires_zero_weight() -> None:
    state = graph({"a": "5/3"}, (("loop", "a", "a", "0/1"),))
    assert check_gradient(state, state).accepted
    bad = graph({"a": "5/3"}, (("loop", "a", "a", "1/1"),))
    assert not check_gradient(state, bad).accepted


def test_parallel_edges_may_share_one_gradient() -> None:
    state = graph({"a": "0/1", "b": "2/1"},
        (("e1", "a", "b", "2/1"), ("e2", "a", "b", "2/1")))
    assert check_gradient(state, state).accepted


def test_parallel_cancellation_does_not_establish_exactness() -> None:
    state = graph({"a": "0/1", "b": "0/1"},
        (("e1", "a", "b", "1/1"), ("e2", "a", "b", "-1/1")))
    checked = check_gradient(state, state)
    assert sum(value for _, value in checked.residuals) == 0
    assert not checked.accepted and checked.reason == "NONZERO_EDGE_RESIDUAL"


def test_oriented_cycle_checks_every_edge() -> None:
    state = graph({"a": "0/1", "b": "1/1", "c": "2/1"},
        (("ab", "a", "b", "1/1"), ("bc", "b", "c", "1/1"), ("ca", "c", "a", "1/1")))
    assert check_gradient(state, state).residuals[-1] == ("ca", Fraction(3))
    assert not check_gradient(state, state).accepted


def test_changed_potential_is_refused_even_when_new_gradient_is_exact() -> None:
    source = single()
    candidate = graph({"a": "0/1", "b": "3/1"}, (("e", "a", "b", "3/1"),))
    assert check_gradient(source, candidate).reason == "PROTECTED_POTENTIAL_CHANGED"


def test_orientation_change_is_refused_even_with_correct_sign() -> None:
    candidate = graph({"a": "0/1", "b": "2/1"}, (("e", "b", "a", "-2/1"),))
    assert check_gradient(single(), candidate).reason == "ORIENTED_TOPOLOGY_CHANGED"


def test_missing_parallel_edge_is_refused() -> None:
    source = graph({"a": "0/1", "b": "2/1"},
        (("e1", "a", "b", "2/1"), ("e2", "a", "b", "2/1")))
    assert check_gradient(source, single()).reason == "ORIENTED_TOPOLOGY_CHANGED"


def test_added_exact_edge_is_refused() -> None:
    candidate = graph({"a": "0/1", "b": "2/1"},
        (("e", "a", "b", "2/1"), ("reverse", "b", "a", "-2/1")))
    assert check_gradient(single(), candidate).reason == "ORIENTED_TOPOLOGY_CHANGED"


def test_vertex_kind_cannot_change() -> None:
    source = single()
    candidate = FiniteACSet((replace(source.parts[0], kind="constraint"), source.parts[1]), source.links)
    assert check_gradient(source, candidate).reason == "COCHAIN_SCHEMA"


def test_zero_denominator_is_refused() -> None:
    state = single("1/0")
    assert check_gradient(state, state).reason == "NONCANONICAL_RATIONAL"


def test_decimal_string_is_not_an_exact_rational_certificate() -> None:
    state = single("2.0")
    assert check_gradient(state, state).reason == "NONCANONICAL_RATIONAL"


def test_float_attribute_is_refused_before_execution() -> None:
    assert_refusal("ATTRIBUTE_TYPE_OR_DUPLICATE", Link,
        "e", "edge", "a", "b", (("cochain", 2.0),))


def test_tiny_nonzero_rational_residual_is_not_rounded_away() -> None:
    state = single("2000000000000000001/1000000000000000000")
    checked = check_gradient(state, state)
    assert not checked.accepted and checked.residuals[0][1] == Fraction(1, 10**18)


def test_registered_dpo_repair_preserves_source_and_restores_gradient() -> None:
    source, registry = fixture_case()
    before = graph_digest(source)
    result = execute_proposal(source, registry, fixture_proposal(source, registry[0]))
    assert result.fuel_remaining == 0 and check_gradient(source, result.state).accepted
    assert graph_digest(source) == before and result.before_digest == before
    assert all(part in result.state.parts for part in source.parts)


def test_structurally_valid_wrong_weight_still_fails_independent_judge() -> None:
    source, registry = fixture_case()
    proposal = fixture_proposal(source, registry[1])
    assert_refusal("NONZERO_EDGE_RESIDUAL", execute_proposal, source, registry, proposal)


def test_unregistered_rule_is_refused() -> None:
    source, registry = fixture_case()
    proposal = {**fixture_proposal(source, registry[0]), "rule_id": "invented"}
    assert_refusal("UNREGISTERED_OR_DUPLICATE_RULE", execute_proposal, source, registry, proposal)


def test_source_and_full_rule_digest_tampering_are_refused() -> None:
    source, registry = fixture_case()
    proposal = fixture_proposal(source, registry[0])
    assert_refusal("SOURCE_DIGEST_MISMATCH", execute_proposal, source, registry,
        {**proposal, "source_digest": "0" * 64})
    altered = replace_edge_rule(source, "bc", "1/1", registry[0].rule_id)
    assert_refusal("RULE_DIGEST_MISMATCH", execute_proposal, source, (altered, registry[1]), proposal)


def test_part_match_tampering_is_refused() -> None:
    source, registry = fixture_case()
    proposal = fixture_proposal(source, registry[0])
    assert_refusal("PART_MATCH_MISMATCH", execute_proposal, source, registry,
        {**proposal, "part_match": {"b": "a", "c": "c"}})


def test_link_match_tampering_is_refused() -> None:
    source, registry = fixture_case()
    proposal = fixture_proposal(source, registry[0])
    assert_refusal("LINK_MATCH_MISMATCH", execute_proposal, source, registry,
        {**proposal, "link_match": {"bc": "ab"}})


def test_fuel_and_result_digest_tampering_are_refused() -> None:
    source, registry = fixture_case()
    proposal = fixture_proposal(source, registry[0])
    for value in (0, 2, True):
        assert_refusal("FUEL_BINDING_MISMATCH", execute_proposal, source, registry, {**proposal, "fuel": value})
    turn = prepare(source, registry)
    raw = json.dumps({**{key: value for key, value in turn.binding.items() if key != "checker_id"},
        "answer": proposal}).encode("utf-8")
    checked = check_reply(turn, raw, source, registry)
    tampered = {**checked, "operation_receipt": {**checked["operation_receipt"], "result_digest": "0" * 64}}
    assert_refusal("OPERATION_RECEIPT_MISMATCH", replay_reply, turn, tampered, source, registry)
    assert_refusal("FUEL_BOUND", apply_registered_rule, source, registry, registry[0].rule_id,
        proposal["part_match"], proposal["link_match"], fuel=0)


def test_pfp_fixture_and_zero_send_replay_bind_actual_bytes_and_judge() -> None:
    source, registry = fixture_case()
    turn = prepare(source, registry)
    proposal = fixture_proposal(source, registry[0])
    raw = json.dumps({**{key: value for key, value in turn.binding.items() if key != "checker_id"},
        "answer": proposal}, sort_keys=True).encode("utf-8")
    checked = check_reply(turn, raw, source, registry)
    assert checked["schema_valid"] and checked["status"] == "HOST_ACCEPTED"
    replayed = replay_reply(turn, checked, source, registry)
    assert replayed["status"] == "HOST_ACCEPTED"
    with pytest.raises(ValueError, match="REPLAY_RAW_MISMATCH"):
        turn.replay({**checked, "raw_reply_sha256": "0" * 64})
    wrong_raw = json.dumps({**{key: value for key, value in turn.binding.items() if key != "checker_id"},
        "answer": fixture_proposal(source, registry[1])}).encode("utf-8")
    wrong = check_reply(turn, wrong_raw, source, registry)
    assert wrong["schema_valid"] and wrong["failure_class"] == "CERTIFICATE"
    assert not wrong["judges"][0]["accepted"]
    foreign_source = single("1/1")
    foreign_registry = (replace_edge_rule(foreign_source, "e", "2/1"),)
    foreign_proposal = fixture_proposal(foreign_source, foreign_registry[0])
    misleading_raw = json.dumps({**{key: value for key, value in turn.binding.items() if key != "checker_id"},
        "answer": foreign_proposal}).encode("utf-8")
    assert_refusal("PREPARED_SOURCE_RULE_MISMATCH", check_reply, turn, misleading_raw,
        foreign_source, foreign_registry)
    foreign_turn = prepare(foreign_source, foreign_registry)
    foreign_raw = json.dumps({**{key: value for key, value in foreign_turn.binding.items() if key != "checker_id"},
        "answer": foreign_proposal}).encode("utf-8")
    foreign_record = check_reply(foreign_turn, foreign_raw, foreign_source, foreign_registry)
    assert_refusal("PREPARED_SOURCE_RULE_MISMATCH", replay_reply, turn, foreign_record,
        foreign_source, foreign_registry)
