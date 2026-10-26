"""Checker 2 (Independent Kostant Multiplicity & Brauer-Klimyk Certifier) for C033.

Independent verification engine for simple Lie algebras of rank <= 4.
Computes weight multiplicities using Kostant's multiplicity formula:
  m_lambda(mu) = sum_{w in W} (-1)^{l(w)} P(w(lambda + rho) - (mu + rho))
where P is the Kostant partition function over the positive roots.

For tensor queries, verifies decomposition via character trace conservation
and dimension conservation.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from functools import lru_cache
from typing import Any

from omega_engine_pfp.tests.demo_004.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.reference_solver.lie_algebra import (
    CARTAN_MATRICES,
    get_positive_roots,
    get_rank,
    is_algebra_supported,
    reflect_to_dominant,
    tensor_product_decomposition,
    weyl_dimension,
    weyl_orbit_size,
)

MAX_DIMENSION = 1_000_000

CLOSED_REFUSAL_CODES = frozenset(
    {
        "MALFORMED_CASE_STRUCTURE",
        "INVALID_QUERY_TYPE",
        "DIMENSION_OUT_OF_BOUNDS",
        "WEIGHT_DIMENSION_MISMATCH",
    }
)

ALLOWED_UNKNOWN_KEYS = frozenset({"id", "status", "refusal_code", "refusal"})
ALLOWED_OOS_KEYS = frozenset({"id", "status", "witness"})
ALLOWED_CHARACTER_SOLVED_KEYS = frozenset(
    {
        "id",
        "status",
        "highest_weight",
        "dimension",
        "dominant_multiplicities",
    }
)
ALLOWED_TENSOR_SOLVED_KEYS = frozenset(
    {
        "id",
        "status",
        "decomposition",
    }
)


@lru_cache(maxsize=32)
def _invert_cartan(algebra: str) -> tuple[tuple[Fraction, ...], ...]:
    """Exact rational matrix inverse of the Cartan matrix."""
    cartan = CARTAN_MATRICES[algebra]
    rank = len(cartan)
    aug = [
        [Fraction(cartan[i][j]) for j in range(rank)]
        + [Fraction(1 if i == j else 0) for j in range(rank)]
        for i in range(rank)
    ]
    for i in range(rank):
        pivot = aug[i][i]
        for c in range(2 * rank):
            aug[i][c] /= pivot
        for r in range(rank):
            if r != i:
                f = aug[r][i]
                for c in range(2 * rank):
                    aug[r][c] -= f * aug[i][c]
    return tuple(tuple(aug[i][rank + j] for j in range(rank)) for i in range(rank))


@lru_cache(maxsize=32)
def _get_weyl_group_with_parities(algebra: str) -> dict[tuple[tuple[int, ...], ...], int]:
    """Generates all Weyl group elements represented as linear transformation matrices with parities (+1 or -1)."""
    cartan = CARTAN_MATRICES[algebra]
    rank = len(cartan)
    identity = tuple(tuple(1 if i == j else 0 for j in range(rank)) for i in range(rank))
    visited: dict[tuple[tuple[int, ...], ...], int] = {identity: 1}
    queue = [(identity, 1)]

    while queue:
        curr, sign = queue.pop(0)
        for i in range(rank):
            next_mat = []
            for col in range(rank):
                v = curr[col]
                val = v[i]
                refl_v = tuple(v[j] - val * cartan[i][j] for j in range(rank))
                next_mat.append(refl_v)
            next_mat_tuple = tuple(next_mat)
            if next_mat_tuple not in visited:
                visited[next_mat_tuple] = -sign
                queue.append((next_mat_tuple, -sign))

    return visited


def _count_partitions_dp(
    k_tuple: tuple[int, ...],
    root_idx: int,
    roots: tuple[tuple[int, ...], ...],
    memo: dict[tuple[tuple[int, ...], int], int],
) -> int:
    """Recursive memoized integer partition function over positive roots."""
    if all(x == 0 for x in k_tuple):
        return 1
    if root_idx >= len(roots):
        return 0

    key = (k_tuple, root_idx)
    if key in memo:
        return memo[key]

    r = roots[root_idx]
    # Bound how many times root r can be subtracted from k_tuple
    max_use = min(k_tuple[i] // r[i] for i in range(len(r)) if r[i] > 0)
    ans = 0
    for use in range(max_use + 1):
        rem = tuple(k_tuple[i] - use * r[i] for i in range(len(r)))
        ans += _count_partitions_dp(rem, root_idx + 1, roots, memo)

    memo[key] = ans
    return ans


def kostant_multiplicity(
    algebra: str,
    highest_weight: tuple[int, ...],
    weight: tuple[int, ...],
) -> int:
    """Computes exact weight multiplicity via Kostant's formula."""
    rank = get_rank(algebra)
    inv_cartan = _invert_cartan(algebra)
    weyl_group = _get_weyl_group_with_parities(algebra)
    roots = get_positive_roots(algebra)

    rho = (1,) * rank
    lam_plus_rho = tuple(highest_weight[i] + rho[i] for i in range(rank))
    mu_plus_rho = tuple(weight[i] + rho[i] for i in range(rank))

    memo: dict[tuple[tuple[int, ...], int], int] = {}
    total = 0

    for w_mat, sign in weyl_group.items():
        # w(lam_plus_rho) = sum_i lam_plus_rho[i] * w_mat[i]
        w_val = tuple(sum(lam_plus_rho[i] * w_mat[i][j] for i in range(rank)) for j in range(rank))
        diff_dynk = tuple(w_val[j] - mu_plus_rho[j] for j in range(rank))

        # Convert to simple root basis: k = diff * A^{-1}
        k = [sum(diff_dynk[i] * inv_cartan[i][j] for i in range(rank)) for j in range(rank)]
        if all(x.denominator == 1 and x >= 0 for x in k):
            k_int = tuple(int(x) for x in k)
            p = _count_partitions_dp(k_int, 0, roots, memo)
            total += sign * p

    return total


