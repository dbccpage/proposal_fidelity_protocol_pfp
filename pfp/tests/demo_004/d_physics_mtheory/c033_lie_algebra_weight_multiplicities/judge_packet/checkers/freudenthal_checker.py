"""Checker 1 (Exact Freudenthal & Weyl Orbit Certifier) for C033.

Verifies:
  - Highest weight correctness (dominant chamber reflection)
  - Exact total dimension via Weyl dimension formula
  - Exact dominant weight multiplicities via Freudenthal recursion
  - Global orbit-sum check: sum_{mu dominant} m(mu) * |W * mu| == dimension
  - Tensor product decomposition dimension check: sum_{nu} mult(nu) * dim(nu) == dim(left) * dim(right)
  - Fail-closed refusal and out-of-scope validation

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from omega_engine_pfp.tests.demo_004.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.reference_solver.lie_algebra import (
    freudenthal_multiplicities,
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


def verify_freudenthal_certificate(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> tuple[bool, str]:
    """Checker 1: Freudenthal recursion + Weyl dimension + Weyl orbit sum verification."""
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

        # Check dominant reflection
        raw_w = case.get("weight", [])
        expected_dom = list(reflect_to_dominant(algebra, tuple(raw_w)))
        if hw != expected_dom:
            return False, f"FAIL: highest_weight {hw} != expected dominant {expected_dom}"

        # Check Weyl dimension formula
        expected_dim = weyl_dimension(algebra, expected_dom)
        if dim != expected_dim:
            return False, f"FAIL: dimension {dim} != expected Weyl dimension {expected_dim}"

        # Check Freudenthal dominant multiplicities
        expected_mults = freudenthal_multiplicities(
            algebra, expected_dom, max_dimension=MAX_DIMENSION
        )

        # Check completeness and exactness of dominant multiplicities
        result_mult_dict = {}
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
            if w_tuple in result_mult_dict:
                return False, f"FAIL: duplicate dominant weight in result: {w_labels}"
            result_mult_dict[w_tuple] = mult

        if result_mult_dict != expected_mults:
            return (
                False,
                f"FAIL: dominant multiplicities mismatch: got {result_mult_dict}, expected {expected_mults}",
            )

        # Global orbit-sum dimension check
        orbit_dim_sum = sum(
            mult * weyl_orbit_size(algebra, w) for w, mult in result_mult_dict.items()
        )
        if orbit_dim_sum != dim:
            return False, f"FAIL: orbit dimension sum {orbit_dim_sum} != declared dimension {dim}"

        return True, "VALID_FREUDENTHAL_CERTIFICATE"

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

        expected_decomp = tensor_product_decomposition(
            algebra, dom_l, dom_r, max_product_dimension=MAX_DIMENSION
        )

        result_decomp_dict = {}
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
                return False, f"FAIL: duplicate component in decomposition: {w_labels}"
            result_decomp_dict[w_tuple] = mult

        if result_decomp_dict != expected_decomp:
            return (
                False,
                f"FAIL: decomposition mismatch: got {result_decomp_dict}, expected {expected_decomp}",
            )

        # Total dimension conservation check
        total_decomp_dim = sum(
            mult * weyl_dimension(algebra, w) for w, mult in result_decomp_dict.items()
        )
        expected_prod_dim = weyl_dimension(algebra, dom_l) * weyl_dimension(algebra, dom_r)
        if total_decomp_dim != expected_prod_dim:
            return (
                False,
                f"FAIL: decomposition total dimension {total_decomp_dim} != product dimension {expected_prod_dim}",
            )

        return True, "VALID_FREUDENTHAL_CERTIFICATE"

    return False, f"FAIL: invalid query {query!r}"
