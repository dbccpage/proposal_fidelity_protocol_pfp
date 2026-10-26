# AuthorityEffect: None.
"""
Knuth-Bendix Completion Algorithm with Joinability Certificates for C046.
Uses the textbook agenda-based saturation loop with term size priority queuing
and complete inter-reduction.
"""

from typing import Any, Dict, List, Tuple

from .critical_pairs import rename_vars
from .term import Fun, Term, Var, mgu, normalize, reduce_one_step
from .term_order import TermOrder


def term_size(t: Term) -> int:
    """Computes total node count of term tree."""
    if t.is_var():
        return 1
    assert isinstance(t, Fun)
    return 1 + sum(term_size(a) for a in t.args)


def canonicalize_rule(lhs: Term, rhs: Term) -> Tuple[Term, Term]:
    """Standardizes variable names to x, y, z, u, v, w, x0, ... in order of appearance."""
    var_map: Dict[str, str] = {}
    names = ["x", "y", "z", "u", "v", "w"]
    counter = 0

    def get_var_name(old: str) -> str:
        nonlocal counter
        if old not in var_map:
            if counter < len(names):
                var_map[old] = names[counter]
            else:
                var_map[old] = f"x{counter}"
            counter += 1
        return var_map[old]

    def rename(t: Term) -> Term:
        if t.is_var():
            assert isinstance(t, Var)
            return Var(get_var_name(t.name))
        assert isinstance(t, Fun)
        return Fun(t.symbol, [rename(a) for a in t.args])

    return rename(lhs), rename(rhs)


def cp_between_two(
    r1: Tuple[Term, Term], r2: Tuple[Term, Term], idx1: int, idx2: int
) -> List[Tuple[Term, Term, str]]:
    l1, r_1 = r1
    l2, r_2 = r2
    l2_ren = rename_vars(l2, f"r{idx2}")
    r2_ren = rename_vars(r_2, f"r{idx2}")
    cps: List[Tuple[Term, Term, str]] = []

    for path, sub in l1.subterms_with_paths():
        if sub.is_var():
            continue
        if idx1 == idx2 and not path:
            continue
        sigma = mgu(sub, l2_ren)
        if sigma is not None:
            c1 = r_1.apply_subst(sigma)
            c2 = l1.apply_subst(sigma).replace_at_path(path, r2_ren.apply_subst(sigma))
            cps.append((c1, c2, f"Overlap between R{idx1} at {path} and R{idx2}"))
    return cps


def knuth_bendix_completion(
    equations: List[Tuple[Term, Term]], order: TermOrder, max_steps: int = 200
) -> Tuple[bool, Any]:
    """
    Executes agenda-based Knuth-Bendix completion loop.
    Returns (True, result_dict) on convergence, or (False, failure_dict).
    """
    E: List[Tuple[Term, Term]] = list(equations)
    R: List[Tuple[Term, Term]] = []
    joinability_certificates: List[Dict[str, Any]] = []
    step = 0

    while E and step < max_steps:
        step += 1
        # Sort equations queue: prioritize smallest combined term size
        E.sort(key=lambda eq: term_size(eq[0]) + term_size(eq[1]))
        s, t = E.pop(0)

        s_norm = normalize(s, R)
        t_norm = normalize(t, R)

        if s_norm == t_norm:
            joinability_certificates.append(
                {"equation": [s.to_json(), t.to_json()], "joined_normal_form": s_norm.to_json()}
            )
            continue

        # Orient equation into a rewrite rule
        if order.greater(s_norm, t_norm):
            new_rule = canonicalize_rule(s_norm, t_norm)
        elif order.greater(t_norm, s_norm):
            new_rule = canonicalize_rule(t_norm, s_norm)
        else:
            return False, {
                "reason": "ORDER_FAILURE",
                "unorientable_equation": [s_norm.to_json(), t_norm.to_json()],
                "step": step,
            }

        new_idx = len(R)
        # Generate critical pairs between new_rule and all current rules in R
        new_cps = []
        for i, r in enumerate(R):
            new_cps.extend(cp_between_two(new_rule, r, new_idx, i))
            new_cps.extend(cp_between_two(r, new_rule, i, new_idx))
        new_cps.extend(cp_between_two(new_rule, new_rule, new_idx, new_idx))

        for c1, c2, info in new_cps:
            E.append((c1, c2))

        # Inter-reduce existing R with new_rule
        new_R = []
        for r_old in R:
            # If left-hand side of old rule is reducible by new_rule, demote back to equations E
            if reduce_one_step(r_old[0], [new_rule]) is not None:
                E.append(r_old)
            else:
                norm_rhs = normalize(r_old[1], [new_rule] + R)
                new_R.append(canonicalize_rule(r_old[0], norm_rhs))
        new_R.append(new_rule)
        R = new_R

    if E:
        return False, {
            "reason": "MAX_STEPS_EXCEEDED",
            "steps": step,
            "remaining_equations_count": len(E),
            "current_rules_count": len(R),
        }

    return True, {
        "converged": True,
        "steps": step,
        "rules_count": len(R),
        "rules": [{"lhs": l.to_json(), "rhs": r.to_json()} for l, r in R],
        "joinability_certificates_count": len(joinability_certificates),
        "joinability_certificates": joinability_certificates[:25],
    }
