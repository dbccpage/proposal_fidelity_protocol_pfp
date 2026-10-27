"""Lattice Holonomy, Plaquette Curvature, and Spanning Tree Gauge Fixing."""

from __future__ import annotations


def multiply_path(
    path: list[str],
    edges: dict[str, str],
    table: dict[str, dict[str, str]],
    identity: str = "e",
) -> str:
    """Compute ordered holonomy along path v_0 -> v_1 -> ... -> v_k.

    U(path) = U_{v_0 v_1} * U_{v_1 v_2} * ... * U_{v_{k-1} v_k}.
    """
    val = identity
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_key = f"{u}->{v}"
        u_elem = edges[edge_key]
        val = table[val][u_elem]
    return val


def compute_all_plaquettes(
    L: int,
    M: int,
    boundary: str,
) -> list[list[str]]:
    """Return list of plaquettes [v0, v1, v2, v3] in counter-clockwise order:

    v0 = (r, c)
    v1 = (r+1, c)
    v2 = (r+1, c+1)
    v3 = (r, c+1)
    """
    plaquettes: list[list[str]] = []
    r_max = L if boundary == "periodic" else L - 1
    c_max = M if boundary == "periodic" else M - 1

    for r in range(r_max):
        for c in range(c_max):
            if boundary == "periodic":
                r0, c0 = r % L, c % M
                r1, c1 = (r + 1) % L, c % M
                r2, c2 = (r + 1) % L, (c + 1) % M
                r3, c3 = r % L, (c + 1) % M
            else:
                r0, c0 = r, c
                r1, c1 = r + 1, c
                r2, c2 = r + 1, c + 1
                r3, c3 = r, c + 1

            v0 = f"{r0},{c0}"
            v1 = f"{r1},{c1}"
            v2 = f"{r2},{c2}"
            v3 = f"{r3},{c3}"
            plaquettes.append([v0, v1, v2, v3])

    return plaquettes


def fix_spanning_tree_gauge(
    L: int,
    M: int,
    edges: dict[str, str],
    table: dict[str, dict[str, str]],
    inverses: dict[str, str],
    identity: str = "e",
) -> dict[str, str]:
    """Compute gauge g: V -> G along spanning tree rooted at (0, 0).

    Sets g_{(0,0)} = e.
    For each tree edge u -> v, sets g_v = g_u * U_{uv}.
    """
    root = "0,0"
    gauge: dict[str, str] = {root: identity}
    queue = [(0, 0)]
    visited = {(0, 0)}

    # Standard grid tree: row traversal first, then column traversal
    while queue:
        r, c = queue.pop(0)
        curr = f"{r},{c}"
        g_curr = gauge[curr]

        # 4 potential non-wrapping neighbors in grid
        neighbors = []
        if r + 1 < L:
            neighbors.append((r + 1, c))
        if r - 1 >= 0:
            neighbors.append((r - 1, c))
        if c + 1 < M:
            neighbors.append((r, c + 1))
        if c - 1 >= 0:
            neighbors.append((r, c - 1))

        for nr, nc in neighbors:
            if (nr, nc) not in visited:
                nxt = f"{nr},{nc}"
                e_key = f"{curr}->{nxt}"
                u_elem = edges[e_key]
                # g_nxt = g_curr * U_{curr->nxt}
                gauge[nxt] = table[g_curr][u_elem]
                visited.add((nr, nc))
                queue.append((nr, nc))

    return gauge


def check_is_pure_gauge(
    gauge: dict[str, str],
    edges: dict[str, str],
    table: dict[str, dict[str, str]],
    inverses: dict[str, str],
    identity: str = "e",
) -> bool:
    """Verify that g_u * U_{uv} * g_v^{-1} == e for ALL edges."""
    for e_key, u_elem in edges.items():
        u, v = e_key.split("->")
        g_u = gauge[u]
        g_v_inv = inverses[gauge[v]]
        # (g_u * U_{uv}) * g_v^{-1}
        step1 = table[g_u][u_elem]
        val = table[step1][g_v_inv]
        if val != identity:
            return False
    return True


def compute_torus_global_loops(
    L: int,
    M: int,
    edges: dict[str, str],
    table: dict[str, dict[str, str]],
    identity: str = "e",
) -> tuple[list[str], str, list[str], str]:
    """Compute holonomies around horizontal loop A and vertical loop B on torus.

    Base point (0, 0).
    Loop A: (0, 0) -> (0, 1) -> ... -> (0, M-1) -> (0, 0)
    Loop B: (0, 0) -> (1, 0) -> ... -> (L-1, 0) -> (0, 0)
    """
    loop_a = [f"0,{c}" for c in range(M)] + ["0,0"]
    hol_a = multiply_path(loop_a, edges, table, identity)

    loop_b = [f"{r},0" for r in range(L)] + ["0,0"]
    hol_b = multiply_path(loop_b, edges, table, identity)

    return loop_a, hol_a, loop_b, hol_b
