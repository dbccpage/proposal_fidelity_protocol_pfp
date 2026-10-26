"""Topological simplex normal form and exact integral homology.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

# =============================================================================
# Part 8: Topological Simplex Normal Form (TSNF) & Exact Integral Homology
# =============================================================================


@dataclass(frozen=True)
class TsnfResult:
    """Evaluation result for Topological Simplex Normal Form (TSNF)."""

    is_tsnf: bool
    status: str  # "Accept", "Reject", "Refuse"
    canonical_vertex_order: bool
    stokes_nilpotent: bool
    smith_invariant_divisibility: bool
    euler_poincare_consistent: bool
    betti_numbers: dict[str, int]
    torsion_coefficients: list[int]
    euler_characteristic: int
    defects: tuple[str, ...]


def _find_snf_pivot(A: list[list[int]], k: int, m: int, n: int) -> tuple[int, int] | None:
    candidates = (
        (abs(A[row][column]), row, column)
        for row in range(k, m)
        for column in range(k, n)
        if A[row][column] != 0
    )
    match = min(candidates, default=None)
    return None if match is None else (match[1], match[2])


def _swap_snf_pivot(A: list[list[int]], k: int, p_r: int, p_c: int, m: int) -> None:
    if p_r != k:
        A[k], A[p_r] = A[p_r], A[k]
    if p_c != k:
        for r in range(m):
            A[r][k], A[r][p_c] = A[r][p_c], A[r][k]


def _eliminate_snf_row_col(A: list[list[int]], k: int, m: int, n: int) -> bool:
    changed = False
    pivot = A[k][k]
    for r in range(k + 1, m):
        if A[r][k] != 0:
            q = A[r][k] // pivot
            for c in range(k, n):
                A[r][c] -= q * A[k][c]
            if A[r][k] != 0:
                changed = True
    for c in range(k + 1, n):
        if A[k][c] != 0:
            q = A[k][c] // pivot
            for r in range(k, m):
                A[r][c] -= q * A[r][k]
            if A[k][c] != 0:
                changed = True
    return changed


def _repair_snf_divisibility(A: list[list[int]], k: int, m: int, n: int) -> bool:
    """Returns True if a divisibility violation was found and row k updated."""
    pivot = A[k][k]
    violating_row = next(
        (
            row
            for row in range(k + 1, m)
            for column in range(k + 1, n)
            if A[row][column] % pivot != 0
        ),
        None,
    )
    if violating_row is None:
        return False
    for column in range(k, n):
        A[k][column] += A[violating_row][column]
    return True


def _reduce_snf_step(A: list[list[int]], k: int, m: int, n: int) -> None:
    while True:
        pivot_coord = _find_snf_pivot(A, k, m, n)
        if pivot_coord is None:
            break
        p_r, p_c = pivot_coord
        _swap_snf_pivot(A, k, p_r, p_c, m)

        changed = _eliminate_snf_row_col(A, k, m, n)
        if not changed:
            if not _repair_snf_divisibility(A, k, m, n):
                break

    if k < m and k < n and A[k][k] < 0:
        for c in range(k, n):
            A[k][c] = -A[k][c]


def compute_smith_normal_form(matrix: Sequence[Sequence[int]]) -> list[int]:
    """Pure exact integer Smith Normal Form reduction over Z.

    Transforms matrix M into diagonal form diag(d_1, d_2, ..., d_r)
    such that d_i > 0 and d_i | d_{i+1} for all i.
    Returns the positive diagonal invariant factors.
    """
    if not matrix or not matrix[0]:
        return []

    A = [list(row) for row in matrix]
    m, n = len(A), len(A[0])
    min_dim = min(m, n)

    for k in range(min_dim):
        _reduce_snf_step(A, k, m, n)

    diag = [abs(A[i][i]) for i in range(min_dim) if A[i][i] != 0]
    return sorted(diag)


def _check_simplex_duplicates(
    vertices: Sequence[int],
    edges: Sequence[tuple[int, int]],
    faces: Sequence[tuple[int, int, int]],
    tetrahedra: Sequence[tuple[int, int, int, int]],
) -> tuple[bool, list[str]]:
    defects: list[str] = []
    canonical = True
    if len(vertices) != len(set(vertices)) or list(vertices) != sorted(set(vertices)):
        canonical = False
        defects.append(f"Non-canonical vertex list (unsorted or duplicates): {vertices}")
    if len(edges) != len(set(edges)):
        canonical = False
        defects.append("Duplicate edges declared in 1-skeleton")
    if len(faces) != len(set(faces)):
        canonical = False
        defects.append("Duplicate faces declared in 2-skeleton")
    if len(tetrahedra) != len(set(tetrahedra)):
        canonical = False
        defects.append("Duplicate tetrahedra declared in 3-skeleton")
    return canonical, defects


def _check_simplex_ordering(
    vertices: Sequence[int],
    edges: Sequence[tuple[int, int]],
    faces: Sequence[tuple[int, int, int]],
    tetrahedra: Sequence[tuple[int, int, int, int]],
) -> tuple[bool, list[str]]:
    canonical, defects = _check_simplex_duplicates(vertices, edges, faces, tetrahedra)

    for e in edges:
        if len(e) != 2 or e[0] >= e[1]:
            canonical = False
            defects.append(f"Non-canonical edge orientation or duplicate: {e}")
    for f in faces:
        if len(f) != 3 or not (f[0] < f[1] < f[2]):
            canonical = False
            defects.append(f"Non-canonical face orientation or duplicate: {f}")
    for t in tetrahedra:
        if len(t) != 4 or not (t[0] < t[1] < t[2] < t[3]):
            canonical = False
            defects.append(f"Non-canonical tetrahedron orientation or duplicate: {t}")
    return canonical, defects


def _build_tsnf_boundary_matrices(
    vertices: Sequence[int],
    edges: Sequence[tuple[int, int]],
    faces: Sequence[tuple[int, int, int]],
    tetrahedra: Sequence[tuple[int, int, int, int]],
    defects: list[str],
) -> tuple[list[list[int]], list[list[int]], list[list[int]]]:
    n_v, n_e, n_f, n_t = len(vertices), len(edges), len(faces), len(tetrahedra)
    v_map = {v: i for i, v in enumerate(sorted(set(vertices)))}
    e_map = {e: j for j, e in enumerate(edges)}
    f_map = {f: k for k, f in enumerate(faces)}
    d1 = _build_edge_boundary(edges, v_map, n_v, n_e)
    d2 = _build_face_boundary(faces, e_map, n_e, n_f, defects)
    d3 = _build_tetrahedron_boundary(tetrahedra, f_map, n_f, n_t, defects)
    return d1, d2, d3


def _build_edge_boundary(
    edges: Sequence[tuple[int, int]], v_map: dict[int, int], n_v: int, n_e: int
) -> list[list[int]]:
    boundary: list[list[int]] = [[0] * n_e for _ in range(n_v)]
    for j, (u, v) in enumerate(edges):
        if u in v_map and v in v_map:
            boundary[v_map[u]][j] = -1
            boundary[v_map[v]][j] = 1
    return boundary


def _build_face_boundary(
    faces: Sequence[tuple[int, int, int]],
    edge_map: dict[tuple[int, int], int],
    n_e: int,
    n_f: int,
    defects: list[str],
) -> list[list[int]]:
    boundary: list[list[int]] = [[0] * n_f for _ in range(n_e)]
    for column, face in enumerate(faces):
        _add_face_boundary(boundary, column, face, edge_map, defects)
    return boundary


def _add_face_boundary(
    boundary: list[list[int]],
    column: int,
    face: tuple[int, int, int],
    edge_map: dict[tuple[int, int], int],
    defects: list[str],
) -> None:
    u, v, w = face
    for (e_u, e_v), sign in [((v, w), 1), ((u, w), -1), ((u, v), 1)]:
        if (e_u, e_v) in edge_map:
            boundary[edge_map[(e_u, e_v)]][column] += sign
        elif (e_v, e_u) in edge_map:
            boundary[edge_map[(e_v, e_u)]][column] -= sign
        else:
            defects.append(f"Face boundary edge ({e_u}, {e_v}) not present in edge list")


def _build_tetrahedron_boundary(
    tetrahedra: Sequence[tuple[int, int, int, int]],
    face_map: dict[tuple[int, int, int], int],
    n_f: int,
    n_t: int,
    defects: list[str],
) -> list[list[int]]:
    boundary: list[list[int]] = [[0] * n_t for _ in range(n_f)]
    for m, (u, v, w, x) in enumerate(tetrahedra):
        for f_face, sign in [
            ((v, w, x), 1),
            ((u, w, x), -1),
            ((u, v, x), 1),
            ((u, v, w), -1),
        ]:
            if f_face in face_map:
                boundary[face_map[f_face]][m] += sign
            else:
                defects.append(f"Tetrahedron boundary face {f_face} not present in face list")
    return boundary


def _check_stokes_nilpotency(
    boundaries: tuple[list[list[int]], list[list[int]], list[list[int]]],
    dimensions: tuple[int, int, int, int],
    defects: list[str],
) -> bool:
    d1, d2, d3 = boundaries
    n_v, n_e, n_f, n_t = dimensions
    first = _first_nonzero_product(d1, d2, n_v, n_e, n_f)
    if first is not None:
        row, column, product = first
        defects.append(
            f"Stokes nilpotency failure at d1.d2 (vertex {row}, face {column}): prod={product}"
        )
        return False
    second = _first_nonzero_product(d2, d3, n_e, n_f, n_t)
    if second is not None:
        row, column, product = second
        defects.append(
            f"Stokes nilpotency failure at d2.d3 (edge {row}, tetrahedron {column}): prod={product}"
        )
        return False
    return True


def _first_nonzero_product(
    left: list[list[int]], right: list[list[int]], rows: int, inner: int, columns: int
) -> tuple[int, int, int] | None:
    products = (
        (row, column, sum(left[row][k] * right[k][column] for k in range(inner)))
        for row in range(rows)
        for column in range(columns)
    )
    return next((entry for entry in products if entry[2] != 0), None)


def _check_invariant_divisibility(
    factors_list: Sequence[Sequence[int]],
    defects: list[str],
) -> bool:
    divisible = True
    for s in factors_list:
        for i in range(len(s) - 1):
            if s[i + 1] % s[i] != 0:
                divisible = False
                defects.append(
                    f"Invariant factor divisibility violated: {s[i]} does not divide {s[i + 1]}"
                )
    return divisible


def _compute_tsnf_homology_and_euler(
    dimensions: tuple[int, int, int, int],
    ranks: tuple[int, int, int],
    defects: list[str],
) -> tuple[dict[str, int], int, bool]:
    n_v, n_e, n_f, n_t = dimensions
    rank1, rank2, rank3 = ranks
    b0 = n_v - rank1
    b1 = n_e - rank1 - rank2
    if n_t > 0:
        b2 = n_f - rank2 - rank3
        b3 = n_t - rank3
        betti = {"b0": b0, "b1": b1, "b2": b2, "b3": b3}
        chi_cells = n_v - n_e + n_f - n_t
        chi_homology = b0 - b1 + b2 - b3
    else:
        b2 = n_f - rank2
        betti = {"b0": b0, "b1": b1, "b2": b2}
        chi_cells = n_v - n_e + n_f
        chi_homology = b0 - b1 + b2

    euler_consistent = chi_cells == chi_homology
    if not euler_consistent:
        defects.append(
            f"Euler-Poincare mismatch: chi_cells={chi_cells} != chi_homology={chi_homology}"
        )
    return betti, chi_cells, euler_consistent


def verify_tsnf(
    vertices: Sequence[int],
    edges: Sequence[tuple[int, int]],
    faces: Sequence[tuple[int, int, int]] = (),
    tetrahedra: Sequence[tuple[int, int, int, int]] = (),
) -> TsnfResult:
    """Verify TSNF invariants exactly on a cell complex up to dimension three."""
    canonical_order, defects = _check_simplex_ordering(vertices, edges, faces, tetrahedra)
    dimensions = len(vertices), len(edges), len(faces), len(tetrahedra)
    boundaries = _build_tsnf_boundary_matrices(vertices, edges, faces, tetrahedra, defects)
    stokes_nilpotent = _check_stokes_nilpotency(boundaries, dimensions, defects)

    d1, d2, d3 = boundaries
    snf1 = compute_smith_normal_form(d1)
    snf2 = compute_smith_normal_form(d2)
    snf3 = compute_smith_normal_form(d3) if dimensions[3] > 0 else []

    divisibility = _check_invariant_divisibility((snf1, snf2, snf3), defects)
    torsion = [d for d in (snf1 + snf2 + snf3) if d > 1]

    betti, chi_cells, euler_consistent = _compute_tsnf_homology_and_euler(
        dimensions, (len(snf1), len(snf2), len(snf3)), defects
    )

    is_tsnf = all((canonical_order, stokes_nilpotent, divisibility, euler_consistent, not defects))
    status = "Accept" if is_tsnf else "Reject" if not canonical_order else "Refuse"

    return TsnfResult(
        is_tsnf=is_tsnf,
        status=status,
        canonical_vertex_order=canonical_order,
        stokes_nilpotent=stokes_nilpotent,
        smith_invariant_divisibility=divisibility,
        euler_poincare_consistent=euler_consistent,
        betti_numbers=betti,
        torsion_coefficients=torsion,
        euler_characteristic=chi_cells,
        defects=tuple(defects),
    )
