"""Independent Persistent Homology Checker (Checker 2) for C015.

Independent reference implementation of matrix reduction and barcode extraction.
Independently parses simplicial complex, verifies face ordering, performs column reduction,
and compares index pairs, essential classes, and value barcode.
"""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import Any


def check_independent_persistence(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a dict"

    status = result.get("status")
    simplices = case.get("simplices", [])
    if not isinstance(simplices, list):
        return False, "simplices missing from case"

    # Check for face ordering violations independently
    seen_verts: set[tuple[int, ...]] = set()
    first_missing_face: tuple[int, ...] | None = None

    for idx, s in enumerate(simplices):
        verts = tuple(sorted(int(v) for v in s["vertices"]))
        dim = int(s["dim"])
        if dim > 0:
            for f in itertools.combinations(verts, dim):
                if f not in seen_verts and first_missing_face is None:
                    first_missing_face = f
                    break
        seen_verts.add(verts)

    if first_missing_face is not None:
        if status != "OUT_OF_SCOPE":
            return (
                False,
                f"Expected OUT_OF_SCOPE due to missing face {first_missing_face}, got {status}",
            )
        return True, "Independent checker confirms OUT_OF_SCOPE"

    if status != "SOLVED":
        return False, f"Expected SOLVED, got {status}"

    # Independent matrix reduction
    n = len(simplices)
    vert_to_idx = {tuple(sorted(int(v) for v in s["vertices"])): i for i, s in enumerate(simplices)}
    D: list[set[int]] = []
    for s in simplices:
        dim = int(s["dim"])
        verts = tuple(sorted(int(v) for v in s["vertices"]))
        col = set()
        if dim > 0:
            for f in itertools.combinations(verts, dim):
                col.add(vert_to_idx[f])
        D.append(col)

    # Reduction
    R = [set(col) for col in D]
    low_to_col: dict[int, int] = {}
    low_map: dict[int, int] = {}

    for j in range(n):
        while R[j]:
            low_j = max(R[j])
            if low_j in low_to_col:
                k = low_to_col[low_j]
                R[j] ^= R[k]
            else:
                low_to_col[low_j] = j
                low_map[j] = low_j
                break

    # Independent extraction of pairs and essential
    ind_pairs = {(low_map[j], j) for j in low_map}
    paired_births = set(low_map.values())
    ind_essential = {i for i in range(n) if i not in paired_births and not R[i]}

    # Check participant pairs
    res_pairs = set()
    for p in result.get("pairs", []):
        res_pairs.add((int(p[0]), int(p[1])))

    if res_pairs != ind_pairs:
        return False, f"Independent pairs mismatch: expected {len(ind_pairs)}, got {len(res_pairs)}"

    # Check participant essential
    res_essential = {int(e) for e in result.get("essential", [])}
    if res_essential != ind_essential:
        return (
            False,
            f"Independent essential mismatch: expected {ind_essential}, got {res_essential}",
        )

    # Check barcode values
    res_barcode = result.get("barcode", {})
    for deg in range(4):
        deg_str = str(deg)
        expected_bars: list[list[str]] = []
        for b, d in ind_pairs:
            if int(simplices[b]["dim"]) == deg:
                vb = Fraction(str(simplices[b]["val"]))
                vd = Fraction(str(simplices[d]["val"]))
                if vb != vd:
                    expected_bars.append([str(vb), str(vd)])
        for e in ind_essential:
            if int(simplices[e]["dim"]) == deg:
                ve = Fraction(str(simplices[e]["val"]))
                expected_bars.append([str(ve), "inf"])

        def bar_key(interval: list[str]) -> tuple[Fraction, Fraction]:
            start = Fraction(interval[0])
            end = Fraction(10**9, 1) if interval[1] == "inf" else Fraction(interval[1])
            return (start, end)

        expected_bars.sort(key=bar_key)

        actual_bars = []
        for b in res_barcode.get(deg_str, []):
            actual_bars.append([str(b[0]), str(b[1])])
        actual_bars.sort(key=bar_key)

        if actual_bars != expected_bars:
            return (
                False,
                f"Independent barcode mismatch in degree {deg}: expected {expected_bars}, got {actual_bars}",
            )

    return True, "Independent persistent homology check passed"
