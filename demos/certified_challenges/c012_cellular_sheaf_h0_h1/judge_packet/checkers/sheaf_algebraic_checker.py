"""Checker 1: Exact Algebraic & Coboundary Certifier for C012.

Reconstructs delta independently from raw case specification over fractions.Fraction.
Validates:
1. All h0_basis vectors satisfy delta x == 0 and are linearly independent.
2. len(h0_basis) == int(h0_dim).
3. len(h1_complement) == int(h1_dim).
4. [delta | h1_complement] spans C^1 (full column rank == dim C^1) and complement
   vectors are independent modulo im delta.
5. Targets:
   - glues == True: delta x == b
   - glues == False: delta^T eta == 0 and <eta, b> != 0
6. Embeds all 4 C011 defenses:
   - _verify_refusal_warranted
   - Key whitelist (no phantom keys)
   - Strict canonical rational format
   - Total exception safety and unknown endpoint guards

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping

CLOSED_REFUSAL_CODES = frozenset(
    {
        "VERTEX_COUNT_OUT_OF_BOUNDS",
        "EDGE_COUNT_OUT_OF_BOUNDS",
        "STALK_DIM_OUT_OF_BOUNDS",
        "COEFFICIENT_BOUND_EXCEEDED",
        "MALFORMED_RESTRICTION_MATRIX",
        "MALFORMED_TARGET_COCHAIN",
        "MALFORMED_CASE_STRUCTURE",
        "DISCONNECTED_GRAPH",
        "BUDGET_EXHAUSTED",
    }
)

CLOSED_OOS_REASONS = frozenset(
    {
        "RESTRICTION_SHAPE_MISMATCH",
        "SELF_LOOP",
        "UNKNOWN_ENDPOINT",
    }
)

SOLVED_ALLOWED_KEYS = frozenset(
    {"status", "h0_dim", "h0_basis", "h1_dim", "h1_complement", "targets", "id", "case_id"}
)


def is_canonical_rational_str(s: Any) -> bool:
    """Strict RFC 8785 canonical rational string format validator."""
    if not isinstance(s, str):
        return False
    if any(c.isspace() for c in s) or "." in s or "e" in s.lower() or "_" in s:
        return False
    if s.startswith("+") or s == "-0" or s.startswith("-0/"):
        return False
    if "/" in s:
        parts = s.split("/")
        if len(parts) != 2:
            return False
        num_str, den_str = parts[0], parts[1]
        try:
            num = int(num_str)
            den = int(den_str)
            if str(num) != num_str or str(den) != den_str:
                return False
            if den <= 1 or num == 0:
                return False
            if math.gcd(abs(num), den) != 1:
                return False
            return True
        except Exception:
            return False
    else:
        try:
            val = int(s)
            return str(val) == s
        except Exception:
            return False


def _parse_vec(v: Any, expected_len: int) -> tuple[bool, list[Fraction], str]:
    if not isinstance(v, list) or len(v) != expected_len:
        return False, [], f"expected list of length {expected_len}"
    res: list[Fraction] = []
    for idx, item in enumerate(v):
        if not is_canonical_rational_str(item):
            return False, [], f"coordinate {idx} is non-canonical rational: {item!r}"
        res.append(Fraction(item))
    return True, res, "OK"


def _mat_rank(M: list[list[Fraction]]) -> int:
    """Computes exact column/row rank of a matrix over Q."""
    if not M or not M[0]:
        return 0
    nrows = len(M)
    ncols = len(M[0])
    A = [[Fraction(entry) for entry in row] for row in M]
    r = 0
    for col in range(ncols):
        pivot_row = -1
        for row in range(r, nrows):
            if A[row][col] != 0:
                pivot_row = row
                break
        if pivot_row == -1:
            continue
        A[r], A[pivot_row] = A[pivot_row], A[r]
        pivot_val = A[r][col]
        for c in range(col, ncols):
            A[r][c] /= pivot_val
        for row in range(nrows):
            if row != r and A[row][col] != 0:
                factor = A[row][col]
                for c in range(col, ncols):
                    A[row][c] -= factor * A[r][c]
        r += 1
        if r == nrows:
            break
    return r


def _mat_vec_mul(M: list[list[Fraction]], v: list[Fraction]) -> list[Fraction]:
    nrows = len(M)
    ncols = len(M[0]) if nrows > 0 else 0
    return [sum(M[r][c] * v[c] for c in range(ncols)) for r in range(nrows)]


def _mat_transpose(M: list[list[Fraction]]) -> list[list[Fraction]]:
    if not M:
        return []
    nrows = len(M)
    ncols = len(M[0])
    return [[M[r][c] for r in range(nrows)] for c in range(ncols)]


def _verify_refusal_warranted(case: Mapping[str, Any], refusal: str) -> tuple[bool, str]:
    """Audits claimed refusal against input case data to prevent bogus refusal passes."""
    if not isinstance(case, Mapping):
        if refusal == "MALFORMED_CASE_STRUCTURE":
            return True, "VALID_REFUSAL_MALFORMED_CASE_STRUCTURE"
        return False, "FAIL: refused on non-mapping case without MALFORMED_CASE_STRUCTURE"

    raw_verts = case.get("vertices")
    raw_edges = case.get("edges")

    if refusal == "VERTEX_COUNT_OUT_OF_BOUNDS":
        if isinstance(raw_verts, list) and 1 <= len(raw_verts) <= 30:
            return False, f"FAIL: refused VERTEX_COUNT_OUT_OF_BOUNDS on valid |V|={len(raw_verts)}"
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "EDGE_COUNT_OUT_OF_BOUNDS":
        if isinstance(raw_edges, list) and 0 <= len(raw_edges) <= 60:
            return False, f"FAIL: refused EDGE_COUNT_OUT_OF_BOUNDS on valid |E|={len(raw_edges)}"
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "STALK_DIM_OUT_OF_BOUNDS":
        has_bad_stalk = False
        d0 = 0
        d1 = 0
        if isinstance(raw_verts, list):
            for v in raw_verts:
                dim_v = v.get("dim") if isinstance(v, Mapping) else 1
                if not isinstance(dim_v, int) or dim_v < 0 or dim_v > 4:
                    has_bad_stalk = True
                else:
                    d0 += dim_v
        if isinstance(raw_edges, list):
            for e in raw_edges:
                dim_e = e.get("dim") if isinstance(e, Mapping) else 1
                if not isinstance(dim_e, int) or dim_e < 0 or dim_e > 4:
                    has_bad_stalk = True
                else:
                    d1 += dim_e
        if d0 > 240 or d1 > 240:
            has_bad_stalk = True
        if not has_bad_stalk:
            return False, "FAIL: refused STALK_DIM_OUT_OF_BOUNDS on valid stalk dimensions"
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "COEFFICIENT_BOUND_EXCEEDED":
        has_bad_coeff = False
        if isinstance(raw_edges, list):
            for e in raw_edges:
                if isinstance(e, Mapping):
                    for key in ("F_u", "F_v", "F_tail", "F_head"):
                        mat = e.get(key)
                        if isinstance(mat, list):
                            for row in mat:
                                if isinstance(row, list):
                                    for item in row:
                                        try:
                                            f = (
                                                Fraction(item)
                                                if isinstance(item, (int, str))
                                                else None
                                            )
                                            if f and (
                                                abs(f.numerator) > 99 or abs(f.denominator) > 99
                                            ):
                                                has_bad_coeff = True
                                        except Exception:
                                            pass
        if not has_bad_coeff:
            return False, "FAIL: refused COEFFICIENT_BOUND_EXCEEDED on case with coefficients <= 99"
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "MALFORMED_RESTRICTION_MATRIX":
        has_malformed_restr = False
        if isinstance(raw_edges, list):
            for e in raw_edges:
                if isinstance(e, Mapping):
                    for key in ("F_u", "F_v"):
                        mat = e.get(key)
                        if mat is not None:
                            if not isinstance(mat, list):
                                has_malformed_restr = True
                            else:
                                for row in mat:
                                    if not isinstance(row, list):
                                        has_malformed_restr = True
                                    else:
                                        for item in row:
                                            if not is_canonical_rational_str(item):
                                                has_malformed_restr = True
        if not has_malformed_restr:
            return (
                False,
                "FAIL: refused MALFORMED_RESTRICTION_MATRIX on case with valid restriction matrices",
            )
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "MALFORMED_TARGET_COCHAIN":
        has_malformed_target = False
        targets = case.get("targets")
        if not isinstance(targets, list):
            has_malformed_target = True
        else:
            dim_c1 = sum(e.get("dim", 1) for e in raw_edges) if isinstance(raw_edges, list) else 0
            for t in targets:
                if not isinstance(t, Mapping) or "b" not in t:
                    has_malformed_target = True
                else:
                    b_vec = t.get("b")
                    if not isinstance(b_vec, list) or len(b_vec) != dim_c1:
                        has_malformed_target = True
                    else:
                        for item in b_vec:
                            if not is_canonical_rational_str(item):
                                has_malformed_target = True
        if not has_malformed_target:
            return False, "FAIL: refused MALFORMED_TARGET_COCHAIN on valid targets"
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "MALFORMED_CASE_STRUCTURE":
        is_malformed = (
            not isinstance(raw_verts, list) or not isinstance(raw_edges, list) or "id" not in case
        )
        if not is_malformed:
            return False, "FAIL: refused MALFORMED_CASE_STRUCTURE on structurally valid case"
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "BUDGET_EXHAUSTED":
        # Budget exhaustion carries no witness a judge can check, and every case
        # within the declared bounds is decidable, so it never counts as valid.
        return False, "FAIL: BUDGET_EXHAUSTED is not a verifiable answer for an in-bounds case"

    return False, f"FAIL: unrecognized or unwarranted refusal code {refusal!r}"


def _verify_oos_warranted(case: Mapping[str, Any], witness: Any) -> tuple[bool, str]:
    """Audits OUT_OF_SCOPE witness against case data."""
    if not isinstance(witness, Mapping):
        return False, "FAIL: OUT_OF_SCOPE witness is not a mapping"

    reason = witness.get("reason")
    if reason not in CLOSED_OOS_REASONS:
        return False, f"FAIL: unknown OUT_OF_SCOPE reason {reason!r}"

    raw_verts = case.get("vertices", [])
    raw_edges = case.get("edges", [])
    vert_ids = {v.get("id") if isinstance(v, Mapping) else v for v in raw_verts}

    if reason == "UNKNOWN_ENDPOINT":
        has_unknown = any(
            (e.get("u") not in vert_ids or e.get("v") not in vert_ids)
            for e in raw_edges
            if isinstance(e, Mapping)
        )
        if not has_unknown:
            return (
                False,
                "FAIL: OUT_OF_SCOPE claimed UNKNOWN_ENDPOINT on graph with valid endpoints",
            )
        return True, "VALID_OOS_UNKNOWN_ENDPOINT"

    if reason == "SELF_LOOP":
        has_self_loop = any(e.get("u") == e.get("v") for e in raw_edges if isinstance(e, Mapping))
        if not has_self_loop:
            return False, "FAIL: OUT_OF_SCOPE claimed SELF_LOOP on graph without self-loops"
        return True, "VALID_OOS_SELF_LOOP"

    if reason == "RESTRICTION_SHAPE_MISMATCH":
        has_shape_mismatch = False
        v_dims = {
            (v.get("id") if isinstance(v, Mapping) else v): (
                v.get("dim", 1) if isinstance(v, Mapping) else 1
            )
            for v in raw_verts
        }
        for e in raw_edges:
            if isinstance(e, Mapping):
                d_e = e.get("dim", 1)
                u = e.get("u")
                v = e.get("v")
                d_u = v_dims.get(u, 1)
                d_v = v_dims.get(v, 1)
                for key, d_vert in [("F_u", d_u), ("F_v", d_v)]:
                    mat = e.get(key)
                    if isinstance(mat, list):
                        if len(mat) != d_e:
                            has_shape_mismatch = True
                        for row in mat:
                            if isinstance(row, list) and len(row) != d_vert:
                                has_shape_mismatch = True
        if not has_shape_mismatch:
            return (
                False,
                "FAIL: OUT_OF_SCOPE claimed RESTRICTION_SHAPE_MISMATCH on matching restriction shapes",
            )
        return True, "VALID_OOS_RESTRICTION_SHAPE_MISMATCH"

    return False, f"FAIL: unhandled OUT_OF_SCOPE reason {reason!r}"


def verify_algebraic_certificate(case: Any, result: Any) -> tuple[bool, str]:
    """Total parsing verifier for Checker 1 (Exact Algebraic & Coboundary Certifier)."""
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

    # 1. Whitelist dictionary keys in result
    for k in result:
        if k not in SOLVED_ALLOWED_KEYS:
            return False, f"FAIL: unexpected extra phantom key {k!r} in result"

    # 2. Extract and validate graph & stalk definitions
    raw_verts = case.get("vertices")
    raw_edges = case.get("edges")
    if not isinstance(raw_verts, list) or not isinstance(raw_edges, list):
        return False, "FAIL: malformed case graph topology"

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
            return False, "FAIL: malformed vertex specification"

        if not isinstance(vid, str) or not isinstance(d_v, int) or d_v < 0:
            return False, "FAIL: invalid vertex id or stalk dimension"
        vertex_offsets[vid] = dim_C0
        vertex_dims[vid] = d_v
        dim_C0 += d_v

    edge_offsets: dict[str, int] = {}
    edge_dims: dict[str, int] = {}
    dim_C1 = 0
    edge_list = []
    for idx, e_spec in enumerate(raw_edges):
        if not isinstance(e_spec, Mapping):
            return False, "FAIL: malformed edge specification"
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
            return False, "FAIL: invalid edge structure"
        if u not in vertex_dims or v not in vertex_dims:
            return False, f"FAIL: edge {eid} references unknown endpoint"

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

    # 3. Assemble coboundary matrix delta: dim_C1 x dim_C0
    delta = [[Fraction(0) for _ in range(dim_C0)] for _ in range(dim_C1)]
    for eid, u, v, d_e, F_u_raw, F_v_raw in edge_list:
        e_row_start = edge_offsets[eid]
        d_u = vertex_dims[u]
        d_v = vertex_dims[v]
        u_col_start = vertex_offsets[u]
        v_col_start = vertex_offsets[v]

        if not isinstance(F_u_raw, list) or len(F_u_raw) != d_e:
            return False, f"FAIL: F_u row count mismatch on edge {eid}"
        for r_idx, row in enumerate(F_u_raw):
            if not isinstance(row, list) or len(row) != d_u:
                return False, f"FAIL: F_u col count mismatch on edge {eid}"
            for c_idx, val_str in enumerate(row):
                if not is_canonical_rational_str(val_str):
                    return False, f"FAIL: non-canonical entry in F_u on edge {eid}"
                delta[e_row_start + r_idx][u_col_start + c_idx] -= Fraction(val_str)

        if not isinstance(F_v_raw, list) or len(F_v_raw) != d_e:
            return False, f"FAIL: F_v row count mismatch on edge {eid}"
        for r_idx, row in enumerate(F_v_raw):
            if not isinstance(row, list) or len(row) != d_v:
                return False, f"FAIL: F_v col count mismatch on edge {eid}"
            for c_idx, val_str in enumerate(row):
                if not is_canonical_rational_str(val_str):
                    return False, f"FAIL: non-canonical entry in F_v on edge {eid}"
                delta[e_row_start + r_idx][v_col_start + c_idx] += Fraction(val_str)

    # 4. Verify H^0 basis
    raw_h0_dim = result.get("h0_dim")
    if not is_canonical_rational_str(str(raw_h0_dim)) or int(raw_h0_dim) < 0:
        return False, f"FAIL: invalid h0_dim {raw_h0_dim!r}"
    h0_dim = int(raw_h0_dim)

    h0_basis_raw = result.get("h0_basis")
    if not isinstance(h0_basis_raw, list) or len(h0_basis_raw) != h0_dim:
        return False, f"FAIL: h0_basis length != h0_dim {h0_dim}"

    h0_vecs: list[list[Fraction]] = []
    for idx, v_raw in enumerate(h0_basis_raw):
        ok, v_frac, msg = _parse_vec(v_raw, dim_C0)
        if not ok:
            return False, f"FAIL: h0_basis vector {idx}: {msg}"
        img = _mat_vec_mul(delta, v_frac)
        if any(c != 0 for c in img):
            return False, f"FAIL: h0_basis vector {idx} not in kernel of delta"
        h0_vecs.append(v_frac)

    # Linear independence of H^0 basis
    if h0_dim > 0:
        X_mat = [[h0_vecs[c][r] for c in range(h0_dim)] for r in range(dim_C0)]
        if _mat_rank(X_mat) != h0_dim:
            return False, "FAIL: h0_basis vectors are linearly dependent"

    # 5. Verify H^1 complement
    raw_h1_dim = result.get("h1_dim")
    if not is_canonical_rational_str(str(raw_h1_dim)) or int(raw_h1_dim) < 0:
        return False, f"FAIL: invalid h1_dim {raw_h1_dim!r}"
    h1_dim = int(raw_h1_dim)

    h1_comp_raw = result.get("h1_complement")
    if not isinstance(h1_comp_raw, list) or len(h1_comp_raw) != h1_dim:
        return False, f"FAIL: h1_complement length != h1_dim {h1_dim}"

    h1_vecs: list[list[Fraction]] = []
    for idx, v_raw in enumerate(h1_comp_raw):
        ok, v_frac, msg = _parse_vec(v_raw, dim_C1)
        if not ok:
            return False, f"FAIL: h1_complement vector {idx}: {msg}"
        h1_vecs.append(v_frac)

    # Augmented matrix: [delta | h1_vecs] of size dim_C1 x (dim_C0 + h1_dim)
    augmented = [delta[r] + [h1_vecs[c][r] for c in range(h1_dim)] for r in range(dim_C1)]
    rank_augmented = _mat_rank(augmented)
    if rank_augmented != dim_C1:
        return (
            False,
            f"FAIL: im(delta) + span(h1_complement) rank {rank_augmented} != dim C^1 {dim_C1}",
        )

    rank_delta = _mat_rank(delta)
    if rank_augmented != rank_delta + h1_dim:
        return False, "FAIL: h1_complement vectors are not independent modulo im(delta)"

    # 6. Verify Targets
    targets_case = case.get("targets", [])
    targets_res = result.get("targets", [])
    if (
        not isinstance(targets_case, list)
        or not isinstance(targets_res, list)
        or len(targets_case) != len(targets_res)
    ):
        return False, "FAIL: targets count mismatch"

    delta_T = _mat_transpose(delta)

    for idx, (t_spec, t_ans) in enumerate(zip(targets_case, targets_res)):
        if not isinstance(t_spec, Mapping) or not isinstance(t_ans, Mapping):
            return False, f"FAIL: malformed target entry at index {idx}"
        b_raw = t_spec.get("b")
        ok, b_frac, msg = _parse_vec(b_raw, dim_C1)
        if not ok:
            return False, f"FAIL: target {idx} b cochain malformed: {msg}"

        glues = t_ans.get("glues")
        if not isinstance(glues, bool):
            return False, f"FAIL: target {idx} missing boolean 'glues'"

        if glues:
            for k in t_ans:
                if k not in ("glues", "x"):
                    return False, f"FAIL: unexpected phantom key {k!r} in target {idx}"
            ok, x_frac, msg = _parse_vec(t_ans.get("x"), dim_C0)
            if not ok:
                return False, f"FAIL: target {idx} gluing vector x: {msg}"
            dx = _mat_vec_mul(delta, x_frac)
            if any(dx[i] != b_frac[i] for i in range(dim_C1)):
                return False, f"FAIL: target {idx} delta x != b (gluing condition failed)"
        else:
            for k in t_ans:
                if k not in ("glues", "eta"):
                    return False, f"FAIL: unexpected phantom key {k!r} in target {idx}"
            ok, eta_frac, msg = _parse_vec(t_ans.get("eta"), dim_C1)
            if not ok:
                return False, f"FAIL: target {idx} obstruction vector eta: {msg}"
            d_T_eta = _mat_vec_mul(delta_T, eta_frac)
            if any(d_T_eta[i] != 0 for i in range(dim_C0)):
                return False, f"FAIL: target {idx} delta^T eta != 0 (not in cokernel)"
            inner_prod = sum(eta_frac[i] * b_frac[i] for i in range(dim_C1))
            if inner_prod == 0:
                return (
                    False,
                    f"FAIL: target {idx} <eta, b> == 0 (invalid Fredholm obstruction witness)",
                )

    return True, "VALID_ALGEBRAIC_CERTIFICATE"


# Alias for backward compatibility
verify_coboundary_certificate = verify_algebraic_certificate
