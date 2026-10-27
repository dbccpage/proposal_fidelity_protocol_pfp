"""Reference solver for C020: Spectral Sequence Pages of a Double Complex."""

from __future__ import annotations

from typing import Any

from .exact_f2 import (
    is_zero_mat_f2,
    mat_mul_f2,
    mats_equal_f2,
    nullspace_f2,
    rank_f2,
    subspace_span_rank_f2,
)


def _first_nonzero_column(matrix: list[list[int]]) -> int:
    """Return the first source generator on which an F2 map is nonzero."""
    if not matrix:
        return 0
    for column in range(len(matrix[0])):
        if any(row[column] % 2 for row in matrix):
            return column
    return 0


class DoubleComplex:
    def __init__(self, case: dict[str, Any]):
        self.case = case
        self.raw_dims = case.get("dims", {})
        self.raw_dh = case.get("d_h", {})
        self.raw_dv = case.get("d_v", {})

        # Parse dimensions n(p, q) for 0 <= p, q <= 5
        self.dims: dict[tuple[int, int], int] = {}
        for p in range(6):
            for q in range(6):
                key = f"{p},{q}"
                self.dims[(p, q)] = int(self.raw_dims.get(key, 0))

        # Matrices: d_h[(p, q)] is n(p-1, q) x n(p, q)
        #           d_v[(p, q)] is n(p, q-1) x n(p, q)
        self.d_h: dict[tuple[int, int], list[list[int]]] = {}
        self.d_v: dict[tuple[int, int], list[list[int]]] = {}
        for p in range(6):
            for q in range(6):
                dim_pq = self.dims[(p, q)]
                dim_h_tgt = self.dims[(p - 1, q)] if p > 0 else 0
                dim_v_tgt = self.dims[(p, q - 1)] if q > 0 else 0

                key = f"{p},{q}"
                # d_h
                if dim_pq > 0 and dim_h_tgt > 0:
                    mat = self.raw_dh.get(key, [[0] * dim_pq for _ in range(dim_h_tgt)])
                    self.d_h[(p, q)] = [[int(x) % 2 for x in row] for row in mat]
                else:
                    self.d_h[(p, q)] = []

                # d_v
                if dim_pq > 0 and dim_v_tgt > 0:
                    mat = self.raw_dv.get(key, [[0] * dim_pq for _ in range(dim_v_tgt)])
                    self.d_v[(p, q)] = [[int(x) % 2 for x in row] for row in mat]
                else:
                    self.d_v[(p, q)] = []

    def validate_complex_laws(self) -> dict[str, Any] | None:
        """Verify d^h d^h = 0, d^v d^v = 0, and d^h d^v = d^v d^h."""
        # 1. d^h d^h = 0
        for p in range(2, 6):
            for q in range(6):
                m1 = self.d_h.get((p, q), [])
                m2 = self.d_h.get((p - 1, q), [])
                if m1 and m2:
                    prod = mat_mul_f2(m2, m1)
                    if not is_zero_mat_f2(prod):
                        return {
                            "status": "OUT_OF_SCOPE",
                            "witness": {
                                "reason": "DH_DH_NOT_ZERO",
                                "generator": f"{p},{q}:{_first_nonzero_column(prod)}",
                            },
                        }

        # 2. d^v d^v = 0
        for p in range(6):
            for q in range(2, 6):
                m1 = self.d_v.get((p, q), [])
                m2 = self.d_v.get((p, q - 1), [])
                if m1 and m2:
                    prod = mat_mul_f2(m2, m1)
                    if not is_zero_mat_f2(prod):
                        return {
                            "status": "OUT_OF_SCOPE",
                            "witness": {
                                "reason": "DV_DV_NOT_ZERO",
                                "generator": f"{p},{q}:{_first_nonzero_column(prod)}",
                            },
                        }

        # 3. d^h d^v = d^v d^h
        for p in range(1, 6):
            for q in range(1, 6):
                m_dv = self.d_v.get((p, q), [])
                m_dh_after = self.d_h.get((p, q - 1), [])
                m_dh = self.d_h.get((p, q), [])
                m_dv_after = self.d_v.get((p - 1, q), [])

                dim_pq = self.dims[(p, q)]
                dim_target = self.dims[(p - 1, q - 1)]
                if dim_pq == 0 or dim_target == 0:
                    continue

                prod1 = (
                    mat_mul_f2(m_dh_after, m_dv)
                    if (m_dv and m_dh_after)
                    else [[0] * dim_pq for _ in range(dim_target)]
                )
                prod2 = (
                    mat_mul_f2(m_dv_after, m_dh)
                    if (m_dh and m_dv_after)
                    else [[0] * dim_pq for _ in range(dim_target)]
                )

                if not mats_equal_f2(prod1, prod2):
                    gen_idx = 0
                    for col in range(dim_pq):
                        col1 = [prod1[r][col] for r in range(dim_target)]
                        col2 = [prod2[r][col] for r in range(dim_target)]
                        if col1 != col2:
                            gen_idx = col
                            break
                    return {
                        "status": "OUT_OF_SCOPE",
                        "witness": {
                            "reason": "DH_DV_NOT_COMMUTING",
                            "generator": f"{p},{q}:{gen_idx}",
                        },
                    }

        return None


