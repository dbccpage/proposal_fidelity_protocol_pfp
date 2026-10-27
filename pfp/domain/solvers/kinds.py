"""Typed requirement kinds over derivable instances.

Seven base kinds, plus sovereign mathematical obligations:
* HomologyBoundaryClosed: simplicial boundary closure ∂₁ ∘ ∂₂ = 0 routed to core_homology.
* HolonomyLoopClosed: path-ordered loop closure U(γ) = I routed to core_holonomy.

Governing Invariant: Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
Sovereign Rust Math Delegation Rule: Zero Python Math Re-invention.
AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from typing import Any, Protocol, Union

from ..exact.errors import ExactRefusal
from ..exact.q import Q
from ..ports.exact_ports import (
    ExactFunctionalPort,
    ExactHolonomyPort,
    ExactHomologyPort,
    RetractionEnginePort,
    get_retraction_port,
    set_retraction_port,
)
from .regime import Inst, Regime, derivable, separable

Term = Union[int, str]
Atom = tuple[int, tuple[Term, ...]]
Assign = dict[str, int]


def _vars(atoms: Iterable[Atom]) -> set[str]:
    return {t for _, args in atoms for t in args if isinstance(t, str)}


def _ground(a: Atom) -> bool:
    return not any(isinstance(t, str) for t in a[1])


# ---------------------------------------------------------------------------
# Sovereign Domain Ports Registration
# ---------------------------------------------------------------------------


class PortUnboundError(ExactRefusal):
    """A sovereign domain port was used before any adapter was bound to it.

    The unbound default used to answer ``boundary_law_verified: True`` without
    reading its input, so a missing native adapter looked like a verified
    boundary law. Now every call refuses with the typed code ``PORT_UNBOUND``.
    """

    def __init__(self, port: str, operation: str) -> None:
        super().__init__(
            "PORT_UNBOUND",
            f"{port}.{operation} was called with no adapter bound; "
            f"bind one with set_{port}_port",
        )
        self.port = port
        self.operation = operation


class _UnboundHomologyPort(ExactHomologyPort):
    """The default homology port: it decides nothing and refuses every call."""

    def compute_betti_numbers(self, complex_descriptor: object) -> list[int]:
        raise PortUnboundError("homology", "compute_betti_numbers")

    def verify_boundary_law(self, complex_descriptor: object) -> bool:
        raise PortUnboundError("homology", "verify_boundary_law")

    def verify_boundary_closed(self, faces: Sequence[Sequence[tuple[int, int, int]]]) -> bool:
        raise PortUnboundError("homology", "verify_boundary_closed")

    def verify_simplicial_boundary_law(
        self, simplices: Sequence[Sequence[int]]
    ) -> Mapping[str, Any]:
        raise PortUnboundError("homology", "verify_simplicial_boundary_law")


class _UnboundHolonomyPort(ExactHolonomyPort):
    """The default holonomy port: it decides nothing and refuses every call."""

    def path_holonomy(self, connection: object, path: Sequence[str]) -> object:
        raise PortUnboundError("holonomy", "path_holonomy")

    def loop_curvature(self, connection: object, loop: Sequence[str]) -> object:
        raise PortUnboundError("holonomy", "loop_curvature")

    def ordered_loop_product(
        self,
        tables: Sequence[Sequence[Sequence[Q]]],
        word: Sequence[tuple[int, bool]],
    ) -> Sequence[Sequence[Q]]:
        raise PortUnboundError("holonomy", "ordered_loop_product")

    def is_ordered_closure(
        self,
        tables: Sequence[Sequence[Sequence[Q]]],
        word: Sequence[tuple[int, bool]],
    ) -> bool:
        raise PortUnboundError("holonomy", "is_ordered_closure")


_GLOBAL_HOMOLOGY_PORT: ExactHomologyPort = _UnboundHomologyPort()
_GLOBAL_HOLONOMY_PORT: ExactHolonomyPort = _UnboundHolonomyPort()


def set_homology_port(port: ExactHomologyPort) -> None:
    global _GLOBAL_HOMOLOGY_PORT
    _GLOBAL_HOMOLOGY_PORT = port


def get_homology_port() -> ExactHomologyPort:
    return _GLOBAL_HOMOLOGY_PORT


def set_holonomy_port(port: ExactHolonomyPort) -> None:
    global _GLOBAL_HOLONOMY_PORT
    _GLOBAL_HOLONOMY_PORT = port


def get_holonomy_port() -> ExactHolonomyPort:
    return _GLOBAL_HOLONOMY_PORT


_GLOBAL_FUNCTIONAL_PORT: ExactFunctionalPort | None = None


def set_functional_port(port: ExactFunctionalPort) -> None:
    global _GLOBAL_FUNCTIONAL_PORT
    _GLOBAL_FUNCTIONAL_PORT = port


def get_functional_port() -> ExactFunctionalPort | None:
    return _GLOBAL_FUNCTIONAL_PORT


# ---------------------------------------------------------------------------
# Requirement Kinds
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Separate:
    rid: str
    i: int
    j: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.rid == other.rid and self.i == other.i and self.j == other.j


@dataclass(frozen=True)
class Holds:
    rid: str
    atom: Atom

    def __post_init__(self) -> None:
        if not _ground(self.atom):
            raise ValueError("Holds takes a ground atom")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.rid == other.rid and self.atom == other.atom


@dataclass(frozen=True)
class Denied:
    rid: str
    atom: Atom

    def __post_init__(self) -> None:
        if not _ground(self.atom):
            raise ValueError("Denied takes a ground atom")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.rid == other.rid and self.atom == other.atom


@dataclass(frozen=True)
class Closure:
    rid: str
    body: tuple[Atom, ...]
    head: tuple[Atom, ...]

    def __post_init__(self) -> None:
        if not _vars(self.head) <= _vars(self.body):
            raise ValueError("a closure head may use only body variables; use Total")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.rid == other.rid and self.body == other.body and self.head == other.head


@dataclass(frozen=True)
class Forbid:
    rid: str
    body: tuple[Atom, ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.rid == other.rid and self.body == other.body


@dataclass(frozen=True)
class Functional:
    rid: str
    form: int
    key_len: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.rid == other.rid and self.form == other.form and self.key_len == other.key_len


@dataclass(frozen=True)
class Total:
    rid: str
    body: tuple[Atom, ...]
    head: tuple[Atom, ...]

    def __post_init__(self) -> None:
        if not (_vars(self.head) - _vars(self.body)):
            raise ValueError("a total head must introduce a variable; use Closure")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.rid == other.rid and self.body == other.body and self.head == other.head


@dataclass(frozen=True)
class HomologyBoundaryClosed:
    """Simplicial homology boundary law verification d o d = 0 via core_homology."""

    rid: str
    faces: tuple[tuple[tuple[int, int, int], ...], ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.rid == other.rid and self.faces == other.faces


@dataclass(frozen=True)
class HolonomyLoopClosed:
    """Discrete path-ordered loop closure U(gamma) = I via core_holonomy."""

    rid: str
    tables: tuple[tuple[tuple[Q, ...], ...], ...]
    word: tuple[tuple[int, bool], ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.rid == other.rid and self.tables == other.tables and self.word == other.word


@dataclass(frozen=True)
class SimplicialBoundaryLawSatisfied:
    """Higher-dimensional simplicial homology boundary matrix verification d_{k-1} o d_k = 0 via core_homology."""

    rid: str
    simplices: tuple[tuple[int, ...], ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.rid == other.rid and self.simplices == other.simplices


Req = Union[
    Separate,
    Holds,
    Denied,
    Closure,
    Forbid,
    Functional,
    Total,
    HomologyBoundaryClosed,
    HolonomyLoopClosed,
    SimplicialBoundaryLawSatisfied,
]

KINDS = (
    "separate",
    "holds",
    "denied",
    "closure",
    "forbid",
    "functional",
    "total",
    "homology_boundary_closed",
    "holonomy_loop_closed",
    "simplicial_boundary_law_satisfied",
)


def kind_of(q: Req) -> str:
    if isinstance(q, HomologyBoundaryClosed):
        return "homology_boundary_closed"
    if isinstance(q, HolonomyLoopClosed):
        return "holonomy_loop_closed"
    if isinstance(q, SimplicialBoundaryLawSatisfied):
        return "simplicial_boundary_law_satisfied"
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
    """Real derivability over an admitted Regime."""

    regime: Regime

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.regime == other.regime

    def derivable(self, inst: Inst) -> bool:
        return bool(derivable(self.regime, inst))

    def instances(self, form: int) -> Iterable[tuple[int, ...]]:
        if form in self.regime.rules:
            return product(range(self.regime.n_data()), repeat=self.regime.forms[form])
        return sorted(a for f, a in self.regime.insts if f == form)


@dataclass(frozen=True)
class ConstOracle:
    """Derivability stubbed to a constant (the native-contribution probe)."""

    regime: Regime
    value: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.regime == other.regime and self.value == other.value

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
    """Every assignment extending env under which all atoms derive."""
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


def refutation(o: Oracle, q: Req) -> tuple[object, ...]:
    """Every violation, canonical and sorted; empty exactly when satisfied."""
    if isinstance(o, ConstOracle):
        return () if _const_verdict(o, q) else ("stubbed",)
    out: list[object] = []
    if isinstance(q, Separate):
        if not separable(o.regime, q.i, q.j):
            out.append((q.i, q.j))
    elif isinstance(q, Holds):
        if not o.derivable(_subst(q.atom, {})):
            out.append(_subst(q.atom, {}))
    elif isinstance(q, Denied):
        if o.derivable(_subst(q.atom, {})):
            out.append(_subst(q.atom, {}))
    elif isinstance(q, Closure):
        for env in matches(o, q.body):
            missing = tuple(_subst(h, env) for h in q.head if not o.derivable(_subst(h, env)))
            if missing:
                out.append((tuple(sorted(env.items())), missing))
    elif isinstance(q, Forbid):
        for env in matches(o, q.body):
            out.append(tuple(sorted(env.items())))
    elif isinstance(q, Total):
        for env in matches(o, q.body):
            if next(matches(o, q.head, env), None) is None:
                out.append(tuple(sorted(env.items())))
    elif isinstance(q, Functional):
        groups: dict[tuple[int, ...], list[tuple[int, ...]]] = {}
        if q.form < len(o.regime.forms):
            for args in o.instances(q.form):
                groups.setdefault(tuple(args[: q.key_len]), []).append(tuple(args))
        for key, rows in sorted(groups.items()):
            if len(rows) > 1:
                out.append((key, tuple(sorted(rows))))
    elif isinstance(q, HomologyBoundaryClosed):
        # Sovereign delegation to core_homology
        if not get_homology_port().verify_boundary_closed(q.faces):
            out.append("boundary_law_violation")
    elif isinstance(q, SimplicialBoundaryLawSatisfied):
        # Sovereign delegation to core_homology
        report = get_homology_port().verify_simplicial_boundary_law(q.simplices)
        if not report.get("boundary_law_verified", False):
            out.append("simplicial_boundary_law_violation")
    elif isinstance(q, HolonomyLoopClosed):
        # Sovereign delegation to core_holonomy
        if not get_holonomy_port().is_ordered_closure(q.tables, q.word):
            out.append("loop_closure_violation")
    return tuple(sorted(set(out), key=repr))


def satisfies(o: Oracle, q: Req) -> bool:
    if isinstance(o, ConstOracle):
        return _const_verdict(o, q)
    return not refutation(o, q)


def _const_verdict(o: ConstOracle, q: Req) -> bool:
    """Closed-form verdicts with derivability constant."""
    n = o.regime.n_data()
    t = o.value
    if isinstance(q, Separate):
        return False
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
    if isinstance(q, Functional):
        arity = o.regime.forms[q.form] if q.form < len(o.regime.forms) else 0
        return not (t and n >= 2 and arity > q.key_len)
    if isinstance(q, HomologyBoundaryClosed):
        return get_homology_port().verify_boundary_closed(q.faces)
    if isinstance(q, SimplicialBoundaryLawSatisfied):
        report = get_homology_port().verify_simplicial_boundary_law(q.simplices)
        return bool(report.get("boundary_law_verified", False))
    if isinstance(q, HolonomyLoopClosed):
        return get_holonomy_port().is_ordered_closure(q.tables, q.word)
    return False


def forms_of(q: Req) -> frozenset[int] | None:
    if isinstance(q, (Separate, HomologyBoundaryClosed, HolonomyLoopClosed, SimplicialBoundaryLawSatisfied)):
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
    elif isinstance(q, Functional):
        base["form"] = q.form
        base["key_len"] = q.key_len
    elif isinstance(q, HomologyBoundaryClosed):
        base["faces"] = [[[t, h, s] for t, h, s in f] for f in q.faces]
    elif isinstance(q, SimplicialBoundaryLawSatisfied):
        base["simplices"] = [list(s) for s in q.simplices]
    elif isinstance(q, HolonomyLoopClosed):
        base["word"] = [[g, back] for g, back in q.word]
    return base


def rename_req(q: Req, pi: tuple[int, ...], phi: tuple[int, ...]) -> Req:
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
        return Closure(
            q.rid,
            tuple(sorted((a(x) for x in q.body), key=repr)),
            tuple(sorted((a(x) for x in q.head), key=repr)),
        )
    if isinstance(q, Forbid):
        return Forbid(q.rid, tuple(sorted((a(x) for x in q.body), key=repr)))
    if isinstance(q, Total):
        return Total(
            q.rid,
            tuple(sorted((a(x) for x in q.body), key=repr)),
            tuple(sorted((a(x) for x in q.head), key=repr)),
        )
    if isinstance(q, Functional):
        return Functional(q.rid, phi[q.form], q.key_len)
    if isinstance(q, SimplicialBoundaryLawSatisfied):
        return SimplicialBoundaryLawSatisfied(
            q.rid,
            tuple(sorted(tuple(sorted(pi[v] if isinstance(v, int) and v < len(pi) else v for v in s)) for s in q.simplices)),
        )
    return q


__all__ = [
    "Assign",
    "Atom",
    "Closure",
    "ConstOracle",
    "Denied",
    "Forbid",
    "Functional",
    "Holds",
    "HolonomyLoopClosed",
    "HomologyBoundaryClosed",
    "SimplicialBoundaryLawSatisfied",
    "Inst",
    "KINDS",
    "Oracle",
    "PortUnboundError",
    "RegimeOracle",
    "Req",
    "RetractionEnginePort",
    "Separate",
    "Term",
    "Total",
    "forms_of",
    "get_functional_port",
    "get_holonomy_port",
    "get_homology_port",
    "get_retraction_port",
    "kind_of",
    "matches",
    "refutation",
    "rename_req",
    "req_json",
    "satisfies",
    "set_functional_port",
    "set_holonomy_port",
    "set_homology_port",
    "set_retraction_port",
]
