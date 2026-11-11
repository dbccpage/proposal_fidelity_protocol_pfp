"""Host-derived characteristic-polynomial verification and certified context artifact.

Derives the characteristic polynomial det(lambda*I - H(J,Delta,K)) solely from the
admitted public affine Hamiltonian matrix representation (hamiltonian_artifact.py),
using exact rational arithmetic (fractions.Fraction) and explicit degree bounds:
  - Degree 4 in lambda (monic leading coefficient 1)
  - Per-variable degree <= 4 in each of J, Delta, K
  - Total degree in (J, Delta, K) <= 4

Verification:
  The polynomial is verified over the 125-point rational Cartesian product grid:
    {-2, -1, 0, 1, 2}^3 in Q^3
  via the source-bound native Rust sidecar (native_sidecar.py).
  By the multi-variable polynomial identity theorem, two polynomials with per-variable
  degree <= 4 agreeing on a 5x5x5 distinct point grid are identically equal in
  Q[lambda, J, Delta, K].

Wire Format:
  All polynomials are normalized through pure value-preserving transport (charpoly_wire.py).

Carrier Assumptions:
  - Domain: Rational field Q represented by exact fractions.Fraction.
  - No floating-point or non-finite numbers are admitted.
  - Coordinate basis: computational basis (00, 01, 10, 11).

Final-Answer Limitations:
  - This polynomial certifies intermediate det(lambda*I - H) ONLY.
  - It does NOT certify eigenvalues, eigenvectors, spectral projectors,
    thermal states, partition functions, dynamics, or time evolution.
  - It does NOT certify full QM solutions or final-answer mathematical accuracy.
  - final_answer_certified is always False.
  - Zero certificates are manufactured from evaluator constants or private answers.
"""
from __future__ import annotations

import functools
import hashlib
import json
import re
from copy import deepcopy
from fractions import Fraction
from itertools import permutations
from pathlib import Path
from typing import Any

import charpoly_wire as wire
import hamiltonian_artifact as pauli
import native_sidecar as sidecar
import qm_native_charpoly as bridge

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# Canonical constants and specifications
SCHEMA = "pfp.qm-host-charpoly.certified-context.v1"
COMPACT_CHAR_BUDGET = 1300  # raised from 1,200 to carry the native receipt digest
COMPACT_SCHEMA = "pfp.qm-host-charpoly.compact-certificate.v1"
CANDIDATE_SCHEMA = "pfp.qm-affine-charpoly-candidate.v1"
SOLVER_CONTEXT_SCHEMA = "pfp.charpoly-workflow.solver-context.v1"

SUPPORTED_SEED_SHA256 = "9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7"
PARAMETERS = ("J", "Delta", "K")
BASIS = ("00", "01", "10", "11")
DIMENSION = 4
DEGREE_BOUND_LAMBDA = 4
DEGREE_BOUND_PER_VARIABLE = 4
GRID_NODES = (-2, -1, 0, 1, 2)
GRID_POINTS = 125

THEOREM = (
    "Per-variable degree <= 4 in (J, Delta, K) and degree 4 in lambda, agreeing "
    "on Cartesian grid {-2, -1, 0, 1, 2}^3 (125 points) certifies exact polynomial "
    "identity det(lambda*I - H(J,Delta,K)) in Q[lambda, J, Delta, K]."
)

CLAIM_SCOPE = "intermediate_characteristic_polynomial_det(lambda*I - H)"
UNCERTIFIED_OBLIGATIONS = (
    "eigenvalues/spectrum branches",
    "eigenvectors/projectors",
    "thermal states/partition functions",
    "dynamics/time evolution",
    "final answer mathematical accuracy",
)
COMPACT_LIMITATION_NOTICE = "Intermediate det(lambda*I - H) only; not a full QM solution."

# Pinned source dependencies
PINNED_SOURCES = {
    "hamiltonian_artifact.py": "bf28b8371f11d2ac34256d3699a1653a2e44562e9d7b4a60e12221c750938925",
    "charpoly_wire.py": "c6e2733092d8224d1e2303b4a988c1d8735829d10bbb790a97423d451f6c5b50",
    "native_sidecar.py": "67feada49e7e73a45897c81b1353aed7251964ed43bb463767cc2434b9c0fc3c",
    "qm_native_charpoly.py": "73af367aa213f9822fe63e4373773914172f65735b652e2376e1edfad786f394",
}

# Catalog of standardized failure states
FAILURE_STATES = {
    "UNREGISTERED_SEED": "The supplied seed SHA-256 does not match the supported benchmark seed.",
    "SEED_HASH_MISMATCH": "The seed SHA-256 in artifact headers contradicts the request seed.",
    "PUBLIC_INPUT_MISMATCH": "The Hamiltonian coefficient matrices do not match the admitted public artifact.",
    "MATRIX_SHAPE_MISMATCH": "The Hamiltonian matrices are not 4x4 or have invalid affine parameter count.",
    "MALFORMED_RATIONAL": "Rational coefficients fail the canonical wire format, range, or bit limits.",
    "DUPLICATE_POWERS": "Sparse monomial representation contains duplicate exponent vectors before zero removal.",
    "NONMONIC_LEADING_COEFFICIENT": "The degree-4 characteristic polynomial leading coefficient is not 1.",
    "DEGREE_LIMIT_EXCEEDED": "Polynomial exceeds degree 4 in lambda or per-variable degree 4 in (J, Delta, K).",
    "GRID_ALIASING_DETECTED": "Polynomial degree aliasing or divergence outside the 125-point Cartesian grid.",
    "STALE_SOURCE_HASH": "Pinned source dependencies have been modified or tampered with.",
    "SWAPPED_BINARY": "Native sidecar binary hash does not match the verified build custody receipt.",
    "CONTRADICTION_FINAL_ANSWER_CLAIM": "Artifact improperly claims to certify full QM solution or eigenvectors.",
    "PROMPT_INJECTION_DETECTED": "Untrusted prompt injection pattern detected in artifact metadata or context.",
    "NONCOMMUTING_SUBSTITUTION": "Parameters were substituted in non-standard order or non-commuting form.",
    "FORGED_CERTIFICATE": "Artifact claims certification without authentic native sidecar verification.",
    "MISSING_NATIVE_EVIDENCE": "No native verification receipt backs the claimed certification, or it could not be re-executed.",
}

# Prompt injection signature patterns
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"certif(y|ied)\s+(this\s+as\s+)?(full|complete)\s+(solution|answer)", re.IGNORECASE),
    re.compile(r"override\s+verification", re.IGNORECASE),
    re.compile(r"<system>", re.IGNORECASE),
]


class HostCharpolyError(ValueError):
    """Base error for host characteristic polynomial operations."""


class HostCharpolyRefusalError(HostCharpolyError):
    """Structured refusal with a standardized failure state code."""

    def __init__(self, code: str, details: str | None = None) -> None:
        self.code = code
        self.details = details or FAILURE_STATES.get(code, code)
        super().__init__(f"{self.code}: {self.details}")


# Backward-compatible alias
HostCharpolyRefusal = HostCharpolyRefusalError


# ---------------------------------------------------------------------------
# Exact Symbolic Polynomial Arithmetic in Q[lambda, J, Delta, K]
# ---------------------------------------------------------------------------

Exponent = tuple[int, int, int, int]
Polynomial = dict[Exponent, Fraction]