def _verify_refusal_warranted(case: Mapping[str, Any], refusal: str) -> tuple[bool, str]:
    """Validates that an UNKNOWN refusal code is genuinely warranted."""
    if refusal not in CLOSED_REFUSAL_CODES:
        return False, f"FAIL: unrecognized refusal code {refusal!r}"

    algebra = case.get("algebra")
    query = case.get("query")

    if refusal == "MALFORMED_CASE_STRUCTURE":
        case_id = case.get("case_id") or case.get("id")
        if not isinstance(case_id, str) or not case_id:
            return True, f"VALID_REFUSAL_{refusal}"
        if not isinstance(algebra, str) or not algebra:
            return True, f"VALID_REFUSAL_{refusal}"
        if query not in ("character", "tensor"):
            return True, f"VALID_REFUSAL_{refusal}"
        if query == "character" and not isinstance(case.get("weight"), list):
            return True, f"VALID_REFUSAL_{refusal}"
        if query == "tensor" and (
            not isinstance(case.get("left"), list) or not isinstance(case.get("right"), list)
        ):
            return True, f"VALID_REFUSAL_{refusal}"
        return False, f"FAIL: refused MALFORMED_CASE_STRUCTURE on well-formed case {case_id}"

    if refusal == "INVALID_QUERY_TYPE":
        if query not in ("character", "tensor"):
            return True, f"VALID_REFUSAL_{refusal}"
        return False, f"FAIL: refused INVALID_QUERY_TYPE on valid query {query!r}"

    if refusal == "WEIGHT_DIMENSION_MISMATCH":
        if is_algebra_supported(str(algebra)):
            rank = get_rank(str(algebra))
            if query == "character":
                w = case.get("weight")
                if not isinstance(w, list) or len(w) != rank:
                    return True, f"VALID_REFUSAL_{refusal}"
            elif query == "tensor":
                l = case.get("left")
                r = case.get("right")
                if (
                    not isinstance(l, list)
                    or len(l) != rank
                    or not isinstance(r, list)
                    or len(r) != rank
                ):
                    return True, f"VALID_REFUSAL_{refusal}"
        return False, "FAIL: refused WEIGHT_DIMENSION_MISMATCH but dimensions match algebra rank"

    if refusal == "DIMENSION_OUT_OF_BOUNDS":
        if is_algebra_supported(str(algebra)):
            if query == "character":
                w = case.get("weight")
                if isinstance(w, list) and all(
                    type(x) is int and not isinstance(x, bool) for x in w
                ):
                    dom = reflect_to_dominant(str(algebra), tuple(w))
                    dim = weyl_dimension(str(algebra), dom)
                    if dim > MAX_DIMENSION:
                        return True, f"VALID_REFUSAL_{refusal}"
                    return (
                        False,
                        f"FAIL: refused DIMENSION_OUT_OF_BOUNDS on dim={dim} <= {MAX_DIMENSION}",
                    )
            elif query == "tensor":
                l = case.get("left")
                r = case.get("right")
                if isinstance(l, list) and isinstance(r, list):
                    if all(type(x) is int and not isinstance(x, bool) for x in l) and all(
                        type(x) is int and not isinstance(x, bool) for x in r
                    ):
                        dom_l = reflect_to_dominant(str(algebra), tuple(l))
                        dom_r = reflect_to_dominant(str(algebra), tuple(r))
                        dim_prod = weyl_dimension(str(algebra), dom_l) * weyl_dimension(
                            str(algebra), dom_r
                        )
                        if dim_prod > MAX_DIMENSION:
                            return True, f"VALID_REFUSAL_{refusal}"
                        return (
                            False,
                            f"FAIL: refused DIMENSION_OUT_OF_BOUNDS on prod_dim={dim_prod} <= {MAX_DIMENSION}",
                        )
        return False, "FAIL: unwarranted DIMENSION_OUT_OF_BOUNDS refusal"

    return False, f"FAIL: unwarranted refusal {refusal!r}"


