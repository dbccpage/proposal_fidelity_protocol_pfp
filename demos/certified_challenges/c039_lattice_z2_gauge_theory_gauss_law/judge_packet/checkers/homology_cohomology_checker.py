"""Checker 2: Cellular Homology, Dual Pairing & Dense Hilbert Space Certifier for C039.

Implements independent homological and cohomological verification over Z_2:
- Cellular chain complex C_2 -d2-> C_1 -d1-> C_0 over Z_2
- Boundary operator rank, Betti numbers b_1 = 2 - chi, b_0 = 1, b_2 = 1
- 1-cycle condition d_1(Z) = 0, 1-cocycle condition d_2^T(X) = 0
- Transversal dual intersection pairing <Z_i, X_j> = delta_{ij} mod 2
- Image exclusion: Z_i not in im(d_2) (non-boundary), X_j not in im(d_1^T) (non-coboundary)
- Independent DFS spanning tree cycle space dimension E - V + 1 for graphs
- Dense exact Hilbert space ground space dimension over Q for small complexes (E <= 10)
- Anti-bypass defense layers: strict int validation, closed schema whitelisting, unwarranted refusal check

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping


def _c2_is_int(val: Any) -> bool:
    """Strict check for int, rejecting bool."""
    return type(val) is int and not isinstance(val, bool)


def _c2_gauss_jordan_gf2(matrix: list[list[int]]) -> tuple[int, list[list[int]]]:
    """Computes GF(2) rank and reduced row echelon form (RREF)."""
    if not matrix or not matrix[0]:
        return 0, []
    mat = [row[:] for row in matrix]
    rows = len(mat)
    cols = len(mat[0])
    rank = 0
    col = 0
    for r in range(rows):
        while col < cols:
            piv = -1
            for i in range(r, rows):
                if mat[i][col] == 1:
                    piv = i
                    break
            if piv != -1:
                mat[r], mat[piv] = mat[piv], mat[r]
                for i in range(rows):
                    if i != r and mat[i][col] == 1:
                        for j in range(col, cols):
                            mat[i][j] ^= mat[r][j]
                rank += 1
                col += 1
                break
            col += 1
        if col >= cols:
            break
    return rank, mat


def _c2_in_image_gf2(target_vec: list[int], col_basis: list[list[int]]) -> bool:
    """Tests if target_vec is in the column span of col_basis over GF(2)."""
    if not col_basis:
        return all(x == 0 for x in target_vec)
    cols = len(col_basis)
    rows = len(target_vec)
    mat = [[col_basis[c][r] for c in range(cols)] for r in range(rows)]
    rank_orig, _ = _c2_gauss_jordan_gf2(mat)
    for r in range(rows):
        mat[r].append(target_vec[r])
    rank_aug, _ = _c2_gauss_jordan_gf2(mat)
    return rank_orig == rank_aug


def _c2_dfs_spanning_tree_cycle_rank(v_count: int, edges: list[list[int]]) -> tuple[int, bool]:
    """Computes cycle rank (E - V + 1) and connectivity via DFS spanning tree."""
    adj: dict[int, list[tuple[int, int]]] = {i: [] for i in range(v_count)}
    for e_idx, e in enumerate(edges):
        u, v = e[0], e[1]
        adj[u].append((v, e_idx))
        adj[v].append((u, e_idx))

    visited = set()
    tree_edges = 0

    def dfs(node: int, parent_edge: int) -> None:
        nonlocal tree_edges
        visited.add(node)
        for nbr, edge_id in adj[node]:
            if edge_id == parent_edge:
                continue
            if nbr not in visited:
                tree_edges += 1
                dfs(nbr, edge_id)

    if v_count > 0:
        dfs(0, -1)

    is_connected = len(visited) == v_count
    cycle_rank = len(edges) - tree_edges
    return cycle_rank, is_connected


def _c2_exact_dense_hilbert_space_gsd(
    v_count: int,
    edges: list[list[int]],
    faces: list[Any],
) -> int:
    """Dense exact Hilbert space ground space dimension check for small complexes (E <= 10)."""
    num_qubits = len(edges)
    dim = 1 << num_qubits

    av_masks = []
    for v in range(v_count):
        mask = 0
        for e_idx, e in enumerate(edges):
            ends = (1 if e[0] == v else 0) + (1 if e[1] == v else 0)
            if ends % 2 == 1:
                mask |= 1 << e_idx
        if mask != 0:
            av_masks.append(mask)

    bp_masks = []
    for f in faces:
        mask = 0
        for item in f:
            e_idx = (
                item
                if _c2_is_int(item)
                else (item[0] if isinstance(item, (list, tuple)) else item.get("edge"))
            )
            mask ^= 1 << e_idx
        if mask != 0:
            bp_masks.append(mask)

    flat_states = []
    for z in range(dim):
        is_flat = True
        for bp in bp_masks:
            bit_count = (z & bp).bit_count()
            if bit_count % 2 != 0:
                is_flat = False
                break
        if is_flat:
            flat_states.append(z)

    visited = set()
    num_orbits = 0
    for z in flat_states:
        if z not in visited:
            num_orbits += 1
            q = [z]
            visited.add(z)
            while q:
                curr = q.pop()
                for av in av_masks:
                    nxt = curr ^ av
                    if nxt not in visited:
                        visited.add(nxt)
                        q.append(nxt)

    return num_orbits


def _c2_verify_refusal_warranted(case: Mapping[str, Any], refusal_code: str) -> tuple[bool, str]:
    """Checker 2 independent refusal validation."""
    valid_codes = frozenset({"TOO_MANY_EDGES", "MALFORMED_CASE_STRUCTURE"})
    if refusal_code not in valid_codes:
        return False, f"FAIL (C2): unrecognized refusal code {refusal_code!r}"

    if not isinstance(case, Mapping):
        return (refusal_code == "MALFORMED_CASE_STRUCTURE"), f"Refusal {refusal_code}"

    query = case.get("query")
    if query not in ("degeneracy", "gauss_law_sector"):
        return (refusal_code == "MALFORMED_CASE_STRUCTURE"), f"Refusal {refusal_code}"

    edges = case.get("edges")
    if not isinstance(edges, list):
        return (refusal_code == "MALFORMED_CASE_STRUCTURE"), f"Refusal {refusal_code}"

    if len(edges) > 300:
        return (refusal_code == "TOO_MANY_EDGES"), f"Refusal {refusal_code}"

    return (
        False,
        f"FAIL (C2): unwarranted UNKNOWN refusal ({refusal_code}) on valid case within bounds",
    )


def _c2_check_topology(case: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, Any] | None]:
    """Independent topological audit of cell complex for Checker 2."""
    edges = case.get("edges", [])
    faces = case.get("faces", [])
    raw_vertices = case.get("vertices", [])
    v_count = len(raw_vertices) if isinstance(raw_vertices, list) else int(raw_vertices)

    if len(edges) > 300:
        return False, "TOO_MANY_EDGES", {"refusal_code": "TOO_MANY_EDGES"}

    query = case.get("query")
    if query == "gauss_law_sector":
        adj_graph = defaultdict(list)
        for e in edges:
            adj_graph[e[0]].append(e[1])
            adj_graph[e[1]].append(e[0])
        visited_v = set()
        if v_count > 0:
            q_v = [0]
            visited_v.add(0)
            while q_v:
                curr = q_v.pop()
                for nxt in adj_graph[curr]:
                    if nxt not in visited_v:
                        visited_v.add(nxt)
                        q_v.append(nxt)
            if len(visited_v) != v_count:
                return False, "GRAPH_DISCONNECTED", {"kind": "graph_disconnected"}
        return True, "VALID_GRAPH", None

    # Edge multiplicity check
    edge_counts: dict[int, int] = defaultdict(int)
    for f in faces:
        for item in f:
            e_idx = (
                item
                if _c2_is_int(item)
                else (item[0] if isinstance(item, (list, tuple)) else item.get("edge"))
            )
            edge_counts[e_idx] += 1

    for e in range(len(edges)):
        if edge_counts[e] != 2:
            return (
                False,
                "NON_MANIFOLD_EDGE",
                {"kind": "edge_not_in_two_faces", "edge": e, "count": edge_counts[e]},
            )

    # Vertex link check
    half_edges_at_v: dict[int, set[tuple[int, int]]] = defaultdict(set)
    for e_idx, e in enumerate(edges):
        u, v = e[0], e[1]
        half_edges_at_v[u].add((e_idx, 0))
        half_edges_at_v[v].add((e_idx, 1))

    corners_at_v: dict[int, list[tuple[tuple[int, int], tuple[int, int]]]] = defaultdict(list)
    for face in faces:
        m = len(face)
        parsed_steps = []
        for step in face:
            if isinstance(step, (list, tuple)) and len(step) >= 2:
                e_ref, d_ref = step[0], step[1]
                direction = 1 if d_ref in (1, "+", "+1") else -1
                parsed_steps.append((e_ref, direction))
            elif isinstance(step, Mapping):
                e_ref = step.get("edge")
                d_ref = step.get("direction", 1)
                direction = 1 if d_ref in (1, "+", "+1") else -1
                parsed_steps.append((e_ref, direction))
            elif _c2_is_int(step):
                direction = 1 if step > 0 else -1
                e_ref = (step - 1) if step > 0 else (abs(step) - 1)
                parsed_steps.append((e_ref, direction))

        for i in range(m):
            e_curr, d_curr = parsed_steps[i]
            e_next, d_next = parsed_steps[(i + 1) % m]
            u_curr, v_curr = edges[e_curr]
            arr_v = v_curr if d_curr == 1 else u_curr
            arr_he = (e_curr, 1 if d_curr == 1 else 0)

            u_next, v_next = edges[e_next]
            dep_v = u_next if d_next == 1 else v_next
            dep_he = (e_next, 0 if d_next == 1 else 1)

            if arr_v == dep_v:
                corners_at_v[arr_v].append((arr_he, dep_he))

    for v in range(v_count):
        he_set = half_edges_at_v[v]
        corners = corners_at_v[v]
        if not he_set:
            return False, "NON_MANIFOLD_VERTEX", {"kind": "vertex_link_not_a_circle", "vertex": v}
        adj = defaultdict(list)
        for h1, h2 in corners:
            adj[h1].append(h2)
            adj[h2].append(h1)
        for h in he_set:
            if len(adj[h]) != 2:
                return (
                    False,
                    "NON_MANIFOLD_VERTEX",
                    {"kind": "vertex_link_not_a_circle", "vertex": v},
                )
        start = next(iter(he_set))
        visited = set()
        q = [start]
        visited.add(start)
        while q:
            curr = q.pop()
            for nxt in adj[curr]:
                if nxt not in visited:
                    visited.add(nxt)
                    q.append(nxt)
        if len(visited) != len(he_set):
            return False, "NON_MANIFOLD_VERTEX", {"kind": "vertex_link_not_a_circle", "vertex": v}

    # Connectivity checks
    adj_graph = defaultdict(list)
    for e in edges:
        adj_graph[e[0]].append(e[1])
        adj_graph[e[1]].append(e[0])
    visited_v = set()
    if v_count > 0:
        q_v = [0]
        visited_v.add(0)
        while q_v:
            curr = q_v.pop()
            for nxt in adj_graph[curr]:
                if nxt not in visited_v:
                    visited_v.add(nxt)
                    q_v.append(nxt)
        if len(visited_v) != v_count:
            return False, "GRAPH_DISCONNECTED", {"kind": "graph_disconnected"}

    face_edge_map: dict[int, list[int]] = defaultdict(list)
    for f_idx, f in enumerate(faces):
        for item in f:
            e_idx = (
                item
                if _c2_is_int(item)
                else (item[0] if isinstance(item, (list, tuple)) else item.get("edge"))
            )
            face_edge_map[e_idx].append(f_idx)

    face_adj = defaultdict(set)
    for f_indices in face_edge_map.values():
        if len(f_indices) == 2:
            f1, f2 = f_indices[0], f_indices[1]
            if f1 != f2:
                face_adj[f1].add(f2)
                face_adj[f2].add(f1)

    if faces:
        visited_f = set()
        q_f = [0]
        visited_f.add(0)
        while q_f:
            curr = q_f.pop()
            for nxt in face_adj[curr]:
                if nxt not in visited_f:
                    visited_f.add(nxt)
                    q_f.append(nxt)
        if len(visited_f) != len(faces):
            return False, "SURFACE_DISCONNECTED", {"kind": "surface_disconnected"}

    return True, "VALID_MANIFOLD", None


def _c2_verify_out_of_scope_warranted(
    case: Mapping[str, Any], answer: Mapping[str, Any]
) -> tuple[bool, str]:
    """Checker 2 independent out of scope validation."""
    witness = answer.get("witness")
    if not isinstance(witness, Mapping):
        return False, "FAIL (C2): OUT_OF_SCOPE answer missing witness Mapping"

    is_valid, reason, defect_witness = _c2_check_topology(case)
    if is_valid:
        return (
            False,
            "FAIL (C2): complex is a valid, connected closed 2-manifold within bounds; OUT_OF_SCOPE unwarranted",
        )

    witness.get("kind")
    if reason in (
        "NON_MANIFOLD_EDGE",
        "NON_MANIFOLD_VERTEX",
        "GRAPH_DISCONNECTED",
        "SURFACE_DISCONNECTED",
    ):
        return True, f"PASS (C2): topological defect verified: {reason}"

    return False, f"FAIL (C2): unrecognized or unverified witness defect: {reason}"


def verify_homology_cohomology_certificate(
    case: Mapping[str, Any], answer: Mapping[str, Any]
) -> tuple[bool, str]:
    """Checker 2 entrypoint."""
    if not isinstance(case, Mapping) or not isinstance(answer, Mapping):
        return False, "FAIL (C2): case and answer must be Mappings"

    status = answer.get("status")
    if type(status) is not str or status not in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}:
        return False, f"FAIL (C2): invalid status '{status}'"

    c_id = case.get("case_id") or case.get("id")
    a_id = answer.get("id") or answer.get("case_id")
    if c_id != a_id:
        return False, f"FAIL (C2): case ID mismatch: case={c_id} vs answer={a_id}"

    if status == "UNKNOWN":
        allowed_keys = {"id", "case_id", "status", "refusal_code"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C2): unexpected key '{k}' in UNKNOWN answer"
        ref_code = answer.get("refusal_code")
        if not isinstance(ref_code, str):
            return False, "FAIL (C2): UNKNOWN answer missing refusal_code"
        return _c2_verify_refusal_warranted(case, ref_code)

    if status == "OUT_OF_SCOPE":
        allowed_keys = {"id", "case_id", "status", "witness"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C2): unexpected key '{k}' in OUT_OF_SCOPE answer"
        return _c2_verify_out_of_scope_warranted(case, answer)

    query = case.get("query")
    if query == "degeneracy":
        return _c2_verify_degeneracy(case, answer)
    elif query == "gauss_law_sector":
        return _c2_verify_sector(case, answer)
    return False, f"FAIL (C2): unknown query '{query}'"


def _c2_verify_degeneracy(case: Mapping[str, Any], answer: Mapping[str, Any]) -> tuple[bool, str]:
    """Verifies degeneracy query via cellular chain complex C_2 -> C_1 -> C_0 and Betti numbers."""
    allowed_keys = {
        "id",
        "case_id",
        "status",
        "V",
        "E",
        "F",
        "euler",
        "rank_star",
        "rank_plaquette",
        "k",
        "gsd",
        "logicals",
    }
    for k in answer.keys():
        if k not in allowed_keys:
            return False, f"FAIL (C2): unexpected key '{k}' in degeneracy answer"

    # Strict int checks
    for field in ("V", "E", "F", "euler", "rank_star", "rank_plaquette", "k", "gsd"):
        if not _c2_is_int(answer.get(field)):
            return (
                False,
                f"FAIL (C2): field '{field}' must be an exact integer, got {type(answer.get(field))}",
            )

    # Verify input is valid closed 2-manifold
    is_valid, reason, _ = _c2_check_topology(case)
    if not is_valid:
        return (
            False,
            f"FAIL (C2): complex is not a valid closed 2-manifold ({reason}); cannot be SOLVED",
        )

    v_val = answer["V"]
    e_val = answer["E"]
    f_val = answer["F"]
    euler_val = answer["euler"]
    rank_star_val = answer["rank_star"]
    rank_plaq_val = answer["rank_plaquette"]
    k_val = answer["k"]
    gsd_val = answer["gsd"]

    edges = case.get("edges", [])
    faces = case.get("faces", [])
    raw_vertices = case.get("vertices", [])
    v_count = len(raw_vertices) if isinstance(raw_vertices, list) else int(raw_vertices)

    if v_val != v_count or e_val != len(edges) or f_val != len(faces):
        return False, "FAIL (C2): geometric counts mismatch with case"

    exp_euler = v_count - len(edges) + len(faces)
    if euler_val != exp_euler:
        return (
            False,
            f"FAIL (C2): euler characteristic mismatch: claimed {euler_val} != computed {exp_euler}",
        )

    num_qubits = len(edges)

    # 1. Construct boundary operator d_1: C_1 -> C_0 over Z_2
    d1_mat = [[0] * num_qubits for _ in range(v_count)]
    for e_idx, e in enumerate(edges):
        u, v = e[0], e[1]
        d1_mat[u][e_idx] ^= 1
        d1_mat[v][e_idx] ^= 1

    rank_d1, _ = _c2_gauss_jordan_gf2(d1_mat)

    # 2. Construct boundary operator d_2: C_2 -> C_1 over Z_2
    d2_mat = [[0] * len(faces) for _ in range(num_qubits)]
    for f_idx, f in enumerate(faces):
        for item in f:
            e_idx = (
                item
                if _c2_is_int(item)
                else (item[0] if isinstance(item, (list, tuple)) else item.get("edge"))
            )
            d2_mat[e_idx][f_idx] ^= 1

    rank_d2, _ = _c2_gauss_jordan_gf2(d2_mat)

    # Verify chain complex property: d_1 * d_2 == 0 mod 2
    for r in range(v_count):
        for c in range(len(faces)):
            val = 0
            for k_idx in range(num_qubits):
                val ^= d1_mat[r][k_idx] & d2_mat[k_idx][c]
            if val != 0:
                return (
                    False,
                    f"FAIL (C2): chain complex condition d1 o d2 = 0 mod 2 violated at (v={r}, f={c})",
                )

    # Betti numbers over Z_2:
    b0 = v_count - rank_d1
    b2 = len(faces) - rank_d2
    b1 = num_qubits - rank_d1 - rank_d2

    if b0 != 1:
        return False, f"FAIL (C2): complex not connected: b_0 = {b0} != 1"
    if b2 != 1:
        return False, f"FAIL (C2): surface not closed 2-manifold: b_2 = {b2} != 1"

    if rank_star_val != rank_d1:
        return (
            False,
            f"FAIL (C2): rank_star mismatch: claimed {rank_star_val} != rank(d1)={rank_d1}",
        )
    if rank_plaq_val != rank_d2:
        return (
            False,
            f"FAIL (C2): rank_plaquette mismatch: claimed {rank_plaq_val} != rank(d2)={rank_d2}",
        )

    if k_val != b1:
        return False, f"FAIL (C2): logical qubits k mismatch: claimed {k_val} != b_1={b1}"

    exp_gsd = 1 << b1
    if gsd_val != exp_gsd:
        return False, f"FAIL (C2): gsd mismatch: claimed {gsd_val} != 2^b_1={exp_gsd}"

    # Verify logicals
    logicals = answer.get("logicals")
    if not isinstance(logicals, Mapping):
        return False, "FAIL (C2): logicals must be a Mapping"

    z_logicals = logicals.get("z")
    x_logicals = logicals.get("x")
    if not isinstance(z_logicals, list) or not isinstance(x_logicals, list):
        return False, "FAIL (C2): logicals z and x must be lists"

    if len(z_logicals) != b1 or len(x_logicals) != b1:
        return (
            False,
            f"FAIL (C2): expected {b1} logical pairs, got len(z)={len(z_logicals)}, len(x)={len(x_logicals)}",
        )

    z_cycles: list[list[int]] = []
    x_cycles: list[list[int]] = []

    for z_str in z_logicals:
        if not isinstance(z_str, str) or len(z_str) != num_qubits:
            return False, "FAIL (C2): logical Z string invalid"
        vec = [1 if c == "Z" else 0 for c in z_str]
        z_cycles.append(vec)

    for x_str in x_logicals:
        if not isinstance(x_str, str) or len(x_str) != num_qubits:
            return False, "FAIL (C2): logical X string invalid"
        vec = [1 if c == "X" else 0 for c in x_str]
        x_cycles.append(vec)

    # 1. Check that each Z_i is a 1-cycle: d_1 * Z_i == 0 mod 2
    for idx, z_vec in enumerate(z_cycles):
        for v in range(v_count):
            val = 0
            for e_idx in range(num_qubits):
                val ^= d1_mat[v][e_idx] & z_vec[e_idx]
            if val != 0:
                return (
                    False,
                    f"FAIL (C2): logical z[{idx}] is not a 1-cycle: d1(z) != 0 at vertex {v}",
                )

    # 2. Check that each X_j is a dual 1-cycle (1-cocycle): d_2^T * X_j == 0 mod 2
    for idx, x_vec in enumerate(x_cycles):
        for f in range(len(faces)):
            val = 0
            for e_idx in range(num_qubits):
                val ^= d2_mat[e_idx][f] & x_vec[e_idx]
            if val != 0:
                return (
                    False,
                    f"FAIL (C2): logical x[{idx}] is not a 1-cocycle: d2^T(x) != 0 at face {f}",
                )

    # 3. Dual intersection pairing: <Z_i, X_j> = sum_e Z_i[e] * X_j[e] mod 2
    for i in range(b1):
        for j in range(b1):
            pairing = 0
            for e_idx in range(num_qubits):
                pairing ^= z_cycles[i][e_idx] & x_cycles[j][e_idx]
            exp_pair = 1 if i == j else 0
            if pairing != exp_pair:
                return (
                    False,
                    f"FAIL (C2): dual intersection pairing <z[{i}], x[{j}]> = {pairing} != {exp_pair}",
                )

    # 4. Homological non-triviality:
    d2_cols = [[d2_mat[e_idx][f_idx] for e_idx in range(num_qubits)] for f_idx in range(len(faces))]
    for idx, z_vec in enumerate(z_cycles):
        if _c2_in_image_gf2(z_vec, d2_cols):
            return False, f"FAIL (C2): logical z[{idx}] is a boundary (in im(d_2)), hence trivial"

    d1_transpose_cols = [[d1_mat[v][e_idx] for e_idx in range(num_qubits)] for v in range(v_count)]
    for idx, x_vec in enumerate(x_cycles):
        if _c2_in_image_gf2(x_vec, d1_transpose_cols):
            return (
                False,
                f"FAIL (C2): logical x[{idx}] is a coboundary (in im(d_1^T)), hence trivial",
            )

    # 5. Dense exact Hilbert space check for small complexes (E <= 10)
    if num_qubits <= 10:
        exact_gsd = _c2_exact_dense_hilbert_space_gsd(v_count, edges, faces)
        if gsd_val != exact_gsd:
            return (
                False,
                f"FAIL (C2): dense exact Hilbert space ground space dimension {exact_gsd} != claimed {gsd_val}",
            )

    return True, "PASS (C2): valid cellular homology & dual pairing certificate"


def _c2_verify_sector(case: Mapping[str, Any], answer: Mapping[str, Any]) -> tuple[bool, str]:
    """Verifies Gauss-law sector query via DFS cycle space dimension."""
    allowed_keys = {"id", "case_id", "status", "sector_dimension", "witness"}
    for k in answer.keys():
        if k not in allowed_keys:
            return False, f"FAIL (C2): unexpected key '{k}' in sector answer"

    if not _c2_is_int(answer.get("sector_dimension")):
        return (
            False,
            f"FAIL (C2): sector_dimension must be exact int, got {type(answer.get('sector_dimension'))}",
        )

    sec_dim = answer["sector_dimension"]
    charges = case.get("charges", {})
    charge_list = list(charges.values()) if isinstance(charges, Mapping) else charges
    prod = 1
    for c in charge_list:
        prod *= c

    if prod == -1:
        if sec_dim != 0:
            return (
                False,
                f"FAIL (C2): sector with odd charge product must have dimension 0, got {sec_dim}",
            )
        witness = answer.get("witness")
        if not isinstance(witness, Mapping) or witness.get("charge_product") != -1:
            return False, "FAIL (C2): empty sector must provide witness {'charge_product': -1}"
        return True, "PASS (C2): valid empty Gauss-law sector certificate"

    if sec_dim == 0:
        return False, "FAIL (C2): non-empty sector cannot have dimension 0"

    edges = case.get("edges", [])
    if len(edges) > 300:
        return False, f"FAIL (C2): E={len(edges)} > 300 must be UNKNOWN with TOO_MANY_EDGES"

    raw_vertices = case.get("vertices", [])
    v_count = len(raw_vertices) if isinstance(raw_vertices, list) else int(raw_vertices)

    cycle_rank, is_connected = _c2_dfs_spanning_tree_cycle_rank(v_count, edges)
    if not is_connected:
        return False, "FAIL (C2): graph is not connected"

    exp_dim = 1 << cycle_rank
    if sec_dim != exp_dim:
        return (
            False,
            f"FAIL (C2): sector dimension mismatch: claimed {sec_dim} != computed 2^{cycle_rank}={exp_dim}",
        )

    return True, "PASS (C2): valid DFS cycle space sector certificate"
