# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Typed requirement kinds over derivable instances.

Seven kinds, each with a decidable ``satisfies``:

* ``Separate(i, j)``   the sealed kind: some context separates data i and j;
* ``Holds(a)``         the ground atom is derivable;
* ``Denied(a)``        the ground atom is not derivable;
* ``Closure(B -> H)``  every assignment deriving all of B derives all of H
                       (H uses only variables of B);
* ``Forbid(B)``        no assignment derives all of B;
* ``Functional(f, k)`` at most one derivable instance of f per k-prefix;
* ``Total(B -> H)``    every assignment deriving B extends, on the variables
                       only H mentions, to one deriving all of H.

A term is a datum index (``int``) or a variable (``str``).  Derivability is
read through an oracle, so the native-contribution probe can replace it by a
constant and see which clauses depend on it.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import product
from typing import Protocol, Union

from .sealed import Regime, sealed_observe

Term = Union[int, str]
Atom = tuple[int, tuple[Term, ...]]
Inst = tuple[int, tuple[int, ...]]
Assign = dict[str, int]


def _vars(atoms: Iterable[Atom]) -> set[str]:
    return {t for _, args in atoms for t in args if isinstance(t, str)}


def _ground(a: Atom) -> bool:
    return not any(isinstance(t, str) for t in a[1])


@dataclass(frozen=True)
class Separate:
    rid: str
    i: int
    j: int


@dataclass(frozen=True)
class Holds:
    rid: str
    atom: Atom

    def __post_init__(self) -> None:
        if not _ground(self.atom):
            raise ValueError("Holds takes a ground atom")


@dataclass(frozen=True)
class Denied:
    rid: str
    atom: Atom

    def __post_init__(self) -> None:
        if not _ground(self.atom):
            raise ValueError("Denied takes a ground atom")


@dataclass(frozen=True)
class Closure:
    rid: str
    body: tuple[Atom, ...]
    head: tuple[Atom, ...]

    def __post_init__(self) -> None:
        if not _vars(self.head) <= _vars(self.body):
            raise ValueError("a closure head may use only body variables; use Total")


@dataclass(frozen=True)
class Forbid:
    rid: str
    body: tuple[Atom, ...]


@dataclass(frozen=True)
class Functional:
    rid: str
    form: int
    key_len: int


@dataclass(frozen=True)
class Total:
    rid: str
    body: tuple[Atom, ...]
    head: tuple[Atom, ...]

    def __post_init__(self) -> None:
        if not (_vars(self.head) - _vars(self.body)):
            raise ValueError("a total head must introduce a variable; use Closure")


Req = Union[Separate, Holds, Denied, Closure, Forbid, Functional, Total]
KINDS = ("separate", "holds", "denied", "closure", "forbid", "functional", "total")


def kind_of(q: Req) -> str:
    return type(q).__name__.lower()


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------


class Oracle(Protocol):
    @property
    def regime(self) -> Regime: ...

    def derivable(self, inst: Inst) -> bool: ...

    def instances(self, form: int) -> Iterable[tuple[int, ...]]: ...


@dataclass(frozen=True)
class RegimeOracle:
    """Real derivability: the sealed ``observe.derivable``."""

    regime: Regime

    def derivable(self, inst: Inst) -> bool:
        return bool(sealed_observe.derivable(self.regime, inst))

    def instances(self, form: int) -> Iterable[tuple[int, ...]]:
        if form in self.regime.rules:
            return product(range(self.regime.n_data()), repeat=self.regime.forms[form])
        return sorted(a for f, a in self.regime.insts if f == form)


@dataclass(frozen=True)
class ConstOracle:
    """Derivability stubbed to a constant (the native-contribution probe)."""

    regime: Regime
    value: bool

    def derivable(self, inst: Inst) -> bool:
        return self.value

    def instances(self, form: int) -> Iterable[tuple[int, ...]]:
        if not self.value:
            return ()
        return product(range(self.regime.n_data()), repeat=self.regime.forms[form])


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _unify(args: tuple[Term, ...], inst: tuple[int, ...], env: Assign) -> Assign | None:
    if len(args) != len(inst):
        return None
    out = dict(env)
    for t, v in zip(args, inst):
        if isinstance(t, int):
            if t != v:
                return None
        elif t in out:
            if out[t] != v:
                return None
        else:
            out[t] = v
    return out


def _subst(a: Atom, env: Assign) -> Inst:
    f, args = a
    return (f, tuple(t if isinstance(t, int) else env[t] for t in args))


def matches(o: Oracle, atoms: tuple[Atom, ...], env: Assign | None = None) -> Iterator[Assign]:
    """Every assignment extending ``env`` under which all atoms derive."""
    env = {} if env is None else env
    if not atoms:
        yield env
        return
    first, rest = atoms[0], atoms[1:]
    f, args = first
    if all(isinstance(t, int) or t in env for t in args):
        if o.derivable(_subst(first, env)):
            yield from matches(o, rest, env)
        return
    if f >= len(o.regime.forms):
        return
    for inst in o.instances(f):
        e2 = _unify(args, inst, env)
        if e2 is not None:
            yield from matches(o, rest, e2)


def _refute_separate(o: Oracle, q: Separate) -> list[object]:
    if not sealed_observe.separable(o.regime, q.i, q.j):
        return [(q.i, q.j)]
    return []


def _refute_holds(o: Oracle, q: Holds) -> list[object]:
    if not o.derivable(_subst(q.atom, {})):
        return [_subst(q.atom, {})]
    return []


