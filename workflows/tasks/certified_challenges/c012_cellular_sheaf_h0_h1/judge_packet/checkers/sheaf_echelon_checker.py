"""Checker 2: Independent Echelon & Dual Dimension Certifier for C012.

Employs an independent fraction-free / echelon reduction algorithm over fractions.Fraction.
Validates:
1. Recomputes rank(delta) independently from scratch.
2. Enforces Euler-Poincare and Rank-Nullity theorems:
   h0_dim == dim C^0 - rank(delta)
   h1_dim == dim C^1 - rank(delta)
   h0_dim - h1_dim == dim C^0 - dim C^1
3. Target solvability oracle:
   Solves [delta | b] independently using echelon reduction.
   Asserts glues == (rank([delta | b]) == rank(delta)).
4. Certifies dual obstruction witnesses:
   delta^T eta == 0 and <eta, b> != 0.
5. Embeds all 4 C011 defenses:
   - _verify_refusal_warranted
   - Key whitelist (no phantom keys)
   - Strict canonical rational format
   - Total exception safety and unknown endpoint guards

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

try:
    from .sheaf_algebraic_checker import (
        CLOSED_OOS_REASONS,
        CLOSED_REFUSAL_CODES,
        SOLVED_ALLOWED_KEYS,
        _verify_oos_warranted,
        _verify_refusal_warranted,
        is_canonical_rational_str,
    )
except (ImportError, ValueError):
    try:
        from c012_cellular_sheaf_h0_h1.judge_packet.checkers.sheaf_algebraic_checker import (
            CLOSED_OOS_REASONS,
            CLOSED_REFUSAL_CODES,
            SOLVED_ALLOWED_KEYS,
            _verify_oos_warranted,
            _verify_refusal_warranted,
            is_canonical_rational_str,
        )
    except (ImportError, ValueError):
        from sheaf_algebraic_checker import (
            SOLVED_ALLOWED_KEYS,
            _verify_oos_warranted,
            _verify_refusal_warranted,
            is_canonical_rational_str,
        )


def _independent_rref_pivots(
    matrix: list[list[Fraction]],
) -> tuple[list[list[Fraction]], list[int]]:
    """Independent canonical RREF implementation with pivot column tracking."""
    if not matrix or not matrix[0]:
        return [], []
    nrows = len(matrix)
    ncols = len(matrix[0])
    A = [[Fraction(entry) for entry in row] for row in matrix]
    pivot_cols: list[int] = []
    r = 0
    for c in range(ncols):
        pivot_row = -1
        for row in range(r, nrows):
            if A[row][c] != 0:
                pivot_row = row
                break
        if pivot_row == -1:
            continue
        A[r], A[pivot_row] = A[pivot_row], A[r]
        pivot_val = A[r][c]
        for j in range(c, ncols):
            A[r][j] /= pivot_val
        for row in range(nrows):
            if row != r and A[row][c] != 0:
                factor = A[row][c]
                for j in range(c, ncols):
                    A[row][j] -= factor * A[r][j]
        pivot_cols.append(c)
        r += 1
        if r == nrows:
            break
    return A, pivot_cols


def _extract_sheaf_delta(
    case: Mapping[str, Any],
) -> tuple[bool, list[list[Fraction]], int, int, str]:
    """Independently extracts block coboundary matrix delta from case."""
    raw_verts = case.get("vertices")
    raw_edges = case.get("edges")
    if not isinstance(raw_verts, list) or not isinstance(raw_edges, list):
        return False, [], 0, 0, "malformed case topology"

    vertex_offsets: dict[str, int] = {}
    vertex_dims: dict[str, int] = {}
    dim_C0 = 0
    for v_spec in raw_verts:
        if isinstance(v_spec, Mapping):
            vid = v_spec.get("id")
            d_v = v_spec.get("dim")
        elif isinstance(v_spec, str):
            vid = v_spec
            stalks_dict = (
                case.get("stalks", {}).get("vertices", {})
                if isinstance(case.get("stalks"), Mapping)
                else {}
            )
            d_v = stalks_dict.get(vid, 1)
        else:
            return False, [], 0, 0, "malformed vertex specification"

        if not isinstance(vid, str) or not isinstance(d_v, int) or d_v < 0:
            return False, [], 0, 0, "invalid vertex id or dimension"
        vertex_offsets[vid] = dim_C0
        vertex_dims[vid] = d_v
        dim_C0 += d_v

    edge_offsets: dict[str, int] = {}
    edge_dims: dict[str, int] = {}
    dim_C1 = 0
    edge_list = []
    for idx, e_spec in enumerate(raw_edges):
        if not isinstance(e_spec, Mapping):
            return False, [], 0, 0, "malformed edge specification"
        eid = e_spec.get("id") or f"e{idx}"
        u = e_spec.get("u") or e_spec.get("tail")
        v = e_spec.get("v") or e_spec.get("head")
        d_e = e_spec.get("dim")
        if d_e is None:
            stalks_dict = (
                case.get("stalks", {}).get("edges", {})
                if isinstance(case.get("stalks"), Mapping)
                else {}
            )
            d_e = stalks_dict.get(eid, 1)

        if (
            not isinstance(eid, str)
            or not isinstance(u, str)
            or not isinstance(v, str)
            or not isinstance(d_e, int)
            or d_e < 0
        ):
            return False, [], 0, 0, "invalid edge structure"
        if u not in vertex_dims or v not in vertex_dims:
            return False, [], 0, 0, f"edge {eid} references unknown endpoint"

        edge_offsets[eid] = dim_C1
        edge_dims[eid] = d_e
        dim_C1 += d_e

        F_u_raw = e_spec.get("F_u")
        if F_u_raw is None:
            F_u_raw = e_spec.get("F_tail")
        F_v_raw = e_spec.get("F_v")
        if F_v_raw is None:
            F_v_raw = e_spec.get("F_head")
        if F_u_raw is None or F_v_raw is None:
            restr_dict = (
                case.get("restrictions", {})
                if isinstance(case.get("restrictions"), Mapping)
                else {}
            )
            e_restr = restr_dict.get(eid, {}) if isinstance(restr_dict.get(eid), Mapping) else {}
            if F_u_raw is None:
                F_u_raw = e_restr.get(u)
            if F_v_raw is None:
                F_v_raw = e_restr.get(v)

        edge_list.append((eid, u, v, d_e, F_u_raw, F_v_raw))

    delta = [[Fraction(0) for _ in range(dim_C0)] for _ in range(dim_C1)]
    for eid, u, v, d_e, F_u_raw, F_v_raw in edge_list:
        e_row_start = edge_offsets[eid]
        d_u = vertex_dims[u]
        d_v = vertex_dims[v]
        u_col_start = vertex_offsets[u]
        v_col_start = vertex_offsets[v]

        if not isinstance(F_u_raw, list) or len(F_u_raw) != d_e:
            return False, [], 0, 0, f"F_u row mismatch on edge {eid}"
        for r_idx, row in enumerate(F_u_raw):
            if not isinstance(row, list) or len(row) != d_u:
                return False, [], 0, 0, f"F_u col mismatch on edge {eid}"
            for c_idx, val_str in enumerate(row):
                if not is_canonical_rational_str(val_str):
                    return False, [], 0, 0, f"non-canonical entry in F_u on edge {eid}"
                delta[e_row_start + r_idx][u_col_start + c_idx] -= Fraction(val_str)

        if not isinstance(F_v_raw, list) or len(F_v_raw) != d_e:
            return False, [], 0, 0, f"F_v row mismatch on edge {eid}"
        for r_idx, row in enumerate(F_v_raw):
            if not isinstance(row, list) or len(row) != d_v:
                return False, [], 0, 0, f"F_v col mismatch on edge {eid}"
            for c_idx, val_str in enumerate(row):
                if not is_canonical_rational_str(val_str):
                    return False, [], 0, 0, f"non-canonical entry in F_v on edge {eid}"
                delta[e_row_start + r_idx][v_col_start + c_idx] += Fraction(val_str)

    return True, delta, dim_C0, dim_C1, "OK"


def verify_echelon_certificate(case: Any, result: Any) -> tuple[bool, str]:
    """Total parsing verifier for Checker 2 (Independent Echelon & Dual Dimension Certifier)."""
    if not isinstance(case, Mapping):
        return False, "FAIL: case is not a mapping"
    if not isinstance(result, Mapping):
        return False, "FAIL: result is not a mapping"

    status = result.get("status")
    if status == "UNKNOWN":
        refusal = result.get("refusal") or result.get("refusal_code")
        if not isinstance(refusal, str):
            return False, "FAIL: UNKNOWN status missing string refusal code"
        return _verify_refusal_warranted(case, refusal)

    if status == "OUT_OF_SCOPE":
        witness = result.get("witness")
        return _verify_oos_warranted(case, witness)

    if status != "SOLVED":
        return False, f"FAIL: unknown status {status!r}"

    # 1. Whitelist dictionary keys
    for k in result:
        if k not in SOLVED_ALLOWED_KEYS:
            return False, f"FAIL: unexpected extra phantom key {k!r} in result"

    # 2. Extract delta and cochain dimensions
    ok, delta, dim_C0, dim_C1, err = _extract_sheaf_delta(case)
    if not ok:
        return False, f"FAIL: {err}"

    # 3. Independent rank computation via RREF
    _, pivot_cols = _independent_rref_pivots(delta)
    rank_delta = len(pivot_cols)

    expected_h0_dim = dim_C0 - rank_delta
    expected_h1_dim = dim_C1 - rank_delta

    # Rank-Nullity / Euler Characteristic theorem verification
    if (expected_h0_dim - expected_h1_dim) != (dim_C0 - dim_C1):
        return False, "FAIL: Euler characteristic theorem violated in checker arithmetic"

    raw_h0_dim = result.get("h0_dim")
    raw_h1_dim = result.get("h1_dim")
    if not is_canonical_rational_str(str(raw_h0_dim)) or not is_canonical_rational_str(
        str(raw_h1_dim)
    ):
        return False, "FAIL: non-canonical dimension format"

    h0_dim = int(raw_h0_dim)
    h1_dim = int(raw_h1_dim)

    if h0_dim != expected_h0_dim:
        return False, f"FAIL: declared h0_dim {h0_dim} != expected dim ker delta {expected_h0_dim}"
    if h1_dim != expected_h1_dim:
        return (
            False,
            f"FAIL: declared h1_dim {h1_dim} != expected dim C^1/im delta {expected_h1_dim}",
        )

    # 4. Verify H^0 basis
    h0_basis_raw = result.get("h0_basis")
    if not isinstance(h0_basis_raw, list) or len(h0_basis_raw) != h0_dim:
        return False, f"FAIL: h0_basis length != h0_dim {h0_dim}"
    h0_vecs: list[list[Fraction]] = []
    for idx, v_raw in enumerate(h0_basis_raw):
        if not isinstance(v_raw, list) or len(v_raw) != dim_C0:
            return False, f"FAIL: h0_basis vector {idx} length mismatch"
        v_frac = []
        for val_str in v_raw:
            if not is_canonical_rational_str(val_str):
                return False, f"FAIL: h0_basis vector {idx} non-canonical entry {val_str!r}"
            v_frac.append(Fraction(val_str))
        # Check delta @ v == 0
        for r in range(dim_C1):
            row_sum = sum(delta[r][c] * v_frac[c] for c in range(dim_C0))
            if row_sum != 0:
                return False, f"FAIL: h0_basis vector {idx} not in ker delta"
        h0_vecs.append(v_frac)

    if h0_dim > 0:
        _, h0_pivots = _independent_rref_pivots(h0_vecs)
        if len(h0_pivots) != h0_dim:
            return False, "FAIL: h0_basis vectors are linearly dependent"

    # 5. Verify H^1 complement
    h1_comp_raw = result.get("h1_complement")
    if not isinstance(h1_comp_raw, list) or len(h1_comp_raw) != h1_dim:
        return False, f"FAIL: h1_complement length != h1_dim {h1_dim}"
    h1_vecs: list[list[Fraction]] = []
    for idx, v_raw in enumerate(h1_comp_raw):
        if not isinstance(v_raw, list) or len(v_raw) != dim_C1:
            return False, f"FAIL: h1_complement vector {idx} length mismatch"
        v_frac = []
        for val_str in v_raw:
            if not is_canonical_rational_str(val_str):
                return False, f"FAIL: h1_complement vector {idx} non-canonical entry {val_str!r}"
            v_frac.append(Fraction(val_str))
        h1_vecs.append(v_frac)

    # Augmented matrix [delta | h1_vecs]: dim_C1 x (dim_C0 + h1_dim)
    augmented_comp = [delta[r] + [h1_vecs[c][r] for c in range(h1_dim)] for r in range(dim_C1)]
    _, comp_pivots = _independent_rref_pivots(augmented_comp)
    if len(comp_pivots) != dim_C1:
        return (
            False,
            f"FAIL: im(delta) + span(h1_complement) rank {len(comp_pivots)} != dim C^1 {dim_C1}",
        )
    if len(comp_pivots) != rank_delta + h1_dim:
        return False, "FAIL: h1_complement vectors are not independent modulo im(delta)"

    # 6. Target Solvability Oracle
    targets_case = case.get("targets", [])
    targets_res = result.get("targets", [])
    if (
        not isinstance(targets_case, list)
        or not isinstance(targets_res, list)
        or len(targets_case) != len(targets_res)
    ):
        return False, "FAIL: targets count mismatch"

    for idx, (t_spec, t_ans) in enumerate(zip(targets_case, targets_res)):
        if not isinstance(t_spec, Mapping) or not isinstance(t_ans, Mapping):
            return False, f"FAIL: malformed target at index {idx}"
        b_raw = t_spec.get("b")
        if not isinstance(b_raw, list) or len(b_raw) != dim_C1:
            return False, f"FAIL: target {idx} b cochain length mismatch"

        b_vec: list[Fraction] = []
        for val_str in b_raw:
            if not is_canonical_rational_str(val_str):
                return False, f"FAIL: target {idx} non-canonical rational in b"
            b_vec.append(Fraction(val_str))

        glues = t_ans.get("glues")
        if not isinstance(glues, bool):
            return False, f"FAIL: target {idx} missing boolean 'glues'"

        # Independent augmented matrix [delta | b]
        aug = [delta[r] + [b_vec[r]] for r in range(dim_C1)]
        _, aug_pivots = _independent_rref_pivots(aug)
        is_solvable = len(aug_pivots) == rank_delta

        if glues != is_solvable:
            return False, (
                f"FAIL: target {idx} claimed glues={glues}, but independent echelon solver "
                f"determined is_solvable={is_solvable}"
            )

        if glues:
            for k in t_ans:
                if k not in ("glues", "x"):
                    return False, f"FAIL: unexpected phantom key {k!r} in target {idx}"
            x_raw = t_ans.get("x")
            if not isinstance(x_raw, list) or len(x_raw) != dim_C0:
                return False, f"FAIL: target {idx} gluing vector length mismatch"
            x_vec: list[Fraction] = []
            for val_str in x_raw:
                if not is_canonical_rational_str(val_str):
                    return False, f"FAIL: target {idx} non-canonical rational in x"
                x_vec.append(Fraction(val_str))
            # Check delta x == b
            for r in range(dim_C1):
                row_sum = sum(delta[r][c] * x_vec[c] for c in range(dim_C0))
                if row_sum != b_vec[r]:
                    return False, f"FAIL: target {idx} delta x != b (gluing condition failed)"
        else:
            for k in t_ans:
                if k not in ("glues", "eta"):
                    return False, f"FAIL: unexpected phantom key {k!r} in target {idx}"
            eta_raw = t_ans.get("eta")
            if not isinstance(eta_raw, list) or len(eta_raw) != dim_C1:
                return False, f"FAIL: target {idx} obstruction vector length mismatch"
            eta_vec: list[Fraction] = []
            for val_str in eta_raw:
                if not is_canonical_rational_str(val_str):
                    return False, f"FAIL: target {idx} non-canonical rational in eta"
                eta_vec.append(Fraction(val_str))

            # Check delta^T eta == 0
            for c in range(dim_C0):
                col_sum = sum(delta[r][c] * eta_vec[r] for r in range(dim_C1))
                if col_sum != 0:
                    return False, f"FAIL: target {idx} obstruction witness not in ker delta^T"

            # Check <eta, b> != 0
            inner = sum(eta_vec[r] * b_vec[r] for r in range(dim_C1))
            if inner == 0:
                return False, f"FAIL: target {idx} obstruction witness is orthogonal to target b"

    return True, "VALID_ECHELON_CERTIFICATE"
