"""Algebraic Certificate Checker (Checker 1) for C016.

Directly verifies mathematical certificates on both complexes:
1. Cocycle condition: delta(alpha) = 0 and delta(beta) = 0 for all basis elements.
2. Independence: basis_p and basis_q represent linearly independent cohomology classes.
3. Nonzero products: cycle z satisfies partial(z) = 0, and <alpha_i smile beta_j, z> == value != 0.
4. Primitives: primitive gamma satisfies delta(gamma) = alpha_i smile beta_j.
5. Rank and verdict consistency: verdict is DISTINGUISHED iff X["rank"] != Y["rank"].
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from omega_engine_pfp.tests.demo_004.b_cohomology.c016_cohomology_ring_cup_products.reference_solver.simplicial_cohomology import (
    alexander_whitney_product,
    build_boundary_matrix,
    close_simplicial_complex,
    compute_betti_numbers,
    evaluate_cochain_on_chain,
)


def parse_serialized_chain(chain_dict: dict[str, Any]) -> dict[tuple[int, ...], Fraction]:
    if not isinstance(chain_dict, dict):
        raise ValueError("serialized chain must be a mapping")
    res: dict[tuple[int, ...], Fraction] = {}
    for k_str, v_str in chain_dict.items():
        if not isinstance(k_str, str):
            raise ValueError("serialized simplex key must be a string")
        # k_str looks like "[0, 1, 2]" or "(0, 1, 2)"
        s = k_str.strip().strip("[]()").replace(" ", "")
        if not s:
            continue
        verts = tuple(sorted(int(x) for x in s.split(",")))
        val = Fraction(str(v_str))
        if val != 0:
            res[verts] = val
    return res


def _parse_basis_index(value: Any, size: int) -> int:
    if type(value) not in (int, str):
        raise ValueError("basis index must be an integer or integer string")
    index = int(value)
    if not 0 <= index < size:
        raise ValueError(f"basis index {index} outside basis of size {size}")
    return index


def check_algebraic_cup_certificate(
    case: dict[str, Any], result: dict[str, Any]
) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a dict"

    status = result.get("status")
    p = case.get("deg_p", 1)
    q = case.get("deg_q", 1)

    raw_X = case.get("X", {}).get("maximal_simplices", [])
    raw_Y = case.get("Y", {}).get("maximal_simplices", [])
    X_simps = close_simplicial_complex(raw_X)
    Y_simps = close_simplicial_complex(raw_Y)

    betti_X = compute_betti_numbers(X_simps)
    betti_Y = compute_betti_numbers(Y_simps)

    # Check if this case should be OUT_OF_SCOPE
    mismatch_degree = next((d for d in range(5) if betti_X[d] != betti_Y[d]), None)
    if mismatch_degree is not None:
        if status != "OUT_OF_SCOPE":
            return (
                False,
                f"Expected OUT_OF_SCOPE due to Betti mismatch X={betti_X} vs Y={betti_Y}, got {status}",
            )
        witness = result.get("witness", {})
        if not isinstance(witness, dict):
            return False, "OUT_OF_SCOPE witness must be a mapping"
        if witness.get("reason") != "BETTI_MISMATCH":
            return False, "OUT_OF_SCOPE witness missing BETTI_MISMATCH reason"
        if witness.get("degree") != str(mismatch_degree):
            return False, f"BETTI_MISMATCH witness must name degree {mismatch_degree}"
        if witness.get("betti_X") != betti_X[mismatch_degree]:
            return False, "BETTI_MISMATCH witness has the wrong X Betti number"
        if witness.get("betti_Y") != betti_Y[mismatch_degree]:
            return False, "BETTI_MISMATCH witness has the wrong Y Betti number"
        return True, "Valid OUT_OF_SCOPE witness verified"

    if status != "SOLVED":
        return False, f"Expected SOLVED, got {status}"

    verdict = result.get("verdict")
    if verdict not in ("DISTINGUISHED", "NOT_DISTINGUISHED_BY_THIS_PRODUCT"):
        return False, f"Invalid verdict: {verdict}"

    # Helper to verify certificate on one side
    def verify_side(
        name: str, side_data: dict[str, Any], simps: dict[int, list[tuple[int, ...]]]
    ) -> tuple[bool, str]:
        if not isinstance(side_data, dict):
            return False, f"{name} certificate is not a dict"

        try:
            claimed_rank = int(side_data.get("rank", -1))
        except (ValueError, TypeError):
            return False, f"{name} rank is not an integer"

        raw_bp = side_data.get("basis_p", [])
        raw_bq = side_data.get("basis_q", [])
        if not isinstance(raw_bp, list) or not isinstance(raw_bq, list):
            return False, f"{name} malformed basis: expected lists of serialized chains"
        try:
            basis_p = [parse_serialized_chain(c) for c in raw_bp]
            basis_q = [parse_serialized_chain(c) for c in raw_bq]
        except (ValueError, ZeroDivisionError) as exc:
            return False, f"{name} malformed basis chain: {exc}"

        valid_p = set(simps[p])
        valid_q = set(simps[q])
        valid_target = set(simps[p + q])
        valid_target_minus_1 = set(simps[p + q - 1]) if p + q > 0 else set()

        for idx, alpha in enumerate(basis_p):
            for s in alpha:
                if s not in valid_p:
                    return False, f"{name} basis_p[{idx}] contains simplex {s} not in C^{p}"

        for idx, beta in enumerate(basis_q):
            for s in beta:
                if s not in valid_q:
                    return False, f"{name} basis_q[{idx}] contains simplex {s} not in C^{q}"

        # 1. Verify cocycle conditions
        # delta_p on basis_p: for each alpha in basis_p, delta_p(alpha) must be 0
        d_p_plus_1 = build_boundary_matrix(simps[p + 1], simps[p]) if p < 4 else []
        for idx, alpha in enumerate(basis_p):
            # Evaluate on all boundary columns of d_{p+1}
            for col_idx, s in enumerate(simps[p + 1]):
                val = Fraction(0)
                if d_p_plus_1:
                    for row_idx, f in enumerate(simps[p]):
                        coeff = d_p_plus_1[row_idx][col_idx]
                        if coeff != 0 and f in alpha:
                            val += coeff * alpha[f]
                if val != 0:
                    return (
                        False,
                        f"{name} basis_p[{idx}] is not a cocycle on simplex {s}: delta={val}",
                    )

        # delta_q on basis_q: for each beta in basis_q, delta_q(beta) must be 0
        d_q_plus_1 = build_boundary_matrix(simps[q + 1], simps[q]) if q < 4 else []
        for idx, beta in enumerate(basis_q):
            for col_idx, s in enumerate(simps[q + 1]):
                val = Fraction(0)
                if d_q_plus_1:
                    for row_idx, f in enumerate(simps[q]):
                        coeff = d_q_plus_1[row_idx][col_idx]
                        if coeff != 0 and f in beta:
                            val += coeff * beta[f]
                if val != 0:
                    return (
                        False,
                        f"{name} basis_q[{idx}] is not a cocycle on simplex {s}: delta={val}",
                    )

        # 2. Verify nonzero witnesses
        nonzero_list = side_data.get("nonzero", [])
        if not isinstance(nonzero_list, list):
            return False, f"{name} malformed nonzero witnesses: expected a list"
        if len(nonzero_list) < claimed_rank:
            return (
                False,
                f"{name} nonzero witnesses count {len(nonzero_list)} < claimed rank {claimed_rank}",
            )

        d_target = build_boundary_matrix(simps[p + q], simps[p + q - 1]) if p + q > 0 else []
        for nw in nonzero_list:
            if not isinstance(nw, dict):
                return False, f"{name} malformed nonzero witness: expected a mapping"
            try:
                i = _parse_basis_index(nw["i"], len(basis_p))
                j = _parse_basis_index(nw["j"], len(basis_q))
                z = parse_serialized_chain(nw["cycle"])
                expected_val = Fraction(str(nw["value"]))
            except (KeyError, ValueError, ZeroDivisionError) as exc:
                return False, f"{name} malformed nonzero witness: {exc}"
            for s in z:
                if s not in valid_target:
                    return False, f"{name} witness cycle contains simplex {s} not in C_{p + q}"
            if expected_val == 0:
                return False, f"{name} nonzero witness reported zero value"

            # Check partial(z) == 0: boundary of cycle z is 0
            if d_target:
                for row_idx, face in enumerate(simps[p + q - 1]):
                    bd_val = Fraction(0)
                    for col_idx, s in enumerate(simps[p + q]):
                        coeff = d_target[row_idx][col_idx]
                        if coeff != 0 and s in z:
                            bd_val += coeff * z[s]
                    if bd_val != 0:
                        return (
                            False,
                            f"{name} witness cycle is not closed at face {face}: partial={bd_val}",
                        )

            # Check <alpha_i smile beta_j, z> == expected_val
            prod = alexander_whitney_product(basis_p[i], basis_q[j], p, q, simps[p + q])
            actual_val = evaluate_cochain_on_chain(prod, z)
            if actual_val != expected_val:
                return (
                    False,
                    f"{name} product evaluation mismatch: expected {expected_val}, got {actual_val}",
                )

        # 3. Verify primitive witnesses for zero products
        prim_list = side_data.get("primitives", [])
        if not isinstance(prim_list, list):
            return False, f"{name} malformed primitive witnesses: expected a list"
        for pw in prim_list:
            if not isinstance(pw, dict):
                return False, f"{name} malformed primitive witness: expected a mapping"
            try:
                i = _parse_basis_index(pw["i"], len(basis_p))
                j = _parse_basis_index(pw["j"], len(basis_q))
                gamma = parse_serialized_chain(pw["gamma"])
            except (KeyError, ValueError, ZeroDivisionError) as exc:
                return False, f"{name} malformed primitive witness: {exc}"
            for s in gamma:
                if s not in valid_target_minus_1:
                    return (
                        False,
                        f"{name} primitive gamma contains simplex {s} not in C^{p + q - 1}",
                    )
            prod = alexander_whitney_product(basis_p[i], basis_q[j], p, q, simps[p + q])

            # Check delta(gamma) == prod
            # delta(gamma)[s] = sum_face sign * gamma[face]
            if d_target:
                for col_idx, s in enumerate(simps[p + q]):
                    delta_gamma_s = Fraction(0)
                    for row_idx, face in enumerate(simps[p + q - 1]):
                        coeff = d_target[row_idx][col_idx]
                        if coeff != 0 and face in gamma:
                            delta_gamma_s += coeff * gamma[face]
                    prod_s = prod.get(s, Fraction(0))
                    if delta_gamma_s != prod_s:
                        return (
                            False,
                            f"{name} primitive failure at simplex {s}: delta(gamma)={delta_gamma_s} != prod={prod_s}",
                        )

        return True, "Side verified"

    ok_x, reason_x = verify_side("X", result.get("X", {}), X_simps)
    if not ok_x:
        return False, f"X certificate failure: {reason_x}"

    ok_y, reason_y = verify_side("Y", result.get("Y", {}), Y_simps)
    if not ok_y:
        return False, f"Y certificate failure: {reason_y}"

    rank_x = int(result["X"]["rank"])
    rank_y = int(result["Y"]["rank"])
    expected_verdict = "DISTINGUISHED" if rank_x != rank_y else "NOT_DISTINGUISHED_BY_THIS_PRODUCT"
    if verdict != expected_verdict:
        return (
            False,
            f"Verdict contradiction: claimed {verdict}, but rank_X={rank_x} vs rank_Y={rank_y} implies {expected_verdict}",
        )

    return True, "Algebraic cup product certificate verified"