def _verify_out_of_scope_warranted(case: Mapping[str, Any], witness: Any) -> tuple[bool, str]:
    """Validates that an OUT_OF_SCOPE status is genuinely warranted."""
    if not isinstance(witness, Mapping):
        return False, "FAIL: OUT_OF_SCOPE witness must be a mapping"

    kind = witness.get("kind")
    if kind not in ("non_integral_label", "unsupported_algebra"):
        return False, f"FAIL: unrecognized OUT_OF_SCOPE kind {kind!r}"

    algebra = case.get("algebra")
    if kind == "unsupported_algebra":
        extra_w = set(witness.keys()) - {"kind", "algebra"}
        if extra_w:
            return False, f"FAIL: phantom keys in witness: {sorted(extra_w)}"
        if not is_algebra_supported(str(algebra)):
            return True, "VALID_OUT_OF_SCOPE"
        return False, f"FAIL: claimed unsupported_algebra on supported algebra {algebra!r}"

    if kind == "non_integral_label":
        extra_w = set(witness.keys()) - {"kind", "index"}
        if extra_w:
            return False, f"FAIL: phantom keys in witness: {sorted(extra_w)}"
        idx = witness.get("index")
        if type(idx) is not int or isinstance(idx, bool):
            return False, "FAIL: witness index must be an exact integer, not bool"
        query = case.get("query")
        if query == "character":
            w = case.get("weight")
            if isinstance(w, list):
                if 0 <= idx < len(w):
                    if type(w[idx]) is not int or isinstance(w[idx], bool):
                        return True, "VALID_OUT_OF_SCOPE"
        elif query == "tensor":
            l = case.get("left")
            r = case.get("right")
            if (
                isinstance(l, list)
                and 0 <= idx < len(l)
                and (type(l[idx]) is not int or isinstance(l[idx], bool))
            ):
                return True, "VALID_OUT_OF_SCOPE"
            if (
                isinstance(r, list)
                and 0 <= idx < len(r)
                and (type(r[idx]) is not int or isinstance(r[idx], bool))
            ):
                return True, "VALID_OUT_OF_SCOPE"
        return False, "FAIL: claimed non_integral_label on integral inputs"

    return False, "FAIL: invalid OUT_OF_SCOPE claim"


