"""Host-only, source-specific seed checks. AuthorityEffect: None.

The host consumes actual candidate maps, tables and exact witnesses. Old
boolean-only attestations are refused rather than filled by reference fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .seed_checks import SEED_IDS, SeedCheckFailure, check


@dataclass
class GateResult:
    seed_id: str
    passed: bool
    verdicts: Dict[str, bool] = field(default_factory=dict)
    failure_reasons: List[str] = field(default_factory=list)
    computed_evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(seed_id=self.seed_id, passed=self.passed, verdicts=self.verdicts,
                    failure_reasons=self.failure_reasons, computed_evidence=self.computed_evidence)


def evaluate_seed_response(seed_id: str, parsed_payload: Dict[str, Any]) -> GateResult:
    """Check this candidate, with unsupported obligations distinguished from rejection."""
    try:
        evidence = check(seed_id, parsed_payload)
    except SeedCheckFailure as exc:
        return GateResult(seed_id, False, {"actual_seed_witness": False}, [str(exc)])
    except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError) as exc:
        return GateResult(seed_id, False, {"actual_seed_witness": False},
                          ["INVALID_WITNESS: " + type(exc).__name__])
    return GateResult(seed_id, True, {"actual_seed_witness": True}, [], evidence)


# Retain the public names; they now share the same deciding implementation.
def evaluate_demo_n02(payload):
    return evaluate_seed_response("DEMO-N02", payload)


def evaluate_demo_n03(payload):
    return evaluate_seed_response("DEMO-N03", payload)


def evaluate_demo_n06(payload):
    return evaluate_seed_response("DEMO-N06", payload)


def evaluate_demo_n08(payload):
    return evaluate_seed_response("DEMO-N08", payload)


def evaluate_demo_b16(payload):
    return evaluate_seed_response("DEMO-B16", payload)


def evaluate_demo_b17(payload):
    return evaluate_seed_response("DEMO-B17", payload)


def evaluate_demo_b18(payload):
    return evaluate_seed_response("DEMO-B18", payload)


def evaluate_demo_q23(payload):
    return evaluate_seed_response("DEMO-Q23", payload)


SEED_EVALUATORS = {
    seed_id: (lambda payload, selected=seed_id: evaluate_seed_response(selected, payload))
    for seed_id in SEED_IDS
}
