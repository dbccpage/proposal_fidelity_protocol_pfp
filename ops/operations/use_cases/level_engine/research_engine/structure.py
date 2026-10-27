# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Finite many-sorted structures: the claim a fixture hosts.

A structure lists sorts with element counts, relation symbols with their
argument sorts, tuples, and exact value data for some elements: an exact
rational, or (since round P6) a digest, exactly 32 bytes, written
``sha256:<64 lowercase hex>``, or (since round P7B) a text, a string of
printable ASCII of at most ``MAX_TEXT`` characters.  A digest is a byte
string, never a number; it is compared byte for byte and never rounded, and
nothing in the grammar reads it.  A text is the same: compared byte for
byte, read only by decoded clauses, never by the grammar.  An element
carries at most one of the three.  Element indices are global, in declared
sort order.

``validate`` checks names, sizes, integer types and exact values.  It does
**not** check tuple arity or index range: those belong to sealed admission,
which refuses them when the fixture is hosted (so a malformed claim is
refused by the sealed rule itself, not by harness prose).

AuthorityEffect: None
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .errors import ExactError, IntakeRefusal
from .exact.q import Q, fmt_q, parse_q

# The carrier cap.  Round P6 lifted it from 12 to 18, the smallest cap that
# hosts the instances three levels need: a six-vertex closed surface with its
# ten triangles, one test cochain and one self-map (18 elements); a solid
# cell with four vertices, three labels, four faces and four walk positions
# (15); a filtered triangle with its pages (10).  Hosting is not search: the
# witness search stays bounded by ``search.EVAL_BUDGET`` over its declared
# class, which is counted before it is enumerated.
MAX_CARRIER = 18
MAX_TUPLES = 4096
NAME = re.compile(r"^[a-z][a-z0-9_]*$")
DIGEST_TEXT = re.compile(r"sha256:[0-9a-f]{64}")
DIGEST_BYTES = 32
# A hosted text: printable ASCII (space to tilde), no control character, at
# most this many characters.  Enough for the contents, names and sources the
# apparatus levels host; a text is data, never a place to hide a claim.
MAX_TEXT = 512
TEXT_CHARS = re.compile(r"[ -~]*")
# Verdict-bearing key names; a payload carrying one anywhere is flag-only.
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
    """Refuse a payload with no datum (``EMPTY_FIXTURE``: only empty
    containers, nulls and empty strings), and a payload that carries a
    verdict-named key anywhere or whose every datum is a boolean
    (``FLAG_ONLY_FIXTURE``)."""
    data = [x for x in _leaves(obj) if x is not None and x != ""]
    if not data:
        raise IntakeRefusal("EMPTY_FIXTURE", f"{where} carries no datum")
    if any(VERDICT_FIELD.match(k) for k in _keys(obj)) or all(isinstance(x, bool) for x in data):
        raise IntakeRefusal("FLAG_ONLY_FIXTURE", f"{where} carries a verdict-bearing field")


@dataclass(frozen=True)
class RelSym:
    name: str
    sorts: tuple[str, ...]


@dataclass(frozen=True)
class FiniteStructure:
    sorts: tuple[tuple[str, int], ...]
    symbols: tuple[RelSym, ...]
    tuples: tuple[tuple[str, tuple[int, ...]], ...]
    values: tuple[tuple[int, Q], ...] = field(default=())
    digests: tuple[tuple[int, bytes], ...] = field(default=())
    texts: tuple[tuple[int, str], ...] = field(default=())

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

    def text(self, e: int) -> str | None:
        for k, v in self.texts:
            if k == e:
                return v
        return None

    def with_tuples(self, tuples: tuple[tuple[str, tuple[int, ...]], ...]) -> "FiniteStructure":
        return FiniteStructure(self.sorts, self.symbols, tuple(sorted(set(tuples))), self.values, self.digests,
                               self.texts)


def _int(x: object, where: str) -> int:
    if isinstance(x, float):
        raise ExactError("RR-FLOAT", f"float at {where}")
    if isinstance(x, bool) or not isinstance(x, int):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"integer expected at {where}")
    return x


def parse_digest(x: object, where: str) -> bytes:
    """``sha256:<64 lowercase hex>`` to its 32 bytes; anything else is refused."""
    if isinstance(x, float):
        raise ExactError("RR-FLOAT", f"float at {where}")
    if not isinstance(x, str) or DIGEST_TEXT.fullmatch(x) is None:
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: a digest is sha256:<64 lowercase hex>")
    return bytes.fromhex(x.split(":", 1)[1])


def fmt_digest(b: bytes) -> str:
    return "sha256:" + b.hex()


def parse_text(x: object, where: str) -> str:
    """A hosted text: printable ASCII of at most ``MAX_TEXT`` characters."""
    if isinstance(x, float):
        raise ExactError("RR-FLOAT", f"float at {where}")
    if not isinstance(x, str) or len(x) > MAX_TEXT or TEXT_CHARS.fullmatch(x) is None:
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: a text is printable ASCII of at most {MAX_TEXT} characters")
    return x


