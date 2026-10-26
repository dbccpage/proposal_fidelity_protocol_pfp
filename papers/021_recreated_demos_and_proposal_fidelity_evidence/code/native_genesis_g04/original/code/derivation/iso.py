"""Implemented isomorphism relation and canonical forms.

Classification: metatheory apparatus (the declared branch-quotient relation).

An isomorphism between regimes is a pair of bijections -- one on datum
indices, one on form indices -- that preserves form arities, maps the
admitted instance set onto the admitted instance set, the rule set onto the
rule set, and the requirement set (as unordered pairs) onto the requirement
set.  Presentation tokens are deliberately forgotten: they are visible only
to the metatheory, so internal structure cannot depend on them.

``canonical`` computes a canonical key: the minimum, over all color-class
preserving bijection pairs, of a total serialization of the regime.  Color
classes come from an iterated, isomorphism-invariant refinement, so equal
keys hold exactly for isomorphic regimes.  Correctness is cross-checked in
the tests against a brute-force minimum over *all* bijection pairs.
"""

from __future__ import annotations

from itertools import permutations, product
from typing import Iterable, Iterator, Optional, Sequence, TypeVar

from .model import Pair, Regime

CanonKey = tuple[
    int,
    tuple[int, ...],
    tuple[tuple[int, tuple[int, ...]], ...],
    tuple[int, ...],
    tuple[Pair, ...],
]

T = TypeVar("T")


class IsoBudgetError(RuntimeError):
    """The declared permutation budget was exceeded."""


def _rank(values: Sequence[object]) -> list[int]:
    """Compress arbitrary orderable color values to dense integer ranks."""
    order = {v: k for k, v in enumerate(sorted(set(map(repr, values))))}
    return [order[repr(v)] for v in values]


def _refine(r: Regime) -> tuple[list[int], list[int]]:
    """Iterated isomorphism-invariant coloring of data and forms."""
    n, nf = r.n_data(), len(r.forms)
    dcol = [0] * n
    fcol = _rank([(r.forms[f], f in r.rules) for f in range(nf)])
    insts = sorted(r.insts)
    reqs = sorted(r.reqs)
    for _ in range(n + nf + 2):
        dsig = []
        for d in range(n):
            occ = sorted(
                (
                    fcol[f],
                    tuple(k for k, a in enumerate(args) if a == d),
                    tuple(sorted((k, dcol[a]) for k, a in enumerate(args))),
                )
                for (f, args) in insts
                if d in args
            )
            partners = sorted(
                dcol[j if i == d else i] for (i, j) in reqs if d in (i, j)
            )
            dsig.append((dcol[d], tuple(occ), tuple(partners)))
        fsig = []
        for f in range(nf):
            rows = sorted(
                tuple(dcol[a] for a in args)
                for (g, args) in insts
                if g == f
            )
            fsig.append((fcol[f], tuple(rows)))
        new_dcol, new_fcol = _rank(dsig), _rank(fsig)
        if new_dcol == dcol and new_fcol == fcol:
            break
        dcol, fcol = new_dcol, new_fcol
    return dcol, fcol


def _class_perms(colors: Sequence[int]) -> Iterator[tuple[int, ...]]:
    """All bijections sending each element to a position in the contiguous
    block its color class occupies when classes are ordered by color, as
    tuples ``pi`` with ``pi[old] = new``.

    Ordering blocks by color (an isomorphism-invariant value) makes the
    resulting serializations of isomorphic regimes range over identical
    sets, so their minima coincide."""
    classes: dict[int, list[int]] = {}
    for idx, c in enumerate(colors):
        classes.setdefault(c, []).append(idx)
    keys = sorted(classes)
    offsets: dict[int, int] = {}
    off = 0
    for c in keys:
        offsets[c] = off
        off += len(classes[c])
    for images in product(
        *(permutations(range(len(classes[c]))) for c in keys)
    ):
        pi = [0] * len(colors)
        for c, image in zip(keys, images):
            for member, slot in zip(classes[c], image):
                pi[member] = offsets[c] + slot
        yield tuple(pi)


