"""Checker 1: Stabilizer Tableau & Symplectic Certifier for C039.

Implements independent stabilizer tableau verification over F2:
- Ranks of star operators A_v and plaquette operators B_p
- Symplectic commutation between logical operators: [Z_i, X_j] = delta_{ij} mod 2
- Commutation with all stabilizers: [Z_i, S] = 0, [X_j, S] = 0
- Augmented matrix F2 row-reduction certifying logical operators do not lie in stabilizer span
- Anti-bypass defense layers: strict int validation, closed schema whitelisting, unwarranted refusal check

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping


def _c1_is_int(val: Any) -> bool:
    """Strict check for int, rejecting bool."""
    return type(val) is int and not isinstance(val, bool)


def _c1_f2_rank(matrix: list[list[int]]) -> int:
    """Computes row rank of matrix over GF(2) via Gaussian elimination."""
    if not matrix or not matrix[0]:
        return 0
    mat = [row[:] for row in matrix]
    rows = len(mat)
    cols = len(mat[0])
    rank = 0
    col = 0
    for r in range(rows):
        while col < cols:
            pivot = -1
            for i in range(r, rows):
                if mat[i][col] == 1:
                    pivot = i
                    break
            if pivot != -1:
                mat[r], mat[pivot] = mat[pivot], mat[r]
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
    return rank


def _c1_pauli_to_symplectic(p_str: str) -> tuple[list[int], list[int]]:
    """Converts a Pauli string over E qubits into (X_vector, Z_vector) over GF(2)."""
    x_vec = []
    z_vec = []
    for char in p_str:
        if char == "I":
            x_vec.append(0)
            z_vec.append(0)
        elif char == "X":
            x_vec.append(1)
            z_vec.append(0)
        elif char == "Z":
            x_vec.append(0)
            z_vec.append(1)
        elif char == "Y":
            x_vec.append(1)
            z_vec.append(1)
        else:
            raise ValueError(f"Invalid Pauli char: {char}")
    return x_vec, z_vec


def _c1_symplectic_inner_product(
    p1: tuple[list[int], list[int]], p2: tuple[list[int], list[int]]
) -> int:
    """Computes symplectic inner product <P1, P2> = P1_X * P2_Z + P1_Z * P2_X mod 2."""
    x1, z1 = p1
    x2, z2 = p2
    prod = 0
    for j in range(len(x1)):
        prod ^= (x1[j] & z2[j]) ^ (z1[j] & x2[j])
    return prod


def _c1_verify_refusal_warranted(case: Mapping[str, Any], refusal_code: str) -> tuple[bool, str]:
    """Validates that a claimed UNKNOWN refusal code is defect-grounded and warranted."""
    valid_codes = frozenset({"TOO_MANY_EDGES", "MALFORMED_CASE_STRUCTURE"})
    if refusal_code not in valid_codes:
        return False, f"FAIL (C1): unrecognized refusal code {refusal_code!r}"

    if not isinstance(case, Mapping):
        if refusal_code == "MALFORMED_CASE_STRUCTURE":
            return True, "PASS (C1): valid UNKNOWN refusal for non-Mapping case"
        return (
            False,
            f"FAIL (C1): non-Mapping case requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
        )

    query = case.get("query")
    if query not in ("degeneracy", "gauss_law_sector"):
        if refusal_code == "MALFORMED_CASE_STRUCTURE":
            return True, "PASS (C1): valid UNKNOWN refusal for invalid query"
        return (
            False,
            f"FAIL (C1): invalid query requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
        )

    edges = case.get("edges")
    if not isinstance(edges, list):
        if refusal_code == "MALFORMED_CASE_STRUCTURE":
            return True, "PASS (C1): valid UNKNOWN refusal for malformed edges"
        return (
            False,
            f"FAIL (C1): malformed edges requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
        )

    if len(edges) > 300:
        if refusal_code == "TOO_MANY_EDGES":
            return True, "PASS (C1): valid UNKNOWN refusal for TOO_MANY_EDGES"
        return False, f"FAIL (C1): > 300 edges requires TOO_MANY_EDGES, got {refusal_code}"

    return (
        False,
        f"FAIL (C1): unwarranted UNKNOWN refusal ({refusal_code}) on valid case within bounds",
    )


def _c1_check_topology(case: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, Any] | None]:
    """Independent topological audit of cell complex for Checker 1."""
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
                if _c1_is_int(item)
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
            elif _c1_is_int(step):
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
                if _c1_is_int(item)
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


def _c1_verify_out_of_scope_warranted(
    case: Mapping[str, Any], answer: Mapping[str, Any]
) -> tuple[bool, str]:
    """Validates OUT_OF_SCOPE witness: verifies non-manifold or disconnected complex."""
    witness = answer.get("witness")
    if not isinstance(witness, Mapping):
        return False, "FAIL (C1): OUT_OF_SCOPE answer missing witness Mapping"

    is_valid, reason, defect_witness = _c1_check_topology(case)
    if is_valid:
        return (
            False,
            "FAIL (C1): complex is a valid, connected closed 2-manifold within bounds; OUT_OF_SCOPE unwarranted",
        )

    witness.get("kind")
    if reason in (
        "NON_MANIFOLD_EDGE",
        "NON_MANIFOLD_VERTEX",
        "GRAPH_DISCONNECTED",
        "SURFACE_DISCONNECTED",
    ):
        return True, f"PASS (C1): topological defect verified: {reason}"

    return False, f"FAIL (C1): unrecognized or unverified witness defect: {reason}"


def verify_stabilizer_tableau_certificate(
    case: Mapping[str, Any], answer: Mapping[str, Any]
) -> tuple[bool, str]:
    """Checker 1 entrypoint."""
    if not isinstance(case, Mapping) or not isinstance(answer, Mapping):
        return False, "FAIL (C1): case and answer must be Mappings"

    status = answer.get("status")
    if type(status) is not str or status not in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}:
        return False, f"FAIL (C1): invalid status '{status}'"

    c_id = case.get("case_id") or case.get("id")
    a_id = answer.get("id") or answer.get("case_id")
    if c_id != a_id:
        return False, f"FAIL (C1): case ID mismatch: case={c_id} vs answer={a_id}"

    if status == "UNKNOWN":
        allowed_keys = {"id", "case_id", "status", "refusal_code"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C1): unexpected key '{k}' in UNKNOWN answer"
        ref_code = answer.get("refusal_code")
        if not isinstance(ref_code, str):
            return False, "FAIL (C1): UNKNOWN answer missing refusal_code"
        return _c1_verify_refusal_warranted(case, ref_code)

    if status == "OUT_OF_SCOPE":
        allowed_keys = {"id", "case_id", "status", "witness"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C1): unexpected key '{k}' in OUT_OF_SCOPE answer"
        return _c1_verify_out_of_scope_warranted(case, answer)

    query = case.get("query")
    if query == "degeneracy":
        return _c1_verify_degeneracy(case, answer)
    elif query == "gauss_law_sector":
        return _c1_verify_sector(case, answer)
    return False, f"FAIL (C1): unknown query '{query}'"


def _c1_verify_degeneracy(case: Mapping[str, Any], answer: Mapping[str, Any]) -> tuple[bool, str]:
    """Verifies degeneracy query under Checker 1."""
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
            return False, f"FAIL (C1): unexpected key '{k}' in degeneracy answer"

    # Strict int checks
    for field in ("V", "E", "F", "euler", "rank_star", "rank_plaquette", "k", "gsd"):
        if not _c1_is_int(answer.get(field)):
            return (
                False,
                f"FAIL (C1): field '{field}' must be an exact integer, got {type(answer.get(field))}",
            )

    # Verify input is valid closed 2-manifold
    is_valid, reason, _ = _c1_check_topology(case)
    if not is_valid:
        return (
            False,
            f"FAIL (C1): complex is not a valid closed 2-manifold ({reason}); cannot be SOLVED",
        )

    v_val = answer["V"]
    e_val = answer["E"]
    f_val = answer["F"]
    euler_val = answer["euler"]
    rank_star_val = answer["rank_star"]
    rank_plaq_val = answer["rank_plaquette"]
    k_val = answer["k"]
    gsd_val = answer["gsd"]

    # Verify input geometry counts
    edges = case.get("edges", [])
    faces = case.get("faces", [])
    raw_vertices = case.get("vertices", [])
    v_count = len(raw_vertices) if isinstance(raw_vertices, list) else int(raw_vertices)

    if v_val != v_count or e_val != len(edges) or f_val != len(faces):
        return (
            False,
            f"FAIL (C1): geometric counts mismatch with case: V={v_val} vs {v_count}, E={e_val} vs {len(edges)}, F={f_val} vs {len(faces)}",
        )

    exp_euler = v_count - len(edges) + len(faces)
    if euler_val != exp_euler:
        return (
            False,
            f"FAIL (C1): euler characteristic mismatch: claimed {euler_val} != computed {exp_euler}",
        )

    num_qubits = len(edges)

    # Build Star operators A_v (pure X) over GF(2)
    stars_gf2: list[list[int]] = []
    for v in range(v_count):
        row = [0] * num_qubits
        for e_idx, e in enumerate(edges):
            u_e, v_e = e[0], e[1]
            ends = 0
            if u_e == v:
                ends += 1
            if v_e == v:
                ends += 1
            row[e_idx] = ends % 2
        stars_gf2.append(row)

    rank_stars_calc = _c1_f2_rank(stars_gf2)
    if rank_star_val != rank_stars_calc:
        return (
            False,
            f"FAIL (C1): rank_star mismatch: claimed {rank_star_val} != computed {rank_stars_calc}",
        )

    # Build Plaquette operators B_p (pure Z) over GF(2)
    plaquettes_gf2: list[list[int]] = []
    for f in faces:
        row = [0] * num_qubits
        for item in f:
            e_idx = (
                item
                if _c1_is_int(item)
                else (item[0] if isinstance(item, (list, tuple)) else item.get("edge"))
            )
            row[e_idx] = (row[e_idx] + 1) % 2
        plaquettes_gf2.append(row)

    rank_plaq_calc = _c1_f2_rank(plaquettes_gf2)
    if rank_plaq_val != rank_plaq_calc:
        return (
            False,
            f"FAIL (C1): rank_plaquette mismatch: claimed {rank_plaq_val} != computed {rank_plaq_calc}",
        )

    # Verify k and GSD
    k_calc = num_qubits - rank_stars_calc - rank_plaq_calc
    if k_val != k_calc:
        return False, f"FAIL (C1): k mismatch: claimed {k_val} != computed {k_calc}"

    if gsd_val != (1 << k_calc):
        return False, f"FAIL (C1): gsd mismatch: claimed {gsd_val} != computed {1 << k_calc}"

    # Verify logicals
    logicals = answer.get("logicals")
    if not isinstance(logicals, Mapping):
        return False, "FAIL (C1): logicals must be a Mapping"

    z_logicals = logicals.get("z")
    x_logicals = logicals.get("x")
    if not isinstance(z_logicals, list) or not isinstance(x_logicals, list):
        return False, "FAIL (C1): logicals z and x must be lists"

    if len(z_logicals) != k_val or len(x_logicals) != k_val:
        return (
            False,
            f"FAIL (C1): expected {k_val} logical pairs, got len(z)={len(z_logicals)}, len(x)={len(x_logicals)}",
        )

    z_symp: list[tuple[list[int], list[int]]] = []
    x_symp: list[tuple[list[int], list[int]]] = []

    for z_str in z_logicals:
        if not isinstance(z_str, str) or len(z_str) != num_qubits:
            return False, f"FAIL (C1): logical Z string must have length {num_qubits}"
        if any(c not in ("I", "Z") for c in z_str):
            return False, f"FAIL (C1): candidate logical Z contains non-Z characters: {z_str}"
        z_symp.append(_c1_pauli_to_symplectic(z_str))

    for x_str in x_logicals:
        if not isinstance(x_str, str) or len(x_str) != num_qubits:
            return False, f"FAIL (C1): logical X string must have length {num_qubits}"
        if any(c not in ("I", "X") for c in x_str):
            return False, f"FAIL (C1): candidate logical X contains non-X characters: {x_str}"
        x_symp.append(_c1_pauli_to_symplectic(x_str))

    # Convert stabilizers to symplectic tuples: (X, Z)
    stars_symp = [(row, [0] * num_qubits) for row in stars_gf2]
    plaq_symp = [([0] * num_qubits, row) for row in plaquettes_gf2]
    all_stab_symp = stars_symp + plaq_symp

    # Check 1: Candidate logicals commute with all stabilizers
    for idx, z_p in enumerate(z_symp):
        for s_idx, stab in enumerate(all_stab_symp):
            if _c1_symplectic_inner_product(z_p, stab) != 0:
                return False, f"FAIL (C1): logical z[{idx}] anticommutes with stabilizer {s_idx}"

    for idx, x_p in enumerate(x_symp):
        for s_idx, stab in enumerate(all_stab_symp):
            if _c1_symplectic_inner_product(x_p, stab) != 0:
                return False, f"FAIL (C1): logical x[{idx}] anticommutes with stabilizer {s_idx}"

    # Check 2: Symplectic Gram matrix [0, I; I, 0] mod 2
    for i in range(k_val):
        for j in range(k_val):
            # [Z_i, Z_j] == 0
            if _c1_symplectic_inner_product(z_symp[i], z_symp[j]) != 0:
                return False, f"FAIL (C1): logical z[{i}] and z[{j}] anticommute"
            # [X_i, X_j] == 0
            if _c1_symplectic_inner_product(x_symp[i], x_symp[j]) != 0:
                return False, f"FAIL (C1): logical x[{i}] and x[{j}] anticommute"
            # [Z_i, X_j] == delta_ij
            exp_comm = 1 if i == j else 0
            act_comm = _c1_symplectic_inner_product(z_symp[i], x_symp[j])
            if act_comm != exp_comm:
                return (
                    False,
                    f"FAIL (C1): non-canonical commutation <z[{i}], x[{j}]> = {act_comm} != {exp_comm}",
                )

    # Check 3: Non-stabilizer verification via augmented F2 rank
    stab_rows: list[list[int]] = []
    for s_x, s_z in all_stab_symp:
        stab_rows.append(s_x + s_z)
    stab_rank = _c1_f2_rank(stab_rows)

    aug_rows: list[list[int]] = [row[:] for row in stab_rows]
    for z_x, z_z in z_symp:
        aug_rows.append(z_x + z_z)
    for x_x, x_z in x_symp:
        aug_rows.append(x_x + x_z)

    aug_rank = _c1_f2_rank(aug_rows)
    if aug_rank != stab_rank + 2 * k_val:
        return (
            False,
            f"FAIL (C1): non-stabilizer verification failed: aug_rank={aug_rank} < stab_rank({stab_rank}) + 2k({2 * k_val})",
        )

    return True, "PASS (C1): valid toric code stabilizer tableau certificate"


def _c1_verify_sector(case: Mapping[str, Any], answer: Mapping[str, Any]) -> tuple[bool, str]:
    """Verifies Gauss-law sector query under Checker 1."""
    allowed_keys = {"id", "case_id", "status", "sector_dimension", "witness"}
    for k in answer.keys():
        if k not in allowed_keys:
            return False, f"FAIL (C1): unexpected key '{k}' in sector answer"

    if not _c1_is_int(answer.get("sector_dimension")):
        return (
            False,
            f"FAIL (C1): sector_dimension must be exact int, got {type(answer.get('sector_dimension'))}",
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
                f"FAIL (C1): sector with odd charge product must have dimension 0, got {sec_dim}",
            )
        witness = answer.get("witness")
        if not isinstance(witness, Mapping) or witness.get("charge_product") != -1:
            return False, "FAIL (C1): empty sector must provide witness {'charge_product': -1}"
        return True, "PASS (C1): valid empty Gauss-law sector certificate"

    # Even charges: product == +1
    if sec_dim == 0:
        return False, "FAIL (C1): non-empty sector cannot have dimension 0"

    edges = case.get("edges", [])
    if len(edges) > 300:
        return False, f"FAIL (C1): E={len(edges)} > 300 must be UNKNOWN with TOO_MANY_EDGES"

    raw_vertices = case.get("vertices", [])
    v_count = len(raw_vertices) if isinstance(raw_vertices, list) else int(raw_vertices)

    # Check graph connectivity
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
            return False, "FAIL (C1): disconnected graph cannot be SOLVED for sector"

    # Compute star rank of graph G via F2 row reduction
    stars_gf2: list[list[int]] = []
    for v in range(v_count):
        row = [0] * len(edges)
        for e_idx, e in enumerate(edges):
            u_e, v_e = e[0], e[1]
            ends = 0
            if u_e == v:
                ends += 1
            if v_e == v:
                ends += 1
            row[e_idx] = ends % 2
        stars_gf2.append(row)

    r_star = _c1_f2_rank(stars_gf2)
    exp_dim = 1 << (len(edges) - r_star)
    if sec_dim != exp_dim:
        return (
            False,
            f"FAIL (C1): sector dimension mismatch: claimed {sec_dim} != computed {exp_dim}",
        )

    return True, "PASS (C1): valid Gauss-law sector certificate"
