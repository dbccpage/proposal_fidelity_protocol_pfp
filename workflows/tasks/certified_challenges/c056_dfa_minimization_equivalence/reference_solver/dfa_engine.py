"""DFA engine: NFA compilation, subset construction, minimization, and certificate extraction."""

from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from .regex_parser import Concat, EmptySet, Epsilon, Literal, Star, Union


def build_nfa(ast) -> Tuple[int, int, List[Tuple[int, Optional[str], int]]]:
    next_state = 0

    def alloc():
        nonlocal next_state
        s = next_state
        next_state += 1
        return s

    def recurse(node):
        if isinstance(node, Epsilon):
            s, f = alloc(), alloc()
            return s, f, [(s, None, f)]
        elif isinstance(node, EmptySet):
            s, f = alloc(), alloc()
            return s, f, []
        elif isinstance(node, Literal):
            s, f = alloc(), alloc()
            return s, f, [(s, node.c, f)]
        elif isinstance(node, Concat):
            s1, f1, tr1 = recurse(node.left)
            s2, f2, tr2 = recurse(node.right)
            return s1, f2, tr1 + tr2 + [(f1, None, s2)]
        elif isinstance(node, Union):
            s, f = alloc(), alloc()
            s1, f1, tr1 = recurse(node.left)
            s2, f2, tr2 = recurse(node.right)
            tr = tr1 + tr2 + [(s, None, s1), (s, None, s2), (f1, None, f), (f2, None, f)]
            return s, f, tr
        elif isinstance(node, Star):
            s, f = alloc(), alloc()
            s1, f1, tr1 = recurse(node.child)
            tr = tr1 + [(s, None, s1), (f1, None, s1), (f1, None, f), (s, None, f)]
            return s, f, tr

    start, accept, transitions = recurse(ast)
    return start, accept, transitions


def nfa_to_dfa(
    start: int, accept: int, transitions: List[Tuple[int, Optional[str], int]], alphabet: List[str]
) -> Tuple[int, List[int], List[List[int]]]:
    adj_eps: Dict[int, List[int]] = {}
    adj_sym: Dict[Tuple[int, str], List[int]] = {}
    for u, sym, v in transitions:
        if sym is None:
            adj_eps.setdefault(u, []).append(v)
        else:
            adj_sym.setdefault((u, sym), []).append(v)

    def eps_closure(states):
        visited = set(states)
        q = deque(states)
        while q:
            u = q.popleft()
            for v in adj_eps.get(u, []):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        return frozenset(visited)

    d0 = eps_closure([start])
    dfa_states = [d0]
    state_map = {d0: 0}
    delta = []
    accept_states = set()

    q = deque([0])
    while q:
        u_idx = q.popleft()
        u_set = dfa_states[u_idx]
        if accept in u_set:
            accept_states.add(u_idx)
        row = []
        for sym in alphabet:
            target_nfa = set()
            for nfa_node in u_set:
                for v in adj_sym.get((nfa_node, sym), []):
                    target_nfa.add(v)
            target_closure = eps_closure(target_nfa)
            if target_closure not in state_map:
                new_idx = len(dfa_states)
                state_map[target_closure] = new_idx
                dfa_states.append(target_closure)
                q.append(new_idx)
            row.append(state_map[target_closure])
        delta.append(row)

    return len(dfa_states), sorted(accept_states), delta


