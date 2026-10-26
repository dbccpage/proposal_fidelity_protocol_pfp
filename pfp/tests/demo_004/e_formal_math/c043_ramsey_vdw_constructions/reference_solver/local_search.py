"""
Local search and automorphism relabelling algorithms for Ramsey and Van der Waerden constraints.
Pure Python standard library implementation.
"""

from itertools import combinations
from typing import Dict, List, Optional, Tuple

from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.reference_solver.algebraic_seeds import (
    QR_17,
    edge_index,
    pentagon_5_colouring,
    vdw_seed_w23,
    vdw_seed_w24,
)


def has_monochromatic_clique(
    colours: str, n: int, s: int, target_colour: str
) -> Optional[List[int]]:
    """
    Check if the colouring contains a monochromatic K_s in target_colour.
    Returns the vertex subset if found, else None.
    """
    for clique in combinations(range(n), s):
        is_mono = True
        for u, v in combinations(clique, 2):
            idx = edge_index(u, v, n)
            if colours[idx] != target_colour:
                is_mono = False
                break
        if is_mono:
            return list(clique)
    return None


def count_monochromatic_cliques(colours: str, n: int, s: int, t: int) -> int:
    """Count forbidden monochromatic cliques: K_s in colour '0' + K_t in colour '1'."""
    count = 0
    for clique in combinations(range(n), s):
        if all(colours[edge_index(u, v, n)] == "0" for u, v in combinations(clique, 2)):
            count += 1
    for clique in combinations(range(n), t):
        if all(colours[edge_index(u, v, n)] == "1" for u, v in combinations(clique, 2)):
            count += 1
    return count


