"""Finite countermodel evaluator and finder for C050 equational non-theorems.
Domain D is {0, 1, ..., size-1}.
"""

import itertools
from typing import Any, Dict, List, Optional, Set, Tuple

from .terms import Term, is_var


def extract_vars(t: Term, var_set: Optional[Set[str]] = None) -> Set[str]:
    """Collect all variables in term t."""
    res = set()
    if is_var(t, var_set):
        res.add(t)
    elif isinstance(t, list):
        for arg in t[1:]:
            res.update(extract_vars(arg, var_set))
    return res


def extract_constants(t: Term, var_set: Optional[Set[str]] = None) -> Set[str]:
    """Collect all constants in ground term t."""
    res = set()
    if isinstance(t, str) and not is_var(t, var_set):
        res.add(t)
    elif isinstance(t, list):
        for arg in t[1:]:
            res.update(extract_constants(arg, var_set))
    return res


def eval_term(t: Term, env: Dict[str, int], tables: Dict[str, Any]) -> int:
    """Evaluate term t in finite algebra with given variable environment and function tables."""
    if isinstance(t, str):
        val = env.get(t, 0)
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    f = t[0]
    if f not in tables:
        raise ValueError(f"Function symbol '{f}' missing from operation tables")

    table = tables[f]
    args = [eval_term(arg, env, tables) for arg in t[1:]]

    try:
        if len(args) == 1:
            return int(table[int(args[0])])
        elif len(args) == 2:
            return int(table[int(args[0])][int(args[1])])
        else:
            curr = table
            for a in args:
                curr = curr[int(a)]
            return int(curr)
    except (IndexError, TypeError, ValueError) as e:
        raise ValueError(f"Table lookup failed for {f}: {e}")


def check_countermodel(
    axioms: List[Tuple[Term, Term]],
    goal: Tuple[Term, Term],
    size: int,
    tables: Dict[str, Any],
    assignment: Dict[str, int],
    var_set: Optional[Set[str]] = None,
) -> Tuple[bool, str]:
    """Validate that (size, tables, assignment) forms a valid countermodel.
    1. Every axiom holds for ALL assignments of its variables in {0..size-1}.
    2. Goal fails under given assignment.
    """
    try:
        size = int(size)
    except (ValueError, TypeError):
        return False, "Size must be an integer"

    if not (1 <= size <= 8):
        return False, f"Invalid domain size {size}: must be between 1 and 8"

    if not isinstance(tables, dict):
        return False, "Tables must be a dictionary"
    if not isinstance(assignment, dict):
        return False, "Assignment must be a dictionary"

    clean_assignment = {}
    for k, v in assignment.items():
        try:
            clean_assignment[str(k)] = int(v)
        except (ValueError, TypeError):
            return False, f"Assignment for '{k}' must be an integer"

    clean_tables = {}
    for f, table in tables.items():
        if not isinstance(table, list):
            return False, f"Table for {f} must be a list"
        try:
            if table and isinstance(table[0], list):
                clean_tables[f] = [[int(cell) for cell in row] for row in table]
            else:
                clean_tables[f] = [int(cell) for cell in table]
        except (ValueError, TypeError, IndexError):
            return False, f"Table entries for {f} must be integers"

    try:
        # 1. Verify all axioms hold universally
        for ax_idx, (l, r) in enumerate(axioms):
            vars_ax = sorted(list(extract_vars(l, var_set).union(extract_vars(r, var_set))))
            if not vars_ax:
                v_l = eval_term(l, clean_assignment, clean_tables)
                v_r = eval_term(r, clean_assignment, clean_tables)
                if v_l != v_r:
                    return False, f"Axiom {ax_idx} violated: {l} ({v_l}) != {r} ({v_r})"
            else:
                for assignment_vals in itertools.product(range(size), repeat=len(vars_ax)):
                    env = {**clean_assignment, **dict(zip(vars_ax, assignment_vals))}
                    v_l = eval_term(l, env, clean_tables)
                    v_r = eval_term(r, env, clean_tables)
                    if v_l != v_r:
                        return (
                            False,
                            f"Axiom {ax_idx} violated under {env}: {l} ({v_l}) != {r} ({v_r})",
                        )

        # 2. Verify goal fails under given assignment
        s, t = goal
        all_consts_set = set()
        for l, r in axioms:
            all_consts_set.update(extract_constants(l, var_set))
            all_consts_set.update(extract_constants(r, var_set))
        all_consts_set.update(extract_constants(s, var_set))
        all_consts_set.update(extract_constants(t, var_set))
        for c in all_consts_set:
            if c not in clean_assignment:
                return False, f"Constant '{c}' missing from witness assignment"
            if not (0 <= clean_assignment[c] < size):
                return (
                    False,
                    f"Assignment value for '{c}' ({clean_assignment[c]}) out of domain bounds [0, {size - 1}]",
                )

        val_s = eval_term(s, clean_assignment, clean_tables)
        val_t = eval_term(t, clean_assignment, clean_tables)

        if val_s == val_t:
            return False, f"Goal holds in candidate countermodel: s ({val_s}) == t ({val_t})"

        return True, f"Valid countermodel of size {size}: s ({val_s}) != t ({val_t})"
    except Exception as e:
        return False, f"Countermodel verification error: {e}"


