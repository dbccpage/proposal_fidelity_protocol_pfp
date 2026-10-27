"""Exact rational non-abelian gauge group holonomies on 4D simplicial complexes.

AuthorityEffect: None.

This module implements:
1. Exact cyclotomic number field arithmetic Q(zeta_n) over Fraction:
   - Elements represented in polynomial basis modulo the n-th cyclotomic polynomial Phi_n(x).
   - Exact +, -, *, /, inverse, conjugate, is_zero, is_real, trace, and norm.
   - Exact roots of unity zeta_n, imaginary unit i, and square roots like sqrt(2) = zeta_8 - zeta_8^3 in Q(zeta_8).
2. Exact CyclotomicMatrix linear algebra:
   - Matrix addition, multiplication, adjoint (conjugate transpose), trace, determinant.
   - Unitarity verification: U^dagger * U == I.
   - Commutator: [A, B] = A * B - B * A.
3. Exact discrete non-abelian gauge groups:
   - SU(2) discrete subgroups:
     * Quaternion group Q_8 = {+/- 1, +/- i, +/- j, +/- k} in Q(i) <= Q(zeta_8).
     * Binary tetrahedral group 2T (order 24) in Q(zeta_8).
     * Universal Clifford + T gate group <H, T> in Q(zeta_8).
   - SO(4) gauge group representations:
     * Via Spin(4) = SU(2) x SU(2) -> SO(4) double cover acting on quaternions H = Q(sqrt(2))^4.
     * Yields exact 4x4 orthogonal matrices over Q(sqrt(2)) <= Q(zeta_8).
4. 4D Simplicial complexes & dual hinge circulation:
   - 4-simplices (pentachora), 3-simplices (tetrahedra), and 2-simplices (triangle hinges).
   - Standard 4-simplex Delta^4, boundary 3-sphere d(Delta^4), and 4D triangulated hinge star.
   - Dual 1-cycle circling a codimension-2 triangular hinge.
5. Non-abelian Wilson loop holonomies & discrete Bianchi identity:
   - Wilson loop W(h) = prod U(sigma_i, sigma_{i+1}) around hinge.
   - Curvature defect cochain K(h) = W(h) - I.
   - Gauge transformation covariance: W(h) -> g * W(h) * g^{-1}.
   - Discrete Bianchi identity around 4D simplex stars.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union


# ---------------------------------------------------------------------------
# 1. Exact Cyclotomic Polynomials & Field Arithmetic
# ---------------------------------------------------------------------------

def cyclotomic_polynomial_coeffs(n: int) -> List[int]:
    """Compute coefficients of the n-th cyclotomic polynomial Phi_n(x) [lowest to highest]."""
    if type(n) is not int or n < 1:
        raise ValueError("conductor must be a positive integer")
    if n == 1:
        return [-1, 1]  # x - 1
    elif n == 2:
        return [1, 1]   # x + 1
    elif n == 3:
        return [1, 1, 1]  # x^2 + x + 1
    elif n == 4:
        return [1, 0, 1]  # x^2 + 1
    elif n == 5:
        return [1, 1, 1, 1, 1]  # x^4 + x^3 + x^2 + x + 1
    elif n == 6:
        return [1, -1, 1]  # x^2 - x + 1
    elif n == 8:
        return [1, 0, 0, 0, 1]  # x^4 + 1
    elif n == 12:
        return [1, 0, -1, 0, 1]  # x^4 - x^2 + 1
    elif n == 24:
        return [1, 0, 0, 0, -1, 0, 0, 0, 1]  # x^8 - x^4 + 1
    else:
        # General exact division: x^n - 1 = prod_{d|n} Phi_d(x)
        poly = [0] * (n + 1)
        poly[0] = -1
        poly[n] = 1
        divisors = [d for d in range(1, n) if n % d == 0]
        curr = poly
        for d in divisors:
            sub = cyclotomic_polynomial_coeffs(d)
            curr = _poly_div(curr, sub)
        return curr


def _poly_div(p1: List[int], p2: List[int]) -> List[int]:
    """Exact polynomial division p1 / p2 with integer coefficients."""
    n1 = len(p1) - 1
    n2 = len(p2) - 1
    if not p1 or not p2 or p2[-1] == 0:
        raise ValueError("nonempty polynomials and a nonzero leading divisor are required")
    quot = [0] * (n1 - n2 + 1)
    rem = [Fraction(c) for c in p1]
    for i in range(n1 - n2, -1, -1):
        coeff = rem[i + n2] / p2[-1]
        if coeff.denominator != 1:
            raise ValueError("polynomial quotient is not integral")
        quot[i] = coeff.numerator
        for j in range(n2 + 1):
            rem[i + j] -= coeff * p2[j]
    if any(rem):
        raise ValueError("polynomial division has a nonzero remainder")
    return quot


def _poly_mod(poly: Sequence[Fraction], modulus: Sequence[int]) -> List[Fraction]:
    """Reduce polynomial by monic modulus polynomial."""
    m_deg = len(modulus) - 1
    assert modulus[-1] == 1, "Modulus must be monic"
    res = [Fraction(c) for c in poly]
    while len(res) > m_deg:
        if res[-1] == 0:
            res.pop()
            continue
        coeff = res.pop()
        deg_shift = len(res) - m_deg + 1
        for i in range(m_deg):
            res[deg_shift + i - 1] -= coeff * Fraction(modulus[i])
    # Pad to m_deg
    while len(res) < m_deg:
        res.append(Fraction(0))
    return res


class Cyclotomic:
    """Exact element of cyclotomic number field Q(zeta_n) = Q[x] / (Phi_n(x))."""

    def __init__(self, conductor: int, coeffs: Sequence[Union[int, Fraction]]) -> None:
        if type(conductor) is not int or conductor < 1:
            raise ValueError("Conductor must be positive integer")
        self.conductor = conductor
        phi = cyclotomic_polynomial_coeffs(conductor)
        self.deg = len(phi) - 1
        reduced = _poly_mod([Fraction(c) for c in coeffs], phi)
        self.coeffs: Tuple[Fraction, ...] = tuple(reduced[:self.deg])

    @classmethod
    def rational(cls, q: Union[int, Fraction], conductor: int = 8) -> Cyclotomic:
        """Create a rational scalar in Q(zeta_n)."""
        return cls(conductor, [Fraction(q)])

    @classmethod
    def zero(cls, conductor: int = 8) -> Cyclotomic:
        """Additive zero in Q(zeta_n)."""
        return cls(conductor, [Fraction(0)])

    @classmethod
    def one(cls, conductor: int = 8) -> Cyclotomic:
        """Multiplicative identity in Q(zeta_n)."""
        return cls(conductor, [Fraction(1)])

    @classmethod
    def zeta(cls, conductor: int = 8) -> Cyclotomic:
        """Primitive n-th root of unity zeta_n."""
        if conductor == 1:
            return cls(1, [1])
        elif conductor == 2:
            return cls(2, [-1])
        return cls(conductor, [0, 1])

    @classmethod
    def i(cls, conductor: int = 8) -> Cyclotomic:
        """Imaginary unit i = zeta_4. In Q(zeta_8), i = zeta_8^2."""
        if conductor % 4 != 0:
            raise ValueError(f"Conductor {conductor} does not contain Gaussian i (must be multiple of 4)")
        if conductor == 4:
            return cls(4, [0, 1])
        power = conductor // 4
        # In Q(zeta_8), power = 2 -> zeta_8^2
        return cls(conductor, [0] * power + [1])

    @classmethod
    def sqrt2(cls, conductor: int = 8) -> Cyclotomic:
        """Square root of 2 in Q(zeta_8). Exact identity: sqrt(2) = zeta_8 - zeta_8^3."""
        if conductor % 8 != 0:
            raise ValueError("Conductor must be multiple of 8 to represent sqrt(2)")
        step = conductor // 8
        # zeta_8^1 - zeta_8^3
        coeffs = [0] * (3 * step + 1)
        coeffs[1 * step] = 1
        coeffs[3 * step] = -1
        return cls(conductor, coeffs)

    @classmethod
    def inv_sqrt2(cls, conductor: int = 8) -> Cyclotomic:
        """1 / sqrt(2) = sqrt(2) / 2 in Q(zeta_8)."""
        return cls.sqrt2(conductor) * Fraction(1, 2)

    def is_zero(self) -> bool:
        """Check if element is 0."""
        return all(c == 0 for c in self.coeffs)

    def is_one(self) -> bool:
        """Check if element is 1."""
        return self.coeffs[0] == 1 and all(c == 0 for c in self.coeffs[1:])

    def conjugate(self) -> Cyclotomic:
        """Complex conjugation automorphism: zeta_n -> zeta_n^{-1} = zeta_n^{n-1}."""
        n = self.conductor
        phi = cyclotomic_polynomial_coeffs(n)
        deg = len(phi) - 1
        res = [Fraction(0)] * deg
        for k, c in enumerate(self.coeffs):
            if c == 0:
                continue
            inv_k = (n - (k % n)) % n
            poly = [Fraction(0)] * (inv_k + 1)
            poly[inv_k] = Fraction(1)
            reduced = _poly_mod(poly, phi)
            for j in range(deg):
                res[j] += c * reduced[j]
        return Cyclotomic(n, res)

    def is_real(self) -> bool:
        """Check if element is invariant under complex conjugation."""
        return self == self.conjugate()

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, (int, Fraction)):
            other = Cyclotomic.rational(other, self.conductor)
        if not isinstance(other, Cyclotomic):
            return False
        if self.conductor == other.conductor:
            return self.coeffs == other.coeffs
        # Match conductors via LCM
        l = (self.conductor * other.conductor) // math.gcd(self.conductor, other.conductor)
        s_lift = self._lift_to(l)
        o_lift = other._lift_to(l)
        return s_lift.coeffs == o_lift.coeffs

    def _lift_to(self, target_conductor: int) -> Cyclotomic:
        """Lift element to a higher multiple conductor."""
        m = self.conductor
        n = target_conductor
        if m == n:
            return self
        assert n % m == 0, f"Cannot lift from {m} to non-multiple {n}"
        step = n // m
        phi = cyclotomic_polynomial_coeffs(n)
        deg = len(phi) - 1
        res = [Fraction(0)] * deg
        for k, c in enumerate(self.coeffs):
            if c == 0:
                continue
            p = k * step
            poly = [Fraction(0)] * (p + 1)
            poly[p] = Fraction(1)
            term = _poly_mod(poly, phi)
            for j in range(deg):
                res[j] += c * term[j]
        return Cyclotomic(n, res)

    def __neg__(self) -> Cyclotomic:
        return Cyclotomic(self.conductor, [-c for c in self.coeffs])

    def __add__(self, other: Union[Cyclotomic, int, Fraction]) -> Cyclotomic:
        if isinstance(other, (int, Fraction)):
            other = Cyclotomic.rational(other, self.conductor)
        if self.conductor != other.conductor:
            l = (self.conductor * other.conductor) // math.gcd(self.conductor, other.conductor)
            return self._lift_to(l) + other._lift_to(l)
        return Cyclotomic(self.conductor, [a + b for a, b in zip(self.coeffs, other.coeffs)])

    def __radd__(self, other: Union[int, Fraction]) -> Cyclotomic:
        return self + other

    def __sub__(self, other: Union[Cyclotomic, int, Fraction]) -> Cyclotomic:
        if isinstance(other, (int, Fraction)):
            other = Cyclotomic.rational(other, self.conductor)
        if self.conductor != other.conductor:
            l = (self.conductor * other.conductor) // math.gcd(self.conductor, other.conductor)
            return self._lift_to(l) - other._lift_to(l)
        return Cyclotomic(self.conductor, [a - b for a, b in zip(self.coeffs, other.coeffs)])

    def __rsub__(self, other: Union[int, Fraction]) -> Cyclotomic:
        return Cyclotomic.rational(other, self.conductor) - self

    def __mul__(self, other: Union[Cyclotomic, int, Fraction]) -> Cyclotomic:
        if isinstance(other, (int, Fraction)):
            return Cyclotomic(self.conductor, [c * Fraction(other) for c in self.coeffs])
        if self.conductor != other.conductor:
            l = (self.conductor * other.conductor) // math.gcd(self.conductor, other.conductor)
            return self._lift_to(l) * other._lift_to(l)

        n = self.conductor
        phi = cyclotomic_polynomial_coeffs(n)
        deg = len(phi) - 1
        raw = [Fraction(0)] * (2 * deg)
        for i, a in enumerate(self.coeffs):
            if a == 0:
                continue
            for j, b in enumerate(other.coeffs):
                raw[i + j] += a * b
        return Cyclotomic(n, _poly_mod(raw, phi))

    def __rmul__(self, other: Union[int, Fraction]) -> Cyclotomic:
        return self * other

    def inverse(self) -> Cyclotomic:
        """Exact multiplicative inverse in Q(zeta_n) via regular representation linear system."""
        if self.is_zero():
            raise ZeroDivisionError("Cannot invert 0 in Cyclotomic field")
        deg = self.deg
        # Build matrix for multiplication by self on basis e_0, ..., e_{deg-1}
        matrix = [[Fraction(0)] * deg for _ in range(deg)]
        for j in range(deg):
            e_j = [Fraction(0)] * deg
            e_j[j] = Fraction(1)
            col_elem = self * Cyclotomic(self.conductor, e_j)
            for i in range(deg):
                matrix[i][j] = col_elem.coeffs[i]

        aug = [row[:] + [Fraction(1 if i == 0 else 0)] for i, row in enumerate(matrix)]
        for col in range(deg):
            piv = -1
            for r in range(col, deg):
                if aug[r][col] != 0:
                    piv = r
                    break
            if piv == -1:
                raise ZeroDivisionError("Element non-invertible in Cyclotomic field")
            if piv != col:
                aug[col], aug[piv] = aug[piv], aug[col]

            scale = aug[col][col]
            for c in range(col, deg + 1):
                aug[col][c] /= scale

            for r in range(deg):
                if r != col and aug[r][col] != 0:
                    factor = aug[r][col]
                    for c in range(col, deg + 1):
                        aug[r][c] -= factor * aug[col][c]

        inv_c = [aug[r][deg] for r in range(deg)]
        return Cyclotomic(self.conductor, inv_c)

    def __truediv__(self, other: Union[Cyclotomic, int, Fraction]) -> Cyclotomic:
        if isinstance(other, (int, Fraction)):
            if other == 0:
                raise ZeroDivisionError("Division by zero")
            return self * (Fraction(1) / Fraction(other))
        return self * other.inverse()

    def __rtruediv__(self, other: Union[int, Fraction]) -> Cyclotomic:
        return Cyclotomic.rational(other, self.conductor) / self

    def norm_squared(self) -> Fraction:
        """Return the squared modulus |z|^2 = z * conjugate(z). Must be a rational Fraction."""
        w = self * self.conjugate()
        assert w.is_real(), "Born weight/norm must be real"
        return w.coeffs[0]

    def to_float(self) -> complex:
        """Evaluate approximately to complex number for inspection/diagnostics only."""
        zeta = math.cos(2 * math.pi / self.conductor) + 1j * math.sin(2 * math.pi / self.conductor)
        total = 0j
        for k, c in enumerate(self.coeffs):
            total += float(c) * (zeta ** k)
        return total

    def __repr__(self) -> str:
        parts = []
        for k, c in enumerate(self.coeffs):
            if c != 0:
                if k == 0:
                    parts.append(f"{c}")
                elif k == 1:
                    parts.append(f"{c}*zeta_{self.conductor}" if c != 1 else f"zeta_{self.conductor}")
                else:
                    parts.append(f"{c}*zeta_{self.conductor}^{k}" if c != 1 else f"zeta_{self.conductor}^{k}")
        return " + ".join(parts) if parts else "0"


# ---------------------------------------------------------------------------
# 2. Exact CyclotomicMatrix Linear Algebra
# ---------------------------------------------------------------------------

class CyclotomicMatrix:
    """Exact matrix with Cyclotomic field entries."""

    def __init__(self, data: Sequence[Sequence[Union[Cyclotomic, int, Fraction]]], conductor: int = 8) -> None:
        self.conductor = conductor
        matrix_data: List[List[Cyclotomic]] = []
        for row in data:
            new_row: List[Cyclotomic] = []
            for item in row:
                if isinstance(item, Cyclotomic):
                    new_row.append(item._lift_to(conductor) if item.conductor != conductor else item)
                else:
                    new_row.append(Cyclotomic.rational(item, conductor))
            matrix_data.append(new_row)

        self.rows = len(matrix_data)
        self.cols = len(matrix_data[0]) if self.rows > 0 else 0
        for r in matrix_data:
            if len(r) != self.cols:
                raise ValueError("Inconsistent row lengths in CyclotomicMatrix")
        self.data: Tuple[Tuple[Cyclotomic, ...], ...] = tuple(tuple(r) for r in matrix_data)

    @classmethod
    def eye(cls, dim: int, conductor: int = 8) -> CyclotomicMatrix:
        """Identity matrix of given dimension."""
        data = [[Cyclotomic.one(conductor) if r == c else Cyclotomic.zero(conductor) for c in range(dim)] for r in range(dim)]
        return cls(data, conductor)

    @classmethod
    def zeros(cls, rows: int, cols: int, conductor: int = 8) -> CyclotomicMatrix:
        """Zero matrix of given dimensions."""
        data = [[Cyclotomic.zero(conductor) for _ in range(cols)] for _ in range(rows)]
        return cls(data, conductor)

    def __getitem__(self, idx: Union[int, Tuple[int, int]]) -> Any:
        if isinstance(idx, tuple):
            r, c = idx
            return self.data[r][c]
        return self.data[idx]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CyclotomicMatrix):
            return False
        if (self.rows, self.cols) != (other.rows, other.cols):
            return False
        for r in range(self.rows):
            for c in range(self.cols):
                if self[r, c] != other[r, c]:
                    return False
        return True

    def __neg__(self) -> CyclotomicMatrix:
        data = [[-self[r, c] for c in range(self.cols)] for r in range(self.rows)]
        return CyclotomicMatrix(data, self.conductor)

    def __add__(self, other: CyclotomicMatrix) -> CyclotomicMatrix:
        if (self.rows, self.cols) != (other.rows, other.cols):
            raise ValueError("Dimension mismatch in matrix addition")
        cond = (self.conductor * other.conductor) // math.gcd(self.conductor, other.conductor)
        data = [[self[r, c] + other[r, c] for c in range(self.cols)] for r in range(self.rows)]
        return CyclotomicMatrix(data, cond)

    def __sub__(self, other: CyclotomicMatrix) -> CyclotomicMatrix:
        if (self.rows, self.cols) != (other.rows, other.cols):
            raise ValueError("Dimension mismatch in matrix subtraction")
        cond = (self.conductor * other.conductor) // math.gcd(self.conductor, other.conductor)
        data = [[self[r, c] - other[r, c] for c in range(self.cols)] for r in range(self.rows)]
        return CyclotomicMatrix(data, cond)

    def __mul__(self, other: Union[CyclotomicMatrix, Cyclotomic, int, Fraction]) -> CyclotomicMatrix:
        if isinstance(other, (Cyclotomic, int, Fraction)):
            data = [[self[r, c] * other for c in range(self.cols)] for r in range(self.rows)]
            return CyclotomicMatrix(data, self.conductor)
        if isinstance(other, CyclotomicMatrix):
            if self.cols != other.rows:
                raise ValueError(f"Cannot multiply matrix ({self.rows}x{self.cols}) with ({other.rows}x{other.cols})")
            cond = (self.conductor * other.conductor) // math.gcd(self.conductor, other.conductor)
            mat_data: List[List[Cyclotomic]] = []
            for r in range(self.rows):
                row: List[Cyclotomic] = []
                for c in range(other.cols):
                    acc = Cyclotomic.zero(cond)
                    for k in range(self.cols):
                        acc += self[r, k] * other[k, c]
                    row.append(acc)
                mat_data.append(row)
            return CyclotomicMatrix(mat_data, cond)
        raise TypeError(f"Unsupported operand for *: {type(other)}")

    def adjoint(self) -> CyclotomicMatrix:
        """Conjugate transpose A^dagger."""
        data = [[self[c, r].conjugate() for c in range(self.rows)] for r in range(self.cols)]
        return CyclotomicMatrix(data, self.conductor)

    def trace(self) -> Cyclotomic:
        """Trace of a square matrix."""
        if self.rows != self.cols:
            raise ValueError("Trace is only defined for square matrices")
        tr = Cyclotomic.zero(self.conductor)
        for i in range(self.rows):
            tr += self[i, i]
        return tr

    def is_unitary(self) -> bool:
        """Verify that U^dagger * U == I."""
        if self.rows != self.cols:
            return False
        prod = self.adjoint() * self
        return prod == CyclotomicMatrix.eye(self.rows, self.conductor)

    def is_zero(self) -> bool:
        """Verify that all matrix elements are zero."""
        for r in range(self.rows):
            for c in range(self.cols):
                if not self[r, c].is_zero():
                    return False
        return True

    def l1_entry_norm(self) -> Fraction:
        """Compute the sum of squared entry norms as an exact rational certificate."""
        total = Fraction(0)
        for r in range(self.rows):
            for c in range(self.cols):
                total += self[r, c].norm_squared()
        return total

    def commutator(self, other: CyclotomicMatrix) -> CyclotomicMatrix:
        """Compute [A, B] = A * B - B * A."""
        return (self * other) - (other * self)


# ---------------------------------------------------------------------------
# 3. Exact Discrete Non-Abelian Gauge Group Representations
# ---------------------------------------------------------------------------

class NonAbelianGaugeGroup:
    """Exact discrete non-abelian gauge group generators in SU(2) and SO(4)."""

    @staticmethod
    def quaternion_group_q8(conductor: int = 8) -> Dict[str, CyclotomicMatrix]:
        """Quaternion group Q_8 = {+/- 1, +/- i, +/- j, +/- k} in SU(2).

        Represented by exact 2x2 unitary matrices:
            1 = [[1, 0], [0, 1]]
            i = [[i, 0], [0, -i]]
            j = [[0, 1], [-1, 0]]
            k = [[0, i], [i, 0]]
        Satisfies: i^2 = j^2 = k^2 = ijk = -1.
        """
        zero = Cyclotomic.zero(conductor)
        one = Cyclotomic.one(conductor)
        neg_one = -one
        i_unit = Cyclotomic.i(conductor)
        neg_i = -i_unit

        mat_1 = CyclotomicMatrix([[one, zero], [zero, one]], conductor)
        mat_neg_1 = CyclotomicMatrix([[neg_one, zero], [zero, neg_one]], conductor)
        mat_i = CyclotomicMatrix([[i_unit, zero], [zero, neg_i]], conductor)
        mat_j = CyclotomicMatrix([[zero, one], [neg_one, zero]], conductor)
        mat_k = CyclotomicMatrix([[zero, i_unit], [i_unit, zero]], conductor)

        return {
            "1": mat_1,
            "-1": mat_neg_1,
            "i": mat_i,
            "-i": -mat_i,
            "j": mat_j,
            "-j": -mat_j,
            "k": mat_k,
            "-k": -mat_k,
        }

    @staticmethod
    def binary_tetrahedral_group_2t(conductor: int = 8) -> List[CyclotomicMatrix]:
        """Binary tetrahedral group 2T (order 24) in SU(2).

        Generated by Q_8 and 8 elements of the form 1/2 (+/- 1 +/- i +/- j +/- k).
        """
        q8 = NonAbelianGaugeGroup.quaternion_group_q8(conductor)
        elements = list(q8.values())
        half = Fraction(1, 2)

        signs = [-1, 1]
        for s0 in signs:
            for s1 in signs:
                for s2 in signs:
                    for s3 in signs:
                        # elem = 1/2 * (s0*1 + s1*i + s2*j + s3*k)
                        elem = (q8["1"] * s0 + q8["i"] * s1 + q8["j"] * s2 + q8["k"] * s3) * half
                        # Avoid duplicates
                        if not any(elem == existing for existing in elements):
                            elements.append(elem)

        assert len(elements) == 24, f"Binary tetrahedral group must have 24 elements, found {len(elements)}"
        return elements

    @staticmethod
    def clifford_plus_t(conductor: int = 8) -> Dict[str, CyclotomicMatrix]:
        """Universal non-abelian quantum / gauge group generators <H, T> in SU(2).

        All entries strictly in Q(zeta_8):
            H = 1/sqrt(2) * [[1, 1], [1, -1]]
            S = [[1, 0], [0, i]]
            T = [[1, 0], [0, zeta_8]]
            X = [[0, 1], [1, 0]]
            Z = [[1, 0], [0, -1]]
        """
        zero = Cyclotomic.zero(conductor)
        one = Cyclotomic.one(conductor)
        inv_sqrt2 = Cyclotomic.inv_sqrt2(conductor)
        i_unit = Cyclotomic.i(conductor)
        zeta8 = Cyclotomic.zeta(conductor)

        H = CyclotomicMatrix([[inv_sqrt2, inv_sqrt2], [inv_sqrt2, -inv_sqrt2]], conductor)
        S = CyclotomicMatrix([[one, zero], [zero, i_unit]], conductor)
        T = CyclotomicMatrix([[one, zero], [zero, zeta8]], conductor)
        X = CyclotomicMatrix([[zero, one], [one, zero]], conductor)
        Z = CyclotomicMatrix([[one, zero], [zero, -one]], conductor)

        return {"H": H, "S": S, "T": T, "X": X, "Z": Z}

    @staticmethod
    def su2_to_so4(u_left: CyclotomicMatrix, u_right: CyclotomicMatrix) -> CyclotomicMatrix:
        """Map a pair (U_L, U_R) in SU(2) x SU(2) to an exact 4x4 matrix in SO(4).

        Using the quaternion vector basis {1, i, j, k}:
        For basis quaternion q_m, compute U_L * q_m * U_R^dagger and extract the 4 components.
        All entries lie in the real subfield Q(sqrt(2)) <= Q(zeta_8).
        """
        assert (u_left.rows, u_left.cols) == (2, 2)
        assert (u_right.rows, u_right.cols) == (2, 2)
        cond = u_left.conductor
        q8 = NonAbelianGaugeGroup.quaternion_group_q8(cond)
        basis = [q8["1"], q8["i"], q8["j"], q8["k"]]

        ur_adj = u_right.adjoint()
        rot_data: List[List[Cyclotomic]] = []

        # Basis inner product formula: Tr(q_n^dagger * q_m) / 2 = delta_{nm}
        for n in range(4):
            row: List[Cyclotomic] = []
            qn_adj = basis[n].adjoint()
            for m in range(4):
                qm = basis[m]
                transformed = u_left * qm * ur_adj
                # Component is 1/2 * Tr(qn^dagger * transformed)
                comp = (qn_adj * transformed).trace() * Fraction(1, 2)
                row.append(comp)
            rot_data.append(row)

        mat_so4 = CyclotomicMatrix(rot_data, cond)
        assert mat_so4.is_unitary(), "Transformed SO(4) matrix must be orthogonal"
        return mat_so4


# ---------------------------------------------------------------------------
# 4. 4D Simplicial Complex Triangulation & Dual Hinge Star
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Simplex4D:
    """A 4-simplex (pentachoron) with 5 vertices."""

    vertices: Tuple[int, int, int, int, int]
    id: str

    def __init__(self, vertices: Sequence[int]) -> None:
        sorted_v = tuple(sorted(set(vertices)))
        if len(sorted_v) != 5:
            raise ValueError(f"4-simplex requires exactly 5 vertices, got {sorted_v}")
        object.__setattr__(self, "vertices", sorted_v)
        object.__setattr__(self, "id", f"s4_{'_'.join(str(v) for v in sorted_v)}")

    def tetrahedra(self) -> List[Tuple[int, int, int, int]]:
        """Return the 5 codimension-1 tetrahedral facets."""
        v = self.vertices
        return [
            tuple(sorted([v[j] for j in range(5) if j != i]))  # type: ignore
            for i in range(5)
        ]

    def triangle_hinges(self) -> List[Tuple[int, int, int]]:
        """Return the 10 codimension-2 triangle hinges."""
        v = self.vertices
        res = []
        for i in range(5):
            for j in range(i + 1, 5):
                res.append(tuple(sorted([v[k] for k in range(5) if k != i and k != j])))
        return res  # type: ignore


class FourSimplexHingeStar:
    """A cluster of 4-simplices meeting around a common 2-simplex triangle hinge.

    This provides the minimal 4D geometric substrate for evaluating non-abelian
    curvature holonomies around codimension-2 Regge hinges.
    """

    def __init__(
        self,
        hinge_vertices: Tuple[int, int, int],
        perimeter_vertices: Sequence[int],
    ) -> None:
        """Construct a star of k 4-simplices sharing hinge (v0, v1, v2) with perimeter cycle."""
        h = tuple(sorted(hinge_vertices))
        if len(h) != 3:
            raise ValueError("Hinge must be a 2-simplex with 3 vertices")
        self.hinge: Tuple[int, int, int] = h  # type: ignore
        k = len(perimeter_vertices)
        if k < 3:
            raise ValueError("Need at least 3 perimeter vertices to close a dual loop around hinge")

        # 4-simplices: sigma_i = (h_0, h_1, h_2, p_i, p_{i+1})
        self.simplices: List[Simplex4D] = []
        self.shared_tetrahedra: List[Tuple[int, int, int, int]] = []

        for i in range(k):
            p_curr = perimeter_vertices[i]
            p_next = perimeter_vertices[(i + 1) % k]
            s = Simplex4D((*self.hinge, p_curr, p_next))
            self.simplices.append(s)
            # Shared interface with next simplex is the tetrahedron (*self.hinge, p_next)
            tau = tuple(sorted((*self.hinge, p_next)))
            self.shared_tetrahedra.append(tau)  # type: ignore

        self.k = k

    def dual_loop(self) -> List[Tuple[str, str]]:
        """Return the ordered directed dual edges connecting adjacent 4-simplices."""
        loop = []
        for i in range(self.k):
            src = self.simplices[i].id
            tgt = self.simplices[(i + 1) % self.k].id
            loop.append((src, tgt))
        return loop


# ---------------------------------------------------------------------------
# 5. Non-Abelian Gauge Connection & Holonomy Computation
# ---------------------------------------------------------------------------

class NonAbelianSimplicialGaugeSystem:
    """Exact non-abelian gauge connection and Wilson loop engine on 4D simplicial complexes."""

    def __init__(self, star: FourSimplexHingeStar, default_identity_group: str = "SU2", conductor: int = 8) -> None:
        self.star = star
        self.conductor = conductor
        self.group_type = default_identity_group
        self.dim = 2 if default_identity_group == "SU2" else 4

        # Connection maps: (src_simplex_id, tgt_simplex_id) -> CyclotomicMatrix
        self.connection: Dict[Tuple[str, str], CyclotomicMatrix] = {}

        # Initialize to flat identity connection
        eye = CyclotomicMatrix.eye(self.dim, conductor)
        for src, tgt in self.star.dual_loop():
            self.connection[(src, tgt)] = eye
            self.connection[(tgt, src)] = eye

    def set_link_gauge_element(self, src_id: str, tgt_id: str, u_matrix: CyclotomicMatrix) -> None:
        """Assign an exact unitary gauge transport matrix to the directed interface."""
        assert u_matrix.is_unitary(), "Gauge transport matrix must be unitary"
        self.connection[(src_id, tgt_id)] = u_matrix
        self.connection[(tgt_id, src_id)] = u_matrix.adjoint()

    def compute_hinge_holonomy(self, reverse: bool = False) -> CyclotomicMatrix:
        """Compute the ordered non-abelian Wilson loop holonomy around the hinge:

            W(h) = P prod_{i=0}^{k-1} U(sigma_i, sigma_{i+1}).
        """
        loop = self.star.dual_loop()
        if reverse:
            # Reversing direction: (tgt, src) in reverse order
            loop = [(tgt, src) for src, tgt in reversed(loop)]

        w = CyclotomicMatrix.eye(self.dim, self.conductor)
        for src, tgt in loop:
            u = self.connection[(src, tgt)]
            w = u * w  # Ordered path-composition

        return w

    def compute_curvature_defect(self) -> CyclotomicMatrix:
        """Compute the curvature defect cochain K(h) = W(h) - I."""
        w = self.compute_hinge_holonomy()
        eye = CyclotomicMatrix.eye(self.dim, self.conductor)
        return w - eye

    def wilson_loop_trace(self) -> Cyclotomic:
        """Normalized gauge-invariant Wilson loop trace: 1/dim * Tr(W(h))."""
        w = self.compute_hinge_holonomy()
        return w.trace() * Fraction(1, self.dim)

    def apply_gauge_transformation(self, gauge_elements: Dict[str, CyclotomicMatrix]) -> None:
        """Apply local gauge transformations g(sigma) at each 4-simplex.

        Under gauge transformation:
            U(sigma, sigma') -> g(sigma) * U(sigma, sigma') * g(sigma')^{-1}.
        """
        for (src, tgt), u in list(self.connection.items()):
            g_src = gauge_elements.get(src, CyclotomicMatrix.eye(self.dim, self.conductor))
            g_tgt = gauge_elements.get(tgt, CyclotomicMatrix.eye(self.dim, self.conductor))
            new_u = g_src * u * g_tgt.adjoint()
            self.connection[(src, tgt)] = new_u


# ---------------------------------------------------------------------------
# 6. Non-Abelian Discrete Bianchi Identity on 3-Cells and 4-Simplices
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TetrahedronBianchiVerification:
    """Receipt certifying discrete Bianchi identity verification on a 3-simplex (tetrahedron)."""

    tetrahedron: Tuple[int, int, int, int]
    basepoint: int
    face_holonomies: Dict[Tuple[int, int, int], CyclotomicMatrix]
    based_face_holonomies: List[CyclotomicMatrix]
    bianchi_product: CyclotomicMatrix
    curvature_defect: CyclotomicMatrix
    is_bianchi_satisfied: bool
    linear_residual: CyclotomicMatrix


@dataclass(frozen=True)
class FourSimplexBianchiVerification:
    """Receipt certifying discrete Bianchi identity verification across all 3-cells of a 4-simplex."""

    simplex_vertices: Tuple[int, int, int, int, int]
    universal_basepoint: int
    tetrahedra_verifications: List[TetrahedronBianchiVerification]
    boundary_bianchi_product: CyclotomicMatrix
    is_all_tetrahedra_satisfied: bool
    boundary_curvature_defect: CyclotomicMatrix


class FourSimplexGaugeSystem:
    """Exact non-abelian gauge system on a single 4-simplex with 10 directed links."""

    def __init__(
        self,
        vertices: Sequence[int] = (0, 1, 2, 3, 4),
        default_identity_group: str = "SU2",
        conductor: int = 8,
    ) -> None:
        v = tuple(sorted(set(vertices)))
        if len(v) != 5:
            raise ValueError(f"4-simplex requires 5 distinct vertices, got {v}")
        self.vertices: Tuple[int, int, int, int, int] = v  # type: ignore
        self.conductor = conductor
        self.group_type = default_identity_group
        self.dim = 2 if default_identity_group == "SU2" else 4
        self.simplex = Simplex4D(self.vertices)

        # Links on all 10 edges: (u, v) -> CyclotomicMatrix
        self.links: Dict[Tuple[int, int], CyclotomicMatrix] = {}
        eye = CyclotomicMatrix.eye(self.dim, conductor)
        for i in range(5):
            for j in range(i + 1, 5):
                u, w = self.vertices[i], self.vertices[j]
                self.links[(u, w)] = eye
                self.links[(w, u)] = eye

    def set_link(self, u: int, v: int, matrix: CyclotomicMatrix) -> None:
        """Assign exact unitary transport matrix to directed edge u -> v."""
        assert matrix.is_unitary(), "Link matrix must be unitary"
        self.links[(u, v)] = matrix
        self.links[(v, u)] = matrix.adjoint()

    def get_link(self, u: int, v: int) -> CyclotomicMatrix:
        """Retrieve transport matrix for directed edge u -> v."""
        return self.links[(u, v)]

    def loop_holonomy(self, path: Sequence[int]) -> CyclotomicMatrix:
        """Compute parallel transport along directed path v0 -> v1 -> ... -> vk.

        For a closed loop (vk == v0), returns the holonomy matrix W in U(n).
        """
        if len(path) < 2:
            return CyclotomicMatrix.eye(self.dim, self.conductor)
        res = CyclotomicMatrix.eye(self.dim, self.conductor)
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            res = self.links[(u, v)] * res
        return res

    def face_holonomy(self, v0: int, v1: int, v2: int) -> CyclotomicMatrix:
        """Holonomy along directed triangular face loop: v0 -> v1 -> v2 -> v0."""
        return self.loop_holonomy([v0, v1, v2, v0])

    def face_curvature_defect(self, v0: int, v1: int, v2: int) -> CyclotomicMatrix:
        """Curvature defect on triangular face: F(v0, v1, v2) = W(v0, v1, v2) - I."""
        w = self.face_holonomy(v0, v1, v2)
        eye = CyclotomicMatrix.eye(self.dim, self.conductor)
        return w - eye

    def verify_tetrahedron_bianchi(
        self,
        tau: Tuple[int, int, int, int],
        basepoint: Optional[int] = None,
    ) -> TetrahedronBianchiVerification:
        """Verify non-abelian discrete Bianchi identity on a 3-simplex (tetrahedron) tau.

        Let vertices be (v0, v1, v2, v3) with chosen basepoint v0.
        Faces meeting at basepoint:
          Face 1: v0 -> v3 -> v1 -> v0 (holonomy W1)
          Face 2: v0 -> v2 -> v3 -> v0 (holonomy W2)
          Face 3: v0 -> v1 -> v2 -> v0 (holonomy W3)
        Opposite face (v1, v2, v3):
          Loop: v1 -> v2 -> v3 -> v1
          Transported to basepoint v0 via edge v0 -> v1:
          W_opp_0 = U(v1, v0) * W(v1, v2, v3) * U(v0, v1)
        Discrete Bianchi operator:
          B(tau) = W1 * W2 * W3 * (W_opp_0)^dagger.
        Discrete Bianchi identity asserts:
          B(tau) == I identically.
        Linear residual:
          (d_A F) = F1 + F2 + F3 - F_opp_0 = O(F^2).
        """
        sorted_tau = tuple(sorted(tau))
        if len(sorted_tau) != 4:
            raise ValueError(f"Tetrahedron must have 4 distinct vertices, got {tau}")
        if basepoint is None:
            basepoint = sorted_tau[0]
        if basepoint not in sorted_tau:
            raise ValueError(f"Basepoint {basepoint} must be one of the tetrahedron vertices {sorted_tau}")

        other = [v for v in sorted_tau if v != basepoint]
        v0 = basepoint
        v1, v2, v3 = other[0], other[1], other[2]

        w1 = self.loop_holonomy([v0, v3, v1, v0])
        w2 = self.loop_holonomy([v0, v2, v3, v0])
        w3 = self.loop_holonomy([v0, v1, v2, v0])

        w_opp_v1 = self.loop_holonomy([v1, v2, v3, v1])
        # Transport to v0 along link v0 -> v1
        w_opp_0 = self.links[(v1, v0)] * w_opp_v1 * self.links[(v0, v1)]

        p123 = w1 * w2 * w3
        b_prod = p123 * w_opp_0.adjoint()
        eye = CyclotomicMatrix.eye(self.dim, self.conductor)
        curv_defect = b_prod - eye
        is_sat = (b_prod == eye)

        f1 = w1 - eye
        f2 = w2 - eye
        f3 = w3 - eye
        f_opp = w_opp_0 - eye
        lin_res = (f1 + f2 + f3) - f_opp

        face_hols = {
            (v0, v3, v1): w1,
            (v0, v2, v3): w2,
            (v0, v1, v2): w3,
            (v1, v2, v3): w_opp_v1,
        }

        return TetrahedronBianchiVerification(
            tetrahedron=sorted_tau,  # type: ignore
            basepoint=v0,
            face_holonomies=face_hols,
            based_face_holonomies=[w1, w2, w3, w_opp_0],
            bianchi_product=b_prod,
            curvature_defect=curv_defect,
            is_bianchi_satisfied=is_sat,
            linear_residual=lin_res,
        )

    def verify_four_simplex_bianchi(
        self,
        universal_basepoint: int = 0,
    ) -> FourSimplexBianchiVerification:
        """Verify non-abelian discrete Bianchi identity across all 5 tetrahedra of the 4-simplex.

        For each tetrahedron tau in d(Delta^4):
          Compute B(tau, basepoint).
          If basepoint != universal_basepoint, transport to universal_basepoint:
            B_0(tau) = U(tau_base, 0) * B(tau, tau_base) * U(0, tau_base).
        Computes boundary Bianchi product prod B_0(tau) == I.
        """
        tetrahedra = self.simplex.tetrahedra()
        verifications: List[TetrahedronBianchiVerification] = []
        b_boundary = CyclotomicMatrix.eye(self.dim, self.conductor)

        for tau in tetrahedra:
            tau_base = universal_basepoint if universal_basepoint in tau else tau[0]
            ver = self.verify_tetrahedron_bianchi(tau, basepoint=tau_base)
            verifications.append(ver)

            # Transport to universal_basepoint if different
            if tau_base != universal_basepoint:
                u_to_univ = self.links[(tau_base, universal_basepoint)]
                u_from_univ = self.links[(universal_basepoint, tau_base)]
                b_univ = u_to_univ * ver.bianchi_product * u_from_univ
            else:
                b_univ = ver.bianchi_product

            b_boundary = b_univ * b_boundary

        eye = CyclotomicMatrix.eye(self.dim, self.conductor)
        all_sat = all(v.is_bianchi_satisfied for v in verifications) and (b_boundary == eye)

        return FourSimplexBianchiVerification(
            simplex_vertices=self.vertices,
            universal_basepoint=universal_basepoint,
            tetrahedra_verifications=verifications,
            boundary_bianchi_product=b_boundary,
            is_all_tetrahedra_satisfied=all_sat,
            boundary_curvature_defect=b_boundary - eye,
        )

    def apply_gauge_transformation(self, node_elements: Dict[int, CyclotomicMatrix]) -> None:
        """Apply local gauge transformations Omega(v) at each vertex of the 4-simplex.

        Under gauge transformation:
          U(u, v) -> Omega(u) * U(u, v) * Omega(v)^dagger.
        """
        for (u, v), mat in list(self.links.items()):
            g_u = node_elements.get(u, CyclotomicMatrix.eye(self.dim, self.conductor))
            g_v = node_elements.get(v, CyclotomicMatrix.eye(self.dim, self.conductor))
            self.links[(u, v)] = g_u * mat * g_v.adjoint()