def poly_add(a: Polynomial, b: Polynomial) -> Polynomial:
    """Exact addition of two multivariate polynomials."""
    result = dict(a)
    for exponent, coeff in b.items():
        new_val = result.get(exponent, Fraction(0)) + coeff
        if new_val != 0:
            result[exponent] = new_val
        elif exponent in result:
            del result[exponent]
    return result


def poly_sub(a: Polynomial, b: Polynomial) -> Polynomial:
    """Exact subtraction of two multivariate polynomials."""
    result = dict(a)
    for exponent, coeff in b.items():
        new_val = result.get(exponent, Fraction(0)) - coeff
        if new_val != 0:
            result[exponent] = new_val
        elif exponent in result:
            del result[exponent]
    return result


def poly_scale(a: Polynomial, scalar: Fraction | int) -> Polynomial:
    """Exact scalar multiplication of a multivariate polynomial."""
    q = Fraction(scalar)
    if q == 0:
        return {}
    return {exp: coeff * q for exp, coeff in a.items() if coeff * q != 0}


def poly_mul(a: Polynomial, b: Polynomial) -> Polynomial:
    """Exact multiplication of two multivariate polynomials."""
    result: dict[Exponent, Fraction] = {}
    for exp_a, coeff_a in a.items():
        for exp_b, coeff_b in b.items():
            exp = (
                exp_a[0] + exp_b[0],
                exp_a[1] + exp_b[1],
                exp_a[2] + exp_b[2],
                exp_a[3] + exp_b[3],
            )
            val = result.get(exp, Fraction(0)) + coeff_a * coeff_b
            if val != 0:
                result[exp] = val
            elif exp in result:
                del result[exp]
    return result


def det_leibniz(matrix: list[list[Polynomial]]) -> Polynomial:
    """Exact Leibniz permutation determinant expansion: det(M) = sum sgn(p) * prod M[i, p(i)]."""
    n = len(matrix)
    det: Polynomial = {}
    for p in permutations(range(n)):
        inv = sum(p[i] > p[j] for i in range(n) for j in range(i + 1, n))
        term: Polynomial = {(0, 0, 0, 0): Fraction((-1) ** inv)}
        for r, c in enumerate(p):
            term = poly_mul(term, matrix[r][c])
        det = poly_add(det, term)
    return det


def det_laplace(matrix: list[list[Polynomial]]) -> Polynomial:
    """Exact Laplace minor expansion along row 0, independent of Leibniz permutation loop."""
    n = len(matrix)
    if n == 1:
        return matrix[0][0]
    if n == 2:
        return poly_sub(
            poly_mul(matrix[0][0], matrix[1][1]),
            poly_mul(matrix[0][1], matrix[1][0]),
        )
    det: Polynomial = {}
    for c in range(n):
        entry = matrix[0][c]
        if not entry:
            continue
        submatrix = [[matrix[r][col] for col in range(n) if col != c] for r in range(1, n)]
        sub_det = det_laplace(submatrix)
        term = poly_mul(entry, sub_det)
        if c % 2 == 1:
            term = poly_scale(term, -1)
        det = poly_add(det, term)
    return det


# ---------------------------------------------------------------------------
# Exact Tensor Lagrange Interpolation & Scalar Determinant
# ---------------------------------------------------------------------------

def lagrange_basis_1d(
    nodes: list[Fraction | int] | tuple[Fraction | int, ...] = GRID_NODES,
    i: int = 0,
) -> dict[int, Fraction]:
    """Exact 1D Lagrange polynomial coefficients for node i over the rational field Q.

    L_i(x) = prod_{j != i} (x - x_j) / (x_i - x_j)

    Returns a dictionary mapping polynomial degree to exact Fraction coefficient.
    Guarantees:
      - Kronecker delta: L_i(x_j) == delta_{ij}
      - Partition of unity: sum_i L_i(x) == 1
    """
    n = len(nodes)
    if not (0 <= i < n):
        raise ValueError(f"Index i={i} out of bounds for nodes length {n}")

    frac_nodes = [Fraction(x) for x in nodes]
    x_i = frac_nodes[i]

    denom = Fraction(1)
    for j, x_j in enumerate(frac_nodes):
        if j != i:
            diff = x_i - x_j
            if diff == 0:
                raise ValueError(f"Duplicate node value detected at indices {i} and {j}: {x_i}")
            denom *= diff

    poly: dict[int, Fraction] = {0: Fraction(1)}
    for j, x_j in enumerate(frac_nodes):
        if j != i:
            new_poly: dict[int, Fraction] = {}
            for d, c in poly.items():
                new_poly[d + 1] = new_poly.get(d + 1, Fraction(0)) + c
                new_poly[d] = new_poly.get(d, Fraction(0)) - c * x_j
            poly = new_poly

    return {d: c / denom for d, c in poly.items() if c != 0}


def eval_scalar_det_4x4(matrix: list[list[Fraction | int]]) -> Fraction:
    """Exact scalar determinant of a 4x4 rational matrix using cross-verified Leibniz and Laplace engines."""
    if len(matrix) != 4 or any(len(row) != 4 for row in matrix):
        raise ValueError(f"Matrix shape must be 4x4, got {len(matrix)}x{len(matrix[0]) if matrix else 0}")

    frac_matrix = [[Fraction(x) for x in row] for row in matrix]

    # Engine 1: Leibniz permutation formula sum sgn(p) * prod M[r, p(r)]
    det_leibniz_val = Fraction(0)
    for p in permutations(range(4)):
        inv = sum(p[i] > p[j] for i in range(4) for j in range(i + 1, 4))
        sign = -1 if inv % 2 else 1
        prod = Fraction(sign)
        for r, c in enumerate(p):
            prod *= frac_matrix[r][c]
        det_leibniz_val += prod

    # Engine 2: Laplace cofactor expansion along row 0
    def _laplace_2x2(m: list[list[Fraction]]) -> Fraction:
        return m[0][0] * m[1][1] - m[0][1] * m[1][0]

    def _laplace_3x3(m: list[list[Fraction]]) -> Fraction:
        res = Fraction(0)
        for col in range(3):
            sub = [[m[r][c] for c in range(3) if c != col] for r in range(1, 3)]
            sign = -1 if col % 2 else 1
            res += sign * m[0][col] * _laplace_2x2(sub)
        return res

    det_laplace_val = Fraction(0)
    for col in range(4):
        sub = [[frac_matrix[r][c] for c in range(4) if c != col] for r in range(1, 4)]
        sign = -1 if col % 2 else 1
        det_laplace_val += sign * frac_matrix[0][col] * _laplace_3x3(sub)

    if det_leibniz_val != det_laplace_val:
        raise HostCharpolyError(
            f"Scalar determinant engines diverged: Leibniz={det_leibniz_val}, Laplace={det_laplace_val}"
        )

    return det_leibniz_val


