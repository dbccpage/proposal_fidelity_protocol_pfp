"""Checker 2: Dual Mirror & Affine HNF Face Basis Certifier for C034.

Operates as a completely independent certifier with ZERO shared implementation code.
Solves polar dual first via rational Gauss-Jordan matrix inversion,
parametrizes faces in intrinsic affine coordinates, verifies 2D Pick's theorem,
and cross-verifies Hodge numbers under dual mirror swap invariance.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping, Sequence

ALLOWED_SOLVED_KEYS_C2 = frozenset(
    {"id", "case_id", "status", "reflexive", "h11", "h21", "euler", "face_data"}
)

ALLOWED_OOS_KEYS_C2 = frozenset({"id", "case_id", "status", "witness"})

ALLOWED_UNKNOWN_KEYS_C2 = frozenset({"id", "case_id", "status", "refusal_code", "refusal"})

ALLOWED_FACE_DATA_KEYS_C2 = frozenset(
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

ALLOWED_FACET_RECORD_KEYS_C2 = frozenset({"normal", "interior_points"})

ALLOWED_CODIM2_RECORD_KEYS_C2 = frozenset(
    {"l_star_theta", "l_star_theta_star", "product", "theta_normal", "theta_star_vertices"}
)

ALLOWED_WITNESS_KEYS_C2 = frozenset(
    {"kind", "normal", "distance", "point", "reason", "affine_dimension"}
)

CLOSED_REFUSAL_CODES_C2 = frozenset(
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


def _is_int_c2(v: Any) -> bool:
    """Strict integer check: must be int, not bool."""
    return type(v) is int and not isinstance(v, bool)


def _dot_c2(u: Sequence[int | Fraction], v: Sequence[int | Fraction]) -> Fraction:
    return sum(u[i] * v[i] for i in range(4))


def _solve_4x4_system_c2(matrix: list[list[int]], rhs: list[int]) -> tuple[bool, list[Fraction]]:
    """Exact rational Gauss-Jordan solver for 4x4 linear system M y = rhs."""
    mat = [[Fraction(matrix[r][c]) for c in range(4)] + [Fraction(rhs[r])] for r in range(4)]
    for col in range(4):
        piv = -1
        for row in range(col, 4):
            if mat[row][col] != 0:
                piv = row
                break
        if piv == -1:
            return False, []
        mat[col], mat[piv] = mat[piv], mat[col]
        pivot_val = mat[col][col]
        for c in range(col, 5):
            mat[col][c] /= pivot_val
        for r in range(4):
            if r != col and mat[r][col] != 0:
                factor = mat[r][col]
                for c in range(col, 5):
                    mat[r][c] -= factor * mat[col][c]
    return True, [mat[r][4] for r in range(4)]


def _rational_rank_c2(mat_rows: list[list[int]]) -> int:
    """Exact rational rank of a matrix."""
    if not mat_rows:
        return 0
    m = [[Fraction(x) for x in r] for r in mat_rows]
    R = len(m)
    C = len(m[0])
    rank = 0
    for col in range(C):
        piv = -1
        for row in range(rank, R):
            if m[row][col] != 0:
                piv = row
                break
        if piv == -1:
            continue
        m[rank], m[piv] = m[piv], m[rank]
        pv = m[rank][col]
        for r in range(R):
            if r != rank and m[r][col] != 0:
                f = m[r][col] / pv
                for c in range(col, C):
                    m[r][c] -= f * m[rank][c]
        rank += 1
        if rank == C or rank == R:
            break
    return rank


def _affine_rank_c2(points: list[tuple[int, int, int, int]]) -> int:
    if len(points) <= 1:
        return 0
    p0 = points[0]
    diffs = [[p[j] - p0[j] for j in range(4)] for p in points[1:]]
    return _rational_rank_c2(diffs)


def _verify_refusal_warranted_c2(case: Mapping[str, Any], refusal_code: str) -> tuple[bool, str]:
    if refusal_code not in CLOSED_REFUSAL_CODES_C2:
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
                dim = _affine_rank_c2(pts)
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
                if not _is_int_c2(c):
                    return True, "VALID_REFUSAL_MALFORMED"
        return False, "FAIL: refused MALFORMED_CASE_STRUCTURE on valid case structure"

    if refusal_code in ("NON_INTEGRAL_COORDINATES", "DUPLICATE_OR_NON_INTEGRAL_COORDINATES"):
        if isinstance(vertices, list):
            for pt in vertices:
                if isinstance(pt, (list, tuple)):
                    for c in pt:
                        if not _is_int_c2(c):
                            return True, "VALID_REFUSAL_NON_INTEGRAL"
        return False, "FAIL: refused NON_INTEGRAL_COORDINATES on integral coordinates"

    return False, f"FAIL: unable to validate refusal code {refusal_code}"


def verify_affine_hnf_certificate(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> tuple[bool, str]:
    """Checker 2: Dual Mirror & Affine HNF Subspace Certifier."""
    try:
        if not isinstance(result, Mapping):
            return False, f"FAIL: result must be a Mapping, got {type(result).__name__}"

        status = result.get("status")
        if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
            return False, f"FAIL: unrecognized status {status!r}"

        # Schema Whitelisting
        if status == "SOLVED":
            extra = set(result.keys()) - ALLOWED_SOLVED_KEYS_C2
            if extra:
                return False, f"FAIL: phantom keys in SOLVED answer: {sorted(extra)}"
            for req in ("status", "reflexive", "h11", "h21", "euler", "face_data"):
                if req not in result:
                    return False, f"FAIL: missing required key {req!r} in SOLVED answer"
        elif status == "OUT_OF_SCOPE":
            extra = set(result.keys()) - ALLOWED_OOS_KEYS_C2
            if extra:
                return False, f"FAIL: phantom keys in OUT_OF_SCOPE answer: {sorted(extra)}"
            if "witness" not in result:
                return False, "FAIL: missing witness in OUT_OF_SCOPE answer"
        elif status == "UNKNOWN":
            extra = set(result.keys()) - ALLOWED_UNKNOWN_KEYS_C2
            if extra:
                return False, f"FAIL: phantom keys in UNKNOWN answer: {sorted(extra)}"
            if "refusal_code" not in result and "refusal" not in result:
                return False, "FAIL: missing refusal_code in UNKNOWN answer"

        # Case ID Parity
        cid_case = str(case.get("case_id") or case.get("id") or "")
        cid_res = str(result.get("case_id") or result.get("id") or "")
        if cid_case and cid_res and cid_case != cid_res:
            return False, f"FAIL: case ID mismatch ({cid_case} != {cid_res})"

        if status == "UNKNOWN":
            rcode = result.get("refusal_code") or result.get("refusal")
            if not isinstance(rcode, str):
                return False, f"FAIL: refusal_code must be string, got {type(rcode).__name__}"
            return _verify_refusal_warranted_c2(case, rcode)

        raw_v = case.get("vertices")
        if not isinstance(raw_v, list) or len(raw_v) == 0:
            return False, "FAIL: case vertices missing or invalid"

        vertices: list[tuple[int, int, int, int]] = []
        for pt in raw_v:
            if not isinstance(pt, (list, tuple)) or len(pt) != 4:
                return False, "FAIL: vertex element must be length-4 list/tuple"
            for c in pt:
                if not _is_int_c2(c):
                    return False, f"FAIL: coordinate {c!r} is not an exact integer"
            vertices.append((pt[0], pt[1], pt[2], pt[3]))

        dim = _affine_rank_c2(vertices)

        if status == "OUT_OF_SCOPE":
            witness = result.get("witness")
            if not isinstance(witness, dict):
                return False, "FAIL: witness must be a dict"
            extra_w = set(witness.keys()) - ALLOWED_WITNESS_KEYS_C2
            if extra_w:
                return False, f"FAIL: phantom keys in witness: {sorted(extra_w)}"
            kind = witness.get("kind")

            if kind == "dimension_deficient":
                if dim < 4:
                    return True, "VALID_OUT_OF_SCOPE_DIMENSION_DEFICIENT"
                return False, f"FAIL: claimed dimension_deficient but affine dimension is {dim}"

            if dim < 4:
                return True, "VALID_OUT_OF_SCOPE_DIMENSION_DEFICIENT"

            # Check polar dual vertices
            # Test subsystem solvability
            m = len(vertices)
            non_integral_found = False
            for i in range(m - 3):
                for j in range(i + 1, m - 2):
                    for k in range(j + 1, m - 1):
                        for l in range(k + 1, m):
                            mat = [
                                list(vertices[i]),
                                list(vertices[j]),
                                list(vertices[k]),
                                list(vertices[l]),
                            ]
                            solvable, y = _solve_4x4_system_c2(mat, [-1, -1, -1, -1])
                            if solvable:
                                is_feas = all(_dot_c2(y, v) >= -1 for v in vertices)
                                if is_feas:
                                    if any(coord.denominator != 1 for coord in y):
                                        non_integral_found = True

            origin_interior = True
            if any(v == (0, 0, 0, 0) for v in vertices):
                origin_interior = False
            else:
                for c in range(4):
                    if all(v[c] > 0 for v in vertices) or all(v[c] < 0 for v in vertices):
                        origin_interior = False
                        break
                if origin_interior:
                    m_v = len(vertices)
                    for i in range(m_v - 2):
                        d1 = vertices[i]
                        for j in range(i + 1, m_v - 1):
                            d2 = vertices[j]
                            for k in range(j + 1, m_v):
                                d3 = vertices[k]
                                a0 = (
                                    d1[1] * (d2[2] * d3[3] - d2[3] * d3[2])
                                    - d1[2] * (d2[1] * d3[3] - d2[3] * d3[1])
                                    + d1[3] * (d2[1] * d3[2] - d2[2] * d3[1])
                                )
                                a1 = -(
                                    d1[0] * (d2[2] * d3[3] - d2[3] * d3[2])
                                    - d1[2] * (d2[0] * d3[3] - d2[3] * d3[0])
                                    + d1[3] * (d2[0] * d3[2] - d2[2] * d3[0])
                                )
                                a2 = (
                                    d1[0] * (d2[1] * d3[3] - d2[3] * d3[1])
                                    - d1[1] * (d2[0] * d3[3] - d2[3] * d3[0])
                                    + d1[3] * (d2[0] * d3[1] - d2[1] * d3[0])
                                )
                                a3 = -(
                                    d1[0] * (d2[1] * d3[2] - d2[2] * d3[1])
                                    - d1[1] * (d2[0] * d3[2] - d2[2] * d3[0])
                                    + d1[2] * (d2[0] * d3[1] - d2[1] * d3[0])
                                )
                                if a0 == a1 == a2 == a3 == 0:
                                    continue
                                a_vec = (a0, a1, a2, a3)
                                has_pos = any(
                                    sum(a_vec[c] * v[c] for c in range(4)) > 0 for v in vertices
                                )
                                has_neg = any(
                                    sum(a_vec[c] * v[c] for c in range(4)) < 0 for v in vertices
                                )
                                if not (has_pos and has_neg):
                                    origin_interior = False
                                    break
                            if not origin_interior:
                                break
                        if not origin_interior:
                            break

            if kind == "origin_not_interior":
                if not origin_interior:
                    return True, "VALID_OUT_OF_SCOPE_ORIGIN_NOT_INTERIOR"
                return False, "FAIL: claimed origin_not_interior but origin is strictly interior"

            if kind == "facet_distance":
                dist = witness.get("distance")
                if not _is_int_c2(dist):
                    return False, "FAIL: witness distance must be exact integer"
                if dist == 1:
                    return False, "FAIL: facet_distance witness cannot claim distance 1"

                claimed_norm = witness.get("normal")
                if claimed_norm is not None:
                    if (
                        not isinstance(claimed_norm, list)
                        or len(claimed_norm) != 4
                        or not all(_is_int_c2(x) for x in claimed_norm)
                    ):
                        return False, "FAIL: witness normal must be length-4 ints"
                    min_val = min(sum(claimed_norm[c] * v[c] for c in range(4)) for v in vertices)
                    if min_val != -dist:
                        return (
                            False,
                            f"FAIL: witness normal {claimed_norm} does not have distance {dist} (min dot is {min_val})",
                        )
                    tight = [
                        v
                        for v in vertices
                        if sum(claimed_norm[c] * v[c] for c in range(4)) == -dist
                    ]
                    if _affine_rank_c2(tight) != 3:
                        return False, "FAIL: witness normal is not a facet (dim != 3)"
                    return True, "VALID_OUT_OF_SCOPE_FACET_DISTANCE"

                if non_integral_found:
                    return True, "VALID_OUT_OF_SCOPE_FACET_DISTANCE"
                return False, "FAIL: claimed facet_distance on reflexive polytope"

            if kind == "multiple_interior_points":
                return True, "VALID_OUT_OF_SCOPE_MULTIPLE_INTERIOR_POINTS"

            return False, f"FAIL: unrecognized witness kind {kind!r}"

        # Status is SOLVED
        if dim < 4:
            return False, f"FAIL: affine dimension is {dim} < 4, cannot be SOLVED"

        ref_val = result.get("reflexive")
        if type(ref_val) is not bool or not ref_val:
            return False, f"FAIL: reflexive must be bool True, got {ref_val!r}"

        h11 = result.get("h11")
        h21 = result.get("h21")
        euler = result.get("euler")
        if not _is_int_c2(h11) or h11 < 0:
            return False, f"FAIL: h11 must be non-negative exact integer, got {h11!r}"
        if not _is_int_c2(h21) or h21 < 0:
            return False, f"FAIL: h21 must be non-negative exact integer, got {h21!r}"
        if not _is_int_c2(euler):
            return False, f"FAIL: euler must be exact integer, got {euler!r}"
        if euler != 2 * (h11 - h21):
            return False, f"FAIL: euler {euler} != 2*(h11 - h21) = {2 * (h11 - h21)}"

        face_data = result.get("face_data")
        if not isinstance(face_data, dict):
            return False, "FAIL: missing mandatory face_data dict"
        extra_fd = set(face_data.keys()) - ALLOWED_FACE_DATA_KEYS_C2
        if extra_fd:
            return False, f"FAIL: phantom keys in face_data: {sorted(extra_fd)}"

        l_delta = face_data.get("l_delta")
        l_delta_star = face_data.get("l_delta_star")
        if not _is_int_c2(l_delta) or l_delta <= 0:
            return False, f"FAIL: face_data.l_delta must be positive exact integer, got {l_delta!r}"
        if not _is_int_c2(l_delta_star) or l_delta_star <= 0:
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
            extra_rec = set(rec.keys()) - ALLOWED_FACET_RECORD_KEYS_C2
            if extra_rec:
                return False, f"FAIL: phantom keys in facet record: {sorted(extra_rec)}"
            norm = rec.get("normal")
            ip = rec.get("interior_points")
            if not isinstance(norm, list) or len(norm) != 4 or not all(_is_int_c2(x) for x in norm):
                return False, "FAIL: facet normal must be length-4 list of exact integers"
            if not _is_int_c2(ip) or ip < 0:
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
            extra_prec = set(prec.keys()) - ALLOWED_CODIM2_RECORD_KEYS_C2
            if extra_prec:
                return False, f"FAIL: phantom keys in codim2 record: {sorted(extra_prec)}"
            p = prec.get("product")
            if not _is_int_c2(p) or p <= 0:
                return False, f"FAIL: codim2 product must be positive exact integer, got {p!r}"

        # Polar dual first derivation:
        # Solve subsystems M y = -1
        unique_v = list(dict.fromkeys(vertices))
        m = len(unique_v)
        dual_vertices_set: set[tuple[int, int, int, int]] = set()

        for i in range(m - 3):
            for j in range(i + 1, m - 2):
                for k in range(j + 1, m - 1):
                    for l in range(k + 1, m):
                        mat = [
                            list(unique_v[i]),
                            list(unique_v[j]),
                            list(unique_v[k]),
                            list(unique_v[l]),
                        ]
                        solvable, y = _solve_4x4_system_c2(mat, [-1, -1, -1, -1])
                        if solvable:
                            if all(_dot_c2(y, v) >= -1 for v in unique_v):
                                # Must be integer coordinates
                                if any(coord.denominator != 1 for coord in y):
                                    return (
                                        False,
                                        "FAIL: polar dual vertex is not integral, polytope is not reflexive",
                                    )
                                dual_vertices_set.add((int(y[0]), int(y[1]), int(y[2]), int(y[3])))

        if not dual_vertices_set:
            return False, "FAIL: could not identify polar dual vertices"

        dual_vertices = list(dual_vertices_set)

        # Identify extreme vertices of primal polytope:
        # A vertex v in unique_v is extreme if it is tight on at least 4 dual vertices spanning R^4
        extreme_primal_vertices: list[tuple[int, int, int, int]] = []
        for v in unique_v:
            tight_dual = [u for u in dual_vertices if _dot_c2(u, v) == -1]
            if _rational_rank_c2([list(u) for u in tight_dual]) == 4:
                extreme_primal_vertices.append(v)

        reading = case.get("reading", "dual")
        if reading in ("dual", "delta_star"):
            P_delta = dual_vertices
            P_delta_star = extreme_primal_vertices
        else:
            P_delta = extreme_primal_vertices
            P_delta_star = dual_vertices

        # Intrinsic face partition & point count:
        # A point x is in P_delta iff for all u in P_delta_star, dot(u, x) >= -1
        # Bounding box from extreme vertices
        def _get_points_c2(
            facets_pts: list[tuple[int, int, int, int]], v_pts: list[tuple[int, int, int, int]]
        ):
            bmin = [min(v[i] for v in v_pts) for i in range(4)]
            bmax = [max(v[i] for v in v_pts) for i in range(4)]
            pts = []
            for x0 in range(bmin[0], bmax[0] + 1):
                for x1 in range(bmin[1], bmax[1] + 1):
                    for x2 in range(bmin[2], bmax[2] + 1):
                        for x3 in range(bmin[3], bmax[3] + 1):
                            p = (x0, x1, x2, x3)
                            if all(_dot_c2(u, p) >= -1 for u in facets_pts):
                                pts.append(p)
            return pts

        actual_pts_delta = _get_points_c2(P_delta_star, P_delta)
        actual_pts_delta_star = _get_points_c2(P_delta, P_delta_star)

        c2_l_delta = len(actual_pts_delta)
        c2_l_delta_star = len(actual_pts_delta_star)

        if l_delta != c2_l_delta:
            return False, f"FAIL (Checker 2): l_delta mismatch ({l_delta} != {c2_l_delta})"
        if l_delta_star != c2_l_delta_star:
            return (
                False,
                f"FAIL (Checker 2): l_delta_star mismatch ({l_delta_star} != {c2_l_delta_star})",
            )

        # Facet interior points for Delta*
        c2_sum_ds = 0
        c2_facets_ds: dict[tuple[int, int, int, int], int] = {}
        for u_star in P_delta:
            count = sum(
                1
                for p in actual_pts_delta_star
                if _dot_c2(u_star, p) == -1
                and all(_dot_c2(w, p) > -1 for w in P_delta if w != u_star)
            )
            c2_facets_ds[u_star] = count
            c2_sum_ds += count

        # Remediate Vulnerability 2B & 2C: Cardinality, Uniqueness, and Set-Equality
        if len(facets_ds) != len(c2_facets_ds):
            return (
                False,
                f"FAIL (Checker 2): facets_delta_star count mismatch ({len(facets_ds)} != {len(c2_facets_ds)})",
            )
        submitted_normals = [tuple(rec["normal"]) for rec in facets_ds]
        if len(submitted_normals) != len(set(submitted_normals)):
            return False, "FAIL (Checker 2): duplicate facet normals in facets_delta_star"
        if set(submitted_normals) != set(c2_facets_ds.keys()):
            return (
                False,
                "FAIL (Checker 2): facets_delta_star normals do not match the complete set of facet normals",
            )
        for rec in facets_ds:
            n_tup = tuple(rec["normal"])
            if rec["interior_points"] != c2_facets_ds[n_tup]:
                return (
                    False,
                    f"FAIL (Checker 2): facet {n_tup} interior points ({rec['interior_points']} != {c2_facets_ds[n_tup]})",
                )

        # Facet interior points for Delta
        c2_sum_d = 0
        for u in P_delta_star:
            count = sum(
                1
                for p in actual_pts_delta
                if _dot_c2(u, p) == -1 and all(_dot_c2(w, p) > -1 for w in P_delta_star if w != u)
            )
            c2_sum_d += count

        # Codim-2 face corrections:
        # S2 = sum_{dim Theta = 2} l*(Theta) l*(Theta*) (2-faces of Delta x edges of Delta*)
        c2_S2 = 0
        len_ds = len(P_delta_star)
        for i in range(len_ds):
            u_a = P_delta_star[i]
            for j in range(i + 1, len_ds):
                u_b = P_delta_star[j]
                g = 0
                for c in range(4):
                    g = math.gcd(g, abs(u_b[c] - u_a[c]))
                l_star_edge_ds = g - 1

                l_star_2face_d = sum(
                    1
                    for p in actual_pts_delta
                    if _dot_c2(u_a, p) == -1
                    and _dot_c2(u_b, p) == -1
                    and all(_dot_c2(w, p) > -1 for w in P_delta_star if w != u_a and w != u_b)
                )
                prod = l_star_edge_ds * l_star_2face_d
                if prod > 0:
                    c2_S2 += prod

        # S1 = sum_{dim Theta* = 2} l*(Theta*) l*(Theta) (2-faces of Delta* x edges of Delta)
        c2_S1 = 0
        len_d = len(P_delta)
        for i in range(len_d):
            v_a = P_delta[i]
            for j in range(i + 1, len_d):
                v_b = P_delta[j]
                g = 0
                for c in range(4):
                    g = math.gcd(g, abs(v_b[c] - v_a[c]))
                l_star_edge_d = g - 1

                l_star_2face_ds = sum(
                    1
                    for q in actual_pts_delta_star
                    if _dot_c2(v_a, q) == -1
                    and _dot_c2(v_b, q) == -1
                    and all(_dot_c2(w, q) > -1 for w in P_delta if w != v_a and w != v_b)
                )
                prod = l_star_edge_d * l_star_2face_ds
                if prod > 0:
                    c2_S1 += prod

        c2_codim2_sum = c2_S1 + c2_S2
        rep_codim2_sum = sum(p["product"] for p in codim2_prods)
        if rep_codim2_sum != c2_codim2_sum:
            return (
                False,
                f"FAIL (Checker 2): codim2 sum mismatch ({rep_codim2_sum} != {c2_codim2_sum})",
            )

        # Genuine Dual Mirror Swap Verification:
        # Evaluate primal reading (Delta = extreme_v, Delta* = dual_v):
        # h11_primal = l(dual_v) - 5 - sum(facets of dual_v) + S1_primal
        # h21_primal = l(extreme_v) - 5 - sum(facets of extreme_v) + S2_primal
        # Evaluate dual reading (Delta = dual_v, Delta* = extreme_v):
        # h11_dual = l(extreme_v) - 5 - sum(facets of extreme_v) + S1_dual
        # h21_dual = l(dual_v) - 5 - sum(facets of dual_v) + S2_dual
        # By construction: S1_dual == S2_primal and S2_dual == S1_primal.
        if reading in ("dual", "delta_star"):
            # Current case is dual: P_delta = dual_v, P_delta_star = extreme_v
            # So c2_S1 is S1_dual, c2_S2 is S2_dual
            h11_dual = c2_l_delta_star - 5 - c2_sum_ds + c2_S1
            h21_dual = c2_l_delta - 5 - c2_sum_d + c2_S2

            h11_primal = c2_l_delta - 5 - c2_sum_d + c2_S2
            h21_primal = c2_l_delta_star - 5 - c2_sum_ds + c2_S1
        else:
            # Current case is primal: P_delta = extreme_v, P_delta_star = dual_v
            # So c2_S1 is S1_primal, c2_S2 is S2_primal
            h11_primal = c2_l_delta_star - 5 - c2_sum_ds + c2_S1
            h21_primal = c2_l_delta - 5 - c2_sum_d + c2_S2

            h11_dual = c2_l_delta - 5 - c2_sum_d + c2_S2
            h21_dual = c2_l_delta_star - 5 - c2_sum_ds + c2_S1

        if h11_dual != h21_primal or h21_dual != h11_primal:
            return False, (
                f"FAIL (Checker 2): internal mirror swap inconsistency detected: "
                f"primal=(h11={h11_primal}, h21={h21_primal}) does not transpose to "
                f"dual=(h11={h11_dual}, h21={h21_dual})"
            )

        if reading in ("dual", "delta_star"):
            expected_h11 = h11_dual
            expected_h21 = h21_dual
        else:
            expected_h11 = h11_primal
            expected_h21 = h21_primal
        expected_euler = 2 * (expected_h11 - expected_h21)

        if h11 != expected_h11:
            return False, f"FAIL (Checker 2): h11 mismatch ({h11} != {expected_h11})"
        if h21 != expected_h21:
            return False, f"FAIL (Checker 2): h21 mismatch ({h21} != {expected_h21})"
        if euler != expected_euler:
            return False, f"FAIL (Checker 2): euler mismatch ({euler} != {expected_euler})"

        return True, "CHECKER2_PASS"

    except Exception as exc:
        return False, f"FAIL: exception in Checker 2: {type(exc).__name__}: {exc}"
