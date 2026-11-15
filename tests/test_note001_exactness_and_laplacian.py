"""
Executable verification for Derivations ATL-N001-007, ATL-N001-008, ATL-N001-011, and ATL-N001-012 (Note 001).

Derivations:
- AUDIT-N001-007: Circulation characterization of exactness (ATL-N001-007)
- AUDIT-N001-008: General-graph exactness criterion via spanning-tree path integration (ATL-N001-008)
- AUDIT-N001-011: p-Laplacian optimality and Euler-Lagrange stationarity for p in (1, inf) (ATL-N001-011)
- AUDIT-N001-012: Hilbertian L2 Hodge decomposition and Moore-Penrose potential (ATL-N001-012)
"""

from fractions import Fraction
import math
import pytest


# ---------------------------------------------------------------------------
# Exact Rational Graph Model & Linear Algebra Helpers
# ---------------------------------------------------------------------------

class ExactRationalGraph:
    """Exact rational graph model supporting coboundary, circulations, and tree integration."""

    def __init__(self, num_vertices, edges, weights=None):
        self.num_vertices = num_vertices
        self.edges = edges  # list of (u, v) tuples
        if weights is None:
            self.weights = [Fraction(1) for _ in edges]
        else:
            self.weights = [Fraction(w) for w in weights]
        if any(w <= 0 for w in self.weights):
            raise ValueError("Edge weights must be strictly positive")

    @property
    def num_edges(self):
        return len(self.edges)

    def d0(self, potential):
        """Evaluate d0 f: (d0 f)_e = f(v) - f(u) for edge (u, v)."""
        return [potential[v] - potential[u] for (u, v) in self.edges]

    def d0_star(self, chain):
        """Evaluate adjoint divergence d0* y."""
        div = [Fraction(0) for _ in range(self.num_vertices)]
        for i, (u, v) in enumerate(self.edges):
            div[u] += chain[i]
            div[v] -= chain[i]
        return div

    def pairing(self, chain, cochain):
        return sum(chain[i] * cochain[i] for i in range(self.num_edges))

    def connected_components(self):
        visited = set()
        components = []
        adj = {v: [] for v in range(self.num_vertices)}
        for idx, (u, v) in enumerate(self.edges):
            adj[u].append((v, idx, 1))
            adj[v].append((u, idx, -1))

        for v in range(self.num_vertices):
            if v not in visited:
                comp_verts = []
                queue = [v]
                visited.add(v)
                while queue:
                    curr = queue.pop(0)
                    comp_verts.append(curr)
                    for nxt, _, _ in adj[curr]:
                        if nxt not in visited:
                            visited.add(nxt)
                            queue.append(nxt)
                components.append(sorted(comp_verts))
        return components

    def spanning_forest(self):
        """Compute spanning tree for each connected component."""
        tree_edges = []
        visited = set()
        adj = {v: [] for v in range(self.num_vertices)}
        for idx, (u, v) in enumerate(self.edges):
            adj[u].append((v, idx, 1))
            adj[v].append((u, idx, -1))

        for comp in self.connected_components():
            root = comp[0]
            comp_visited = {root}
            queue = [root]
            while queue:
                curr = queue.pop(0)
                for nxt, e_idx, sgn in adj[curr]:
                    if nxt not in comp_visited:
                        comp_visited.add(nxt)
                        visited.add(nxt)
                        tree_edges.append(e_idx)
                        queue.append(nxt)

        tree_set = set(tree_edges)
        chord_edges = [i for i in range(self.num_edges) if i not in tree_set]
        return tree_edges, chord_edges

    def fundamental_cycles(self):
        """Generate fundamental cycle circulation vectors for all chord edges."""
        tree_edges, chord_edges = self.spanning_forest()
        cycles = []

        adj_tree = {v: [] for v in range(self.num_vertices)}
        for e_idx in tree_edges:
            u, v = self.edges[e_idx]
            adj_tree[u].append((v, e_idx, 1))
            adj_tree[v].append((u, e_idx, -1))

        def find_tree_path(start, target):
            queue = [(start, [])]
            visited = {start}
            while queue:
                curr, path = queue.pop(0)
                if curr == target:
                    return path
                for nxt, e_idx, sgn in adj_tree[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append((nxt, path + [(e_idx, sgn)]))
            return None

        for chord_idx in chord_edges:
            u, v = self.edges[chord_idx]
            tree_path = find_tree_path(v, u)
            cycle_vec = [Fraction(0) for _ in range(self.num_edges)]
            cycle_vec[chord_idx] = Fraction(1)
            for e_idx, sgn in tree_path:
                cycle_vec[e_idx] += Fraction(sgn)
            cycles.append(cycle_vec)

        return cycles


def rational_matrix_rank(matrix):
    """Compute exact matrix rank via Gaussian elimination over Fraction."""
    A = [[Fraction(x) for x in row] for row in matrix]
    m = len(A)
    n = len(A[0]) if m > 0 else 0
    rank = 0
    for col in range(n):
        pivot = None
        for r in range(rank, m):
            if A[r][col] != Fraction(0):
                pivot = r
                break
        if pivot is None:
            continue
        A[rank], A[pivot] = A[pivot], A[rank]
        pv = A[rank][col]
        for c in range(col, n):
            A[rank][c] /= pv
        for r in range(m):
            if r != rank and A[r][col] != Fraction(0):
                factor = A[r][col]
                for c in range(col, n):
                    A[r][c] -= factor * A[rank][c]
        rank += 1
        if rank == m:
            break
    return rank


def rational_solve_linear_system(A, b):
    """Exact rational linear solve Ax = b via Gaussian elimination."""
    m = len(A)
    n = len(A[0])
    M = [A[r][:] + [b[r]] for r in range(m)]
    row = 0
    for col in range(n):
        pivot = None
        for r in range(row, m):
            if M[r][col] != Fraction(0):
                pivot = r
                break
        if pivot is None:
            continue
        M[row], M[pivot] = M[pivot], M[row]
        pv = M[row][col]
        for c in range(col, n + 1):
            M[row][c] /= pv
        for r in range(m):
            if r != row and M[r][col] != Fraction(0):
                factor = M[r][col]
                for c in range(col, n + 1):
                    M[r][c] -= factor * M[row][c]
        row += 1
    return [M[i][n] for i in range(n)]


# ---------------------------------------------------------------------------
# Test Suite 1: ATL-N001-007 (Circulation Characterization of Exactness)
# ---------------------------------------------------------------------------

def test_n001_007_exact_cochain_annihilates_all_circulations():
    """Verify that an exact cochain c = d0 f pairs to zero with all circulations."""
    edges = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)]
    g = ExactRationalGraph(5, edges)
    f = [Fraction(2), Fraction(-3), Fraction(5), Fraction(1), Fraction(-4)]
    c_exact = g.d0(f)

    circulations = g.fundamental_cycles()
    assert len(circulations) == 2
    for y in circulations:
        assert g.d0_star(y) == [Fraction(0)] * 5
        assert g.pairing(y, c_exact) == Fraction(0)