def interpolate_trivariate_charpoly(
    matrices: dict[str, list[list[Fraction]]],
    nodes: tuple[int, ...] | list[int] = GRID_NODES,
    K_val: Fraction | int = Fraction(0),
) -> dict[tuple[int, int, int], Fraction]:
    """Exact 3D tensor product Lagrange interpolation of trivariate charpoly P(lambda; g_1, g_2) at fixed K.

    Evaluates 125 scalar determinants det(lambda_k*I - H(g_{1,i}, g_{2,j}, K_val)) over nodes^3
    and reconstructs the unique polynomial in Q[lambda, g_1, g_2].
    For K_val = 0, identically reconstructs:
      P(lambda; g_1, g_2) = lambda^4 - (4*g_1^2 + 4*g_2^2)*lambda^2
    """
    frac_k = Fraction(K_val)
    n_nodes = len(nodes)
    basis = [lagrange_basis_1d(nodes, idx) for idx in range(n_nodes)]

    reconstructed: dict[tuple[int, int, int], Fraction] = {}
    for i, g1 in enumerate(nodes):
        for j, g2 in enumerate(nodes):
            for k, lam in enumerate(nodes):
                mat = [[Fraction(0)] * 4 for _ in range(4)]
                for r in range(4):
                    for c in range(4):
                        entry = (
                            -matrices["constant"][r][c]
                            - Fraction(g1) * matrices["J"][r][c]
                            - Fraction(g2) * matrices["Delta"][r][c]
                            - frac_k * matrices["K"][r][c]
                        )
                        if r == c:
                            entry += Fraction(lam)
                        mat[r][c] = entry
                det_val = eval_scalar_det_4x4(mat)
                if det_val == 0:
                    continue
                for d_lam, c_lam in basis[k].items():
                    for d_g1, c_g1 in basis[i].items():
                        for d_g2, c_g2 in basis[j].items():
                            coeff = det_val * c_lam * c_g1 * c_g2
                            key = (d_lam, d_g1, d_g2)
                            reconstructed[key] = reconstructed.get(key, Fraction(0)) + coeff

    return {k: v for k, v in reconstructed.items() if v != 0}


def interpolate_charpoly_from_grid(
    matrices: dict[str, list[list[Fraction]]],
    nodes: tuple[int, ...] | list[int] = GRID_NODES,
    native_host: Any | None = None,
) -> dict[tuple[int, int, int, int], Fraction]:
    """Exact 3D tensor product Lagrange interpolation of the full 4-variable charpoly P(lambda, J, Delta, K).

    Evaluates 125 grid nodes on (J, Delta, K) in nodes^3.
    Replays either through native_sidecar.NativeHost or exact host scalar evaluation.
    Reconstructs the full 4-variable characteristic polynomial identically matching
    det_leibniz and det_laplace.
    """
    n_nodes = len(nodes)
    basis = [lagrange_basis_1d(nodes, idx) for idx in range(n_nodes)]

    observed_coeffs: list[list[Fraction]] = []

    if native_host is not None:
        grid_matrices = []
        for j in nodes:
            for d in nodes:
                for k in nodes:
                    mat_rows = []
                    for r in range(4):
                        row = []
                        for c in range(4):
                            val = (
                                matrices["constant"][r][c]
                                + Fraction(j) * matrices["J"][r][c]
                                + Fraction(d) * matrices["Delta"][r][c]
                                + Fraction(k) * matrices["K"][r][c]
                            )
                            row.append(str(val))
                        mat_rows.append(row)
                    grid_matrices.append(mat_rows)
        observed_coeffs, _custody = native_host.compute(grid_matrices)
    else:
        for j in nodes:
            for d in nodes:
                for k in nodes:
                    h_mat = [
                        [
                            matrices["constant"][r][c]
                            + Fraction(j) * matrices["J"][r][c]
                            + Fraction(d) * matrices["Delta"][r][c]
                            + Fraction(k) * matrices["K"][r][c]
                            for c in range(4)
                        ]
                        for r in range(4)
                    ]
                    det_values = []
                    for lam in nodes:
                        char_mat = [
                            [
                                (Fraction(lam) if r == c else Fraction(0)) - h_mat[r][c]
                                for c in range(4)
                            ]
                            for r in range(4)
                        ]
                        det_values.append(eval_scalar_det_4x4(char_mat))
                    lam_coeffs = [Fraction(0)] * 5
                    for l_idx, det_v in enumerate(det_values):
                        for deg, coeff in basis[l_idx].items():
                            lam_coeffs[deg] += det_v * coeff
                    observed_coeffs.append(lam_coeffs)

    reconstructed_4var: dict[tuple[int, int, int, int], Fraction] = {}
    idx = 0
    for i, _j_val in enumerate(nodes):
        for j, _d_val in enumerate(nodes):
            for k, _k_val in enumerate(nodes):
                row = observed_coeffs[idx]
                idx += 1
                for m, c_val in enumerate(row):
                    if c_val == 0:
                        continue
                    for dj, cj in basis[i].items():
                        for dd, cd in basis[j].items():
                            for dk, ck in basis[k].items():
                                coeff = c_val * cj * cd * ck
                                exp = (m, dj, dd, dk)
                                reconstructed_4var[exp] = reconstructed_4var.get(exp, Fraction(0)) + coeff

    return {k: v for k, v in reconstructed_4var.items() if v != 0}


def _format_monomial_term(powers: tuple[int, ...] | list[int], coeff: Fraction, var_names: tuple[str, ...]) -> str:
    parts = []
    if coeff != 1 and coeff != -1:
        parts.append(str(coeff))
    elif coeff == -1 and not any(p > 0 for p in powers):
        parts.append("-1")
    for p, v in zip(powers, var_names):
        if p == 1:
            parts.append(v)
        elif p > 1:
            parts.append(f"{v}^{p}")
    if not parts:
        return "1"
    if coeff == -1 and len(parts) > 0 and parts[0] != "-1":
        return "-" + "*".join(parts)
    return "*".join(parts)


def format_charpoly_standard_form(
    poly: dict[tuple[int, ...], Fraction],
    variables: tuple[str, ...] = ("lambda", "J", "Delta", "K"),
) -> str:
    """Format characteristic polynomial in standard descending degree form."""
    lam_var = variables[0]
    param_vars = variables[1:]
    by_lam: dict[int, list[tuple[tuple[int, ...], Fraction]]] = {}
    for exp, coeff in poly.items():
        lam_p = exp[0]
        p_powers = exp[1:]
        by_lam.setdefault(lam_p, []).append((p_powers, coeff))

    parts: list[tuple[str, str]] = []
    for lam_p in sorted(by_lam.keys(), reverse=True):
        p_terms = by_lam[lam_p]
        p_terms.sort(key=lambda item: (-sum(item[0]), *(-item[0][i] for i in range(len(item[0])))))

        if len(p_terms) == 1 and all(p == 0 for p in p_terms[0][0]):
            c = p_terms[0][1]
            if c == 1 and lam_p > 0:
                t = f"{lam_var}^{lam_p}" if lam_p > 1 else lam_var
                parts.append(("+", t))
                continue
            elif c == -1 and lam_p > 0:
                t = f"{lam_var}^{lam_p}" if lam_p > 1 else lam_var
                parts.append(("-", t))
                continue

        all_negative = all(c < 0 for _, c in p_terms)
        factor_sign = "-" if all_negative else "+"

        factor_parts = []
        for i, (p_pow, c) in enumerate(p_terms):
            effective_c = -c if all_negative else c
            abs_c = abs(effective_c)
            sign = "-" if effective_c < 0 else "+"
            t_str = _format_monomial_term(p_pow, abs_c, param_vars)
            if i == 0:
                factor_parts.append(("-" if sign == "-" else "") + t_str)
            else:
                factor_parts.append(f"{sign} {t_str}")

        inner = " ".join(factor_parts)
        bracketed = f"({inner})" if len(p_terms) > 1 else inner

        if lam_p == 0:
            term_full = bracketed
        else:
            lam_s = f"*{lam_var}^{lam_p}" if lam_p > 1 else f"*{lam_var}"
            term_full = f"{bracketed}{lam_s}"

        parts.append((factor_sign, term_full))

    res = ""
    for i, (sign, t) in enumerate(parts):
        if i == 0:
            res += ("-" if sign == "-" else "") + t
        else:
            res += f" {sign} {t}"
    return res


