"""Six-Dimensional (1,0) Supergravity Anomaly Cancellation Engine.

Provides exact rational group theory, trace coefficients (A^R, B^R, C^R),
anomaly polynomials, and Gram matrix inertia calculations for 6D SUGRA spectra.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

# Supported groups and their dimensions
GROUP_DIMS: dict[str, int] = {
    "SU(2)": 3,
    "SU(3)": 8,
    "SU(4)": 15,
    "SU(5)": 24,
    "SU(6)": 35,
    "SU(7)": 48,
    "SU(8)": 63,
    "SO(7)": 21,
    "SO(9)": 36,
    "SO(10)": 45,
    "SO(11)": 55,
    "SO(12)": 66,
    "SO(13)": 78,
    "SO(14)": 91,
    "Sp(1)": 3,
    "Sp(2)": 10,
    "Sp(3)": 21,
    "Sp(4)": 36,
    "G2": 14,
    "F4": 52,
    "E6": 78,
    "E7": 133,
    "E8": 248,
}

# Normalization lambda per gauge group family
GROUP_LAMBDAS: dict[str, int] = {
    "SU": 1,
    "SO": 2,
    "Sp": 1,
    "G2": 2,
    "F4": 6,
    "E6": 6,
    "E7": 12,
    "E8": 60,
}

# Groups without independent quartic Casimir (B^R = 0 for all R)
GROUPS_WITHOUT_QUARTIC: frozenset[str] = frozenset(
    {"SU(2)", "SU(3)", "Sp(1)", "G2", "F4", "E6", "E7", "E8"}
)


def get_group_lambda(group: str) -> int:
    """Returns the group normalization constant lambda_i."""
    for prefix in ("SU", "SO", "Sp", "G2", "F4", "E6", "E7", "E8"):
        if group.startswith(prefix):
            return GROUP_LAMBDAS[prefix]
    raise ValueError(f"Unknown group family for {group}")


def is_group_supported(group: str) -> bool:
    """Checks whether the simple gauge factor is supported."""
    return group in GROUP_DIMS


def get_group_dim(group: str) -> int:
    """Returns the dimension of the adjoint representation of group."""
    if group not in GROUP_DIMS:
        raise ValueError(f"Unsupported group: {group}")
    return GROUP_DIMS[group]


def get_rep_dim(group: str, rep: str) -> int:
    """Returns dimension of representation rep in group."""
    if rep == "adj":
        return get_group_dim(group)

    if group.startswith("SU("):
        n = int(group[3:-1])
        if rep in ("fund", str(n)):
            return n
        if rep in ("antisym", f"AS_{n * (n - 1) // 2}"):
            return n * (n - 1) // 2
        if rep in ("sym", f"S_{n * (n + 1) // 2}"):
            return n * (n + 1) // 2
    elif group.startswith("SO("):
        n = int(group[3:-1])
        if rep in ("vect", "fund", str(n)):
            return n
        if rep in ("spinor", "spin"):
            if n == 7:
                return 8
            if n in (9, 10):
                return 16
            if n in (11, 12):
                return 32
            if n in (13, 14):
                return 64
    elif group.startswith("Sp("):
        n = int(group[3:-1])
        if rep in ("fund", str(2 * n)):
            return 2 * n
        if rep in ("antisym", f"AS_{n * (2 * n - 1) - 1}"):
            return n * (2 * n - 1) - 1
    elif group == "G2":
        if rep in ("fund", "7"):
            return 7
    elif group == "F4":
        if rep in ("fund", "26"):
            return 26
    elif group == "E6":
        if rep in ("fund", "27"):
            return 27
    elif group == "E7":
        if rep in ("fund", "56"):
            return 56
    elif group == "E8":
        if rep == "adj":
            return 248

    raise ValueError(f"Unknown representation {rep!r} for group {group}")


def is_rep_pseudoreal(group: str, rep: str) -> bool:
    """Returns True if the representation is pseudoreal (quaternionic)."""
    if group == "SU(2)" and rep in ("fund", "2"):
        return True
    if group.startswith("Sp(") and rep in ("fund", str(get_rep_dim(group, "fund"))):
        return True
    if group == "E7" and rep in ("fund", "56"):
        return True
    if group in ("SO(11)", "SO(12)", "SO(13)") and rep in ("spinor", "spin"):
        return True
    return False


# Classical factors whose fundamental satisfies tr F^4 = 1/2 (tr F^2)^2, so that the
# general SU(N) / Sp(N) quartic coefficient B folds into C (Kumar, Morrison and Taylor 2010).
_FOLD_QUARTIC_INTO_C: frozenset[str] = frozenset({"SU(2)", "SU(3)", "Sp(1)"})


def get_trace_coefficients(group: str, rep: str) -> tuple[Fraction, Fraction, Fraction]:
    """Returns exact rational trace coefficients (A^R, B^R, C^R).

    For SU(2), SU(3) and Sp(1) there is no independent quartic Casimir and
    tr F^4 = 1/2 (tr F^2)^2, so tr_R F^4 = B tr F^4 + C (tr F^2)^2 becomes
    (C + B/2) (tr F^2)^2: B is reported as 0 and B/2 is added to C.
    """
    A, B, C = _general_trace_coefficients(group, rep)
    if group in _FOLD_QUARTIC_INTO_C:
        return A, Fraction(0), C + B / 2
    return A, B, C


def _general_trace_coefficients(group: str, rep: str) -> tuple[Fraction, Fraction, Fraction]:
    """Trace coefficients from the general SU(N), SO(N), Sp(N) and exceptional formulas."""
    if group.startswith("SU("):
        n = int(group[3:-1])
        if rep == "adj":
            return Fraction(2 * n), Fraction(2 * n), Fraction(6)
        if rep in ("fund", str(n)):
            return Fraction(1), Fraction(1), Fraction(0)
        if rep in ("antisym", f"AS_{n * (n - 1) // 2}"):
            return Fraction(n - 2), Fraction(n - 8), Fraction(3)
        if rep in ("sym", f"S_{n * (n + 1) // 2}"):
            return Fraction(n + 2), Fraction(n + 8), Fraction(3)

    elif group.startswith("SO("):
        n = int(group[3:-1])
        if rep == "adj":
            A = Fraction(n - 2)
            B = Fraction(n - 8)
            C = Fraction(3)
            return A, B, C
        if rep in ("vect", "fund", str(n)):
            A = Fraction(1)
            B = Fraction(1)
            C = Fraction(0)
            return A, B, C
        if rep in ("spinor", "spin"):
            if n == 7:
                return Fraction(1), Fraction(-1, 2), Fraction(3, 8)
            if n in (9, 10):
                return Fraction(2), Fraction(-1), Fraction(3, 4)
            if n in (11, 12):
                return Fraction(4), Fraction(-2), Fraction(3, 2)
            if n in (13, 14):
                return Fraction(8), Fraction(-4), Fraction(3)

    elif group.startswith("Sp("):
        n = int(group[3:-1])
        if rep == "adj":
            return Fraction(2 * n + 2), Fraction(2 * n + 8), Fraction(3)
        if rep in ("fund", str(2 * n)):
            return Fraction(1), Fraction(1), Fraction(0)
        if rep in ("antisym", f"AS_{n * (2 * n - 1) - 1}"):
            return Fraction(2 * n - 2), Fraction(2 * n - 8), Fraction(3)

    elif group == "G2":
        if rep in ("fund", "7"):
            return Fraction(1), Fraction(0), Fraction(1, 4)
        if rep == "adj":
            return Fraction(4), Fraction(0), Fraction(5, 2)
    elif group == "F4":
        if rep in ("fund", "26"):
            return Fraction(1), Fraction(0), Fraction(1, 12)
        if rep == "adj":
            return Fraction(3), Fraction(0), Fraction(5, 12)
    elif group == "E6":
        if rep in ("fund", "27"):
            return Fraction(1), Fraction(0), Fraction(1, 12)
        if rep == "adj":
            return Fraction(4), Fraction(0), Fraction(1, 2)
    elif group == "E7":
        if rep in ("fund", "56"):
            return Fraction(1), Fraction(0), Fraction(1, 24)
        if rep == "adj":
            return Fraction(3), Fraction(0), Fraction(1, 6)
    elif group == "E8":
        if rep == "adj":
            return Fraction(1), Fraction(0), Fraction(1, 100)

    raise ValueError(f"Trace coefficients not defined for {group} rep {rep}")


def compute_exact_inertia(matrix: list[list[Fraction]]) -> dict[str, int]:
    """Computes exact inertia (positive, negative, zero) of symmetric rational matrix.

    Uses exact rational Gaussian elimination with symmetric pivoting (congruence transforms
    preserving Sylvester's Law of Inertia).
    """
    n = len(matrix)
    if n == 0:
        return {"positive": 0, "negative": 0, "zero": 0}

    A = [[Fraction(matrix[i][j]) for j in range(n)] for i in range(n)]
    n_pos = 0
    n_neg = 0
    n_zero = 0

    i = 0
    while i < n:
        # Search for maximal non-zero diagonal element in remaining block
        best = i
        for k in range(i, n):
            if abs(A[k][k]) > abs(A[best][best]):
                best = k

        if A[best][best] != 0:
            if best != i:
                # Symmetrically swap row/col i and best
                for r in range(n):
                    A[r][i], A[r][best] = A[r][best], A[r][i]
                A[i], A[best] = A[best], A[i]

            pivot = A[i][i]
            if pivot > 0:
                n_pos += 1
            else:
                n_neg += 1

            for j in range(i + 1, n):
                factor = A[j][i] / pivot
                for c in range(i + 1, n):
                    A[j][c] -= factor * A[i][c]
                A[j][i] = Fraction(0)
            i += 1
        else:
            # Diagonal is zero. Look for off-diagonal non-zero entry
            found_r, found_c = -1, -1
            for r in range(i, n):
                for c in range(r + 1, n):
                    if A[r][c] != 0:
                        found_r, found_c = r, c
                        break
                if found_r != -1:
                    break

            if found_r == -1:
                # Entire remaining submatrix is zero
                n_zero += n - i
                break
            else:
                # Symmetrically add column found_c to found_r and row found_c to found_r
                # This makes new A[found_r][found_r] = 2 * A[found_r][found_c] != 0
                for k in range(n):
                    A[k][found_r] += A[k][found_c]
                for k in range(n):
                    A[found_r][k] += A[found_c][k]
                # Repeat step i with non-zero diagonal
                continue

    return {"positive": n_pos, "negative": n_neg, "zero": n_zero}


def evaluate_6d_sugra_spectrum(case: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluates a 6D (1,0) SUGRA spectrum against all five anomaly cancellation conditions."""
    if not isinstance(case, Mapping):
        return {
            "id": "unknown",
            "status": "UNKNOWN",
            "refusal": "MALFORMED_CASE_STRUCTURE",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }

    raw_id = case.get("id")
    case_id = str(raw_id) if raw_id is not None else ""
    T = case.get("T")
    gauge_group = case.get("gauge_group", [])
    hypers = case.get("hypers", [])
    neutral_hypers = case.get("neutral_hypers", 0)

    # 1. Parameter Validation
    # Defect 3: Reject booleans and out-of-bounds ints for T
    if isinstance(T, bool) or not isinstance(T, int) or T < 0 or T > 30:
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "T_OUT_OF_BOUNDS",
            "refusal_code": "T_OUT_OF_BOUNDS",
        }

    # Defect 3: Reject booleans and out-of-bounds ints for neutral_hypers
    if (
        isinstance(neutral_hypers, bool)
        or not isinstance(neutral_hypers, int)
        or neutral_hypers < 0
    ):
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "NEUTRAL_HYPERS_OUT_OF_BOUNDS",
            "refusal_code": "NEUTRAL_HYPERS_OUT_OF_BOUNDS",
        }

    if not isinstance(gauge_group, list) or len(gauge_group) > 4:
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "GROUP_NOT_SUPPORTED",
            "refusal_code": "GROUP_NOT_SUPPORTED",
        }

    for g in gauge_group:
        if not isinstance(g, str) or not is_group_supported(g):
            if g == "SO(8)":
                return {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"kind": "unsupported_so8_triality", "factor": gauge_group.index(g)},
                }
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "GROUP_NOT_SUPPORTED",
                "refusal_code": "GROUP_NOT_SUPPORTED",
            }

    # Defect 2: Validate hypers type before iteration
    if not isinstance(hypers, list):
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_CASE_STRUCTURE",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }

    # Validate Hypermultiplets and check for Out-of-Scope half-hypers
    k_factors = len(gauge_group)
    processed_hypers: list[dict[str, Any]] = []

    for h_idx, h in enumerate(hypers):
        if not isinstance(h, Mapping):
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_CASE_STRUCTURE",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }

        mult_val = h.get("multiplicity", 1)

        # Defect 4: Reject booleans for multiplicity
        if isinstance(mult_val, bool):
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MULTIPLICITY_OUT_OF_BOUNDS",
                "refusal_code": "MULTIPLICITY_OUT_OF_BOUNDS",
            }

        # Defect 5: Exact rational conversion without coercive .limit_denominator(2)
        try:
            mult = Fraction(str(mult_val))
        except (ValueError, ZeroDivisionError, TypeError):
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MULTIPLICITY_OUT_OF_BOUNDS",
                "refusal_code": "MULTIPLICITY_OUT_OF_BOUNDS",
            }

        if mult <= 0 or (mult.denominator not in (1, 2)):
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MULTIPLICITY_OUT_OF_BOUNDS",
                "refusal_code": "MULTIPLICITY_OUT_OF_BOUNDS",
            }

        reps = h.get("reps")
        if not isinstance(reps, list) or len(reps) != k_factors:
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_CASE_STRUCTURE",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }

        # Defect 1: Validate representation names before attempting arithmetic
        for idx, r in enumerate(reps):
            if not isinstance(r, str):
                return {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "MALFORMED_CASE_STRUCTURE",
                    "refusal_code": "MALFORMED_CASE_STRUCTURE",
                }
            if r != "1":
                try:
                    get_rep_dim(gauge_group[idx], r)
                except ValueError:
                    return {
                        "id": case_id,
                        "status": "UNKNOWN",
                        "refusal": "REPRESENTATION_NOT_SUPPORTED",
                        "refusal_code": "REPRESENTATION_NOT_SUPPORTED",
                    }

        # Check half-hypermultiplet validity
        if mult.denominator == 2:
            # Can only be a half-hyper if charged under exactly one simple factor with a pseudoreal representation
            non_singlets = [(idx, r) for idx, r in enumerate(reps) if r != "1"]
            if len(non_singlets) != 1:
                return {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"kind": "half_hyper_in_nonpseudoreal_rep", "hyper_index": h_idx},
                }
            f_idx, r_name = non_singlets[0]
            g_name = gauge_group[f_idx]
            if not is_rep_pseudoreal(g_name, r_name):
                return {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"kind": "half_hyper_in_nonpseudoreal_rep", "factor": f_idx},
                }

        processed_hypers.append({"mult": mult, "reps": reps})

    try:
        # 2. Compute V (dimension of gauge vectors)
        V = sum(get_group_dim(g) for g in gauge_group)

        # 3. Compute H (total hypermultiplet count)
        total_charged_H = Fraction(0)
        for h in processed_hypers:
            mult = h["mult"]
            dim_prod = 1
            for idx, r in enumerate(h["reps"]):
                if r != "1":
                    dim_prod *= get_rep_dim(gauge_group[idx], r)
            total_charged_H += mult * dim_prod

        if total_charged_H.denominator != 1:
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "NON_INTEGER_HYPER_COUNT",
                "refusal_code": "NON_INTEGER_HYPER_COUNT",
            }

        H = int(total_charged_H) + neutral_hypers

        # Condition 1: Pure Gravitational Anomaly H - V + 29*T == 273
        grav_lhs = H - V + 29 * T
        cond1_ok = grav_lhs == 273
        if not cond1_ok:
            return {
                "id": case_id,
                "status": "SOLVED",
                "H": H,
                "V": V,
                "T": T,
                "verdict": "ANOMALOUS",
                "first_failure": {
                    "condition": 1,
                    "lhs": str(grav_lhs),
                    "rhs": "273",
                },
            }

        # Condition 2: Quartic Casimir Cancellation for each factor with quartic Casimir
        quartic_records: list[dict[str, Any]] = []
        for f_idx, g_name in enumerate(gauge_group):
            if g_name in GROUPS_WITHOUT_QUARTIC:
                continue

            _, B_adj, _ = get_trace_coefficients(g_name, "adj")
            B_hypers = Fraction(0)
            for h in processed_hypers:
                r = h["reps"][f_idx]
                if r != "1":
                    # Multiplicity weighted by spectator dimensions
                    spectator_dim = 1
                    for s_idx, s_rep in enumerate(h["reps"]):
                        if s_idx != f_idx and s_rep != "1":
                            spectator_dim *= get_rep_dim(gauge_group[s_idx], s_rep)
                    mult_factor = h["mult"] * spectator_dim
                    _, B_r, _ = get_trace_coefficients(g_name, r)
                    B_hypers += mult_factor * B_r

            quartic_records.append(
                {
                    "factor": f_idx,
                    "group": g_name,
                    "B_adj": str(B_adj),
                    "B_hypers": str(B_hypers),
                    "ok": (B_adj == B_hypers),
                }
            )

            if B_adj != B_hypers:
                return {
                    "id": case_id,
                    "status": "SOLVED",
                    "H": H,
                    "V": V,
                    "T": T,
                    "verdict": "ANOMALOUS",
                    "first_failure": {
                        "condition": 2,
                        "factor": f_idx,
                        "lhs": str(B_adj),
                        "rhs": str(B_hypers),
                    },
                }

        # Condition 3: a . a == 9 - T
        aa = Fraction(9 - T)

        # Condition 4: Anomaly Vector Intersections (a.b_i, b_i.b_i, b_i.b_j)
        ab_list: list[str] = []
        bb_list: list[str] = []
        ab_vals: list[Fraction] = []
        bb_vals: list[Fraction] = []

        for f_idx, g_name in enumerate(gauge_group):
            lam = get_group_lambda(g_name)
            A_adj, _, C_adj = get_trace_coefficients(g_name, "adj")

            # Sum over hypers
            A_sum = Fraction(0)
            C_sum = Fraction(0)
            for h in processed_hypers:
                r = h["reps"][f_idx]
                if r != "1":
                    spectator_dim = 1
                    for s_idx, s_rep in enumerate(h["reps"]):
                        if s_idx != f_idx and s_rep != "1":
                            spectator_dim *= get_rep_dim(gauge_group[s_idx], s_rep)
                    mult_factor = h["mult"] * spectator_dim
                    A_r, _, C_r = get_trace_coefficients(g_name, r)
                    A_sum += mult_factor * A_r
                    C_sum += mult_factor * C_r

            ab_i = Fraction(1, 6) * lam * (A_adj - A_sum)
            bb_i = Fraction(1, 3) * (lam**2) * (C_sum - C_adj)

            ab_vals.append(ab_i)
            bb_vals.append(bb_i)
            ab_list.append(str(ab_i))
            bb_list.append(str(bb_i))

        # Cross terms b_i . b_j (i < j)
        cross_dict: dict[tuple[int, int], Fraction] = {}
        for i in range(k_factors):
            for j in range(i + 1, k_factors):
                lam_i = get_group_lambda(gauge_group[i])
                lam_j = get_group_lambda(gauge_group[j])
                cross_sum = Fraction(0)
                for h in processed_hypers:
                    r_i = h["reps"][i]
                    r_j = h["reps"][j]
                    if r_i != "1" and r_j != "1":
                        spectator_dim = 1
                        for s_idx, s_rep in enumerate(h["reps"]):
                            if s_idx not in (i, j) and s_rep != "1":
                                spectator_dim *= get_rep_dim(gauge_group[s_idx], s_rep)
                        mult_factor = h["mult"] * spectator_dim
                        A_ri, _, _ = get_trace_coefficients(gauge_group[i], r_i)
                        A_rj, _, _ = get_trace_coefficients(gauge_group[j], r_j)
                        cross_sum += mult_factor * A_ri * A_rj

                bij = lam_i * lam_j * cross_sum
                cross_dict[(i, j)] = bij
                cross_dict[(j, i)] = bij

        # Build the (k+1) x (k+1) Gram matrix M
        gram_dim = k_factors + 1
        M = [[Fraction(0) for _ in range(gram_dim)] for _ in range(gram_dim)]
        M[0][0] = aa

        for i in range(k_factors):
            M[0][i + 1] = ab_vals[i]
            M[i + 1][0] = ab_vals[i]
            M[i + 1][i + 1] = bb_vals[i]

        for i in range(k_factors):
            for j in range(k_factors):
                if i != j:
                    M[i + 1][j + 1] = cross_dict.get((i, j), Fraction(0))

        # Condition 5: Realizability in Signature (1, T)
        inertia = compute_exact_inertia(M)
        cond5_ok = inertia["positive"] <= 1 and inertia["negative"] <= T

        if not cond5_ok:
            return {
                "id": case_id,
                "status": "SOLVED",
                "H": H,
                "V": V,
                "T": T,
                "coefficients": {
                    "a.a": str(aa),
                    "a.b": ab_list,
                    "b.b": bb_list,
                },
                "quartic": quartic_records,
                "gram_inertia": inertia,
                "verdict": "ANOMALOUS",
                "first_failure": {
                    "condition": 5,
                    "inertia": inertia,
                    "T": T,
                    "reason": f"Gram matrix inertia ({inertia['positive']}, {inertia['negative']}) cannot embed in (1, {T})",
                },
            }

        # All necessary conditions passed!
        return {
            "id": case_id,
            "status": "SOLVED",
            "H": H,
            "V": V,
            "T": T,
            "gravitational": {"lhs": grav_lhs, "ok": True},
            "coefficients": {
                "a.a": str(aa),
                "a.b": ab_list,
                "b.b": bb_list,
            },
            "quartic": quartic_records,
            "gram_inertia": inertia,
            "verdict": "PASSES_NECESSARY_CONDITIONS",
        }

    except ValueError as e:
        if "Unknown representation" in str(e) or "Trace coefficients not defined" in str(e):
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "REPRESENTATION_NOT_SUPPORTED",
                "refusal_code": "REPRESENTATION_NOT_SUPPORTED",
            }
        raise
