# AuthorityEffect: None.
"""
Finite field and Galois ring arithmetic for MUB constructions.

Provides exact algebraic structures:
1. Galois Rings GR(4, r) for characteristic 2 dimensions d = 2^r (d = 2, 4, 8):
   - Basic primitive polynomials over Z_4.
   - Exact Teichmuller sets T_r of size 2^r.
   - Frobenius automorphism sigma and trace map Tr: GR(4, r) -> Z_4.
2. Odd prime fields F_p for p in {3, 5, 7}.
3. Odd prime power field GF(9) = F_3[u] / (u^2 + 1) with trace Tr: GF(9) -> F_3.
"""

from typing import List, Tuple


class GaloisRingGR4:
    """
    Galois ring GR(4, r) = Z_4[xi] / (h(xi)) for r in {1, 2, 3}.
    Elements are represented as tuples of coefficients (c_0, ..., c_{r-1}) in Z_4 = {0, 1, 2, 3}.
    """

    def __init__(self, r: int):
        if r not in (1, 2, 3):
            raise ValueError(f"Unsupported Galois ring rank r={r} (expected 1, 2, or 3)")
        self.r = r
        # Precompute Teichmuller set T and trace
        self.teichmuller_set: List[Tuple[int, ...]] = self._build_teichmuller_set()

    def zero(self) -> Tuple[int, ...]:
        return tuple(0 for _ in range(self.r))

    def one(self) -> Tuple[int, ...]:
        res = [0] * self.r
        res[0] = 1
        return tuple(res)

    def add(self, p: Tuple[int, ...], q: Tuple[int, ...]) -> Tuple[int, ...]:
        return tuple((p[i] + q[i]) % 4 for i in range(self.r))

    def sub(self, p: Tuple[int, ...], q: Tuple[int, ...]) -> Tuple[int, ...]:
        return tuple((p[i] - q[i]) % 4 for i in range(self.r))

    def scale_int(self, p: Tuple[int, ...], k: int) -> Tuple[int, ...]:
        return tuple((c * k) % 4 for c in p)

    def mul(self, p: Tuple[int, ...], q: Tuple[int, ...]) -> Tuple[int, ...]:
        if self.r == 1:
            return ((p[0] * q[0]) % 4,)
        elif self.r == 2:
            # h(xi) = xi^2 + xi + 1 => xi^2 = 3*xi + 3 mod 4
            c0 = (p[0] * q[0] + 3 * p[1] * q[1]) % 4
            c1 = (p[0] * q[1] + p[1] * q[0] + 3 * p[1] * q[1]) % 4
            return (c0, c1)
        else:  # r == 3
            # h(xi) = xi^3 + 2*xi^2 + xi + 3 => xi^3 = 2*xi^2 + 3*xi + 1 mod 4
            # xi^4 = 3*xi^2 + 3*xi + 2 mod 4
            res = [0] * 5
            for i in range(3):
                for j in range(3):
                    res[i + j] = (res[i + j] + p[i] * q[j]) % 4
            if res[4] != 0:
                c = res[4]
                res[2] = (res[2] + 3 * c) % 4
                res[1] = (res[1] + 3 * c) % 4
                res[0] = (res[0] + 2 * c) % 4
                res[4] = 0
            if res[3] != 0:
                c = res[3]
                res[2] = (res[2] + 2 * c) % 4
                res[1] = (res[1] + 3 * c) % 4
                res[0] = (res[0] + 1 * c) % 4
                res[3] = 0
            return tuple(res[:3])

    def frobenius(self, p: Tuple[int, ...]) -> Tuple[int, ...]:
        """Frobenius automorphism sigma: fixes Z_4 and acts as xi -> xi^2."""
        if self.r == 1:
            return p
        elif self.r == 2:
            # sigma(p0 + p1*xi) = p0 + p1*xi^2 = p0 + p1*(3 + 3*xi) = (p0 + 3*p1) + 3*p1*xi
            p0, p1 = p
            return ((p0 + 3 * p1) % 4, (3 * p1) % 4)
        else:  # r == 3
            # sigma(1) = (1, 0, 0)
            # sigma(xi) = xi^2 = (0, 0, 1)
            # sigma(xi^2) = xi^4 = 3*xi^2 + 3*xi + 2 = (2, 3, 3)
            p0, p1, p2 = p
            c0 = (p0 + 2 * p2) % 4
            c1 = (3 * p2) % 4
            c2 = (p1 + 3 * p2) % 4
            return (c0, c1, c2)

    def trace(self, p: Tuple[int, ...]) -> int:
        """Trace map Tr: GR(4, r) -> Z_4 = sum_{j=0}^{r-1} sigma^j(p). Returns int in {0, 1, 2, 3}."""
        if self.r == 1:
            return p[0] % 4
        elif self.r == 2:
            f1 = self.frobenius(p)
            tot = self.add(p, f1)
            return tot[0] % 4
        else:  # r == 3
            f1 = self.frobenius(p)
            f2 = self.frobenius(f1)
            tot = self.add(self.add(p, f1), f2)
            return tot[0] % 4

    def _build_teichmuller_set(self) -> List[Tuple[int, ...]]:
        """Construct the Teichmuller set T_r of size 2^r where elements satisfy x^{2^r} = x."""
        if self.r == 1:
            return [(0,), (1,)]
        elif self.r == 2:
            # T = {0, 1, xi, xi^2}
            zero = (0, 0)
            one = (1, 0)
            xi = (0, 1)
            xi2 = self.mul(xi, xi)
            return [zero, one, xi, xi2]
        else:  # r == 3
            # T = {0, 1, xi, xi^2, xi^3, xi^4, xi^5, xi^6}
            zero = (0, 0, 0)
            one = (1, 0, 0)
            xi = (0, 1, 0)
            powers = [one]
            curr = xi
            for _ in range(6):
                powers.append(curr)
                curr = self.mul(curr, xi)
            return [zero] + powers


class FiniteFieldGF9:
    """
    Finite field GF(9) = F_3[u] / (u^2 + 1).
    Elements are represented as pairs (c_0, c_1) in {0, 1, 2}^2 representing c_0 + c_1 * u.
    """

    def __init__(self):
        self.elements: List[Tuple[int, int]] = [(c0, c1) for c1 in range(3) for c0 in range(3)]

    def add(self, p: Tuple[int, int], q: Tuple[int, int]) -> Tuple[int, int]:
        return ((p[0] + q[0]) % 3, (p[1] + q[1]) % 3)

    def sub(self, p: Tuple[int, int], q: Tuple[int, int]) -> Tuple[int, int]:
        return ((p[0] - q[0]) % 3, (p[1] - q[1]) % 3)

    def mul(self, p: Tuple[int, int], q: Tuple[int, int]) -> Tuple[int, int]:
        # (p0 + p1*u)*(q0 + q1*u) = (p0*q0 - p1*q1) + (p0*q1 + p1*q0)*u mod 3
        c0 = (p[0] * q[0] - p[1] * q[1]) % 3
        c1 = (p[0] * q[1] + p[1] * q[0]) % 3
        return (c0, c1)

    def trace(self, p: Tuple[int, int]) -> int:
        """Trace map Tr: GF(9) -> F_3. Tr(c0 + c1*u) = 2*c0 = -c0 mod 3."""
        return (2 * p[0]) % 3
