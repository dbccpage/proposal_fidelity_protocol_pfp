"""Integer factorization and primality testing for C048.
Uses Miller-Rabin deterministic test and Pollard's rho algorithm.
"""

import math
from typing import Set


def is_prime(n: int) -> bool:
    """Deterministic Miller-Rabin primality test for n < 2^64."""
    if n < 2:
        return False
    if n in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        return True
    if any(n % p == 0 for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)):
        return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    # Deterministic bases for 64-bit integers
    bases = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for a in bases:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def pollard_rho(n: int) -> int:
    """Find a non-trivial factor of composite n using Pollard's rho algorithm."""
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3
    if is_prime(n):
        return n

    for c in range(1, 100):
        def f(x):
            return (pow(x, 2, n) + c) % n
        x = 2
        y = 2
        d = 1
        while d == 1:
            x = f(x)
            y = f(f(y))
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d
    return n


def prime_factors(n: int) -> Set[int]:
    """Return all distinct prime factors of integer n."""
    n = abs(n)
    if n <= 1:
        return set()

    factors = set()
    # Trial division for small primes
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71):
        if n % p == 0:
            factors.add(p)
            while n % p == 0:
                n //= p
        if n == 1:
            return factors

    # Recursive factorization
    stack = [n]
    while stack:
        cur = stack.pop()
        if cur == 1:
            continue
        if is_prime(cur):
            factors.add(cur)
        else:
            divisor = pollard_rho(cur)
            if divisor == cur:
                # Fallback: step trial division
                d_found = False
                for d in range(73, min(10000, int(math.isqrt(cur)) + 1), 2):
                    if cur % d == 0:
                        stack.append(d)
                        stack.append(cur // d)
                        d_found = True
                        break
                if not d_found:
                    factors.add(cur)
            else:
                stack.append(divisor)
                stack.append(cur // divisor)

    return factors
