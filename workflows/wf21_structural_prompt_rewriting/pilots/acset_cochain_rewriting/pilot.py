"""Bounded cochain fixtures and source/rule-bound proposal execution."""

import json
from dataclasses import asdict

from omega_engine_pfp.domain.rewriting.finite_dpo import (
    DpoRule,
    FiniteACSet,
    Link,
    Part,
    RewriteRefusal,
    RewriteResult,
    apply_registered_rule,
    graph_digest,
    rule_digest,
)
from omega_engine_pfp.infrastructure.task_turn import PreparedTaskTurn, prepare_task_turn

from .checker import check_gradient

ANSWER_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "source_digest": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "rule_digest": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "rule_id": {"type": "string", "minLength": 1, "maxLength": 96},
        "part_match": {"type": "object", "maxProperties": 128,
            "additionalProperties": {"type": "string", "minLength": 1, "maxLength": 96}},
        "link_match": {"type": "object", "maxProperties": 256,
            "additionalProperties": {"type": "string", "minLength": 1, "maxLength": 96}},
        "fuel": {"type": "integer", "const": 1},
    },
    "required": ["source_digest", "rule_digest", "rule_id", "part_match", "link_match",
        "fuel"],
}


def graph(potentials: dict[str, str], edges: tuple[tuple[str, str, str, str], ...]) -> FiniteACSet:
    return FiniteACSet(tuple(Part(key, "vertex", (("potential", value),))
        for key, value in potentials.items()), tuple(Link(key, "edge", start, end,
        (("cochain", value),)) for key, start, end, value in edges))


def replace_edge_rule(state: FiniteACSet, edge_id: str, weight: str,
    rule_id: str = "repair_edge") -> DpoRule:
    edge = next(link for link in state.links if link.id == edge_id)
    endpoints = tuple(part for part in state.parts if part.id in (edge.source, edge.target))
    left = FiniteACSet(endpoints, (edge,))
    interface = FiniteACSet(endpoints, ())
    right = FiniteACSet(endpoints, (Link(edge.id, edge.kind, edge.source, edge.target,
        (("cochain", weight),)),))
    return DpoRule(rule_id, left, interface, right)


def execute_proposal(source: FiniteACSet, registry: tuple[DpoRule, ...], proposal: dict) -> RewriteResult:
    if type(proposal) is not dict or set(proposal) != set(ANSWER_SCHEMA["required"]):
        raise RewriteRefusal("PROPOSAL_SHAPE")
    if proposal["source_digest"] != graph_digest(source):
        raise RewriteRefusal("SOURCE_DIGEST_MISMATCH")
    matches = tuple(rule for rule in registry if rule.rule_id == proposal["rule_id"])
    if len(matches) != 1:
        raise RewriteRefusal("UNREGISTERED_OR_DUPLICATE_RULE")
    if proposal["rule_digest"] != rule_digest(matches[0]):
        raise RewriteRefusal("RULE_DIGEST_MISMATCH")
    if type(proposal["fuel"]) is not int or proposal["fuel"] != 1:
        raise RewriteRefusal("FUEL_BINDING_MISMATCH")
    result = apply_registered_rule(source, registry, proposal["rule_id"],
        proposal["part_match"], proposal["link_match"], fuel=proposal["fuel"],
        protected_parts=frozenset(part.id for part in source.parts))
    checked = check_gradient(source, result.state)
    if not checked.accepted:
        raise RewriteRefusal(checked.reason)
    return result


def fixture_case() -> tuple[FiniteACSet, tuple[DpoRule, ...]]:
    source = graph({"a": "0/1", "b": "1/2", "c": "4/3"}, (
        ("ab", "a", "b", "1/2"), ("bc", "b", "c", "7/6"), ("ac", "a", "c", "4/3")))
    return source, (replace_edge_rule(source, "bc", "5/6", "repair_bc"),
        replace_edge_rule(source, "bc", "7/6", "retain_bad_bc"))


def fixture_proposal(source: FiniteACSet, rule: DpoRule) -> dict:
    """Explicit host fixture, never a claimed actual model response."""
    parts = {part.id: part.id for part in rule.left.parts}
    links = {link.id: link.id for link in rule.left.links}
    return {"source_digest": graph_digest(source), "rule_digest": rule_digest(rule),
        "rule_id": rule.rule_id, "part_match": parts, "link_match": links, "fuel": 1}


def prepare(source: FiniteACSet, registry: tuple[DpoRule, ...]) -> PreparedTaskTurn:
    public = {"source": asdict(source), "source_digest": graph_digest(source),
        "rules": [{"body": asdict(rule), "digest": rule_digest(rule)} for rule in registry]}
    return prepare_task_turn(system="Propose one licensed cochain rewrite. Return a JSON instance.",
        user="Restore the exact edgewise gradient for the supplied fixed potentials. "
        "Keep every vertex, potential, oriented edge multiplicity and nonselected edge. "
        "Choose a registered rule and explicit injective matches; use fuel 1. "
        "Copy the selected source/rule digests from the inventory and return matches.\n"
        + json.dumps(public, sort_keys=True),
        task_id="acset-cochain-rewriting-v001", attempt_id="cochain-fixture:0",
        answer_schema=ANSWER_SCHEMA, checker_id="finite-edgewise-gradient-v001")


def _judge(source: FiniteACSet, registry: tuple[DpoRule, ...]):
    def judge(_case: dict, proposal: dict) -> tuple[bool, str]:
        try:
            execute_proposal(source, registry, proposal)
            return True, "Exact topology and edgewise Fraction residuals checked."
        except RewriteRefusal as exc:
            return False, exc.code
    return judge


def _with_receipt(checked: dict, source: FiniteACSet, registry: tuple[DpoRule, ...]) -> dict:
    if checked["status"] != "HOST_ACCEPTED":
        return checked
    result = execute_proposal(source, registry, checked["answer"])
    receipt = {"source_digest": result.before_digest, "result_digest": result.after_digest,
        "rule_id": result.rule_id, "rule_digest": checked["answer"]["rule_digest"],
        "part_match": dict(result.part_match), "link_match": dict(result.link_match),
        "fuel": 1, "fuel_remaining": result.fuel_remaining}
    return {**checked, "operation_receipt": receipt}


def _check_turn_binding(turn: PreparedTaskTurn, source: FiniteACSet,
    registry: tuple[DpoRule, ...]) -> None:
    if type(turn) is not PreparedTaskTurn or turn != prepare(source, registry):
        raise RewriteRefusal("PREPARED_SOURCE_RULE_MISMATCH")


def check_reply(turn: PreparedTaskTurn, raw: bytes, source: FiniteACSet,
    registry: tuple[DpoRule, ...]) -> dict:
    _check_turn_binding(turn, source, registry)
    checked = turn.check(raw, judges=(("finite-edgewise-gradient-v001", _judge(source, registry)),),
        require_checker=True)
    return _with_receipt(checked, source, registry)


def replay_reply(turn: PreparedTaskTurn, record: dict, source: FiniteACSet,
    registry: tuple[DpoRule, ...]) -> dict:
    _check_turn_binding(turn, source, registry)
    checked = turn.replay(record, judges=(("finite-edgewise-gradient-v001", _judge(source, registry)),),
        require_checker=True)
    actual = _with_receipt(checked, source, registry)
    expected_receipt = actual.get("operation_receipt")
    retained_receipt = record.get("operation_receipt")
    profile = dict(sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    if json.dumps(expected_receipt, **profile) != json.dumps(retained_receipt, **profile):
        raise RewriteRefusal("OPERATION_RECEIPT_MISMATCH")
    return actual