def test_n001_007_orthogonal_complement_dimension():
    """Verify rank-nullity relation dim(im d0) + dim(ker d0^T) = |E| exactly over Fraction."""
    edges = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)]
    n_v, n_e = 5, len(edges)
    d0 = [[Fraction(0)] * n_v for _ in range(n_e)]
    for i, (u, v) in enumerate(edges):
        d0[i][u] = Fraction(-1)
        d0[i][v] = Fraction(1)

    d0_T = [[d0[r][c] for r in range(n_e)] for c in range(n_v)]
    rank_d0 = rational_matrix_rank(d0)
    rank_d0_T = rational_matrix_rank(d0_T)
    nullity_d0_T = n_e - rank_d0_T
    assert rank_d0 == rank_d0_T == 4
    assert nullity_d0_T == 2
    assert rank_d0 + nullity_d0_T == n_e


def test_n001_007_non_exact_has_nonzero_pairing():
    """Verify that a cochain with non-zero cycle flux pairs non-trivially with circulations."""
    edges = [(0, 1), (1, 2), (2, 0)]
    g = ExactRationalGraph(3, edges)
    c_inexact = [Fraction(1), Fraction(0), Fraction(0)]
    y_cycle = [Fraction(1), Fraction(1), Fraction(1)]

    assert g.d0_star(y_cycle) == [Fraction(0), Fraction(0), Fraction(0)]
    pairing = g.pairing(y_cycle, c_inexact)
    assert pairing == Fraction(1) != Fraction(0)


