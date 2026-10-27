"""Checker 2: Independent Dense Spectral LDL^H Checker over Q[i] and Exact Kernel Rank.

Independent from Checker 1: does not use generator basis, decompositions, or minimizers.
Constructs exact dense operator H - E0*I over Gaussian rationals Q[i],
confirms positive semidefiniteness via exact rational LDL^T / LDL^H,
and confirms exact kernel dimension == claimed degeneracy.

Includes secondary NumPy eigensolver labelled SECONDARY_NUMERIC.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# ---------------------------------------------------------------------------
# Exact Gaussian Rational Field Q[i]
# ---------------------------------------------------------------------------


class GaussianRational:
    """Exact Gaussian rational number a + bi with a, b in Fraction."""

    __slots__ = ("r", "i")

    def __init__(self, r: Any = 0, i: Any = 0) -> None:
        self.r: Fraction = r if isinstance(r, Fraction) else Fraction(r)
        self.i: Fraction = i if isinstance(i, Fraction) else Fraction(i)

    def __repr__(self) -> str:
        if self.i == 0:
            return f"{self.r}"
        if self.r == 0:
            return f"{self.i}i"
        sign = "+" if self.i > 0 else "-"
        return f"({self.r} {sign} {abs(self.i)}i)"

    def __add__(self, other: Any) -> GaussianRational:
        if isinstance(other, GaussianRational):
            return GaussianRational(self.r + other.r, self.i + other.i)
        return GaussianRational(self.r + other, self.i)

    def __radd__(self, other: Any) -> GaussianRational:
        return self.__add__(other)

    def __sub__(self, other: Any) -> GaussianRational:
        if isinstance(other, GaussianRational):
            return GaussianRational(self.r - other.r, self.i - other.i)
        return GaussianRational(self.r - other, self.i)

    def __rsub__(self, other: Any) -> GaussianRational:
        if isinstance(other, GaussianRational):
            return GaussianRational(other.r - self.r, other.i - self.i)
        return GaussianRational(other - self.r, -self.i)

    def __mul__(self, other: Any) -> GaussianRational:
        if isinstance(other, GaussianRational):
            return GaussianRational(
                self.r * other.r - self.i * other.i,
                self.r * other.i + self.i * other.r,
            )
        return GaussianRational(self.r * other, self.i * other)

    def __rmul__(self, other: Any) -> GaussianRational:
        return self.__mul__(other)

    def __truediv__(self, other: Any) -> GaussianRational:
        if isinstance(other, GaussianRational):
            denom = other.r * other.r + other.i * other.i
            if denom == 0:
                raise ZeroDivisionError("Division by zero GaussianRational")
            return GaussianRational(
                (self.r * other.r + self.i * other.i) / denom,
                (self.i * other.r - self.r * other.i) / denom,
            )
        if other == 0:
            raise ZeroDivisionError("Division by zero")
        return GaussianRational(self.r / other, self.i / other)

    def conj(self) -> GaussianRational:
        return GaussianRational(self.r, -self.i)

    def norm_sq(self) -> Fraction:
        return self.r * self.r + self.i * self.i

    def is_zero(self) -> bool:
        return self.r == 0 and self.i == 0


def _is_exact_int(val: Any) -> bool:
    """True if val is int and NOT bool."""
    return isinstance(val, int) and not isinstance(val, bool)


def _validate_case_structure(case: Any) -> tuple[bool, str, dict[str, Any] | None]:
    """Validates case dictionary against input schema.

    Returns (is_valid, refusal_code_if_invalid, parsed_data_if_valid).
    """
    if not isinstance(case, Mapping):
        return False, "MALFORMED_CASE_STRUCTURE", None

    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id:
        return False, "MALFORMED_CASE_STRUCTURE", None

    n = case.get("n")
    if not _is_exact_int(n) or not (1 <= n <= 8):
        return False, "NUM_QUBITS_OUT_OF_BOUNDS", None

    terms_raw = case.get("terms")
    if not isinstance(terms_raw, list):
        return False, "MALFORMED_CASE_STRUCTURE", None

    if len(terms_raw) > 24:
        return False, "TERM_COUNT_OUT_OF_BOUNDS", None

    seen_ids: set[str] = set()
    terms: list[dict[str, Any]] = []

    valid_paulis = {"I", "X", "Y", "Z"}

    for t in terms_raw:
        if not isinstance(t, Mapping):
            return False, "MALFORMED_CASE_STRUCTURE", None

        t_id = t.get("id")
        if not isinstance(t_id, str) or not t_id:
            return False, "INVALID_TERM_ID", None
        if t_id in seen_ids:
            return False, "DUPLICATE_TERM_ID", None
        seen_ids.add(t_id)

        p_str = t.get("P")
        if (
            not isinstance(p_str, str)
            or len(p_str) != n
            or any(c not in valid_paulis for c in p_str)
        ):
            return False, "MALFORMED_PAULI_WORD", None

        w_raw = t.get("w")
        if (
            not isinstance(w_raw, (list, tuple))
            or len(w_raw) != 2
            or not _is_exact_int(w_raw[0])
            or not _is_exact_int(w_raw[1])
            or w_raw[0] <= 0
            or w_raw[1] <= 0
        ):
            return False, "INVALID_WEIGHT", None

        target = t.get("target")
        if not _is_exact_int(target) or target not in (1, -1):
            return False, "INVALID_TARGET_SIGN", None

        terms.append(
            {
                "id": t_id,
                "P": p_str,
                "w": Fraction(w_raw[0], w_raw[1]),
                "target": target,
            }
        )

    return True, "", {"id": case_id, "n": n, "terms": terms}


def _pauli_words_commute(p1: str, p2: str) -> bool:
    """Checks if two Pauli strings commute (even number of anticommuting single-qubit positions)."""
    anticommute_count = 0
    for c1, c2 in zip(p1, p2):
        if c1 != "I" and c2 != "I" and c1 != c2:
            anticommute_count += 1
    return (anticommute_count % 2) == 0


def _symplectic_rank_gf2(vectors: list[list[int]]) -> int:
    """Computes row rank of vectors over GF(2)."""
    if not vectors:
        return 0
    rows = len(vectors)
    cols = len(vectors[0])
    aug = [row[:] for row in vectors]

    rank = 0
    for c in range(cols):
        piv = -1
        for r in range(rank, rows):
            if aug[r][c] == 1:
                piv = r
                break
        if piv == -1:
            continue
        aug[rank], aug[piv] = aug[piv], aug[rank]
        for r in range(rows):
            if r != rank and aug[r][c] == 1:
                for j in range(c, cols):
                    aug[r][j] ^= aug[rank][j]
        rank += 1
    return rank


def _build_exact_hamiltonian(n: int, terms: list[dict[str, Any]]) -> list[list[GaussianRational]]:
    """Builds the exact dense 2^n x 2^n Hamiltonian matrix over GaussianRational.

    H = sum_i (w_i / 2) * (I - s_i * P_i)
    """
    dim = 1 << n
    zero = GaussianRational(0)
    mat = [[zero for _ in range(dim)] for _ in range(dim)]

    for term in terms:
        w: Fraction = term["w"]
        s: int = term["target"]
        P: str = term["P"]
        half_w = w / 2

        for col in range(dim):
            # Compute action of P on basis state |col>
            row = col
            phase_pow = 0
            for q in range(n):
                bit = (col >> (n - 1 - q)) & 1
                c = P[q]
                if c == "I":
                    pass
                elif c == "Z":
                    if bit == 1:
                        phase_pow = (phase_pow + 2) % 4
                elif c == "X":
                    row ^= 1 << (n - 1 - q)
                elif c == "Y":
                    row ^= 1 << (n - 1 - q)
                    # Y|0> = i|1> (phase 1), Y|1> = -i|0> (phase 3)
                    phase_pow = (phase_pow + (3 if bit == 1 else 1)) % 4

            # Diagonal contribution from Identity in (I - s*P)/2:
            mat[col][col] = mat[col][col] + half_w

            # Pauli contribution: -s * (w/2) * P
            sign = -s * half_w
            if phase_pow == 0:
                coeff = GaussianRational(sign, 0)
            elif phase_pow == 1:
                coeff = GaussianRational(0, sign)
            elif phase_pow == 2:
                coeff = GaussianRational(-sign, 0)
            else:
                coeff = GaussianRational(0, -sign)

            mat[row][col] = mat[row][col] + coeff

    return mat


def _ldlt_hermitian_psd(mat: list[list[GaussianRational]], dim: int) -> tuple[bool, int, str]:
    """Computes exact LDL^H decomposition with diagonal pivoting on Hermitian matrix mat.

    Returns (is_psd, nullity, reason).
    """
    A = [row[:] for row in mat]
    nullity = 0

    for k in range(dim):
        # Diagonal pivoting: find row p with max diagonal entry
        best_p = k
        best_val = A[k][k].r
        for p in range(k + 1, dim):
            if A[p][p].r > best_val:
                best_val = A[p][p].r
                best_p = p

        # If best diagonal is negative, matrix has a strictly negative eigenvalue
        if best_val < 0:
            return False, 0, f"Negative pivot {best_val} at step {k}; matrix is not PSD"

        # If best diagonal is 0, for a PSD matrix the entire remaining submatrix must be zero
        if best_val == 0:
            for r in range(k, dim):
                if A[r][r].r < 0:
                    return False, 0, f"Negative pivot {A[r][r].r} in remaining null block"
                for c in range(r, dim):
                    if not A[r][c].is_zero():
                        return (
                            False,
                            0,
                            f"Non-zero off-diagonal entry {A[r][c]} in zero-diagonal block at ({r}, {c})",
                        )
            nullity += dim - k
            break

        # Swap rows and columns k and best_p
        if best_p != k:
            A[k], A[best_p] = A[best_p], A[k]
            for r in range(dim):
                A[r][k], A[r][best_p] = A[r][best_p], A[r][k]

        pivot_val = A[k][k].r
        row_k = [A[k][j] for j in range(dim)]
        col_k = [A[i][k] for i in range(dim)]

        # Eliminate rows below k using saved row_k and col_k
        for i in range(k + 1, dim):
            if col_k[i].is_zero():
                continue
            factor = col_k[i] / pivot_val
            for j in range(k + 1, dim):
                A[i][j] = A[i][j] - factor * row_k[j]
            A[i][k] = GaussianRational(0)
            A[k][i] = GaussianRational(0)

    return True, nullity, "OK"


# ---------------------------------------------------------------------------
# Primary Checker 2: Exact Spectral LDL^H
# ---------------------------------------------------------------------------


def verify_spectral_optimality(
    case: Mapping[str, Any], result: Mapping[str, Any]
) -> tuple[bool, str]:
    """Strictly validates a solver output against the input case using exact spectral analysis.

    Constructs dense operator H - E0*I over Q[i] and confirms:
    1. Positive semidefiniteness via exact LDL^H decomposition.
    2. Exact nullity (kernel dimension) == claimed degeneracy.

    Returns (True, "VALID") or (False, "FAIL: <reason>").
    Never raises an unhandled exception.
    """
    try:
        if not isinstance(result, Mapping):
            return False, f"FAIL: Result must be a JSON object, got {type(result).__name__}"

        status = result.get("status")
        if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
            return (
                False,
                f"FAIL: Invalid status: {status!r}; expected SOLVED, OUT_OF_SCOPE, or UNKNOWN",
            )

        is_valid_case, expected_refusal, case_data = _validate_case_structure(case)

        # -------------------------------------------------------------
        # Branch 1: Case is malformed or out of bounds -> expect UNKNOWN
        # -------------------------------------------------------------
        if not is_valid_case:
            if status != "UNKNOWN":
                return (
                    False,
                    f"FAIL: Case is malformed/out-of-bounds ({expected_refusal}) but solver reported {status!r}",
                )
            reported_refusal = result.get("refusal_code")
            if not isinstance(reported_refusal, str) or not reported_refusal:
                return False, "FAIL: Status is UNKNOWN but refusal_code is missing or empty"
            if reported_refusal != expected_refusal:
                return (
                    False,
                    f"FAIL: Expected refusal_code {expected_refusal!r}, got {reported_refusal!r}",
                )
            return True, "VALID: Refusal code verified on malformed/out-of-bounds case"

        # -------------------------------------------------------------
        # Case is valid and in-bounds
        # -------------------------------------------------------------
        assert case_data is not None
        n: int = case_data["n"]
        terms: list[dict[str, Any]] = case_data["terms"]
        term_map = {t["id"]: t for t in terms}

        if status == "UNKNOWN":
            return False, "FAIL: Case is well-formed and in-bounds, but solver reported UNKNOWN"

        # Check for anticommuting pairs in input
        first_anticommuting_pair: tuple[str, str] | None = None
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                if not _pauli_words_commute(terms[i]["P"], terms[j]["P"]):
                    pair = sorted([terms[i]["id"], terms[j]["id"]])
                    first_anticommuting_pair = (pair[0], pair[1])
                    break
            if first_anticommuting_pair is not None:
                break

        # -------------------------------------------------------------
        # Branch 2: OUT_OF_SCOPE
        # -------------------------------------------------------------
        if status == "OUT_OF_SCOPE":
            if first_anticommuting_pair is None:
                return False, "FAIL: All Hamiltonian terms commute; status OUT_OF_SCOPE is invalid"

            witness = result.get("witness")
            if not isinstance(witness, (list, tuple)) or len(witness) != 2:
                return (
                    False,
                    f"FAIL: OUT_OF_SCOPE witness must be a list of 2 string IDs, got {type(witness).__name__}",
                )

            w0, w1 = witness[0], witness[1]
            if not isinstance(w0, str) or not isinstance(w1, str):
                return False, "FAIL: Witness elements must be strings"
            if w0 >= w1:
                return (
                    False,
                    f"FAIL: Witness IDs must be strictly sorted lexicographically, got [{w0!r}, {w1!r}]",
                )
            if w0 not in term_map or w1 not in term_map:
                return False, f"FAIL: Witness IDs [{w0!r}, {w1!r}] not found in case terms"

            p0 = term_map[w0]["P"]
            p1 = term_map[w1]["P"]
            if _pauli_words_commute(p0, p1):
                return (
                    False,
                    f"FAIL: Witness terms {w0!r} ({p0}) and {w1!r} ({p1}) actually commute",
                )

            return True, "VALID: Non-commuting witness verified"

        # -------------------------------------------------------------
        # Branch 3: SOLVED
        # -------------------------------------------------------------
        if first_anticommuting_pair is not None:
            return False, (
                f"FAIL: Hamiltonian contains anticommuting terms "
                f"({first_anticommuting_pair[0]}, {first_anticommuting_pair[1]}), but status is SOLVED"
            )

        # 1. Wire format checks for SOLVED
        energy_raw = result.get("energy")
        if (
            not isinstance(energy_raw, (list, tuple))
            or len(energy_raw) != 2
            or not _is_exact_int(energy_raw[0])
            or not _is_exact_int(energy_raw[1])
            or energy_raw[1] <= 0
        ):
            return (
                False,
                f"FAIL: Invalid energy field: {energy_raw!r}; expected [num, den] with den > 0",
            )

        # Coprime check
        gcd_val = math.gcd(abs(energy_raw[0]), energy_raw[1])
        if gcd_val != 1:
            return False, f"FAIL: Energy fraction {energy_raw!r} is unreduced (gcd={gcd_val})"
        reported_energy = Fraction(energy_raw[0], energy_raw[1])

        degeneracy_raw = result.get("degeneracy")
        if not _is_exact_int(degeneracy_raw) or degeneracy_raw <= 0:
            return False, f"FAIL: Invalid degeneracy: {degeneracy_raw!r}; must be positive integer"
        reported_degeneracy: int = degeneracy_raw

        # Additional certificate wire checks
        basis_raw = result.get("basis")
        if not isinstance(basis_raw, (list, tuple)) or any(
            not isinstance(b, str) for b in basis_raw
        ):
            return (
                False,
                f"FAIL: Basis must be a list of string term IDs, got {type(basis_raw).__name__}",
            )
        if len(set(basis_raw)) != len(basis_raw):
            return False, "FAIL: Basis contains duplicate generator IDs"
        for b_id in basis_raw:
            if b_id not in term_map:
                return False, f"FAIL: Basis generator ID {b_id!r} not found in case terms"

        k = len(basis_raw)
        if k > n:
            return False, f"FAIL: Basis length {k} exceeds number of qubits {n}"

        # Basis commutativity
        for i in range(k):
            for j in range(i + 1, k):
                if not _pauli_words_commute(
                    term_map[basis_raw[i]]["P"], term_map[basis_raw[j]]["P"]
                ):
                    return (
                        False,
                        f"FAIL: Basis generators {basis_raw[i]} and {basis_raw[j]} anticommute",
                    )

        # Symplectic linear independence over GF(2)
        sym_vecs = []
        for b_id in basis_raw:
            p_str = term_map[b_id]["P"]
            x_bits = [1 if c in ("X", "Y") else 0 for c in p_str]
            z_bits = [1 if c in ("Z", "Y") else 0 for c in p_str]
            sym_vecs.append(x_bits + z_bits)
        if _symplectic_rank_gf2(sym_vecs) != k:
            return False, f"FAIL: Basis generators are linearly dependent (rank != count {k})"

        decomp_raw = result.get("decomposition")
        if not isinstance(decomp_raw, (list, tuple)):
            return False, f"FAIL: Decomposition must be a list, got {type(decomp_raw).__name__}"
        if len(decomp_raw) != len(terms):
            return False, f"FAIL: Decomposition count {len(decomp_raw)} != terms count {len(terms)}"

        seen_d_ids: set[str] = set()
        for d in decomp_raw:
            if not isinstance(d, Mapping):
                return False, f"FAIL: Decomposition entry is not a dict: {type(d).__name__}"
            d_id = d.get("id")
            if not isinstance(d_id, str) or d_id not in term_map:
                return False, f"FAIL: Decomposition has invalid or unknown term ID: {d_id!r}"
            if d_id in seen_d_ids:
                return False, f"FAIL: Duplicate decomposition entry for term ID: {d_id!r}"
            seen_d_ids.add(d_id)

            mask = d.get("mask")
            if not _is_exact_int(mask) or mask < 0 or mask >= (1 << k):
                return False, f"FAIL: Mask {mask!r} out of bounds for k={k} on term {d_id!r}"
            phase = d.get("phase")
            if not _is_exact_int(phase) or phase not in (1, -1):
                return False, f"FAIL: Phase {phase!r} not in {{+1, -1}} on term {d_id!r}"

        # Verify algebraic consistency of decomposition with claimed basis
        single_mul = {
            ("I", "I"): (0, "I"),
            ("I", "X"): (0, "X"),
            ("I", "Y"): (0, "Y"),
            ("I", "Z"): (0, "Z"),
            ("X", "I"): (0, "X"),
            ("X", "X"): (0, "I"),
            ("X", "Y"): (1, "Z"),
            ("X", "Z"): (3, "Y"),
            ("Y", "I"): (0, "Y"),
            ("Y", "X"): (3, "Z"),
            ("Y", "Y"): (0, "I"),
            ("Y", "Z"): (1, "X"),
            ("Z", "I"): (0, "Z"),
            ("Z", "X"): (1, "Y"),
            ("Z", "Y"): (3, "X"),
            ("Z", "Z"): (0, "I"),
        }
        for d in decomp_raw:
            d_id = d["id"]
            mask = d["mask"]
            phase = d["phase"]
            exp_p = 0 if phase == 1 else 2
            curr_w = "I" * n
            curr_p = 0
            for j in range(k):
                if (mask >> j) & 1:
                    gen_w = term_map[basis_raw[j]]["P"]
                    res_w_list = []
                    for c1, c2 in zip(curr_w, gen_w):
                        p_step, c_res = single_mul[(c1, c2)]
                        curr_p = (curr_p + p_step) % 4
                        res_w_list.append(c_res)
                    curr_w = "".join(res_w_list)
            expected_w = term_map[d_id]["P"]
            if curr_p != exp_p or curr_w != expected_w:
                return False, (
                    f"FAIL: Decomposition algebraic mismatch for term {d_id!r}: "
                    f"expected phase {phase} and word {expected_w}, got phase i^{curr_p} and {curr_w}"
                )

        minimizers_raw = result.get("minimizers")
        if not isinstance(minimizers_raw, (list, tuple)):
            return False, "FAIL: Minimizers must be a list of non-negative integers"
        min_list: list[int] = []
        for m in minimizers_raw:
            if not _is_exact_int(m) or m < 0 or m >= (1 << k):
                return False, f"FAIL: Minimizer {m!r} is not an integer bitmask in [0, 2^{k}-1]"
            min_list.append(m)
        if len(set(min_list)) != len(min_list):
            return False, "FAIL: Minimizers list contains duplicates"
        if len(min_list) * (1 << (n - k)) != reported_degeneracy:
            return False, (
                f"FAIL: Inconsistent certificate: len(minimizers)={len(min_list)} * 2^(n-k)={1 << (n - k)} "
                f"!= degeneracy={reported_degeneracy}"
            )

        # Verify that each submitted minimizer bitmask achieves reported ground energy E_0
        for m in min_list:
            m_energy = Fraction(0)
            evals = [-1 if ((m >> j) & 1) else 1 for j in range(k)]
            for d in decomp_raw:
                t_id = d["id"]
                mask = d["mask"]
                sigma = d["phase"]
                target = term_map[t_id]["target"]
                w = term_map[t_id]["w"]
                term_eig = sigma
                for j in range(k):
                    if (mask >> j) & 1:
                        term_eig *= evals[j]
                if term_eig != target:
                    m_energy += w
            if m_energy != reported_energy:
                return (
                    False,
                    f"FAIL: Minimizer mask {m} has energy {m_energy} != ground energy {reported_energy}",
                )

        # 2. Construct exact dense Hamiltonian H over Q[i]
        H = _build_exact_hamiltonian(n, terms)
        dim = 1 << n

        # Construct A = H - E0 * I
        for idx in range(dim):
            H[idx][idx] = H[idx][idx] - reported_energy

        # 3. Exact LDL^H decomposition with diagonal pivoting
        is_psd, nullity, reason = _ldlt_hermitian_psd(H, dim)
        if not is_psd:
            return False, f"FAIL: Spectral LDL^H check failed: {reason}"

        # 4. Verify kernel dimension == reported degeneracy
        if nullity != reported_degeneracy:
            return False, (
                f"FAIL: Exact spectral kernel dimension {nullity} != claimed degeneracy {reported_degeneracy}"
            )

        return True, f"VALID: Spectral LDL^H confirmed PSD with exact kernel dimension {nullity}"

    except Exception as exc:
        return False, f"FAIL: Unhandled exception during spectral checker: {exc}"


# ---------------------------------------------------------------------------
# Secondary Numeric Eigensolver (NumPy)
# ---------------------------------------------------------------------------

_SIGMA_FLOAT = {
    "I": np.array([[1.0, 0.0], [0.0, 1.0]], dtype=complex) if HAS_NUMPY else None,
    "X": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex) if HAS_NUMPY else None,
    "Y": np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex) if HAS_NUMPY else None,
    "Z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex) if HAS_NUMPY else None,
}


def secondary_numeric_check(case: Mapping[str, Any], result: Mapping[str, Any]) -> tuple[bool, str]:
    """Secondary NumPy floating-point eigensolver reference check.

    Labelled SECONDARY_NUMERIC. Restricted to n <= 8.
    Verifies that ground energy and eigenspace dimension agree with
    numerical diagonalization within float tolerance.
    """
    if not HAS_NUMPY:
        return True, "SECONDARY_NUMERIC: NumPy not installed; skipped"

    try:
        if not isinstance(result, Mapping):
            return (
                False,
                f"SECONDARY_NUMERIC: Result is not a JSON object ({type(result).__name__})",
            )

        if result.get("status") != "SOLVED":
            return True, "SECONDARY_NUMERIC: Case not solved; skipped"

        is_valid, _, case_data = _validate_case_structure(case)
        if not is_valid or case_data is None:
            return False, "SECONDARY_NUMERIC: Case structure invalid"

        n = case_data["n"]
        terms = case_data["terms"]
        dim = 1 << n

        h_mat = np.zeros((dim, dim), dtype=complex)
        eye = np.eye(dim, dtype=complex)

        for t in terms:
            p_str = t["P"]
            mat = _SIGMA_FLOAT[p_str[0]]
            for c in p_str[1:]:
                mat = np.kron(mat, _SIGMA_FLOAT[c])
            proj = 0.5 * (eye - t["target"] * mat)
            h_mat += float(t["w"]) * proj

        eigenvalues = np.sort(np.linalg.eigvalsh(h_mat))
        min_eig = float(eigenvalues[0])

        energy_raw = result.get("energy")
        if (
            not isinstance(energy_raw, (list, tuple))
            or len(energy_raw) != 2
            or not _is_exact_int(energy_raw[0])
            or not _is_exact_int(energy_raw[1])
            or energy_raw[1] <= 0
        ):
            return False, f"SECONDARY_NUMERIC: Invalid energy field: {energy_raw!r}"

        reported_energy_float = float(energy_raw[0]) / float(energy_raw[1])
        deg_raw = result.get("degeneracy")
        if not _is_exact_int(deg_raw) or deg_raw <= 0:
            return False, f"SECONDARY_NUMERIC: Invalid degeneracy: {deg_raw!r}"
        reported_deg = int(deg_raw)

        if abs(min_eig - reported_energy_float) > 1e-6:
            return (
                False,
                f"SECONDARY_NUMERIC: min_eig {min_eig:.6f} != reported {reported_energy_float:.6f}",
            )

        spectral_norm = float(np.max(np.abs(eigenvalues)))
        noise_floor = max(1e-6, 1e-12 * spectral_norm)
        numerical_deg = int(np.sum(eigenvalues - min_eig < noise_floor))

        if numerical_deg != reported_deg:
            return (
                False,
                f"SECONDARY_NUMERIC: numerical degeneracy {numerical_deg} != reported {reported_deg}",
            )

        return True, f"SECONDARY_NUMERIC: Verified min_eig={min_eig:.6f}, deg={numerical_deg}"
    except Exception as exc:
        return False, f"SECONDARY_NUMERIC: Failed with error: {exc}"