def _perm_count(colors: Sequence[int]) -> int:
    out = 1
    counts: dict[int, int] = {}
    for c in colors:
        counts[c] = counts.get(c, 0) + 1
    for c in counts:
        for k in range(2, counts[c] + 1):
            out *= k
    return out


def serialize(r: Regime, pi: Sequence[int], phi: Sequence[int]) -> CanonKey:
    """Total serialization of the regime under the bijection pair."""
    forms = [0] * len(r.forms)
    for f, arity in enumerate(r.forms):
        forms[phi[f]] = arity
    insts = sorted(
        (phi[f], tuple(pi[a] for a in args)) for (f, args) in r.insts
    )
    rules = sorted(phi[f] for f in r.rules)
    reqs = sorted(
        (min(pi[i], pi[j]), max(pi[i], pi[j])) for (i, j) in r.reqs
    )
    return (
        r.n_data(),
        tuple(forms),
        tuple(insts),
        tuple(rules),
        tuple(reqs),
    )


def canonical_witness(
    r: Regime, perm_budget: int = 100_000
) -> tuple[CanonKey, tuple[int, ...], tuple[int, ...]]:
    """Canonical key together with a bijection pair attaining it."""
    dcol, fcol = _refine(r)
    total = _perm_count(dcol) * _perm_count(fcol)
    if total > perm_budget:
        raise IsoBudgetError(
            f"{total} candidate bijections exceed the declared budget "
            f"{perm_budget}"
        )
    return min(
        (serialize(r, pi, phi), pi, phi)
        for pi in _class_perms(dcol)
        for phi in _class_perms(fcol)
    )


def canonical(r: Regime, perm_budget: int = 100_000) -> CanonKey:
    """Canonical key under the implemented isomorphism relation."""
    return canonical_witness(r, perm_budget)[0]


def _invert(perm: Sequence[int]) -> tuple[int, ...]:
    out = [0] * len(perm)
    for old, new in enumerate(perm):
        out[new] = old
    return tuple(out)


def find_iso(
    a: Regime, b: Regime, perm_budget: int = 100_000
) -> Optional[tuple[tuple[int, ...], tuple[int, ...]]]:
    """A bijection pair ``(dmap, fmap)`` with
    ``serialize(a, dmap, fmap) == serialize(b, identity)`` — i.e. an
    isomorphism carrying ``a`` exactly onto ``b``'s structure (tokens
    excluded) — or ``None`` when the regimes are not isomorphic.  The
    returned pair is re-verified before being returned."""
    key_a, pi_a, phi_a = canonical_witness(a, perm_budget)
    key_b, pi_b, phi_b = canonical_witness(b, perm_budget)
    if key_a != key_b:
        return None
    inv_pi_b, inv_phi_b = _invert(pi_b), _invert(phi_b)
    dmap = tuple(inv_pi_b[pi_a[d]] for d in range(a.n_data()))
    fmap = tuple(inv_phi_b[phi_a[f]] for f in range(len(a.forms)))
    identity_d = tuple(range(b.n_data()))
    identity_f = tuple(range(len(b.forms)))
    if serialize(a, dmap, fmap) != serialize(b, identity_d, identity_f):
        raise RuntimeError(
            "isomorphism witness failed re-verification"
        )  # pragma: no cover - canonical machinery guarantees this
    return (dmap, fmap)


def canonical_bruteforce(r: Regime) -> CanonKey:
    """Reference canonical key: minimum over *all* bijection pairs, with no
    refinement.  Test use only (factorial blowup).

    The serialization carries the arity table with the bijection, so equal
    reference keys characterize isomorphism.  Note the refined ``canonical``
    minimizes over a subset of bijections; the two keys may differ as
    values, but equality of keys agrees between the two functions (the
    refinement is isomorphism-invariant), which is what the tests check."""
    n, nf = r.n_data(), len(r.forms)
    return min(
        serialize(r, pi, phi)
        for pi in permutations(range(n))
        for phi in permutations(range(nf))
    )