# ---------------------------------------------------------------------------
# Admitted Public Matrix Parsing & Polynomial Derivation
# ---------------------------------------------------------------------------

def _parse_artifact_text(artifact_input: str | dict[str, Any] | None, seed_hash: str) -> str:
    """Convert artifact input to checked JSON string representation."""
    if artifact_input is None:
        artifact_dict = pauli.public_input_artifact(seed_hash)
        return json.dumps(artifact_dict, separators=(",", ":"))
    if isinstance(artifact_input, dict):
        return json.dumps(artifact_input, separators=(",", ":"))
    if isinstance(artifact_input, str):
        return artifact_input
    raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", "artifact_input must be string or dict")


def _parse_matrix_rows(name: str, rows: Any) -> list[list[Fraction]]:
    """Validate 4x4 matrix dimensions and canonical rational entries."""
    if type(rows) is not list or len(rows) != DIMENSION:
        raise HostCharpolyRefusalError("MATRIX_SHAPE_MISMATCH", f"{name} matrix row count != {DIMENSION}")
    parsed_rows: list[list[Fraction]] = []
    for r, row in enumerate(rows):
        if type(row) is not list or len(row) != DIMENSION:
            raise HostCharpolyRefusalError("MATRIX_SHAPE_MISMATCH", f"{name} row {r} length != {DIMENSION}")
        converted_row: list[Fraction] = []
        for c, text in enumerate(row):
            if type(text) is not str:
                raise HostCharpolyRefusalError("MALFORMED_RATIONAL", f"entry {name}[{r}][{c}] not a string")
            try:
                q = Fraction(text)
            except (ValueError, ZeroDivisionError) as exc:
                raise HostCharpolyRefusalError("MALFORMED_RATIONAL", f"entry {name}[{r}][{c}]: {exc}") from None
            if f"{q.numerator}/{q.denominator}" != text:
                raise HostCharpolyRefusalError("MALFORMED_RATIONAL", f"entry {name}[{r}][{c}] non-canonical")
            converted_row.append(q)
        parsed_rows.append(converted_row)
    return parsed_rows


def admit_public_matrices(
    seed_hash: str = SUPPORTED_SEED_SHA256,
    artifact_input: str | dict[str, Any] | None = None,
) -> dict[str, list[list[Fraction]]]:
    """Ingest, validate, and convert admitted public Hamiltonian coefficient matrices."""
    if type(seed_hash) is not str or seed_hash != SUPPORTED_SEED_SHA256:
        raise HostCharpolyRefusalError("UNREGISTERED_SEED")

    artifact_text = _parse_artifact_text(artifact_input, seed_hash)
    checked = pauli.check_artifact(artifact_text, seed_hash)
    if not checked["accepted"] or checked["errors"] or checked["mismatches"]:
        error_msg = checked["errors"][0] if checked["errors"] else "matrix entries mismatch Pauli tensor products"
        raise HostCharpolyRefusalError("PUBLIC_INPUT_MISMATCH", error_msg)

    matrices_json = checked["canonical_candidate"]["coefficient_matrices"]
    parsed: dict[str, list[list[Fraction]]] = {
        "constant": [[Fraction(0)] * DIMENSION for _ in range(DIMENSION)]
    }

    for name in PARAMETERS:
        if name not in matrices_json:
            raise HostCharpolyRefusalError("MATRIX_SHAPE_MISMATCH", f"missing parameter matrix: {name}")
        parsed[name] = _parse_matrix_rows(name, matrices_json[name])

    return parsed


def build_characteristic_matrix(
    matrices: dict[str, list[list[Fraction]]],
) -> list[list[Polynomial]]:
    """Build symbolic matrix entries for lambda*I - H(J, Delta, K)."""
    n = DIMENSION
    matrix: list[list[Polynomial]] = []
    for r in range(n):
        row: list[Polynomial] = []
        for c in range(n):
            entry: Polynomial = {}
            if r == c:
                entry[(1, 0, 0, 0)] = Fraction(1)
            const_val = matrices["constant"][r][c]
            if const_val != 0:
                entry[(0, 0, 0, 0)] = entry.get((0, 0, 0, 0), Fraction(0)) - const_val
            for idx, name in enumerate(PARAMETERS):
                val = matrices[name][r][c]
                if val != 0:
                    exp = [0, 0, 0, 0]
                    exp[idx + 1] = 1
                    key = tuple(exp)
                    entry[key] = entry.get(key, Fraction(0)) - val
            row.append({k: v for k, v in entry.items() if v != 0})
        matrix.append(row)
    return matrix


def check_degree_bounds(poly: Polynomial) -> None:
    """Enforce degree bounds: deg 4 in lambda (monic), per-variable deg <= 4 in J, Delta, K."""
    max_lambda = max((exp[0] for exp in poly), default=0)
    if max_lambda != DEGREE_BOUND_LAMBDA:
        raise HostCharpolyRefusalError(
            "DEGREE_LIMIT_EXCEEDED",
            f"polynomial degree in lambda is {max_lambda}, expected exactly {DEGREE_BOUND_LAMBDA}",
        )
    if poly.get((DEGREE_BOUND_LAMBDA, 0, 0, 0)) != Fraction(1):
        raise HostCharpolyRefusalError(
            "NONMONIC_LEADING_COEFFICIENT",
            "leading lambda^4 coefficient is not monic 1",
        )
    for exp, _ in poly.items():
        if exp[0] < 0 or exp[0] > DEGREE_BOUND_LAMBDA:
            raise HostCharpolyRefusalError(
                "DEGREE_LIMIT_EXCEEDED",
                f"lambda exponent {exp[0]} out of bound [0, {DEGREE_BOUND_LAMBDA}]",
            )
        for var_idx, name in enumerate(PARAMETERS):
            var_degree = exp[var_idx + 1]
            if var_degree < 0 or var_degree > DEGREE_BOUND_PER_VARIABLE:
                raise HostCharpolyRefusalError(
                    "DEGREE_LIMIT_EXCEEDED",
                    f"{name} exponent {var_degree} exceeds per-variable degree bound {DEGREE_BOUND_PER_VARIABLE}",
                )
        if sum(exp[1:]) > DEGREE_BOUND_PER_VARIABLE:
            raise HostCharpolyRefusalError(
                "DEGREE_LIMIT_EXCEEDED",
                f"total parameter degree {sum(exp[1:])} exceeds degree bound {DEGREE_BOUND_PER_VARIABLE}",
            )


def derive_charpoly_polynomial(
    matrices: dict[str, list[list[Fraction]]],
) -> Polynomial:
    """Derive characteristic polynomial using dual Leibniz and Laplace cross-verified engines."""
    char_matrix = build_characteristic_matrix(matrices)
    poly_leibniz = det_leibniz(char_matrix)
    poly_laplace = det_laplace(char_matrix)

    if poly_leibniz != poly_laplace:
        raise HostCharpolyError("INTERNAL_ERROR: Leibniz and Laplace determinant engines diverged")

    check_degree_bounds(poly_leibniz)
    return poly_leibniz


def polynomial_to_wire_coefficients(poly: Polynomial) -> list[list[dict[str, Any]]]:
    """Convert polynomial into ascending lambda coefficient arrays matching charpoly_wire."""
    coefficients: list[list[dict[str, Any]]] = [[] for _ in range(DEGREE_BOUND_LAMBDA + 1)]
    for exp, coeff in sorted(poly.items(), key=lambda item: (item[0][0], item[0][1:])):
        lam_power = exp[0]
        powers = list(exp[1:])
        coefficients[lam_power].append({
            "powers": powers,
            "q": str(coeff),
        })
    return coefficients


