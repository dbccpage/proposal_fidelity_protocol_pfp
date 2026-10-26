"""Reference solver entry point for Challenge C056: DFA Minimization and Equivalence."""

from typing import Any, Dict

from .dfa_engine import check_equivalence, compile_minimal_dfa
from .regex_parser import ParseError, parse_regex


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    cid = case.get("case_id")
    task = case.get("task")
    alphabet = case.get("alphabet")

    if not isinstance(alphabet, list) or len(alphabet) == 0:
        return {"case_id": cid, "status": "OUT_OF_SCOPE", "witness": {"reason": "INVALID_ALPHABET"}}

    # Verify alphabet elements are valid single character strings
    for a in alphabet:
        if not isinstance(a, str) or len(a) != 1 or a in ("%", "#", "(", ")", "*", "|"):
            return {
                "case_id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "INVALID_ALPHABET_SYMBOL"},
            }

    if task == "MINIMIZE":
        regex_str = case.get("regex")
        if not isinstance(regex_str, str):
            return {
                "case_id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "INVALID_REGEX_TYPE"},
            }
        try:
            ast = parse_regex(regex_str, alphabet)
        except ParseError as pe:
            return {
                "case_id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "PARSE_ERROR", "detail": str(pe)},
            }
        except Exception as e:
            return {
                "case_id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "PARSE_ERROR", "detail": str(e)},
            }

        min_dfa = compile_minimal_dfa(ast, alphabet)
        return {
            "case_id": cid,
            "status": "SOLVED",
            "states": min_dfa["states"],
            "accept": min_dfa["accept"],
            "delta": min_dfa["delta"],
            "access": min_dfa["access"],
            "separators": min_dfa["separators"],
        }

    elif task == "EQUIV":
        r1_str = case.get("r1")
        r2_str = case.get("r2")
        if not isinstance(r1_str, str) or not isinstance(r2_str, str):
            return {
                "case_id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "INVALID_REGEX_TYPE"},
            }
        try:
            ast1 = parse_regex(r1_str, alphabet)
            ast2 = parse_regex(r2_str, alphabet)
        except ParseError as pe:
            return {
                "case_id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "PARSE_ERROR", "detail": str(pe)},
            }
        except Exception as e:
            return {
                "case_id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "PARSE_ERROR", "detail": str(e)},
            }

        m1 = compile_minimal_dfa(ast1, alphabet)
        m2 = compile_minimal_dfa(ast2, alphabet)
        eq_res = check_equivalence(m1, m2, alphabet)

        res = {"case_id": cid, "status": "SOLVED", **eq_res}
        return res

    else:
        return {
            "case_id": cid,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "UNKNOWN_TASK", "task": str(task)},
        }