def test_n001_007_negative_control_non_circulation_pairing_fails():
    """Verify that pairing an exact cochain with a non-circulation does not vanish."""
    edges = [(0, 1), (1, 2), (2, 0)]
    g = ExactRationalGraph(3, edges)
    f = [Fraction(0), Fraction(1), Fraction(3)]
    c = g.d0(f)  # [1, 2, -3]
    y_non_circ = [Fraction(1), Fraction(0), Fraction(0)]
    assert g.d0_star(y_non_circ) != [Fraction(0), Fraction(0), Fraction(0)]
    assert g.pairing(y_non_circ, c) == Fraction(1) != Fraction(0)


# ---------------------------------------------------------------------------
# Test Suite 2: ATL-N001-008 (General-Graph Exactness Criterion)
# ---------------------------------------------------------------------------

def test_n001_008_connected_graph_tree_integration():
    """Verify exact potential recovery on a connected graph via tree integration."""
    edges = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)]
    g = ExactRationalGraph(5, edges)
    f_orig = [Fraction(0), Fraction(4), Fraction(-1), Fraction(7), Fraction(2)]
    c = g.d0(f_orig)

    tree_edges, chord_edges = g.spanning_forest()
    f_rec = [Fraction(0)] * 5
    f_rec[1] = f_rec[0] + c[0]
    f_rec[2] = f_rec[1] + c[1]
    f_rec[3] = f_rec[2] + c[3]
    f_rec[4] = f_rec[3] + c[4]

    assert g.d0(f_rec) == c


def test_n001_008_disconnected_graph_forest_integration():
    """Verify exactness on a disconnected graph with two independent cycles."""
    edges = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]
    g = ExactRationalGraph(6, edges)
    f_orig = [Fraction(0), Fraction(3), Fraction(-2), Fraction(0), Fraction(5), Fraction(1)]
    c = g.d0(f_orig)

    cycles = g.fundamental_cycles()
    assert len(cycles) == 2
    for y in cycles:
        assert g.pairing(y, c) == Fraction(0)


