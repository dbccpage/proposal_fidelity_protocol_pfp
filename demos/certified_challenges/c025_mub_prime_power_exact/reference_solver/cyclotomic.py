# AuthorityEffect: None.
"""
Exact cyclotomic field arithmetic over Q(zeta_m).

Provides exact arithmetic for cyclotomic fields Q(zeta_m) represented as polynomials
modulo Phi_m(x) with rational coefficients (fractions.Fraction).
Conforms to strict RFC 8785 canonical rational encoding (unit denominators serialized without /1).
"""

from fractions import Fraction
from typing import List, Tuple, Union


def format_fraction(f: Fraction) -> str:
    """Format Fraction to exact wire canonical form (e.g. '1', '-3', '2/3')."""
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def parse_fraction(val: Union[str, int, Fraction]) -> Fraction:
    """Parse string, integer, or Fraction into Fraction."""
    if isinstance(val, Fraction):
        return val
    if isinstance(val, int):
        return Fraction(val, 1)
    return Fraction(val)


def get_cyclotomic_polynomial(m: int) -> List[Fraction]:
    """
    Compute cyclotomic polynomial Phi_m(x) as list of coefficients [a_0, a_1, ..., a_deg]
    such that Phi_m(x) = sum_{k=0}^deg a_k x^k.
    """
    if m == 1:
        return [Fraction(-1), Fraction(1)]
    if m == 2:
        return [Fraction(1), Fraction(1)]
    if m == 3:
        return [Fraction(1), Fraction(1), Fraction(1)]
    if m == 4:
        return [Fraction(1), Fraction(0), Fraction(1)]
    if m == 5:
        return [Fraction(1), Fraction(1), Fraction(1), Fraction(1), Fraction(1)]
    if m == 6:
        return [Fraction(1), Fraction(-1), Fraction(1)]
    if m == 7:
        return [
            Fraction(1),
            Fraction(1),
            Fraction(1),
            Fraction(1),
            Fraction(1),
            Fraction(1),
            Fraction(1),
        ]
    if m == 8:
        return [Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(1)]
    if m == 9:
        return [
            Fraction(1),
            Fraction(0),
            Fraction(0),
            Fraction(1),
            Fraction(0),
            Fraction(0),
            Fraction(1),
        ]
    if m == 10:
        return [Fraction(1), Fraction(-1), Fraction(1), Fraction(-1), Fraction(1)]
    if m == 12:
        return [Fraction(1), Fraction(0), Fraction(-1), Fraction(0), Fraction(1)]
    if m == 20:
        # Phi_20(x) = x^8 - x^6 + x^4 - x^2 + 1
        poly = [Fraction(0)] * 9
        poly[0] = Fraction(1)
        poly[2] = Fraction(-1)
        poly[4] = Fraction(1)
        poly[6] = Fraction(-1)
        poly[8] = Fraction(1)
        return poly

    # General Moebius inversion formula for Phi_m(x)
    divisors = [d for d in range(1, m + 1) if m % d == 0]
    mu = [0] * (m + 1)
    mu[1] = 1
    primes = []
    is_prime = [True] * (m + 1)
    for i in range(2, m + 1):
        if is_prime[i]:
            primes.append(i)
            mu[i] = -1
        for p in primes:
            if i * p > m:
                break
            is_prime[i * p] = False
            if i % p == 0:
                mu[i * p] = 0
                break
            else:
                mu[i * p] = -mu[i]

    def poly_mul(p1: List[Fraction], p2: List[Fraction]) -> List[Fraction]:
        res = [Fraction(0)] * (len(p1) + len(p2) - 1)
        for i, c1 in enumerate(p1):
            for j, c2 in enumerate(p2):
                res[i + j] += c1 * c2
        return res

    def poly_div(dividend: List[Fraction], divisor: List[Fraction]) -> List[Fraction]:
        quot = [Fraction(0)] * (len(dividend) - len(divisor) + 1)
        rem = list(dividend)
        lead_div = divisor[-1]
        for i in range(len(quot) - 1, -1, -1):
            if rem[i + len(divisor) - 1] != 0:
                q = rem[i + len(divisor) - 1] / lead_div
                quot[i] = q
                for j in range(len(divisor)):
                    rem[i + j] -= q * divisor[j]
        return quot

    num_factors = [d for d in divisors if mu[m // d] == 1]
    den_factors = [d for d in divisors if mu[m // d] == -1]

    curr = [Fraction(1)]
    for d in num_factors:
        fac = [Fraction(0)] * (d + 1)
        fac[0] = Fraction(-1)
        fac[d] = Fraction(1)
        curr = poly_mul(curr, fac)

    for d in den_factors:
        fac = [Fraction(0)] * (d + 1)
        fac[0] = Fraction(-1)
        fac[d] = Fraction(1)
        curr = poly_div(curr, fac)

    while len(curr) > 1 and curr[-1] == 0:
        curr.pop()
    return curr


def poly_reduce(coeffs: List[Fraction], modulus: List[Fraction]) -> List[Fraction]:
    """Reduce polynomial coeffs modulo monic modulus."""
    deg_m = len(modulus) - 1
    rem = list(coeffs)
    while len(rem) > 1 and rem[-1] == 0:
        rem.pop()
    if len(rem) <= deg_m:
        return rem + [Fraction(0)] * (deg_m - len(rem))

    lead_mod = modulus[-1]
    for i in range(len(rem) - 1, deg_m - 1, -1):
        if rem[i] != 0:
            q = rem[i] / lead_mod
            rem[i] = Fraction(0)
            for j in range(deg_m):
                rem[i - deg_m + j] -= q * modulus[j]

    res = rem[:deg_m]
    if len(res) < deg_m:
        res = res + [Fraction(0)] * (deg_m - len(res))
    return res


class CyclotomicElement:
    """
    An element of Q(zeta_m).
    Represented by canonical coefficients of length m (powers of zeta_m^0 .. zeta_m^{m-1}).
    Internal reduction modulo Phi_m(x) is maintained for equality and arithmetic.
    """

    def __init__(self, m: int, coeffs: Union[List[Union[Fraction, str, int]], Tuple]):
        self.m = m
        parsed = [parse_fraction(c) for c in coeffs]
        if len(parsed) < m:
            parsed = parsed + [Fraction(0)] * (m - len(parsed))
        elif len(parsed) > m:
            folded = [Fraction(0)] * m
            for idx, c in enumerate(parsed):
                folded[idx % m] += c
            parsed = folded
        self.coeffs: List[Fraction] = parsed
        self._phi_m = get_cyclotomic_polynomial(m)

    @classmethod
    def zero(cls, m: int) -> "CyclotomicElement":
        return cls(m, [Fraction(0)] * m)

    @classmethod
    def one(cls, m: int) -> "CyclotomicElement":
        coeffs = [Fraction(0)] * m
        coeffs[0] = Fraction(1)
        return cls(m, coeffs)

    @classmethod
    def from_rational(cls, m: int, r: Union[Fraction, int, str]) -> "CyclotomicElement":
        coeffs = [Fraction(0)] * m
        coeffs[0] = parse_fraction(r)
        return cls(m, coeffs)

    @classmethod
    def zeta_pow(cls, m: int, k: int) -> "CyclotomicElement":
        power = k % m
        coeffs = [Fraction(0)] * m
        coeffs[power] = Fraction(1)
        return cls(m, coeffs)

    def canonical_reduced(self) -> List[Fraction]:
        """Reduce coeffs modulo Phi_m(x) to unique canonical form."""
        return poly_reduce(self.coeffs, self._phi_m)

    def is_zero(self) -> bool:
        can = self.canonical_reduced()
        return all(c == 0 for c in can)

    def is_rational(self) -> Tuple[bool, Fraction]:
        """Check if element is purely rational (all higher powers in reduced form are zero)."""
        can = self.canonical_reduced()
        if all(c == 0 for c in can[1:]):
            return True, can[0]
        return False, Fraction(0)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CyclotomicElement):
            return False
        if self.m == other.m:
            can_s = self.canonical_reduced()
            can_o = other.canonical_reduced()
            return can_s == can_o
        from math import lcm

        l = lcm(self.m, other.m)
        s_lift = self.lift_to(l)
        o_lift = other.lift_to(l)
        return s_lift == o_lift

    def lift_to(self, new_m: int) -> "CyclotomicElement":
        """Lift element from Q(zeta_m) to Q(zeta_{new_m}) where m | new_m."""
        if new_m == self.m:
            return self
        if new_m % self.m != 0:
            raise ValueError(f"Cannot lift Q(zeta_{self.m}) to Q(zeta_{new_m}): not a multiple")
        factor = new_m // self.m
        new_coeffs = [Fraction(0)] * new_m
        for k, c in enumerate(self.coeffs):
            if c != 0:
                new_coeffs[k * factor] += c
        return CyclotomicElement(new_m, new_coeffs)

    def __add__(self, other: "CyclotomicElement") -> "CyclotomicElement":
        if self.m != other.m:
            from math import lcm

            l = lcm(self.m, other.m)
            return self.lift_to(l) + other.lift_to(l)
        new_c = [c1 + c2 for c1, c2 in zip(self.coeffs, other.coeffs)]
        return CyclotomicElement(self.m, new_c)

    def __sub__(self, other: "CyclotomicElement") -> "CyclotomicElement":
        if self.m != other.m:
            from math import lcm

            l = lcm(self.m, other.m)
            return self.lift_to(l) - other.lift_to(l)
        new_c = [c1 - c2 for c1, c2 in zip(self.coeffs, other.coeffs)]
        return CyclotomicElement(self.m, new_c)

    def __mul__(self, other: Union["CyclotomicElement", Fraction, int]) -> "CyclotomicElement":
        if isinstance(other, (Fraction, int)):
            f = parse_fraction(other)
            return CyclotomicElement(self.m, [c * f for c in self.coeffs])
        if self.m != other.m:
            from math import lcm

            l = lcm(self.m, other.m)
            return self.lift_to(l) * other.lift_to(l)
        res = [Fraction(0)] * self.m
        for i, c1 in enumerate(self.coeffs):
            if c1 == 0:
                continue
            for j, c2 in enumerate(other.coeffs):
                if c2 == 0:
                    continue
                res[(i + j) % self.m] += c1 * c2
        return CyclotomicElement(self.m, res)

    def conjugate(self) -> "CyclotomicElement":
        """Complex conjugate: zeta_m^k -> zeta_m^{-k} = zeta_m^{(m-k)%m}."""
        res = [Fraction(0)] * self.m
        for k, c in enumerate(self.coeffs):
            if c != 0:
                res[(self.m - (k % self.m)) % self.m] += c
        return CyclotomicElement(self.m, res)

    def abs_sq(self) -> "CyclotomicElement":
        """Compute |z|^2 = z * z^*."""
        return self * self.conjugate()

    def to_wire(self) -> List[str]:
        """Convert coefficients to wire format list of m rational strings."""
        return [format_fraction(c) for c in self.coeffs]

    @classmethod
    def from_wire(cls, m: int, wire: List[str]) -> "CyclotomicElement":
        return cls(m, wire)

    def __repr__(self) -> str:
        terms = []
        for k, c in enumerate(self.coeffs):
            if c != 0:
                terms.append(f"{format_fraction(c)}*z^{k}")
        return " + ".join(terms) if terms else "0"
