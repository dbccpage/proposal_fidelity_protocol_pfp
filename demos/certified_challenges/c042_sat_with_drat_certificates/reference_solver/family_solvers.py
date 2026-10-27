# AuthorityEffect: None.
"""
Problem encoders, decoders, and direct problem-level checkers for the 5 families:
1. Graph k-colouring
2. Pigeonhole PHP(p, h)
3. Latin-square completion
4. Tseitin parity formulas
5. Exact cover / polyomino tiling
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple


# -------------------------------------------------------------
# 1. Graph k-colouring
# -------------------------------------------------------------
def encode_coloring(
    n: int, k: int, edges: List[List[int]]
) -> Tuple[int, List[List[int]], Dict[Tuple[int, int], int]]:
    """Encodes graph colouring into CNF."""
    var_map: Dict[Tuple[int, int], int] = {}
    var_counter = 1
    for u in range(n):
        for c in range(k):
            var_map[(u, c)] = var_counter
            var_counter += 1

    clauses: List[List[int]] = []
    # At least one colour per vertex
    for u in range(n):
        clauses.append([var_map[(u, c)] for c in range(k)])

    # At most one colour per vertex
    for u in range(n):
        for c1 in range(k):
            for c2 in range(c1 + 1, k):
                clauses.append([-var_map[(u, c1)], -var_map[(u, c2)]])

    # Adjacent vertices have different colours
    for u, v in edges:
        for c in range(k):
            clauses.append([-var_map[(u, c)], -var_map[(v, c)]])

    return var_counter - 1, clauses, var_map


def decode_coloring(
    n: int, k: int, model: Dict[int, int], var_map: Dict[Tuple[int, int], int]
) -> Dict[str, Any]:
    colours = []
    for u in range(n):
        col = 0
        for c in range(k):
            if model.get(var_map[(u, c)], 0) == 1:
                col = c
                break
        colours.append(col)
    return {"colour": colours}


def check_coloring_solution(case: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[bool, str]:
    """Problem-level check for graph colouring."""
    n = case["n"]
    k = case["k"]
    edges = case["edges"]
    colours = solution.get("colour")
    if not isinstance(colours, list) or len(colours) != n:
        return False, f"Expected colour list of length {n}, got {colours}"

    for u, c in enumerate(colours):
        if type(c) is not int:
            return False, f"Vertex {u} colour is not strict int: {type(c)}"
        if c < 0 or c >= k:
            return False, f"Vertex {u} colour {c} out of range [0, {k - 1}]"

    for u, v in edges:
        if colours[u] == colours[v]:
            return False, f"Edge ({u}, {v}) monochromatic with colour {colours[u]}"

    return True, "Valid graph colouring"


# -------------------------------------------------------------
# 2. Pigeonhole PHP(p, h)
# -------------------------------------------------------------
def encode_php(
    pigeons: int, holes: int, blocked: Optional[List[List[int]]] = None
) -> Tuple[int, List[List[int]], Dict[Tuple[int, int], int]]:
    """Encodes PHP into CNF."""
    blocked_set = {tuple(b) for b in (blocked or [])}
    var_map: Dict[Tuple[int, int], int] = {}
    var_counter = 1
    for p in range(pigeons):
        for h in range(holes):
            var_map[(p, h)] = var_counter
            var_counter += 1

    clauses: List[List[int]] = []
    # Each pigeon in at least one hole (excluding blocked)
    for p in range(pigeons):
        p_clause = [var_map[(p, h)] for h in range(holes) if (p, h) not in blocked_set]
        clauses.append(p_clause)

    # No hole gets two pigeons
    for h in range(holes):
        for p1 in range(pigeons):
            for p2 in range(p1 + 1, pigeons):
                clauses.append([-var_map[(p1, h)], -var_map[(p2, h)]])

    # Blocked holes cannot be assigned
    for p, h in blocked_set:
        if (p, h) in var_map:
            clauses.append([-var_map[(p, h)]])

    return var_counter - 1, clauses, var_map


def decode_php(
    pigeons: int, holes: int, model: Dict[int, int], var_map: Dict[Tuple[int, int], int]
) -> Dict[str, Any]:
    assignment = []
    for p in range(pigeons):
        hole = -1
        for h in range(holes):
            if model.get(var_map[(p, h)], 0) == 1:
                hole = h
                break
        assignment.append(hole)
    return {"assignment": assignment}


def check_php_solution(case: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[bool, str]:
    p = case["pigeons"]
    h = case["holes"]
    blocked_set = {tuple(b) for b in case.get("blocked", [])}
    assignment = solution.get("assignment")
    if not isinstance(assignment, list) or len(assignment) != p:
        return False, f"Expected assignment list of length {p}, got {assignment}"

    seen_holes = set()
    for pigeon, hole in enumerate(assignment):
        if type(hole) is not int:
            return False, f"Pigeon {pigeon} hole is not strict int: {type(hole)}"
        if hole < 0 or hole >= h:
            return False, f"Pigeon {pigeon} hole {hole} out of range [0, {h - 1}]"
        if (pigeon, hole) in blocked_set:
            return False, f"Pigeon {pigeon} placed in blocked hole {hole}"
        if hole in seen_holes:
            return False, f"Two pigeons assigned to hole {hole}"
        seen_holes.add(hole)

    return True, "Valid PHP assignment"


# -------------------------------------------------------------
# 3. Latin-Square Completion
# -------------------------------------------------------------
def encode_latin_square(
    order: int, prefilled: List[List[int]]
) -> Tuple[int, List[List[int]], Dict[Tuple[int, int, int], int]]:
    """Encodes Latin-Square completion into CNF."""
    var_map: Dict[Tuple[int, int, int], int] = {}
    var_counter = 1
    for r in range(order):
        for c in range(order):
            for v in range(order):
                var_map[(r, c, v)] = var_counter
                var_counter += 1

    clauses: List[List[int]] = []
    # Each cell has at least one value
    for r in range(order):
        for c in range(order):
            clauses.append([var_map[(r, c, v)] for v in range(order)])

    # Each cell has at most one value
    for r in range(order):
        for c in range(order):
            for v1 in range(order):
                for v2 in range(v1 + 1, order):
                    clauses.append([-var_map[(r, c, v1)], -var_map[(r, c, v2)]])

    # Each value appears at most once in each row
    for r in range(order):
        for v in range(order):
            for c1 in range(order):
                for c2 in range(c1 + 1, order):
                    clauses.append([-var_map[(r, c1, v)], -var_map[(r, c2, v)]])

    # Each value appears at most once in each column
    for c in range(order):
        for v in range(order):
            for r1 in range(order):
                for r2 in range(r1 + 1, order):
                    clauses.append([-var_map[(r1, c, v)], -var_map[(r2, c, v)]])

    # Prefilled cells
    for r, c, v in prefilled:
        clauses.append([var_map[(r, c, v)]])

    return var_counter - 1, clauses, var_map


def decode_latin_square(
    order: int, model: Dict[int, int], var_map: Dict[Tuple[int, int, int], int]
) -> Dict[str, Any]:
    grid = [[0 for _ in range(order)] for _ in range(order)]
    for r in range(order):
        for c in range(order):
            for v in range(order):
                if model.get(var_map[(r, c, v)], 0) == 1:
                    grid[r][c] = v
                    break
    return {"grid": grid}


def check_latin_square_solution(case: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[bool, str]:
    order = case["order"]
    prefilled = case.get("prefilled", [])
    grid = solution.get("grid")
    if not isinstance(grid, list) or len(grid) != order:
        return False, f"Expected grid of {order} rows, got {grid}"

    for r in range(order):
        row = grid[r]
        if not isinstance(row, list) or len(row) != order:
            return False, f"Row {r} invalid"
        row_vals = set()
        for c, v in enumerate(row):
            if type(v) is not int:
                return False, f"Cell ({r}, {c}) is not strict int"
            if v < 0 or v >= order:
                return False, f"Cell ({r}, {c}) value {v} out of range [0, {order - 1}]"
            row_vals.add(v)
        if len(row_vals) != order:
            return False, f"Row {r} has duplicate values"

    for c in range(order):
        col_vals = {grid[r][c] for r in range(order)}
        if len(col_vals) != order:
            return False, f"Col {c} has duplicate values"

    for r, c, v in prefilled:
        if grid[r][c] != v:
            return False, f"Prefilled cell ({r}, {c}) expected {v}, got {grid[r][c]}"

    return True, "Valid Latin Square completion"


# -------------------------------------------------------------
# 4. Tseitin Parity Formulas
# -------------------------------------------------------------
def encode_tseitin(
    vertices: int, edges: List[List[int]], charges: List[int]
) -> Tuple[int, List[List[int]], Dict[int, int]]:
    """Encodes Tseitin parity formula into CNF."""
    # Variable for each edge 1..num_edges
    num_edges = len(edges)
    edge_map = {e_idx: e_idx + 1 for e_idx in range(num_edges)}

    # Incidence list for each vertex
    incident: Dict[int, List[Tuple[int, int]]] = {v: [] for v in range(vertices)}
    for e_idx, (u, v) in enumerate(edges):
        incident[u].append((e_idx, edge_map[e_idx]))
        incident[v].append((e_idx, edge_map[e_idx]))

    clauses: List[List[int]] = []

    for v in range(vertices):
        inc_vars = [var for _, var in incident[v]]
        target_parity = charges[v] % 2
        # Generate parity constraints: for every combination of signs, sum must match parity
        # For small degrees (<= 4), iterate over all 2^deg assignments:
        deg = len(inc_vars)
        for mask in range(1 << deg):
            popcount = bin(mask).count("1")
            if popcount % 2 != target_parity:
                # This assignment violates the parity -> forbid it
                clause = []
                for bit_idx in range(deg):
                    var = inc_vars[bit_idx]
                    if (mask >> bit_idx) & 1:
                        clause.append(-var)
                    else:
                        clause.append(var)
                clauses.append(clause)

    return num_edges, clauses, edge_map


def decode_tseitin(num_edges: int, model: Dict[int, int]) -> Dict[str, Any]:
    vals = [model.get(e_idx + 1, 0) for e_idx in range(num_edges)]
    return {"edge_values": vals}


def check_tseitin_solution(case: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[bool, str]:
    vertices = case["vertices"]
    edges = case["edges"]
    charges = case["charges"]
    vals = solution.get("edge_values")
    if not isinstance(vals, list) or len(vals) != len(edges):
        return False, f"Expected edge_values of length {len(edges)}, got {vals}"

    for idx, v in enumerate(vals):
        if type(v) is not int:
            return False, f"Edge {idx} value is not strict int"
        if v not in {0, 1}:
            return False, f"Edge {idx} value {v} not in {{0, 1}}"

    incident = {v: [] for v in range(vertices)}
    for e_idx, (u, v) in enumerate(edges):
        incident[u].append(e_idx)
        incident[v].append(e_idx)

    for v in range(vertices):
        parity_sum = sum(vals[e] for e in incident[v]) % 2
        if parity_sum != (charges[v] % 2):
            return (
                False,
                f"Vertex {v} parity check failed: got {parity_sum}, expected {charges[v] % 2}",
            )

    return True, "Valid Tseitin parity solution"


# -------------------------------------------------------------
# 5. Exact Cover & Polyomino Tiling
# -------------------------------------------------------------
def encode_tiling(
    rows: int, cols: int, tiles: List[List[List[int]]], blocked: Optional[List[List[int]]] = None
) -> Tuple[int, List[List[int]], Dict[int, int]]:
    """Encodes polyomino tiling exact cover into CNF."""
    blocked_set = {tuple(b) for b in (blocked or [])}
    num_tiles = len(tiles)
    tile_var = {t_idx: t_idx + 1 for t_idx in range(num_tiles)}

    # Cell to covering tiles map
    cell_covers: Dict[Tuple[int, int], List[int]] = {}
    for r in range(rows):
        for c in range(cols):
            if (r, c) not in blocked_set:
                cell_covers[(r, c)] = []

    for t_idx, squares in enumerate(tiles):
        if any((r, c) in blocked_set for r, c in squares):
            continue
        for r, c in squares:
            if (r, c) in cell_covers:
                cell_covers[(r, c)].append(tile_var[t_idx])

    clauses: List[List[int]] = []
    # Each valid square covered by exactly one tile
    for (r, c), covering_tiles in cell_covers.items():
        if not covering_tiles:
            # Uncoverable cell -> empty clause
            clauses.append([])
            continue
        # At least one
        clauses.append(list(covering_tiles))
        # At most one
        for i in range(len(covering_tiles)):
            for j in range(i + 1, len(covering_tiles)):
                clauses.append([-covering_tiles[i], -covering_tiles[j]])

    return num_tiles, clauses, tile_var


def decode_tiling(num_tiles: int, model: Dict[int, int]) -> Dict[str, Any]:
    selected = [t_idx for t_idx in range(num_tiles) if model.get(t_idx + 1, 0) == 1]
    return {"selected_tiles": selected}


def check_tiling_solution(case: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[bool, str]:
    rows = case["rows"]
    cols = case["cols"]
    tiles = case["tiles"]
    blocked_set = {tuple(b) for b in case.get("blocked", [])}
    selected = solution.get("selected_tiles")
    if not isinstance(selected, list):
        return False, "selected_tiles must be a list"

    covered: Set[Tuple[int, int]] = set()
    for t_idx in selected:
        if type(t_idx) is not int:
            return False, f"Tile index {t_idx} is not strict int"
        if t_idx < 0 or t_idx >= len(tiles):
            return False, f"Tile index {t_idx} out of range"
        for r, c in tiles[t_idx]:
            if (r, c) in blocked_set:
                return False, f"Tile {t_idx} covers blocked square ({r}, {c})"
            if (r, c) in covered:
                return False, f"Square ({r}, {c}) covered multiple times"
            covered.add((r, c))

    expected_cells = {(r, c) for r in range(rows) for c in range(cols) if (r, c) not in blocked_set}
    if covered != expected_cells:
        missing = expected_cells - covered
        return False, f"Tiling incomplete: {len(missing)} squares uncovered"

    return True, "Valid exact cover tiling"


def check_problem_solution(case: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[bool, str]:
    """Unified problem-level checker dispatcher."""
    fam = case.get("family")
    if fam == "coloring":
        return check_coloring_solution(case, solution)
    elif fam == "php":
        return check_php_solution(case, solution)
    elif fam == "latin_square":
        return check_latin_square_solution(case, solution)
    elif fam == "tseitin":
        return check_tseitin_solution(case, solution)
    elif fam == "tiling":
        return check_tiling_solution(case, solution)
    else:
        return False, f"Unknown problem family: {fam}"
