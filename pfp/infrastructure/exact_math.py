from __future__ import annotations

import itertools
import json
from fractions import Fraction
from hashlib import sha256
from math import comb
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from ..domain.homology.carrier import Carrier
from ..domain.homology.cochain import (
    BoundaryMatrix,
    Cochain,
    IntegerMatrix,
    SmithNormalFormResult,
    require_integer,
    require_rational,
)
from ..domain.kernel.ports import GenesisCycleSolverPort, PfpSolverPort
from ..domain.kernel.result import (
    DomainError,
    EvaluationVerdict,
    GenesisCycleVerdict,
    RefusalCode,
    Result,
    TerminalStatus,
)


class ExactRationalSolver(PfpSolverPort):
    """Deterministic exact rational solver for discrete simplicial complexes."""

    def verify_nilpotency(
        self, d0: BoundaryMatrix, d1: BoundaryMatrix
    ) -> Result[bool, DomainError]:
        if d1.cols != d0.rows:
            return Result.err(
                DomainError(
                    RefusalCode.NILPOTENCY_BROKEN,
                    f"Dimension mismatch for nilpotency: d1 cols ({d1.cols}) != d0 rows ({d0.rows})",
                )
            )

        for r_idx, d1_row in enumerate(d1.data):
            for c_idx in range(d0.cols):
                prod_val = sum(d1_row[k] * d0.data[k][c_idx] for k in range(d1.cols))
                if prod_val != 0:
                    return Result.err(
                        DomainError(
                            RefusalCode.NILPOTENCY_BROKEN,
                            f"Nonzero nilpotency product (d1 @ d0)[{r_idx}, {c_idx}] = {prod_val}",
                        )
                    )

        return Result.ok(True)

    def compute_gamma2(self, d1: BoundaryMatrix, omega: Cochain) -> Result[Fraction, DomainError]:
        if len(omega.values) != d1.cols:
            return Result.err(
                DomainError(
                    RefusalCode.MAP_UNDEFINED,
                    f"Cochain length {len(omega.values)} != d1 cols {d1.cols}",
                )
            )
        coboundary = d1.multiply_vector(omega.values)
        gamma2 = sum(abs(v) for v in coboundary)
        return Result.ok(gamma2)

    def compute_phi1(
        self, d0: BoundaryMatrix, omega: Cochain
    ) -> Result[Tuple[Fraction, Tuple[Fraction, ...]], DomainError]:
        """Compute Phi1(omega) = min_alpha ||omega - d0 * alpha||_1 over Q.

        For finite carrier graph complexes, alpha is determined on vertices up to
        connected component constants. In the standard discrete simplex/sub-manifold,
        we find the exact rational minimizer.
        """
        if len(omega.values) != d0.rows:
            return Result.err(
                DomainError(
                    RefusalCode.MAP_UNDEFINED,
                    f"Cochain length {len(omega.values)} != d0 rows {d0.rows}",
                )
            )

        # First check if omega is exact: omega = d0 * alpha with residual 0
        # Solve d0 * alpha = omega via Gaussian elimination over Fraction
        alpha_exact = self._solve_linear_system(d0, omega.values)
        if alpha_exact is not None:
            return Result.ok((Fraction(0), alpha_exact))

        # The objective is piecewise linear on the quotient by ker(d0).
        # A minimum occurs where rank(d0) independent residual hyperplanes
        # meet. Enumerate those intersections, not a bounded potential grid.
        # This is a small reference solver; refuse before an excessive search.
        rank = self._rank(d0)
        if comb(d0.rows, rank) > 100_000:
            return Result.err(
                DomainError(
                    RefusalCode.ENUMERATION_LIMIT_EXCEEDED,
                    "Exact L1 reference enumeration exceeds 100000 active sets",
                )
            )
        best_phi = omega.l1_norm()
        best_alpha = tuple(Fraction(0) for _ in range(d0.cols))
        for indices in itertools.combinations(range(d0.rows), rank):
            active = BoundaryMatrix(rank, d0.cols, tuple(d0.data[i] for i in indices))
            if self._rank(active) != rank:
                continue
            alpha = self._solve_linear_system(active, tuple(omega.values[i] for i in indices))
            if alpha is None:
                continue
            residual = sum(abs(w - v) for w, v in zip(omega.values, d0.multiply_vector(alpha)))
            if residual < best_phi:
                best_phi, best_alpha = residual, alpha
        return Result.ok((best_phi, best_alpha))

    @staticmethod
    def _rank(mat: BoundaryMatrix) -> int:
        rows = [list(map(Fraction, row)) for row in mat.data]
        rank = 0
        for col in range(mat.cols):
            pivot = next((i for i in range(rank, mat.rows) if rows[i][col]), None)
            if pivot is None:
                continue
            rows[rank], rows[pivot] = rows[pivot], rows[rank]
            value = rows[rank][col]
            rows[rank] = [v / value for v in rows[rank]]
            for i in range(rank + 1, mat.rows):
                scale = rows[i][col]
                rows[i] = [a - scale * b for a, b in zip(rows[i], rows[rank])]
            rank += 1
        return rank

    def verify_duality_gap(
        self, d0: BoundaryMatrix, omega: Cochain, phi1: Fraction, dual_vector: Tuple[Fraction, ...]
    ) -> Result[Fraction, DomainError]:
        try:
            require_rational(phi1)
            for value in dual_vector:
                require_rational(value)
        except TypeError as exc:
            return Result.err(DomainError(RefusalCode.POLICY_VIOLATION, str(exc)))
        if d0.rows != len(omega.values) or len(dual_vector) != len(omega.values):
            return Result.err(
                DomainError(
                    RefusalCode.DUALITY_GAP_NONZERO,
                    f"Dual vector length {len(dual_vector)} != omega length {len(omega.values)}",
                )
            )

        # Check ||y*||_infinity <= 1
        for idx, y_val in enumerate(dual_vector):
            if abs(y_val) > Fraction(1):
                return Result.err(
                    DomainError(
                        RefusalCode.DUALITY_GAP_NONZERO,
                        f"Dual feasibility violated at index {idx}: |{y_val}| > 1",
                    )
                )

        for col in range(d0.cols):
            if sum(y * row[col] for y, row in zip(dual_vector, d0.data)) != 0:
                return Result.err(
                    DomainError(
                        RefusalCode.DUALITY_GAP_NONZERO,
                        "Dual is not a circulation: d0^T y != 0",
                    )
                )
        dual_val = sum(y * w for y, w in zip(dual_vector, omega.values))
        gap = phi1 - dual_val
        if gap != 0:
            return Result.err(
                DomainError(
                    RefusalCode.DUALITY_GAP_NONZERO,
                    f"Nonzero duality gap: primal {phi1}, dual {dual_val}",
                )
            )

        return Result.ok(gap)

    def _solve_linear_system(
        self, mat: BoundaryMatrix, target: Sequence[Fraction]
    ) -> Optional[Tuple[Fraction, ...]]:
        """Exact rational Gaussian elimination to check if target is in im(d0)."""
        m, n = mat.rows, mat.cols
        aug = [[Fraction(v) for v in mat.data[r]] + [Fraction(target[r])] for r in range(m)]

        pivot_row = 0
        pivot_cols = []
        for c in range(n):
            if pivot_row >= m:
                break
            # Find non-zero pivot
            sel = None
            for r in range(pivot_row, m):
                if aug[r][c] != 0:
                    sel = r
                    break
            if sel is None:
                continue
            aug[pivot_row], aug[sel] = aug[sel], aug[pivot_row]
            pivot_val = aug[pivot_row][c]
            for col_idx in range(c, n + 1):
                aug[pivot_row][col_idx] /= pivot_val

            for r in range(m):
                if r != pivot_row and aug[r][c] != 0:
                    factor = aug[r][c]
                    for col_idx in range(c, n + 1):
                        aug[r][col_idx] -= factor * aug[pivot_row][col_idx]

            pivot_cols.append(c)
            pivot_row += 1

        # Check consistency: all-zero rows must have 0 on RHS
        for r in range(pivot_row, m):
            if aug[r][n] != 0:
                return None

        sol = [Fraction(0)] * n
        for r_idx, c_idx in enumerate(pivot_cols):
            sol[c_idx] = aug[r_idx][n]

        return tuple(sol)

    def compute_hodge_decomposition(
        self, d0: BoundaryMatrix, d1: BoundaryMatrix, omega: Cochain
    ) -> Result[
        Tuple[Tuple[Fraction, ...], Tuple[Fraction, ...], Tuple[Fraction, ...]], DomainError
    ]:
        """Compute exact discrete rational Hodge 3-way orthogonal decomposition over Q.

        Decomposes omega into (exact, harmonic, coexact) where:
        - exact = d0 * phi in im(d0)
        - coexact = d1^T * psi in im(d1^T)
        - harmonic in ker(d1) cap ker(d0^T)
        - exact, harmonic, coexact are mutually orthogonal in standard Q inner product
        - exact + harmonic + coexact == omega
        """
        if len(omega.values) != d0.rows or len(omega.values) != d1.cols:
            return Result.err(
                DomainError(
                    RefusalCode.MAP_UNDEFINED,
                    f"Dimension mismatch: omega len {len(omega.values)} vs d0 rows {d0.rows}, d1 cols {d1.cols}",
                )
            )

        # 1. Coexact component: solve (d1 @ d1^T) * psi = d1 * omega
        d1_omega = d1.multiply_vector(omega.values)
        m1_data = [
            [sum(d1.data[r1][c] * d1.data[r2][c] for c in range(d1.cols)) for r2 in range(d1.rows)]
            for r1 in range(d1.rows)
        ]
        m1_mat = BoundaryMatrix(
            len(m1_data),
            len(m1_data[0]),
            tuple(tuple(Fraction(x) for x in r) for r in m1_data),
        )
        psi = self._solve_linear_system(m1_mat, d1_omega)
        if psi is None:
            return Result.err(
                DomainError(
                    RefusalCode.HOMOLOGY_CYCLE_OBSTRUCTION,
                    "Cannot solve for coexact component on face coboundary.",
                )
            )

        coexact = tuple(sum(d1.data[f][e] * psi[f] for f in range(d1.rows)) for e in range(d1.cols))

        # 2. Exact component: solve (d0^T @ d0) * phi = d0^T * omega
        d0_t_omega = [
            sum(d0.data[e][v] * omega.values[e] for e in range(d0.rows)) for v in range(d0.cols)
        ]
        l0_data = [
            [sum(d0.data[e][u] * d0.data[e][v] for e in range(d0.rows)) for v in range(d0.cols)]
            for u in range(d0.cols)
        ]
        l0_mat = BoundaryMatrix(
            len(l0_data),
            len(l0_data[0]),
            tuple(tuple(Fraction(x) for x in r) for r in l0_data),
        )
        phi = self._solve_linear_system(l0_mat, d0_t_omega)
        if phi is None:
            return Result.err(
                DomainError(
                    RefusalCode.HOMOLOGY_CYCLE_OBSTRUCTION,
                    "Cannot solve for exact component on vertex coboundary.",
                )
            )

        exact = d0.multiply_vector(phi)

        # 3. Harmonic component = omega - exact - coexact
        harmonic = tuple(omega.values[e] - exact[e] - coexact[e] for e in range(len(omega.values)))

        # 4. Verification of Hodge orthogonality and nilpotency conditions
        d1_exact = d1.multiply_vector(exact)
        d1_harm = d1.multiply_vector(harmonic)
        d0_t_harm = [
            sum(d0.data[e][v] * harmonic[e] for e in range(d0.rows)) for v in range(d0.cols)
        ]
        if (
            any(v != 0 for v in d1_exact)
            or any(v != 0 for v in d1_harm)
            or any(v != 0 for v in d0_t_harm)
        ):
            return Result.err(
                DomainError(
                    RefusalCode.HOMOLOGY_CYCLE_OBSTRUCTION,
                    "Harmonic or boundary nilpotency condition violated in Hodge decomposition.",
                )
            )

        dot_exact_harm = sum(exact[e] * harmonic[e] for e in range(len(omega.values)))
        dot_exact_coex = sum(exact[e] * coexact[e] for e in range(len(omega.values)))
        dot_harm_coex = sum(harmonic[e] * coexact[e] for e in range(len(omega.values)))
        if dot_exact_harm != 0 or dot_exact_coex != 0 or dot_harm_coex != 0:
            return Result.err(
                DomainError(
                    RefusalCode.HOMOLOGY_CYCLE_OBSTRUCTION,
                    "Components are not mutually orthogonal in standard rational inner product.",
                )
            )

        return Result.ok((exact, harmonic, coexact))

    def evaluate(
        self,
        packet_id: str,
        carrier: Carrier,
        omega: Cochain,
        d0: Optional[BoundaryMatrix],
        d1: Optional[BoundaryMatrix],
        dual_vector: Optional[Sequence[int | Fraction]] = None,
    ) -> Result[EvaluationVerdict, DomainError]:
        """Evaluate a proposal packet with exact rational arithmetic."""
        from use_cases.evaluate_pfp_primitive import EvaluatePfpPrimitiveUseCase

        return EvaluatePfpPrimitiveUseCase(self).evaluate(
            packet_id, carrier, omega, d0, d1, dual_vector
        )


