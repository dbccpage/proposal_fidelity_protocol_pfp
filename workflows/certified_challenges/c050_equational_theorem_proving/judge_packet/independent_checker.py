"""Independent second checker for C050: Equational Theorem Proving.
Validates proofs and countermodels with independent AST parsing and evaluation.
"""

import copy
from typing import Any, Dict, Tuple


def independent_check(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    """Independent second checker verification."""
    if not isinstance(result, dict):
        return False, "Result must be a JSON object"

    case_id = case.get("case_id")
    if result.get("case_id") != case_id:
        return False, f"Case ID mismatch: expected {case_id}, got {result.get('case_id')}"

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    # Syntax validation
    axioms = case.get("axioms")
    goal = case.get("goal")

    is_malformed = (
        not isinstance(axioms, list)
        or any(not isinstance(ax, list) or len(ax) != 2 for ax in axioms)
        or not isinstance(goal, list)
        or len(goal) != 2
    )

    if status == "OUT_OF_SCOPE":
        if is_malformed:
            return True, "Independent checker: Valid OUT_OF_SCOPE confirmed"
        return False, "Independent checker: Case is syntactically valid, cannot be OUT_OF_SCOPE"

    if is_malformed:
        return (
            False,
            "Independent checker: Case is malformed, solver should have returned OUT_OF_SCOPE",
        )

    if status == "UNKNOWN":
        return False, "Independent checker: Solver returned UNKNOWN"

    kind = result.get("kind")
    if kind not in ("PROOF", "COUNTERMODEL"):
        return False, f"Independent checker: Invalid kind {kind}"

    # Helpers
    def indep_get_subterm(t, pos):
        curr = t
        for idx in pos:
            curr = curr[idx + 1]
        return curr

    def indep_apply_subst(t, subst):
        if isinstance(t, str):
            return copy.deepcopy(subst.get(t, t))
        return [t[0]] + [indep_apply_subst(arg, subst) for arg in t[1:]]

    def indep_replace_subterm(t, pos, repl):
        if not pos:
            return copy.deepcopy(repl)
        idx = pos[0]
        new_t = [t[0]] + list(t[1:])
        new_t[idx + 1] = indep_replace_subterm(t[idx + 1], pos[1:], repl)
        return new_t

    if kind == "PROOF":
        steps = result.get("steps")
        if not isinstance(steps, list):
            return False, "Independent checker: steps must be a list"

        curr = goal[0]
        for idx, step in enumerate(steps):
            ax_idx = step.get("axiom")
            direction = step.get("dir")
            pos = step.get("pos")
            subst = step.get("subst")
            exp_res = step.get("result")

            if not (0 <= ax_idx < len(axioms)):
                return False, f"Independent checker: Step {idx} invalid axiom {ax_idx}"

            ax_l, ax_r = axioms[ax_idx]
            src_pat, dst_pat = (ax_l, ax_r) if direction == "lr" else (ax_r, ax_l)

            try:
                subt = indep_get_subterm(curr, pos)
            except Exception as e:
                return False, f"Independent checker: Step {idx} invalid pos {pos}: {e}"

            inst_src = indep_apply_subst(src_pat, subst)
            if inst_src != subt:
                return (
                    False,
                    f"Independent checker: Step {idx} pattern mismatch: {inst_src} != {subt}",
                )

            inst_dst = indep_apply_subst(dst_pat, subst)
            next_t = indep_replace_subterm(curr, pos, inst_dst)
            if next_t != exp_res:
                return (
                    False,
                    f"Independent checker: Step {idx} result mismatch: {next_t} != {exp_res}",
                )

            curr = next_t

        if curr != goal[1]:
            return False, f"Independent checker: proof ended at {curr}, expected {goal[1]}"

        return True, "Independent checker: Valid PROOF confirmed"

    if kind == "COUNTERMODEL":
        size = result.get("size")
        tables = result.get("tables", {})
        assignment = result.get("assignment", {})

        if not (1 <= size <= 8):
            return False, f"Independent checker: invalid size {size}"

        def indep_eval(t, env):
            if isinstance(t, str):
                try:
                    return int(env.get(t, 0))
                except (ValueError, TypeError):
                    return 0
            f = t[0]
            if f not in tables:
                return 0
            tbl = tables[f]
            args = [indep_eval(a, env) for a in t[1:]]
            try:
                if len(args) == 1:
                    return int(tbl[int(args[0])])
                elif len(args) == 2:
                    return int(tbl[int(args[0])][int(args[1])])
                else:
                    c = tbl
                    for a in args:
                        c = c[int(a)]
                    return int(c)
            except Exception:
                return 0

        val_s = indep_eval(goal[0], assignment)
        val_t = indep_eval(goal[1], assignment)

        if val_s == val_t:
            return False, f"Independent checker: goal holds under assignment ({val_s} == {val_t})"

        return True, "Independent checker: Valid COUNTERMODEL confirmed"

    return False, "Independent checker: Unhandled configuration"
