"""Independent recomputation of published reference values.

Two computations, both in exact rational arithmetic and both independent of
the challenge packages' own code:

- Trace identities for 6d anomaly coefficients. For a representation R of a
  group G with Cartan element F, the package's triple (A, B, C) must satisfy
  tr_R F^2 = A tr F^2 and tr_R F^4 = B tr F^4 + C (tr F^2)^2, where tr is
  the trace in the defining representation. The harness evaluates both sides
  from the weights of R at several rational Cartan points. The check does not
  depend on how a convention splits B and C: any valid triple satisfies it.

- Genus-zero Gopakumar-Vafa invariants of one-parameter Calabi-Yau
  hypersurfaces in weighted projective space, from the hypergeometric period,
  the mirror map and the Yukawa coupling (the method of Candelas, de la Ossa,
  Green and Parkes, 1991), computed as exact power series.

It also flags digests that equal SHA-256 of a trivial input (empty bytes,
``[]``, ``{}``, ``null``), which is what a pin computed over missing data
records.
"""

from __future__ import annotations

import hashlib
import re
from fractions import Fraction
from itertools import combinations, product
from math import factorial
from typing import Any

TRIVIAL_INPUTS = {
    "empty bytes": b"",
    "[]": b"[]",
    "{}": b"{}",
    "null": b"null",
    "newline": b"\n",
    '""': b'""',
}
TRIVIAL_DIGESTS = {hashlib.sha256(v).hexdigest(): k for k, v in TRIVIAL_INPUTS.items()}
CARTAN_POINTS = (
    (
        Fraction(3),
        Fraction(-1, 2),
        Fraction(5, 7),
        Fraction(2, 3),
        Fraction(-4, 5),
        Fraction(1, 9),
        Fraction(7, 4),
        Fraction(-2, 11),
    ),
    (
        Fraction(1, 2),
        Fraction(2),
        Fraction(-3, 4),
        Fraction(5, 3),
        Fraction(1, 7),
        Fraction(-6, 5),
        Fraction(3, 8),
        Fraction(4, 9),
    ),
    (
        Fraction(-5, 3),
        Fraction(7, 2),
        Fraction(1, 4),
        Fraction(-1),
        Fraction(9, 5),
        Fraction(2, 7),
        Fraction(-3, 10),
        Fraction(6, 11),
    ),
)


def trivial_digest_pins(record: Any, path: str = "$") -> list[dict[str, str]]:
    """Every 64-hex string in ``record`` that is SHA-256 of a trivial input."""
    out: list[dict[str, str]] = []
    if isinstance(record, dict):
        for key in sorted(record):
            out.extend(trivial_digest_pins(record[key], f"{path}.{key}"))
    elif isinstance(record, list):
        for index, item in enumerate(record):
            out.extend(trivial_digest_pins(item, f"{path}[{index}]"))
    elif isinstance(record, str) and record in TRIVIAL_DIGESTS:
        out.append({"field": path, "digest_of": TRIVIAL_DIGESTS[record]})
    return out


def _group(name: str) -> tuple[str, int] | None:
    match = re.fullmatch(r"(SU|Sp|SO)\((\d+)\)", name)
    if match:
        return match.group(1), int(match.group(2))
    if name == "G2":
        return "G", 2
    return None


def _cartan(family: str, n: int, point: tuple[Fraction, ...]) -> list[Fraction]:
    if family == "SU":
        xs = list(point[: n - 1])
        return xs + [-sum(xs, Fraction(0))]
    if family == "G":
        xs = list(point[:2])
        return xs + [-sum(xs, Fraction(0))]
    rank = n if family == "Sp" else n // 2
    return list(point[:rank])