class ExactIntegerSmithNormalFormSolver(GenesisCycleSolverPort):
    """Deterministic exact integer Smith Normal Form solver over Z for simplicial complexes."""

    def compute_snf(self, matrix: IntegerMatrix) -> Result[SmithNormalFormResult, DomainError]:
        m, n = matrix.rows, matrix.cols
        if m == 0 or n == 0:
            u = IntegerMatrix.from_nested_ints(
                [[1 if i == j else 0 for j in range(m)] for i in range(m)]
            )
            v = IntegerMatrix.from_nested_ints(
                [[1 if i == j else 0 for j in range(n)] for i in range(n)]
            )
            v_inv = IntegerMatrix.from_nested_ints(
                [[1 if i == j else 0 for j in range(n)] for i in range(n)]
            )
            d = IntegerMatrix(m, n, tuple(tuple(0 for _ in range(n)) for _ in range(m)))
            return Result.ok(
                SmithNormalFormResult(u=u, d=d, v=v, v_inv=v_inv, invariant_factors=(), rank=0)
            )

        D = [list(row) for row in matrix.data]
        U = [[1 if i == j else 0 for j in range(m)] for i in range(m)]
        V = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
        V_inv = [[1 if i == j else 0 for j in range(n)] for i in range(n)]

        def swap_rows(i: int, k: int) -> None:
            D[i], D[k] = D[k], D[i]
            U[i], U[k] = U[k], U[i]

        def swap_cols(j: int, k: int) -> None:
            for r in range(m):
                D[r][j], D[r][k] = D[r][k], D[r][j]
            for r in range(n):
                V[r][j], V[r][k] = V[r][k], V[r][j]
                V_inv[j][r], V_inv[k][r] = V_inv[k][r], V_inv[j][r]

        def add_row(src: int, dst: int, c: int) -> None:
            for col in range(n):
                D[dst][col] += c * D[src][col]
            for col in range(m):
                U[dst][col] += c * U[src][col]

        def add_col(src: int, dst: int, c: int) -> None:
            for row in range(m):
                D[row][dst] += c * D[row][src]
            for row in range(n):
                V[row][dst] += c * V[row][src]
                V_inv[src][row] -= c * V_inv[dst][row]

        def mult_row(r: int, c: int) -> None:
            for col in range(n):
                D[r][col] *= c
            for col in range(m):
                U[r][col] *= c

        def mult_col(col_idx: int, c: int) -> None:
            for r in range(m):
                D[r][col_idx] *= c
            for r in range(n):
                V[r][col_idx] *= c
                V_inv[col_idx][r] *= c

        min_dim = min(m, n)
        for k in range(min_dim):
            step_count = 0
            while True:
                step_count += 1
                if step_count > 10_000:
                    return Result.err(
                        DomainError(
                            RefusalCode.POLICY_VIOLATION,
                            f"SNF pivot reduction exceeded iteration limit at pivot {k}",
                        )
                    )
                # 1. find pivot with smallest non-zero absolute value
                pivot_val = 0
                pr, pc = -1, -1
                for r in range(k, m):
                    for c in range(k, n):
                        val = abs(D[r][c])
                        if val > 0:
                            if pivot_val == 0 or val < pivot_val:
                                pivot_val = val
                                pr, pc = r, c
                if pr == -1:
                    break
                if pr != k:
                    swap_rows(pr, k)
                if pc != k:
                    swap_cols(pc, k)
                if D[k][k] < 0:
                    mult_row(k, -1)

                changed = False
                # Eliminate column k
                for r in range(k + 1, m):
                    if D[r][k] != 0:
                        q = D[r][k] // D[k][k]
                        if q != 0:
                            add_row(k, r, -q)
                        if D[r][k] != 0:
                            changed = True
                            break
                if changed:
                    continue

                # Eliminate row k
                for c in range(k + 1, n):
                    if D[k][c] != 0:
                        q = D[k][c] // D[k][k]
                        if q != 0:
                            add_col(k, c, -q)
                        if D[k][c] != 0:
                            changed = True
                            break
                if changed:
                    continue

                # Check divisibility of all entries in submatrix
                div_fail = False
                for r in range(k + 1, m):
                    for c in range(k + 1, n):
                        if D[r][c] % D[k][k] != 0:
                            add_row(r, k, 1)
                            div_fail = True
                            break
                    if div_fail:
                        break
                if div_fail:
                    continue

                break

        # Verification check: U @ A @ V == D
        u_mat = IntegerMatrix.from_nested_ints(U)
        v_mat = IntegerMatrix.from_nested_ints(V)
        v_inv_mat = IntegerMatrix.from_nested_ints(V_inv)
        d_mat = IntegerMatrix.from_nested_ints(D)

        u_a = u_mat.multiply_matrix(matrix)
        u_a_v = u_a.multiply_matrix(v_mat)
        if u_a_v != d_mat:
            return Result.err(
                DomainError(
                    RefusalCode.POLICY_VIOLATION,
                    "SNF certification failed: U * A * V != D",
                )
            )

        diag = tuple(D[i][i] for i in range(min_dim) if D[i][i] != 0)
        # Check divisibility chain
        for i in range(len(diag) - 1):
            if diag[i + 1] % diag[i] != 0:
                return Result.err(
                    DomainError(
                        RefusalCode.POLICY_VIOLATION,
                        f"Invariant factor divisibility broken: {diag[i + 1]} not divisible by {diag[i]}",
                    )
                )

        return Result.ok(
            SmithNormalFormResult(
                u=u_mat,
                d=d_mat,
                v=v_mat,
                v_inv=v_inv_mat,
                invariant_factors=diag,
                rank=len(diag),
            )
        )

    def evaluate_genesis_cycle_balance(
        self,
        carrier: Carrier,
        d1: IntegerMatrix,
        d2: IntegerMatrix,
        beta: Optional[Tuple[int, ...]] = None,
        target_cycle: Optional[Tuple[int, ...]] = None,
        proposal_id: str = "GENESIS-CYCLE-001",
    ) -> Result[GenesisCycleVerdict, DomainError]:
        """Evaluates Genesis cycle balance psi(beta) = [d2 beta] in H_1(V, E, B; Z) under static cell bounds."""
        if beta is not None and target_cycle is not None:
            return Result.err(
                DomainError(RefusalCode.POLICY_VIOLATION, "Supply beta or target_cycle, not both")
            )
        try:
            for value in beta if beta is not None else target_cycle or ():
                require_integer(value)
        except TypeError as exc:
            return Result.err(DomainError(RefusalCode.NON_INTEGRAL_BOUNDARY, str(exc)))

        # 1. Enforce static cell bounds: N_max = (|V| <= 64, |E| <= 128, |B| <= 64)
        if not carrier.validate_cell_bounds():
            return Result.err(
                DomainError(
                    RefusalCode.CELL_BOUND_EXCEEDED,
                    f"Static cell bounds N_max exceeded: |V|={carrier.num_vertices} (max {carrier.bounds.max_vertices}), "
                    f"|E|={carrier.num_edges} (max {carrier.bounds.max_edges}), "
                    f"|B|={carrier.num_faces} (max {carrier.bounds.max_faces})",
                )
            )

        if carrier.field != "Z":
            return Result.err(DomainError(RefusalCode.POLICY_VIOLATION, "Genesis requires field Z"))

        # Also verify matrix dimensions match carrier dimensions
        num_v = carrier.num_vertices
        num_e = carrier.num_edges
        num_b = carrier.num_faces

        if d1.cols != num_e or d1.rows != num_v:
            return Result.err(
                DomainError(
                    RefusalCode.MAP_UNDEFINED,
                    f"d1 dimensions ({d1.rows}x{d1.cols}) disagree with carrier (|V|={num_v}, |E|={num_e})",
                )
            )
        if d2.rows != num_e or d2.cols != num_b:
            return Result.err(
                DomainError(
                    RefusalCode.MAP_UNDEFINED,
                    f"d2 dimensions ({d2.rows}x{d2.cols}) disagree with carrier (|E|={num_e}, |B|={num_b})",
                )
            )

        # 2. Enforce Nilpotency d1 @ d2 == 0 over Z
        prod = d1.multiply_matrix(d2)
        for r_idx, row in enumerate(prod.data):
            for c_idx, val in enumerate(row):
                if val != 0:
                    return Result.err(
                        DomainError(
                            RefusalCode.NILPOTENCY_BROKEN,
                            f"Nonzero nilpotency product (d1 @ d2)[{r_idx}, {c_idx}] = {val}",
                        )
                    )

        # 3. Determine the target 1-cycle z in Z^E
        if target_cycle is not None:
            if len(target_cycle) != num_e:
                return Result.err(
                    DomainError(
                        RefusalCode.MAP_UNDEFINED,
                        f"Target cycle length ({len(target_cycle)}) != declared edges |E| ({num_e})",
                    )
                )
            # Verify target_cycle is in ker(d1): d1 @ z == 0
            d1_z = d1.multiply_vector(target_cycle)
            for r_idx, val in enumerate(d1_z):
                if val != 0:
                    return Result.err(
                        DomainError(
                            RefusalCode.POLICY_VIOLATION,
                            f"Target vector is not a closed 1-cycle: (d1 @ z)[{r_idx}] = {val} != 0",
                        )
                    )
            z = target_cycle
        elif beta is not None:
            if len(beta) != num_b:
                return Result.err(
                    DomainError(
                        RefusalCode.MAP_UNDEFINED,
                        f"Proposal beta length ({len(beta)}) != declared 2-cells |B| ({num_b})",
                    )
                )
            z = d2.multiply_vector(beta)
        else:
            return Result.err(
                DomainError(
                    RefusalCode.MAP_UNDEFINED,
                    "Either proposal beta or target_cycle must be provided.",
                )
            )

        # 4. Compute SNF of d2: U * d2 * V = D
        snf_res = self.compute_snf(d2)
        if snf_res.is_err:
            return Result.err(snf_res.unwrap_err())
        snf = snf_res.unwrap()

        # 5. Transform z' = U @ z in Z^E
        z_prime = snf.u.multiply_vector(z)

        # 6. Check divisibility against diagonal D
        is_balanced = True
        torsion_coeffs = []
        cocycle_witness = None
        refusal_reason = ""
        refusal_code = None

        y_vals = [0] * num_b
        for i in range(num_e):
            val = z_prime[i]
            d_i = snf.invariant_factors[i] if i < snf.rank else 0

            if d_i > 0:
                if val % d_i != 0:
                    is_balanced = False
                    torsion_coeffs.append(d_i)
                    if refusal_code is None:
                        refusal_code = RefusalCode.TORSION_OBSTRUCTION
                        refusal_reason = f"Torsion obstruction: component {i} (val={val}) not divisible by invariant factor {d_i}"
                else:
                    y_vals[i] = val // d_i
            else:
                # d_i == 0: row of D is zero. So we must have val == 0!
                if val != 0:
                    is_balanced = False
                    if cocycle_witness is None:
                        # Row i of U is the certified dual cocycle witness!
                        cocycle_witness = snf.u.data[i]
                        refusal_code = RefusalCode.HOMOLOGY_CYCLE_OBSTRUCTION
                        refusal_reason = (
                            f"Free homology cycle obstruction: [z] != 0 in H_1; "
                            f"witness row {i} of U has inner product {val} != 0."
                        )

        d1_snf = self.compute_snf(d1)
        if d1_snf.is_err:
            return Result.err(d1_snf.unwrap_err())
        h1_free_rank = num_e - d1_snf.unwrap().rank - snf.rank

        if is_balanced:
            # Reconstruct exact integer preimage c = V @ y in Z^B
            c = snf.v.multiply_vector(y_vals)
            # Replay verification: d2 @ c == z
            recomputed_z = d2.multiply_vector(c)
            if recomputed_z != z:
                return Result.err(
                    DomainError(
                        RefusalCode.POLICY_VIOLATION,
                        "SNF preimage reconstruction failed: d2 * c != z",
                    )
                )
            return Result.ok(
                GenesisCycleVerdict(
                    proposal_id=proposal_id,
                    is_balanced=True,
                    status=TerminalStatus.EXACT,
                    h1_free_rank=h1_free_rank,
                    torsion_coefficients=(),
                    invariant_factors=snf.invariant_factors,
                    boundary_preimage=c,
                    cocycle_witness=None,
                    cycle_boundary=z,
                    message="Cycle is completely balanced over Z by 2-cell boundary preimage.",
                )
            )
        else:
            status = (
                TerminalStatus.OPEN_OBSTRUCTION
                if torsion_coeffs
                else TerminalStatus.STABILIZED_SURVIVOR
            )
            return Result.ok(
                GenesisCycleVerdict(
                    proposal_id=proposal_id,
                    is_balanced=False,
                    status=status,
                    h1_free_rank=h1_free_rank,
                    torsion_coefficients=tuple(torsion_coeffs),
                    invariant_factors=snf.invariant_factors,
                    boundary_preimage=None,
                    cocycle_witness=cocycle_witness,
                    cycle_boundary=z,
                    refusal_code=refusal_code,
                    message=refusal_reason,
                )
            )