# ---------------------------------------------------------------------------
# Native Sidecar & Provenance Verification
# ---------------------------------------------------------------------------

def check_prompt_injection(text: str) -> None:
    """Detect untrusted prompt injection patterns in artifacts."""
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            raise HostCharpolyRefusalError("PROMPT_INJECTION_DETECTED", f"matches pattern: {pattern.pattern}")


def check_provenance_pins() -> dict[str, str]:
    """Verify pinned source dependency hashes against live workspace files."""
    hashes: dict[str, str] = {}
    for filename, expected_sha in PINNED_SOURCES.items():
        filepath = HERE / filename
        if not filepath.is_file():
            raise HostCharpolyRefusalError("STALE_SOURCE_HASH", f"missing source dependency: {filename}")
        actual_sha = hashlib.sha256(filepath.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            raise HostCharpolyRefusalError(
                "STALE_SOURCE_HASH",
                f"source SHA mismatch for {filename}: expected {expected_sha}, got {actual_sha}",
            )
        hashes[filename] = actual_sha
    return hashes


def receipt_digest(receipt: dict[str, Any]) -> str:
    """Canonical SHA-256 of a native verification receipt."""
    return hashlib.sha256(json.dumps(receipt, sort_keys=True).encode("utf-8")).hexdigest()


def native_candidate_sha256(normalized_coefficients: list[list[dict[str, Any]]],
                            seed_hash: str = SUPPORTED_SEED_SHA256) -> str:
    """The candidate digest the native receipt binds for these coefficients (recomputed, not trusted)."""
    public = bridge.prepare_public(seed_hash)["payload"]["native_public_input"]
    assertion = sidecar.assertion_text(normalized_coefficients)
    assertion_bytes = assertion.encode("utf-8")
    candidate = {
        "schema": CANDIDATE_SCHEMA,
        "public_input_sha256": sidecar.digest(public),
        "obligation_id": public["obligation_id"],
        "answer_sha256": hashlib.sha256(assertion_bytes).hexdigest(),
        "assertion_span": [0, len(assertion_bytes)],
        "assertion_text": assertion,
        "coefficients": normalized_coefficients,
    }
    return sidecar.digest(candidate)


def verify_via_native_sidecar(
    normalized_coefficients: list[list[dict[str, Any]]],
    seed_hash: str = SUPPORTED_SEED_SHA256,
) -> dict[str, Any]:
    """Verify normalized coefficients against native sidecar host on the 125-point grid."""
    packet = bridge.prepare_public(seed_hash)
    public = packet["payload"]["native_public_input"]

    assertion = sidecar.assertion_text(normalized_coefficients)
    assertion_bytes = assertion.encode("utf-8")

    candidate = {
        "schema": CANDIDATE_SCHEMA,
        "public_input_sha256": sidecar.digest(public),
        "obligation_id": public["obligation_id"],
        "answer_sha256": hashlib.sha256(assertion_bytes).hexdigest(),
        "assertion_span": [0, len(assertion_bytes)],
        "assertion_text": assertion,
        "coefficients": normalized_coefficients,
    }

    try:
        host = sidecar.NativeHost()
        _binary, custody = host.custody()
    except (sidecar.Infrastructure, OSError, KeyError, TypeError, ValueError) as exc:
        raise HostCharpolyRefusalError("SWAPPED_BINARY", f"native custody check failed: {exc}") from None

    receipt = sidecar.verify(public, candidate, assertion, host=host)
    if receipt["status"] != "CERTIFIED_IDENTITY":
        raise HostCharpolyRefusalError("FORGED_CERTIFICATE", f"native verification rejected: {receipt.get('status')}")

    return {
        "native_receipt": receipt,
        "binary_sha256": custody["binary_sha256"],
        "build_receipt_sha256": custody["build_receipt_sha256"],
        "grid_points": receipt.get("grid_points", GRID_POINTS),
        "public_packet_sha256": packet["sha256"],
    }


# ---------------------------------------------------------------------------
# Certified Context Artifact Generation & Validation
# ---------------------------------------------------------------------------

def derive_host_charpoly(
    seed_hash: str = SUPPORTED_SEED_SHA256,
    artifact_input: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Offline derivation of the characteristic polynomial and normalized wire format."""
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise HostCharpolyRefusalError("UNREGISTERED_SEED")

    matrices = admit_public_matrices(seed_hash, artifact_input)
    det_poly = derive_charpoly_polynomial(matrices)
    raw_coefficients = polynomial_to_wire_coefficients(det_poly)

    raw_wire_payload = {"coefficients": raw_coefficients}
    raw_json = json.dumps(raw_wire_payload, separators=(",", ":"))
    wire_receipt = wire.normalize_candidate(raw_json)

    if not wire_receipt["accepted"] or wire_receipt["status"] != "NORMALIZED":
        code = wire_receipt.get("refusal", {}).get("code", "WIRE_NORMALIZATION_FAILED")
        raise HostCharpolyRefusalError("MALFORMED_RATIONAL", f"charpoly wire rejected: {code}")

    normalized = json.loads(wire_receipt["normalized_json"])
    return {
        "seed_sha256": seed_hash,
        "polynomial": det_poly,
        "wire_receipt": wire_receipt,
        "normalized_coefficients": normalized["coefficients"],
        "normalized_json": wire_receipt["normalized_json"],
        "normalized_sha256": wire_receipt["normalized_sha256"],
    }


@functools.lru_cache(maxsize=4)
def get_expected_charpoly_standard_form(seed_hash: str = SUPPORTED_SEED_SHA256) -> str:
    """Derive canonical standard form string of characteristic polynomial for given seed."""
    matrices = admit_public_matrices(seed_hash)
    poly = derive_charpoly_polynomial(matrices)
    return format_charpoly_standard_form(poly, ("lambda", *PARAMETERS))


@functools.lru_cache(maxsize=4)
def get_expected_public_hamiltonian_matrix(seed_hash: str = SUPPORTED_SEED_SHA256) -> list[list[str]]:
    """Format expected public Hamiltonian matrix strings from admitted public matrices."""
    matrices = admit_public_matrices(seed_hash)
    rows: list[list[str]] = []
    for r in range(DIMENSION):
        row: list[str] = []
        for c in range(DIMENSION):
            parts: list[str] = []
            k_val = matrices["K"][r][c]
            d_val = matrices["Delta"][r][c]
            j_val = matrices["J"][r][c]
            if k_val != 0:
                parts.append("K" if k_val == 1 else ("-K" if k_val == -1 else f"{k_val}*K"))
            if d_val != 0:
                term = "Delta" if abs(d_val) == 1 else f"{abs(d_val)}*Delta"
                if parts:
                    sign = "+" if d_val > 0 else "-"
                    parts.append(f"{sign}{term}")
                else:
                    parts.append(term if d_val > 0 else f"-{term}")
            if j_val != 0:
                term = "J" if abs(j_val) == 1 else f"{abs(j_val)}*J"
                if parts:
                    sign = "+" if j_val > 0 else "-"
                    parts.append(f"{sign}{term}")
                else:
                    parts.append(term if j_val > 0 else f"-{term}")
            row.append("".join(parts) if parts else "0")
        rows.append(row)
    return rows


def build_compact_solver_context(
    certified_context: dict[str, Any] | None = None,
    seed_hash: str = SUPPORTED_SEED_SHA256,
    artifact_input: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Project verified evidence into the compact solver context
    (schema pfp.qm-host-charpoly.compact-certificate.v1, canonical length <= COMPACT_CHAR_BUDGET).

    The native verification fields are copied from a receipt produced by an actual
    native run: either the given full ``certified_context`` (which must carry its
    receipt), or a full context built here first. Without a native receipt this
    refuses (``MISSING_NATIVE_EVIDENCE`` or the native refusal) instead of emitting
    ``CERTIFIED_IDENTITY``.
    """
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise HostCharpolyRefusalError("UNREGISTERED_SEED")
    if certified_context is None:
        certified_context = build_certified_context(seed_hash, artifact_input, compact=False)
    receipt = certified_context.get("native_receipt") if isinstance(certified_context, dict) else None
    if not isinstance(receipt, dict) or receipt.get("status") != "CERTIFIED_IDENTITY":
        raise HostCharpolyRefusalError("MISSING_NATIVE_EVIDENCE", "compact projection needs a certified native receipt")

    matrices = admit_public_matrices(seed_hash, artifact_input)
    poly = derive_charpoly_polynomial(matrices)
    standard_str = format_charpoly_standard_form(poly, ("lambda", *PARAMETERS))

    return {
        "schema": COMPACT_SCHEMA,
        "status": "CERTIFIED_INTERMEDIATE_CHARPOLY",
        "seed_sha256": seed_hash,
        "obligation_id": f"registered-qm-charpoly:{seed_hash}",
        "polynomial": {
            "standard_form": standard_str,
        },
        "carrier": {
            "domain": "Q",
            "variables": ["lambda", *PARAMETERS],
            "degree_bounds": {"lambda": DEGREE_BOUND_LAMBDA, "parameters": DEGREE_BOUND_PER_VARIABLE},
        },
        "native_verification": {
            "status": receipt["status"],
            "grid_points_verified": receipt.get("grid_points"),
            "receipt_sha256": receipt_digest(receipt),
        },
        "public_hamiltonian": {
            "basis": list(BASIS),
            "matrix": get_expected_public_hamiltonian_matrix(seed_hash),
        },
        "limitations": {
            "certified_scope": [CLAIM_SCOPE],
            "uncertified_obligations": list(UNCERTIFIED_OBLIGATIONS),
            "final_answer_certified": False,
            "notice": COMPACT_LIMITATION_NOTICE,
        },
    }


def build_compact_certificate(
    seed_hash: str = SUPPORTED_SEED_SHA256,
    artifact_input: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compact certificate: native verification runs first, then the result is projected."""
    return build_compact_solver_context(None, seed_hash, artifact_input)


def build_certified_context(
    seed_hash: str = SUPPORTED_SEED_SHA256,
    artifact_input: str | dict[str, Any] | None = None,
    compact: bool = True,
) -> dict[str, Any]:
    """Construct certified context artifact.

    When compact=True (default), returns the compact serialized certificate
    (schema pfp.qm-host-charpoly.compact-certificate.v1, <= 1,200 characters).
    When compact=False, returns the complete artifact without internal failure_states.
    """
    source_hashes = check_provenance_pins()
    derived = derive_host_charpoly(seed_hash, artifact_input)
    coefficients = derived["normalized_coefficients"]

    # Native verification happens before any certificate is written, on both paths.
    native_info = verify_via_native_sidecar(coefficients, seed_hash)
    evidence = {"native_receipt": native_info["native_receipt"]}
    compact_cert = build_compact_solver_context(evidence, seed_hash, artifact_input)
    if compact:
        return compact_cert

    solver_context = {
        "schema": SOLVER_CONTEXT_SCHEMA,
        "representation": "coefficients",
        "coefficients": coefficients,
        "compact_certificate": compact_cert,
    }

    return {
        "schema": SCHEMA,
        "status": "CERTIFIED_INTERMEDIATE_CHARPOLY",
        "seed_sha256": seed_hash,
        "obligation_id": f"registered-qm-charpoly:{seed_hash}",
        "theorem": THEOREM,
        "carrier": {
            "domain": "Rational field Q with exact rational arithmetic (fractions.Fraction)",
            "variables": ["lambda", *PARAMETERS],
            "basis": list(BASIS),
            "degree_bounds": {
                "lambda": DEGREE_BOUND_LAMBDA,
                "J": DEGREE_BOUND_PER_VARIABLE,
                "Delta": DEGREE_BOUND_PER_VARIABLE,
                "K": DEGREE_BOUND_PER_VARIABLE,
            },
            "grid_nodes": list(GRID_NODES),
            "grid_point_count": GRID_POINTS,
        },
        "source_bindings": {
            "pinned_sources": source_hashes,
            "native_binary_sha256": native_info["binary_sha256"],
            "native_build_receipt_sha256": native_info["build_receipt_sha256"],
        },
        "admitted_public_matrix": {
            "source_path": "dag/benchmark/hamiltonian_artifact.py",
            "source_sha256": source_hashes["hamiltonian_artifact.py"],
            "basis": list(BASIS),
            "parameters": list(PARAMETERS),
        },
        "wire_normalization": {
            "wire_schema": derived["wire_receipt"]["schema"],
            "normalized_sha256": derived["normalized_sha256"],
            "transformations": derived["wire_receipt"]["transformations"],
        },
        "native_verification": {
            "status": native_info["native_receipt"]["status"],
            "grid_points_verified": native_info["grid_points"],
            "public_packet_sha256": native_info["public_packet_sha256"],
            "native_receipt_digest": receipt_digest(native_info["native_receipt"]),
            "polynomial_sha256": derived["normalized_sha256"],
        },
        "native_receipt": native_info["native_receipt"],
        "solver_context": solver_context,
        "limitations": {
            "certified_scope": [CLAIM_SCOPE],
            "uncertified_obligations": list(UNCERTIFIED_OBLIGATIONS),
            "final_answer_certified": False,
            "evaluation_role": (
                "Host-derived intermediate prompt context ONLY; not a full QM solution, "
                "not evidence of solver accuracy."
            ),
        },
    }


def _verify_native_evidence(context: dict[str, Any], schema: str, seed_hash: str, reexecute_native: bool) -> dict:
    """Check that the claimed native verification is backed by a receipt bound to the host polynomial.

    The polynomial is re-derived here (exact Leibniz/Laplace determinant, independent of
    the artifact). A full context must carry its native receipt; the receipt must bind
    that polynomial's candidate digest and the admitted public input. With
    ``reexecute_native`` (default) the native sidecar is run again on the re-derived
    coefficients and must reproduce the claimed receipt digest exactly; if it cannot
    run, validation refuses. A compact certificate carries only the receipt digest,
    so it can be validated only by re-execution.
    """
    native = context["native_verification"]
    derived = derive_host_charpoly(seed_hash)
    claimed_digest = native.get("native_receipt_digest" if schema == SCHEMA else "receipt_sha256")
    if not isinstance(claimed_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", claimed_digest):
        raise HostCharpolyRefusalError("MISSING_NATIVE_EVIDENCE", "no native receipt digest")
    if schema == SCHEMA:
        receipt = context.get("native_receipt")
        if not isinstance(receipt, dict):
            raise HostCharpolyRefusalError("MISSING_NATIVE_EVIDENCE", "full context carries no native receipt")
        if receipt_digest(receipt) != claimed_digest:
            raise HostCharpolyRefusalError("FORGED_CERTIFICATE", "receipt digest does not match the receipt")
        if native.get("polynomial_sha256") != derived["normalized_sha256"]:
            raise HostCharpolyRefusalError("FORGED_CERTIFICATE", "polynomial digest differs from host derivation")
        solver = context.get("solver_context")
        if not isinstance(solver, dict) or solver.get("coefficients") != derived["normalized_coefficients"]:
            raise HostCharpolyRefusalError("FORGED_CERTIFICATE", "certificate payload differs from host derivation")
        public = bridge.prepare_public(seed_hash)["payload"]["native_public_input"]
        if (receipt.get("status") != "CERTIFIED_IDENTITY" or receipt.get("grid_points") != GRID_POINTS
                or receipt.get("candidate_sha256") != native_candidate_sha256(derived["normalized_coefficients"], seed_hash)
                or receipt.get("public_input_sha256") != sidecar.digest(public)
                or receipt.get("binary_sha256") != context.get("source_bindings", {}).get("native_binary_sha256")):
            raise HostCharpolyRefusalError("FORGED_CERTIFICATE", "native receipt is not bound to this polynomial")
    if not reexecute_native:
        return {"native_reexecuted": False, "receipt_sha256": claimed_digest}
    try:
        fresh = verify_via_native_sidecar(derived["normalized_coefficients"], seed_hash)
    except HostCharpolyRefusalError as exc:
        raise HostCharpolyRefusalError("MISSING_NATIVE_EVIDENCE", f"native re-execution unavailable: {exc.code}") from None
    if receipt_digest(fresh["native_receipt"]) != claimed_digest:
        raise HostCharpolyRefusalError("FORGED_CERTIFICATE", "claimed receipt is not reproduced by native re-execution")
    return {"native_reexecuted": True, "receipt_sha256": claimed_digest}


def validate_certified_context(context_input: str | dict[str, Any], *, reexecute_native: bool = True) -> dict[str, Any]:
    """Strictly validate a certified context artifact, enforcing limitations and provenance.

    Declared verification fields are never sufficient: see ``_verify_native_evidence``.
    """
    if isinstance(context_input, str):
        check_prompt_injection(context_input)
        try:
            context = json.loads(context_input)
        except json.JSONDecodeError as exc:
            raise HostCharpolyRefusalError("MALFORMED_JSON", f"invalid JSON: {exc}") from None
    elif isinstance(context_input, dict):
        context = deepcopy(context_input)
    else:
        raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", "context must be string or dict")

    schema = context.get("schema")
    if schema not in (SCHEMA, COMPACT_SCHEMA):
        raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", f"schema must be {SCHEMA} or {COMPACT_SCHEMA}")

    if context.get("status") != "CERTIFIED_INTERMEDIATE_CHARPOLY":
        raise HostCharpolyRefusalError("FORGED_CERTIFICATE", "invalid status field")

    seed_hash = context.get("seed_sha256")
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise HostCharpolyRefusalError("UNREGISTERED_SEED", "unsupported seed hash")

    limitations = context.get("limitations")
    if not isinstance(limitations, dict):
        raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", "missing limitations section")

    if limitations.get("final_answer_certified") is not False:
        raise HostCharpolyRefusalError(
            "CONTRADICTION_FINAL_ANSWER_CLAIM",
            "final_answer_certified must be explicitly False",
        )

    if limitations.get("certified_scope") != [CLAIM_SCOPE]:
        raise HostCharpolyRefusalError(
            "CONTRADICTION_FINAL_ANSWER_CLAIM",
            f"certified_scope must contain only '{CLAIM_SCOPE}'",
        )

    uncertified = limitations.get("uncertified_obligations")
    if not isinstance(uncertified, list) or not set(UNCERTIFIED_OBLIGATIONS).issubset(set(uncertified)):
        raise HostCharpolyRefusalError(
            "CONTRADICTION_FINAL_ANSWER_CLAIM",
            "uncertified_obligations must declare all uncertified QM obligations",
        )

    carrier = context.get("carrier")
    if not isinstance(carrier, dict):
        raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", "missing carrier section")

    native_verif = context.get("native_verification")
    if not isinstance(native_verif, dict):
        raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", "missing native_verification section")
    if native_verif.get("status") != "CERTIFIED_IDENTITY":
        raise HostCharpolyRefusalError(
            "FORGED_CERTIFICATE",
            "native_verification status must be 'CERTIFIED_IDENTITY'",
        )
    if native_verif.get("grid_points_verified") != GRID_POINTS:
        raise HostCharpolyRefusalError(
            "FORGED_CERTIFICATE",
            f"native_verification grid_points_verified must equal {GRID_POINTS}",
        )

    if schema == COMPACT_SCHEMA:
        # Carrier bounds and domain validation
        if carrier.get("domain") != "Q":
            raise HostCharpolyRefusalError("FORGED_CERTIFICATE", "carrier domain must be 'Q'")
        if carrier.get("variables") != ["lambda", *PARAMETERS]:
            raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", f"carrier variables must be ['lambda', *{PARAMETERS}]")
        bounds = carrier.get("degree_bounds")
        if not isinstance(bounds, dict):
            raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", "missing degree_bounds in carrier")
        if bounds.get("lambda") != DEGREE_BOUND_LAMBDA:
            raise HostCharpolyRefusalError(
                "DEGREE_LIMIT_EXCEEDED",
                f"carrier degree_bounds.lambda must equal {DEGREE_BOUND_LAMBDA}",
            )
        if bounds.get("parameters") != DEGREE_BOUND_PER_VARIABLE:
            raise HostCharpolyRefusalError(
                "DEGREE_LIMIT_EXCEEDED",
                f"carrier degree_bounds.parameters must equal {DEGREE_BOUND_PER_VARIABLE}",
            )

        # Limitation notice validation
        notice = limitations.get("notice")
        if not isinstance(notice, str):
            raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", "missing limitations.notice")
        check_prompt_injection(notice)
        if notice != COMPACT_LIMITATION_NOTICE:
            raise HostCharpolyRefusalError(
                "CONTRADICTION_FINAL_ANSWER_CLAIM",
                f"limitations notice must match expected disclaimer text '{COMPACT_LIMITATION_NOTICE}'",
            )

        # Public Hamiltonian matrix validation
        pub_ham = context.get("public_hamiltonian")
        if not isinstance(pub_ham, dict):
            raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", "missing public_hamiltonian section")
        if pub_ham.get("basis") != list(BASIS):
            raise HostCharpolyRefusalError("PUBLIC_INPUT_MISMATCH", f"public_hamiltonian basis must be {list(BASIS)}")
        expected_matrix = get_expected_public_hamiltonian_matrix(seed_hash)
        if pub_ham.get("matrix") != expected_matrix:
            raise HostCharpolyRefusalError(
                "PUBLIC_INPUT_MISMATCH",
                "public_hamiltonian matrix representation does not match admitted public matrix",
            )

        # Characteristic polynomial standard form validation
        poly_info = context.get("polynomial")
        if not isinstance(poly_info, dict):
            raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", "missing polynomial section")
        standard_form = poly_info.get("standard_form")
        if not isinstance(standard_form, str):
            raise HostCharpolyRefusalError("SHAPE_OR_TYPE_VIOLATION", "missing polynomial standard_form string")
        check_prompt_injection(standard_form)
        expected_standard_form = get_expected_charpoly_standard_form(seed_hash)
        if standard_form != expected_standard_form:
            raise HostCharpolyRefusalError(
                "CONTRADICTION_FINAL_ANSWER_CLAIM",
                f"polynomial standard_form does not match host-derived characteristic polynomial for seed {seed_hash}",
            )

    elif schema == SCHEMA:
        if carrier.get("grid_point_count") != GRID_POINTS:
            raise HostCharpolyRefusalError(
                "FORGED_CERTIFICATE",
                f"carrier grid_point_count must equal {GRID_POINTS}",
            )
        bounds = carrier.get("degree_bounds")
        if isinstance(bounds, dict) and bounds.get("lambda") != DEGREE_BOUND_LAMBDA:
            raise HostCharpolyRefusalError(
                "DEGREE_LIMIT_EXCEEDED",
                f"carrier degree_bounds.lambda must equal {DEGREE_BOUND_LAMBDA}",
            )
        eval_role = limitations.get("evaluation_role")
        if isinstance(eval_role, str):
            check_prompt_injection(eval_role)
        solver_ctx = context.get("solver_context")
        if isinstance(solver_ctx, dict) and "compact_certificate" in solver_ctx:
            validate_certified_context(solver_ctx["compact_certificate"], reexecute_native=reexecute_native)

    check_provenance_pins()
    evidence = _verify_native_evidence(context, schema, seed_hash, reexecute_native)
    return {"valid": True, "context": context, "evidence": evidence}


# ---------------------------------------------------------------------------
# Candidate Verification & Attack Registry Engine
# ---------------------------------------------------------------------------

def _check_candidate_preflight(raw_text: str, seed_hash: str) -> tuple[str | None, str | None]:
    """Scan candidate text for unregistered seeds, injections, and contradiction claims."""
    if seed_hash != SUPPORTED_SEED_SHA256:
        return "UNREGISTERED_SEED", FAILURE_STATES["UNREGISTERED_SEED"]

    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(raw_text):
            return "PROMPT_INJECTION_DETECTED", f"matches injection pattern: {pattern.pattern}"

    compact = raw_text.replace(" ", "").lower()
    if '"final_answer_certified":true' in compact:
        return "CONTRADICTION_FINAL_ANSWER_CLAIM", "candidate improperly claims final_answer_certified: True"

    for forbidden in ["eigenvector", "eigenstate", "projector", "thermal_state", "partition_function", "dynamics"]:
        if f'"{forbidden}"' in raw_text.lower():
            return "CONTRADICTION_FINAL_ANSWER_CLAIM", f"candidate claims uncertified obligation: {forbidden}"

    return None, None


def _check_parsed_coefficient_degrees(coefficients: list[list[dict[str, Any]]]) -> tuple[str | None, str | None]:
    """Verify explicit degree bounds <= 4 on all monomials."""
    for terms in coefficients:
        for term in terms:
            powers = term["powers"]
            for var_idx, p in enumerate(powers):
                if p > DEGREE_BOUND_PER_VARIABLE:
                    return "DEGREE_LIMIT_EXCEEDED", f"{PARAMETERS[var_idx]} exponent {p} > {DEGREE_BOUND_PER_VARIABLE}"
            if sum(powers) > DEGREE_BOUND_PER_VARIABLE:
                return "DEGREE_LIMIT_EXCEEDED", f"total parameter degree {sum(powers)} > {DEGREE_BOUND_PER_VARIABLE}"
    return None, None


def _verify_native_receipt(
    coefficients: list[list[dict[str, Any]]], seed_hash: str
) -> dict[str, Any]:
    """Invoke native sidecar and translate receipt into standard verification fields."""
    try:
        packet = bridge.prepare_public(seed_hash)
        public = packet["payload"]["native_public_input"]
        assertion = sidecar.assertion_text(coefficients)
        assertion_bytes = assertion.encode("utf-8")

        candidate_obj = {
            "schema": CANDIDATE_SCHEMA,
            "public_input_sha256": sidecar.digest(public),
            "obligation_id": public["obligation_id"],
            "answer_sha256": hashlib.sha256(assertion_bytes).hexdigest(),
            "assertion_span": [0, len(assertion_bytes)],
            "assertion_text": assertion,
            "coefficients": coefficients,
        }

        native_receipt = sidecar.verify(public, candidate_obj, assertion)
    except (sidecar.Infrastructure, OSError, KeyError, TypeError, ValueError) as exc:
        return {
            "accepted": False,
            "status": "INFRASTRUCTURE_REFUSAL",
            "refusal_code": "SWAPPED_BINARY",
            "refusal_details": str(exc),
        }

    status = native_receipt["status"]
    if status == "CERTIFIED_IDENTITY":
        return {
            "accepted": True,
            "status": "CERTIFIED_IDENTITY",
            "certified_scope": [CLAIM_SCOPE],
            "grid_points": native_receipt.get("grid_points", GRID_POINTS),
            "refusal_code": None,
            "refusal_details": None,
        }
    if status == "REFUTED_IDENTITY":
        return {
            "accepted": False,
            "status": "REFUTED_IDENTITY",
            "refusal_code": "REFUTED_IDENTITY",
            "witness": native_receipt.get("witness"),
            "refusal_details": "candidate polynomial refuted on native grid",
        }
    if status == "INFRASTRUCTURE_REFUSAL":
        reason = native_receipt.get("reason", "INFRASTRUCTURE_REFUSAL")
        ref_code = "SWAPPED_BINARY" if any(s in reason for s in ("BINARY", "CUSTODY", "BUILD")) else reason
        return {
            "accepted": False,
            "status": "INFRASTRUCTURE_REFUSAL",
            "refusal_code": ref_code,
            "refusal_details": reason,
        }
    return {
        "accepted": False,
        "status": status,
        "refusal_code": native_receipt.get("reason", "UNSUPPORTED_OR_MALFORMED"),
        "refusal_details": native_receipt.get("reason"),
    }


def verify_candidate_charpoly(
    candidate_input: str | dict[str, Any],
    seed_hash: str = SUPPORTED_SEED_SHA256,
    artifact_input: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Test candidate characteristic polynomial for false acceptance or false refusal."""
    receipt: dict[str, Any] = {
        "schema": "pfp.qm-host-charpoly.verification-receipt.v1",
        "accepted": False,
        "status": "REFUSED",
        "refusal_code": None,
        "refusal_details": None,
        "seed_sha256": seed_hash,
        "certified_scope": [],
        "witness": None,
    }

    if isinstance(candidate_input, str):
        raw_text = candidate_input
    elif isinstance(candidate_input, dict):
        raw_text = json.dumps(candidate_input, separators=(",", ":"))
    else:
        receipt["refusal_code"] = "SHAPE_OR_TYPE_VIOLATION"
        receipt["refusal_details"] = "candidate must be string or dict"
        return receipt

    preflight_code, preflight_details = _check_candidate_preflight(raw_text, seed_hash)
    if preflight_code:
        receipt["refusal_code"] = preflight_code
        receipt["refusal_details"] = preflight_details
        return receipt

    wire_receipt = wire.normalize_candidate(raw_text)
    if not wire_receipt["accepted"] or wire_receipt["status"] != "NORMALIZED":
        code = wire_receipt.get("refusal", {}).get("code", "MALFORMED_JSON")
        receipt["refusal_code"] = code
        receipt["refusal_details"] = f"wire refused with code {code}"
        return receipt

    normalized_data = json.loads(wire_receipt["normalized_json"])
    coefficients = normalized_data["coefficients"]

    degree_code, degree_details = _check_parsed_coefficient_degrees(coefficients)
    if degree_code:
        receipt["refusal_code"] = degree_code
        receipt["refusal_details"] = degree_details
        return receipt

    native_res = _verify_native_receipt(coefficients, seed_hash)
    receipt.update(native_res)
    return receipt
