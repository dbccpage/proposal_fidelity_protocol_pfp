"""Fixture-only protected-query prompt rewriting; no LLM or network calls."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from omega_engine_pfp.domain.prompt_representations.symbolic_prompt_representation import (
    SymbolicPromptRepresentation,
)
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

PROTECTED_ROLES = frozenset({"task", "constraint", "output"})
GRAMMAR_SHA256 = hashlib.sha256(b"pfp.symbolic-constraint-binding.v001").hexdigest()
ANSWER_SCHEMA = {
    "oneOf": [
        {
            "type": "object",
            "properties": {
                "status": {"const": "PROPOSE"},
                "potentials": {
                    "type": "object",
                    "properties": {
                        key: {"type": "string", "minLength": 1} for key in ("a", "b", "c")
                    },
                    "required": ["a", "b", "c"],
                    "additionalProperties": False,
                },
            },
            "required": ["status", "potentials"],
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {
                "status": {"const": "REFUSE"},
                "reason": {"type": "string", "minLength": 1},
            },
            "required": ["status", "reason"],
            "additionalProperties": False,
        },
    ],
}


def prompt_state(
    task: str = 'Find exact potentials on vertices a,b,c with a=0. Directed edge values: a→b=3/2; b→c=-7/3; a→c=-5/6. Keep "signs" and orientation.',
    constraint: str = "Use rational values; reject missing edges and report every edge residual.",
    output: str = "Return a JSON instance that validates against the supplied closed response schema, or a declared refusal instance. Do not return the schema itself.",
    source_id: str = "prompt-rewriting-fixture-v001",
) -> FiniteACSet:
    """Retain seed and contract bytes as attributes, not expected answers."""
    if any(type(text) is not str for text in (task, constraint, output, source_id)):
        raise RewriteRefusal("PROMPT_TEXT_TYPE")
    texts = (task, constraint, output)
    parts = tuple(
        Part(f"s{index}", role, (("position", str(index)), ("text", text)))
        for index, (role, text) in enumerate(
            zip(("task", "constraint", "output"), texts, strict=True)
        )
    )
    Part("source", "source", (("source_id", source_id),))
    source_digest = hashlib.sha256(
        json.dumps(texts, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return FiniteACSet(
        parts
        + (Part("source", "source", (("source_id", source_id), ("source_sha256", source_digest))),),
    )


def protected_query(state: FiniteACSet) -> tuple[tuple[str, str, bytes], ...]:
    """Independent judge for exact ordered source-slot/role/UTF-8-text identity."""
    if type(state) is not FiniteACSet:
        raise RewriteRefusal("GRAPH_TYPE")
    ordered = []
    for part in state.parts:
        if part.kind in PROTECTED_ROLES:
            attrs = dict(part.attrs)
            if (
                set(attrs) != {"position", "text"}
                or len(attrs["position"]) > 3
                or not re.fullmatch(r"0|[1-9][0-9]*", attrs["position"])
            ):
                raise RewriteRefusal("PROMPT_SLOT_ATTRIBUTES")
            ordered.append(
                (int(attrs["position"]), part.id, part.kind, attrs["text"].encode("utf-8"))
            )
    ordered.sort()
    if [item[0] for item in ordered] != list(range(len(ordered))) or not any(
        item[2] == "task" for item in ordered
    ):
        raise RewriteRefusal("PROMPT_SLOT_ORDER")
    return tuple((slot_id, role, text) for _, slot_id, role, text in ordered)


def _source(state: FiniteACSet) -> Part:
    sources = [part for part in state.parts if part.kind == "source"]
    if len(sources) != 1 or set(dict(sources[0].attrs)) != {"source_id", "source_sha256"}:
        raise RewriteRefusal("PROMPT_SOURCE")
    return sources[0]


def judge_preserved_prompt(before: FiniteACSet, after: FiniteACSet) -> None:
    """Structural admissibility alone does not imply the protected query equality."""
    if protected_query(before) != protected_query(after) or _source(before) != _source(after):
        raise RewriteRefusal("PROTECTED_QUERY_CHANGED")


def insertion_rules(state: FiniteACSet) -> tuple[DpoRule, ...]:
    """Versioned registered attachments; neither computes or discloses an answer."""
    task = next(part for part in state.parts if part.kind == "task")
    left = FiniteACSet((task,))
    rules = []
    for rule_id, kind, attrs in (
        (
            "prompt_hint_v001",
            "hint",
            (("text", "Check each protected constraint before proposing a certificate."),),
        ),
        ("prompt_symbolic_v001", "encoding", (("mode", "symbolic-constraint-binding-v001"),)),
    ):
        extra = Part("attachment", kind, attrs)
        rules.append(
            DpoRule(
                rule_id,
                left,
                left,
                FiniteACSet(
                    (task, extra), (Link("attachment_link", "context", extra.id, task.id),)
                ),
            )
        )
    return tuple(rules)


@dataclass(frozen=True)
class PromptRewrite:
    rewrite: RewriteResult
    rule_sha256: str


def operation_receipt(rewrite: PromptRewrite) -> dict:
    result = rewrite.rewrite
    return {
        "rule_id": result.rule_id,
        "rule_sha256": rewrite.rule_sha256,
        "before_sha256": result.before_digest,
        "after_sha256": result.after_digest,
        "part_match": dict(result.part_match),
        "link_match": dict(result.link_match),
        "fuel": result.fuel_remaining + 1,
        "fuel_remaining": result.fuel_remaining,
    }


def rewrite_prompt(
    state: FiniteACSet,
    registry: tuple[DpoRule, ...],
    rule_id: str,
    part_match: dict[str, str],
    link_match: dict[str, str],
    *,
    source_sha256: str,
    fuel: int = 2,
) -> PromptRewrite:
    if type(source_sha256) is not str or graph_digest(state) != source_sha256:
        raise RewriteRefusal("STALE_SOURCE")
    result = apply_registered_rule(
        state,
        registry,
        rule_id,
        part_match,
        link_match,
        fuel=fuel,
        protected_parts=frozenset(
            part.id for part in state.parts if part.kind in PROTECTED_ROLES | {"source"}
        ),
    )
    judge_preserved_prompt(state, result.state)
    rule = next(rule for rule in registry if rule.rule_id == rule_id)
    return PromptRewrite(result, rule_digest(rule))


def render_prompt(state: FiniteACSet) -> str:
    query = protected_query(state)
    source = dict(_source(state).attrs)
    attachments = [part for part in state.parts if part.kind in {"hint", "encoding"}]
    symbolic = any(part.kind == "encoding" for part in attachments)
    if symbolic:
        roles = [(f"s{index}", role) for index, (_, role, _) in enumerate(query)]
        texts = {f"s{index}": text.decode("utf-8") for index, (_, _, text) in enumerate(query)}
        representation = SymbolicPromptRepresentation.from_bindings(
            source_id=source["source_id"],
            source_sha256=source["source_sha256"],
            proposal_sha256=graph_digest(state),
            grammar_sha256=GRAMMAR_SHA256,
            slot_roles=roles,
            slot_texts=texts,
        )
        rendered = representation.render()
    else:
        rendered = json.dumps(
            {
                "source_id": source["source_id"],
                "slots": [
                    {"slot": slot, "role": role, "text": text.decode("utf-8")}
                    for slot, role, text in query
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    hints = [dict(part.attrs)["text"] for part in attachments if part.kind == "hint"]
    return rendered + (
        "\nUntrusted optional hints: " + json.dumps(hints, ensure_ascii=False) if hints else ""
    )


def prepared_turn(state: FiniteACSet, *, rewrite: PromptRewrite | None = None) -> PreparedTaskTurn:
    """Wrap every rendered seed using the existing typed PFP boundary."""
    context = {
        "source_mode": "FIXTURE_ONLY",
        "authority_effect": "None",
        "graph_sha256": graph_digest(state),
    }
    if rewrite is not None:
        if type(rewrite) is not PromptRewrite or rewrite.rewrite.state != state:
            raise RewriteRefusal("TURN_REWRITE_MISMATCH")
        context["rewrite"] = operation_receipt(rewrite)
    return prepare_task_turn(
        system="Answer the protected task. Return only a JSON instance that validates against the supplied PFP response schema; do not return the schema itself.",
        user=render_prompt(state),
        task_id="acset-prompt-rewriting-v001",
        attempt_id="fixture:0",
        answer_schema=ANSWER_SCHEMA,
        context=context,
    )


def replay_fixture_record(source: FiniteACSet, registry: tuple[DpoRule, ...], record: dict) -> dict:
    """Reexecute the host step and recheck retained PFP bytes; never send a prompt."""
    if type(record) is not dict or type(record.get("operation_receipt")) is not dict:
        raise RewriteRefusal("OPERATION_RECEIPT_SHAPE")
    expected = record["operation_receipt"]
    fields = {
        "rule_id",
        "rule_sha256",
        "before_sha256",
        "after_sha256",
        "part_match",
        "link_match",
        "fuel",
        "fuel_remaining",
    }
    if set(expected) != fields:
        raise RewriteRefusal("OPERATION_RECEIPT_SHAPE")
    matches = tuple(rule for rule in registry if rule.rule_id == expected["rule_id"])
    if len(matches) != 1 or rule_digest(matches[0]) != expected["rule_sha256"]:
        raise RewriteRefusal("RULE_DIGEST_MISMATCH")
    actual = rewrite_prompt(
        source,
        registry,
        expected["rule_id"],
        expected["part_match"],
        expected["link_match"],
        source_sha256=expected["before_sha256"],
        fuel=expected["fuel"],
    )
    profile = dict(sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    receipt = operation_receipt(actual)
    if json.dumps(receipt, **profile) != json.dumps(expected, **profile):
        raise RewriteRefusal("OPERATION_RECEIPT_MISMATCH")
    for key in ("rule_id", "rule_sha256", "before_sha256", "after_sha256", "fuel_remaining"):
        if json.dumps(record.get(key), **profile) != json.dumps(receipt[key], **profile):
            raise RewriteRefusal("OPERATION_RECEIPT_MISMATCH")
    turn = prepared_turn(actual.rewrite.state, rewrite=actual)
    public = {
        "system": turn.prompt.system,
        "user": turn.prompt.user,
        "response_schema": turn.prompt.response_schema,
    }
    if json.dumps(public, **profile) != json.dumps(record.get("pfp_turn"), **profile):
        raise RewriteRefusal("PUBLIC_TURN_MISMATCH")
    checked = turn.replay(record)
    if not checked["schema_valid"]:
        raise RewriteRefusal("PFP_FIXTURE_CHECK_FAILED")
    return {"operation_receipt": receipt, "checked": checked}