# --- Exact Witness Replay Utilities ---


def rational(x: Any) -> Fraction:
    if isinstance(x, bool) or isinstance(x, float) or not isinstance(x, (int, str, Fraction)):
        raise ValueError("exact rational required; floats and booleans refused")
    if len(str(x)) > 256:
        raise ValueError("coefficient size limit")
    return Fraction(x)


def vec(xs: Sequence[Any]) -> List[Fraction]:
    if not isinstance(xs, list) or len(xs) > 256:
        raise ValueError("bounded vector required")
    return [rational(x) for x in xs]


def dot(a: Sequence[Any], b: Sequence[Any]) -> Fraction:
    if len(a) != len(b):
        raise ValueError("vector dimensions")
    return sum((rational(x) * rational(y) for x, y in zip(a, b)), Fraction())


def mv(a: Sequence[Sequence[Any]], x: Sequence[Any]) -> List[Fraction]:
    return [dot(row, x) for row in a]


def transpose(a: Sequence[Sequence[Any]]) -> List[List[Any]]:
    if not a:
        return []
    if any(len(row) != len(a[0]) for row in a):
        raise ValueError("ragged matrix")
    return [list(row) for row in zip(*a)]


def mm(a: Sequence[Sequence[Any]], b: Sequence[Sequence[Any]]) -> List[List[Fraction]]:
    return [[dot(row, col) for col in transpose(b)] for row in a]


