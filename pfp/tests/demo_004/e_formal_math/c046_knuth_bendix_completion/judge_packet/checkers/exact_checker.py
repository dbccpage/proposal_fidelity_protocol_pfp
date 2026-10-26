# AuthorityEffect: None.
"""
Exact Checker for C046: Knuth-Bendix Completion with Joinability Certificates.
Validates solver outputs against algebraic confluence, termination order, term reduction,
and (for COMPLETE) soundness: every submitted rule must follow from the input equations.
"""

from typing import Any, Dict, List, Tuple

from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.judge_packet.checkers.judge_completion import (
    follows_from,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.reference_solver.critical_pairs import (
    get_critical_pairs,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.reference_solver.term import (
    Term,
    normalize,
    parse_term,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.reference_solver.term_order import (
    TermOrder,
)


def check_exact(case: Dict[str, Any], ans: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(ans, dict):
        return False, "Answer must be a dictionary"

    if ans.get("case_id") != case.get("case_id"):
        return False, f"case_id mismatch: expected {case.get('case_id')}, got {ans.get('case_id')}"

    status = ans.get("status")
    if status not in {"SOLVED", "REFUSED"}:
        return False, f"Invalid status: {status}"

    task = case.get("task", "COMPLETE")

    if status == "REFUSED":
        if "reason" not in ans:
            return False, "Missing refusal reason"
        return True, f"Valid refusal with reason: {ans['reason']}"

    # Status is SOLVED
    if task == "COMPLETE":
        for field in ["converged", "rules_count", "rules", "joinability_certificates_count"]:
            if field not in ans:
                return False, f"Missing field in COMPLETE task: {field}"

        rules_list = ans["rules"]
        if not isinstance(rules_list, list) or len(rules_list) != ans["rules_count"]:
            return False, "rules list does not match rules_count"

        # Parse rules and check termination ordering
        precedence = case.get("precedence")
        order = TermOrder(precedence)
        parsed_rules: List[Tuple[Term, Term]] = []
        for r_entry in rules_list:
            if not isinstance(r_entry, dict) or "lhs" not in r_entry or "rhs" not in r_entry:
                return False, f"Malformed rule entry: {r_entry}"
            try:
                lhs = parse_term(r_entry["lhs"])
                rhs = parse_term(r_entry["rhs"])
            except Exception as e:
                return False, f"Failed parsing rule: {r_entry}: {e}"

            if not order.greater(lhs, rhs):
                return (
                    False,
                    f"Rule fails reduction ordering: {r_entry['lhs']} is not > {r_entry['rhs']}",
                )
            parsed_rules.append((lhs, rhs))

        # Check local confluence via critical pairs
        cps = get_critical_pairs(parsed_rules)
        for c1, c2, info in cps:
            norm1 = normalize(c1, parsed_rules)
            norm2 = normalize(c2, parsed_rules)
            if norm1 != norm2:
                return (
                    False,
                    f"Rules not confluent! Critical pair ({c1}, {c2}) reduces to distinct normal forms: {norm1} != {norm2}",
                )

        # Verify that all original input equations join under the submitted rules
        for eq_pair in case.get("equations", []):
            try:
                s_t = parse_term(str(eq_pair[0]))
                t_t = parse_term(str(eq_pair[1]))
                s_norm = normalize(s_t, parsed_rules)
                t_norm = normalize(t_t, parsed_rules)
                if s_norm != t_norm:
                    return (
                        False,
                        f"Input equation {eq_pair} is not joinable under submitted TRS: {s_norm} != {t_norm}",
                    )
            except Exception as e:
                return False, f"Error validating input equation {eq_pair}: {e}"

        # Soundness: every submitted rule must follow from the input equations. The judge's own
        # completion (judge_completion.py; budget independent of the case's max_steps) decides it.
        try:
            input_eqs = [(str(eq[0]), str(eq[1])) for eq in case.get("equations", [])]
        except (TypeError, IndexError, KeyError) as e:
            return False, f"Cannot read input equations for the soundness check: {e}"
        sound, detail = follows_from(
            input_eqs, precedence, [(r["lhs"], r["rhs"]) for r in rules_list]
        )
        if sound is None:
            return False, f"Soundness not certified: {detail}"
        if not sound:
            return False, f"Unsound completion: {detail}"

        return (
            True,
            f"Convergent TRS verified with {len(parsed_rules)} rules and 0 unjoinable critical pairs",
        )

    elif task == "CHECK_CONFLUENCE":
        if "is_confluent" not in ans:
            return False, "Missing is_confluent field"

        # Verify truth using reference solver
        from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.reference_solver.solver import (
            solve as ref_solve,
        )

        ref_ans = ref_solve(case)
        if ans["is_confluent"] != ref_ans["is_confluent"]:
            return (
                False,
                f"Confluence mismatch: expected {ref_ans['is_confluent']}, got {ans['is_confluent']}",
            )

        return True, f"Confluence check verified: is_confluent={ans['is_confluent']}"

    elif task == "REDUCE":
        if "normal_form" not in ans or "term" not in ans:
            return False, "Missing normal_form or term field"

        from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.reference_solver.solver import (
            solve as ref_solve,
        )

        ref_ans = ref_solve(case)
        if ans["normal_form"] != ref_ans["normal_form"]:
            return (
                False,
                f"Normal form mismatch: expected {ref_ans['normal_form']}, got {ans['normal_form']}",
            )

        return True, f"Term reduced to unique normal form {ans['normal_form']}"

    return False, f"Unknown task: {task}"
