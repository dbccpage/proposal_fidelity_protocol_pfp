"""Exact Hilbert symbol calculations over Q_v for C048.
Computes (u, w)_v for v in {inf, 2, odd primes p} under Serre's formulas.
"""

from typing import Union


def legendre_symbol(a: int, p: int) -> int:
    """Compute the Legendre symbol (a / p) for odd prime p via Euler's criterion."""
    a = a % p
    if a == 0:
        return 0
    res = pow(a, (p - 1) // 2, p)
    return -1 if res == p - 1 else 1


def hilbert_symbol(u: int, w: int, place: Union[int, str]) -> int:
    """Compute the Hilbert symbol (u, w)_place for nonzero integers u, w.
    place can be 'inf', 2, or an odd prime p.
    Returns +1 or -1.
    """
    if u == 0 or w == 0:
        raise ValueError("Hilbert symbol undefined for zero arguments")

    if place == "inf":
        return -1 if (u < 0 and w < 0) else 1

    p = int(place)
    if p < 2:
        raise ValueError(f"Invalid prime place: {place}")

    # Extract p-adic valuations
    alpha = 0
    u0 = u
    while u0 % p == 0:
        u0 //= p
        alpha += 1

    beta = 0
    w0 = w
    while w0 % p == 0:
        w0 //= p
        beta += 1

    if p == 2:
        # Serre formula for p = 2:
        # eps(x) = (x - 1) / 2 mod 2 for odd x
        # omega(x) = (x^2 - 1) / 8 mod 2 for odd x
        eps_u = ((u0 - 1) // 2) % 2
        eps_w = ((w0 - 1) // 2) % 2
        omega_u = ((u0 * u0 - 1) // 8) % 2
        omega_w = ((w0 * w0 - 1) // 8) % 2

        exponent = (eps_u * eps_w + alpha * omega_w + beta * omega_u) % 2
        return -1 if exponent == 1 else 1
    else:
        # Serre formula for odd prime p:
        # (-1)^{alpha * beta * (p-1)/2} * (u0 / p)^beta * (w0 / p)^alpha
        exp_sign = (alpha * beta * ((p - 1) // 2)) % 2
        s1 = -1 if exp_sign == 1 else 1

        leg_u = legendre_symbol(u0, p)
        leg_w = legendre_symbol(w0, p)

        term_u = (leg_u**beta) if beta % 2 == 1 else 1
        term_w = (leg_w**alpha) if alpha % 2 == 1 else 1

        return s1 * term_u * term_w
