"""Finite many-sorted structures: the claim a fixture hosts.

Classification: Domain Solvers Finite Structure.
Governing Invariant: Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
Sovereign Rust Math Delegation: ExactHomologyPort and ExactHolonomyPort routing.
AuthorityEffect: None.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from ..exact.errors import ExactError
from ..exact.q import ONE, ZERO, Q, fmt_q, parse_q
from ..ports.exact_ports import ExactHolonomyPort, ExactHomologyPort
from .errors import IntakeRefusal
from .kinds import get_holonomy_port, get_homology_port

MAX_CARRIER = 18
MAX_TUPLES = 4096
NAME = re.compile(r"^[a-z][a-z0-9_]*$")
DIGEST_TEXT = re.compile(r"sha256:[0-9a-f]{64}")
DIGEST_BYTES = 32
VERDICT_FIELD = re.compile(
    r"^(is_.*|has_.*|.*_verified|.*_residual|.*_anticommute|verified|passes|passed|valid|ok|"
    r"accepted|verdict|outcome|grade|status|differential_squared|certified|proved)$",
    re.IGNORECASE,
)


def _leaves(value: object) -> list[object]:
    if isinstance(value, dict):
        return [x for item in value.values() for x in _leaves(item)]
    if isinstance(value, list):
        return [x for item in value for x in _leaves(item)]
    return [value]


def _keys(value: object) -> list[str]:
    if isinstance(value, dict):
        return [str(k) for k in value] + [k for item in value.values() for k in _keys(item)]
    if isinstance(value, list):
        return [k for item in value for k in _keys(item)]
    return []


def refuse_hollow(obj: object, where: str = "payload") -> None:
    data = [x for x in _leaves(obj) if x is not None and x != ""]
    if not data:
        raise IntakeRefusal("EMPTY_FIXTURE", f"{where} carries no datum")
    if any(VERDICT_FIELD.match(k) for k in _keys(obj)) or all(isinstance(x, bool) for x in data):
        raise IntakeRefusal("FLAG_ONLY_FIXTURE", f"{where} carries a verdict-bearing field")


@dataclass(frozen=True)
class RelSym:
    name: str
    sorts: tuple[str, ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.name == other.name and self.sorts == other.sorts


@dataclass(frozen=True)
class FiniteStructure:
    sorts: tuple[tuple[str, int], ...]
    symbols: tuple[RelSym, ...]
    tuples: tuple[tuple[str, tuple[int, ...]], ...]
    values: tuple[tuple[int, Q], ...] = field(default=())
    digests: tuple[tuple[int, bytes], ...] = field(default=())

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.sorts == other.sorts
            and self.symbols == other.symbols
            and self.tuples == other.tuples
            and self.values == other.values
            and self.digests == other.digests
        )

    def n(self) -> int:
        return sum(c for _, c in self.sorts)

    def offset(self, sort: str) -> int:
        off = 0
        for s, c in self.sorts:
            if s == sort:
                return off
            off += c
        raise KeyError(sort)

    def elements(self, sort: str) -> tuple[int, ...]:
        off = self.offset(sort)
        count = dict(self.sorts)[sort]
        return tuple(range(off, off + count))

    def sort_of(self, e: int) -> tuple[str, int]:
        off = 0
        for s, c in self.sorts:
            if off <= e < off + c:
                return (s, e - off)
            off += c
        raise IndexError(e)

    def value(self, e: int) -> Q | None:
        for k, v in self.values:
            if k == e:
                return v
        return None

    def digest(self, e: int) -> bytes | None:
        for k, v in self.digests:
            if k == e:
                return v
        return None

    def with_tuples(self, tuples: tuple[tuple[str, tuple[int, ...]], ...]) -> FiniteStructure:
        return FiniteStructure(
            self.sorts,
            self.symbols,
            tuple(sorted(set(tuples))),
            self.values,
            self.digests,
        )

    # -- Simplicial Homology Routing (core_homology) ------------------------
    def faces_as_signed_cells(self) -> list[list[tuple[int, int, int]]]:
        """Extracts cell faces as signed boundary terms (tail, head, sign)."""
        edge_rows = [args for name, args in self.tuples if name == "edge"]
        ends = {e: (t, h) for e, t, h in edge_rows}
        plus_rows = [args for name, args in self.tuples if name == "plus"]
        minus_rows = [args for name, args in self.tuples if name == "minus"]
        face_rows = [args for name, args in self.tuples if name == "face"]

        out = []
        for row in face_rows:
            f = row[0]
            terms = [
                (ends[e][0], ends[e][1], 1)
                for ff, e in plus_rows
                if ff == f and e in ends
            ]
            terms += [
                (ends[e][0], ends[e][1], -1)
                for ff, e in minus_rows
                if ff == f and e in ends
            ]
            out.append(sorted(terms))
        return out

    def verify_boundary_closed(self, port: ExactHomologyPort | None = None) -> bool:
        """Verifies boundary law d o d = 0 via sovereign core_homology port."""
        hom_port = port or get_homology_port()
        return hom_port.verify_boundary_closed(self.faces_as_signed_cells())

    # -- Discrete Holonomy Routing (core_holonomy) --------------------------
    def turn_tables(
        self, axes_sort: str = "axis", turn_sort: str = "turn"
    ) -> dict[int, tuple[tuple[Q, ...], ...]]:
        """Constructs 4x4 rotation tables from turn/image/flips relations."""
        sort_names = {s for s, _ in self.sorts}
        if axes_sort not in sort_names or turn_sort not in sort_names:
            return {}
        axes = self.elements(axes_sort)
        turns = self.elements(turn_sort)
        flip_rows = [args for name, args in self.tuples if name == "flips"]
        image_rows = [args for name, args in self.tuples if name == "image"]

        tables = {}
        for g in turns:
            flips = {a for gg, a in flip_rows if gg == g}
            m = [[ZERO] * 4 for _ in range(4)]
            for gg, a, b in image_rows:
                if gg == g and a in axes and b in axes:
                    m[axes.index(b)][axes.index(a)] = -ONE if a in flips else ONE
            m[3][3] = ONE
            tables[g] = tuple(tuple(r) for r in m)
        return tables

    def ordered_loop_product(
        self,
        word: Sequence[tuple[int, bool]],
        port: ExactHolonomyPort | None = None,
    ) -> Sequence[Sequence[Q]]:
        """Evaluates path-ordered loop product via sovereign core_holonomy port."""
        hol_port = port or get_holonomy_port()
        sort_names = {s for s, _ in self.sorts}
        if "turn" not in sort_names:
            return ()
        turns = self.elements("turn")
        tables_map = self.turn_tables()
        tables_list = [tables_map[g] for g in turns if g in tables_map]
        return hol_port.ordered_loop_product(tables_list, word)

    def is_loop_closed(
        self,
        word: Sequence[tuple[int, bool]],
        port: ExactHolonomyPort | None = None,
    ) -> bool:
        """Verifies whether loop product is identity via sovereign core_holonomy port."""
        hol_port = port or get_holonomy_port()
        sort_names = {s for s, _ in self.sorts}
        if "turn" not in sort_names:
            return False
        turns = self.elements("turn")
        tables_map = self.turn_tables()
        tables_list = [tables_map[g] for g in turns if g in tables_map]
        return hol_port.is_ordered_closure(tables_list, word)


def _int(x: object, where: str) -> int:
    if isinstance(x, float):
        raise ExactError("RR-FLOAT", f"float at {where}")
    if isinstance(x, bool) or not isinstance(x, int):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"integer expected at {where}")
    return x


def parse_digest(x: object, where: str) -> bytes:
    if isinstance(x, float):
        raise ExactError("RR-FLOAT", f"float at {where}")
    if not isinstance(x, str) or DIGEST_TEXT.fullmatch(x) is None:
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: a digest is sha256:<64 lowercase hex>")
    return bytes.fromhex(x.split(":", 1)[1])


def fmt_digest(b: bytes) -> str:
    return "sha256:" + b.hex()


def from_json(obj: object, where: str = "structure") -> FiniteStructure:
    refuse_hollow(obj, where)
    if not isinstance(obj, dict):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where} is not an object")
    unknown = set(obj) - {"sorts", "symbols", "tuples", "values", "digests"}
    if unknown or not {"sorts", "symbols", "tuples"} <= set(obj):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where} has the wrong field set")
    sorts_raw, syms_raw, tuples_raw = obj["sorts"], obj["symbols"], obj["tuples"]
    values_raw = obj.get("values", [])
    digests_raw = obj.get("digests", [])
    if not all(isinstance(x, list) for x in (sorts_raw, syms_raw, tuples_raw, values_raw, digests_raw)):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where} fields must be lists")
    assert isinstance(sorts_raw, list) and isinstance(syms_raw, list)
    assert isinstance(tuples_raw, list) and isinstance(values_raw, list) and isinstance(digests_raw, list)
    sorts = tuple((str(s), _int(c, f"{where}.sorts")) for s, c in sorts_raw)
    symbols = tuple(
        RelSym(str(d["name"]), tuple(str(x) for x in d["sorts"])) for d in syms_raw
    )
    tuples = tuple(
        (str(s), tuple(_int(a, f"{where}.tuples") for a in args)) for s, args in tuples_raw
    )
    values = tuple((_int(e, f"{where}.values"), parse_q(v)) for e, v in values_raw)
    digests = tuple(
        (_int(e, f"{where}.digests"), parse_digest(v, f"{where}.digests"))
        for e, v in digests_raw
    )
    fs = FiniteStructure(sorts, symbols, tuples, values, digests)
    validate(fs, where)
    return fs


def to_json(fs: FiniteStructure) -> dict[str, object]:
    out: dict[str, object] = {
        "sorts": [[s, c] for s, c in fs.sorts],
        "symbols": [{"name": r.name, "sorts": list(r.sorts)} for r in fs.symbols],
        "tuples": [[s, list(a)] for s, a in fs.tuples],
        "values": [[e, fmt_q(v)] for e, v in fs.values],
    }
    if fs.digests:
        out["digests"] = [[e, fmt_digest(b)] for e, b in fs.digests]
    return out


def validate(fs: FiniteStructure, where: str = "structure") -> None:
    names = [s for s, _ in fs.sorts] + [r.name for r in fs.symbols]
    for nm in names:
        if not NAME.match(nm):
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: name {nm!r} is not a native identifier")
    if len(set(names)) != len(names):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: sort and symbol names collide")
    if any(c < 0 for _, c in fs.sorts):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: negative sort count")
    if fs.n() > MAX_CARRIER:
        raise IntakeRefusal("SIZE_CAP", f"{where}: carrier over {MAX_CARRIER}")
    if len(fs.tuples) > MAX_TUPLES:
        raise IntakeRefusal("SIZE_CAP", f"{where}: over {MAX_TUPLES} tuples")
    sym_names = {r.name for r in fs.symbols}
    sort_names = {s for s, _ in fs.sorts}
    for r in fs.symbols:
        for s in r.sorts:
            if s not in sort_names:
                raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: symbol {r.name} names unknown sort")
    for s, _ in fs.tuples:
        if s not in sym_names:
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: tuple on unknown symbol {s}")
    if len(set(fs.tuples)) != len(fs.tuples):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: duplicate tuple")
    seen: set[int] = set()
    for e, v in fs.values:
        if not isinstance(v, Q):
            raise ExactError("RR-FLOAT", f"{where}: value is not exact")
        if e in seen or not 0 <= e < fs.n():
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: bad value element {e}")
        seen.add(e)
    for e, b in fs.digests:
        if not isinstance(b, bytes) or len(b) != DIGEST_BYTES:
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: a digest is exactly {DIGEST_BYTES} bytes")
        if e in seen or not 0 <= e < fs.n():
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: bad digest element {e}")
        seen.add(e)


__all__ = [
    "DIGEST_BYTES",
    "FiniteStructure",
    "MAX_CARRIER",
    "MAX_TUPLES",
    "RelSym",
    "fmt_digest",
    "from_json",
    "parse_digest",
    "refuse_hollow",
    "to_json",
    "validate",
]
