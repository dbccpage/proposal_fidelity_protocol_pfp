"""Simplicial Cohomology, Alexander-Whitney Cup Products, and Exact Witness Synthesis."""

from __future__ import annotations

import itertools
from fractions import Fraction

from .rational_linear_algebra import exact_rank, exact_solve, nullspace_basis


def close_simplicial_complex(
    maximal_simplices: list[list[int]],
) -> dict[int, list[tuple[int, ...]]]:
    """Downset closure from maximal simplices into graded simplex lists.

    Returns dict mapping dim -> sorted list of simplices (as sorted vertex tuples).
    """
    dim_simplices: dict[int, set[tuple[int, ...]]] = {d: set() for d in range(5)}

    for s in maximal_simplices:
        verts = tuple(sorted(s))
        dim = len(verts) - 1
        if dim > 4 or dim < 0:
            raise ValueError(f"Simplex dimension {dim} out of bounds (<= 4)")
        # Add all subsets
        for k in range(1, len(verts) + 1):
            for sub in itertools.combinations(verts, k):
                dim_simplices[k - 1].add(sub)

    return {d: sorted(list(dim_simplices[d])) for d in range(5)}


def build_boundary_matrix(
    simplices_k: list[tuple[int, ...]], simplices_k_minus_1: list[tuple[int, ...]]
) -> list[list[Fraction]]:
    """Build boundary matrix d_k : C_k -> C_{k-1} with standard signs (-1)^i."""
    m = len(simplices_k_minus_1)
    n = len(simplices_k)
    if m == 0 or n == 0:
        return []

    idx_map = {s: i for i, s in enumerate(simplices_k_minus_1)}
    mat: list[list[Fraction]] = [[Fraction(0) for _ in range(n)] for _ in range(m)]

    for j, s in enumerate(simplices_k):
        # s has length k + 1
        for i in range(len(s)):
            face = s[:i] + s[i + 1 :]
            sign = Fraction(1 if i % 2 == 0 else -1)
            row = idx_map[face]
            mat[row][j] = sign

    return mat


def compute_betti_numbers(graded_simplices: dict[int, list[tuple[int, ...]]]) -> list[int]:
    """Compute rational Betti numbers b_0, b_1, b_2, b_3, b_4."""
    # d_k : C_k -> C_{k-1}
    ranks: dict[int, int] = {}
    for k in range(1, 5):
        d_k = build_boundary_matrix(graded_simplices[k], graded_simplices[k - 1])
        ranks[k] = exact_rank(d_k)
    ranks[0] = 0
    ranks[5] = 0

    betti = []
    for k in range(5):
        n_k = len(graded_simplices[k])
        # b_k = dim C_k - rank(d_k) - rank(d_{k+1})
        b_k = n_k - ranks[k] - ranks[k + 1]
        betti.append(b_k)
    return betti


def compute_cohomology_basis(
    graded_simplices: dict[int, list[tuple[int, ...]]], k: int
) -> list[dict[tuple[int, ...], Fraction]]:
    """Find a basis of cocycles representing H^k(X; Q).

    delta_k : C^k -> C^{k+1} is transpose of d_{k+1} : C_{k+1} -> C_k.
    B^k = image of delta_{k-1} (transpose of d_k).
    """
    n_k = len(graded_simplices[k])
    if n_k == 0:
        return []

    # delta_k : C^k -> C^{k+1} is transpose of d_{k+1} : C_{k+1} -> C_k
    if k < 4:
        d_k_plus_1 = build_boundary_matrix(graded_simplices[k + 1], graded_simplices[k])
        if d_k_plus_1 and d_k_plus_1[0]:
            delta_k = list(map(list, zip(*d_k_plus_1)))
        else:
            delta_k = []
    else:
        delta_k = []

    # Z^k = ker(delta_k)
    if delta_k and len(delta_k) > 0 and len(delta_k[0]) > 0:
        z_k_basis = nullspace_basis(delta_k)
    else:
        # All k-cochains are cocycles if no k+1 simplices
        z_k_basis = [[Fraction(1 if i == j else 0) for i in range(n_k)] for j in range(n_k)]

    if not z_k_basis:
        return []

    # B^k = image of delta_{k-1} = col space of delta_{k-1} (transpose of d_k)
    if k > 0:
        d_k = build_boundary_matrix(graded_simplices[k], graded_simplices[k - 1])
        # delta_{k-1} is (n_k x n_{k-1}) matrix whose columns are delta_{k-1}(e_j)
        # transpose of d_k: row i of d_k is col i of delta_{k-1}
        # In d_k: d_k[i][j] is coefficient of face i in d(simplex j).
        # Coboundary of face i is sum_j d_k[i][j] simplex j.
        # So column i of delta_{k-1} is [d_k[i][j] for j in range(n_k)].
        b_k_cols: list[list[Fraction]] = []
        for i in range(len(graded_simplices[k - 1])):
            col = [d_k[i][j] for j in range(n_k)]
            b_k_cols.append(col)
    else:
        b_k_cols = []

    # Select vectors from z_k_basis that are linearly independent modulo B^k
    # We build a matrix with B^k columns, and greedily add vectors from z_k_basis if rank increases
    mat_cols = [[val for val in col] for col in b_k_cols]
    curr_rank = exact_rank(list(map(list, zip(*mat_cols)))) if mat_cols else 0

    basis_cocycles: list[list[Fraction]] = []
    for vec in z_k_basis:
        test_cols = mat_cols + [vec]
        test_mat = list(map(list, zip(*test_cols)))
        new_rank = exact_rank(test_mat)
        if new_rank > curr_rank:
            mat_cols.append(vec)
            curr_rank = new_rank
            basis_cocycles.append(vec)

    # Convert to sparse dict
    res = []
    for vec in basis_cocycles:
        c_dict = {}
        for idx, val in enumerate(vec):
            if val != 0:
                c_dict[graded_simplices[k][idx]] = val
        res.append(c_dict)
    return res


