"""Exact holonomy checks for finite-group connections on square lattices.

A finite group is given by named elements, a full multiplication table and an
inverse map; the constructor checks the group axioms on every element, pair
and triple. A connection assigns a group element to each positively oriented
edge of an L x M square lattice with open or periodic boundaries. Traversing
an edge against its orientation uses the inverse element.

The flatness check multiplies every plaquette. A plaquette whose four links
are all the identity may be skipped, because its product is the identity; the
skip saves multiplications and never changes a verdict. When every plaquette
is flat, an open lattice is gauge-trivial. On a periodic lattice the two
holonomies around the non-contractible cycles decide the verdict: both equal
to the identity gives FLAT_TRIVIAL, otherwise FLAT_NONTRIVIAL. All arithmetic
is table lookup on element names; there is no floating point.
"""

from __future__ import annotations

import itertools
from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

Vertex = tuple[int, int]
Edge = tuple[Vertex, Vertex]

FLAT_TRIVIAL = "FLAT_TRIVIAL"
FLAT_NONTRIVIAL = "FLAT_NONTRIVIAL"
NOT_FLAT = "NOT_FLAT"
VERDICTS = (FLAT_TRIVIAL, FLAT_NONTRIVIAL, NOT_FLAT)


class GroupTableError(ValueError):
    """The supplied elements, table and inverse map do not define a group."""


class LatticeError(ValueError):
    """A lattice, connection, path or gauge is malformed."""


class FiniteGroup:
    """A finite group given by a complete multiplication table."""

    def __init__(
        self,
        name: str,
        elements: Iterable[str],
        identity: str,
        table: Mapping[str, Mapping[str, str]],
        inverse: Mapping[str, str],
    ) -> None:
        if not isinstance(elements, Iterable) or isinstance(elements, (str, bytes, Mapping)):
            raise GroupTableError("elements must be a nonempty sequence of strings")
        names = tuple(elements)
        if type(name) is not str:
            raise GroupTableError("group name must be a string")
        if not names or any(type(a) is not str for a in names):
            raise GroupTableError("elements must be a nonempty sequence of strings")
        if len(set(names)) != len(names):
            raise GroupTableError("element names must be distinct")
        members = frozenset(names)
        if type(identity) is not str or identity not in members:
            raise GroupTableError("identity is not an element")
        if not isinstance(table, Mapping) or not isinstance(inverse, Mapping):
            raise GroupTableError("table and inverse map must be mappings")
        if set(table) != members or set(inverse) != members:
            raise GroupTableError("table rows and inverse map must cover exactly the elements")
        rows: dict[str, Mapping[str, str]] = {}
        for a in names:
            row = table[a]
            if not isinstance(row, Mapping) or set(row) != members:
                raise GroupTableError(f"row {a!r} is not total and closed")
            if any(type(row[b]) is not str or row[b] not in members for b in names):
                raise GroupTableError(f"row {a!r} is not total and closed")
            rows[a] = MappingProxyType({b: row[b] for b in names})
        if any(type(inverse[a]) is not str or inverse[a] not in members for a in names):
            raise GroupTableError("inverse values must be group elements")
        self._name = name
        self._elements = names
        self._identity = identity
        self._table = MappingProxyType(rows)
        self._inverse = MappingProxyType({a: inverse[a] for a in names})
        self._check_axioms()

    def _check_axioms(self) -> None:
        e = self._identity
        for a in self._elements:
            if self.mul(e, a) != a or self.mul(a, e) != a:
                raise GroupTableError(f"identity law fails at {a!r}")
            b = self._inverse[a]
            if b not in self._table or self.mul(a, b) != e or self.mul(b, a) != e:
                raise GroupTableError(f"inverse law fails at {a!r}")
        for a, b, c in itertools.product(self._elements, repeat=3):
            if self.mul(self.mul(a, b), c) != self.mul(a, self.mul(b, c)):
                raise GroupTableError(f"associativity fails at {(a, b, c)!r}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def elements(self) -> tuple[str, ...]:
        return self._elements

    @property
    def identity(self) -> str:
        return self._identity

    def mul(self, a: str, b: str) -> str:
        return self._table[a][b]

    def inv(self, a: str) -> str:
        return self._inverse[a]

    def product(self, factors: Iterable[str]) -> str:
        acc = self._identity
        for factor in factors:
            acc = self._table[acc][factor]
        return acc

    def commute(self, a: str, b: str) -> bool:
        return self.mul(a, b) == self.mul(b, a)

    def is_abelian(self) -> bool:
        return all(self.commute(a, b) for a, b in itertools.combinations(self._elements, 2))

    def order_of(self, a: str) -> int:
        acc, n = a, 1
        while acc != self._identity:
            acc, n = self.mul(acc, a), n + 1
        return n

    def as_table(self) -> dict[str, dict[str, str]]:
        return {a: dict(row) for a, row in self._table.items()}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FiniteGroup) or type(other) is not type(self):
            return NotImplemented
        return (
            self._elements == other._elements
            and self._identity == other._identity
            and self.as_table() == other.as_table()
        )

    __hash__ = None  # type: ignore[assignment]


