"""Pure Python stdlib 4D Convex Geometry and Batyrev Calabi-Yau Hodge Engine.

Zero external dependencies: strictly standard library primitives.
Exact integer and rational arithmetic for 4D reflexive lattice polytopes.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping, Optional, Sequence


def is_exact_int(val: Any) -> bool:
    """Returns True if and only if val is an int and strictly not a boolean."""
    return type(val) is int and not isinstance(val, bool)


def gcd_list(values: Sequence[int]) -> int:
    """Computes greatest common divisor of an arbitrary sequence of integers."""
    g = 0
    for v in values:
        g = math.gcd(g, abs(v))
    return g


def det3(r0: Sequence[int], r1: Sequence[int], r2: Sequence[int]) -> int:
    """Exact integer 3x3 determinant."""
    return (
        r0[0] * (r1[1] * r2[2] - r1[2] * r2[1])
        - r0[1] * (r1[0] * r2[2] - r1[2] * r2[0])
        + r0[2] * (r1[0] * r2[1] - r1[1] * r2[0])
    )


def det4(r0: Sequence[int], r1: Sequence[int], r2: Sequence[int], r3: Sequence[int]) -> int:
    """Exact integer 4x4 determinant via cofactor expansion along row 0."""
    m0 = det3((r1[1], r1[2], r1[3]), (r2[1], r2[2], r2[3]), (r3[1], r3[2], r3[3]))
    m1 = det3((r1[0], r1[2], r1[3]), (r2[0], r2[2], r2[3]), (r3[0], r3[2], r3[3]))
    m2 = det3((r1[0], r1[1], r1[3]), (r2[0], r2[1], r2[3]), (r3[0], r3[1], r3[3]))
    m3 = det3((r1[0], r1[1], r1[2]), (r2[0], r2[1], r2[2]), (r3[0], r3[1], r3[2]))
    return r0[0] * m0 - r0[1] * m1 + r0[2] * m2 - r0[3] * m3


def cross4(
    d1: tuple[int, int, int, int],
    d2: tuple[int, int, int, int],
    d3: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    """Computes exact 4D cross product of three 4-vectors."""
    a0 = det3((d1[1], d1[2], d1[3]), (d2[1], d2[2], d2[3]), (d3[1], d3[2], d3[3]))
    a1 = -det3((d1[0], d1[2], d1[3]), (d2[0], d2[2], d2[3]), (d3[0], d3[2], d3[3]))
    a2 = det3((d1[0], d1[1], d1[3]), (d2[0], d2[1], d2[3]), (d3[0], d3[1], d3[3]))
    a3 = -det3((d1[0], d1[1], d1[2]), (d2[0], d2[1], d2[2]), (d3[0], d3[1], d3[2]))
    return (a0, a1, a2, a3)


def dot4(u: Sequence[int], v: Sequence[int]) -> int:
    """Exact integer dot product of two 4-vectors."""
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2] + u[3] * v[3]


def compute_linear_rank(vectors: Sequence[Sequence[int]]) -> int:
    """Computes exact linear rank of a list of integer vectors using Fraction Gaussian elimination."""
    if not vectors:
        return 0
    mat = [[Fraction(x) for x in v] for v in vectors]
    num_rows = len(mat)
    num_cols = len(mat[0])
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


def compute_affine_dimension(points: Sequence[Sequence[int]]) -> int:
    """Computes exact affine dimension of points using Gaussian elimination."""
    if len(points) <= 1:
        return 0
    p0 = points[0]
    diffs = [[p[j] - p0[j] for j in range(4)] for p in points[1:]]
    return compute_linear_rank(diffs)


def validate_input_case(
    case: Mapping[str, Any],
) -> tuple[str, Optional[str], Optional[dict[str, Any]], Optional[list[tuple[int, int, int, int]]]]:
    """Validates input case against C034 schema and constraints.

    Returns:
        (status, refusal_code, witness, vertices)
        If valid: ("OK", None, None, vertices_list)
        If malformed or out of bounds: ("UNKNOWN", refusal_code, None, None)
        If lower-dimensional: ("OUT_OF_SCOPE", None, witness, None)
    """
    if not isinstance(case, Mapping):
        return "UNKNOWN", "MALFORMED_CASE_STRUCTURE", None, None

    cid = case.get("case_id") or case.get("id")
    if not cid or not isinstance(cid, str):
        return "UNKNOWN", "MALFORMED_CASE_STRUCTURE", None, None

    reading = case.get("reading")
    if reading not in ("primal", "dual", "delta", "delta_star"):
        return "UNKNOWN", "INVALID_READING_SPECIFIER", None, None

    raw_vertices = case.get("vertices")
    if not isinstance(raw_vertices, list) or len(raw_vertices) == 0:
        return "UNKNOWN", "MALFORMED_CASE_STRUCTURE", None, None

    if len(raw_vertices) > 40:
        return "UNKNOWN", "TOO_MANY_VERTICES", None, None

    vertices: list[tuple[int, int, int, int]] = []
    for pt in raw_vertices:
        if not isinstance(pt, (list, tuple)) or len(pt) != 4:
            return "UNKNOWN", "MALFORMED_CASE_STRUCTURE", None, None
        for coord in pt:
            if not is_exact_int(coord):
                return "UNKNOWN", "MALFORMED_CASE_STRUCTURE", None, None
            if abs(coord) > 30:
                return "UNKNOWN", "COORDINATES_OUT_OF_BOUNDS", None, None
        vertices.append((pt[0], pt[1], pt[2], pt[3]))

    aff_dim = compute_affine_dimension(vertices)
    if aff_dim < 4:
        return (
            "OUT_OF_SCOPE",
            None,
            {"kind": "dimension_deficient", "affine_dimension": aff_dim},
            None,
        )

    return "OK", None, None, vertices


def enumerate_facets(
    vertices: list[tuple[int, int, int, int]],
) -> tuple[list[tuple[tuple[int, int, int, int], int]], list[tuple[int, int, int, int]]]:
    """Enumerates all 3-facets of conv(vertices) and extracts extreme vertices.

    Returns:
        (facets, extreme_vertices)
        where each facet is (primitive_inward_normal, b) such that <normal, x> >= b.
    """
    len(vertices)
    # Deduplicate vertices while preserving order
    unique_v = list(dict.fromkeys(vertices))
    m = len(unique_v)

    facets_dict: dict[tuple[tuple[int, int, int, int], int], set[int]] = {}

    # Check 4-tuples
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

                    a = cross4(d1, d2, d3)
                    if a == (0, 0, 0, 0):
                        continue

                    g = gcd_list(a)
                    a = (a[0] // g, a[1] // g, a[2] // g, a[3] // g)
                    b = dot4(a, p1)

                    # Check supporting hyperplane condition
                    has_pos = False
                    has_neg = False
                    for v in unique_v:
                        val = dot4(a, v) - b
                        if val > 0:
                            has_pos = True
                            if has_neg:
                                break
                        elif val < 0:
                            has_neg = True
                            if has_pos:
                                break

                    if has_pos and has_neg:
                        continue  # intersects interior

                    # Orient inward so dot(a, v) >= b
                    if has_neg and not has_pos:
                        a = (-a[0], -a[1], -a[2], -a[3])
                        b = -b

                    facet_key = (a, b)
                    if facet_key not in facets_dict:
                        # Find all vertices on this hyperplane
                        on_facet = {idx for idx, v in enumerate(unique_v) if dot4(a, v) == b}
                        if len(on_facet) >= 4:
                            facet_pts = [unique_v[idx] for idx in on_facet]
                            if compute_affine_dimension(facet_pts) == 3:
                                facets_dict[facet_key] = on_facet

    facets = list(facets_dict.keys())

    # Extract extreme vertices: vertices contained in facets whose normals span R^4 (rank 4)
    extreme_vertices: list[tuple[int, int, int, int]] = []
    for idx, v in enumerate(unique_v):
        incident_normals = [facet[0] for facet, on_v in facets_dict.items() if idx in on_v]
        if compute_linear_rank(incident_normals) == 4:
            extreme_vertices.append(v)

    return facets, extreme_vertices


def count_lattice_points_4d(
    facets: list[tuple[tuple[int, int, int, int], int]],
    extreme_vertices: list[tuple[int, int, int, int]],
) -> list[tuple[int, int, int, int]]:
    """Counts and enumerates lattice points in 4D polytope using coordinate slicer."""
    bmin = [min(v[i] for v in extreme_vertices) for i in range(4)]
    bmax = [max(v[i] for v in extreme_vertices) for i in range(4)]

    points: list[tuple[int, int, int, int]] = []

    for x0 in range(bmin[0], bmax[0] + 1):
        feasible_x0 = True
        for (u0, u1, u2, u3), b in facets:
            max_rem = sum(
                max(u * bmin[j], u * bmax[j]) for j, u in enumerate((u1, u2, u3), start=1)
            )
            if u0 * x0 + max_rem < b:
                feasible_x0 = False
                break
        if not feasible_x0:
            continue

        for x1 in range(bmin[1], bmax[1] + 1):
            feasible_x1 = True
            for (u0, u1, u2, u3), b in facets:
                max_rem = sum(
                    max(u * bmin[j], u * bmax[j]) for j, u in enumerate((u2, u3), start=2)
                )
                if u0 * x0 + u1 * x1 + max_rem < b:
                    feasible_x1 = False
                    break
            if not feasible_x1:
                continue

            for x2 in range(bmin[2], bmax[2] + 1):
                low3 = bmin[3]
                high3 = bmax[3]
                feasible_x2 = True
                for (u0, u1, u2, u3), b in facets:
                    lhs_012 = u0 * x0 + u1 * x1 + u2 * x2
                    if u3 > 0:
                        bound = math.ceil((b - lhs_012) / u3)
                        if bound > low3:
                            low3 = bound
                    elif u3 < 0:
                        bound = math.floor((lhs_012 - b) / (-u3))
                        if bound < high3:
                            high3 = bound
                    else:
                        if lhs_012 < b:
                            feasible_x2 = False
                            break
                if not feasible_x2 or low3 > high3:
                    continue

                for x3 in range(low3, high3 + 1):
                    # Final check on all facets
                    pt = (x0, x1, x2, x3)
                    if all(dot4(u, pt) >= b for u, b in facets):
                        points.append(pt)

    return points


def solve_calabi_yau_polytope(case: Any) -> dict[str, Any]:
    """Core Batyrev Calabi-Yau Hodge solver."""
    cid = (
        str(case.get("case_id") or case.get("id") or "unknown_case")
        if isinstance(case, Mapping)
        else "unknown_case"
    )
    status, refusal_code, witness, vertices = validate_input_case(case)

    if status == "UNKNOWN":
        return {"id": cid, "status": "UNKNOWN", "refusal_code": refusal_code}
    if status == "OUT_OF_SCOPE":
        return {"id": cid, "status": "OUT_OF_SCOPE", "witness": witness}

    assert vertices is not None

    # Step 1: Enumerate facets of input polytope
    facets, extreme_vertices = enumerate_facets(vertices)

    # Step 2: Check strict origin interiority (<u, 0> = 0 > b => b < 0)
    for (u0, u1, u2, u3), b in facets:
        if b >= 0:
            return {
                "id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {
                    "kind": "origin_not_interior",
                    "reason": "origin not in strict interior",
                },
            }

    # Step 3: Check reflexivity (all facet distances d = -b == 1)
    for u, b in facets:
        dist = -b
        if dist != 1:
            return {
                "id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "facet_distance", "normal": list(u), "distance": dist},
            }

    # Polytope is reflexive! Form primal and dual
    # Let P_in be the input polytope.
    # Vertices of P_in dual are the facet normals of P_in:
    dual_vertices = [u for u, b in facets]
    [(v, -1) for v in extreme_vertices]
    [(u, -1) for u in dual_vertices]

    reading = case.get("reading", "dual")
    if reading in ("dual", "delta_star"):
        # Input was Delta*. So Delta* = P_in, Delta = P_in*
        delta_star_verts = extreme_vertices
        delta_star_facets = [(u, -1) for u in dual_vertices]
        delta_verts = dual_vertices
        delta_facets = [(v, -1) for v in extreme_vertices]
    else:
        # Input was Delta. So Delta = P_in, Delta* = P_in*
        delta_verts = extreme_vertices
        delta_facets = [(u, -1) for u in dual_vertices]
        delta_star_verts = dual_vertices
        delta_star_facets = [(v, -1) for v in extreme_vertices]

    # Enumerate lattice points in Delta and Delta*
    l_pts_delta = count_lattice_points_4d(delta_facets, delta_verts)
    l_pts_delta_star = count_lattice_points_4d(delta_star_facets, delta_star_verts)

    # Check for multiple interior points
    int_pts_delta = [p for p in l_pts_delta if all(dot4(u, p) > -1 for u, _ in delta_facets)]
    if len(int_pts_delta) > 1:
        extra_pt = next(p for p in int_pts_delta if p != (0, 0, 0, 0))
        return {
            "id": cid,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "multiple_interior_points", "point": list(extra_pt)},
        }

    l_delta = len(l_pts_delta)
    l_delta_star = len(l_pts_delta_star)

    # Codimension-1 facet interior points of Delta* (dim 3 facets of Delta*, dual to vertices of Delta)
    facets_delta_star_records: list[dict[str, Any]] = []
    sum_l_star_theta_star_codim1 = 0

    for u_star, _ in delta_star_facets:
        # A point p in Delta* is in relint(facet) iff <u_star, p> == -1 and <w, p> > -1 for all w != u_star
        interior_count = sum(
            1
            for p in l_pts_delta_star
            if dot4(u_star, p) == -1
            and all(dot4(w, p) > -1 for w, _ in delta_star_facets if w != u_star)
        )
        facets_delta_star_records.append(
            {
                "normal": list(u_star),
                "interior_points": interior_count,
            }
        )
        sum_l_star_theta_star_codim1 += interior_count

    # Codimension-1 facet interior points of Delta (dim 3 facets of Delta, dual to vertices of Delta*)
    sum_l_star_theta_codim1 = 0
    for u, _ in delta_facets:
        interior_count = sum(
            1
            for p in l_pts_delta
            if dot4(u, p) == -1 and all(dot4(w, p) > -1 for w, _ in delta_facets if w != u)
        )
        sum_l_star_theta_codim1 += interior_count

    # Codimension-2 face pairings (Batyrev 1994, Theorem 4.4.4):
    #
    # S1 (for h11): Sum over 2-faces Theta* of Delta* and dual edges Theta of Delta.
    # An edge Theta of Delta connects two vertices v_a, v_b of Delta.
    # Its relative interior lattice points: l*(Theta) = gcd(v_b - v_a) - 1.
    # The dual 2-face Theta* of Delta* has relative interior points u in Delta* satisfying:
    # <u, v_a> == -1, <u, v_b> == -1, and <u, v_m> > -1 for all other v_m in delta_verts.
    s1 = 0
    codim2_products_delta: list[dict[str, Any]] = []
    m_verts_delta = len(delta_verts)
    for i in range(m_verts_delta):
        v_a = delta_verts[i]
        for j in range(i + 1, m_verts_delta):
            v_b = delta_verts[j]
            diff = (v_b[0] - v_a[0], v_b[1] - v_a[1], v_b[2] - v_a[2], v_b[3] - v_a[3])
            g = gcd_list(diff)
            l_star_theta = g - 1
            if l_star_theta <= 0:
                continue

            l_star_theta_star = sum(
                1
                for u in l_pts_delta_star
                if dot4(u, v_a) == -1
                and dot4(u, v_b) == -1
                and all(dot4(u, v_m) > -1 for v_m in delta_verts if v_m != v_a and v_m != v_b)
            )

            prod = l_star_theta * l_star_theta_star
            if prod > 0:
                s1 += prod
                codim2_products_delta.append(
                    {
                        "l_star_theta": l_star_theta,
                        "l_star_theta_star": l_star_theta_star,
                        "product": prod,
                    }
                )

    # S2 (for h21): Sum over 2-faces Theta of Delta and dual edges Theta* of Delta*.
    # An edge Theta* of Delta* connects two vertices u_a, u_b of Delta*.
    # Its relative interior lattice points: l*(Theta*) = gcd(u_b - u_a) - 1.
    # The dual 2-face Theta of Delta has relative interior points p in Delta satisfying:
    # <u_a, p> == -1, <u_b, p> == -1, and <w, p> > -1 for all other w in delta_star_verts.
    s2 = 0
    codim2_products_delta_star: list[dict[str, Any]] = []
    m_verts_star = len(delta_star_verts)
    for i in range(m_verts_star):
        u_a = delta_star_verts[i]
        for j in range(i + 1, m_verts_star):
            u_b = delta_star_verts[j]
            diff = (u_b[0] - u_a[0], u_b[1] - u_a[1], u_b[2] - u_a[2], u_b[3] - u_a[3])
            g = gcd_list(diff)
            l_star_theta_star = g - 1
            if l_star_theta_star <= 0:
                continue

            l_star_theta = sum(
                1
                for p in l_pts_delta
                if dot4(u_a, p) == -1
                and dot4(u_b, p) == -1
                and all(dot4(w, p) > -1 for w in delta_star_verts if w != u_a and w != u_b)
            )

            prod = l_star_theta_star * l_star_theta
            if prod > 0:
                s2 += prod
                codim2_products_delta_star.append(
                    {
                        "l_star_theta": l_star_theta,
                        "l_star_theta_star": l_star_theta_star,
                        "product": prod,
                    }
                )

    # Batyrev's formulas:
    # h11 = l(Delta*) - 5 - sum_{codim theta* = 1} l*(theta*) + S1
    # h21 = l(Delta) - 5 - sum_{codim theta = 1} l*(theta) + S2
    # euler = 2 * (h11 - h21)
    h11 = l_delta_star - 5 - sum_l_star_theta_star_codim1 + s1
    h21 = l_delta - 5 - sum_l_star_theta_codim1 + s2
    euler = 2 * (h11 - h21)

    return {
        "id": cid,
        "status": "SOLVED",
        "reflexive": True,
        "h11": h11,
        "h21": h21,
        "euler": euler,
        "face_data": {
            "l_delta": l_delta,
            "l_delta_star": l_delta_star,
            "facets_delta_star": facets_delta_star_records,
            "codim2_products_delta": codim2_products_delta,
            "codim2_products_delta_star": codim2_products_delta_star,
            "codim2_products": codim2_products_delta + codim2_products_delta_star,
        },
    }