def compute_homology_basis(
    graded_simplices: dict[int, list[tuple[int, ...]]], k: int
) -> list[dict[tuple[int, ...], Fraction]]:
    """Find a basis of cycles representing H_k(X; Q)."""
    n_k = len(graded_simplices[k])
    if n_k == 0:
        return []

    if k > 0:
        d_k = build_boundary_matrix(graded_simplices[k], graded_simplices[k - 1])
        z_k_basis = nullspace_basis(d_k)
    else:
        z_k_basis = [[Fraction(1 if i == j else 0) for i in range(n_k)] for j in range(n_k)]

    if not z_k_basis:
        return []

    # B_k = image of d_{k+1}
    if k < 4:
        d_k_plus_1 = build_boundary_matrix(graded_simplices[k + 1], graded_simplices[k])
        # columns of d_{k+1} are elements of B_k
        b_k_cols = [
            [d_k_plus_1[i][j] for i in range(n_k)] for j in range(len(graded_simplices[k + 1]))
        ]
    else:
        b_k_cols = []

    mat_cols = [[val for val in col] for col in b_k_cols]
    curr_rank = exact_rank(list(map(list, zip(*mat_cols)))) if mat_cols else 0

    basis_cycles: list[list[Fraction]] = []
    for vec in z_k_basis:
        test_cols = mat_cols + [vec]
        test_mat = list(map(list, zip(*test_cols)))
        new_rank = exact_rank(test_mat)
        if new_rank > curr_rank:
            mat_cols.append(vec)
            curr_rank = new_rank
            basis_cycles.append(vec)

    res = []
    for vec in basis_cycles:
        c_dict = {}
        for idx, val in enumerate(vec):
            if val != 0:
                c_dict[graded_simplices[k][idx]] = val
        res.append(c_dict)
    return res


def alexander_whitney_product(
    alpha: dict[tuple[int, ...], Fraction],
    beta: dict[tuple[int, ...], Fraction],
    p: int,
    q: int,
    simplices_p_plus_q: list[tuple[int, ...]],
) -> dict[tuple[int, ...], Fraction]:
    """Compute Alexander-Whitney cup product alpha smile beta on (p+q)-simplices.

    For [v_0, ..., v_{p+q}] with v_0 < ... < v_{p+q}:
      (alpha smile beta)[v_0, ..., v_{p+q}] = alpha[v_0, ..., v_p] * beta[v_p, ..., v_{p+q}].
    """
    res: dict[tuple[int, ...], Fraction] = {}
    for s in simplices_p_plus_q:
        front_face = s[: p + 1]
        back_face = s[p:]
        val_a = alpha.get(front_face, Fraction(0))
        val_b = beta.get(back_face, Fraction(0))
        prod = val_a * val_b
        if prod != 0:
            res[s] = prod
    return res


def evaluate_cochain_on_chain(
    cochain: dict[tuple[int, ...], Fraction], chain: dict[tuple[int, ...], Fraction]
) -> Fraction:
    val = Fraction(0)
    for s, c_val in chain.items():
        if s in cochain:
            val += cochain[s] * c_val
    return val


def find_primitive_coboundary(
    omega: dict[tuple[int, ...], Fraction],
    k: int,  # degree of omega
    graded_simplices: dict[int, list[tuple[int, ...]]],
) -> dict[tuple[int, ...], Fraction] | None:
    """Find gamma in C^{k-1} such that delta_{k-1}(gamma) = omega."""
    if k == 0:
        return None
    simplices_k = graded_simplices[k]
    simplices_k_minus_1 = graded_simplices[k - 1]

    d_k = build_boundary_matrix(simplices_k, simplices_k_minus_1)
    # delta_{k-1} is transpose of d_k
    # We want delta_{k-1} gamma = omega.
    # Rows are k-simplices (len simplices_k = len(d_k[0])), cols are k-1-simplices (len simplices_k_minus_1 = len(d_k))
    # matrix A has shape (len(simplices_k), len(simplices_k_minus_1))
    # A[j][i] = d_k[i][j]
    m = len(simplices_k)
    n = len(simplices_k_minus_1)
    A = [[d_k[i][j] for i in range(n)] for j in range(m)]

    b = [core.get(s, Fraction(0)) for s in simplices_k]
    sol = exact_solve(A, b)
    if sol is None:
        return None

    res = {}
    for idx, val in enumerate(sol):
        if val != 0:
            res[simplices_k_minus_1[idx]] = val
    return res