def isomorphic(a: Regime, b: Regime, perm_budget: int = 100_000) -> bool:
    return canonical(a, perm_budget) == canonical(b, perm_budget)


def rename(r: Regime, pi: Sequence[int], phi: Sequence[int]) -> Regime:
    """Apply a bijection pair to produce an isomorphic regime (test helper
    and invariance witness)."""
    data = [""] * r.n_data()
    for d, tok in enumerate(r.data):
        data[pi[d]] = tok
    forms = [0] * len(r.forms)
    for f, arity in enumerate(r.forms):
        forms[phi[f]] = arity
    insts = frozenset(
        (phi[f], tuple(pi[a] for a in args)) for (f, args) in r.insts
    )
    rules = frozenset(phi[f] for f in r.rules)
    reqs = frozenset(
        (min(pi[i], pi[j]), max(pi[i], pi[j])) for (i, j) in r.reqs
    )
    return Regime(tuple(data), tuple(forms), insts, rules, reqs)


def group_by_canonical(
    regimes: Iterable[tuple[Regime, T]], perm_budget: int = 100_000
) -> dict[CanonKey, list[T]]:
    """Group payloads by the canonical key of their regime, preserving
    insertion order inside each class."""
    out: dict[CanonKey, list[T]] = {}
    for regime, payload in regimes:
        out.setdefault(canonical(regime, perm_budget), []).append(payload)
    return out


def _inplace_class_perms(colors: Sequence[int]) -> Iterator[tuple[int, ...]]:
    """All bijections mapping each color class onto itself (members permute
    among their own original positions).  Automorphisms preserve the
    isomorphism-invariant coloring, so searching these suffices."""
    classes: dict[int, list[int]] = {}
    for idx, c in enumerate(colors):
        classes.setdefault(c, []).append(idx)
    keys = sorted(classes)
    for images in product(*(permutations(classes[c]) for c in keys)):
        pi = [0] * len(colors)
        for c, image in zip(keys, images):
            for member, target in zip(classes[c], image):
                pi[member] = target
        yield tuple(pi)


def automorphisms(
    r: Regime, perm_budget: int = 100_000
) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    """All automorphisms of the regime: bijection pairs under which the
    renamed regime equals the regime itself (tokens ignored)."""
    dcol, fcol = _refine(r)
    total = _perm_count(dcol) * _perm_count(fcol)
    if total > perm_budget:
        raise IsoBudgetError(
            f"{total} candidate bijections exceed the declared budget "
            f"{perm_budget}"
        )
    identity_key = serialize(
        r, tuple(range(r.n_data())), tuple(range(len(r.forms)))
    )
    return [
        (pi, phi)
        for pi in _inplace_class_perms(dcol)
        for phi in _inplace_class_perms(fcol)
        if serialize(r, pi, phi) == identity_key
    ]


def pair_orbits(
    r: Regime, pairs: Sequence[Pair], perm_budget: int = 100_000
) -> tuple[tuple[Pair, ...], ...]:
    """Orbits of unordered data pairs under the automorphism group of the
    regime, each orbit sorted, orbits ordered by their least member.

    The orbit decomposition is isomorphism-equivariant: renaming the
    regime by any bijection maps orbits onto orbits.  Selecting one
    representative per orbit therefore yields an equivariant challenge
    policy (unlike raw least-pair selection, which depends on the
    representative labeling)."""
    autos = automorphisms(r, perm_budget)
    remaining = set(pairs)
    orbits: list[tuple[Pair, ...]] = []
    for pair in sorted(pairs):
        if pair not in remaining:
            continue
        orbit = {
            (min(pi[pair[0]], pi[pair[1]]), max(pi[pair[0]], pi[pair[1]]))
            for (pi, _) in autos
        }
        orbit &= remaining
        remaining -= orbit
        orbits.append(tuple(sorted(orbit)))
    return tuple(orbits)
