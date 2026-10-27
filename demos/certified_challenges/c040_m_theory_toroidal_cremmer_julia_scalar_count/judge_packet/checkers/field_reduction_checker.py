"""Checker 1: Field Reduction & Hodge Dualization Checker for Challenge C040.

Direct field-theoretic reduction and Hodge dualization:
  - Counts 11D metric and 3-form components explicitly by origin.
  - Evaluates Hodge dualization condition:
      D - p - 2 == 0 for scalars (p-form dualizes to scalar when p = D - 2).
      D - p - 2 == 1 for vectors (p-form dualizes to vector when p = D - 3).
  - Verifies scalar breakdowns add up to total:
      total == metric + three_form + sum(dual_forms).
  - Independent Type IIA on T^{k-1} field reduction:
      NS-NS: metric (k-1)k//2, B-field comb(k-1, 2), dilaton 1.
      R-R: 1-form A_mu (1 vector, k-1 scalars), 3-form C_3 (comb(k-1, 3) scalars,
           comb(k-1, 2) vectors, k-1 2-forms, 1 3-form).
      Applies dualization in D dimensions.
  - Independent Type IIB on T^{k-1} field reduction:
      NS-NS: metric, B-field, dilaton.
      R-R: axion C_0 (1 scalar), 2-form C_2, self-dual 4-form C_4+ (halved components).
      Verifies that for all k >= 2, IIA and IIB give identical totals to M-theory on T^k!

All internal identifiers strictly use namespace prefix `_c1_*`.
Zero shared imports or helper code with Checker 2.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

# -----------------------------------------------------------------------------
# Internal Mathematical Primitives (_c1_*)
# -----------------------------------------------------------------------------


def _c1_comb(n: int, r: int) -> int:
    """Computes binomial coefficient C(n, r). Returns 0 if r < 0 or r > n."""
    if r < 0 or r > n or n < 0:
        return 0
    return math.comb(n, r)


def _c1_is_strict_int(val: Any) -> bool:
    """Verifies that val is an integer and strictly not a boolean."""
    return type(val) is int


# -----------------------------------------------------------------------------
# M-Theory 11D Toroidal Reduction Logic (_c1_*)
# -----------------------------------------------------------------------------


def _c1_mtheory_scalars(k: int) -> dict[str, int]:
    """Computes scalar field components from 11D supergravity on T^k by origin.

    11D metric G_MN on T^k:
      - Internal metric g_ij: k(k+1)//2 scalars.
    11D 3-form C_MNP on T^k:
      - Internal 3-form C_ijk: comb(k, 3) scalars.
    Dualized forms in D = 11 - k dimensions:
      - Dualization condition to scalar: D - p - 2 == 0 => p = D - 2.
      - In D = 5 (k = 6): p = 3 (C_mu_nu_rho, comb(6, 0) = 1) -> 1 scalar.
      - In D = 4 (k = 7): p = 2 (C_mu_nu_i, comb(7, 1) = 7) -> 7 scalars.
      - In D = 3 (k = 8): p = 1 (all vectors dualize to scalars):
          KK vectors g_mu_i: k = 8 scalars.
          3-form vectors C_mu_ij: comb(8, 2) = 28 scalars.
          Total dual vectors in D = 3: 8 + 28 = 36 scalars.
    """
    D = 11 - k
    metric_scalars = k * (k + 1) // 2
    three_form_scalars = _c1_comb(k, 3)

    dual_breakdown: dict[str, int] = {}
    if D == 5:
        dual_breakdown["dual_C_mu_nu_rho"] = _c1_comb(k, 0)  # 1
    elif D == 4:
        dual_breakdown["dual_C_mu_nu_i"] = _c1_comb(k, 1)  # 7
    elif D == 3:
        dual_breakdown["dual_kk_vectors"] = k  # 8
        dual_breakdown["dual_C_mu_ij"] = _c1_comb(k, 2)  # 28

    dual_sum = sum(dual_breakdown.values())
    total = metric_scalars + three_form_scalars + dual_sum

    res: dict[str, int] = {
        "metric": metric_scalars,
        "three_form": three_form_scalars,
        "total": total,
    }
    res.update(dual_breakdown)
    return res


def _c1_mtheory_vectors(k: int) -> dict[str, int]:
    """Computes vector field components in D = 11 - k dimensions by origin.

    11D metric cross components g_mu_i: k Kaluza-Klein vectors.
    11D 3-form components C_mu_ij: comb(k, 2) vectors.
    Dualized forms in D dimensions:
      - Dualization condition to vector: D - p - 2 == 1 => p = D - 3.
      - In D = 6 (k = 5): p = 3 (C_mu_nu_rho, comb(5, 0) = 1) -> 1 vector.
      - In D = 5 (k = 6): p = 2 (C_mu_nu_i, comb(6, 1) = 6) -> 6 vectors.
      - In D = 3 (k = 8): in D=3, all vectors dualize to scalars, so 0 propagating vectors.
    """
    D = 11 - k
    if D == 3:
        return {
            "metric_kk": 0,
            "three_form": 0,
            "dual_forms": 0,
            "total": 0,
        }

    metric_kk = k
    three_form_vecs = _c1_comb(k, 2)
    dual_vecs = 0

    if D == 6:
        dual_vecs = _c1_comb(k, 0)  # 1
    elif D == 5:
        dual_vecs = _c1_comb(k, 1)  # 6

    total = metric_kk + three_form_vecs + dual_vecs
    return {
        "metric_kk": metric_kk,
        "three_form": three_form_vecs,
        "dual_forms": dual_vecs,
        "total": total,
    }


# -----------------------------------------------------------------------------
# Type IIA Reduction on T^{k-1} (_c1_*)
# -----------------------------------------------------------------------------


def _c1_iia_scalars(k: int) -> dict[str, int]:
    """Computes scalar field components from 10D Type IIA on T^{k-1}.

    Let m = k - 1. D = 10 - m = 11 - k.
    NS-NS sector:
      - metric: m(m+1)//2 scalars
      - B-field: comb(m, 2) scalars
      - dilaton: 1 scalar
    R-R sector:
      - 1-form A_mu: m scalars (A_i)
      - 3-form C_3: comb(m, 3) scalars (C_ijk)
    Direct scalars total:
      m(m+1)//2 + comb(m, 2) + 1 + m + comb(m, 3)
      Notice: m(m+1)//2 + m + 1 = k(k+1)//2 (internal metric of 11D)
              comb(m, 2) + comb(m, 3) = comb(m+1, 3) = comb(k, 3) (internal 3-form)
    Dualized forms:
      In D = 5: 3-form C_mu_nu_rho (1) dualizes to scalar => 1 scalar.
      In D = 4: 2-forms B_mu_nu (1) + C_mu_nu_i (m) = m + 1 = k 2-forms dualize to scalars => k scalars.
      In D = 3: all vectors dualize to scalars:
        KK vecs: m
        B-field vecs: m
        A_mu: 1
        C_3 vecs: comb(m, 2)
        Total vecs: 2m + 1 + comb(m, 2) = k + comb(k, 2) = 36 scalars.
    """
    m = k - 1
    D = 11 - k
    ns_metric = m * (m + 1) // 2
    ns_b = _c1_comb(m, 2)
    dilaton = 1
    rr_a = m
    rr_c3 = _c1_comb(m, 3)

    direct_scalars = ns_metric + ns_b + dilaton + rr_a + rr_c3

    dual_scalars = 0
    if D == 5:
        dual_scalars = 1  # 3-form C_mu_nu_rho
    elif D == 4:
        dual_scalars = 1 + m  # B_mu_nu + C_mu_nu_i
    elif D == 3:
        dual_scalars = 2 * m + 1 + _c1_comb(m, 2)  # all vectors dualize

    total = direct_scalars + dual_scalars
    return {
        "ns_metric": ns_metric,
        "ns_b": ns_b,
        "dilaton": dilaton,
        "rr_a": rr_a,
        "rr_c3": rr_c3,
        "dual_scalars": dual_scalars,
        "total": total,
    }


def _c1_iia_vectors(k: int) -> dict[str, int]:
    """Computes vector field components from 10D Type IIA on T^{k-1}."""
    m = k - 1
    D = 11 - k
    if D == 3:
        return {"total": 0}

    direct_vecs = m + m + 1 + _c1_comb(m, 2)  # KK + B_mu_i + A_mu + C_mu_ij
    dual_vecs = 0
    if D == 6:
        dual_vecs = 1  # C_mu_nu_rho
    elif D == 5:
        dual_vecs = 1 + m  # B_mu_nu + C_mu_nu_i

    total = direct_vecs + dual_vecs
    return {"total": total}


# -----------------------------------------------------------------------------
# Type IIB Reduction on T^{k-1} (_c1_*)
# -----------------------------------------------------------------------------


def _c1_iib_scalars(k: int) -> dict[str, int]:
    """Computes scalar field components from 10D Type IIB on T^{k-1}.

    Let m = k - 1. D = 11 - k.
    NS-NS sector:
      - metric: m(m+1)//2
      - B-field: comb(m, 2)
      - dilaton: 1
    R-R sector:
      - axion C_0: 1
      - 2-form C_2: comb(m, 2)
      - self-dual 4-form C_4+:
        In 10D, *F_5 = F_5 halves the independent degrees of freedom.
        - For m < 4: comb(m, 4) = 0.
        - For m = 4 (D = 6): comb(4, 4) = 1 scalar C_ijkl.
        - For m = 5 (D = 5): comb(5, 4) = 5 scalars C_ijkl.
        - For m = 6 (D = 4): comb(6, 4) = 15 scalars C_ijkl.
        - For m = 7 (D = 3): comb(7, 4) = 35 scalars C_ijkl.
    Dualized forms in D dimensions:
      - In D = 4: B_mu_nu (1) + C_mu_nu (1) = 2 2-forms dualize to 2 scalars.
      - In D = 3: vectors (KK: m, B: m, C_2: m = 3m = 21) dualize to 21 scalars.
    """
    m = k - 1
    D = 11 - k
    ns_metric = m * (m + 1) // 2
    ns_b = _c1_comb(m, 2)
    dilaton = 1
    rr_c0 = 1
    rr_c2 = _c1_comb(m, 2)
    rr_c4 = _c1_comb(m, 4)

    direct_scalars = ns_metric + ns_b + dilaton + rr_c0 + rr_c2 + rr_c4

    dual_scalars = 0
    if D == 4:
        dual_scalars = 2  # B_mu_nu and C_mu_nu
    elif D == 3:
        dual_scalars = 3 * m  # KK + B + C2 vectors

    total = direct_scalars + dual_scalars
    return {
        "ns_metric": ns_metric,
        "ns_b": ns_b,
        "dilaton": dilaton,
        "rr_c0": rr_c0,
        "rr_c2": rr_c2,
        "rr_c4": rr_c4,
        "dual_scalars": dual_scalars,
        "total": total,
    }


def _c1_iib_vectors(k: int) -> dict[str, int]:
    """Computes vector field components from 10D Type IIB on T^{k-1}."""
    m = k - 1
    D = 11 - k
    if D == 3:
        return {"total": 0}

    # Direct vectors: KK (m) + B_mu_i (m) + C_mu_i (m) = 3m
    base_vecs = 3 * m
    c4_vecs = 0
    dual_vecs = 0

    if D == 6:
        # C_mu_ijk has comb(4, 3) = 4
        c4_vecs = _c1_comb(m, 3)
    elif D == 5:
        # C_mu_ijk has comb(5, 3) = 10, plus dual 2-forms B_mu_nu (1) + C_mu_nu (1) = 2
        c4_vecs = _c1_comb(m, 3)
        dual_vecs = 2
    elif D == 4:
        # In D=4, C_mu_ijk has comb(6, 3) = 20, self-duality halves to 10
        c4_vecs = _c1_comb(m, 3) // 2
    elif D >= 7:
        if m >= 3:
            c4_vecs = _c1_comb(m, 3)

    total = base_vecs + c4_vecs + dual_vecs
    return {"total": total}


# -----------------------------------------------------------------------------
# Anti-Bypass Validation Functions (_c1_*)
# -----------------------------------------------------------------------------


def _c1_verify_refusal_warranted(
    case: Mapping[str, Any], answer: Mapping[str, Any]
) -> tuple[bool, str]:
    """Validates that a refusal is strictly defect-grounded.

    Refusal is warranted ONLY when k is outside [1, 8].
    Must emit status == 'UNKNOWN' and refusal_code == 'K_OUT_OF_BOUNDS'.
    """
    k = case.get("k")
    if _c1_is_strict_int(k) and 1 <= k <= 8:
        return False, f"Anti-bypass: refusal unwarranted for valid k={k}"

    refusal_code = answer.get("refusal_code")
    if refusal_code != "K_OUT_OF_BOUNDS":
        return (
            False,
            f"Anti-bypass: invalid refusal_code '{refusal_code}', expected 'K_OUT_OF_BOUNDS'",
        )

    allowed_keys = {"id", "case_id", "status", "refusal_code"}
    extra_keys = set(answer.keys()) - allowed_keys
    if extra_keys:
        return False, f"Anti-bypass: phantom keys in refusal answer: {sorted(extra_keys)}"

    return True, "C1_REFUSAL_WARRANTED"


def _c1_check_scalars_breakdown(k: int, scalars_dict: Mapping[str, Any]) -> tuple[bool, str]:
    """Validates that the scalar breakdown matches field reduction by origin and sums correctly."""
    allowed_scalar_keys = {
        "metric",
        "three_form",
        "total",
        "dual_C_mu_nu_rho",
        "dual_C_mu_nu_i",
        "dual_kk_vectors",
        "dual_C_mu_ij",
        "dual_forms",
    }
    extra_keys = set(scalars_dict.keys()) - allowed_scalar_keys
    if extra_keys:
        return False, f"Anti-bypass: phantom keys in scalars breakdown: {sorted(extra_keys)}"

    for key, val in scalars_dict.items():
        if not _c1_is_strict_int(val):
            return False, f"Anti-bypass: scalar breakdown key '{key}' has non-integer value {val!r}"

    exp = _c1_mtheory_scalars(k)
    D = 11 - k

    # Check metric components
    if scalars_dict.get("metric") != exp["metric"]:
        return (
            False,
            f"Scalar metric count mismatch: got {scalars_dict.get('metric')}, expected {exp['metric']}",
        )

    # Check 3-form components
    if scalars_dict.get("three_form") != exp["three_form"]:
        return (
            False,
            f"Scalar three_form count mismatch: got {scalars_dict.get('three_form')}, expected {exp['three_form']}",
        )

    # Trap Layer 1: Metric-plus-3-form only trap
    undualized_sum = exp["metric"] + exp["three_form"]
    reported_total = scalars_dict.get("total")
    if reported_total == undualized_sum and exp["total"] > undualized_sum:
        return False, (
            f"Anti-bypass: metric-plus-3-form only trap triggered: reported {reported_total}, "
            f"omitted dualized scalars (expected {exp['total']} in D={D})"
        )

    # Trap Layer 2: False scalar dualization in D=6
    if D == 6:
        # In D=6, 3-form dualizes to vector, NOT scalar.
        if "dual_C_mu_nu_rho" in scalars_dict and scalars_dict["dual_C_mu_nu_rho"] > 0:
            return (
                False,
                "Anti-bypass: false scalar dualization in D=6 (3-form dualizes to vector, not scalar)",
            )
        if reported_total != 25:
            return (
                False,
                f"Total scalar count for k=5 (D=6) must be exactly 25, got {reported_total}",
            )

    # Dimension-specific dualized form checks
    if D == 5:
        if scalars_dict.get("dual_C_mu_nu_rho") != 1:
            return (
                False,
                f"D=5 requires dual_C_mu_nu_rho == 1, got {scalars_dict.get('dual_C_mu_nu_rho')}",
            )
    elif D == 4:
        if scalars_dict.get("dual_C_mu_nu_i") != 7:
            return (
                False,
                f"D=4 requires dual_C_mu_nu_i == 7, got {scalars_dict.get('dual_C_mu_nu_i')}",
            )
    elif D == 3:
        if scalars_dict.get("dual_kk_vectors") != 8:
            return (
                False,
                f"D=3 requires dual_kk_vectors == 8, got {scalars_dict.get('dual_kk_vectors')}",
            )
        if scalars_dict.get("dual_C_mu_ij") != 28:
            return False, f"D=3 requires dual_C_mu_ij == 28, got {scalars_dict.get('dual_C_mu_ij')}"

    # Sum consistency
    component_sum = sum(v for k_name, v in scalars_dict.items() if k_name != "total")
    if reported_total != component_sum:
        return (
            False,
            f"Scalar components do not sum to total: sum={component_sum} vs total={reported_total}",
        )

    if reported_total != exp["total"]:
        return False, f"Scalar total mismatch: got {reported_total}, expected {exp['total']}"

    return True, "SCALARS_OK"


def _c1_check_vectors_breakdown(k: int, vectors_dict: Mapping[str, Any]) -> tuple[bool, str]:
    """Validates vector breakdown in D dimensions."""
    allowed_vector_keys = {"metric_kk", "three_form", "dual_forms", "total"}
    extra_keys = set(vectors_dict.keys()) - allowed_vector_keys
    if extra_keys:
        return False, f"Anti-bypass: phantom keys in vectors breakdown: {sorted(extra_keys)}"

    for key, val in vectors_dict.items():
        if not _c1_is_strict_int(val):
            return False, f"Anti-bypass: vector breakdown key '{key}' has non-integer value {val!r}"

    exp = _c1_mtheory_vectors(k)
    reported_total = vectors_dict.get("total")
    if reported_total != exp["total"]:
        return False, f"Vector total mismatch: got {reported_total}, expected {exp['total']}"

    if "metric_kk" in vectors_dict and vectors_dict["metric_kk"] != exp["metric_kk"]:
        return (
            False,
            f"Vector metric_kk mismatch: got {vectors_dict['metric_kk']}, expected {exp['metric_kk']}",
        )

    if "three_form" in vectors_dict and vectors_dict["three_form"] != exp["three_form"]:
        return (
            False,
            f"Vector three_form mismatch: got {vectors_dict['three_form']}, expected {exp['three_form']}",
        )

    return True, "VECTORS_OK"


# -----------------------------------------------------------------------------
# Primary Verification Entrypoint (_c1_*)
# -----------------------------------------------------------------------------


def verify_field_reduction_certificate(
    case: Mapping[str, Any],
    answer: Mapping[str, Any],
) -> tuple[bool, str]:
    """Checker 1 entrypoint: verifies answer against field reduction and Hodge dualization."""
    if not isinstance(case, Mapping) or not isinstance(answer, Mapping):
        return False, "Malformed input: case and answer must be mappings"

    # Status check
    status = answer.get("status")
    if status == "UNKNOWN":
        return _c1_verify_refusal_warranted(case, answer)

    if status != "SOLVED":
        return False, f"Invalid answer status '{status}', must be 'SOLVED' or 'UNKNOWN'"

    k = case.get("k")
    if not _c1_is_strict_int(k) or k < 1 or k > 8:
        return False, f"Case k={k!r} out of bounds for SOLVED status"

    ans_k = answer.get("k")
    if not _c1_is_strict_int(ans_k) or ans_k != k:
        return False, f"Answer k={ans_k!r} must be strict int matching case k={k}"

    ans_D = answer.get("D")
    exp_D = 11 - k
    if ans_D is not None and (not _c1_is_strict_int(ans_D) or ans_D != exp_D):
        return False, f"Answer D={ans_D!r} must be strict int matching 11 - k = {exp_D}"

    query = case.get("query")
    theory = case.get("theory", "M")

    # Closed schema validation
    allowed_root_keys = {"id", "case_id", "status", "k", "D", "query", "theory", query}
    extra_keys = set(answer.keys()) - allowed_root_keys
    if extra_keys:
        return False, f"Anti-bypass: phantom keys in answer: {sorted(extra_keys)}"

    # Theory cross-checks (Controls)
    if theory == "IIA":
        exp_iia = _c1_iia_scalars(k)
        exp_m = _c1_mtheory_scalars(k)
        if exp_iia["total"] != exp_m["total"]:
            return (
                False,
                f"Internal error: IIA total {exp_iia['total']} != M total {exp_m['total']}",
            )
    elif theory == "IIB":
        exp_iib = _c1_iib_scalars(k)
        exp_m = _c1_mtheory_scalars(k)
        if exp_iib["total"] != exp_m["total"]:
            return (
                False,
                f"Internal error: IIB total {exp_iib['total']} != M total {exp_m['total']}",
            )

    # Handle Queries
    if query == "scalars":
        scalars_data = answer.get("scalars")
        if not isinstance(scalars_data, Mapping):
            return False, "Query 'scalars' missing valid 'scalars' mapping in answer"
        return _c1_check_scalars_breakdown(k, scalars_data)

    elif query == "coset":
        coset_data = answer.get("coset")
        if not isinstance(coset_data, Mapping):
            return False, "Query 'coset' missing valid 'coset' mapping in answer"
        allowed_coset_keys = {"G", "K", "dimG", "dimK", "difference"}
        extra = set(coset_data.keys()) - allowed_coset_keys
        if extra:
            return False, f"Anti-bypass: phantom keys in coset mapping: {sorted(extra)}"
        dimG = coset_data.get("dimG")
        dimK = coset_data.get("dimK")
        diff = coset_data.get("difference")
        if not (_c1_is_strict_int(dimG) and _c1_is_strict_int(dimK) and _c1_is_strict_int(diff)):
            return False, "Anti-bypass: coset dimensions must be strict integers"
        if dimG - dimK != diff:
            return False, f"Coset difference inconsistent: {dimG} - {dimK} != {diff}"
        exp_m = _c1_mtheory_scalars(k)
        if diff != exp_m["total"]:
            return (
                False,
                f"Coset difference {diff} does not equal field-theoretic scalar count {exp_m['total']}",
            )
        return True, "C1_COSET_OK"

    elif query == "branching":
        branching_data = answer.get("branching")
        if not isinstance(branching_data, list):
            return False, "Query 'branching' missing valid 'branching' list in answer"
        total_dim = 0
        p_dim = None
        adj_count = 0
        p_count = 0
        for item in branching_data:
            if not (isinstance(item, (list, tuple)) and len(item) == 2):
                return False, f"Invalid branching element format: {item!r}"
            label, d = item
            if not isinstance(label, str) or not _c1_is_strict_int(d):
                return False, "Branching item must be [str, int]"
            total_dim += d
            if "adjoint" in label.lower():
                adj_count += 1
            else:
                p_count += 1
                p_dim = d
        if adj_count != 1 or p_count != 1:
            return (
                False,
                f"Anti-bypass: branching must contain exactly 1 adjoint and 1 p-rep, got {adj_count} and {p_count}",
            )
        exp_m = _c1_mtheory_scalars(k)
        if p_dim is not None and p_dim != exp_m["total"]:
            return (
                False,
                f"Branching p-dimension {p_dim} != field-theoretic scalar count {exp_m['total']}",
            )
        return True, "C1_BRANCHING_OK"

    elif query == "vectors":
        vectors_data = answer.get("vectors")
        if not isinstance(vectors_data, Mapping):
            return False, "Query 'vectors' missing valid 'vectors' mapping in answer"
        return _c1_check_vectors_breakdown(k, vectors_data)

    else:
        return False, f"Unknown query type: {query}"