def sub(a: Sequence[Any], b: Sequence[Any]) -> List[Fraction]:
    if len(a) != len(b):
        raise ValueError("vector dimensions")
    return [rational(x) - rational(y) for x, y in zip(a, b)]


def same(a: Sequence[Any], b: Sequence[Any]) -> bool:
    return vec(a) == vec(b)


def rank(a: Sequence[Sequence[Any]]) -> int:
    rows = [vec(row) for row in a]
    if not rows:
        return 0
    n = len(rows[0])
    r = 0
    if any(len(row) != n for row in rows):
        raise ValueError("ragged matrix")
    for col in range(n):
        pivot = next((i for i in range(r, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        v = rows[r][col]
        rows[r] = [x / v for x in rows[r]]
        for i in range(len(rows)):
            if i != r:
                v = rows[i][col]
                rows[i] = [x - v * y for x, y in zip(rows[i], rows[r])]
        r += 1
        if r == len(rows):
            break
    return r


def det(a: Sequence[Sequence[Any]]) -> Fraction:
    n = len(a)
    if any(len(row) != n for row in a):
        raise ValueError("square matrix required")
    if n == 0:
        return Fraction(1)
    if n == 1:
        return rational(a[0][0])
    return sum(
        (
            (-1) ** j * rational(a[0][j]) * det([row[:j] + row[j + 1 :] for row in a[1:]])
            for j in range(n)
        ),
        Fraction(),
    )


def f2(x: Any) -> List[int]:
    if not isinstance(x, list) or any(type(v) is not int or v not in (0, 1) for v in x):
        raise ValueError("F2 vector requires literal 0/1 integers")
    return x


def span2(gens: Sequence[Sequence[int]], n: int) -> Set[Tuple[int, ...]]:
    for g in gens:
        if len(f2(list(g))) != n:
            raise ValueError("F2 generator shape")
    return {
        tuple(sum(bits[j] * gens[j][i] for j in range(len(gens))) % 2 for i in range(n))
        for bits in itertools.product((0, 1), repeat=len(gens))
    }


def l1_certificate(
    matrix: Sequence[Sequence[Any]], omega: Sequence[Any], c: Dict[str, Any]
) -> Fraction:
    alpha = vec(c["alpha"])
    dual = vec(c["dual"])
    residual = sub(omega, mv(matrix, alpha))
    if len(dual) != len(omega):
        raise ValueError("dual dimensions")
    if any(mv(transpose(matrix), dual)):
        raise ValueError("dual is not a circulation")
    if any(abs(y) > 1 for y in dual):
        raise ValueError("dual capacity exceeded")
    primal = sum(map(abs, residual), Fraction())
    lower = dot(dual, omega)
    if primal != lower:
        raise ValueError("nonzero primal-dual gap")
    if not same(c["residual"], residual):
        raise ValueError("submitted residual does not replay")
    if rational(c["value"]) != primal:
        raise ValueError("submitted optimum does not replay")
    return primal


def digest(x: Any) -> str:
    return sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def string_digest(x: str) -> str:
    return sha256(x.encode()).hexdigest()


def compose(f: Dict[Any, Any], g: Dict[Any, Any]) -> Dict[Any, Any]:
    return {x: f[y] for x, y in g.items()}


def function_closure(
    generators: Sequence[Dict[Any, Any]], carrier: Sequence[Any]
) -> List[Dict[Any, Any]]:
    identity = {x: x for x in carrier}
    out = {tuple(identity[x] for x in carrier): identity}
    todo = [identity]
    while todo:
        f = todo.pop()
        for g in generators:
            h = compose(g, f)
            key = tuple(h[x] for x in carrier)
            if key not in out:
                out[key] = h
                todo.append(h)
            if len(out) > 4096:
                raise ValueError("closure limit")
    return list(out.values())


def natural_join(
    left: Sequence[Sequence[Any]],
    lh: Sequence[str],
    right: Sequence[Sequence[Any]],
    rh: Sequence[str],
) -> Tuple[List[str], Set[Tuple[Any, ...]]]:
    heading = list(lh) + [a for a in rh if a not in lh]
    out = set()
    for row_l in left:
        for r in right:
            ld = dict(zip(lh, row_l))
            rd = dict(zip(rh, r))
            if all(ld[a] == rd[a] for a in set(lh) & set(rh)):
                out.add(tuple(({**ld, **rd})[a] for a in heading))
    return heading, out


def fd_holds(
    rows: Sequence[Sequence[Any]], heading: Sequence[str], lhs: Sequence[str], rhs: Sequence[str]
) -> bool:
    lhs_idx = [heading.index(a) for a in lhs]
    rhs_idx = [heading.index(a) for a in rhs]
    return all(
        tuple(x[i] for i in lhs_idx) != tuple(y[i] for i in lhs_idx)
        or tuple(x[i] for i in rhs_idx) == tuple(y[i] for i in rhs_idx)
        for x in rows
        for y in rows
    )


def affine_compose(
    left: Sequence[Sequence[Any]], right: Sequence[Sequence[Any]]
) -> List[List[Fraction]]:
    return mm(left, right)


TRI = [[-1, 1, 0], [0, -1, 1], [-1, 0, 1]]
CYCLE = [[-1, 1, 0], [0, -1, 1], [1, 0, -1]]
