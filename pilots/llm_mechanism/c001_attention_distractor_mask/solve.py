"""
solve.py — Standard executable interface for Challenge C001.

Exposes `def solve(case: dict) -> dict` returning canonical JSON outputs:
- SOLVED (verdict, repair, or audit)
- OUT_OF_SCOPE (with field and reason witness)
- UNKNOWN (with refusal reason)
"""

from __future__ import annotations

from typing import Any, Dict

from .solver import (
    ConstraintSystem,
    audit_witness,
    format_int,
    host_verdict,
    solve_single_repair,
)


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """Solves a Symbol Game Challenge C001 case.

    Args:
        case: Dictionary containing the problem instance:
            - items: List[str]
            - edges: List[Tuple[str, str, int]]
            - claims: Dict[Tuple[str, str] | str, int]
            - kind: "verdict" | "repair" | "audit"
            - claimed_potential: Optional[Dict[str, str | int]]

    Returns:
        JSON-serializable response dictionary adhering strictly to the C001 schema.
    """
    if not isinstance(case, dict):
        return {
            "status": "OUT_OF_SCOPE",
            "witness": {"field": "case", "reason": "MUST_BE_DICT"},
        }

    kind = case.get("kind")
    if kind not in ("verdict", "repair", "audit"):
        return {
            "status": "OUT_OF_SCOPE",
            "witness": {"field": "kind", "reason": f"UNSUPPORTED_KIND_{kind!r}"},
        }

    # Validate and parse the constraint graph
    try:
        system = ConstraintSystem.from_dict(case)
    except ValueError as exc:
        msg = str(exc)
        field = (
            "edges"
            if ("edge" in msg or "relation" in msg or "opposed" in msg)
            else ("claims" if "claim" in msg else "items")
        )
        return {
            "status": "OUT_OF_SCOPE",
            "witness": {"field": field, "reason": msg},
        }
    except Exception as exc:
        return {
            "status": "OUT_OF_SCOPE",
            "witness": {"field": "case", "reason": f"UNPARSEABLE: {exc}"},
        }

    if kind == "verdict":
        status, result = host_verdict(system)
        if status == "CONSISTENT" and isinstance(result, dict):
            # Format potentials as canonical decimal strings
            pot_formatted = {k: format_int(v) for k, v in result.items()}
            return {
                "status": "SOLVED",
                "kind": "verdict",
                "answer": "CONSISTENT",
                "potential": pot_formatted,
            }
        elif status == "CONTRADICTION" and isinstance(result, list):
            return {
                "status": "SOLVED",
                "kind": "verdict",
                "answer": "CONTRADICTION",
                "cycle": result,
            }
        else:
            return {
                "status": "UNKNOWN",
                "refusal": f"VERDICT_FAILED_WITH_STATUS_{status}",
            }

    elif kind == "repair":
        return solve_single_repair(system)

    elif kind == "audit":
        claimed = case.get("claimed_potential")
        if claimed is None:
            return {
                "status": "OUT_OF_SCOPE",
                "witness": {"field": "claimed_potential", "reason": "MISSING_CLAIMED_POTENTIAL"},
            }
        return audit_witness(system, claimed)

    return {
        "status": "UNKNOWN",
        "refusal": f"UNHANDLED_KIND_{kind}",
    }