def test_n001_008_negative_control_single_cycle_violation():
    """Verify that a single non-vanishing cycle pairing invalidates exactness."""
    edges = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)]
    g = ExactRationalGraph(5, edges)
    c_mutated = [Fraction(0), Fraction(0), Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    cycles = g.fundamental_cycles()
    pairings = [g.pairing(y, c_mutated) for y in cycles]
    assert any(p != Fraction(0) for p in pairings)


# ---------------------------------------------------------------------------
# Test Suite 3: ATL-N001-011 (p-Laplacian Optimality)
# ---------------------------------------------------------------------------

def test_n001_011_p_laplacian_strict_convexity():
    """Verify strict convexity of powered residual energy for p in (1, inf)."""
    weights = [1.0, 2.0, 1.5]
    r1 = [1.0, -2.0, 3.0]
    r2 = [2.0, 1.0, -1.0]
    r_mid = [0.5 * (r1[i] + r2[i]) for i in range(3)]

    for p in [1.2, 1.5, 2.0, 3.0]:
        E1 = sum(w * (abs(x) ** p) for w, x in zip(weights, r1)) / p
        E2 = sum(w * (abs(x) ** p) for w, x in zip(weights, r2)) / p
        E_mid = sum(w * (abs(x) ** p) for w, x in zip(weights, r_mid)) / p
        assert E_mid < 0.5 * (E1 + E2)


def _minimize_p_laplacian(edges, weights, c, p, tol=1e-7, max_iter=2000):
    """Pure-Python gradient descent with backtracking line search for p-Laplacian."""
    n_v = 3
    f_free = [0.0, 0.0]

    def loss_and_grad(f_f):
        f = [0.0, f_f[0], f_f[1]]
        df = [f[v] - f[u] for (u, v) in edges]
        r = [c[e] - df[e] for e in range(len(edges))]
        loss = sum(weights[e] * (abs(r[e]) ** p) / p for e in range(len(edges)))
        grad_r = [weights[e] * (abs(r[e]) ** (p - 1)) * (1.0 if r[e] >= 0 else -1.0) for e in range(len(edges))]
        div = [0.0] * n_v
        for e, (u, v) in enumerate(edges):
            div[u] += grad_r[e]
            div[v] -= grad_r[e]
        grad_free = [div[1], div[2]]
        return loss, grad_free, div, r

    alpha = 0.1
    for _ in range(max_iter):
        loss, g, div, r = loss_and_grad(f_free)
        g_norm = math.sqrt(g[0] ** 2 + g[1] ** 2)
        if g_norm < tol:
            break
        step = alpha
        while step > 1e-12:
            new_f = [f_free[0] - step * g[0], f_free[1] - step * g[1]]
            new_loss, _, _, _ = loss_and_grad(new_f)
            if new_loss < loss:
                f_free = new_f
                break
            step *= 0.5
        alpha = min(step * 1.2, 1.0)
    loss, g, div, r = loss_and_grad(f_free)
    return f_free, div, r


def test_n001_011_p_laplacian_euler_lagrange_condition():
    """Verify Euler-Lagrange condition d0^T (w |r|^{p-2} r) = 0 at the minimizer."""
    edges = [(0, 1), (1, 2), (2, 0)]
    weights = [1.0, 2.0, 3.0]
    c = [1.0, 1.0, 1.0]

    for p in [1.5, 2.0, 3.0, 4.0]:
        f_free, div, r = _minimize_p_laplacian(edges, weights, c, p, tol=1e-7)
        max_div = max(abs(x) for x in div)
        assert max_div < 1e-5


def test_n001_011_p_laplacian_dual_witness_circulation():
    """Verify that the normalized dual witness z_p* is a valid circulation."""
    edges = [(0, 1), (1, 2), (2, 0)]
    weights = [1.0, 2.0, 3.0]
    c = [1.0, 1.0, 1.0]
    p = 2.0
    q = 2.0

    f_free, div, r_opt = _minimize_p_laplacian(edges, weights, c, p, tol=1e-8)
    norm_r = (sum(weights[e] * (abs(r_opt[e]) ** p) for e in range(3))) ** (1.0 / p)
    z = [(weights[e] * (abs(r_opt[e]) ** (p - 1)) * (1.0 if r_opt[e] >= 0 else -1.0)) / (norm_r ** (p - 1)) for e in range(3)]

    div_z = [0.0] * 3
    for e, (u, v) in enumerate(edges):
        div_z[u] += z[e]
        div_z[v] -= z[e]

    dual_norm = (sum((weights[e] ** (1 - q)) * (abs(z[e]) ** q) for e in range(3))) ** (1.0 / q)
    pairing = sum(z[e] * c[e] for e in range(3))

    assert max(abs(x) for x in div_z) < 1e-6
    assert math.isclose(dual_norm, 1.0, rel_tol=1e-6)
    assert math.isclose(pairing, norm_r, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# Test Suite 4: ATL-N001-012 (L2 Hodge and Moore-Penrose)
# ---------------------------------------------------------------------------

def test_n001_012_moore_penrose_potential_exact_rational():
    """Verify exact rational Moore-Penrose potential on a weighted 3-cycle."""
    weights = [Fraction(1), Fraction(2), Fraction(3)]
    f = [Fraction(4, 11), Fraction(-3, 11), Fraction(-1, 11)]
    assert sum(f) == Fraction(0)

    df = [f[1] - f[0], f[2] - f[1], f[0] - f[2]]
    c = [Fraction(1), Fraction(1), Fraction(1)]
    r = [c[i] - df[i] for i in range(3)]
    assert r == [Fraction(18, 11), Fraction(9, 11), Fraction(6, 11)]

    Wr = [weights[i] * r[i] for i in range(3)]
    assert Wr == [Fraction(18, 11), Fraction(18, 11), Fraction(18, 11)]
    div = [-Wr[0] + Wr[2], Wr[0] - Wr[1], Wr[1] - Wr[2]]
    assert div == [Fraction(0), Fraction(0), Fraction(0)]


def test_n001_012_normal_equations_satisfaction():
    """Verify normal equations L f = d0^T W c with L = d0^T W d0 in exact rational arithmetic."""
    edges = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)]
    n_v, n_e = 5, len(edges)
    weights = [Fraction(1), Fraction(2), Fraction(3, 2), Fraction(5, 2), Fraction(6, 5), Fraction(3)]
    c = [Fraction(2), Fraction(-1), Fraction(1, 2), Fraction(6, 5), Fraction(-4, 5), Fraction(1)]

    d0 = [[Fraction(0)] * n_v for _ in range(n_e)]
    for i, (u, v) in enumerate(edges):
        d0[i][u] = Fraction(-1)
        d0[i][v] = Fraction(1)

    # L = d0^T W d0
    L = [[Fraction(0)] * n_v for _ in range(n_v)]
    for i in range(n_v):
        for j in range(n_v):
            L[i][j] = sum(d0[e][i] * weights[e] * d0[e][j] for e in range(n_e))

    # rhs = d0^T W c
    rhs = [sum(d0[e][i] * weights[e] * c[e] for e in range(n_e)) for i in range(n_v)]

    # Invertible augmented system with gauge sum(f) = 0
    M_L = [row[:] for row in L]
    M_b = rhs[:]
    M_L[0] = [Fraction(1)] * n_v
    M_b[0] = Fraction(0)

    f_mp = rational_solve_linear_system(M_L, M_b)
    assert sum(f_mp) == Fraction(0)

    Lf = [sum(L[i][j] * f_mp[j] for j in range(n_v)) for i in range(n_v)]
    assert Lf == rhs


