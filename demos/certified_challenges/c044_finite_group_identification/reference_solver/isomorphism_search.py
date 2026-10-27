# AuthorityEffect: None.
"""
Isomorphism Search and Verification for C044.
Finds and verifies generator images extending to a bijective homomorphism between groups
using structured basis backtracking.
"""

from typing import Dict, List, Optional, Tuple


def get_element_order(table: List[List[int]], x: int) -> int:
    curr = x
    ord_val = 1
    while curr != 0:
        curr = table[curr][x]
        ord_val += 1
    return ord_val


def extend_and_verify_isomorphism(
    t_g: List[List[int]], gens_g: List[int], t_h: List[List[int]], chosen_h: List[int]
) -> Tuple[bool, Optional[Dict[int, int]]]:
    n = len(t_g)
    if len(t_h) != n:
        return False, None

    phi = {0: 0}
    q = [0]
    while q:
        curr = q.pop(0)
        for g_i, h_i in zip(gens_g, chosen_h):
            nxt = t_g[curr][g_i]
            mapped = t_h[phi[curr]][h_i]
            if nxt in phi:
                if phi[nxt] != mapped:
                    return False, None
            else:
                phi[nxt] = mapped
                q.append(nxt)

    if len(phi) != n or len(set(phi.values())) != n:
        return False, None

    for x in range(n):
        for y in range(n):
            if phi[t_g[x][y]] != t_h[phi[x]][phi[y]]:
                return False, None

    return True, phi


def find_isomorphism(
    t_g: List[List[int]], gens_g: List[int], t_h: List[List[int]], max_steps: int = 10000
) -> Tuple[bool, Optional[List[int]], Optional[Dict[int, int]]]:
    n = len(t_g)
    if len(t_h) != n:
        return False, None, None

    gen_orders = [get_element_order(t_g, g) for g in gens_g]
    steps = [0]

    def backtrack(
        idx: int, chosen_h: List[int], generated_h: set
    ) -> Optional[Tuple[List[int], Dict[int, int]]]:
        if idx == len(gens_g):
            ok, phi = extend_and_verify_isomorphism(t_g, gens_g, t_h, chosen_h)
            if ok and phi is not None:
                return chosen_h, phi
            return None

        target_ord = gen_orders[idx]
        for h in range(n):
            steps[0] += 1
            if steps[0] > max_steps:
                return None

            if get_element_order(t_h, h) == target_ord:
                # If generator idx was independent of previous generators in G, h must be independent in H
                if len(gens_g) > 1 and h in generated_h:
                    continue

                new_gen = set(generated_h)
                q = [h]
                new_gen.add(h)
                while q:
                    curr = q.pop(0)
                    for h_prev in chosen_h + [h]:
                        nxt1 = t_h[curr][h_prev]
                        if nxt1 not in new_gen:
                            new_gen.add(nxt1)
                            q.append(nxt1)
                        nxt2 = t_h[h_prev][curr]
                        if nxt2 not in new_gen:
                            new_gen.add(nxt2)
                            q.append(nxt2)

                res = backtrack(idx + 1, chosen_h + [h], new_gen)
                if res is not None:
                    return res

        return None

    res = backtrack(0, [], {0})
    if res is not None:
        images, phi = res
        return True, images, phi

    return False, None, None