def compute_spectral_sequence(
    dc: DoubleComplex, filtration: str = "columns"
) -> tuple[dict[str, str], list[dict[str, str]], dict[str, str], dict[str, str]]:
    """Compute (E2, differentials, Einf, tot_homology) for given filtration."""
    # Build total spaces Tot_n = direct sum_{p+q=n} C_{p,q}
    # For column filtration, order sum by p = 0..n
    # For row filtration, order sum by q = 0..n
    tot_offsets: dict[int, dict[tuple[int, int], tuple[int, int]]] = {}
    tot_dims: dict[int, int] = {}

    for n in range(11):
        offsets: dict[tuple[int, int], tuple[int, int]] = {}
        curr = 0
        pairs = [(p, n - p) for p in range(n + 1) if 0 <= p <= 5 and 0 <= n - p <= 5]
        # Order by filtration index: p for columns, q for rows
        if filtration == "columns":
            pairs.sort(key=lambda item: item[0])
        else:
            pairs.sort(key=lambda item: item[1])

        for p, q in pairs:
            dim_pq = dc.dims.get((p, q), 0)
            if dim_pq > 0:
                offsets[(p, q)] = (curr, curr + dim_pq)
                curr += dim_pq
            else:
                offsets[(p, q)] = (curr, curr)
        tot_offsets[n] = offsets
        tot_dims[n] = curr

    # Build total boundary matrices D_n : Tot_n -> Tot_{n-1}
    D_mats: dict[int, list[list[int]]] = {}
    for n in range(1, 11):
        m = tot_dims[n - 1]
        k = tot_dims[n]
        if m == 0 or k == 0:
            D_mats[n] = []
            continue
        mat = [[0] * k for _ in range(m)]
        for (p, q), (start_c, end_c) in tot_offsets[n].items():
            dim_src = end_c - start_c
            if dim_src == 0:
                continue

            # d^h : C_{p,q} -> C_{p-1, q}
            if p > 0 and (p - 1, q) in tot_offsets[n - 1]:
                start_r, end_r = tot_offsets[n - 1][(p - 1, q)]
                dh = dc.d_h.get((p, q), [])
                for r_idx in range(len(dh)):
                    for c_idx in range(len(dh[0])):
                        mat[start_r + r_idx][start_c + c_idx] ^= dh[r_idx][c_idx]

            # d^v : C_{p,q} -> C_{p, q-1}
            if q > 0 and (p, q - 1) in tot_offsets[n - 1]:
                start_r, end_r = tot_offsets[n - 1][(p, q - 1)]
                dv = dc.d_v.get((p, q), [])
                for r_idx in range(len(dv)):
                    for c_idx in range(len(dv[0])):
                        mat[start_r + r_idx][start_c + c_idx] ^= dv[r_idx][c_idx]

        D_mats[n] = mat

    # Total homology: dim H_n(Tot) = dim ker(D_n) - rank(D_{n+1})
    tot_homology: dict[str, str] = {}
    for n in range(11):
        dim_tot_n = tot_dims[n]
        if dim_tot_n == 0:
            continue
        if n == 0 or not D_mats.get(n):
            dim_ker = dim_tot_n
        else:
            dim_ker = dim_tot_n - rank_f2(D_mats[n])

        if n + 1 <= 10 and D_mats.get(n + 1):
            dim_im = rank_f2(D_mats[n + 1])
        else:
            dim_im = 0

        h_n = dim_ker - dim_im
        if h_n > 0:
            tot_homology[str(n)] = str(h_n)

    # Filtered pieces helper
    def get_filt_cols(n: int, s: int) -> list[int]:
        cols: list[int] = []
        for (p, q), (start_c, end_c) in tot_offsets[n].items():
            filt_val = p if filtration == "columns" else q
            if filt_val <= s:
                cols.extend(range(start_c, end_c))
        return cols

    def get_Z_plus_F_dim(p: int, q: int, r: int) -> int:
        """Compute dim(Z^r_{p,q} + F_{s-1} Tot_n) directly."""
        n = p + q
        s = p if filtration == "columns" else q
        cols_Fs = get_filt_cols(n, s)
        tot_dims[n]
        if not cols_Fs:
            return 0
        cols_Fs_minus_1 = set(get_filt_cols(n, s - 1))

        if n == 0 or r > s + 1:
            # Condition D(x) = 0
            if n == 0:
                # All cols_Fs are cycles
                return len(cols_Fs)
            mat_D = D_mats.get(n, [])
            if not mat_D:
                return len(cols_Fs)
            # D(x) = 0 restricted to cols_Fs
            sub_sys = [[mat_D[r_idx][c] for c in cols_Fs] for r_idx in range(tot_dims[n - 1])]
            sol_vecs = nullspace_f2(sub_sys, len(cols_Fs))
        else:
            # D(x) in F_{s - r} Tot_{n-1}
            mat_D = D_mats.get(n, [])
            if not mat_D:
                return len(cols_Fs)
            cols_F_target = set(get_filt_cols(n - 1, s - r))
            bad_rows = [
                row_idx for row_idx in range(tot_dims[n - 1]) if row_idx not in cols_F_target
            ]
            if not bad_rows:
                return len(cols_Fs)
            sub_sys = [[mat_D[r_idx][c] for c in cols_Fs] for r_idx in bad_rows]
            sol_vecs = nullspace_f2(sub_sys, len(cols_Fs))

        # sol_vecs in F_s coords + basis of F_{s-1}
        # Basis of F_{s-1} in F_s coords: unit vectors for c in cols_Fs_minus_1
        full_basis: list[list[int]] = list(sol_vecs)
        for idx, c in enumerate(cols_Fs):
            if c in cols_Fs_minus_1:
                vec = [0] * len(cols_Fs)
                vec[idx] = 1
                full_basis.append(vec)

        return subspace_span_rank_f2(full_basis, len(cols_Fs))

    # Compute E2 by double complex homology: E2 = H^h(H^v(C)) for columns, H^v(H^h(C)) for rows
    E_dims: dict[int, dict[tuple[int, int], int]] = {r: {} for r in range(2, 7)}
    for p in range(6):
        for q in range(6):
            if filtration == "columns":
                # E0 = C, d0 = dv: (p, q) -> (p, q-1)
                # E1_{p,q} = ker(dv_{p,q}) / im(dv_{p, q+1})
                # d1 : E1_{p,q} -> E1_{p-1, q} induced by dh
                # E2_{p,q} = ker(d1_{p,q}) / im(d1_{p+1, q})
                pass

    # Actually, using Z^2 and B^1 with exact quotient:
    # Notice: dim E^2_{p,q} for columns:
    # E^1_{p,q} = dim ker(d^v_{p,q}) - rank(d^v_{p, q+1})
    # Since d_1 is induced by d^h on vertical homology:
    # ker(d_1)_{p,q} = { x in ker(d^v_{p,q}) | d^h(x) in im(d^v_{p-1, q}) } / im(d^v_{p, q+1})
    # im(d_1)_{p+1, q} = (d^h(ker(d^v_{p+1, q})) + im(d^v_{p, q})) / im(d^v_{p, q})
    # So:
    # dim E^2_{p,q} = dim{ x in ker(d^v_{p,q}) | d^h(x) in im(d^v_{p-1, q}) }
    #               - dim( d^h(ker(d^v_{p+1, q})) + im(d^v_{p, q+1}) )
    for p in range(6):
        for q in range(6):
            dim_pq = dc.dims[(p, q)]
            if dim_pq == 0:
                E_dims[2][(p, q)] = 0
                continue

            if filtration == "columns":
                dv_pq = dc.d_v.get((p, q), [])
                dv_next = dc.d_v.get((p, q + 1), [])  # C_{p, q+1} -> C_{p, q}
                dh_pq = dc.d_h.get((p, q), [])  # C_{p, q} -> C_{p-1, q}
                dh_prev = dc.d_h.get((p + 1, q), [])  # C_{p+1, q} -> C_{p, q}
                dc.d_v.get(
                    (p - 1, q + 1), []
                )  # C_{p-1, q+1} -> C_{p-1, q} (or q if target is p-1, q)
                # Wait: target of dh is (p-1, q). In C_{p-1, q}, im(d^v) comes from C_{p-1, q+1}!
                dv_tgt_mat = dc.d_v.get((p - 1, q + 1), [])

                # ker(dv_{p,q})
                ker_dv = nullspace_f2(dv_pq, dim_pq)

                # Condition: x in ker(dv_{p,q}) and dh(x) in im(dv_{p-1, q+1})
                # dh(x) = dv_tgt * y => [dh | dv_tgt] [x; y] = 0
                dim_tgt = dc.dims.get((p - 1, q), 0)
                if dim_tgt == 0 or not dh_pq:
                    # dh(x) = 0 is trivially satisfied
                    num_sub = ker_dv
                else:
                    # We want dh(x) in col_space(dv_tgt_mat)
                    # Coordinates in C_{p-1, q} orthogonal to im(dv_tgt_mat) must vanish on dh(x)
                    # i.e., nullspace of (dv_tgt_mat)^T
                    if not dv_tgt_mat:
                        coker_basis = [
                            [1 if i == j else 0 for j in range(dim_tgt)] for i in range(dim_tgt)
                        ]
                    else:
                        # Transpose of dv_tgt_mat
                        dim_src_tgt = dc.dims.get((p - 1, q + 1), 0)
                        dv_tgt_T = [
                            [dv_tgt_mat[r][c] for r in range(dim_tgt)] for c in range(dim_src_tgt)
                        ]
                        coker_basis = nullspace_f2(dv_tgt_T, dim_tgt)

                    # Now for each w in coker_basis, w^T * dh * x = 0
                    coker_dh = mat_mul_f2(coker_basis, dh_pq)
                    # Also x in ker(dv)
                    full_sys = coker_dh + dv_pq
                    num_sub = nullspace_f2(full_sys, dim_pq)

                dim_num = subspace_span_rank_f2(num_sub, dim_pq)

                # Denominator: d^h(ker(dv_{p+1, q})) + im(dv_{p, q+1}) in C_{p, q}
                dim_p1_q = dc.dims.get((p + 1, q), 0)
                dv_p1_q = dc.d_v.get((p + 1, q), [])
                ker_dv_p1 = nullspace_f2(dv_p1_q, dim_p1_q)

                dh_ker: list[list[int]] = []
                if dh_prev and ker_dv_p1:
                    for k_vec in ker_dv_p1:
                        # dh_prev * k_vec
                        y = [0] * dim_pq
                        for r_idx in range(dim_pq):
                            val = 0
                            for c_idx in range(dim_p1_q):
                                val ^= dh_prev[r_idx][c_idx] & k_vec[c_idx]
                            y[r_idx] = val
                        dh_ker.append(y)

                im_dv_next: list[list[int]] = []
                if dv_next:
                    dim_p_q1 = dc.dims.get((p, q + 1), 0)
                    for c_idx in range(dim_p_q1):
                        im_dv_next.append([dv_next[r_idx][c_idx] for r_idx in range(dim_pq)])

                dim_den = subspace_span_rank_f2(dh_ker + im_dv_next, dim_pq)
                e2 = dim_num - dim_den
                E_dims[2][(p, q)] = e2

            else:  # rows filtration
                # E0 = C, d0 = dh: (p, q) -> (p-1, q)
                # E1_{p,q} = ker(dh_{p,q}) / im(dh_{p+1, q})
                # d1 : E1_{p,q} -> E1_{p, q-1} induced by dv
                dh_pq = dc.d_h.get((p, q), [])
                dh_next = dc.d_h.get((p + 1, q), [])
                dv_pq = dc.d_v.get((p, q), [])
                dv_prev = dc.d_v.get((p, q + 1), [])
                dh_tgt_mat = dc.d_h.get((p + 1, q - 1), [])

                ker_dh = nullspace_f2(dh_pq, dim_pq)
                dim_tgt = dc.dims.get((p, q - 1), 0)

                if dim_tgt == 0 or not dv_pq:
                    num_sub = ker_dh
                else:
                    if not dh_tgt_mat:
                        coker_basis = [
                            [1 if i == j else 0 for j in range(dim_tgt)] for i in range(dim_tgt)
                        ]
                    else:
                        dim_src_tgt = dc.dims.get((p + 1, q - 1), 0)
                        dh_tgt_T = [
                            [dh_tgt_mat[r][c] for r in range(dim_tgt)] for c in range(dim_src_tgt)
                        ]
                        coker_basis = nullspace_f2(dh_tgt_T, dim_tgt)

                    coker_dv = mat_mul_f2(coker_basis, dv_pq)
                    full_sys = coker_dv + dh_pq
                    num_sub = nullspace_f2(full_sys, dim_pq)

                dim_num = subspace_span_rank_f2(num_sub, dim_pq)

                # Denominator: d^v(ker(dh_{p, q+1})) + im(dh_{p+1, q})
                dim_p_q1 = dc.dims.get((p, q + 1), 0)
                dh_p_q1 = dc.d_h.get((p, q + 1), [])
                ker_dh_q1 = nullspace_f2(dh_p_q1, dim_p_q1)

                dv_ker: list[list[int]] = []
                if dv_prev and ker_dh_q1:
                    for k_vec in ker_dh_q1:
                        y = [0] * dim_pq
                        for r_idx in range(dim_pq):
                            val = 0
                            for c_idx in range(dim_p_q1):
                                val ^= dv_prev[r_idx][c_idx] & k_vec[c_idx]
                            y[r_idx] = val
                        dv_ker.append(y)

                im_dh_next: list[list[int]] = []
                if dh_next:
                    dim_p1_q = dc.dims.get((p + 1, q), 0)
                    for c_idx in range(dim_p1_q):
                        im_dh_next.append([dh_next[r_idx][c_idx] for r_idx in range(dim_pq)])

                dim_den = subspace_span_rank_f2(dv_ker + im_dh_next, dim_pq)
                e2 = dim_num - dim_den
                E_dims[2][(p, q)] = e2

    # Now compute differentials and higher pages using filtered total complex Z^r
    differentials: list[dict[str, str]] = []
    curr_page = {k: v for k, v in E_dims[2].items()}

    for r in range(2, 6):
        leaving_ranks: dict[tuple[int, int], int] = {}
        for p in range(6):
            for q in range(6):
                dim_zr = get_Z_plus_F_dim(p, q, r)
                dim_zr1 = get_Z_plus_F_dim(p, q, r + 1)
                rank_dr = dim_zr - dim_zr1
                if rank_dr > 0:
                    leaving_ranks[(p, q)] = rank_dr
                    differentials.append(
                        {
                            "r": str(r),
                            "from": f"{p},{q}",
                            "rank": str(rank_dr),
                        }
                    )

        # Advance page via recursion
        next_page: dict[tuple[int, int], int] = {}
        for p in range(6):
            for q in range(6):
                val = curr_page.get((p, q), 0)
                # Leaving rank
                r_out = leaving_ranks.get((p, q), 0)
                # Arriving rank
                if filtration == "columns":
                    src_p = p + r
                    src_q = q - r + 1
                else:
                    src_p = p - r + 1
                    src_q = q + r
                r_in = leaving_ranks.get((src_p, src_q), 0)
                new_val = val - r_out - r_in
                next_page[(p, q)] = max(0, new_val)
                E_dims[r + 1][(p, q)] = next_page[(p, q)]

        curr_page = next_page

    # E^inf is E^6
    E2_map = {f"{p},{q}": str(v) for (p, q), v in E_dims[2].items() if v > 0}
    Einf_map = {f"{p},{q}": str(v) for (p, q), v in E_dims[6].items() if v > 0}

    return E2_map, differentials, Einf_map, tot_homology


def solve(case: dict[str, Any]) -> dict[str, Any]:
    """Solve C020 double complex spectral sequence challenge case."""
    dc = DoubleComplex(case)
    err = dc.validate_complex_laws()
    if err:
        return err

    filt_req = case.get("filtration", "columns")
    if filt_req == "both":
        e2_c, diffs_c, einf_c, tot_c = compute_spectral_sequence(dc, "columns")
        e2_r, diffs_r, einf_r, _ = compute_spectral_sequence(dc, "rows")
        return {
            "status": "SOLVED",
            "filtration": "both",
            "columns": {
                "E2": e2_c,
                "differentials": diffs_c,
                "Einf": einf_c,
            },
            "rows": {
                "E2": e2_r,
                "differentials": diffs_r,
                "Einf": einf_r,
            },
            "tot_homology": tot_c,
        }
    else:
        filtration = "columns" if filt_req == "columns" else "rows"
        e2, diffs, einf, tot = compute_spectral_sequence(dc, filtration)
        return {
            "status": "SOLVED",
            "filtration": filtration,
            "E2": e2,
            "differentials": diffs,
            "Einf": einf,
            "tot_homology": tot,
        }