def find_countermodel(
    axioms: List[Tuple[Term, Term]],
    goal: Tuple[Term, Term],
    max_size: int = 3,
    var_set: Optional[Set[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Brute-force search for small finite countermodel."""
    # Collect symbols
    func_arities = {}

    def collect_funcs(t: Term):
        if isinstance(t, list):
            f = t[0]
            ar = len(t) - 1
            func_arities[f] = ar
            for arg in t[1:]:
                collect_funcs(arg)

    for l, r in axioms:
        collect_funcs(l)
        collect_funcs(r)
    collect_funcs(goal[0])
    collect_funcs(goal[1])

    s, t = goal
    all_consts_set = set()
    for l, r in axioms:
        all_consts_set.update(extract_constants(l, var_set))
        all_consts_set.update(extract_constants(r, var_set))
    all_consts_set.update(extract_constants(s, var_set))
    all_consts_set.update(extract_constants(t, var_set))
    all_consts = sorted(list(all_consts_set))

    for size in range(2, max_size + 1):
        # Generate candidate tables for each function symbol
        fn_candidates = {}
        for fname, arity in func_arities.items():
            if arity == 1:
                tables_for_f = [
                    list(t_flat) for t_flat in itertools.product(range(size), repeat=size)
                ]
                fn_candidates[fname] = tables_for_f
            elif arity == 2:
                tables_for_f = [
                    [list(t_flat[i * size : (i + 1) * size]) for i in range(size)]
                    for t_flat in itertools.product(range(size), repeat=size * size)
                ]
                fn_candidates[fname] = tables_for_f
            else:
                fn_candidates[fname] = []

        if any(len(cands) == 0 for cands in fn_candidates.values()):
            continue

        fnames = list(fn_candidates.keys())
        all_table_combos = itertools.product(*[fn_candidates[fn] for fn in fnames])

        for combo in all_table_combos:
            tables = {fn: tbl for fn, tbl in zip(fnames, combo)}
            for c_vals in itertools.product(range(size), repeat=len(all_consts)):
                assignment = dict(zip(all_consts, c_vals))
                axioms_hold = True
                for ax_l, ax_r in axioms:
                    vrs = sorted(
                        list(extract_vars(ax_l, var_set).union(extract_vars(ax_r, var_set)))
                    )
                    for a_vals in itertools.product(range(size), repeat=len(vrs)):
                        env = {**assignment, **dict(zip(vrs, a_vals))}
                        if eval_term(ax_l, env, tables) != eval_term(ax_r, env, tables):
                            axioms_hold = False
                            break
                    if not axioms_hold:
                        break
                if axioms_hold:
                    if eval_term(s, assignment, tables) != eval_term(t, assignment, tables):
                        return {
                            "status": "SOLVED",
                            "kind": "COUNTERMODEL",
                            "size": size,
                            "tables": tables,
                            "assignment": assignment,
                        }
    return None