def symmetric_group_s3() -> FiniteGroup:
    """S3 as the permutations of {0, 1, 2}; (p q)(i) = p(q(i))."""
    perms = sorted(itertools.permutations(range(3)))

    def label(p: tuple[int, ...]) -> str:
        return "".join(str(i) for i in p)

    def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(p[q[i]] for i in range(3))

    def inverse(p: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(p.index(i) for i in range(3))

    table = {label(p): {label(q): label(compose(p, q)) for q in perms} for p in perms}
    return FiniteGroup(
        "S3",
        [label(p) for p in perms],
        "012",
        table,
        {label(p): label(inverse(p)) for p in perms},
    )


_UNITS = {
    "e": (1, 0, 0, 0),
    "i": (0, 1, 0, 0),
    "j": (0, 0, 1, 0),
    "k": (0, 0, 0, 1),
}


def quaternion_group_q8() -> FiniteGroup:
    """Q8 = {+-1, +-i, +-j, +-k} under the Hamilton product of integer quaternions."""
    coords: dict[str, tuple[int, int, int, int]] = {}
    for unit, q in _UNITS.items():
        coords[unit] = q
        coords["-" + unit] = (-q[0], -q[1], -q[2], -q[3])
    names = {q: label for label, q in coords.items()}

    def hamilton(x: tuple[int, ...], y: tuple[int, ...]) -> tuple[int, int, int, int]:
        a1, b1, c1, d1 = x
        a2, b2, c2, d2 = y
        return (
            a1 * a2 - b1 * b2 - c1 * c2 - d1 * d2,
            a1 * b2 + b1 * a2 + c1 * d2 - d1 * c2,
            a1 * c2 - b1 * d2 + c1 * a2 + d1 * b2,
            a1 * d2 + b1 * c2 - c1 * b2 + d1 * a2,
        )

    order = ["e", "-e", "i", "-i", "j", "-j", "k", "-k"]
    table = {a: {b: names[hamilton(coords[a], coords[b])] for b in order} for a in order}
    conjugate = {a: names[(q[0], -q[1], -q[2], -q[3])] for a, q in coords.items()}
    return FiniteGroup("Q8", order, "e", table, conjugate)


@dataclass(frozen=True)
class Lattice:
    """An L x M square lattice of vertices (r, c); periodic means a torus."""

    rows: int
    cols: int
    periodic: bool

    def __post_init__(self) -> None:
        if type(self.rows) is not int or type(self.cols) is not int:
            raise LatticeError("rows and cols must be int")
        if type(self.periodic) is not bool:
            raise LatticeError("periodic must be bool")
        # With two rows or columns on a torus, two distinct edges would join the
        # same pair of vertices; naming edges by endpoints needs at least three.
        minimum = 3 if self.periodic else 2
        if self.rows < minimum or self.cols < minimum:
            raise LatticeError(f"need at least {minimum} rows and columns")

    def vertices(self) -> list[Vertex]:
        return [(r, c) for r in range(self.rows) for c in range(self.cols)]

    def positive_edges(self) -> list[Edge]:
        edges: list[Edge] = []
        for r, c in self.vertices():
            if c + 1 < self.cols or self.periodic:
                edges.append(((r, c), (r, (c + 1) % self.cols)))
            if r + 1 < self.rows or self.periodic:
                edges.append(((r, c), ((r + 1) % self.rows, c)))
        return edges

    def plaquette_origins(self) -> list[Vertex]:
        rows = self.rows if self.periodic else self.rows - 1
        cols = self.cols if self.periodic else self.cols - 1
        return [(r, c) for r in range(rows) for c in range(cols)]

    def plaquette(self, r: int, c: int) -> tuple[Vertex, Vertex, Vertex, Vertex]:
        """Boundary of plaquette (r, c) in the order (r,c), (r+1,c), (r+1,c+1), (r,c+1)."""
        r1, c1 = (r + 1) % self.rows, (c + 1) % self.cols
        return ((r, c), (r1, c), (r1, c1), (r, c1))

    def loop_a(self) -> list[Vertex]:
        """Row-0 cycle from (0, 0) through increasing columns; periodic lattices only."""
        if not self.periodic:
            raise LatticeError("an open lattice has no non-contractible cycle")
        return [(0, c) for c in range(self.cols)] + [(0, 0)]

    def loop_b(self) -> list[Vertex]:
        """Column-0 cycle from (0, 0) through increasing rows; periodic lattices only."""
        if not self.periodic:
            raise LatticeError("an open lattice has no non-contractible cycle")
        return [(r, 0) for r in range(self.rows)] + [(0, 0)]


class Connection:
    """A group element on every positive edge; reversed traversal uses the inverse."""

    def __init__(self, group: FiniteGroup, lattice: Lattice, links: Mapping[Edge, str]) -> None:
        expected = set(lattice.positive_edges())
        if set(links) != expected:
            raise LatticeError("links must assign exactly the positive edges of the lattice")
        members = set(group.elements)
        if any(type(value) is not str or value not in members for value in links.values()):
            raise LatticeError("every link must be a group element")
        self._group = group
        self._lattice = lattice
        self._links = MappingProxyType(dict(links))

    @property
    def group(self) -> FiniteGroup:
        return self._group

    @property
    def lattice(self) -> Lattice:
        return self._lattice

    def links(self) -> dict[Edge, str]:
        return dict(self._links)

    def link(self, u: Vertex, v: Vertex) -> str:
        if (u, v) in self._links:
            return self._links[(u, v)]
        if (v, u) in self._links:
            return self._group.inv(self._links[(v, u)])
        raise LatticeError(f"{u} -> {v} is not an edge of the lattice")

    def path_holonomy(self, path: Sequence[Vertex]) -> str:
        """Ordered product U(v0 v1) U(v1 v2) ... along a vertex path."""
        if len(path) < 2:
            raise LatticeError("a path needs at least two vertices")
        return self._group.product(self.link(u, v) for u, v in zip(path, path[1:], strict=False))

    def cycle_holonomy(self, cycle: Sequence[Vertex]) -> str:
        """Holonomy of a closed cycle listed without repeating its first vertex."""
        if len(cycle) < 2:
            raise LatticeError("a cycle needs at least two vertices")
        return self.path_holonomy([*cycle, cycle[0]])

    def plaquette_links(self, r: int, c: int) -> list[str]:
        cycle = self._lattice.plaquette(r, c)
        return [self.link(cycle[i], cycle[(i + 1) % 4]) for i in range(4)]

    def plaquette_holonomy(self, r: int, c: int) -> str:
        return self._group.product(self.plaquette_links(r, c))


def trivial_connection(group: FiniteGroup, lattice: Lattice) -> Connection:
    return Connection(group, lattice, {edge: group.identity for edge in lattice.positive_edges()})


def gauge_transform(connection: Connection, gauge: Mapping[Vertex, str]) -> Connection:
    """U'(u v) = g(u) U(u v) g(v)^-1 on every positive edge."""
    group = connection.group
    _check_gauge(connection, gauge)
    links = {
        (u, v): group.mul(group.mul(gauge[u], value), group.inv(gauge[v]))
        for (u, v), value in connection.links().items()
    }
    return Connection(group, connection.lattice, links)


def _check_gauge(connection: Connection, gauge: Mapping[Vertex, str]) -> None:
    if set(gauge) != set(connection.lattice.vertices()):
        raise LatticeError("a gauge must assign every vertex")
    if any(type(g) is not str or g not in connection.group.elements for g in gauge.values()):
        raise LatticeError("every gauge value must be a group element")


def gauge_trivializes(connection: Connection, gauge: Mapping[Vertex, str]) -> bool:
    """True when g(u) U(u v) g(v)^-1 is the identity on every edge."""
    _check_gauge(connection, gauge)
    group = connection.group
    return all(
        group.mul(group.mul(gauge[u], value), group.inv(gauge[v])) == group.identity
        for (u, v), value in connection.links().items()
    )


def spanning_tree_gauge(connection: Connection) -> dict[Vertex, str]:
    """Breadth-first tree of non-wrapping edges from (0, 0); g(v) = g(u) U(u v)."""
    group, lattice = connection.group, connection.lattice
    gauge: dict[Vertex, str] = {(0, 0): group.identity}
    queue: deque[Vertex] = deque([(0, 0)])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < lattice.rows and 0 <= nc < lattice.cols and (nr, nc) not in gauge:
                gauge[(nr, nc)] = group.mul(gauge[(r, c)], connection.link((r, c), (nr, nc)))
                queue.append((nr, nc))
    return gauge


@dataclass(frozen=True)
class FlatnessReport:
    """Outcome of the complete flatness check."""

    verdict: str
    plaquettes: int
    skipped_identity_plaquettes: int
    nonflat_plaquettes: int
    witness_plaquette: tuple[Vertex, ...] | None = None
    witness_holonomy: str | None = None
    hol_a: str | None = None
    hol_b: str | None = None
    gauge: tuple[tuple[Vertex, str], ...] | None = None


def check_flatness(connection: Connection, *, skip_identity_links: bool = True) -> FlatnessReport:
    """Multiply every plaquette, then decide FLAT_TRIVIAL, FLAT_NONTRIVIAL or NOT_FLAT."""
    group, lattice = connection.group, connection.lattice
    e = group.identity
    origins = lattice.plaquette_origins()
    skipped = 0
    nonflat: list[tuple[tuple[Vertex, ...], str]] = []
    for r, c in origins:
        factors = connection.plaquette_links(r, c)
        if skip_identity_links and all(x == e for x in factors):
            skipped += 1
            continue
        hol = group.product(factors)
        if hol != e:
            nonflat.append((lattice.plaquette(r, c), hol))
    if nonflat:
        return FlatnessReport(
            NOT_FLAT, len(origins), skipped, len(nonflat), nonflat[0][0], nonflat[0][1]
        )
    hol_a = hol_b = None
    if lattice.periodic:
        hol_a = connection.path_holonomy(lattice.loop_a())
        hol_b = connection.path_holonomy(lattice.loop_b())
        if not group.commute(hol_a, hol_b):
            raise AssertionError("a flat torus connection gave non-commuting cycle holonomies")
        if hol_a != e or hol_b != e:
            if gauge_trivializes(connection, spanning_tree_gauge(connection)):
                raise AssertionError("tree gauge trivializes a connection with nontrivial cycles")
            return FlatnessReport(
                FLAT_NONTRIVIAL, len(origins), skipped, 0, hol_a=hol_a, hol_b=hol_b
            )
    gauge = spanning_tree_gauge(connection)
    if not gauge_trivializes(connection, gauge):
        raise AssertionError("tree gauge fails on a flat connection with trivial cycles")
    return FlatnessReport(
        FLAT_TRIVIAL,
        len(origins),
        skipped,
        0,
        hol_a=hol_a,
        hol_b=hol_b,
        gauge=tuple(sorted(gauge.items())),
    )


def parse_vertex(text: str) -> Vertex:
    """Parse the 'r,c' vertex names used by the challenge files."""
    parts = text.split(",") if type(text) is str else []
    if len(parts) != 2 or not all(p.isascii() and p.isdigit() for p in parts):
        raise LatticeError(f"malformed vertex name {text!r}")
    return (int(parts[0]), int(parts[1]))


def connection_from_directed_links(
    group: FiniteGroup, lattice: Lattice, directed: Mapping[str, str]
) -> Connection:
    """Build a connection from 'r,c->r,c' keys listing both directions of every edge.

    Refuses duplicate parsed edges, unknown elements, a missing direction,
    an unknown edge, or U(v u) != U(u v)^-1.
    """
    parsed: dict[Edge, str] = {}
    for key, value in directed.items():
        ends = key.split("->") if type(key) is str else []
        if len(ends) != 2:
            raise LatticeError(f"malformed edge key {key!r}")
        edge = (parse_vertex(ends[0]), parse_vertex(ends[1]))
        if edge in parsed:
            raise LatticeError(f"duplicate parsed edge {key!r}")
        if type(value) is not str or value not in group.elements:
            raise LatticeError(f"unknown group element on edge {key!r}")
        parsed[edge] = value
    links: dict[Edge, str] = {}
    for u, v in lattice.positive_edges():
        if (u, v) not in parsed or (v, u) not in parsed:
            raise LatticeError(f"edge {u} -> {v} is not listed in both directions")
        if parsed[(v, u)] != group.inv(parsed[(u, v)]):
            raise LatticeError(f"inverse mismatch on edge {u} -> {v}")
        links[(u, v)] = parsed[(u, v)]
    if len(parsed) != 2 * len(links):
        raise LatticeError("directed links name an edge that is not in the lattice")
    return Connection(group, lattice, links)


def connection_from_case(case: Mapping[str, object]) -> Connection:
    """Read a C017 challenge case: L, M, boundary, group table and directed links."""
    spec = case.get("group")
    if not isinstance(spec, Mapping):
        raise LatticeError("case group must be a mapping")
    if any(key not in spec for key in ("name", "elements", "identity", "table", "inverses")):
        raise GroupTableError("case group is missing a required field")
    group = FiniteGroup(
        spec["name"], spec["elements"], spec["identity"], spec["table"], spec["inverses"],
    )
    boundary = case.get("boundary")
    if boundary not in ("open", "periodic"):
        raise LatticeError(f"unknown boundary {boundary!r}")
    lattice = Lattice(case.get("L"), case.get("M"), boundary == "periodic")  # type: ignore[arg-type]
    edges = case.get("edges")
    if not isinstance(edges, Mapping):
        raise LatticeError("case edges must be a mapping")
    return connection_from_directed_links(group, lattice, edges)


def _plaquette_listings(lattice: Lattice) -> set[tuple[Vertex, ...]]:
    """Every plaquette boundary in either orientation and from any starting vertex."""
    listings: set[tuple[Vertex, ...]] = set()
    for r, c in lattice.plaquette_origins():
        cycle = lattice.plaquette(r, c)
        for turned in (cycle, tuple(reversed(cycle))):
            for k in range(4):
                listings.add(turned[k:] + turned[:k])
    return listings


def verify_claim(connection: Connection, claim: object) -> tuple[bool, str]:
    """Check a proposed verdict and its certificate against the connection.

    NOT_FLAT needs a plaquette, listed in either orientation from any vertex,
    whose ordered product equals the stated holonomy and is not the identity.
    FLAT_NONTRIVIAL needs every plaquette flat and a stated closed loop whose
    product equals its stated, non-identity holonomy; in a flat connection a
    contractible loop has identity holonomy, so such a loop is non-contractible.
    FLAT_TRIVIAL (or the challenge name PURE_GAUGE) needs a gauge that makes
    every link the identity. Anything else is rejected with a reason.
    """
    if not isinstance(claim, Mapping):
        return False, "claim is not a mapping"
    verdict = claim.get("verdict")
    group, lattice = connection.group, connection.lattice
    try:
        if verdict == NOT_FLAT:
            listed = tuple(parse_vertex(v) for v in claim.get("plaquette", ()))
            if listed not in _plaquette_listings(lattice):
                return False, "listed vertices are not a plaquette boundary"
            actual = connection.cycle_holonomy(listed)
            if actual == group.identity:
                return False, "the listed plaquette is flat"
            if claim.get("holonomy") != actual:
                return False, f"stated holonomy {claim.get('holonomy')!r}, product {actual!r}"
            return True, "non-flat plaquette confirmed"
        if verdict == FLAT_NONTRIVIAL:
            if not lattice.periodic:
                return False, "an open lattice has no non-contractible cycle"
            if check_flatness(connection).verdict == NOT_FLAT:
                return False, "a plaquette is not flat"
            nontrivial = False
            for loop_key, hol_key in (("loop_a", "hol_a"), ("loop_b", "hol_b")):
                loop = [parse_vertex(v) for v in claim.get(loop_key, ())]
                if not loop:
                    continue
                if loop[0] != loop[-1]:
                    return False, f"{loop_key} is not closed"
                actual = connection.path_holonomy(loop)
                if claim.get(hol_key) != actual:
                    return False, f"stated {hol_key} {claim.get(hol_key)!r}, product {actual!r}"
                nontrivial = nontrivial or actual != group.identity
            if not nontrivial:
                return False, "no stated loop has a non-identity holonomy"
            return True, "flat with a non-identity loop holonomy"
        if verdict in (FLAT_TRIVIAL, "PURE_GAUGE"):
            raw = claim.get("gauge")
            if not isinstance(raw, Mapping):
                return False, "gauge missing"
            gauge = {}
            for key, value in raw.items():
                vertex = parse_vertex(key)
                if vertex in gauge:
                    raise LatticeError(f"duplicate parsed gauge vertex {key!r}")
                gauge[vertex] = value
            if not gauge_trivializes(connection, gauge):
                return False, "gauge does not make every link the identity"
            return True, "gauge makes every link the identity"
    except (LatticeError, TypeError) as error:
        return False, f"malformed certificate: {error}"
    return False, f"no checkable verdict (status {claim.get('status')!r})"
