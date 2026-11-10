"""
schemas.py — JSON Schema and GBNF grammar contracts for Challenge C005.

Defines strict structured output schemas and corresponding GBNF grammar
definitions for consistency certificates and cycle repairs.
"""

from __future__ import annotations

from typing import Any

# JSON Schema for C001 Consistency Verdict and Certificate
CONSISTENCY_JSON_SCHEMA: dict[str, Any] = {
    "name": "consistency_verdict",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["CONSISTENT", "INCONSISTENT"],
                "description": "Whether the given linear difference relations have a valid integer potential.",
            },
            "certificate": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": "Map from item identifier to integer potential string, or cycle obstruction.",
            },
        },
        "required": ["verdict", "certificate"],
        "additionalProperties": False,
    },
}

# JSON Schema for C004 Cycle Repair Solution
CYCLE_REPAIR_JSON_SCHEMA: dict[str, Any] = {
    "name": "cycle_repair_solution",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["SOLVED", "UNPARSEABLE"],
                "description": "Status of the cycle repair.",
            },
            "repaired": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Repaired integer claims in cyclic order summing to zero.",
            },
            "weighted_l1": {
                "type": "string",
                "description": "Weighted L1 distance between initial and repaired claims.",
            },
        },
        "required": ["status", "repaired", "weighted_l1"],
        "additionalProperties": False,
    },
}

# GBNF Grammars
CONSISTENCY_GBNF_GRAMMAR: str = r"""root ::= "{" ws "\"verdict\":" ws verdict_val "," ws "\"certificate\":" ws cert_obj "}" ws
verdict_val ::= "\"CONSISTENT\"" | "\"INCONSISTENT\""
cert_obj ::= "{" ws (pair ("," ws pair)*)? "}" ws
pair ::= string ":" ws integer_str
string ::= "\"" [a-zA-Z0-9_]+ "\""
integer_str ::= "\"" ("-"? [0-9]+) "\""
ws ::= [ \t\n\r]*
"""

CYCLE_REPAIR_GBNF_GRAMMAR: str = r"""root ::= "{" ws "\"status\":" ws "\"SOLVED\"," ws "\"repaired\":" ws int_array "," ws "\"weighted_l1\":" ws integer_str "}" ws
int_array ::= "[" ws (integer_str ("," ws integer_str)*)? "]" ws
integer_str ::= "\"" ("-"? [0-9]+) "\""
ws ::= [ \t\n\r]*
"""


def validate_json_schema(obj: Any, schema_name: str) -> tuple[bool, str | None]:
    """Validate a parsed JSON object against the declared schema shape.

    Returns (True, None) if valid, or (False, error_reason) if invalid.
    """
    if not isinstance(obj, dict):
        return False, "Output root must be a JSON object"

    if schema_name == "consistency_verdict":
        if set(obj.keys()) != {"verdict", "certificate"}:
            return False, f"Keys must be exactly verdict and certificate, got {list(obj.keys())}"
        if obj.get("verdict") not in ("CONSISTENT", "INCONSISTENT"):
            return False, f"Invalid verdict value: {obj.get('verdict')}"
        cert = obj.get("certificate")
        if not isinstance(cert, dict):
            return False, "Certificate must be a dictionary"
        for k, v in cert.items():
            if not isinstance(k, str) or not isinstance(v, str):
                return False, f"Certificate entry must be str -> str, got {type(k)} -> {type(v)}"
        return True, None

    elif schema_name == "cycle_repair_solution":
        if set(obj.keys()) != {"status", "repaired", "weighted_l1"}:
            return (
                False,
                f"Keys must be exactly status, repaired, weighted_l1, got {list(obj.keys())}",
            )
        if obj.get("status") not in ("SOLVED", "UNPARSEABLE"):
            return False, f"Invalid status: {obj.get('status')}"
        repaired = obj.get("repaired")
        if not isinstance(repaired, list) or not all(isinstance(x, str) for x in repaired):
            return False, "Repaired must be a list of strings"
        if not isinstance(obj.get("weighted_l1"), str):
            return False, "weighted_l1 must be a string"
        return True, None

    return False, f"Unknown schema_name: {schema_name}"
