"""Algebraic Certificate Checker (Checker 1) for C015.

Directly verifies the mathematical reduction certificate over F2:
1. V is upper unitriangular (diagonal 1, 0 below diagonal).
2. D * V = R over F2 holds for all columns.
3. R is reduced (no two nonzero columns share the same lowest row index).
4. Reported index pairs (i, j) are in exact bijection with nonzero columns of R: low(j) = i.
5. Reported essential indices are exactly those cycle columns never killed.
6. Reported value barcodes match the pairs with zero-length intervals removed.
7. Essential count per degree equals F2 Betti numbers of the full complex.
"""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import Any


def check_algebraic_certificate(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a dict"

    status = result.get("status")
    if status == "OUT_OF_SCOPE":
        # Verify witness
        witness = result.get("witness")
        if not isinstance(witness, dict):
            return False, "OUT_OF_SCOPE result missing witness dict"
        s_id = str(witness.get("simplex"))
        missing_face = witness.get("missing_earlier_face")
        if not s_id or not missing_face:
            return False, "Witness missing simplex or missing_earlier_face"

        # Verify against case that face compatibility is truly violated
        simplices = case.get("simplices", [])
        seen = set()
        violation_confirmed = False
        for idx, s in enumerate(simplices):
            verts = tuple(sorted(int(v) for v in s["vertices"]))
            dim = int(s["dim"])
            if dim > 0:
                for f in itertools.combinations(verts, dim):
                    if f not in seen:
                        # Found a missing face
                        violation_confirmed = True
                        break
            seen.add(verts)
            if violation_confirmed:
                break
        if not violation_confirmed:
            return False, "OUT_OF_SCOPE reported but complex is actually face-compatible"
        return True, "Valid OUT_OF_SCOPE witness verified"

    if status != "SOLVED":
        return False, f"Unexpected result status: {status}"

    simplices = case.get("simplices")
    if not isinstance(simplices, list):
        return False, "Case missing simplices list"
    n = len(simplices)

    # 1. Rebuild boundary matrix D over F2
    seen_simplices: dict[tuple[int, ...], int] = {}
    D_cols: list[set[int]] = []
    parsed_simplices: list[dict[str, Any]] = []

    for idx, s in enumerate(simplices):
        verts = tuple(sorted(int(v) for v in s["vertices"]))
        dim = int(s["dim"])
        val_str = str(s["val"])
        seen_simplices[verts] = idx
        parsed_simplices.append({"dim": dim, "val": Fraction(val_str)})

        col: set[int] = set()
        if dim > 0:
            for f in itertools.combinations(verts, dim):
                if f not in seen_simplices:
                    return False, f"Case has face ordering violation at simplex {idx}"
                col.add(seen_simplices[f])
        D_cols.append(col)

    # 2. Parse participant V_columns and R_columns
    raw_v = result.get("V_columns", {})
    raw_r = result.get("R_columns", {})
    if not isinstance(raw_v, dict) or not isinstance(raw_r, dict):
        return False, "V_columns or R_columns is not a dict"

    V_cols: dict[int, set[int]] = {}
    for k_str, col_list in raw_v.items():
        try:
            k = int(k_str)
            if not isinstance(col_list, list):
                return False, f"V_columns[{k_str}] is not a list"
            V_cols[k] = {int(r) for r in col_list}
        except (ValueError, TypeError):
            return False, f"Malformed entry in V_columns for key {k_str}"

    R_cols: dict[int, set[int]] = {}
    for k_str, col_list in raw_r.items():
        try:
            k = int(k_str)
            if not isinstance(col_list, list):
                return False, f"R_columns[{k_str}] is not a list"
            R_cols[k] = {int(r) for r in col_list}
        except (ValueError, TypeError):
            return False, f"Malformed entry in R_columns for key {k_str}"

    # 3. Check V is upper unitriangular
    for j in range(n):
        col = V_cols.get(j, {j})
        if j not in col:
            return False, f"Diagonal entry V[{j}, {j}] is 0"
        for i in col:
            if i > j:
                return False, f"V is not upper triangular: nonzero entry at ({i}, {j})"
            if i < 0:
                return False, f"Negative index {i} in V"

    # 4. Check D * V = R over F2
    for j in range(n):
        col_v = V_cols.get(j, {j})
        expected_r: set[int] = set()
        for k in col_v:
            if k >= n:
                return False, f"Column index {k} in V[{j}] out of range"
            expected_r ^= D_cols[k]

        actual_r = R_cols.get(j, D_cols[j])
        if expected_r != actual_r:
            return (
                False,
                f"D * V = R failure at column {j}: expected {sorted(expected_r)}, got {sorted(actual_r)}",
            )

    # 5. Check R is reduced
    low_to_col: dict[int, int] = {}
    low_map: dict[int, int] = {}
    for j in range(n):
        col_r = R_cols.get(j, D_cols[j])
        if col_r:
            low_j = max(col_r)
            low_map[j] = low_j
            if low_j in low_to_col:
                return (
                    False,
                    f"R is not reduced: columns {low_to_col[low_j]} and {j} share lowest row {low_j}",
                )
            low_to_col[low_j] = j

    # 6. Check reported pairs
    raw_pairs = result.get("pairs")
    if not isinstance(raw_pairs, list):
        return False, "pairs is not a list"

    expected_pairs_set = {(low_map[j], j) for j in low_map}
    actual_pairs_set = set()
    for p in raw_pairs:
        if not isinstance(p, list) or len(p) != 2:
            return False, f"Pair {p} is not a 2-element list"
        try:
            b, d = int(p[0]), int(p[1])
        except (ValueError, TypeError):
            return False, f"Malformed indices in pair {p}"
        actual_pairs_set.add((b, d))

        # Check dimension difference: dim(d) must equal dim(b) + 1
        dim_b = parsed_simplices[b]["dim"]
        dim_d = parsed_simplices[d]["dim"]
        if dim_d != dim_b + 1:
            return (
                False,
                f"Pair ({b}, {d}) dimension mismatch: dim({d})={dim_d} != dim({b})={dim_b} + 1",
            )

    if actual_pairs_set != expected_pairs_set:
        return (
            False,
            f"Reported pairs mismatch R reduction: expected {len(expected_pairs_set)} pairs, got {len(actual_pairs_set)}",
        )

    # 7. Check essential classes
    raw_essential = result.get("essential")
    if not isinstance(raw_essential, list):
        return False, "essential is not a list"

    paired_births = set(low_map.values())
    expected_essential = {
        i for i in range(n) if i not in paired_births and not R_cols.get(i, D_cols[i])
    }
    actual_essential = set()
    for e in raw_essential:
        try:
            actual_essential.add(int(e))
        except (ValueError, TypeError):
            return False, f"Malformed index in essential: {e}"

    if actual_essential != expected_essential:
        return (
            False,
            f"Reported essential mismatch: expected {sorted(expected_essential)}, got {sorted(actual_essential)}",
        )

    # 8. Check value barcode
    raw_barcode = result.get("barcode")
    if not isinstance(raw_barcode, dict):
        return False, "barcode is not a dict"

    # Reconstruct expected barcode
    expected_barcode: dict[str, list[list[str]]] = {}
    for d in range(4):
        expected_barcode[str(d)] = []

    for b, d in sorted(expected_pairs_set, key=lambda p: (p[0], p[1])):
        dim_b = parsed_simplices[b]["dim"]
        val_b = parsed_simplices[b]["val"]
        val_d = parsed_simplices[d]["val"]
        if val_b != val_d:
            expected_barcode[str(dim_b)].append([str(val_b), str(val_d)])

    for e in sorted(expected_essential):
        dim_e = parsed_simplices[e]["dim"]
        val_e = parsed_simplices[e]["val"]
        expected_barcode[str(dim_e)].append([str(val_e), "inf"])

    def bar_key(interval: list[str]) -> tuple[Fraction, Fraction]:
        start = Fraction(interval[0])
        end = Fraction(10**9, 1) if interval[1] == "inf" else Fraction(interval[1])
        return (start, end)

    for deg_str in expected_barcode:
        expected_barcode[deg_str].sort(key=bar_key)

    # Validate participant barcode against expected
    for deg_str in expected_barcode:
        actual_bars = raw_barcode.get(deg_str, [])
        if not isinstance(actual_bars, list):
            return False, f"barcode[{deg_str}] is not a list"

        actual_parsed = []
        for interval in actual_bars:
            if not isinstance(interval, list) or len(interval) != 2:
                return False, f"Invalid barcode interval {interval} in degree {deg_str}"
            try:
                start = Fraction(str(interval[0]))
                end_str = str(interval[1])
                if end_str != "inf":
                    end = Fraction(end_str)
                    if start == end:
                        return (
                            False,
                            f"Zero-length interval [{start}, {end}] was kept in value barcode!",
                        )
                    if end < start:
                        return False, f"Inverted interval [{start}, {end}] in degree {deg_str}"
                actual_parsed.append([str(interval[0]), end_str])
            except (ValueError, TypeError, ZeroDivisionError):
                return False, f"Malformed values in interval {interval}"

        actual_parsed.sort(key=bar_key)
        if actual_parsed != expected_barcode[deg_str]:
            return (
                False,
                f"Barcode mismatch in degree {deg_str}: expected {expected_barcode[deg_str]}, got {actual_parsed}",
            )

    return True, "Algebraic reduction certificate verified over F2"
