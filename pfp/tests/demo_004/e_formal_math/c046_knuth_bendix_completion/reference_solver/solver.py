# AuthorityEffect: None.
"""
Reference Solver for C046: Knuth-Bendix Equational Completion with Joinability Certificates.
Pure Python standard library with DDC operational tracing and zero external dependencies.
"""

from typing import Any, Dict, List, Tuple

from .completion import knuth_bendix_completion
from .critical_pairs import get_critical_pairs
from .ddc_tracer import DDCTracer
from .term import Term, normalize, parse_term
from .term_order import TermOrder


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = case.get("case_id", "c046_case")
    task = case.get("task", "COMPLETE")
    tracer = DDCTracer(case_id)

    tracer.record_step("E", f"Received task {task} for case {case_id}")

    if task == "COMPLETE":
        eqs_raw = case.get("equations")
        if eqs_raw is None or not isinstance(eqs_raw, list):
            tracer.record_step("R", "Missing or invalid equations array")
            return {
                "case_id": case_id,
                "status": "REFUSED",
                "reason": "MALFORMED_INPUT",
                "witness": {"detail": "Missing equations"},
                "ddc_trace": tracer.get_summary(),
            }

        # Parse equations
        equations: List[Tuple[Term, Term]] = []
        for pair in eqs_raw:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                tracer.record_step("R", f"Malformed equation pair: {pair}")
                return {
                    "case_id": case_id,
                    "status": "REFUSED",
                    "reason": "MALFORMED_TERM",
                    "witness": {"pair": pair},
                    "ddc_trace": tracer.get_summary(),
                }
            try:
                l_term = parse_term(str(pair[0]))
                r_term = parse_term(str(pair[1]))
                equations.append((l_term, r_term))
            except Exception as e:
                tracer.record_step("R", f"Failed parsing equation: {pair}: {e}")
                return {
                    "case_id": case_id,
                    "status": "REFUSED",
                    "reason": "MALFORMED_TERM",
                    "witness": {"pair": pair, "error": str(e)},
                    "ddc_trace": tracer.get_summary(),
                }

        # Build term order
        precedence = case.get("precedence")
        order = TermOrder(precedence)
        tracer.record_step(
            "Lambda", f"Initialized TermOrder with {len(order.precedence)} precedence levels"
        )

        max_steps = case.get("max_steps", 200)
        tracer.record_step("D", f"Starting completion saturation with max_steps={max_steps}")
        ok, res = knuth_bendix_completion(equations, order, max_steps=max_steps)

        if not ok:
            tracer.record_step("R", f"Completion halted: {res['reason']}", res)
            return {
                "case_id": case_id,
                "status": "REFUSED",
                "reason": res["reason"],
                "witness": res,
                "ddc_trace": tracer.get_summary(),
            }

        tracer.record_step(
            "C", f"Generated and joined {res['joinability_certificates_count']} critical pairs"
        )
        tracer.record_step("I", f"Canonical convergent TRS reached with {res['rules_count']} rules")
        tracer.record_step("M", "All critical pairs validated joinable")
        tracer.record_step("T", "Emitted completion result")

        return {
            "case_id": case_id,
            "status": "SOLVED",
            "task": "COMPLETE",
            "converged": True,
            "steps": res["steps"],
            "rules_count": res["rules_count"],
            "rules": res["rules"],
            "joinability_certificates_count": res["joinability_certificates_count"],
            "joinability_certificates": res["joinability_certificates"],
            "ddc_trace": tracer.get_summary(),
        }

    elif task == "CHECK_CONFLUENCE":
        rules_raw = case.get("rules")
        if rules_raw is None or not isinstance(rules_raw, list):
            tracer.record_step("R", "Missing rules in CHECK_CONFLUENCE")
            return {
                "case_id": case_id,
                "status": "REFUSED",
                "reason": "MALFORMED_INPUT",
                "witness": {"detail": "Missing rules"},
                "ddc_trace": tracer.get_summary(),
            }

        rules: List[Tuple[Term, Term]] = []
        for r_entry in rules_raw:
            try:
                if isinstance(r_entry, dict):
                    lhs = parse_term(r_entry["lhs"])
                    rhs = parse_term(r_entry["rhs"])
                elif isinstance(r_entry, (list, tuple)):
                    lhs = parse_term(str(r_entry[0]))
                    rhs = parse_term(str(r_entry[1]))
                else:
                    raise ValueError(f"Unrecognized rule format: {r_entry}")
                rules.append((lhs, rhs))
            except Exception as e:
                tracer.record_step("R", f"Failed parsing rule: {r_entry}: {e}")
                return {
                    "case_id": case_id,
                    "status": "REFUSED",
                    "reason": "MALFORMED_TERM",
                    "witness": {"rule": r_entry, "error": str(e)},
                    "ddc_trace": tracer.get_summary(),
                }

        tracer.record_step("C", f"Computing critical pairs for {len(rules)} rules")
        cps = get_critical_pairs(rules)
        unjoinable = []

        for c1, c2, info in cps:
            norm1 = normalize(c1, rules)
            norm2 = normalize(c2, rules)
            if norm1 != norm2:
                unjoinable.append(
                    {
                        "critical_pair": [c1.to_json(), c2.to_json()],
                        "normal_forms": [norm1.to_json(), norm2.to_json()],
                        "source": info,
                    }
                )

        is_confluent = len(unjoinable) == 0
        tracer.record_step(
            "M", f"Confluence verdict: {is_confluent} (unjoinable count: {len(unjoinable)})"
        )
        tracer.record_step("T", "Emitted confluence determination")

        return {
            "case_id": case_id,
            "status": "SOLVED",
            "task": "CHECK_CONFLUENCE",
            "is_confluent": is_confluent,
            "critical_pairs_count": len(cps),
            "unjoinable_count": len(unjoinable),
            "unjoinable_critical_pairs": unjoinable,
            "ddc_trace": tracer.get_summary(),
        }

    elif task == "REDUCE":
        rules_raw = case.get("rules", [])
        term_str = case.get("term")
        if term_str is None:
            tracer.record_step("R", "Missing term in REDUCE")
            return {
                "case_id": case_id,
                "status": "REFUSED",
                "reason": "MALFORMED_INPUT",
                "witness": {"detail": "Missing term"},
                "ddc_trace": tracer.get_summary(),
            }

        try:
            target_term = parse_term(term_str)
            rules = []
            for r in rules_raw:
                if isinstance(r, dict):
                    rules.append((parse_term(r["lhs"]), parse_term(r["rhs"])))
                else:
                    rules.append((parse_term(str(r[0])), parse_term(str(r[1]))))
        except Exception as e:
            tracer.record_step("R", f"Failed parsing: {e}")
            return {
                "case_id": case_id,
                "status": "REFUSED",
                "reason": "MALFORMED_TERM",
                "witness": {"error": str(e)},
                "ddc_trace": tracer.get_summary(),
            }

        tracer.record_step("R", f"Normalizing term {term_str}")
        norm = normalize(target_term, rules)
        tracer.record_step("T", f"Reached normal form: {norm}")

        return {
            "case_id": case_id,
            "status": "SOLVED",
            "task": "REDUCE",
            "term": term_str,
            "normal_form": norm.to_json(),
            "ddc_trace": tracer.get_summary(),
        }

    else:
        tracer.record_step("R", f"Unknown task: {task}")
        return {
            "case_id": case_id,
            "status": "REFUSED",
            "reason": "UNKNOWN_TASK",
            "witness": {"task": task},
            "ddc_trace": tracer.get_summary(),
        }