def weights(group: str, rep: str, point: tuple[Fraction, ...]) -> list[Fraction] | None:
    """Weights of ``rep`` evaluated at a Cartan point, or None if unsupported."""
    parsed = _group(group)
    if parsed is None:
        return None
    family, n = parsed
    x = _cartan(family, n, point)
    if family == "SU":
        if rep in ("fund", str(n)):
            return list(x)
        if rep == "adj":
            return [a - b for i, a in enumerate(x) for j, b in enumerate(x) if i != j] + [
                Fraction(0)
            ] * (n - 1)
        if rep in ("antisym", f"AS_{n * (n - 1) // 2}"):
            return [x[i] + x[j] for i, j in combinations(range(n), 2)]
        if rep in ("sym", f"S_{n * (n + 1) // 2}"):
            return [x[i] + x[j] for i in range(n) for j in range(i, n)]
        return None
    if family == "Sp":
        fund = [s * xi for xi in x for s in (1, -1)]
        if rep in ("fund", str(2 * n)):
            return fund
        pairs = [
            s * x[i] + t * x[j]
            for i, j in combinations(range(n), 2)
            for s, t in product((1, -1), repeat=2)
        ]
        if rep == "adj":
            return pairs + [s * 2 * xi for xi in x for s in (1, -1)] + [Fraction(0)] * n
        if rep in ("antisym", f"AS_{n * (2 * n - 1) - 1}"):
            return pairs + [Fraction(0)] * (n - 1)
        return None
    if family == "SO":
        rank = n // 2
        odd = n % 2 == 1
        vect = [s * xi for xi in x for s in (1, -1)] + ([Fraction(0)] if odd else [])
        if rep in ("vect", "fund", str(n)):
            return vect
        if rep == "adj":
            pairs = [
                s * x[i] + t * x[j]
                for i, j in combinations(range(rank), 2)
                for s, t in product((1, -1), repeat=2)
            ]
            return (
                pairs
                + ([s * xi for xi in x for s in (1, -1)] if odd else [])
                + [Fraction(0)] * rank
            )
        if rep in ("spinor", "spin"):
            out = []
            for signs in product((1, -1), repeat=rank):
                if not odd and signs.count(-1) % 2 == 1:
                    continue
                out.append(sum((Fraction(s) * xi for s, xi in zip(signs, x)), Fraction(0)) / 2)
            return out
        return None
    if family == "G":
        fund7 = list(x) + [-xi for xi in x] + [Fraction(0)]
        if rep in ("fund", "7"):
            return fund7
        if rep == "adj":
            roots = [a - b for i, a in enumerate(x) for j, b in enumerate(x) if i != j]
            return roots + list(x) + [-xi for xi in x] + [Fraction(0)] * 2
    return None


def _defining(group: str, point: tuple[Fraction, ...]) -> list[Fraction] | None:
    parsed = _group(group)
    if parsed is None:
        return None
    family, n = parsed
    if family == "SO":
        return weights(group, "vect", point)
    if family == "G":
        return weights(group, "fund", point)
    return weights(group, "fund", point)


def trace_identity_check(
    group: str, rep: str, triple: tuple[Fraction, Fraction, Fraction]
) -> dict[str, Any]:
    """Checks tr_R F^2 = A tr F^2 and tr_R F^4 = B tr F^4 + C (tr F^2)^2 at three Cartan points."""
    a, b, c = triple
    failures = []
    implied_c = None
    for point in CARTAN_POINTS:
        rep_w = weights(group, rep, point)
        fund_w = _defining(group, point)
        if rep_w is None or fund_w is None:
            return {"status": "UNSUPPORTED"}
        t2 = sum((w**2 for w in fund_w), Fraction(0))
        t4 = sum((w**4 for w in fund_w), Fraction(0))
        r2 = sum((w**2 for w in rep_w), Fraction(0))
        r4 = sum((w**4 for w in rep_w), Fraction(0))
        if r2 != a * t2:
            failures.append(f"quadratic identity fails: tr_R F^2 = {r2}, A tr F^2 = {a * t2}")
        if r4 != b * t4 + c * t2**2:
            failures.append(
                f"quartic identity fails: tr_R F^4 = {r4}, B tr F^4 + C (tr F^2)^2 = {b * t4 + c * t2**2}"
            )
        if implied_c is None and t2 != 0:
            implied_c = (r4 - b * t4) / t2**2
    return {
        "status": "PASS" if not failures else "FAIL",
        "failures": sorted(set(failures))[:4],
        "c_implied_by_weights_given_b": str(implied_c) if implied_c is not None else None,
    }


def _series_mul(a: list[Fraction], b: list[Fraction], n: int) -> list[Fraction]:
    out = [Fraction(0)] * n
    for i, ai in enumerate(a[:n]):
        if ai == 0:
            continue
        for j, bj in enumerate(b[: n - i]):
            out[i + j] += ai * bj
    return out


def _series_inv(a: list[Fraction], n: int) -> list[Fraction]:
    if a[0] == 0:
        raise ZeroDivisionError("series with zero constant term is not invertible")
    out = [Fraction(0)] * n
    out[0] = 1 / a[0]
    for k in range(1, n):
        acc = sum((a[j] * out[k - j] for j in range(1, min(k, len(a) - 1) + 1)), Fraction(0))
        out[k] = -acc / a[0]
    return out


def _series_exp(a: list[Fraction], n: int) -> list[Fraction]:
    if a and a[0] != 0:
        raise ValueError("exp requires zero constant term")
    out = [Fraction(0)] * n
    out[0] = Fraction(1)
    deriv = [k * a[k] for k in range(1, min(len(a), n))]
    for k in range(1, n):
        acc = sum(
            (deriv[j - 1] * out[k - j] for j in range(1, k + 1) if j - 1 < len(deriv)), Fraction(0)
        )
        out[k] = acc / k
    return out


