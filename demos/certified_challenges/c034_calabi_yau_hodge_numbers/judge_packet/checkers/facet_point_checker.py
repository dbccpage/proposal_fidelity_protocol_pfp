"""Checker 1: Direct Primal Facet & Bounding-Box Point Certifier for C034.

Operates as a self-contained certifier with ZERO shared implementation code.
Evaluates 4D affine determinants, bounding-box lattice point enumeration,
facet mask incidence, and Batyrev Hodge number formulas.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping, Sequence

ALLOWED_SOLVED_KEYS = frozenset(
    {"id", "case_id", "status", "reflexive", "h11", "h21", "euler", "face_data"}
)

ALLOWED_OOS_KEYS = frozenset({"id", "case_id", "status", "witness"})

ALLOWED_UNKNOWN_KEYS = frozenset({"id", "case_id", "status", "refusal_code", "refusal"})

ALLOWED_FACE_DATA_KEYS = frozenset(
    {
        "l_delta",
        "l_delta_star",
        "facets_delta_star",
        "codim2_products",
        "codim2_products_delta",
        "codim2_products_delta_star",
        "facets_delta",
    }
)

ALLOWED_FACET_RECORD_KEYS = frozenset({"normal", "interior_points"})

ALLOWED_CODIM2_RECORD_KEYS = frozenset(
    {"l_star_theta", "l_star_theta_star", "product", "theta_normal", "theta_star_vertices"}
)

ALLOWED_WITNESS_KEYS = frozenset(
    {"kind", "normal", "distance", "point", "reason", "affine_dimension"}
)

CLOSED_REFUSAL_CODES = frozenset(
    {
        "MALFORMED_CASE_STRUCTURE",
        "COORDINATES_OUT_OF_BOUNDS",
        "TOO_MANY_VERTICES",
        "INVALID_READING_SPECIFIER",
        "INVALID_READING_FLAG",
        "DIMENSION_LESS_THAN_FOUR",
        "LOWER_DIMENSIONAL_POLYTOPE",
        "NON_INTEGRAL_COORDINATES",
        "DUPLICATE_OR_NON_INTEGRAL_COORDINATES",
    }
)


def _is_exact_int(val: Any) -> bool:
    """Returns True if and only if val is an int and strictly not a boolean."""
    return type(val) is int and not isinstance(val, bool)


def _gcd_list(vals: Sequence[int]) -> int:
    g = 0
    for v in vals:
        g = math.gcd(g, abs(v))
    return g


def _dot4(a: Sequence[int], b: Sequence[int]) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]


def _det3_c1(r0: Sequence[int], r1: Sequence[int], r2: Sequence[int]) -> int:
    return (
        r0[0] * (r1[1] * r2[2] - r1[2] * r2[1])
        - r0[1] * (r1[0] * r2[2] - r1[2] * r2[0])
        + r0[2] * (r1[0] * r2[1] - r1[1] * r2[0])
    )


def _cross4_c1(
    d1: Sequence[int], d2: Sequence[int], d3: Sequence[int]
) -> tuple[int, int, int, int]:
    a0 = _det3_c1((d1[1], d1[2], d1[3]), (d2[1], d2[2], d2[3]), (d3[1], d3[2], d3[3]))
    a1 = -_det3_c1((d1[0], d1[2], d1[3]), (d2[0], d2[2], d2[3]), (d3[0], d3[2], d3[3]))
    a2 = _det3_c1((d1[0], d1[1], d1[3]), (d2[0], d2[1], d2[3]), (d3[0], d3[1], d3[3]))
    a3 = -_det3_c1((d1[0], d1[1], d1[2]), (d2[0], d2[1], d2[2]), (d3[0], d3[1], d3[2]))
    return (a0, a1, a2, a3)


def _compute_rank_c1(vectors: Sequence[Sequence[int]]) -> int:
    """Exact rank over Q by Gaussian elimination on Fractions (no float tolerance).

    Entries must be exact ints (bool rejected); anything else raises TypeError.
    """
    if not vectors:
        return 0
    mat: list[list[Fraction]] = []
    for v in vectors:
        row = []
        for x in v:
            if not _is_exact_int(x):
                raise TypeError(f"rank entries must be exact ints, got {x!r}")
            row.append(Fraction(x))
        mat.append(row)
    num_rows = len(mat)
    num_cols = len(mat[0])
    if any(len(r) != num_cols for r in mat):
        raise ValueError("rank input rows must have equal length")
    rank = 0
    for col in range(num_cols):
        pivot = -1
        for row in range(rank, num_rows):
            if mat[row][col] != 0:
                pivot = row
                break
        if pivot == -1:
            continue
        mat[rank], mat[pivot] = mat[pivot], mat[rank]
        p_val = mat[rank][col]
        for row in range(num_rows):
            if row != rank and mat[row][col] != 0:
                factor = mat[row][col] / p_val
                for c in range(col, num_cols):
                    mat[row][c] -= factor * mat[rank][c]
        rank += 1
        if rank == num_cols or rank == num_rows:
            break
    return rank


def _compute_affine_dim_c1(points: Sequence[Sequence[int]]) -> int:
    if len(points) <= 1:
        return 0
    p0 = points[0]
    diffs = [[p[j] - p0[j] for j in range(4)] for p in points[1:]]
    return _compute_rank_c1(diffs)


def _verify_refusal_warranted(case: Mapping[str, Any], refusal_code: str) -> tuple[bool, str]:
    """Verifies whether the refusal is mathematically and structurally warranted."""
    if refusal_code not in CLOSED_REFUSAL_CODES:
        return False, f"FAIL: unrecognized refusal code {refusal_code!r}"

    cid = case.get("case_id") or case.get("id")
    reading = case.get("reading")
    vertices = case.get("vertices")

    if refusal_code == "COORDINATES_OUT_OF_BOUNDS":
        if isinstance(vertices, list):
            has_oob = any(
                isinstance(pt, (list, tuple))
                and any(isinstance(c, int) and abs(c) > 30 for c in pt)
                for pt in vertices
            )
            if has_oob:
                return True, "VALID_REFUSAL_COORDINATES_OUT_OF_BOUNDS"
        return False, "FAIL: refused COORDINATES_OUT_OF_BOUNDS on bounded coordinates"

    if refusal_code == "TOO_MANY_VERTICES":
        if isinstance(vertices, list) and len(vertices) > 40:
            return True, "VALID_REFUSAL_TOO_MANY_VERTICES"
        return False, "FAIL: refused TOO_MANY_VERTICES on vertex count <= 40"

    if refusal_code in ("INVALID_READING_SPECIFIER", "INVALID_READING_FLAG"):
        if reading not in ("primal", "dual", "delta", "delta_star"):
            return True, "VALID_REFUSAL_INVALID_READING"
        return False, f"FAIL: refused INVALID_READING on valid reading {reading!r}"

    if refusal_code in ("DIMENSION_LESS_THAN_FOUR", "LOWER_DIMENSIONAL_POLYTOPE"):
        if isinstance(vertices, list) and len(vertices) >= 1:
            try:
                pts = [(p[0], p[1], p[2], p[3]) for p in vertices]
                dim = _compute_affine_dim_c1(pts)
                if dim < 4:
                    return True, "VALID_REFUSAL_LOWER_DIMENSION"
            except Exception:
                pass
        return False, "FAIL: refused LOWER_DIMENSION on full 4D polytope"

    if refusal_code == "MALFORMED_CASE_STRUCTURE":
        if not isinstance(case, Mapping) or not cid or not isinstance(cid, str):
            return True, "VALID_REFUSAL_MALFORMED"
        if not isinstance(vertices, list) or len(vertices) == 0:
            return True, "VALID_REFUSAL_MALFORMED"
        for pt in vertices:
            if not isinstance(pt, (list, tuple)) or len(pt) != 4:
                return True, "VALID_REFUSAL_MALFORMED"
            for c in pt:
                if not _is_exact_int(c):
                    return True, "VALID_REFUSAL_MALFORMED"
        return False, "FAIL: refused MALFORMED_CASE_STRUCTURE on valid case structure"

    if refusal_code in ("NON_INTEGRAL_COORDINATES", "DUPLICATE_OR_NON_INTEGRAL_COORDINATES"):
        if isinstance(vertices, list):
            for pt in vertices:
                if isinstance(pt, (list, tuple)):
                    for c in pt:
                        if not _is_exact_int(c):
                            return True, "VALID_REFUSAL_NON_INTEGRAL"
        return False, "FAIL: refused NON_INTEGRAL_COORDINATES on integral coordinates"

    return False, f"FAIL: unable to validate refusal code {refusal_code}"


def verify_facet_point_certificate(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> tuple[bool, str]:
    """Checker 1: Direct Primal Facet & Bounding-Box Point Certifier."""
    try:
        if not isinstance(result, Mapping):
            return False, f"FAIL: result must be a Mapping, got {type(result).__name__}"

        status = result.get("status")
        if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
            return False, f"FAIL: unrecognized status {status!r}"

        # Schema Whitelisting
        if status == "SOLVED":
            extra = set(result.keys()) - ALLOWED_SOLVED_KEYS
            if extra:
                return False, f"FAIL: phantom keys in SOLVED answer: {sorted(extra)}"
            for req in ("status", "reflexive", "h11", "h21", "euler", "face_data"):
                if req not in result:
                    return False, f"FAIL: missing required key {req!r} in SOLVED answer"
        elif status == "OUT_OF_SCOPE":
            extra = set(result.keys()) - ALLOWED_OOS_KEYS
            if extra:
                return False, f"FAIL: phantom keys in OUT_OF_SCOPE answer: {sorted(extra)}"
            if "witness" not in result:
                return False, "FAIL: missing witness in OUT_OF_SCOPE answer"
        elif status == "UNKNOWN":
            extra = set(result.keys()) - ALLOWED_UNKNOWN_KEYS
            if extra:
                return False, f"FAIL: phantom keys in UNKNOWN answer: {sorted(extra)}"
            if "refusal_code" not in result and "refusal" not in result:
                return False, "FAIL: missing refusal_code in UNKNOWN answer"

        # Case ID Parity
        cid_case = str(case.get("case_id") or case.get("id") or "")
        cid_res = str(result.get("case_id") or result.get("id") or "")
        if cid_case and cid_res and cid_case != cid_res:
            return False, f"FAIL: case ID mismatch ({cid_case} != {cid_res})"

        # Handle UNKNOWN status
        if status == "UNKNOWN":
            rcode = result.get("refusal_code") or result.get("refusal")
            if not isinstance(rcode, str):
                return False, f"FAIL: refusal_code must be string, got {type(rcode).__name__}"
            return _verify_refusal_warranted(case, rcode)

        # Validate input vertices for geometry check
        raw_v = case.get("vertices")
        if not isinstance(raw_v, list) or len(raw_v) == 0:
            return False, "FAIL: case vertices missing or invalid"

        vertices: list[tuple[int, int, int, int]] = []
        for pt in raw_v:
            if not isinstance(pt, (list, tuple)) or len(pt) != 4:
                return False, "FAIL: vertex element must be length-4 list/tuple"
            for c in pt:
                if not _is_exact_int(c):
                    return False, f"FAIL: coordinate {c!r} is not an exact integer"
            vertices.append((pt[0], pt[1], pt[2], pt[3]))

        aff_dim = _compute_affine_dim_c1(vertices)

        # Handle OUT_OF_SCOPE status
        if status == "OUT_OF_SCOPE":
            witness = result.get("witness")
            if not isinstance(witness, dict):
                return False, "FAIL: witness must be a dict"
            extra_w = set(witness.keys()) - ALLOWED_WITNESS_KEYS
            if extra_w:
                return False, f"FAIL: phantom keys in witness: {sorted(extra_w)}"
            kind = witness.get("kind")

            if kind == "dimension_deficient":
                if aff_dim < 4:
                    return True, "VALID_OUT_OF_SCOPE_DIMENSION_DEFICIENT"
                return False, f"FAIL: claimed dimension_deficient but affine dimension is {aff_dim}"

            if aff_dim < 4:
                return True, "VALID_OUT_OF_SCOPE_DIMENSION_DEFICIENT"

            # Check facets
            unique_v = list(dict.fromkeys(vertices))
            m = len(unique_v)
            facets_dict: dict[tuple[tuple[int, int, int, int], int], set[int]] = {}
            for i in range(m - 3):
                p1 = unique_v[i]
                for j in range(i + 1, m - 2):
                    p2 = unique_v[j]
                    d1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2], p2[3] - p1[3])
                    for k in range(j + 1, m - 1):
                        p3 = unique_v[k]
                        d2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2], p3[3] - p1[3])
                        for l in range(k + 1, m):
                            p4 = unique_v[l]
                            d3 = (p4[0] - p1[0], p4[1] - p1[1], p4[2] - p1[2], p4[3] - p1[3])
                            a = _cross4_c1(d1, d2, d3)
                            if a == (0, 0, 0, 0):
                                continue
                            g = _gcd_list(a)
                            a = (a[0] // g, a[1] // g, a[2] // g, a[3] // g)
                            b = _dot4(a, p1)
                            has_pos = any(_dot4(a, v) > b for v in unique_v)
                            has_neg = any(_dot4(a, v) < b for v in unique_v)
                            if has_pos and has_neg:
                                continue
                            if has_neg and not has_pos:
                                a = (-a[0], -a[1], -a[2], -a[3])
                                b = -b
                            fkey = (a, b)
                            if fkey not in facets_dict:
                                on_f = {idx for idx, v in enumerate(unique_v) if _dot4(a, v) == b}
                                if len(on_f) >= 4:
                                    if _compute_affine_dim_c1([unique_v[idx] for idx in on_f]) == 3:
                                        facets_dict[fkey] = on_f

            if kind == "origin_not_interior":
                if any(b >= 0 for _, b in facets_dict.keys()):
                    return True, "VALID_OUT_OF_SCOPE_ORIGIN_NOT_INTERIOR"
                return False, "FAIL: claimed origin_not_interior but origin is strictly interior"

            if kind == "facet_distance":
                claimed_dist = witness.get("distance")
                if not _is_exact_int(claimed_dist):
                    return False, "FAIL: witness distance must be exact integer"
                if claimed_dist == 1:
                    return False, "FAIL: facet_distance witness cannot claim distance 1"
                has_non_unit_dist = any(-b != 1 for _, b in facets_dict.keys())
                if not has_non_unit_dist:
                    return False, "FAIL: claimed facet_distance on reflexive polytope"
                claimed_norm = witness.get("normal")
                if claimed_norm is not None:
                    if (
                        not isinstance(claimed_norm, list)
                        or len(claimed_norm) != 4
                        or not all(_is_exact_int(x) for x in claimed_norm)
                    ):
                        return False, "FAIL: witness normal must be length-4 list of exact integers"
                    norm_t = tuple(claimed_norm)
                    if (norm_t, -claimed_dist) not in facets_dict:
                        return (
                            False,
                            f"FAIL: witness normal {norm_t} and distance {claimed_dist} do not match any actual facet",
                        )
                return True, "VALID_OUT_OF_SCOPE_FACET_DISTANCE"

            if kind == "multiple_interior_points":
                return True, "VALID_OUT_OF_SCOPE_MULTIPLE_INTERIOR_POINTS"

            return False, f"FAIL: unrecognized witness kind {kind!r}"

        # Status is SOLVED
        if aff_dim < 4:
            return False, f"FAIL: polytope has affine dimension {aff_dim} < 4, cannot be SOLVED"

        # Check boolean injection
        ref_val = result.get("reflexive")
        if type(ref_val) is not bool or not ref_val:
            return False, f"FAIL: reflexive must be bool True, got {ref_val!r}"

        h11 = result.get("h11")
        h21 = result.get("h21")
        euler = result.get("euler")
        if not _is_exact_int(h11) or h11 < 0:
            return False, f"FAIL: h11 must be non-negative exact integer, got {h11!r}"
        if not _is_exact_int(h21) or h21 < 0:
            return False, f"FAIL: h21 must be non-negative exact integer, got {h21!r}"
        if not _is_exact_int(euler):
            return False, f"FAIL: euler must be exact integer, got {euler!r}"
        if euler != 2 * (h11 - h21):
            return False, f"FAIL: euler {euler} != 2*(h11 - h21) = {2 * (h11 - h21)}"

        face_data = result.get("face_data")
        if not isinstance(face_data, dict):
            return False, "FAIL: missing mandatory face_data dict"
        extra_fd = set(face_data.keys()) - ALLOWED_FACE_DATA_KEYS
        if extra_fd:
            return False, f"FAIL: phantom keys in face_data: {sorted(extra_fd)}"

        l_delta = face_data.get("l_delta")
        l_delta_star = face_data.get("l_delta_star")
        if not _is_exact_int(l_delta) or l_delta <= 0:
            return False, f"FAIL: face_data.l_delta must be positive exact integer, got {l_delta!r}"
        if not _is_exact_int(l_delta_star) or l_delta_star <= 0:
            return (
                False,
                f"FAIL: face_data.l_delta_star must be positive exact integer, got {l_delta_star!r}",
            )

        facets_ds = face_data.get("facets_delta_star")
        if not isinstance(facets_ds, list):
            return False, "FAIL: face_data.facets_delta_star must be list"
        for rec in facets_ds:
            if not isinstance(rec, dict):
                return False, "FAIL: facet record must be dict"
            extra_rec = set(rec.keys()) - ALLOWED_FACET_RECORD_KEYS
            if extra_rec:
                return False, f"FAIL: phantom keys in facet record: {sorted(extra_rec)}"
            norm = rec.get("normal")
            ip = rec.get("interior_points")
            if (
                not isinstance(norm, list)
                or len(norm) != 4
                or not all(_is_exact_int(x) for x in norm)
            ):
                return False, "FAIL: facet normal must be length-4 list of exact integers"
            if not _is_exact_int(ip) or ip < 0:
                return (
                    False,
                    f"FAIL: interior_points must be non-negative exact integer, got {ip!r}",
                )

        codim2_prods = face_data.get("codim2_products")
        if not isinstance(codim2_prods, list):
            return False, "FAIL: face_data.codim2_products must be list"
        for prec in codim2_prods:
            if not isinstance(prec, dict):
                return False, "FAIL: codim2 record must be dict"
            extra_prec = set(prec.keys()) - ALLOWED_CODIM2_RECORD_KEYS
            if extra_prec:
                return False, f"FAIL: phantom keys in codim2 record: {sorted(extra_prec)}"
            p = prec.get("product")
            if not _is_exact_int(p) or p <= 0:
                return False, f"FAIL: codim2 product must be positive exact integer, got {p!r}"

        # Recompute geometric invariants to verify 100% truth
        unique_v = list(dict.fromkeys(vertices))
        m = len(unique_v)
        facets_dict: dict[tuple[tuple[int, int, int, int], int], set[int]] = {}
        for i in range(m - 3):
            p1 = unique_v[i]
            for j in range(i + 1, m - 2):
                p2 = unique_v[j]
                d1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2], p2[3] - p1[3])
                for k in range(j + 1, m - 1):
                    p3 = unique_v[k]
                    d2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2], p3[3] - p1[3])
                    for l in range(k + 1, m):
                        p4 = unique_v[l]
                        d3 = (p4[0] - p1[0], p4[1] - p1[1], p4[2] - p1[2], p4[3] - p1[3])
                        a = _cross4_c1(d1, d2, d3)
                        if a == (0, 0, 0, 0):
                            continue
                        g = _gcd_list(a)
                        a = (a[0] // g, a[1] // g, a[2] // g, a[3] // g)
                        b = _dot4(a, p1)
                        has_pos = any(_dot4(a, v) > b for v in unique_v)
                        has_neg = any(_dot4(a, v) < b for v in unique_v)
                        if has_pos and has_neg:
                            continue
                        if has_neg and not has_pos:
                            a = (-a[0], -a[1], -a[2], -a[3])
                            b = -b
                        fkey = (a, b)
                        if fkey not in facets_dict:
                            on_f = {idx for idx, v in enumerate(unique_v) if _dot4(a, v) == b}
                            if len(on_f) >= 4:
                                if _compute_affine_dim_c1([unique_v[idx] for idx in on_f]) == 3:
                                    facets_dict[fkey] = on_f

        # Check reflexivity
        for _, b in facets_dict.keys():
            if b >= 0:
                return False, "FAIL: origin not strictly interior, cannot be SOLVED"
            if -b != 1:
                return False, f"FAIL: facet distance {-b} != 1, cannot be SOLVED"

        # Extreme vertices of P
        extreme_v: list[tuple[int, int, int, int]] = []
        for idx, v in enumerate(unique_v):
            inc_normals = [facet[0] for facet, on_v in facets_dict.items() if idx in on_v]
            if _compute_rank_c1(inc_normals) == 4:
                extreme_v.append(v)

        dual_v = [facet[0] for facet in facets_dict.keys()]

        reading = case.get("reading", "dual")
        if reading in ("dual", "delta_star"):
            delta_star_verts = extreme_v
            delta_star_facets = [(u, -1) for u in dual_v]
            delta_verts = dual_v
            delta_facets = [(v, -1) for v in extreme_v]
        else:
            delta_verts = extreme_v
            delta_facets = [(u, -1) for u in dual_v]
            delta_star_verts = dual_v
            delta_star_facets = [(v, -1) for v in extreme_v]

        # Scan points
        def _scan_c1(
            facets: list[tuple[tuple[int, int, int, int], int]],
            verts: list[tuple[int, int, int, int]],
        ):
            bmin = [min(v[i] for v in verts) for i in range(4)]
            bmax = [max(v[i] for v in verts) for i in range(4)]
            res = []
            for x0 in range(bmin[0], bmax[0] + 1):
                for x1 in range(bmin[1], bmax[1] + 1):
                    for x2 in range(bmin[2], bmax[2] + 1):
                        for x3 in range(bmin[3], bmax[3] + 1):
                            pt = (x0, x1, x2, x3)
                            if all(_dot4(u, pt) >= b for u, b in facets):
                                res.append(pt)
            return res

        pts_delta = _scan_c1(delta_facets, delta_verts)
        pts_delta_star = _scan_c1(delta_star_facets, delta_star_verts)

        actual_l_delta = len(pts_delta)
        actual_l_delta_star = len(pts_delta_star)

        if l_delta != actual_l_delta:
            return False, f"FAIL: l_delta mismatch ({l_delta} != {actual_l_delta})"
        if l_delta_star != actual_l_delta_star:
            return False, f"FAIL: l_delta_star mismatch ({l_delta_star} != {actual_l_delta_star})"

        # Facet interior points of Delta*
        sum_l_star_ds = 0
        actual_facets_ds_counts: dict[tuple[int, int, int, int], int] = {}
        for u_star, _ in delta_star_facets:
            cnt = sum(
                1
                for p in pts_delta_star
                if _dot4(u_star, p) == -1
                and all(_dot4(w, p) > -1 for w, _ in delta_star_facets if w != u_star)
            )
            actual_facets_ds_counts[u_star] = cnt
            sum_l_star_ds += cnt

        # Check facet records with strict cardinality, uniqueness, and set-equality guards
        if len(facets_ds) != len(actual_facets_ds_counts):
            return (
                False,
                f"FAIL: facets_delta_star count mismatch ({len(facets_ds)} != {len(actual_facets_ds_counts)})",
            )
        submitted_normals = [tuple(rec["normal"]) for rec in facets_ds]
        if len(submitted_normals) != len(set(submitted_normals)):
            return False, "FAIL: duplicate facet normals in facets_delta_star"
        if set(submitted_normals) != set(actual_facets_ds_counts.keys()):
            return (
                False,
                "FAIL: facets_delta_star normals do not match the complete set of facet normals",
            )
        for rec in facets_ds:
            norm_t = tuple(rec["normal"])
            if rec["interior_points"] != actual_facets_ds_counts[norm_t]:
                return (
                    False,
                    f"FAIL: facet {norm_t} interior count mismatch ({rec['interior_points']} != {actual_facets_ds_counts[norm_t]})",
                )

        # Facet interior points of Delta
        sum_l_star_d = 0
        for u, _ in delta_facets:
            cnt = sum(
                1
                for p in pts_delta
                if _dot4(u, p) == -1 and all(_dot4(w, p) > -1 for w, _ in delta_facets if w != u)
            )
            sum_l_star_d += cnt

        # Codimension-2 face pairings:
        # S2 = sum_{dim Theta = 2} l*(Theta) l*(Theta*) (2-faces of Delta x edges of Delta*)
        actual_S2 = 0
        m_s = len(delta_star_verts)
        for i in range(m_s):
            u_a = delta_star_verts[i]
            for j in range(i + 1, m_s):
                u_b = delta_star_verts[j]
                diff = (u_b[0] - u_a[0], u_b[1] - u_a[1], u_b[2] - u_a[2], u_b[3] - u_a[3])
                l_star_edge_ds = _gcd_list(diff) - 1
                l_star_2face_d = sum(
                    1
                    for p in pts_delta
                    if _dot4(u_a, p) == -1
                    and _dot4(u_b, p) == -1
                    and all(_dot4(w, p) > -1 for w in delta_star_verts if w != u_a and w != u_b)
                )
                prod = l_star_edge_ds * l_star_2face_d
                if prod > 0:
                    actual_S2 += prod

        # S1 = sum_{dim Theta* = 2} l*(Theta*) l*(Theta) (2-faces of Delta* x edges of Delta)
        actual_S1 = 0
        m_d = len(delta_verts)
        for i in range(m_d):
            v_a = delta_verts[i]
            for j in range(i + 1, m_d):
                v_b = delta_verts[j]
                diff = (v_b[0] - v_a[0], v_b[1] - v_a[1], v_b[2] - v_a[2], v_b[3] - v_a[3])
                l_star_edge_d = _gcd_list(diff) - 1
                l_star_2face_ds = sum(
                    1
                    for q in pts_delta_star
                    if _dot4(v_a, q) == -1
                    and _dot4(v_b, q) == -1
                    and all(_dot4(w, q) > -1 for w in delta_verts if w != v_a and w != v_b)
                )
                prod = l_star_edge_d * l_star_2face_ds
                if prod > 0:
                    actual_S1 += prod

        actual_codim2_sum = actual_S1 + actual_S2
        reported_codim2_sum = sum(p["product"] for p in codim2_prods)
        if reported_codim2_sum != actual_codim2_sum:
            return (
                False,
                f"FAIL: codim-2 correction sum mismatch ({reported_codim2_sum} != {actual_codim2_sum})",
            )

        # Batyrev's exact Hodge formulas
        actual_h11 = actual_l_delta_star - 5 - sum_l_star_ds + actual_S1
        actual_h21 = actual_l_delta - 5 - sum_l_star_d + actual_S2
        actual_euler = 2 * (actual_h11 - actual_h21)

        if h11 != actual_h11:
            return False, f"FAIL: h11 mismatch ({h11} != {actual_h11})"
        if h21 != actual_h21:
            return False, f"FAIL: h21 mismatch ({h21} != {actual_h21})"
        if euler != actual_euler:
            return False, f"FAIL: euler mismatch ({euler} != {actual_euler})"

        return True, "CHECKER1_PASS"

    except Exception as exc:
        return False, f"FAIL: exception in Checker 1: {type(exc).__name__}: {exc}"
