"""Bounded PFP proposal checking and answer-free repair feedback.

The proposer never supplies its own verdict. Domain judges are injected ports;
this use case neither solves the task nor compares against stored answers.
AuthorityEffect: None.
"""

from __future__ import annotations

import base64
from collections import deque
from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import unquote

from jsonschema import Draft202012Validator, validators
from jsonschema.exceptions import SchemaError

from ..domain.contracts.pfp_runtime import PfpPrompt, PfpTaskPrompt
from ..domain.pfp_ingress import strict_json


@dataclass(frozen=True)
class ProposalCheck:
    status: str
    failure_class: str
    judges: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Host-authored, bounded guidance. Raw judge diagnostics can contain answers and
# therefore never cross back into the model prompt.
REPAIR_RULES = {
    "ENVELOPE": "Return exactly the declared SPK-001 JSON envelope, without fences or prose.",
    "TASK_ENVELOPE": "Return exactly the declared task JSON schema and bound task/attempt/input identifiers, without fences or extra fields.",
    "CERTIFICATE": "Recompute the witness from the input. Check dimensions, identifiers, exact arithmetic, and every certificate equation before submitting.",
    "SCOPE": "An abstention is not a solution. Use a declared refusal only when its input predicate holds; otherwise supply a checkable witness.",
    "WIRE_DISCRIMINATOR": "Use exactly the status and kind literals declared in the task schema. They are separate fields; never invent values or change letter case.",
    "COBOUNDARY_RESIDUAL": "Integrate differences along a spanning tree, then compute every edge residual from its endpoint potentials instead of guessing a pattern. Certify the repaired cochain and a matching feasible circulation.",
    "PAULI_PHASE": "Track signed Pauli products and independent generator relations before searching sectors. Enumerate admissible joint eigenvalue sectors; derive energy, all minimizers, and degeneracy from that same sector list.",
}


def parse_proposal(raw: str) -> dict[str, Any]:
    """Strict common envelope; task-specific typing remains the domain judge's job."""
    if type(raw) is not str or len(raw.encode("utf-8")) > 1_048_576:
        raise ValueError("REPLY_SIZE_OR_TYPE")
    try:
        payload = strict_json(raw)
    except Exception as exc:
        raise ValueError("INVALID_EXACT_JSON") from exc
    keys = {"derived_under_policy", "summary", "process_integrity", "sections", "answer"}
    if type(payload) is not dict or set(payload) != keys:
        raise ValueError("ENVELOPE_KEYS")
    if payload["derived_under_policy"] != "SPK-001" or payload["sections"] != []:
        raise ValueError("ENVELOPE_POLICY_OR_SECTIONS")
    summary = payload["summary"]
    required = {"narrowest_defensible_thesis", "evidence_scope", "next_concrete_test"}
    if type(summary) is not dict or set(summary) != required:
        raise ValueError("ENVELOPE_SUMMARY")
    if any(type(v) is not str or not v.strip() for v in summary.values()):
        raise ValueError("ENVELOPE_SUMMARY_TEXT")
    integrity = payload["process_integrity"]
    if type(integrity) is not dict or set(integrity) != {
        "seed_allows_theory_refutation",
        "detected_prompt_biases",
        "should_continue",
    }:
        raise ValueError("ENVELOPE_INTEGRITY")
    if any(
        type(integrity[k]) is not bool for k in ("seed_allows_theory_refutation", "should_continue")
    ):
        raise ValueError("ENVELOPE_BOOLEAN")
    if type(integrity["detected_prompt_biases"]) is not list or any(
        type(v) is not str for v in integrity["detected_prompt_biases"]
    ):
        raise ValueError("ENVELOPE_BIASES")
    if type(payload["answer"]) is not dict:
        raise ValueError("ENVELOPE_ANSWER_OBJECT")
    return payload


def normalize_judgement(value: Any) -> tuple[bool, str]:
    """Only known checker shapes; never bool(value) or numeric coercion."""
    if type(value) is bool:
        return value, "ACCEPT" if value else "REJECT"
    if (
        type(value) is tuple
        and len(value) in (2, 3)
        and type(value[0]) is bool
        and type(value[1]) is str
    ):
        return value[0], value[1]
    if type(value) is dict and value.get("verdict") in ("PASS", "FAIL"):
        reason = value.get("reason", value.get("details"))
        if type(reason) is str:
            return value["verdict"] == "PASS", reason
    raise ValueError("INVALID_CHECKER_RESULT")


