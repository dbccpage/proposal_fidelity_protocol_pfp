"""MSS-N Grammar Levels 0-8 Executable Parser, Serializer, and Validator.

AuthorityEffect: None.

This module implements a deterministic recursive-descent parser, canonical
serializer, and semantic validator for MSS-N Grammar Levels 0 through 8,
conforming to Grammar 1-8 specifications in research/mssn_sn_tower/grammar/.

Wire Alphabet (Gamma38):
    Alphanumeric payload (Sigma36): 0-9, a-z (36 glyphs)
    Structural delimiters: <, > (2 glyphs)
    Reserved constructor prefix: 'op<' (from glyphs 'o', 'p', '<')
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Union

from .grammar import App, Atom, Diff

__all__ = [
    "SIGMA_36",
    "GAMMA_38",
    "Packet",
    "Diff",
    "Atom",
    "App",
    "GrammarError",
    "LexicalError",
    "SyntaxError",
    "ValidationError",
    "SimplexValidationError",
    "OrbitValidationError",
    "RationalValidationError",
    "DualWitnessError",
    "ArityError",
    "parse_packet",
    "serialize_packet",
    "is_active_at_level",
    "validate_packet_semantics",
    "validate_level1_uplift",
    "validate_level2_graph_element",
    "validate_level3_simplex",
    "validate_level5_regge",
    "validate_level7_orbit",
    "validate_level8_harmonic",
    "validate_rational",
    "validate_dual_cert",
]

# --- Character Accounting --------------------------------------------------

SIGMA_36: frozenset[str] = frozenset("0123456789abcdefghijklmnopqrstuvwxyz")
GAMMA_38: frozenset[str] = SIGMA_36 | frozenset({"<", ">"})


# --- AST Definitions -------------------------------------------------------


Packet = Union[Diff, Atom, App]


# --- Error Classes ---------------------------------------------------------


class GrammarError(ValueError):
    """Base class for MSS-N Grammar parsing and syntax errors."""

    def __init__(self, message: str, *, position: int, reason: str) -> None:
        super().__init__(f"{message} (at position {position}): {reason}")
        self.message = message
        self.position = position
        self.reason = reason


class LexicalError(GrammarError):
    """Raised when an input string contains characters outside the Gamma38 wire alphabet."""


class SyntaxError(GrammarError):
    """Raised when delimiter balancing, packet boundaries, or structural parsing fails."""


class ValidationError(ValueError):
    """Base class for Level-specific semantic validation errors."""


class SimplexValidationError(ValidationError):
    """Raised when an abstract simplex violates distinctness, canonical ordering, or dimension."""


class OrbitValidationError(ValidationError):
    """Raised when an orbit record violates period length consistency or primitivity laws."""


class RationalValidationError(ValidationError):
    """Raised when an exact rational number violates denominator positivity or coprime reduction."""


class DualWitnessError(ValidationError):
    """Raised when a dual certificate violates zero duality gap or circulation flow conservation."""


class ArityError(ValidationError):
    """Raised when an opcode application violates its declared child count schema."""


# --- Recursive-Descent Parser ---------------------------------------------


class _Cursor:
    """String reader tracking current read position."""

    __slots__ = ("text", "pos")

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def eof(self) -> bool:
        return self.pos >= len(self.text)

    def peek(self, n: int = 1) -> str:
        return self.text[self.pos : self.pos + n]

    def advance(self, n: int = 1) -> None:
        self.pos += n


def _parse_alnum_run(cur: _Cursor) -> str:
    start = cur.pos
    while not cur.eof() and cur.peek() in SIGMA_36:
        cur.advance(1)
    return cur.text[start : cur.pos]


def _parse_single_packet(cur: _Cursor) -> Packet:
    """Parses one complete packet from the cursor."""
    if cur.peek(3) == "op<":
        cur.advance(3)
        children: list[Packet] = []
        while True:
            if cur.eof():
                raise SyntaxError(
                    "Unexpected EOF inside application",
                    position=cur.pos,
                    reason="unclosed application",
                )
            if cur.peek() == ">":
                cur.advance(1)
                return App(tuple(children))
            children.append(_parse_single_packet(cur))

    if cur.peek() == "<":
        cur.advance(1)
        word = _parse_alnum_run(cur)
        if cur.eof() or cur.peek() != ">":
            bad = cur.peek(1) if not cur.eof() else "<EOF>"
            raise SyntaxError(
                f"Expected '>' to close atom/diff, found {bad!r}",
                position=cur.pos,
                reason=f"unterminated atom/diff before {bad!r}",
            )
        cur.advance(1)  # Consume '>'
        return Diff() if word == "" else Atom(word)

    bad = cur.peek(1) if not cur.eof() else "<EOF>"
    raise SyntaxError(
        f"Expected packet starting with '<' or 'op<', found bare {bad!r}",
        position=cur.pos,
        reason=f"unwrapped bare content starting with {bad!r}",
    )


def parse_packet(text: str) -> Packet:
    """Parses a complete input string as exactly one outer MSS packet.

    Raises:
        LexicalError: If text contains any character outside Gamma38.
        SyntaxError: If text is empty, contains syntax defects, or trailing content.
    """
    if not text:
        raise SyntaxError(
            "Input string is empty",
            position=0,
            reason="empty input",
        )

    # 1. Lexical scan: strict Gamma38 verification
    for idx, ch in enumerate(text):
        if ch not in GAMMA_38:
            raise LexicalError(
                f"Illegal character {ch!r}",
                position=idx,
                reason=f"character {ch!r} outside wire alphabet Gamma38",
            )

    # 2. Structural parse
    cur = _Cursor(text)
    packet = _parse_single_packet(cur)

    # 3. Parsing Law 1: Exactly one complete outer packet
    if not cur.eof():
        raise SyntaxError(
            f"Trailing content after outer packet: {cur.text[cur.pos :]!r}",
            position=cur.pos,
            reason="multiple outer packets or trailing garbage",
        )

    return packet


def serialize_packet(packet: Packet) -> str:
    """Serializes an AST Packet to its canonical wire format.

    Satisfies serialize_packet(parse_packet(s)) == s for all valid wire strings.
    """
    if isinstance(packet, Diff):
        return "<>"
    if isinstance(packet, Atom):
        return f"<{packet.word}>"
    if isinstance(packet, App):
        return "op<" + "".join(serialize_packet(c) for c in packet.children) + ">"
    raise TypeError(f"Unknown packet node type: {type(packet)!r}")


# --- Level Activation Semantics -------------------------------------------


def is_active_at_level(packet: Packet, level: int) -> bool:
    """Checks whether a packet is active at a given MSS level.

    Level 0: Sole legal packet is Diff '<>'.
    Level 1: Atoms must strictly use binary digits '0' and '1'.
    """
    if level == 0:
        return isinstance(packet, Diff)

    if level == 1:
        active = frozenset("01")

        def walk(p: Packet) -> bool:
            if isinstance(p, Diff):
                return True
            if isinstance(p, Atom):
                return all(ch in active for ch in p.word)
            if isinstance(p, App):
                return all(walk(c) for c in p.children)
            raise TypeError(f"Unknown packet type: {type(p)!r}")

        return walk(packet)

    raise ValueError(f"Activation check not defined for level {level}")


# --- Level-Specific Semantic Validators -----------------------------------


def _expect_atom(p: Packet, field_name: str) -> Atom:
    if not isinstance(p, Atom):
        raise ValidationError(f"Field '{field_name}' must be an Atom, got {type(p).__name__}")
    return p


def _expect_app(p: Packet, field_name: str) -> App:
    if not isinstance(p, App):
        raise ValidationError(f"Field '{field_name}' must be an App, got {type(p).__name__}")
    return p


def _parse_binary_int(atom: Atom, field_name: str) -> int:
    try:
        return int(atom.word, 2)
    except ValueError:
        raise ValidationError(
            f"Field '{field_name}' expects binary integer string, got {atom.word!r}"
        )


def validate_level1_uplift(app: App) -> None:
    """Validates opcode <0> Up-Lift: `op<<0><><0><1>>`."""
    if len(app.children) != 4:
        raise ArityError(
            f"Up-Lift opcode <0> expects exactly 3 children (diff, sym0, sym1), got {len(app.children) - 1}"
        )
    if not isinstance(app.children[1], Diff):
        raise ValidationError("Up-Lift child 1 must be Diff '<>'")
    _expect_atom(app.children[2], "sym0")
    _expect_atom(app.children[3], "sym1")


def validate_level2_graph_element(app: App) -> None:
    """Validates Level 2 graph opcodes:

    - Vertex: `op<<1><id>>`
    - DirectedEdge: `op<<10><u><v>>` (or with rational weight at Level 8)
    - GraphContainer: `op<<11>item*>`
    - ObstructionWitness: `op<<100><>carrier>`
    """
    opcode = app.opcode
    if opcode == "1":
        if len(app.children) != 2:
            raise ArityError(
                f"Vertex opcode <1> expects exactly 1 child, got {len(app.children) - 1}"
            )
        _expect_atom(app.children[1], "vertex_id")

    elif opcode == "10":
        if len(app.children) not in (3, 4):
            raise ArityError(
                f"DirectedEdge opcode <10> expects 2 or 3 children, got {len(app.children) - 1}"
            )
        u = _expect_atom(app.children[1], "source")
        v = _expect_atom(app.children[2], "target")
        if u.word == v.word:
            raise ValidationError(
                f"Irreflexivity violation: directed edge self-loop forbidden ({u.word} -> {v.word})"
            )
        if len(app.children) == 4:
            # Level 8 weighted edge entry
            validate_rational(_expect_app(app.children[3], "weight"))

    elif opcode == "100":
        if len(app.children) != 3:
            raise ArityError(
                f"ObstructionWitness opcode <100> expects 2 children (<> and carrier), got {len(app.children) - 1}"
            )
        if not isinstance(app.children[1], Diff):
            raise ValidationError("ObstructionWitness child 1 must be Diff '<>'")

    elif opcode == "11":
        # GraphContainer: validate child items recursively
        for child in app.children[1:]:
            if isinstance(child, App):
                validate_packet_semantics(child)


def validate_level3_simplex(app: App) -> None:
    """Validates abstract simplex opcode <101>: `op<<101><dim><v0><v1>...<vn>>`.

    Laws:
    1. Dimension matching: exactly dim + 1 vertices.
    2. Distinctness: all vertices must be strictly pairwise distinct.
    3. Canonical ordering: vertices must be in strictly ascending binary integer order.
    """
    if len(app.children) < 2:
        raise ArityError("Simplex opcode <101> requires at least a dimension atom")

    dim_atom = _expect_atom(app.children[1], "dimension")
    dim = _parse_binary_int(dim_atom, "dimension")
    expected_vertex_count = dim + 1

    vertex_atoms: list[Atom] = []
    for idx, child in enumerate(app.children[2:]):
        vertex_atoms.append(_expect_atom(child, f"vertex_{idx}"))

    if len(vertex_atoms) != expected_vertex_count:
        raise SimplexValidationError(
            f"Dimension mismatch: declared dimension {dim} requires {expected_vertex_count} vertices, "
            f"got {len(vertex_atoms)}"
        )

    # 1. Distinctness Check
    seen_words: set[str] = set()
    for v in vertex_atoms:
        if v.word in seen_words:
            raise SimplexValidationError(
                f"Vertex distinctness violation: duplicate vertex <{v.word}> in simplex"
            )
        seen_words.add(v.word)

    # 2. Canonical Ordering Check (strictly ascending binary integers)
    int_values = [_parse_binary_int(v, "vertex") for v in vertex_atoms]
    for i in range(len(int_values) - 1):
        if int_values[i] >= int_values[i + 1]:
            raise SimplexValidationError(
                f"Canonical ordering violation: vertices {[v.word for v in vertex_atoms]} "
                f"are not in strictly ascending order ({int_values[i]} >= {int_values[i + 1]})"
            )


def validate_level5_regge(app: App) -> None:
    """Validates Level 5 metric and Regge opcodes:

    - EdgeLength: `op<<110><u><v><val>>`
    - MetricSimplex: `op<<111>simplex length*>`
    - DeficitReceipt: `op<<1010><dim>hinge<full><sum><residual>>`
    """
    opcode = app.opcode
    if opcode == "110":
        if len(app.children) != 4:
            raise ArityError(
                f"EdgeLength opcode <110> requires 3 children (u, v, val), got {len(app.children) - 1}"
            )
        u = _expect_atom(app.children[1], "u")
        v = _expect_atom(app.children[2], "v")
        if u.word == v.word:
            raise ValidationError(f"Self-loop edge length forbidden ({u.word} == {v.word})")
        val_atom = _expect_atom(app.children[3], "length_value")
        val = _parse_binary_int(val_atom, "length_value")
        if val <= 0:
            raise ValidationError(f"Edge length must be strictly positive, got {val}")

    elif opcode == "111":
        if len(app.children) < 2:
            raise ArityError(
                "MetricSimplex opcode <111> requires at least an abstract simplex child"
            )
        simplex_child = _expect_app(app.children[1], "abstract_simplex")
        if simplex_child.opcode != "101":
            raise ValidationError("MetricSimplex child 1 must be an AbstractSimplex opcode <101>")
        validate_level3_simplex(simplex_child)

        dim = _parse_binary_int(_expect_atom(simplex_child.children[1], "dimension"), "dimension")
        expected_edge_count = (dim * (dim + 1)) // 2
        edge_length_children = app.children[2:]
        if len(edge_length_children) != expected_edge_count:
            raise ValidationError(
                f"MetricSimplex dimension {dim} requires {expected_edge_count} edge length records, "
                f"got {len(edge_length_children)}"
            )
        for idx, el in enumerate(edge_length_children):
            el_app = _expect_app(el, f"edge_length_{idx}")
            if el_app.opcode != "110":
                raise ValidationError("MetricSimplex edge records must have opcode <110>")
            validate_level5_regge(el_app)

    elif opcode == "1010":
        if len(app.children) != 6:
            raise ArityError(
                f"DeficitReceipt opcode <1010> requires 5 children (dim, hinge, full, sum, residual), "
                f"got {len(app.children) - 1}"
            )
        _parse_binary_int(_expect_atom(app.children[1], "dim"), "dim")
        # Hinge can be a vertex app or atom
        if isinstance(app.children[2], App):
            validate_level2_graph_element(app.children[2])

        full = _parse_binary_int(_expect_atom(app.children[3], "full"), "full")
        accum = _parse_binary_int(_expect_atom(app.children[4], "sum"), "sum")
        deficit = _parse_binary_int(_expect_atom(app.children[5], "residual"), "residual")

        if full != accum + deficit:
            raise ValidationError(
                f"Deficit arithmetic violation: full ({full}) != sum ({accum}) + deficit ({deficit})"
            )


def validate_level7_orbit(app: App) -> None:
    """Validates Level 7 dynamical orbit opcodes:

    - PeriodicOrbitTable: `op<<1101>shift_spec orbit_record*>`
    - ShiftSpec: `op<<11010>alphabet_size block_length>`
    - OrbitRecord: `op<<1110>period primitive_flag vertex_seq...>`
    """
    opcode = app.opcode
    if opcode == "11010":
        if len(app.children) != 3:
            raise ArityError(
                f"ShiftSpec opcode <11010> requires alphabet_size and block_length, got {len(app.children) - 1}"
            )
        _parse_binary_int(_expect_atom(app.children[1], "alphabet_size"), "alphabet_size")
        _parse_binary_int(_expect_atom(app.children[2], "block_length"), "block_length")

    elif opcode == "1110":
        if len(app.children) < 3:
            raise ArityError(
                f"OrbitRecord opcode <1110> requires period, primitive_flag, and vertices, got {len(app.children) - 1}"
            )
        period = _parse_binary_int(_expect_atom(app.children[1], "period"), "period")
        flag_atom = _expect_atom(app.children[2], "primitive_flag")
        if flag_atom.word not in ("0", "1"):
            raise OrbitValidationError(
                f"Primitive flag must be '<0>' or '<1>', found {flag_atom.word!r}"
            )

        vertex_atoms: list[Atom] = []
        for idx, child in enumerate(app.children[3:]):
            vertex_atoms.append(_expect_atom(child, f"vertex_{idx}"))

        # 1. Length Consistency Law
        if len(vertex_atoms) != period:
            raise OrbitValidationError(
                f"Length consistency violation: declared period {period} but vertex sequence has length {len(vertex_atoms)}"
            )

        # 2. Primitivity Verification Law
        seq = tuple(v.word for v in vertex_atoms)
        min_period = period
        for k in range(1, period):
            if seq[k:] + seq[:k] == seq:
                min_period = k
                break

        is_primitive = min_period == period
        asserted_primitive = flag_atom.word == "1"

        if asserted_primitive and not is_primitive:
            raise OrbitValidationError(
                f"MalformedPrimitiveClaim: orbit asserting primitive flag <1> has minimal period {min_period} < {period}"
            )

    elif opcode == "1101":
        if len(app.children) < 2:
            raise ArityError(
                "PeriodicOrbitTable opcode <1101> requires at least a shift_spec child"
            )
        shift_spec = _expect_app(app.children[1], "shift_spec")
        if shift_spec.opcode != "11010":
            raise ValidationError("PeriodicOrbitTable child 1 must be ShiftSpec opcode <11010>")
        validate_level7_orbit(shift_spec)

        for idx, child in enumerate(app.children[2:]):
            rec = _expect_app(child, f"orbit_record_{idx}")
            if rec.opcode != "1110":
                raise ValidationError(
                    "PeriodicOrbitTable children must be OrbitRecord opcode <1110>"
                )
            validate_level7_orbit(rec)


def validate_rational(app: App) -> Fraction:
    """Validates opcode <10010> RationalValue: `op<<10010><sign><num><den>>`.

    Laws:
    1. sign is '<0>' (non-negative) or '<1>' (negative).
    2. num >= 0 in binary.
    3. den >= 1 in binary.
    4. Coprime reduction: gcd(num, den) == 1.
    5. Canonical zero: if num == 0, sign must be '<0>' and den must be '<1>'.

    Returns the exact Python Fraction value.
    """
    if app.opcode != "10010":
        raise RationalValidationError(
            f"Expected opcode <10010> for RationalValue, got <{app.opcode}>"
        )
    if len(app.children) != 4:
        raise ArityError(f"RationalValue requires sign, num, and den, got {len(app.children) - 1}")

    sign_atom = _expect_atom(app.children[1], "sign_flag")
    if sign_atom.word not in ("0", "1"):
        raise RationalValidationError(
            f"Rational sign_flag must be '<0>' or '<1>', got {sign_atom.word!r}"
        )

    num = _parse_binary_int(_expect_atom(app.children[2], "num"), "num")
    den = _parse_binary_int(_expect_atom(app.children[3], "den"), "den")

    if den <= 0:
        raise RationalValidationError(f"Rational denominator must be strictly positive, got {den}")

    g = math.gcd(num, den)
    if g != 1:
        raise RationalValidationError(
            f"Rational fraction not reduced: {num}/{den} has gcd {g} != 1"
        )

    if num == 0:
        if sign_atom.word != "0" or den != 1:
            raise RationalValidationError(
                f"Canonical zero must be encoded as op<<10010><0><0><1>>, got sign={sign_atom.word}, den={den}"
            )

    sign = -1 if sign_atom.word == "1" else 1
    return Fraction(sign * num, den)


def validate_dual_cert(app: App) -> None:
    """Validates opcode <10001> DualCertReceipt: `op<<10001>primal_mass dual_mass flow_vector>`.

    Laws:
    1. Zero duality gap: primal_mass == dual_mass.
    2. Circulation conservation: net flow at each vertex must be 0.
    """
    if app.opcode != "10001":
        raise DualWitnessError(f"Expected opcode <10001> for DualCertReceipt, got <{app.opcode}>")
    if len(app.children) != 4:
        raise ArityError(
            f"DualCertReceipt requires primal_mass, dual_mass, and flow_vector, got {len(app.children) - 1}"
        )

    primal_val = validate_rational(_expect_app(app.children[1], "primal_mass"))
    dual_val = validate_rational(_expect_app(app.children[2], "dual_mass"))

    # 1. Zero duality gap
    if primal_val != dual_val:
        raise DualWitnessError(
            f"InfeasibleDualWitness: non-zero duality gap (primal={primal_val}, dual={dual_val})"
        )

    # 2. Circulation flow conservation
    flow_container = _expect_app(app.children[3], "flow_vector")
    if flow_container.opcode != "11":
        raise DualWitnessError("flow_vector must be GraphContainer opcode <11>")

    net_flows: dict[str, Fraction] = {}
    for idx, child in enumerate(flow_container.children[1:]):
        edge_flow = _expect_app(child, f"edge_flow_{idx}")
        if edge_flow.opcode != "10011":
            raise DualWitnessError("flow_vector entries must have opcode <10011>")
        if len(edge_flow.children) != 4:
            raise ArityError(f"EdgeFlow requires u, v, flow_val, got {len(edge_flow.children) - 1}")
        u = _expect_atom(edge_flow.children[1], "u").word
        v = _expect_atom(edge_flow.children[2], "v").word
        val = validate_rational(_expect_app(edge_flow.children[3], "flow_val"))

        net_flows[u] = net_flows.get(u, Fraction(0)) - val
        net_flows[v] = net_flows.get(v, Fraction(0)) + val

    # Verify net flow is 0 at every vertex
    for vertex, net in net_flows.items():
        if net != Fraction(0):
            raise DualWitnessError(
                f"Flow conservation violated at vertex <{vertex}>: net circulation = {net} != 0"
            )


def validate_level8_harmonic(app: App) -> None:
    """Validates Level 8 monadic and harmonic cochain opcodes:

    - AdjunctionPacket: `op<<1111>src tgt unit counit>`
    - HarmonicPacket: `op<<10000>id edges dual_cert>`
    """
    opcode = app.opcode
    if opcode == "1111":
        if len(app.children) != 5:
            raise ArityError(f"AdjunctionPacket requires 4 children, got {len(app.children) - 1}")
        _expect_atom(app.children[1], "level_src")
        _expect_atom(app.children[2], "level_tgt")
        unit = _expect_app(app.children[3], "unit_map")
        counit = _expect_app(app.children[4], "counit_map")
        if unit.opcode != "11110":
            raise ValidationError("Adjunction child 3 must be UnitMap opcode <11110>")
        if counit.opcode != "11111":
            raise ValidationError("Adjunction child 4 must be CounitMap opcode <11111>")

    elif opcode == "10000":
        if len(app.children) != 4:
            raise ArityError(f"HarmonicPacket requires 3 children, got {len(app.children) - 1}")
        _expect_atom(app.children[1], "cochain_id")
        edges = _expect_app(app.children[2], "edge_vector")
        validate_level2_graph_element(edges)
        dual_cert = _expect_app(app.children[3], "dual_cert_receipt")
        validate_dual_cert(dual_cert)


def validate_packet_semantics(packet: Packet) -> None:
    """Recursively validates all recognized semantic opcodes across Levels 0-8."""
    if isinstance(packet, (Diff, Atom)):
        return

    if isinstance(packet, App):
        opcode = packet.opcode
        if opcode == "0":
            validate_level1_uplift(packet)
        elif opcode in ("1", "10", "11", "100"):
            validate_level2_graph_element(packet)
        elif opcode == "101":
            validate_level3_simplex(packet)
        elif opcode in ("110", "111", "1010"):
            validate_level5_regge(packet)
        elif opcode in ("1101", "11010", "1110"):
            validate_level7_orbit(packet)
        elif opcode == "10010":
            validate_rational(packet)
        elif opcode == "10001":
            validate_dual_cert(packet)
        elif opcode in ("1111", "10000"):
            validate_level8_harmonic(packet)
        elif opcode == "1100":
            if len(packet.children) != 2:
                raise ArityError("TypedRefusal opcode <1100> requires exactly 1 code child")
            _expect_atom(packet.children[1], "refusal_code")
        elif opcode == "1011":
            if len(packet.children) != 5:
                raise ArityError("HigherCell opcode <1011> requires 4 children")

        # Recursively validate children
        for child in packet.children:
            if isinstance(child, App):
                validate_packet_semantics(child)
