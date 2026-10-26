"""Reference Solver for C016: Cohomology Ring Cup Products.

Decides whether cup products distinguish two simplicial complexes X and Y with equal Betti numbers.
Returns certificates for both complexes (basis cocycles, nonzero cycle evaluations, coboundary primitives).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from .ddc_tracer import DDCTracer
from .rational_linear_algebra import exact_rank
from .simplicial_cohomology import (
    alexander_whitney_product,
    close_simplicial_complex,
    compute_betti_numbers,
    compute_cohomology_basis,
    compute_homology_basis,
    evaluate_cochain_on_chain,
    find_primitive_coboundary,
)


def serialize_chain(chain_dict: dict[tuple[int, ...], Fraction]) -> dict[str, str]:
    return {str(list(k)): str(v) for k, v in sorted(chain_dict.items())}


def solve(case: dict[str, Any]) -> tuple[dict[str, Any], DDCTracer]:
    tracer = DDCTracer()
    case_id = str(case.get("id", "c016_unknown"))
    tracer.record_step("E", "init_solver", payload={"case_id": case_id})

    # Validate degrees p and q
    p = case.get("deg_p", 1)
    q = case.get("deg_q", 1)
    if not isinstance(p, int) or not isinstance(q, int) or p < 0 or q < 0 or p + q > 4:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "INVALID_DEGREES",
            "refusal_code": "INVALID_DEGREES",
            "details": f"deg_p={p}, deg_q={q} must satisfy p, q >= 0 and p+q <= 4",
        }
        tracer.record_step(
            "M", "refusal_degrees", payload=refusal, refusal_reason="INVALID_DEGREES"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    raw_X = case.get("X", {}).get("maximal_simplices")
    raw_Y = case.get("Y", {}).get("maximal_simplices")
    if not isinstance(raw_X, list) or not isinstance(raw_Y, list):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_INPUT",
            "refusal_code": "MALFORMED_INPUT",
            "details": "X and Y must contain maximal_simplices lists",
        }
        tracer.record_step(
            "M", "refusal_missing_complexes", payload=refusal, refusal_reason="MALFORMED_INPUT"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    try:
        X_simplices = close_simplicial_complex(raw_X)
        Y_simplices = close_simplicial_complex(raw_Y)
    except Exception as ex:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_INPUT",
            "refusal_code": "MALFORMED_INPUT",
            "details": str(ex),
        }
        tracer.record_step(
            "M", "refusal_closure", payload=refusal, refusal_reason="MALFORMED_INPUT"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    tracer.record_step(
        "C",
        "complexes_closed",
        payload={
            "X_counts": {str(k): len(v) for k, v in X_simplices.items()},
            "Y_counts": {str(k): len(v) for k, v in Y_simplices.items()},
        },
    )

    # Compute Betti numbers on both sides
    betti_X = compute_betti_numbers(X_simplices)
    betti_Y = compute_betti_numbers(Y_simplices)
    tracer.record_step(
        "E", "betti_numbers_computed", payload={"betti_X": betti_X, "betti_Y": betti_Y}
    )

    # Check for Betti mismatch
    for deg in range(5):
        if betti_X[deg] != betti_Y[deg]:
            out_of_scope = {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {
                    "reason": "BETTI_MISMATCH",
                    "degree": str(deg),
                    "betti_X": betti_X[deg],
                    "betti_Y": betti_Y[deg],
                },
            }
            tracer.record_step("I", "betti_mismatch_detected", payload=out_of_scope)
            tracer.record_step("T", "terminalize_out_of_scope", payload=out_of_scope)
            return out_of_scope, tracer

    # Helper to analyze cup products on one complex
    def analyze_complex(simplices: dict[int, list[tuple[int, ...]]]) -> dict[str, Any]:
        basis_p = compute_cohomology_basis(simplices, p)
        basis_q = compute_cohomology_basis(simplices, q)
        homology_target = compute_homology_basis(simplices, p + q)

        # Form all products alpha_i smile beta_j
        products: list[tuple[int, int, dict[tuple[int, ...], Fraction]]] = []
        for i, a in enumerate(basis_p):
            for j, b in enumerate(basis_q):
                prod = alexander_whitney_product(a, b, p, q, simplices[p + q])
                products.append((i, j, prod))

        # Evaluate against homology basis
        # Matrix shape: len(homology_target) rows, len(products) columns
        eval_matrix: list[list[Fraction]] = []
        for z in homology_target:
            row = [evaluate_cochain_on_chain(prod, z) for _, _, prod in products]
            eval_matrix.append(row)

        rank = exact_rank(eval_matrix)

        # Find independent nonzero products and witness cycles
        nonzero_witnesses = []
        primitive_witnesses = []

        # Find a basis of column indices that achieve rank
        if rank > 0:
            # Transpose to find pivot columns of eval_matrix
            # Using row reduction on eval_matrix
            # Let's find which products are nonzero in cohomology
            # Greedily pick columns that increase rank
            chosen_cols: list[int] = []
            curr_submat: list[list[Fraction]] = [[] for _ in range(len(homology_target))]
            curr_r = 0

            for col_idx, (i, j, prod) in enumerate(products):
                test_submat = [
                    curr_submat[r] + [eval_matrix[r][col_idx]] for r in range(len(homology_target))
                ]
                new_r = exact_rank(test_submat)
                if new_r > curr_r:
                    chosen_cols.append(col_idx)
                    curr_submat = test_submat
                    curr_r = new_r
                    # Find a cycle witnessing that this product is nonzero
                    # Pick the first cycle where evaluation is nonzero
                    witness_cycle = None
                    witness_val = Fraction(0)
                    for z in homology_target:
                        v = evaluate_cochain_on_chain(prod, z)
                        if v != 0:
                            witness_cycle = z
                            witness_val = v
                            break
                    if witness_cycle is not None:
                        nonzero_witnesses.append(
                            {
                                "i": str(i),
                                "j": str(j),
                                "cycle": serialize_chain(witness_cycle),
                                "value": str(witness_val),
                            }
                        )

        # For remaining products that are exact (coboundaries in cohomology), find primitive gamma
        for col_idx, (i, j, prod) in enumerate(products):
            # Check if all evaluations on homology basis are zero (meaning it represents zero in cohomology)
            all_zero = all(eval_matrix[r][col_idx] == 0 for r in range(len(homology_target)))
            if all_zero and p + q > 0:
                gamma = find_primitive_coboundary(prod, p + q, simplices)
                if gamma is not None:
                    primitive_witnesses.append(
                        {
                            "i": str(i),
                            "j": str(j),
                            "gamma": serialize_chain(gamma),
                        }
                    )

        return {
            "rank": str(rank),
            "basis_p": [serialize_chain(c) for c in basis_p],
            "basis_q": [serialize_chain(c) for c in basis_q],
            "nonzero": nonzero_witnesses,
            "primitives": primitive_witnesses,
        }

    X_cert = analyze_complex(X_simplices)
    Y_cert = analyze_complex(Y_simplices)

    rank_X = int(X_cert["rank"])
    rank_Y = int(Y_cert["rank"])

    verdict = "DISTINGUISHED" if rank_X != rank_Y else "NOT_DISTINGUISHED_BY_THIS_PRODUCT"
    tracer.record_step(
        "D",
        "cup_product_ranks_evaluated",
        payload={
            "rank_X": rank_X,
            "rank_Y": rank_Y,
            "verdict": verdict,
        },
    )

    result = {
        "id": case_id,
        "status": "SOLVED",
        "verdict": verdict,
        "X": X_cert,
        "Y": Y_cert,
    }

    tracer.record_step("T", "terminal_pass", payload=result)
    return result, tracer