class CheckProposalUseCase:
    def execute(
        self,
        case: Mapping[str, Any],
        raw_reply: str,
        judges: Sequence[tuple[str, Callable[[Any, Any], Any]]],
    ) -> ProposalCheck:
        try:
            answer = parse_proposal(raw_reply)["answer"]
        except (ValueError, TypeError):
            return ProposalCheck("PROVIDER_COMPLETED", "ENVELOPE")
        return self.check_answer(case, answer, judges)

    def check_answer(self, case: Mapping[str, Any], answer: Any, judges) -> ProposalCheck:
        """Also accepts explicitly labelled NO_LLM controls without forging envelopes."""
        if not judges:
            return ProposalCheck("INFRASTRUCTURE_ERROR", "UNREGISTERED_CHECKER")
        results = []
        for name, judge in judges:
            try:
                accepted, reason = normalize_judgement(judge(deepcopy(case), deepcopy(answer)))
                results.append({"judge": name, "accepted": accepted, "reason": reason})
            except Exception as exc:
                results.append({"judge": name, "error": type(exc).__name__, "reason": str(exc)})
                return ProposalCheck("CHECKER_DEFECT", "CHECKER", tuple(results))
        if len({r["accepted"] for r in results}) != 1:
            return ProposalCheck("CHECKER_DEFECT", "DISAGREEMENT", tuple(results))
        refusal = type(answer) is dict and answer.get("status") in ("UNKNOWN", "OUT_OF_SCOPE")
        if all(r["accepted"] for r in results):
            return ProposalCheck(
                "TYPED_REFUSAL" if refusal else "HOST_ACCEPTED", "NONE", tuple(results)
            )
        failure_class = "SCOPE" if refusal else "CERTIFICATE"
        if not refusal:
            if any(
                "invalid status" in r["reason"].lower()
                or "unexpected status" in r["reason"].lower()
                for r in results
            ):
                failure_class = "WIRE_DISCRIMINATOR"
            elif any(
                r["judge"].startswith("circulation_checker:")
                and "coboundary relation broken" in r["reason"]
                for r in results
            ):
                failure_class = "COBOUNDARY_RESIDUAL"
            elif any(
                r["judge"] == "algebraic_checker:verify_certificate"
                and (
                    "Decomposition algebraic mismatch" in r["reason"]
                    or "Reported energy" in r["reason"]
                )
                for r in results
            ):
                failure_class = "PAULI_PHASE"
        return ProposalCheck("PROVIDER_COMPLETED", failure_class, tuple(results))


def _check_local_reference_graph(schema):
    """Reject unresolvable refs and recursion on the same instance before a send.

    References inside properties/items may recurse because each application
    advances into a child instance. Applying allOf/not/refs to the same instance
    must instead form an acyclic graph. Definitions declare nodes but do not
    apply their schemas to the enclosing instance.
    """
    nodes, resources, anchors, edges, references = {}, {}, {}, {}, []

    def visit(value, path=(), resource=()):
        if type(value) not in (dict, bool):
            return
        if type(value) is dict and "$id" in value:
            resource = path
        nodes[path], resources[path], edges[path] = value, resource, set()
        if type(value) is bool:
            return
        for keyword in ("$anchor", "$dynamicAnchor"):
            anchor = value.get(keyword)
            if type(anchor) is str:
                key = (resource, anchor)
                if key in anchors and anchors[key] != path:
                    raise ValueError("DUPLICATE_TASK_SCHEMA_ANCHOR")
                anchors[key] = path
        for keyword in ("$ref", "$dynamicRef"):
            if keyword in value:
                references.append((path, value[keyword]))

        def child(item, child_path, *, descends=False, definition=False):
            if type(item) not in (dict, bool):
                return  # The metaschema supplies the precise invalid-type error.
            visit(item, child_path, resource)
            if not descends and not definition:
                edges[path].add(child_path)

        for keyword in ("properties", "patternProperties", "dependentSchemas", "$defs", "definitions"):
            mapping = value.get(keyword)
            if type(mapping) is dict:
                for name, item in mapping.items():
                    child(item, path + (keyword, name),
                          descends=keyword in ("properties", "patternProperties"),
                          definition=keyword in ("$defs", "definitions"))
        for keyword in ("allOf", "anyOf", "oneOf", "prefixItems"):
            sequence = value.get(keyword)
            if type(sequence) is list:
                for index, item in enumerate(sequence):
                    child(item, path + (keyword, index), descends=keyword == "prefixItems")
        for keyword in ("not", "if", "then", "else", "items", "contains", "additionalProperties",
                        "unevaluatedProperties", "propertyNames", "unevaluatedItems", "contentSchema"):
            if keyword in value:
                child(value[keyword], path + (keyword,),
                      descends=keyword not in ("not", "if", "then", "else"))

    visit(schema)
    for path, reference in references:
        fragment = unquote(reference[1:])
        root = resources[path]
        if not fragment:
            target = root
        elif not fragment.startswith("/"):
            target = anchors.get((root, fragment))
        else:
            target, value = root, nodes[root]
            try:
                for part in fragment[1:].split("/"):
                    key = part.replace("~1", "/").replace("~0", "~")
                    key = int(key) if type(value) is list else key
                    value = value[key]
                    target += (key,)
            except (KeyError, IndexError, TypeError, ValueError):
                target = None
        if target not in nodes:
            raise ValueError("UNRESOLVED_TASK_SCHEMA_REFERENCE")
        edges[path].add(target)

    # Iterative topological elimination also bounds long, flat reference chains.
    incoming = dict.fromkeys(nodes, 0)
    for targets in edges.values():
        for target in targets:
            incoming[target] += 1
    ready = deque(path for path, count in incoming.items() if count == 0)
    removed = 0
    while ready:
        path = ready.popleft()
        removed += 1
        for target in edges[path]:
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
    if removed != len(nodes):
        raise ValueError("NONPRODUCTIVE_TASK_SCHEMA_REFERENCE")