def _refute_denied(o: Oracle, q: Denied) -> list[object]:
    if o.derivable(_subst(q.atom, {})):
        return [_subst(q.atom, {})]
    return []


def _refute_closure(o: Oracle, q: Closure) -> list[object]:
    out: list[object] = []
    for env in matches(o, q.body):
        missing = tuple(_subst(h, env) for h in q.head if not o.derivable(_subst(h, env)))
        if missing:
            out.append((tuple(sorted(env.items())), missing))
    return out


def _refute_forbid(o: Oracle, q: Forbid) -> list[object]:
    return [tuple(sorted(env.items())) for env in matches(o, q.body)]


def _refute_total(o: Oracle, q: Total) -> list[object]:
    out: list[object] = []
    for env in matches(o, q.body):
        if next(matches(o, q.head, env), None) is None:
            out.append(tuple(sorted(env.items())))
    return out


def _refute_functional(o: Oracle, q: Req) -> list[object]:
    groups: dict[tuple[int, ...], list[tuple[int, ...]]] = {}
    if q.form < len(o.regime.forms):
        for args in o.instances(q.form):
            groups.setdefault(tuple(args[: q.key_len]), []).append(tuple(args))
    out: list[object] = []
    for key, rows in sorted(groups.items()):
        if len(rows) > 1:
            out.append((key, tuple(sorted(rows))))
    return out


_REFUTERS = (
    (Separate, _refute_separate),
    (Holds, _refute_holds),
    (Denied, _refute_denied),
    (Closure, _refute_closure),
    (Forbid, _refute_forbid),
    (Total, _refute_total),
)


def _refute_rows(o: Oracle, q: Req) -> list[object]:
    for kind, refute in _REFUTERS:
        if isinstance(q, kind):
            return refute(o, q)
    return _refute_functional(o, q)


def refutation(o: Oracle, q: Req) -> tuple[object, ...]:
    """Every violation, canonical and sorted; empty exactly when satisfied."""
    if isinstance(o, ConstOracle):
        return () if _const_verdict(o, q) else ("stubbed",)
    return tuple(sorted(set(_refute_rows(o, q)), key=repr))


def satisfies(o: Oracle, q: Req) -> bool:
    if isinstance(o, ConstOracle):
        return _const_verdict(o, q)
    return not refutation(o, q)


def _const_verdict(o: ConstOracle, q: Req) -> bool:
    """Closed-form verdicts with derivability constant (no enumeration)."""
    n = o.regime.n_data()
    t = o.value
    if isinstance(q, Separate):
        return False  # every datum then has the same profile
    if isinstance(q, Holds):
        return t
    if isinstance(q, Denied):
        return not t
    if isinstance(q, Closure):
        return t or bool(q.body)
    if isinstance(q, Forbid):
        return not (t and (n > 0 or not _vars(q.body))) if q.body else False
    if isinstance(q, Total):
        return (t and n > 0) or (not t and bool(q.body))
    arity = o.regime.forms[q.form] if q.form < len(o.regime.forms) else 0
    return not (t and n >= 2 and arity > q.key_len)


def forms_of(q: Req) -> frozenset[int] | None:
    """Forms a requirement reads; ``None`` for ``Separate``, which reads
    every context and so can be met by new witness structure."""
    if isinstance(q, Separate):
        return None
    if isinstance(q, (Holds, Denied)):
        return frozenset({q.atom[0]})
    if isinstance(q, (Closure, Total)):
        return frozenset(f for f, _ in q.body + q.head)
    if isinstance(q, Forbid):
        return frozenset(f for f, _ in q.body)
    return frozenset({q.form})


def req_json(q: Req) -> dict[str, object]:
    def atom(a: Atom) -> list[object]:
        return [a[0], [t if isinstance(t, int) else "?" + t for t in a[1]]]

    base: dict[str, object] = {"id": q.rid, "kind": kind_of(q)}
    if isinstance(q, Separate):
        base["pair"] = [q.i, q.j]
    elif isinstance(q, (Holds, Denied)):
        base["atom"] = atom(q.atom)
    elif isinstance(q, (Closure, Total)):
        base["body"] = [atom(a) for a in q.body]
        base["head"] = [atom(a) for a in q.head]
    elif isinstance(q, Forbid):
        base["body"] = [atom(a) for a in q.body]
    else:
        base["form"] = q.form
        base["key_len"] = q.key_len
    return base


def rename_req(q: Req, pi: tuple[int, ...], phi: tuple[int, ...]) -> Req:
    """Apply a data bijection ``pi`` and a form bijection ``phi``."""

    def a(x: Atom) -> Atom:
        return (phi[x[0]], tuple(pi[t] if isinstance(t, int) else t for t in x[1]))

    if isinstance(q, Separate):
        i, j = pi[q.i], pi[q.j]
        return Separate(q.rid, min(i, j), max(i, j))
    if isinstance(q, Holds):
        return Holds(q.rid, a(q.atom))
    if isinstance(q, Denied):
        return Denied(q.rid, a(q.atom))
    if isinstance(q, Closure):
        return Closure(q.rid, tuple(sorted((a(x) for x in q.body), key=repr)), tuple(sorted((a(x) for x in q.head), key=repr)))
    if isinstance(q, Forbid):
        return Forbid(q.rid, tuple(sorted((a(x) for x in q.body), key=repr)))
    if isinstance(q, Total):
        return Total(q.rid, tuple(sorted((a(x) for x in q.body), key=repr)), tuple(sorted((a(x) for x in q.head), key=repr)))
    return Functional(q.rid, phi[q.form], q.key_len)
