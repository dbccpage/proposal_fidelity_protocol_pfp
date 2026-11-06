"""Bidirectional equational theorem prover and step generator for C050."""

import collections
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from .terms import (
    Term,
    apply_subst,
    get_all_positions,
    get_subterm,
    match_term,
    replace_subterm,
)


def term_to_str(t: Term) -> str:
    """Canonical string representation for hashing."""
    return json.dumps(t, sort_keys=True)


def invert_dir(d: str) -> str:
    return "rl" if d == "lr" else "lr"


def prove_equational(
    axioms: List[Tuple[Term, Term]],
    goal: Tuple[Term, Term],
    max_depth: int = 4,
    max_nodes: int = 1500,
    var_set: Optional[Set[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Bidirectional equational proof search for ground s = t."""
    s, t = goal

    if s == t:
        return {"status": "SOLVED", "kind": "PROOF", "lemmas": [], "steps": []}

    s_str = term_to_str(s)
    t_str = term_to_str(t)

    # Queue stores: (term, path_of_steps)
    # Step format: {"axiom": idx, "dir": "lr"|"rl", "pos": p, "subst": sigma, "result": term_next}
    forward_visited = {s_str: []}
    backward_visited = {t_str: []}

    f_queue = collections.deque([(s, [])])
    b_queue = collections.deque([(t, [])])

    nodes_expanded = 0

    while (f_queue or b_queue) and nodes_expanded < max_nodes:
        # 1. Forward step
        if f_queue:
            curr, steps = f_queue.popleft()
            curr_str = term_to_str(curr)
            nodes_expanded += 1

            # Check if met backward frontier
            if curr_str in backward_visited:
                # Splice forward path + backward path reversed
                b_steps = backward_visited[curr_str]
                # Combine
                all_steps = steps + b_steps
                return {"status": "SOLVED", "kind": "PROOF", "lemmas": [], "steps": all_steps}

            if len(steps) < max_depth:
                positions = get_all_positions(curr)
                for p in positions:
                    subt = get_subterm(curr, p)
                    for ax_idx, (l, r) in enumerate(axioms):
                        for direction in ("lr", "rl"):
                            src_pat, dst_pat = (l, r) if direction == "lr" else (r, l)
                            subst = match_term(src_pat, subt, var_set)
                            if subst is not None:
                                next_subt = apply_subst(dst_pat, subst)
                                next_term = replace_subterm(curr, p, next_subt)
                                next_str = term_to_str(next_term)
                                if next_str not in forward_visited:
                                    step_rec = {
                                        "axiom": ax_idx,
                                        "dir": direction,
                                        "pos": p,
                                        "subst": subst,
                                        "result": next_term,
                                    }
                                    new_steps = steps + [step_rec]
                                    forward_visited[next_str] = new_steps
                                    f_queue.append((next_term, new_steps))

                                    if next_str in backward_visited:
                                        all_steps = new_steps + backward_visited[next_str]
                                        return {
                                            "status": "SOLVED",
                                            "kind": "PROOF",
                                            "lemmas": [],
                                            "steps": all_steps,
                                        }

        # 2. Backward step (from t)
        if b_queue:
            curr, steps = b_queue.popleft()
            curr_str = term_to_str(curr)
            nodes_expanded += 1

            if curr_str in forward_visited:
                f_steps = forward_visited[curr_str]
                all_steps = f_steps + steps
                return {"status": "SOLVED", "kind": "PROOF", "lemmas": [], "steps": all_steps}

            if len(steps) < max_depth:
                positions = get_all_positions(curr)
                for p in positions:
                    subt = get_subterm(curr, p)
                    for ax_idx, (l, r) in enumerate(axioms):
                        for direction in ("lr", "rl"):
                            src_pat, dst_pat = (l, r) if direction == "lr" else (r, l)
                            subst = match_term(src_pat, subt, var_set)
                            if subst is not None:
                                next_subt = apply_subst(dst_pat, subst)
                                prev_term = replace_subterm(curr, p, next_subt)
                                prev_str = term_to_str(prev_term)
                                if prev_str not in backward_visited:
                                    # When stepping backward, moving from prev_term to curr requires inverting direction
                                    inv_direction = invert_dir(direction)
                                    step_rec = {
                                        "axiom": ax_idx,
                                        "dir": inv_direction,
                                        "pos": p,
                                        "subst": subst,
                                        "result": curr,
                                    }
                                    # In backward path, this step goes from prev_term to curr, then followed by remaining steps to t
                                    new_steps = [step_rec] + steps
                                    backward_visited[prev_str] = new_steps
                                    b_queue.append((prev_term, new_steps))

                                    if prev_str in forward_visited:
                                        all_steps = forward_visited[prev_str] + new_steps
                                        return {
                                            "status": "SOLVED",
                                            "kind": "PROOF",
                                            "lemmas": [],
                                            "steps": all_steps,
                                        }

    return None