def minimize_dfa(
    num_states: int, accept_set: List[int], delta: List[List[int]], alphabet: List[str]
) -> Dict[str, Any]:
    accept = set(accept_set)
    non_accept = set(range(num_states)) - accept

    # Moore / Hopcroft partition refinement
    P = []
    if accept:
        P.append(frozenset(accept))
    if non_accept:
        P.append(frozenset(non_accept))

    changed = True
    while changed:
        changed = False
        new_P = []
        for group in P:
            if len(group) <= 1:
                new_P.append(group)
                continue
            sig_map = {}
            for state in group:
                sig = []
                for a_idx in range(len(alphabet)):
                    dst = delta[state][a_idx]
                    for g_idx, g in enumerate(P):
                        if dst in g:
                            sig.append(g_idx)
                            break
                sig_tuple = tuple(sig)
                sig_map.setdefault(sig_tuple, []).append(state)
            if len(sig_map) > 1:
                changed = True
                for sub in sig_map.values():
                    new_P.append(frozenset(sub))
            else:
                new_P.append(group)
        P = new_P

    # Find group containing old start state 0
    start_group_idx = next(i for i, g in enumerate(P) if 0 in g)

    # Build transition table between partition groups
    group_delta = []
    for g in P:
        rep = next(iter(g))
        row = []
        for a_idx in range(len(alphabet)):
            dst = delta[rep][a_idx]
            dst_group = next(g2_idx for g2_idx, g2 in enumerate(P) if dst in g2)
            row.append(dst_group)
        group_delta.append(row)

    # Reorder reachable groups in BFS order from start_group_idx
    visited = {start_group_idx: 0}
    order = [start_group_idx]
    q = deque([start_group_idx])
    while q:
        u = q.popleft()
        for dst in group_delta[u]:
            if dst not in visited:
                visited[dst] = len(order)
                order.append(dst)
                q.append(dst)

    min_states = len(order)
    min_accept = []
    min_delta = []
    for new_id, old_g in enumerate(order):
        rep = next(iter(P[old_g]))
        if rep in accept:
            min_accept.append(new_id)
        row = [visited[group_delta[old_g][a_idx]] for a_idx in range(len(alphabet))]
        min_delta.append(row)

    # Compute access words via BFS on alphabet order
    access = [""] * min_states
    access_visited = {0}
    q_access = deque([(0, "")])
    while q_access:
        u, w = q_access.popleft()
        access[u] = w
        for a_idx, a in enumerate(alphabet):
            v = min_delta[u][a_idx]
            if v not in access_visited:
                access_visited.add(v)
                q_access.append((v, w + a))

    # Compute pairwise separating suffixes
    separators = {}
    min_accept_set = set(min_accept)
    for p in range(min_states):
        for q_state in range(p + 1, min_states):
            pq_q = deque([(p, q_state, "")])
            pq_vis = {(p, q_state)}
            found_sep = None
            while pq_q:
                u1, u2, w = pq_q.popleft()
                if (u1 in min_accept_set) != (u2 in min_accept_set):
                    found_sep = w
                    break
                for a_idx, a in enumerate(alphabet):
                    v1 = min_delta[u1][a_idx]
                    v2 = min_delta[u2][a_idx]
                    pair = (min(v1, v2), max(v1, v2))
                    if pair[0] != pair[1] and pair not in pq_vis:
                        pq_vis.add(pair)
                        pq_q.append((pair[0], pair[1], w + a))
            separators[f"{p},{q_state}"] = found_sep

    return {
        "states": min_states,
        "accept": min_accept,
        "delta": min_delta,
        "access": access,
        "separators": separators,
    }


def compile_minimal_dfa(ast, alphabet: List[str]) -> Dict[str, Any]:
    s, f, tr = build_nfa(ast)
    k, acc, d = nfa_to_dfa(s, f, tr, alphabet)
    return minimize_dfa(k, acc, d, alphabet)


def check_equivalence(
    m1: Dict[str, Any], m2: Dict[str, Any], alphabet: List[str]
) -> Dict[str, Any]:
    # Product automaton BFS to find shortest distinguishing word
    q = deque([(0, 0, "")])
    visited = {(0, 0)}
    acc1 = set(m1["accept"])
    acc2 = set(m2["accept"])
    diff_word = None

    while q:
        u1, u2, w = q.popleft()
        if (u1 in acc1) != (u2 in acc2):
            diff_word = w
            break
        for a_idx, a in enumerate(alphabet):
            v1 = m1["delta"][u1][a_idx]
            v2 = m2["delta"][u2][a_idx]
            if (v1, v2) not in visited:
                visited.add((v1, v2))
                q.append((v1, v2, w + a))

    if diff_word is not None:
        return {"kind": "DIFFERENT", "word": diff_word}

    # If equivalent, compute isomorphism bijection from DFA 1 to DFA 2
    phi = {0: 0}
    q_iso = deque([0])
    while q_iso:
        u = q_iso.popleft()
        for a_idx in range(len(alphabet)):
            v1 = m1["delta"][u][a_idx]
            v2 = m2["delta"][phi[u]][a_idx]
            if v1 not in phi:
                phi[v1] = v2
                q_iso.append(v1)
            elif phi[v1] != v2:
                # Should never happen for minimal DFAs of equivalent languages
                raise ValueError(f"Isomorphism violation: phi[{v1}]={phi[v1]} != {v2}")

    return {
        "kind": "EQUAL",
        "dfa1": {"states": m1["states"], "accept": m1["accept"], "delta": m1["delta"]},
        "dfa2": {"states": m2["states"], "accept": m2["accept"], "delta": m2["delta"]},
        "bijection": {str(k): v for k, v in sorted(phi.items())},
    }