def has_monochromatic_ap(seq: str, k: int) -> Optional[Tuple[int, int]]:
    """
    Check if seq contains a monochromatic k-term AP.
    Returns (start_idx, step_d) if found, else None.
    """
    n = len(seq)
    for a in range(n):
        for d in range(1, (n - 1 - a) // (k - 1) + 1):
            target = seq[a]
            if all(seq[a + i * d] == target for i in range(1, k)):
                return (a, d)
    return None


def count_monochromatic_aps(seq: str, k: int) -> int:
    """Count the total number of monochromatic k-term APs in seq."""
    n = len(seq)
    count = 0
    for a in range(n):
        for d in range(1, (n - 1 - a) // (k - 1) + 1):
            target = seq[a]
            if all(seq[a + i * d] == target for i in range(1, k)):
                count += 1
    return count


def parse_fixed_edges(fixed: list, n: int) -> Dict[int, str]:
    """Parse fixed edges from input list into {edge_idx: colour_str}."""
    res = {}
    for item in fixed:
        if len(item) == 3:
            u, v, c = item
            idx = edge_index(u, v, n)
            res[idx] = str(c)
        elif len(item) == 2:
            idx, c = item
            res[int(idx)] = str(c)
    return res


def parse_fixed_elements(fixed: list) -> Dict[int, str]:
    """Parse fixed elements for vdW into {pos: colour_str}."""
    res = {}
    for item in fixed:
        pos, c = item
        res[int(pos)] = str(c)
    return res


def solve_ramsey2_paley(n: int, s: int, t: int, fixed_dict: Dict[int, str]) -> Optional[str]:
    """
    Attempt to find an automorphism of Paley 17 or Pentagon 5 that satisfies fixed_dict.
    """
    if s == 3 and t == 3 and n <= 5:
        # Check permutations of Pentagon 5
        base_colours = list(pentagon_5_colouring(5))
        # Automorphisms of C5: dihedral group D5 (10 elements)
        # We can also check all 5! = 120 permutations since 5! is tiny
        for p in combinations(range(5), n):
            # p is a subset of 5 vertices
            for perm in [[0, 1, 2, 3, 4]]:  # simplified
                cand = []
                for u in range(n):
                    for v in range(u + 1, n):
                        idx = edge_index(u, v, n)
                        cand.append(base_colours[idx])
                cand_str = "".join(cand)
                # check fixed
                if all(cand_str[idx] == col for idx, col in fixed_dict.items()):
                    if count_monochromatic_cliques(cand_str, n, s, t) == 0:
                        return cand_str

    if s == 4 and t == 4 and n <= 17:
        # Paley graph affine automorphisms: x -> (a*x + b) % 17
        for a in QR_17:
            for b in range(17):
                perm = [(a * x + b) % 17 for x in range(17)]
                cand = []
                for u in range(n):
                    for v in range(u + 1, n):
                        pu, pv = perm[u], perm[v]
                        diff = abs(pu - pv) % 17
                        cand.append("1" if diff in QR_17 else "0")
                cand_str = "".join(cand)
                if all(cand_str[idx] == col for idx, col in fixed_dict.items()):
                    return cand_str

        # Color complementation automorphisms: multiply by non-residue 3
        non_res = 3
        for a in QR_17:
            for b in range(17):
                perm = [(a * non_res * x + b) % 17 for x in range(17)]
                cand = []
                for u in range(n):
                    for v in range(u + 1, n):
                        pu, pv = perm[u], perm[v]
                        diff = abs(pu - pv) % 17
                        cand.append("1" if diff in QR_17 else "0")
                cand_str = "".join(cand)
                if all(cand_str[idx] == col for idx, col in fixed_dict.items()):
                    return cand_str

        # If affine automorphisms do not match fixed_dict, use general Paley embedding DFS
        cand_embed = embed_paley_17(n, fixed_dict)
        if cand_embed is not None:
            return cand_embed

    if s == 3 and t == 4 and n <= 8:
        from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.reference_solver.algebraic_seeds import (
            ramsey_seed_r34,
        )

        base_colours = ramsey_seed_r34(n)
        if all(base_colours[idx] == col for idx, col in fixed_dict.items()):
            if count_monochromatic_cliques(base_colours, n, s, t) == 0:
                return base_colours

    return None


def embed_paley_17(n: int, fixed_dict: Dict[int, str]) -> Optional[str]:
    """Embed vertices of K_n into Paley 17 to satisfy fixed edge constraints."""
    from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.reference_solver.algebraic_seeds import (
        index_to_edge,
    )

    fixed_pairs = {}
    for idx, col in fixed_dict.items():
        u, v = index_to_edge(idx, n)
        fixed_pairs[(u, v)] = int(col)

    assigned = [-1] * n
    used = set()

    def dfs(u):
        if u == n:
            return True
        for val in range(17):
            if val in used:
                continue
            valid = True
            for prev in range(u):
                pair = (prev, u)
                if pair in fixed_pairs:
                    diff = abs(assigned[prev] - val) % 17
                    col = 1 if diff in QR_17 else 0
                    if col != fixed_pairs[pair]:
                        valid = False
                        break
            if valid:
                assigned[u] = val
                used.add(val)
                if dfs(u + 1):
                    return True
                used.remove(val)
                assigned[u] = -1
        return False

    if dfs(0):
        res = []
        for i in range(n):
            for j in range(i + 1, n):
                diff = abs(assigned[i] - assigned[j]) % 17
                res.append("1" if diff in QR_17 else "0")
        return "".join(res)
    return None


def embed_greenwood_gleason_16(n: int, fixed_dict: Dict[int, str]) -> Optional[str]:
    """Embed vertices of K_n into Greenwood-Gleason 16 to satisfy fixed edge constraints."""
    from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.reference_solver.algebraic_seeds import (
        GF16_C0,
        GF16_C1,
        GF16_C2,
        index_to_edge,
    )

    fixed_pairs = {}
    for idx, col in fixed_dict.items():
        u, v = index_to_edge(idx, n)
        fixed_pairs[(u, v)] = int(col)

    assigned = [-1] * n
    used = set()

    def dfs(u):
        if u == n:
            return True
        for val in range(16):
            if val in used:
                continue
            valid = True
            for prev in range(u):
                pair = (prev, u)
                if pair in fixed_pairs:
                    diff = assigned[prev] ^ val
                    if diff in GF16_C0:
                        c = 0
                    elif diff in GF16_C1:
                        c = 1
                    elif diff in GF16_C2:
                        c = 2
                    else:
                        c = -1
                    if c != fixed_pairs[pair]:
                        valid = False
                        break
            if valid:
                assigned[u] = val
                used.add(val)
                if dfs(u + 1):
                    return True
                used.remove(val)
                assigned[u] = -1
        return False

    if dfs(0):
        res = []
        for i in range(n):
            for j in range(i + 1, n):
                diff = assigned[i] ^ assigned[j]
                if diff in GF16_C0:
                    res.append("0")
                elif diff in GF16_C1:
                    res.append("1")
                else:
                    res.append("2")
        return "".join(res)
    return None


def solve_vdw_local_search(
    r: int, k: int, n: int, fixed_dict: Dict[int, str], max_flips: int = 500
) -> Optional[str]:
    """
    Solve Van der Waerden constraints via seed initialization, symmetry transforms, and min-conflicts AP repair.
    """
    import random

    from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.reference_solver.algebraic_seeds import (
        vdw_seed_w25,
        vdw_seed_w33,
    )

    # Start with algebraic seed if available
    base_str: Optional[str] = None
    if k == 3 and r == 2 and n <= 8:
        base_str = vdw_seed_w23(n)
    elif k == 4 and r == 2 and n <= 34:
        base_str = vdw_seed_w24(n)
    elif k == 5 and r == 2 and n <= 80:
        base_str = vdw_seed_w25(n)
    elif k == 3 and r == 3 and n <= 26:
        base_str = vdw_seed_w33(n)

    if base_str is not None:
        # Test original, reflection, and colour inversions
        candidates = [base_str, base_str[::-1]]
        if r == 2:
            inv = "".join("1" if c == "0" else "0" for c in base_str)
            candidates.extend([inv, inv[::-1]])

        for cand in candidates:
            if all(cand[pos] == col for pos, col in fixed_dict.items() if pos < n):
                if has_monochromatic_ap(cand, k) is None:
                    return cand

        base = list(base_str)
    else:
        base = [str(random.randint(0, r - 1)) for _ in range(n)]

    # Impose fixed constraints
    for pos, c in fixed_dict.items():
        if pos < n:
            base[pos] = c

    # If already free of APs, return
    s = "".join(base)
    if has_monochromatic_ap(s, k) is None:
        return s

    # Min-conflicts repair
    mutable_positions = [i for i in range(n) if i not in fixed_dict]
    if not mutable_positions:
        return None

    cur = list(base)
    for step in range(max_flips):
        ap = has_monochromatic_ap("".join(cur), k)
        if ap is None:
            return "".join(cur)
        a, d = ap
        bad_indices = [a + i * d for i in range(k) if (a + i * d) in mutable_positions]
        if not bad_indices:
            # All indices in the AP are fixed, impossible to satisfy!
            return None
        # Pick one bad index and flip to best colour
        pick = random.choice(bad_indices)
        best_col = cur[pick]
        min_v = 10**9
        for c in range(r):
            c_str = str(c)
            cur[pick] = c_str
            v_cnt = count_monochromatic_aps("".join(cur), k)
            if v_cnt < min_v:
                min_v = v_cnt
                best_col = c_str
        cur[pick] = best_col

    return None
