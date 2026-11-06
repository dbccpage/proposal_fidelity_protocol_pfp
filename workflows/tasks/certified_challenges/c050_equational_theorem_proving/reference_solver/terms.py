"""First-order term representation, unification/matching, and term rewriting.
Syntax conforms to C050 Prefix JSON standard.
"""

import copy
from typing import Any, Dict, List, Optional, Set, Tuple, Union

Term = Union[str, List[Any]]


def is_var(t: Term, var_set: Optional[Set[str]] = None) -> bool:
    """Determine if a term is a variable."""
    if not isinstance(t, str):
        return False
    if var_set is not None:
        return t in var_set
    # Default convention: x, y, z, u, v, w, x0, x1, etc.
    return t in {"x", "y", "z", "u", "v", "w"} or (
        len(t) >= 2 and t[0] in "xyzuvw" and t[1:].isdigit()
    )


def get_subterm(t: Term, pos: List[int]) -> Term:
    """Retrieve subterm at position pos.
    Position [] refers to root.
    Position [i] refers to the i-th argument of a compound term [f, arg0, arg1, ...].
    """
    curr = t
    for idx in pos:
        if not isinstance(curr, list) or len(curr) <= idx + 1 or idx < 0:
            raise ValueError(f"Invalid position {pos} for term {t}")
        curr = curr[idx + 1]
    return curr


def replace_subterm(t: Term, pos: List[int], repl: Term) -> Term:
    """Return a new term with the subterm at pos replaced by repl."""
    if not pos:
        return copy.deepcopy(repl)
    if not isinstance(t, list):
        raise ValueError(f"Cannot navigate into atomic term {t} with pos {pos}")
    idx = pos[0]
    if idx < 0 or idx + 1 >= len(t):
        raise ValueError(f"Invalid child index {idx} in term {t}")
    new_t = [t[0]] + list(t[1:])
    new_t[idx + 1] = replace_subterm(t[idx + 1], pos[1:], repl)
    return new_t


def get_all_positions(t: Term) -> List[List[int]]:
    """Return all valid position paths in term t."""
    positions = [[]]
    if isinstance(t, list):
        for idx in range(len(t) - 1):
            child_pos = get_all_positions(t[idx + 1])
            for cp in child_pos:
                positions.append([idx] + cp)
    return positions


def apply_subst(t: Term, subst: Dict[str, Term]) -> Term:
    """Apply substitution mapping variables to terms."""
    if isinstance(t, str):
        return copy.deepcopy(subst.get(t, t))
    return [t[0]] + [apply_subst(arg, subst) for arg in t[1:]]


def match_term(
    pattern: Term,
    target: Term,
    var_set: Optional[Set[str]] = None,
    subst: Optional[Dict[str, Term]] = None,
) -> Optional[Dict[str, Term]]:
    """Syntactic one-way pattern matching.
    Returns substitution Dict if pattern matches target, else None.
    """
    if subst is None:
        subst = {}

    if is_var(pattern, var_set):
        var_name = pattern
        if var_name in subst:
            if subst[var_name] == target:
                return subst
            return None
        subst[var_name] = copy.deepcopy(target)
        return subst

    if isinstance(pattern, str):
        if pattern == target:
            return subst
        return None

    if not isinstance(target, list) or len(pattern) != len(target) or pattern[0] != target[0]:
        return None

    for p_arg, t_arg in zip(pattern[1:], target[1:]):
        res = match_term(p_arg, t_arg, var_set, subst)
        if res is None:
            return None
    return subst


def rewrite_step(
    term: Term,
    axiom: Tuple[Term, Term],
    direction: str,
    pos: List[int],
    subst: Dict[str, Term],
    var_set: Optional[Set[str]] = None,
) -> Tuple[bool, Optional[Term], str]:
    """Execute a single equational rewrite step.
    direction: 'lr' (left-to-right) or 'rl' (right-to-left)
    """
    l, r = axiom
    src_pat, dst_pat = (l, r) if direction == "lr" else (r, l)

    try:
        subt = get_subterm(term, pos)
    except Exception as e:
        return False, None, f"Invalid position {pos}: {e}"

    # Verify that src_pat under subst equals subt
    inst_src = apply_subst(src_pat, subst)
    if inst_src != subt:
        return (
            False,
            None,
            f"Subterm at {pos} is {subt}, does not match instantiated lhs {inst_src}",
        )

    inst_dst = apply_subst(dst_pat, subst)
    new_term = replace_subterm(term, pos, inst_dst)
    return True, new_term, "Rewrite step valid"
