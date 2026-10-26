"""General cells and the parallel-one-cells check.

AuthorityEffect: None.

Source: mss_n_grammar_000.md section 13. A general cell packet has shape
`op<<1011><dimension><id>source target>` (opcode `<1011>` from the section 5
table). Doc section 13's own words: "The two-cell does not become meaningful
merely because the packet parses. The host must verify that its source and
target are parallel one-cells in the admitted context." `verify_parallel`
(and `verify_two_cell_is_well_formed`, which uses it) is exactly that host
verification, implemented and tested against the doc's own three worked
examples (a 0-cell, a 1-cell, and a 2-cell comparing two parallel 1-cells).
"""

from __future__ import annotations

from dataclasses import dataclass

from .grammar import App, Atom, Packet

__all__ = [
    "CELL_OPCODE",
    "Cell",
    "cell_from_packet",
    "verify_parallel",
    "verify_two_cell_is_well_formed",
]

CELL_OPCODE = "1011"


@dataclass(frozen=True)
class Cell:
    """A parsed general cell: dimension, a raw identifier word (kept as a
    string, never compared for parallelism -- see `verify_parallel`), and a
    source/target which are themselves either a plain Packet (for a 0-cell,
    or a 1-cell's object endpoints) or a nested Cell (for an n-cell with
    n >= 2, comparing lower cells).
    """

    dimension: int
    id: str
    source: Packet | "Cell"
    target: Packet | "Cell"


def _binary_word_to_int(word: str) -> int:
    if not set(word) <= {"0", "1"}:
        raise ValueError(f"dimension word {word!r} is not a binary word")
    return int(word, 2)


def cell_from_packet(packet: Packet) -> Cell:
    """Parse a general cell packet `op<<1011><dimension><id>source target>`.

    Recursively parses `source`/`target` as nested `Cell` objects when they
    themselves look like cell packets (an App whose first child is the
    `<1011>` opcode atom); otherwise leaves them as the raw parsed Packet
    (this is exactly what happens for the doc's own 0-cell and 1-cell
    examples, whose source/target are `Diff()`/`Atom` object identifiers,
    not nested cells).
    """
    if not isinstance(packet, App) or len(packet.children) != 5:
        raise ValueError(
            f"not a 5-child cell application (opcode, dimension, id, source, "
            f"target): {packet!r}"
        )
    opcode, dim_atom, id_atom, source_raw, target_raw = packet.children
    if not (isinstance(opcode, Atom) and opcode.word == CELL_OPCODE):
        raise ValueError(f"first child is not the {CELL_OPCODE!r} cell opcode: {packet!r}")
    if not isinstance(dim_atom, Atom):
        raise ValueError(f"second child (dimension) is not an atom: {packet!r}")
    if not isinstance(id_atom, Atom):
        raise ValueError(f"third child (id) is not an atom: {packet!r}")
    dimension = _binary_word_to_int(dim_atom.word)

    def maybe_nested_cell(child: Packet) -> Packet | Cell:
        if isinstance(child, App) and len(child.children) == 5:
            first = child.children[0]
            if isinstance(first, Atom) and first.word == CELL_OPCODE:
                return cell_from_packet(child)
        return child

    return Cell(
        dimension=dimension,
        id=id_atom.word,
        source=maybe_nested_cell(source_raw),
        target=maybe_nested_cell(target_raw),
    )


def verify_parallel(cell_a: Cell, cell_b: Cell) -> bool:
    """Two n-cells are PARALLEL iff they share dimension, source, AND target.

    Note precisely what is NOT compared: `id`. The doc's own worked example
    (section 13) compares two distinct, differently-IDed 1-cells (`id='10'`
    and `id='11'`) that both run from object `0` to object `1` -- they are
    parallel precisely because "parallel" is a statement about endpoints,
    not about identity/name.
    """
    return (
        cell_a.dimension == cell_b.dimension
        and cell_a.source == cell_b.source
        and cell_a.target == cell_b.target
    )


def verify_two_cell_is_well_formed(two_cell: Cell) -> bool:
    """The host verification doc section 13 demands: for a 2-cell, its own
    `.source` and `.target` must themselves be `Cell` objects one dimension
    lower, and those two lower cells must be parallel to each other. A
    2-cell whose source/target are mismatched dimension, or are not
    themselves cells at all, or ARE cells but are not parallel, is not
    "meaningful merely because the packet parses" -- it fails this check.
    """
    src, tgt = two_cell.source, two_cell.target
    if not (isinstance(src, Cell) and isinstance(tgt, Cell)):
        return False
    if src.dimension != two_cell.dimension - 1 or tgt.dimension != two_cell.dimension - 1:
        return False
    return verify_parallel(src, tgt)
