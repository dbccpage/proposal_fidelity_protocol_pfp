"""2D Cell Complex Topology, Manifold Validation, and Toric Code Degeneracy for C039.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Mapping

try:
    from .f2_algebra import (
        f2_extend_basis,
        f2_invert_matrix,
        f2_nullspace,
        f2_rank,
        f2_rref,
        format_pauli_string,
        popcount,
    )
except (ImportError, ValueError):
    from f2_algebra import (  # type: ignore
        f2_extend_basis,
        f2_invert_matrix,
        f2_nullspace,
        f2_rank,
        format_pauli_string,
        popcount,
    )


def is_strict_int(val: Any) -> bool:
    """Strict check for integer, rejecting boolean."""
    return type(val) is int and not isinstance(val, bool)


def parse_and_validate_cell_complex(
    case: Mapping[str, Any],
) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    """Parses and validates a 2D cell complex, checking manifold topology and bounds.

    Returns:
        (status, extra, complex_data)
        - status == "UNKNOWN": extra={"refusal_code": ...}
        - status == "OUT_OF_SCOPE": extra={"witness": ...}
        - status == "SOLVED": complex_data={...}
    """
    if not isinstance(case, Mapping):
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    # Check for presence of complex representation
    # Format A: explicit 'vertices', 'edges', 'faces'
    # Format B: 'faces' as edge walks, 'edges' as endpoint pairs
    vertices_raw = case.get("vertices")
    edges_raw = case.get("edges")
    faces_raw = case.get("faces")

    if faces_raw is None or not isinstance(faces_raw, list) or len(faces_raw) == 0:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    # Parse vertices
    vertex_map: dict[Any, int] = {}
    if vertices_raw is not None:
        if not isinstance(vertices_raw, list):
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
        for v in vertices_raw:
            if isinstance(v, bool):
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
            if v not in vertex_map:
                vertex_map[v] = len(vertex_map)

    # Parse edges
    # Each edge e has tail u and head v
    edge_list: list[tuple[int, int]] = []
    edge_map: dict[Any, int] = {}

    if edges_raw is not None:
        if not isinstance(edges_raw, list):
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
        for idx, e in enumerate(edges_raw):
            if isinstance(e, (list, tuple)) and len(e) == 2:
                u_raw, v_raw = e[0], e[1]
                e_id: Any = idx
            elif isinstance(e, dict):
                e_id = e.get("id", idx)
                if (
                    "endpoints" in e
                    and isinstance(e["endpoints"], (list, tuple))
                    and len(e["endpoints"]) == 2
                ):
                    u_raw, v_raw = e["endpoints"][0], e["endpoints"][1]
                elif "u" in e and "v" in e:
                    u_raw, v_raw = e["u"], e["v"]
                else:
                    return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
            else:
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

            if isinstance(u_raw, bool) or isinstance(v_raw, bool):
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

            if u_raw not in vertex_map:
                vertex_map[u_raw] = len(vertex_map)
            if v_raw not in vertex_map:
                vertex_map[v_raw] = len(vertex_map)

            u = vertex_map[u_raw]
            v = vertex_map[v_raw]
            edge_map[e_id] = len(edge_list)
            edge_list.append((u, v))

    # Parse faces
    # Each face is a closed edge walk: list of steps (e_idx, direction)
    face_walks: list[list[tuple[int, int]]] = []

    for f_idx, face in enumerate(faces_raw):
        if not isinstance(face, list) or len(face) == 0:
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

        parsed_walk: list[tuple[int, int]] = []
        for step in face:
            if isinstance(step, (list, tuple)) and len(step) == 2:
                e_ref, d_ref = step[0], step[1]
                if isinstance(d_ref, bool) or isinstance(e_ref, bool):
                    return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
                if d_ref in (1, "+", "+1"):
                    direction = 1
                elif d_ref in (-1, "-", "-1"):
                    direction = -1
                else:
                    return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

                if e_ref in edge_map:
                    e_idx = edge_map[e_ref]
                elif is_strict_int(e_ref) and 0 <= e_ref < len(edge_list):
                    e_idx = e_ref
                else:
                    return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

                parsed_walk.append((e_idx, direction))

            elif isinstance(step, dict):
                e_ref = step.get("edge")
                d_ref = step.get("direction", step.get("dir", 1))
                if isinstance(d_ref, bool) or isinstance(e_ref, bool):
                    return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
                direction = (
                    1 if d_ref in (1, "+", "+1") else (-1 if d_ref in (-1, "-", "-1") else 0)
                )
                if direction == 0:
                    return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

                if e_ref in edge_map:
                    e_idx = edge_map[e_ref]
                elif is_strict_int(e_ref) and 0 <= e_ref < len(edge_list):
                    e_idx = e_ref
                else:
                    return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

                parsed_walk.append((e_idx, direction))

            elif isinstance(step, str):
                # Signed string e.g. "+e0", "-e0", "e0"
                s = step.strip()
                if s.startswith("-"):
                    direction = -1
                    e_name = s[1:]
                elif s.startswith("+"):
                    direction = 1
                    e_name = s[1:]
                else:
                    direction = 1
                    e_name = s

                if e_name in edge_map:
                    e_idx = edge_map[e_name]
                else:
                    try:
                        e_int = int(e_name)
                        if e_int in edge_map:
                            e_idx = edge_map[e_int]
                        elif 0 <= e_int < len(edge_list):
                            e_idx = e_int
                        else:
                            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
                    except ValueError:
                        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

                parsed_walk.append((e_idx, direction))

            elif is_strict_int(step):
                # Signed 1-indexed int or 0-indexed int
                if step > 0:
                    e_idx = step - 1
                    direction = 1
                elif step < 0:
                    e_idx = abs(step) - 1
                    direction = -1
                else:
                    return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

                if not (0 <= e_idx < len(edge_list)):
                    return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
                parsed_walk.append((e_idx, direction))

            else:
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

        face_walks.append(parsed_walk)

    V = len(vertex_map)
    E = len(edge_list)
    F = len(face_walks)

    # Bound check: E <= 300
    if E > 300:
        return "UNKNOWN", {"refusal_code": "TOO_MANY_EDGES"}, None

    # 1. Edge-in-two-faces check
    # Every edge must appear exactly twice across all face boundary walks
    edge_traversal_count: dict[int, int] = defaultdict(int)
    for walk in face_walks:
        for e_idx, _ in walk:
            edge_traversal_count[e_idx] += 1

    for e in range(E):
        count = edge_traversal_count[e]
        if count != 2:
            witness = {
                "kind": "edge_not_in_two_faces",
                "edge": e,
                "count": count,
            }
            return "OUT_OF_SCOPE", {"witness": witness}, None

    # 2. Walk continuity and Vertex link topology
    half_edges_at_vertex: dict[int, set[tuple[int, int]]] = defaultdict(set)
    for e_idx, (u, v) in enumerate(edge_list):
        half_edges_at_vertex[u].add((e_idx, 0))
        half_edges_at_vertex[v].add((e_idx, 1))

    corners_at_vertex: dict[int, list[tuple[tuple[int, int], tuple[int, int]]]] = defaultdict(list)

    for walk in face_walks:
        m = len(walk)
        for i in range(m):
            e_curr, d_curr = walk[i]
            e_next, d_next = walk[(i + 1) % m]

            # Determine where step i enters
            u_curr, v_curr = edge_list[e_curr]
            if d_curr == 1:
                arrival_vertex = v_curr
                arrival_half_edge = (e_curr, 1)
            else:
                arrival_vertex = u_curr
                arrival_half_edge = (e_curr, 0)

            # Determine where step i+1 leaves
            u_next, v_next = edge_list[e_next]
            if d_next == 1:
                departure_vertex = u_next
                departure_half_edge = (e_next, 0)
            else:
                departure_vertex = v_next
                departure_half_edge = (e_next, 1)

            if arrival_vertex != departure_vertex:
                # Discontinuous face boundary walk
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

            v = arrival_vertex
            corners_at_vertex[v].append((arrival_half_edge, departure_half_edge))

    # Validate link of each vertex
    for v in range(V):
        half_edges = half_edges_at_vertex[v]
        corners = corners_at_vertex[v]

        # Build link graph
        link_adj: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
        for h1, h2 in corners:
            link_adj[h1].append(h2)
            link_adj[h2].append(h1)

        # Every half-edge at v must have degree 2
        for h in half_edges:
            if len(link_adj[h]) != 2:
                witness = {"kind": "vertex_link_not_a_circle", "vertex": v}
                return "OUT_OF_SCOPE", {"witness": witness}, None

        if len(half_edges) == 0:
            witness = {"kind": "vertex_link_not_a_circle", "vertex": v}
            return "OUT_OF_SCOPE", {"witness": witness}, None

        # Link must be a single connected cycle
        start = next(iter(half_edges))
        visited: set[tuple[int, int]] = set()
        q: deque[tuple[int, int]] = deque([start])
        visited.add(start)
        while q:
            curr = q.popleft()
            for nbr in link_adj[curr]:
                if nbr not in visited:
                    visited.add(nbr)
                    q.append(nbr)

        if len(visited) != len(half_edges):
            witness = {"kind": "vertex_link_not_a_circle", "vertex": v}
            return "OUT_OF_SCOPE", {"witness": witness}, None

    # 3. Surface connectivity
    face_edge_map: dict[int, list[int]] = defaultdict(list)
    for f_idx, walk in enumerate(face_walks):
        for e_idx, _ in walk:
            face_edge_map[e_idx].append(f_idx)

    face_adj: dict[int, set[int]] = defaultdict(set)
    for e_idx, f_indices in face_edge_map.items():
        if len(f_indices) == 2:
            f1, f2 = f_indices[0], f_indices[1]
            if f1 != f2:
                face_adj[f1].add(f2)
                face_adj[f2].add(f1)

    visited_faces: set[int] = set()
    q_face: deque[int] = deque([0])
    visited_faces.add(0)
    while q_face:
        curr = q_face.popleft()
        for nbr in face_adj[curr]:
            if nbr not in visited_faces:
                visited_faces.add(nbr)
                q_face.append(nbr)

    if len(visited_faces) != F:
        comp_count = 1
        unvisited = set(range(F)) - visited_faces
        while unvisited:
            comp_count += 1
            st = min(unvisited)
            q_c = deque([st])
            unvisited.remove(st)
            while q_c:
                c_curr = q_c.popleft()
                for nbr in face_adj[c_curr]:
                    if nbr in unvisited:
                        unvisited.remove(nbr)
                        q_c.append(nbr)
        witness = {"kind": "surface_disconnected", "components": comp_count}
        return "OUT_OF_SCOPE", {"witness": witness}, None

    return (
        "SOLVED",
        None,
        {
            "V": V,
            "E": E,
            "F": F,
            "edge_list": edge_list,
            "face_walks": face_walks,
        },
    )


def solve_degeneracy_query(
    case: Mapping[str, Any],
) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    """Solves the degeneracy query for a closed connected 2D cell complex.

    Returns:
        (status, extra, solution)
    """
    status, extra, complex_data = parse_and_validate_cell_complex(case)
    if status != "SOLVED":
        return status, extra, None

    assert complex_data is not None
    V = complex_data["V"]
    E = complex_data["E"]
    F = complex_data["F"]
    edge_list = complex_data["edge_list"]
    face_walks = complex_data["face_walks"]

    # 1. Build Star operators A_v as F2 bitmasks (V x E)
    # A_{v, e} = (number of edge-ends of e at v) mod 2
    star_rows = [0] * V
    for e_idx, (u, w) in enumerate(edge_list):
        if u != w:
            star_rows[u] ^= 1 << e_idx
            star_rows[w] ^= 1 << e_idx

    # 2. Build Plaquette operators B_p as F2 bitmasks (F x E)
    # B_{p, e} = (number of times face p traverses e) mod 2
    plaquette_rows = [0] * F
    for p_idx, walk in enumerate(face_walks):
        e_counts: dict[int, int] = defaultdict(int)
        for e_idx, _ in walk:
            e_counts[e_idx] += 1
        for e_idx, cnt in e_counts.items():
            if cnt % 2 == 1:
                plaquette_rows[p_idx] ^= 1 << e_idx

    # 3. Compute ranks
    rank_star = f2_rank(star_rows, E)
    rank_plaquette = f2_rank(plaquette_rows, E)

    euler = V - E + F
    k = E - rank_star - rank_plaquette
    gsd = 1 << k

    # 4. Construct canonical logical operators
    if k == 0:
        logicals = {"z": [], "x": []}
    else:
        # ker(A) basis
        ker_A = f2_nullspace(star_rows, E)
        # Extend row_span(B) with vectors from ker_A
        z_cands, _ = f2_extend_basis(plaquette_rows, ker_A, E)
        if len(z_cands) != k:
            raise RuntimeError(f"Expected {k} logical Z generators, found {len(z_cands)}")

        # ker(B) basis
        ker_B = f2_nullspace(plaquette_rows, E)
        # Extend row_span(A) with vectors from ker_B
        x_cands, _ = f2_extend_basis(star_rows, ker_B, E)
        if len(x_cands) != k:
            raise RuntimeError(f"Expected {k} logical X generators, found {len(x_cands)}")

        # Intersection matrix M_ij = popcount(z_i & x_j) mod 2
        M_rows = []
        for i in range(k):
            row_val = 0
            for j in range(k):
                dot = popcount(z_cands[i] & x_cands[j]) % 2
                if dot:
                    row_val |= 1 << j
            M_rows.append(row_val)

        # Invert M over F2
        M_inv = f2_invert_matrix(M_rows, k)

        # Canonical x operators: x'_l = sum_j (M_inv)_{jl} * x_cands[j]
        canonical_x = []
        for l in range(k):
            x_l = 0
            for j in range(k):
                coeff = (M_inv[j] >> l) & 1
                if coeff:
                    x_l ^= x_cands[j]
            canonical_x.append(x_l)

        # Verify canonical symplectic commutation: z_i . x'_l = delta_{il}
        for i in range(k):
            for l in range(k):
                expected = 1 if i == l else 0
                actual = popcount(z_cands[i] & canonical_x[l]) % 2
                assert actual == expected, f"Symplectic commutation failed at ({i}, {l})"

        # Format as Pauli strings
        z_strings = [format_pauli_string(z, "Z", E) for z in z_cands]
        x_strings = [format_pauli_string(x, "X", E) for x in canonical_x]
        logicals = {"z": z_strings, "x": x_strings}

    solution = {
        "V": V,
        "E": E,
        "F": F,
        "euler": euler,
        "rank_star": rank_star,
        "rank_plaquette": rank_plaquette,
        "k": k,
        "gsd": gsd,
        "logicals": logicals,
    }

    return "SOLVED", None, solution
