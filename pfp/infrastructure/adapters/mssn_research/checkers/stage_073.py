"""Target checker of record for MSS-073, row 73 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 73): check uniform refinement estimates against the target
functional. Negative instance: convergence inferred from a single mesh is
rejected.

Input (closed): ``{"integrand": [c], "depths": [[k, S_k]], "constant": C |
null, "start": k0}``. The target functional is the exact integral I of the
polynomial f (ascending rational coefficients) over [0, 1]. At depth k the
mesh has 2^k equal cells of width h_k = 2^-k, and S_k is the left-end sum.
The claim is a refinement estimate |S_k - I| <= C h_k for every depth
k >= k0; ``depths`` lists producer values of S_k.

The checker decides the claim for every depth, not at the listed ones. For a
polynomial f of degree d, S is a polynomial in h of degree <= d (Faulhaber),
found exactly by interpolating S at h = 1/N, N = 1..d+1; S(0) = I. With
g(h) = (S(h) - I) / h, the claim is |g(2^-k)| <= C for all k >= k0. If
|g(0)| > C it fails; otherwise an explicit depth K is computed beyond which
the tail of g cannot break the bound (using the first nonzero higher
coefficient when |g(0)| = C), and the depths k0..K-1 are checked exactly.
Listed S_k are recomputed independently by direct summation.

Declared input class: polynomial integrands on [0, 1] with rational
coefficients, degree <= 8; left-end sums on dyadic meshes; listed depths
k <= 12; the explicit depth K at most k0 + 200. No continuum object is formed;
the rate is the only statement that descends.

Clauses, decided in this order:

- C1 ``R073_NO_RATE``: no constant is given, so the claim rests on listed
  meshes alone (the level's negative: one depth offered as convergence);
- C2 ``R073_SUM_MISMATCH``: a listed S_k differs from the exact left-end sum;
- C3 ``R073_BOUND_FAILS``: some depth k >= k0 has |S_k - I| > C h_k.
"""

STAGE = 73
ROW_SHA256 = "sha256:898200faf233c08ed7baf438ae0968dce7024073d145943199219f805174ce4b"
FIELDS = ("constant", "depths", "integrand", "start")
CLAUSES = (
    ("C1", "R073_NO_RATE"),
    ("C2", "R073_SUM_MISMATCH"),
    ("C3", "R073_BOUND_FAILS"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"constant": None, "depths": [[3, "7/16"]], "integrand": ["0/1", "1/1"], "start": 3}
OWN_NEGATIVE_CODE = "R073_NO_RATE"


def _evaluate(p, x):
    total = Fraction(0)
    for c in reversed(p):
        total = total * x + c
    return total


def _left_sum(f, cells):
    return sum((_evaluate(f, Fraction(i, cells)) for i in range(cells)), Fraction(0)) / cells


def _interpolate(points):
    size = len(points)
    out = [Fraction(0)] * size
    for k, (xk, yk) in enumerate(points):
        basis, scale = [Fraction(1)], Fraction(1)
        for j, (xj, _) in enumerate(points):
            if j != k:
                basis = [Fraction(0)] + basis
                for t in range(len(basis) - 1):
                    basis[t] -= xj * basis[t + 1]
                scale *= xk - xj
        for t in range(size):
            out[t] += yk * basis[t] / scale
    return out


def _holds_everywhere(g, bound, k0):
    c, tail = g[0], g[1:]
    if abs(c) > bound:
        return False
    if all(x == 0 for x in tail):
        return True
    if abs(c) == bound:
        if bound == 0:
            return False
        m = next(j for j, x in enumerate(tail) if x != 0)
        if (c > 0) == (tail[m] > 0):
            return False
        rest = sum((abs(x) for x in tail[m + 1:]), Fraction(0))
        total = sum((abs(x) for x in tail), Fraction(0))

        def safe(h):
            return h * rest < abs(tail[m]) and h * total <= bound
    else:
        total = sum((abs(x) for x in tail), Fraction(0))

        def safe(h):
            return h * total <= bound - abs(c)
    k = k0
    while not safe(Fraction(1, 2 ** k)):
        _require(k - k0 < 200, "R_SCHEMA")
        if abs(_evaluate(g, Fraction(1, 2 ** k))) > bound:
            return False
        k += 1
    return True


def _decide(payload):
    f = _rats(payload["integrand"])
    _require(1 <= len(f) <= 9, "R_SCHEMA")
    k0 = _nat(payload["start"])
    depths = []
    for item in _seq(payload["depths"]):
        _seq(item, 2)
        k = _nat(item[0])
        _require(k <= 12, "R_SCHEMA")
        depths.append((k, _rat(item[1])))
    _require(depths, "R_SCHEMA")
    constant = payload["constant"]
    _require(constant is not None, "R073_NO_RATE")
    constant = _rat(constant)
    for k, claimed in depths:
        _require(claimed == _left_sum(f, 2 ** k), "R073_SUM_MISMATCH")
    integral = sum((c / (p + 1) for p, c in enumerate(f)), Fraction(0))
    s = _interpolate([(Fraction(1, n), _left_sum(f, n)) for n in range(1, len(f) + 1)])
    if s[0] != integral:
        raise ValueError("the left sums do not tend to the integral")
    g = s[1:] or [Fraction(0)]
    _require(_holds_everywhere(g, constant, k0), "R073_BOUND_FAILS")