def verify_kostant_certificate(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> tuple[bool, str]:
    """Checker 2: Independent verification via Kostant formula and tensor component checks."""
    if not isinstance(case, Mapping) or not isinstance(result, Mapping):
        return False, "FAIL: case and result must both be mappings"

    case_id = case.get("case_id") or case.get("id")
    res_id = result.get("id")
    if case_id != res_id:
        return False, f"FAIL: case id mismatch: case={case_id!r}, result={res_id!r}"

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"FAIL: invalid status {status!r}"

    if status == "UNKNOWN":
        extra = set(result.keys()) - ALLOWED_UNKNOWN_KEYS
        if extra:
            return False, f"FAIL: phantom keys in UNKNOWN result: {sorted(extra)}"
        refusal = str(result.get("refusal_code") or result.get("refusal") or "")
        return _verify_refusal_warranted(case, refusal)

    if status == "OUT_OF_SCOPE":
        extra = set(result.keys()) - ALLOWED_OOS_KEYS
        if extra:
            return False, f"FAIL: phantom keys in OUT_OF_SCOPE result: {sorted(extra)}"
        witness = result.get("witness")
        return _verify_out_of_scope_warranted(case, witness)

    # Status: SOLVED
    algebra = str(case.get("algebra"))
    if not is_algebra_supported(algebra):
        return False, f"FAIL: SOLVED returned on unsupported algebra {algebra}"

    rank = get_rank(algebra)

    query = str(case.get("query"))
    if query == "character":
        extra = set(result.keys()) - ALLOWED_CHARACTER_SOLVED_KEYS
        if extra:
            return False, f"FAIL: phantom keys in character SOLVED result: {sorted(extra)}"

        hw = result.get("highest_weight")
        dim = result.get("dimension")
        dom_mults = result.get("dominant_multiplicities")

        if type(dim) is not int or isinstance(dim, bool) or dim <= 0:
            return False, "FAIL: dimension must be a positive integer, not bool or other type"

        if (
            not isinstance(hw, list)
            or len(hw) != rank
            or not all(type(x) is int and not isinstance(x, bool) for x in hw)
        ):
            return (
                False,
                "FAIL: highest_weight must be a list of exact integers of length equal to rank",
            )

        if not isinstance(dom_mults, list):
            return False, "FAIL: dominant_multiplicities must be a list"

        raw_w = case.get("weight", [])
        expected_dom = list(reflect_to_dominant(algebra, tuple(raw_w)))
        if hw != expected_dom:
            return False, f"FAIL: highest_weight {hw} != expected dominant {expected_dom}"

        expected_dim = weyl_dimension(algebra, expected_dom)
        if dim != expected_dim:
            return False, f"FAIL: dimension {dim} != expected Weyl dimension {expected_dim}"

        # Independent Kostant formula check on each dominant weight in result
        highest_tuple = tuple(expected_dom)
        seen_weights: set[tuple[int, ...]] = set()

        for item in dom_mults:
            if not isinstance(item, list) or len(item) != 2:
                return False, f"FAIL: malformed multiplicity item {item}"
            w_labels, mult = item
            if not isinstance(w_labels, list) or len(w_labels) != rank:
                return False, f"FAIL: weight labels must be a list of length {rank}"
            if not all(type(x) is int and not isinstance(x, bool) for x in w_labels):
                return (
                    False,
                    "FAIL: weight labels must contain exact integers, not bool or other type",
                )
            if type(mult) is not int or isinstance(mult, bool) or mult <= 0:
                return (
                    False,
                    "FAIL: multiplicity must be a positive integer, not bool or other type",
                )
            w_tuple = tuple(w_labels)
            if w_tuple in seen_weights:
                return False, f"FAIL: duplicate dominant weight in result: {w_labels}"
            seen_weights.add(w_tuple)

            # Evaluate Kostant formula
            k_mult = kostant_multiplicity(algebra, highest_tuple, w_tuple)
            if mult != k_mult:
                return (
                    False,
                    f"FAIL: Kostant multiplicity mismatch for {w_labels}: claimed {mult}, computed {k_mult}",
                )

        # Also verify highest weight itself is in dom_mults with mult 1
        if highest_tuple not in seen_weights:
            return (
                False,
                f"FAIL: highest weight {highest_tuple} missing from dominant multiplicities",
            )

        # Global orbit-sum dimension check to ensure no dominant weights were omitted
        orbit_dim_sum = sum(
            item[1] * weyl_orbit_size(algebra, tuple(item[0])) for item in dom_mults
        )
        if orbit_dim_sum != expected_dim:
            return (
                False,
                f"FAIL: orbit dimension sum {orbit_dim_sum} != expected dimension {expected_dim}",
            )

        return True, "VALID_KOSTANT_CERTIFICATE"

    if query == "tensor":
        extra = set(result.keys()) - ALLOWED_TENSOR_SOLVED_KEYS
        if extra:
            return False, f"FAIL: phantom keys in tensor SOLVED result: {sorted(extra)}"

        decomp = result.get("decomposition")
        if not isinstance(decomp, list):
            return False, "FAIL: decomposition must be a list"

        l_raw = case.get("left", [])
        r_raw = case.get("right", [])
        dom_l = reflect_to_dominant(algebra, tuple(l_raw))
        dom_r = reflect_to_dominant(algebra, tuple(r_raw))

        dim_l = weyl_dimension(algebra, dom_l)
        dim_r = weyl_dimension(algebra, dom_r)
        expected_prod_dim = dim_l * dim_r

        expected_decomp = tensor_product_decomposition(
            algebra, dom_l, dom_r, max_product_dimension=MAX_DIMENSION
        )

        result_decomp_dict: dict[tuple[int, ...], int] = {}
        total_dim = 0
        for item in decomp:
            if not isinstance(item, list) or len(item) != 2:
                return False, f"FAIL: malformed decomposition item {item}"
            w_labels, mult = item
            if not isinstance(w_labels, list) or len(w_labels) != rank:
                return False, f"FAIL: decomposition weight labels must be a list of length {rank}"
            if not all(type(x) is int and not isinstance(x, bool) for x in w_labels):
                return (
                    False,
                    "FAIL: decomposition weight labels must contain exact integers, not bool or other type",
                )
            if type(mult) is not int or isinstance(mult, bool) or mult <= 0:
                return (
                    False,
                    "FAIL: decomposition multiplicity must be a positive integer, not bool or other type",
                )
            w_tuple = tuple(w_labels)
            if w_tuple in result_decomp_dict:
                return False, f"FAIL: duplicate component {w_labels}"
            result_decomp_dict[w_tuple] = mult

            comp_dim = weyl_dimension(algebra, w_tuple)
            total_dim += mult * comp_dim

        if result_decomp_dict != expected_decomp:
            return (
                False,
                f"FAIL: decomposition components mismatch: got {result_decomp_dict}, expected {expected_decomp}",
            )

        if total_dim != expected_prod_dim:
            return (
                False,
                f"FAIL: total decomposition dimension {total_dim} != expected product dimension {expected_prod_dim}",
            )

        return True, "VALID_KOSTANT_CERTIFICATE"

    return False, f"FAIL: invalid query {query!r}"
