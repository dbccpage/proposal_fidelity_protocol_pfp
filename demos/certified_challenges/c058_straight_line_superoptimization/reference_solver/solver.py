"""Main solver entrypoint for C058 Straight-Line Superoptimization."""

from typing import Any, Dict

from .evaluator import validate_ir
from .superoptimizer import optimize_program


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """Solves a straight-line superoptimization problem instance.

    Args:
        case: Dictionary containing:
            - case_id: string identifier
            - width: bit width (8, 16, 32, 64)
            - inputs: list of input variable names (e.g. ["x", "y"])
            - ops: list of instructions [target, op, ...]
            - out: output variable name
            - target_len: maximum allowed length of shortened program (optional)

    Returns:
        JSON-serializable response dictionary:
            - status: "SOLVED", "UNKNOWN", or "OUT_OF_SCOPE"
            - ops, out: if SOLVED
            - code: if UNKNOWN
            - witness: if OUT_OF_SCOPE
    """
    case_id = case.get("case_id", "unknown") if isinstance(case, dict) else "unknown"

    is_valid, err_code, witness = validate_ir(case)
    if not is_valid:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": witness or {"reason": err_code},
        }

    status, ops, out = optimize_program(case)

    if status == "SOLVED":
        return {"case_id": case_id, "status": "SOLVED", "ops": ops, "out": out}
    else:
        return {"case_id": case_id, "status": "UNKNOWN", "code": "NO_SHORTER_FOUND"}