def _harmonic(m: int) -> Fraction:
    return sum((Fraction(1, k) for k in range(1, m + 1)), Fraction(0))


def gv_invariants(weights_: list[int], max_degree: int) -> dict[str, Any]:
    """Genus-zero GV invariants n_1..n_D of the degree-sum(w) hypersurface in WP(w)."""
    if any(type(w) is not int or w <= 0 for w in weights_):
        raise TypeError("weights must be positive ints")
    d = sum(weights_)
    prod_w = 1
    for w in weights_:
        prod_w *= w
    kappa = Fraction(d, prod_w)
    mu = Fraction(d**d)
    for w in weights_:
        mu /= Fraction(w**w)
    n = max_degree + 1
    a = [
        Fraction(factorial(d * k), 1) / _prod(factorial(w * k) for w in weights_) for k in range(n)
    ]
    tilde = [
        a[k] * (d * _harmonic(d * k) - sum((w * _harmonic(w * k) for w in weights_), Fraction(0)))
        for k in range(n)
    ]
    omega0_inv = _series_inv(a, n)
    f = _series_mul(tilde, omega0_inv, n)
    q_over_z = _series_exp(f, n)
    g = [Fraction(1)] + [Fraction(0)] * (n - 1)
    for k in range(1, n):
        g[k] = k * f[k]
    omega0_sq = _series_mul(a, a, n)
    g3 = _series_mul(_series_mul(g, g, n), g, n)
    delta = [Fraction(1), -mu] + [Fraction(0)] * (n - 2)
    denom = _series_mul(_series_mul(delta, omega0_sq, n), g3, n)
    yukawa_z = [kappa * c for c in _series_inv(denom, n)]
    z_of_q = _reversion(q_over_z, n)
    yukawa_q = _compose(yukawa_z, z_of_q, n)
    counts: dict[int, Fraction] = {}
    for k in range(1, n):
        acc = yukawa_q[k] - sum((counts[m] * m**3 for m in range(1, k) if k % m == 0), Fraction(0))
        counts[k] = acc / k**3
    return {
        "kappa": str(kappa),
        "mu": str(mu),
        "n": {str(k): str(v) for k, v in counts.items()},
        "all_integers": all(v.denominator == 1 for v in counts.values()),
    }


def _prod(values: Any) -> int:
    out = 1
    for v in values:
        out *= v
    return out


def _reversion(q_over_z: list[Fraction], n: int) -> list[Fraction]:
    """Given q = z * E(z) with E(0) = 1, returns coefficients of z(q) = q * R(q), as z-series in q."""
    z = [Fraction(0), Fraction(1)] + [Fraction(0)] * (n - 2)
    for _ in range(n):
        e_of_z = _compose(q_over_z, z, n)
        inv = _series_inv(e_of_z, n)
        z = [Fraction(0)] + inv[: n - 1]
    return z


def _compose(outer: list[Fraction], inner: list[Fraction], n: int) -> list[Fraction]:
    """outer(inner(q)) truncated at q^n; inner has zero constant term."""
    out = [Fraction(0)] * n
    power = [Fraction(1)] + [Fraction(0)] * (n - 1)
    for k in range(n):
        if k < len(outer) and outer[k] != 0:
            for i in range(n):
                out[i] += outer[k] * power[i]
        power = _series_mul(power, inner, n)
    return out


FAMILY_LINE = re.compile(
    r"\*\*(?P<name>[A-Za-z]+)\*\*:\s*\$\\mathbb\{WP\}\((?P<weights>[\d,\s]+)\)\$"
)
VALUE_ITEM = re.compile(r"n_(\d+)\s*=\s*(\d+)")


def parse_task_gv_table(text: str) -> list[dict[str, Any]]:
    """Reads 'Pinned One-Parameter Families' rows: name, weights, published n_k values."""
    rows = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = FAMILY_LINE.search(line)
        if not match:
            continue
        weights_ = [int(w) for w in match.group("weights").replace(" ", "").split(",") if w]
        values: dict[str, str] = {}
        for follow in lines[index + 1 : index + 3]:
            for k, v in VALUE_ITEM.findall(follow):
                values[k] = v
        rows.append(
            {
                "family": match.group("name"),
                "weights": weights_,
                "published": values,
                "line": index + 1,
            }
        )
    return rows


def compare_gv_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        published = row["published"]
        if not published:
            continue
        top = max(int(k) for k in published)
        computed = gv_invariants(row["weights"], top)["n"]
        entries = []
        for k in sorted(published, key=int):
            entries.append(
                {
                    "k": k,
                    "published": published[k],
                    "recomputed": computed[k],
                    "agrees": published[k] == computed[k],
                }
            )
        out.append(
            {
                "family": row["family"],
                "weights": row["weights"],
                "line": row["line"],
                "values": entries,
            }
        )
    return out