def test_n001_012_weighted_hodge_orthogonality():
    """Verify that exact component d0 f and residual r are W-orthogonal in exact arithmetic."""
    edges = [(0, 1), (1, 2), (2, 0)]
    weights = [Fraction(1), Fraction(2), Fraction(3)]
    c = [Fraction(1), Fraction(2), Fraction(-1)]
    n_v, n_e = 3, 3

    d0 = [[Fraction(0)] * n_v for _ in range(n_e)]
    for i, (u, v) in enumerate(edges):
        d0[i][u] = Fraction(-1)
        d0[i][v] = Fraction(1)

    L = [[sum(d0[e][i] * weights[e] * d0[e][j] for e in range(n_e)) for j in range(n_v)] for i in range(n_v)]
    rhs = [sum(d0[e][i] * weights[e] * c[e] for e in range(n_e)) for i in range(n_v)]

    M_L = [row[:] for row in L]
    M_b = rhs[:]
    M_L[0] = [Fraction(1)] * n_v
    M_b[0] = Fraction(0)

    f = rational_solve_linear_system(M_L, M_b)
    df = [sum(d0[e][j] * f[j] for j in range(n_v)) for e in range(n_e)]
    r = [c[e] - df[e] for e in range(n_e)]

    inner_prod = sum(df[e] * weights[e] * r[e] for e in range(n_e))
    assert inner_prod == Fraction(0)


def test_n001_012_pythagorean_energy_conservation():
    """Verify Pythagorean energy conservation ||c||_{2,w}^2 = ||d0 f||_{2,w}^2 + ||r||_{2,w}^2."""
    edges = [(0, 1), (1, 2), (2, 0)]
    weights = [Fraction(2), Fraction(3, 2), Fraction(3)]
    c = [Fraction(3), Fraction(-3, 2), Fraction(2)]
    n_v, n_e = 3, 3

    d0 = [[Fraction(0)] * n_v for _ in range(n_e)]
    for i, (u, v) in enumerate(edges):
        d0[i][u] = Fraction(-1)
        d0[i][v] = Fraction(1)

    L = [[sum(d0[e][i] * weights[e] * d0[e][j] for e in range(n_e)) for j in range(n_v)] for i in range(n_v)]
    rhs = [sum(d0[e][i] * weights[e] * c[e] for e in range(n_e)) for i in range(n_v)]

    M_L = [row[:] for row in L]
    M_b = rhs[:]
    M_L[0] = [Fraction(1)] * n_v
    M_b[0] = Fraction(0)

    f = rational_solve_linear_system(M_L, M_b)
    df = [sum(d0[e][j] * f[j] for j in range(n_v)) for e in range(n_e)]
    r = [c[e] - df[e] for e in range(n_e)]

    E_total = sum(weights[e] * (c[e] ** 2) for e in range(n_e))
    E_exact = sum(weights[e] * (df[e] ** 2) for e in range(n_e))
    E_res = sum(weights[e] * (r[e] ** 2) for e in range(n_e))
    assert E_total == E_exact + E_res