def from_json(obj: object, where: str = "structure") -> FiniteStructure:
    refuse_hollow(obj, where)
    if not isinstance(obj, dict):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where} is not an object")
    unknown = set(obj) - {"sorts", "symbols", "tuples", "values", "digests", "texts"}
    if unknown or not {"sorts", "symbols", "tuples"} <= set(obj):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where} has the wrong field set")
    sorts_raw, syms_raw, tuples_raw = obj["sorts"], obj["symbols"], obj["tuples"]
    values_raw = obj.get("values", [])
    digests_raw = obj.get("digests", [])
    texts_raw = obj.get("texts", [])
    if not all(isinstance(x, list) for x in (sorts_raw, syms_raw, tuples_raw, values_raw, digests_raw, texts_raw)):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where} fields must be lists")
    assert isinstance(sorts_raw, list) and isinstance(syms_raw, list)
    assert isinstance(tuples_raw, list) and isinstance(values_raw, list) and isinstance(digests_raw, list)
    assert isinstance(texts_raw, list)
    sorts = tuple((str(s), _int(c, f"{where}.sorts")) for s, c in sorts_raw)
    symbols = tuple(
        RelSym(str(d["name"]), tuple(str(x) for x in d["sorts"])) for d in syms_raw
    )
    tuples = tuple(
        (str(s), tuple(_int(a, f"{where}.tuples") for a in args)) for s, args in tuples_raw
    )
    values = tuple((_int(e, f"{where}.values"), parse_q(v)) for e, v in values_raw)
    digests = tuple((_int(e, f"{where}.digests"), parse_digest(v, f"{where}.digests")) for e, v in digests_raw)
    texts = tuple((_int(e, f"{where}.texts"), parse_text(v, f"{where}.texts")) for e, v in texts_raw)
    fs = FiniteStructure(sorts, symbols, tuples, values, digests, texts)
    validate(fs, where)
    return fs


def to_json(fs: FiniteStructure) -> dict[str, object]:
    """The draft form; ``digests`` and ``texts`` appear only when the
    structure carries one."""
    out: dict[str, object] = {
        "sorts": [[s, c] for s, c in fs.sorts],
        "symbols": [{"name": r.name, "sorts": list(r.sorts)} for r in fs.symbols],
        "tuples": [[s, list(a)] for s, a in fs.tuples],
        "values": [[e, fmt_q(v)] for e, v in fs.values],
    }
    if fs.digests:
        out["digests"] = [[e, fmt_digest(b)] for e, b in fs.digests]
    if fs.texts:
        out["texts"] = [[e, t] for e, t in fs.texts]
    return out


def _validate_names(fs: FiniteStructure, where: str) -> None:
    names = [s for s, _ in fs.sorts] + [r.name for r in fs.symbols]
    for nm in names:
        if not NAME.match(nm):
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: name {nm!r} is not a native identifier")
    if len(set(names)) != len(names):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: sort and symbol names collide")


def _validate_caps(fs: FiniteStructure, where: str) -> None:
    if any(c < 0 for _, c in fs.sorts):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: negative sort count")
    if fs.n() > MAX_CARRIER:
        raise IntakeRefusal("SIZE_CAP", f"{where}: carrier over {MAX_CARRIER}")
    if len(fs.tuples) > MAX_TUPLES:
        raise IntakeRefusal("SIZE_CAP", f"{where}: over {MAX_TUPLES} tuples")


def _validate_symbols(fs: FiniteStructure, where: str) -> None:
    sort_names = {s for s, _ in fs.sorts}
    for r in fs.symbols:
        for s in r.sorts:
            if s not in sort_names:
                raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: symbol {r.name} names unknown sort")


def _validate_tuple_rows(fs: FiniteStructure, where: str) -> None:
    sym_names = {r.name for r in fs.symbols}
    for s, _ in fs.tuples:
        if s not in sym_names:
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: tuple on unknown symbol {s}")
    if len(set(fs.tuples)) != len(fs.tuples):
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: duplicate tuple")


def _validate_values(fs: FiniteStructure, where: str, seen: set[int]) -> None:
    for e, v in fs.values:
        if not isinstance(v, Q):
            raise ExactError("RR-FLOAT", f"{where}: value is not exact")
        if e in seen or not 0 <= e < fs.n():
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: bad value element {e}")
        seen.add(e)


def _validate_digests(fs: FiniteStructure, where: str, seen: set[int]) -> None:
    for e, b in fs.digests:
        if not isinstance(b, bytes) or len(b) != DIGEST_BYTES:
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: a digest is exactly {DIGEST_BYTES} bytes")
        # An element carries one value, a rational or a digest, never both.
        if e in seen or not 0 <= e < fs.n():
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: bad digest element {e}")
        seen.add(e)


def _validate_texts(fs: FiniteStructure, where: str, seen: set[int]) -> None:
    for e, t in fs.texts:
        parse_text(t, f"{where}.texts")
        # A text is one more kind of value: never beside a rational or a digest.
        if e in seen or not 0 <= e < fs.n():
            raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: bad text element {e}")
        seen.add(e)


def validate(fs: FiniteStructure, where: str = "structure") -> None:
    _validate_names(fs, where)
    _validate_caps(fs, where)
    _validate_symbols(fs, where)
    _validate_tuple_rows(fs, where)
    seen: set[int] = set()
    _validate_values(fs, where, seen)
    _validate_digests(fs, where, seen)
    _validate_texts(fs, where, seen)
