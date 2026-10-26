"""Checker 2 (Independent Weight-System & Sylvester Minor Certifier) for C032.

Independent verification engine for 6D supergravity anomaly cancellation.
Derives the trace coefficients A, B, C, the representation dimensions and the
normalization lambda from explicit weight systems (traces of Cartan-diagonal
representation matrices, see weight_systems.py) instead of the reference
solver's table, and evaluates Gram matrix inertia by symmetric pivoting.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any

from omega_engine_pfp.tests.demo_004.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.judge_packet.checkers.weight_systems import (
    SUPPORTED_GROUPS,
    WeightDerivationError,
    group_dim,
    has_independent_quartic,
    is_pseudoreal,
    normalization_lambda,
    rep_dim,
    trace_coefficients,
)

# Checker 2 takes group data only from weight_systems (derived from weights),
# never from the reference solver's coefficient table.


def is_group_supported(group: str) -> bool:
    return group in SUPPORTED_GROUPS


def get_group_dim(group: str) -> int:
    return group_dim(group)


def get_rep_dim(group: str, rep: str) -> int:
    return rep_dim(group, rep)


def get_group_lambda(group: str) -> int:
    return normalization_lambda(group)


def is_rep_pseudoreal(group: str, rep: str) -> bool:
    try:
        return is_pseudoreal(group, rep)
    except WeightDerivationError:
        return False


CLOSED_REFUSAL_CODES = frozenset(
    {
        "MALFORMED_CASE_STRUCTURE",
        "GROUP_NOT_SUPPORTED",
        "REPRESENTATION_NOT_SUPPORTED",
        "T_OUT_OF_BOUNDS",
        "NEUTRAL_HYPERS_OUT_OF_BOUNDS",
        "MULTIPLICITY_OUT_OF_BOUNDS",
        "NON_INTEGER_HYPER_COUNT",
    }
)

ALLOWED_UNKNOWN_KEYS = frozenset({"id", "status", "refusal_code", "refusal"})
ALLOWED_OOS_KEYS = frozenset({"id", "status", "witness"})
ALLOWED_SOLVED_KEYS = frozenset(
    {
        "id",
        "status",
        "H",
        "V",
        "T",
        "gravitational",
        "coefficients",
        "quartic",
        "gram_inertia",
        "verdict",
        "first_failure",
    }
)

ALLOWED_COEFFICIENT_KEYS = frozenset({"a.a", "a.b", "b.b"})
ALLOWED_GRAVITATIONAL_KEYS = frozenset({"lhs", "ok"})
ALLOWED_INERTIA_KEYS = frozenset({"positive", "negative", "zero"})
ALLOWED_WITNESS_KEYS = frozenset({"kind", "factor", "hyper_index"})
ALLOWED_FIRST_FAILURE_KEYS = frozenset(
    {"condition", "factor", "lhs", "rhs", "inertia", "T", "reason"}
)
ALLOWED_QUARTIC_RECORD_KEYS = frozenset({"factor", "group", "B_adj", "B_hypers", "ok"})


def _sylvester_inertia(matrix: list[list[Fraction]]) -> dict[str, int]:
    """Computes inertia using recursive leading principal minor determinant evaluation."""
    n = len(matrix)
    if n == 0:
        return {"positive": 0, "negative": 0, "zero": 0}

    # Fraction-free Bareiss algorithm to compute determinant and diagonal pivots
    M = [[Fraction(matrix[i][j]) for j in range(n)] for i in range(n)]
    n_pos = 0
    n_neg = 0
    n_zero = 0

    i = 0
    while i < n:
        # Pivot search
        pivot_idx = i
        for k in range(i, n):
            if abs(M[k][k]) > abs(M[pivot_idx][pivot_idx]):
                pivot_idx = k

        if M[pivot_idx][pivot_idx] != 0:
            if pivot_idx != i:
                # Symmetrically swap row/col
                for r in range(n):
                    M[r][i], M[r][pivot_idx] = M[r][pivot_idx], M[r][i]
                M[i], M[pivot_idx] = M[pivot_idx], M[i]

            pivot = M[i][i]
            if pivot > 0:
                n_pos += 1
            else:
                n_neg += 1

            for j in range(i + 1, n):
                factor = M[j][i] / pivot
                for c in range(i + 1, n):
                    M[j][c] -= factor * M[i][c]
                M[j][i] = Fraction(0)
            i += 1
        else:
            # Check for non-zero off-diagonal entry
            found = False
            for r in range(i, n):
                for c in range(r + 1, n):
                    if M[r][c] != 0:
                        # Symmetric regularization
                        for k in range(n):
                            M[k][r] += M[k][c]
                        for k in range(n):
                            M[r][k] += M[c][k]
                        found = True
                        break
                if found:
                    break
            if not found:
                n_zero += n - i
                break

    return {"positive": n_pos, "negative": n_neg, "zero": n_zero}


def _independent_matrix_trace_coeffs(group: str, rep: str) -> tuple[Fraction, Fraction, Fraction]:
    """Trace coefficients from power sums over the weight system (Cartan-diagonal traces)."""
    return trace_coefficients(group, rep)


def _verify_matrix_refusal_warranted(case: Mapping[str, Any], refusal: str) -> tuple[bool, str]:
    """Validates that a claimed UNKNOWN refusal code is genuinely warranted by case properties."""
    if refusal not in CLOSED_REFUSAL_CODES:
        return False, f"FAIL: unrecognized refusal code {refusal!r}"

    T = case.get("T")
    gauge_group = case.get("gauge_group")
    neutral_hypers = case.get("neutral_hypers")
    hypers = case.get("hypers")

    if refusal == "T_OUT_OF_BOUNDS":
        if isinstance(T, int) and not isinstance(T, bool) and 0 <= T <= 30:
            return False, f"FAIL: refused T_OUT_OF_BOUNDS on valid T={T}"
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "NEUTRAL_HYPERS_OUT_OF_BOUNDS":
        if (
            isinstance(neutral_hypers, int)
            and not isinstance(neutral_hypers, bool)
            and neutral_hypers >= 0
        ):
            return (
                False,
                f"FAIL: refused NEUTRAL_HYPERS_OUT_OF_BOUNDS on valid neutral_hypers={neutral_hypers}",
            )
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "GROUP_NOT_SUPPORTED":
        if isinstance(gauge_group, list) and len(gauge_group) <= 4:
            if all(isinstance(g, str) and is_group_supported(g) for g in gauge_group):
                return (
                    False,
                    f"FAIL: refused GROUP_NOT_SUPPORTED on supported gauge groups {gauge_group}",
                )
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "MALFORMED_CASE_STRUCTURE":
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            return True, f"VALID_REFUSAL_{refusal}"
        if (
            not isinstance(T, int)
            or isinstance(T, bool)
            or not isinstance(neutral_hypers, int)
            or isinstance(neutral_hypers, bool)
        ):
            return True, f"VALID_REFUSAL_{refusal}"
        if not isinstance(gauge_group, list) or not isinstance(hypers, list):
            return True, f"VALID_REFUSAL_{refusal}"
        return False, f"FAIL: refused MALFORMED_CASE_STRUCTURE on well-formed case {case_id}"

    if refusal == "MULTIPLICITY_OUT_OF_BOUNDS":
        if isinstance(hypers, list):
            for h in hypers:
                if isinstance(h, Mapping):
                    m = h.get("multiplicity")
                    try:
                        f = Fraction(str(m))
                        if f <= 0 or f.denominator not in (1, 2):
                            return True, f"VALID_REFUSAL_{refusal}"
                    except Exception:
                        return True, f"VALID_REFUSAL_{refusal}"
        return (
            False,
            "FAIL: refused MULTIPLICITY_OUT_OF_BOUNDS but all multiplicities are valid positive integers/half-integers",
        )

    if refusal == "REPRESENTATION_NOT_SUPPORTED":
        if isinstance(hypers, list) and isinstance(gauge_group, list):
            for h in hypers:
                if isinstance(h, Mapping):
                    reps = h.get("reps")
                    if isinstance(reps, list):
                        for idx, r in enumerate(reps):
                            if idx < len(gauge_group) and r != "1":
                                g = gauge_group[idx]
                                try:
                                    get_rep_dim(g, r)
                                except Exception:
                                    return True, f"VALID_REFUSAL_{refusal}"
        return (
            False,
            "FAIL: refused REPRESENTATION_NOT_SUPPORTED but all representations are supported",
        )

    return False, f"FAIL: unwarranted refusal {refusal!r} on valid case"


def _verify_matrix_out_of_scope_warranted(
    case: Mapping[str, Any], witness: Any
) -> tuple[bool, str]:
    """Audits OUT_OF_SCOPE witness against case parameters."""
    if not isinstance(witness, Mapping):
        return False, "FAIL: OUT_OF_SCOPE status missing witness mapping"

    extra = set(witness.keys()) - ALLOWED_WITNESS_KEYS
    if extra:
        return False, f"FAIL: phantom keys in witness: {sorted(extra)}"

    kind = witness.get("kind")
    if kind == "unsupported_so8_triality" and "SO(8)" in case.get("gauge_group", []):
        return True, "VALID_OUT_OF_SCOPE"
    if kind == "half_hyper_in_nonpseudoreal_rep":
        gauge_group = case.get("gauge_group", [])
        for h in case.get("hypers", []):
            if isinstance(h, Mapping):
                try:
                    if Fraction(str(h.get("multiplicity", 1))).denominator == 2:
                        reps = h.get("reps", [])
                        non_singlets = [(idx, r) for idx, r in enumerate(reps) if r != "1"]
                        if len(non_singlets) != 1:
                            return True, "VALID_OUT_OF_SCOPE"
                        f_idx, r_name = non_singlets[0]
                        if f_idx < len(gauge_group):
                            g_name = gauge_group[f_idx]
                            if not is_rep_pseudoreal(g_name, r_name):
                                return True, "VALID_OUT_OF_SCOPE"
                except Exception:
                    pass
        return (
            False,
            "FAIL: claimed half_hyper_in_nonpseudoreal_rep but all half-hypers are in pseudoreal reps",
        )
    return False, f"FAIL: invalid OUT_OF_SCOPE witness {witness}"


def verify_sugra_matrix_certificate(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> tuple[bool, str]:
    """Independent Checker 2: verifies 6D SUGRA spectrum via matrix traces and Sylvester minors."""
    if not isinstance(case, Mapping) or not isinstance(result, Mapping):
        return False, "FAIL: case and result must be mappings"

    try:
        status = result.get("status")
        if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
            return False, f"FAIL: invalid status {status!r}"

        if status == "UNKNOWN":
            extra = set(result.keys()) - ALLOWED_UNKNOWN_KEYS
            if extra:
                return False, f"FAIL: phantom keys in UNKNOWN result: {sorted(extra)}"
            refusal = str(result.get("refusal_code") or result.get("refusal") or "")
            if not refusal:
                return False, "FAIL: UNKNOWN status missing refusal_code"
            return _verify_matrix_refusal_warranted(case, refusal)

        if status == "OUT_OF_SCOPE":
            extra = set(result.keys()) - ALLOWED_OOS_KEYS
            if extra:
                return False, f"FAIL: phantom keys in OUT_OF_SCOPE result: {sorted(extra)}"
            witness = result.get("witness")
            return _verify_matrix_out_of_scope_warranted(case, witness)

        # Status: SOLVED
        extra = set(result.keys()) - ALLOWED_SOLVED_KEYS
        if extra:
            return False, f"FAIL: phantom keys in SOLVED result: {sorted(extra)}"

        T = case.get("T")
        gauge_group = case.get("gauge_group", [])
        hypers = case.get("hypers", [])
        neutral_hypers = case.get("neutral_hypers", 0)

        if not isinstance(gauge_group, list):
            return False, "FAIL: gauge_group must be a list"
        if not isinstance(hypers, list):
            return False, "FAIL: hypers must be a list"
        if not isinstance(T, int) or isinstance(T, bool):
            return False, "FAIL: T must be an int"
        if not isinstance(neutral_hypers, int) or isinstance(neutral_hypers, bool):
            return False, "FAIL: neutral_hypers must be an int"

        # Pre-validate hypers structure and reps length (Total Parsing Safety)
        for h in hypers:
            if not isinstance(h, Mapping):
                return False, "FAIL: hyper element must be a mapping"
            reps = h.get("reps")
            if not isinstance(reps, list) or len(reps) != len(gauge_group):
                return (
                    False,
                    f"FAIL: hypers reps length ({len(reps) if isinstance(reps, list) else None}) must match gauge_group length ({len(gauge_group)})",
                )
            try:
                m = Fraction(str(h.get("multiplicity", 1)))
                if m <= 0 or m.denominator not in (1, 2):
                    return False, f"FAIL: invalid hyper multiplicity {m}"
            except Exception as e:
                return False, f"FAIL: unparseable hyper multiplicity ({e})"
            for idx, r in enumerate(reps):
                if not isinstance(r, str):
                    return False, f"FAIL: rep must be a string, got {r!r}"
                if r != "1":
                    try:
                        get_rep_dim(gauge_group[idx], r)
                    except Exception as e:
                        return (
                            False,
                            f"FAIL: invalid representation {r} for group {gauge_group[idx]} ({e})",
                        )

        V_true = sum(get_group_dim(g) for g in gauge_group)
        charged_H = Fraction(0)
        for h in hypers:
            m = Fraction(str(h.get("multiplicity", 1)))
            d = 1
            for idx, r in enumerate(h.get("reps", [])):
                if r != "1":
                    d *= get_rep_dim(gauge_group[idx], r)
            charged_H += m * d

        H_true = int(charged_H) + neutral_hypers

        res_V = result.get("V")
        res_H = result.get("H")
        res_T = result.get("T")

        if type(res_V) is not int or isinstance(res_V, bool) or res_V != V_true:
            return False, f"FAIL: declared V={res_V!r} != true V={V_true} (must be exact int)"
        if type(res_H) is not int or isinstance(res_H, bool) or res_H != H_true:
            return False, f"FAIL: declared H={res_H!r} != true H={H_true} (must be exact int)"
        if type(res_T) is not int or isinstance(res_T, bool) or res_T != T:
            return False, f"FAIL: declared T={res_T!r} != true T={T} (must be exact int)"

        verdict = result.get("verdict")
        if verdict not in ("PASSES_NECESSARY_CONDITIONS", "ANOMALOUS"):
            return False, f"FAIL: invalid verdict {verdict!r}"

        # Condition 1: Gravitational
        grav_sum = H_true - V_true + 29 * T
        if grav_sum != 273:
            if verdict != "ANOMALOUS":
                return False, "FAIL: expected ANOMALOUS on gravitational condition failure"
            ff = result.get("first_failure")
            if not isinstance(ff, Mapping) or ff.get("condition") != 1:
                return False, f"FAIL: expected first_failure condition 1, got {ff}"
            extra_ff = set(ff.keys()) - ALLOWED_FIRST_FAILURE_KEYS
            if extra_ff:
                return False, f"FAIL: phantom keys in first_failure: {sorted(extra_ff)}"
            return True, "PASS: correctly detected condition 1 failure via matrix checker"

        # Condition 2: Quartic
        for f_idx, g_name in enumerate(gauge_group):
            if not has_independent_quartic(g_name):
                continue
            _, B_adj, _ = _independent_matrix_trace_coeffs(g_name, "adj")
            B_sum = Fraction(0)
            for h in hypers:
                r = h["reps"][f_idx]
                if r != "1":
                    spec_dim = 1
                    for s_idx, s_rep in enumerate(h["reps"]):
                        if s_idx != f_idx and s_rep != "1":
                            spec_dim *= get_rep_dim(gauge_group[s_idx], s_rep)
                    m = Fraction(str(h.get("multiplicity", 1))) * spec_dim
                    _, B_r, _ = _independent_matrix_trace_coeffs(g_name, r)
                    B_sum += m * B_r

            if B_adj != B_sum:
                if verdict != "ANOMALOUS":
                    return False, f"FAIL: expected ANOMALOUS on quartic failure for {g_name}"
                ff = result.get("first_failure")
                if not isinstance(ff, Mapping) or ff.get("condition") != 2:
                    return False, f"FAIL: expected first_failure condition 2, got {ff}"
                extra_ff = set(ff.keys()) - ALLOWED_FIRST_FAILURE_KEYS
                if extra_ff:
                    return False, f"FAIL: phantom keys in first_failure: {sorted(extra_ff)}"
                return True, "PASS: correctly detected condition 2 failure via matrix checker"

        # Condition 5: Sylvester Inertia
        k_factors = len(gauge_group)
        ab_vals: list[Fraction] = []
        bb_vals: list[Fraction] = []
        for f_idx, g_name in enumerate(gauge_group):
            lam = get_group_lambda(g_name)
            A_adj, _, C_adj = _independent_matrix_trace_coeffs(g_name, "adj")
            A_sum = Fraction(0)
            C_sum = Fraction(0)
            for h in hypers:
                r = h["reps"][f_idx]
                if r != "1":
                    spec_dim = 1
                    for s_idx, s_rep in enumerate(h["reps"]):
                        if s_idx != f_idx and s_rep != "1":
                            spec_dim *= get_rep_dim(gauge_group[s_idx], s_rep)
                    m = Fraction(str(h.get("multiplicity", 1))) * spec_dim
                    A_r, _, C_r = _independent_matrix_trace_coeffs(g_name, r)
                    A_sum += m * A_r
                    C_sum += m * C_r
            ab_vals.append(Fraction(1, 6) * lam * (A_adj - A_sum))
            bb_vals.append(Fraction(1, 3) * (lam**2) * (C_sum - C_adj))

        cross_dict: dict[tuple[int, int], Fraction] = {}
        for i in range(k_factors):
            for j in range(i + 1, k_factors):
                lam_i = get_group_lambda(gauge_group[i])
                lam_j = get_group_lambda(gauge_group[j])
                cross_sum = Fraction(0)
                for h in hypers:
                    r_i = h["reps"][i]
                    r_j = h["reps"][j]
                    if r_i != "1" and r_j != "1":
                        spec_dim = 1
                        for s_idx, s_rep in enumerate(h["reps"]):
                            if s_idx not in (i, j) and s_rep != "1":
                                spec_dim *= get_rep_dim(gauge_group[s_idx], s_rep)
                        m = Fraction(str(h.get("multiplicity", 1))) * spec_dim
                        A_ri, _, _ = _independent_matrix_trace_coeffs(gauge_group[i], r_i)
                        A_rj, _, _ = _independent_matrix_trace_coeffs(gauge_group[j], r_j)
                        cross_sum += m * A_ri * A_rj
                cross_dict[(i, j)] = lam_i * lam_j * cross_sum
                cross_dict[(j, i)] = cross_dict[(i, j)]

        gram_dim = k_factors + 1
        M = [[Fraction(0) for _ in range(gram_dim)] for _ in range(gram_dim)]
        M[0][0] = Fraction(9 - T)
        for i in range(k_factors):
            M[0][i + 1] = ab_vals[i]
            M[i + 1][0] = ab_vals[i]
            M[i + 1][i + 1] = bb_vals[i]
        for i in range(k_factors):
            for j in range(k_factors):
                if i != j:
                    M[i + 1][j + 1] = cross_dict.get((i, j), Fraction(0))

        inertia = _sylvester_inertia(M)
        if inertia["positive"] > 1 or inertia["negative"] > T:
            if verdict != "ANOMALOUS":
                return False, "FAIL: expected ANOMALOUS on Gram inertia failure"
            ff = result.get("first_failure")
            if not isinstance(ff, Mapping) or ff.get("condition") != 5:
                return False, f"FAIL: expected first_failure condition 5, got {ff}"
            extra_ff = set(ff.keys()) - ALLOWED_FIRST_FAILURE_KEYS
            if extra_ff:
                return False, f"FAIL: phantom keys in first_failure: {sorted(extra_ff)}"
            return True, "PASS: correctly detected condition 5 failure via matrix checker"

        if verdict != "PASSES_NECESSARY_CONDITIONS":
            return False, f"FAIL: spectrum satisfies all conditions but verdict is {verdict}"

        # Mandatory Arithmetic Payloads for PASSES_NECESSARY_CONDITIONS
        # 1. Gravitational payload
        res_grav = result.get("gravitational")
        if res_grav is None or not isinstance(res_grav, Mapping):
            return False, "FAIL: missing or invalid mandatory 'gravitational' payload"
        extra_grav = set(res_grav.keys()) - ALLOWED_GRAVITATIONAL_KEYS
        if extra_grav:
            return False, f"FAIL: phantom keys in gravitational payload: {sorted(extra_grav)}"
        if res_grav.get("lhs") != grav_sum and str(res_grav.get("lhs")) != str(grav_sum):
            return (
                False,
                f"FAIL: gravitational lhs declared {res_grav.get('lhs')} != true {grav_sum}",
            )
        if res_grav.get("ok") is not True:
            return False, f"FAIL: gravitational ok declared {res_grav.get('ok')} != true"

        # 2. Coefficients payload
        coeffs = result.get("coefficients")
        if coeffs is None or not isinstance(coeffs, Mapping):
            return False, "FAIL: missing or invalid mandatory 'coefficients' payload"
        extra_coeffs = set(coeffs.keys()) - ALLOWED_COEFFICIENT_KEYS
        if extra_coeffs:
            return False, f"FAIL: phantom keys in coefficients payload: {sorted(extra_coeffs)}"
        if set(coeffs.keys()) != ALLOWED_COEFFICIENT_KEYS:
            return (
                False,
                f"FAIL: coefficients keys must be exactly {sorted(ALLOWED_COEFFICIENT_KEYS)}, got {sorted(coeffs.keys())}",
            )
        if coeffs.get("a.a") != str(Fraction(9 - T)):
            return (
                False,
                f"FAIL: coefficients['a.a'] declared {coeffs.get('a.a')!r} != true {Fraction(9 - T)}",
            )
        if coeffs.get("a.b") != [str(x) for x in ab_vals]:
            return (
                False,
                f"FAIL: coefficients['a.b'] declared {coeffs.get('a.b')!r} != true {[str(x) for x in ab_vals]}",
            )
        if coeffs.get("b.b") != [str(x) for x in bb_vals]:
            return (
                False,
                f"FAIL: coefficients['b.b'] declared {coeffs.get('b.b')!r} != true {[str(x) for x in bb_vals]}",
            )

        # 3. Quartic payload
        res_quartic = result.get("quartic")
        if res_quartic is None or not isinstance(res_quartic, list):
            return False, "FAIL: missing or invalid mandatory 'quartic' payload"
        for q_rec in res_quartic:
            if not isinstance(q_rec, Mapping):
                return False, "FAIL: quartic record must be a mapping"
            extra_q = set(q_rec.keys()) - ALLOWED_QUARTIC_RECORD_KEYS
            if extra_q:
                return False, f"FAIL: phantom keys in quartic record: {sorted(extra_q)}"
            f_idx = q_rec.get("factor")
            if isinstance(f_idx, int) and 0 <= f_idx < len(gauge_group):
                g_name = gauge_group[f_idx]
                B_hypers_true = Fraction(0)
                for h in hypers:
                    r = h["reps"][f_idx]
                    if r != "1":
                        spec_dim = 1
                        for s_idx, s_rep in enumerate(h["reps"]):
                            if s_idx != f_idx and s_rep != "1":
                                spec_dim *= get_rep_dim(gauge_group[s_idx], s_rep)
                        m = Fraction(str(h.get("multiplicity", 1))) * spec_dim
                        _, B_r, _ = _independent_matrix_trace_coeffs(g_name, r)
                        B_hypers_true += m * B_r
                if str(q_rec.get("B_hypers")) != str(B_hypers_true):
                    return (
                        False,
                        f"FAIL: quartic B_hypers declared {q_rec.get('B_hypers')} != true {B_hypers_true}",
                    )

        # 4. Gram inertia payload (with strict int validation rejecting booleans)
        res_inertia = result.get("gram_inertia")
        if res_inertia is None or not isinstance(res_inertia, Mapping):
            return False, "FAIL: missing or invalid mandatory 'gram_inertia' payload"
        extra_inertia = set(res_inertia.keys()) - ALLOWED_INERTIA_KEYS
        if extra_inertia:
            return False, f"FAIL: phantom keys in gram_inertia payload: {sorted(extra_inertia)}"
        for k in ("positive", "negative", "zero"):
            val = res_inertia.get(k)
            if type(val) is not int or isinstance(val, bool):
                return False, f"FAIL: gram_inertia[{k}] must be exact int, got {val!r}"
            if val != inertia[k]:
                return False, f"FAIL: gram_inertia[{k}] declared {val} != true {inertia[k]}"

        return (
            True,
            f"PASS: matrix checker confirmed consistent 6D SUGRA spectrum (T={T}, H={H_true}, V={V_true})",
        )

    except Exception as e:
        return False, f"FAIL: unhandled error in matrix checker ({e})"
