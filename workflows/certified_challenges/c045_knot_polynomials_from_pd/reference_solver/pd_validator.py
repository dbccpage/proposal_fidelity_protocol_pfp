# AuthorityEffect: None.
"""
Planar Diagram (PD) Code Validator and Geometric Parser for C045.
Verifies label multiplicity, single-component knot property, rotation system planarity,
crossing signs, and total writhe.
"""

from typing import Any, Dict, List, Tuple


def validate_and_parse_pd(pd: List[List[int]]) -> Tuple[bool, Any]:
    n = len(pd)
    if n == 0 or n > 14:
        return False, {"reason": "INVALID_CROSSING_COUNT", "crossings": n}

    # 1. Edge label multiplicity
    counts: Dict[int, int] = {}
    for c in pd:
        if len(c) != 4:
            return False, {"reason": "MALFORMED_CROSSING_TUPLE", "tuple": c}
        for e in c:
            counts[e] = counts.get(e, 0) + 1

    for e, cnt in counts.items():
        if cnt != 2:
            return False, {"reason": "EDGE_LABEL_MULTIPLICITY", "label": e, "count": cnt}

    expected_labels = set(range(1, 2 * n + 1))
    if set(counts.keys()) != expected_labels:
        missing = expected_labels - set(counts.keys())
        extra = set(counts.keys()) - expected_labels
        return False, {
            "reason": "EDGE_LABEL_MULTIPLICITY",
            "label": next(iter(missing or extra)),
            "count": 0,
        }

    # 2. Components check (knot vs link)
    # Successor along knot orientation: 1 -> 2 -> ... -> 2n -> 1
    succ = {e: (e % (2 * n)) + 1 for e in range(1, 2 * n + 1)}
    visited = set()
    curr = 1
    comp = []
    while curr not in visited:
        visited.add(curr)
        comp.append(curr)
        curr = succ[curr]

    if len(comp) != 2 * n:
        return False, {"reason": "TWO_COMPONENTS", "component_edges": [comp]}

    # 3. Planarity via combinatorial rotation system
    # Darts: (crossing_idx, pos 0..3)
    edge_map: Dict[int, List[Tuple[int, int]]] = {}
    for c_idx, cross in enumerate(pd):
        for pos, e in enumerate(cross):
            edge_map.setdefault(e, []).append((c_idx, pos))

    alpha: Dict[Tuple[int, int], Tuple[int, int]] = {}
    for e, darts in edge_map.items():
        if len(darts) != 2:
            return False, {"reason": "EDGE_LABEL_MULTIPLICITY", "label": e, "count": len(darts)}
        d1, d2 = darts[0], darts[1]
        alpha[d1] = d2
        alpha[d2] = d1

    visited_darts = set()
    face_count = 0
    all_darts = list(alpha.keys())
    for d in all_darts:
        if d not in visited_darts:
            face_count += 1
            curr_d = d
            while curr_d not in visited_darts:
                visited_darts.add(curr_d)
                opp = alpha[curr_d]
                curr_d = (opp[0], (opp[1] + 1) % 4)

    if face_count != n + 2:
        return False, {"reason": "NON_PLANAR", "faces": face_count, "expected": n + 2}

    # 4. Orientation consistency and crossing signs
    # PD convention X[i, j, k, l]:
    # i is incoming under-strand (i -> k).
    # j, l are over-strand edges. One is incoming, one is outgoing.
    # Check that understrand satisfies k = succ(i)
    n2 = 2 * n
    signs = []
    a_smoothings = []

    for c_idx, (i, j, k, l) in enumerate(pd):
        if (i % n2) + 1 != k:
            return False, {
                "reason": "ORIENTATION_INCONSISTENT",
                "crossing_index": c_idx,
                "understrand": [i, k],
            }

        # Overstrand: either l -> j (positive crossing) or j -> l (negative crossing)
        succ_l = (l % n2) + 1
        succ_j = (j % n2) + 1

        if succ_l == j:
            # Overstrand goes l -> j: right-handed positive crossing
            sign = 1
            a_pairs = ((i, l), (j, k))
            b_pairs = ((i, j), (k, l))
        elif succ_j == l:
            # Overstrand goes j -> l: left-handed negative crossing
            sign = -1
            a_pairs = ((i, j), (k, l))
            b_pairs = ((i, l), (j, k))
        else:
            return False, {
                "reason": "ORIENTATION_INCONSISTENT",
                "crossing_index": c_idx,
                "overstrand": [j, l],
            }

        signs.append(sign)
        a_smoothings.append((a_pairs, b_pairs))

    writhe = sum(signs)
    return True, {
        "writhe": writhe,
        "signs": signs,
        "a_smoothings": a_smoothings,
        "crossings_count": n,
    }
