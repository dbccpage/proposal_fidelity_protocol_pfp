"""
solve.py — Executable solver meeting the Challenge C005 contract.

Executes consistency verdict or cycle repair under a declared decoding control,
returning verified solution objects or typed refusal objects:
- CONTROL_NOT_HONORED: route failed probe_before_trust
- PROVIDER_REFUSAL_OR_INCOMPLETE: length cutoff or upstream refusal
- UNPARSEABLE: invalid JSON or shape violation

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .checkers import verify_consistency_certificate, verify_cycle_repair
from .client import GovernedClient
from .controls import ControlKind, get_control_config
from .schemas import validate_json_schema


@dataclass(frozen=True)
class SolveResult:
    status: str  # "SOLVED", "CONSISTENT", "INCONSISTENT", "UNKNOWN"
    payload: dict[str, Any]
    refusal: str | None = None
    cost_usd: float | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {"status": self.status}
        if self.refusal:
            res["refusal"] = self.refusal
        res.update(self.payload)
        return res


def solve_c005_case(
    case: dict[str, Any],
    client: GovernedClient,
    control: ControlKind,
    control_honored: bool = True,
) -> SolveResult:
    """Solve one consistency or cycle repair case under the specified decoding control."""
    # 1. Check if control was honored by route
    if control != ControlKind.NONE and not control_honored:
        return SolveResult(
            status="UNKNOWN",
            payload={"route": client.provider, "control": control.value},
            refusal="CONTROL_NOT_HONORED",
            cost_usd=0.0,
        )

    task_type = case.get("kind", "consistency")
    prompt = case.get("prompt", "")
    config = get_control_config(kind=control, task_family=task_type)

    # 2. Complete with governed client
    try:
        receipt = client.complete(prompt, config, max_tokens=64)
    except Exception as exc:
        return SolveResult(
            status="UNKNOWN",
            payload={"error": str(exc)},
            refusal="PROVIDER_REFUSAL_OR_INCOMPLETE",
            cost_usd=None,
        )

    # 3. Check finish reason
    if receipt.finish_reason == "length":
        return SolveResult(
            status="UNKNOWN",
            payload={"finish_reason": "length", "raw_content": receipt.content},
            refusal="PROVIDER_REFUSAL_OR_INCOMPLETE",
            cost_usd=receipt.cost_usd,
        )

    # 4. Parse content
    content = receipt.content.strip()
    try:
        parsed = json.loads(content)
    except Exception:
        # If control was NONE or LOGIT_BIAS, try extracting JSON substring
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end > start:
            try:
                parsed = json.loads(content[start : end + 1])
            except Exception:
                return SolveResult(
                    status="UNKNOWN",
                    payload={"raw_content": content},
                    refusal="UNPARSEABLE",
                    cost_usd=receipt.cost_usd,
                )
        else:
            return SolveResult(
                status="UNKNOWN",
                payload={"raw_content": content},
                refusal="UNPARSEABLE",
                cost_usd=receipt.cost_usd,
            )

    # 5. Schema shape validation
    schema_name = "consistency_verdict" if task_type == "consistency" else "cycle_repair_solution"
    valid, err = validate_json_schema(parsed, schema_name)
    if not valid:
        return SolveResult(
            status="UNKNOWN",
            payload={"raw_content": content, "schema_error": err},
            refusal="UNPARSEABLE",
            cost_usd=receipt.cost_usd,
        )

    # 6. Exact Host Verification
    if task_type == "consistency":
        edges = case.get("edges", [])
        verdict = parsed.get("verdict", "")
        cert = parsed.get("certificate", {})
        check = verify_consistency_certificate(edges, verdict, cert)
        if not check.is_valid:
            return SolveResult(
                status="UNKNOWN",
                payload={
                    "verdict": verdict,
                    "certificate": cert,
                    "verification_error": check.error_message,
                },
                refusal="FALSE_WITNESS",
                cost_usd=receipt.cost_usd,
            )
        return SolveResult(
            status=verdict,
            payload={"verdict": verdict, "certificate": cert},
            refusal=None,
            cost_usd=receipt.cost_usd,
        )

    elif task_type == "cycle_repair":
        claims = [e[2] for e in case.get("edges", [])]
        weights = case.get("weights", [1] * len(claims))
        repaired = parsed.get("repaired", [])
        declared_cost = parsed.get("weighted_l1")
        check = verify_cycle_repair(claims, weights, repaired, declared_cost)
        if not check.is_valid or not check.is_optimal:
            return SolveResult(
                status="UNKNOWN",
                payload={
                    "repaired": repaired,
                    "weighted_l1": declared_cost,
                    "verification_error": check.error_message,
                    "is_optimal": check.is_optimal,
                },
                refusal="SUBOPTIMAL_OR_INVALID_REPAIR",
                cost_usd=receipt.cost_usd,
            )
        return SolveResult(
            status="SOLVED",
            payload={"repaired": repaired, "weighted_l1": declared_cost, "is_optimal": True},
            refusal=None,
            cost_usd=receipt.cost_usd,
        )

    return SolveResult(
        status="UNKNOWN",
        payload={},
        refusal="UNKNOWN_TASK_KIND",
        cost_usd=receipt.cost_usd,
    )