def task_turn_validator(schema):
    """Native integer typing and local-only JSON Schema references, with no retrieval."""

    def local_references(value):
        if type(value) is dict:
            for key, item in value.items():
                if key in ("$ref", "$dynamicRef") and (
                    type(item) is not str or not item.startswith("#")
                ):
                    raise ValueError("EXTERNAL_SCHEMA_REFERENCE")
                if key in ("const", "enum", "default", "examples"):
                    continue  # Instance data is not a schema or a retrieval instruction.
                if key in (
                    "properties",
                    "patternProperties",
                    "$defs",
                    "definitions",
                    "dependentSchemas",
                ):
                    if type(item) is dict:
                        for subschema in item.values():
                            local_references(subschema)
                    continue
                local_references(item)
        elif type(value) is list:
            for item in value:
                local_references(item)

    local_references(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ValueError("INVALID_TASK_ANSWER_SCHEMA") from exc
    _check_local_reference_graph(schema)
    strict = validators.extend(
        Draft202012Validator,
        type_checker=Draft202012Validator.TYPE_CHECKER.redefine(
            "integer", lambda _, value: type(value) is int
        ),
    )
    return strict(schema)


class CheckPfpTaskTurnUseCase:
    """Check actual reply bytes; unchecked role prose never becomes HOST_ACCEPTED."""

    def execute(
        self,
        task: PfpTaskPrompt,
        prompt: PfpPrompt,
        raw_reply: bytes,
        *,
        judges=(),
        require_checker: bool = False,
    ) -> dict[str, Any]:
        from .pfp_prompt import task_turn_response_schema

        if type(raw_reply) is not bytes:
            raise ValueError("RAW_REPLY_BYTES_REQUIRED")
        if type(require_checker) is not bool:
            raise ValueError("INVALID_CHECKER_REQUIREMENT")
        result = dict(
            raw_reply_base64=base64.b64encode(raw_reply).decode("ascii"),
            raw_reply_sha256=sha256(raw_reply).hexdigest(),
            raw_reply_bytes=len(raw_reply),
            schema_valid=False,
            evidence_grade="UNVERIFIED",
            authority_effect="None",
        )
        checked = ProposalCheck("PROVIDER_COMPLETED", "TASK_ENVELOPE")
        try:
            schema = prompt.response_schema
            properties = schema["properties"]
            expected = task_turn_response_schema(task, properties["attempt_id"]["const"])
            if schema != expected:
                raise ValueError("PREPARED_TASK_INPUT_MISMATCH")
            payload = strict_json(raw_reply.decode("utf-8"))
            if not task_turn_validator(schema).is_valid(payload):
                raise ValueError("TASK_REPLY_SCHEMA")
            result.update(schema_valid=True, answer=deepcopy(payload["answer"]))
        except Exception as exc:
            result["reason"] = str(exc)
            result.update(checked.to_dict())
            return result
        if judges:
            checked = CheckProposalUseCase().check_answer(task.case, payload["answer"], judges)
            result["evidence_grade"] = (
                "UNVERIFIED" if checked.status == "CHECKER_DEFECT" else "TASK_CHECKED"
            )
        elif require_checker:
            checked = ProposalCheck("INFRASTRUCTURE_ERROR", "UNREGISTERED_CHECKER")
        else:
            checked = ProposalCheck("PROVIDER_COMPLETED", "NONE")
        result.update(checked.to_dict())
        return result


def repair_feedback(result: ProposalCheck) -> str | None:
    """Checker failures stop dependent stages; wrong candidates get bounded guidance."""
    return REPAIR_RULES.get(result.failure_class)
