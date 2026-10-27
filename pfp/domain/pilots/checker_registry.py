"""Versioned pilot checker ingress. AuthorityEffect: None."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pfp.domain.pfp_ingress import (
    MAX_JSON_DEPTH as MAX_JSON_DEPTH,
)
from pfp.domain.pfp_ingress import (
    MAX_REPLY_BYTES as MAX_REPLY_BYTES,
)
from pfp.domain.pfp_ingress import (
    is_integer,
)
from pfp.domain.pfp_ingress import (
    strict_json as strict_json,
)
from pfp.domain.pfp_ingress import (
    unique_pairs as unique_pairs,
)

from ..kernel.result import RefusalCode
from ..types.base import EvaluationStatus
from .fail_closed_gate import FailClosedRefusalGate, GateEvaluationResult

CHECKER_VERSION = "pfp.pilot-checkers.v2"


@dataclass(frozen=True)
class CheckerDefinition:
    checker_id: str
    response_schema: dict[str, Any]
    version: str = CHECKER_VERSION


_INTEGER = {"type": "integer"}
_SCHEMAS = {
    "PFP-01-EXACT-LINALG": {"answer": _INTEGER},
    "PFP-02-EXACT-PRIMES": {"primes": {"type": "array", "items": _INTEGER}},
    "PFP-02-GRAPH-FACTS": {"answer": {"type": "object"}},
    "PFP-03-OBSERVER-VISIBILITY": {"answer": {"type": "object"}},
    "PFP-03-EXACT-FOL-DEDUCTION": {
        "verdict": {"type": "string", "enum": ["YES", "NO"]},
        "premise_count": _INTEGER,
    },
    "PFP-04-EXACT-EPISTEMIC-REFUSAL": {
        "computable": {"type": "boolean"}, "reason": {"type": "string", "minLength": 1},
    },
    "PFP-05-EXACT-2X2-DETERMINANT": {"det": _INTEGER},
}


def checker_definition(checker_id: str) -> CheckerDefinition:
    if checker_id not in _SCHEMAS:
        raise ValueError(f"UNKNOWN_CHECKER: {checker_id}")
    properties = _SCHEMAS[checker_id]
    # Return a detached schema: callers cannot mutate the registry.
    return CheckerDefinition(checker_id, json.loads(json.dumps({
        "type": "object", "properties": properties, "required": list(properties),
    })))


def evaluate_candidate(checker_id: str, expected: Any, payload: Any) -> GateEvaluationResult:
    try:
        checker_definition(checker_id)
    except ValueError:
        return GateEvaluationResult(
            EvaluationStatus.REFUSED, RefusalCode.MAP_UNDEFINED,
            reason=f"Unknown checker ID: {checker_id}",
        )
    return FailClosedRefusalGate.evaluate_candidate_payload(checker_id, expected, payload)


def is_acyclic(edges: list[tuple[int, int]]) -> bool:
    """Finite directed-edge witness check, independent of a preferred gold edge."""
    vertices = {vertex for edge in edges for vertex in edge}
    remaining = set(vertices)
    while remaining:
        roots = {v for v in remaining if not any(b == v and a in remaining for a, b in edges)}
        if not roots:
            return False
        remaining.difference_update(roots)
    return True


def valid_triangle_repair(answer: int, edges: list[tuple[int, int]]) -> bool:
    return (
        is_integer(answer) and 1 <= answer <= len(edges) and not is_acyclic(edges)
        and is_acyclic([edge for index, edge in enumerate(edges, 1) if index != answer])
    )
