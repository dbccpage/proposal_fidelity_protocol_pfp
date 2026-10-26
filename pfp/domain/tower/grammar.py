"""A fresh recursive-descent parser for Grammar.

AuthorityEffect: None.

Source spec (real, on disk, read in full):
    genesis/008_mssn_s_n_symbol_game_recovery/code/python/_docs/_the_symbol_game_history/
    mss_n_grammar.md

This parser does not exist anywhere else in this repository, in any language.
A repo-wide grep for the literal wire strings this grammar produces (`op<<`,
`0><><0><1`) found zero real parsers -- one promisingly-named file,
`code/python/_docs/_the_symbol_game_history/mss_parser.rs` (and its Rust-tree
duplicate), turned out to implement a completely different, unrelated toy
grammar (`"A OP B > C"`-style flat token matching, no recursive bracket
nesting). This module is this notebook series' own original contribution --
labelled as such everywhere it is used, never cited as if it already existed.

The grammar (doc section 2, transcribed exactly)::

    packet  ::= diff | atom | app
    diff    ::= <>
    atom    ::= <word>
    app     ::= op<packet*>
    word    ::= alnum+
    alnum   ::= 0|1|2|...|9|a|b|...|z

Parsing law 6 ("the parser uses maximal recognition of the reserved prefix
`op<`") plus law 5 ("siblings require no commas because every child is
self-delimiting") together make this grammar parseable with exactly one
character of lookahead at every choice point: a packet position either begins
with the three literal characters `op<` (an application) or with `<` (a diff
or an atom) -- nothing else is legal at a packet position. Inside an
application, the loop "parse one child, then check whether the next character
closes the application" needs no bracket counting, because each child
consumes exactly its own delimiters recursively (doc section 2.2).
"""

from __future__ import annotations

from dataclasses import dataclass

from . import golden_corpus

__all__ = [
    "Packet",
    "Diff",
    "Atom",
    "App",
    "GrammarError",
    "parse",
    "serialize",
    "is_active_at_level",
    "ACTIVE_ALPHABET_BY_LEVEL",
]


# --- The AST ------------------------------------------------------------


@dataclass(frozen=True)
class Diff:
    """The unique empty atom `<>` -- Primitive Difference (doc section 3.1)."""

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return "Diff()"

    def serialize(self) -> str:
        return "<>"

    def __str__(self) -> str:
        return self.serialize()


@dataclass(frozen=True)
class Atom:
    """A named atom `<word>`. `word` is a nonempty string over Sigma36."""

    word: str

    def __post_init__(self) -> None:
        if type(self.word) is not str:
            raise TypeError("Atom.word must be a string")
        if not self.word:
            raise ValueError("Atom.word must be nonempty (use Diff() for <>)")
        bad = set(self.word) - golden_corpus.SIGMA_36
        if bad:
            raise ValueError(f"Atom.word contains glyphs outside Sigma36: {sorted(bad)!r}")

    @property
    def value(self) -> str:
        """The atom payload as used by typed packet contracts."""
        return self.word

    def serialize(self) -> str:
        return f"<{self.word}>"

    def __str__(self) -> str:
        return self.serialize()

    def is_binary(self) -> bool:
        return set(self.word) <= {"0", "1"}

    def as_binary_int(self) -> int:
        if not self.is_binary():
            raise ValueError("atom is not binary")
        return int(self.word, 2)


@dataclass(frozen=True)
class App:
    """An application `op<child1 child2 ...>`. Zero or more children."""

    children: tuple["Packet", ...]

    def __post_init__(self) -> None:
        if type(self.children) is not tuple or any(
            type(c) not in (Diff, Atom, App) for c in self.children
        ):
            raise TypeError("App.children must be a tuple of canonical packet nodes")

    @property
    def opcode(self) -> str | None:
        return self.children[0].word if self.children and type(self.children[0]) is Atom else None

    @property
    def opcode_node(self) -> "Packet":
        if not self.children:
            raise ValueError("untyped application has no opcode")
        return self.children[0]

    @property
    def arguments(self) -> tuple["Packet", ...]:
        return self.children[1:]

    def arity(self) -> int:
        return len(self.arguments)

    def serialize(self) -> str:
        return "op<" + "".join(c.serialize() for c in self.children) + ">"

    def __str__(self) -> str:
        return self.serialize()


Packet = Diff | Atom | App


# --- Parsing errors -------------------------------------------------------


class GrammarError(ValueError):
    """A Grammar syntax error.

    `reason` is this parser's own, mechanical, first-point-of-failure
    diagnosis. It is deliberately NOT forced to match the source doc's
    one-word classification for the same invalid string (see
    golden_corpus.INVALID's docstring) -- a recursive-descent parser reports
    where *it* first gets stuck, which is an honest and reproducible fact
    about this implementation, not necessarily the same phrasing a human
    would reach for. Where the two agree, that is worth noting; where they
    do not, that is worth noting too, not silently smoothed over.
    """

    def __init__(self, message: str, *, reason: str, position: int) -> None:
        super().__init__(f"{message} (at position {position}): {reason}")
        self.reason = reason
        self.position = position


class _Cursor:
    """A minimal position-tracking string reader used only inside parse()."""

    __slots__ = ("text", "pos")

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def eof(self) -> bool:
        return self.pos >= len(self.text)

    def peek(self, n: int = 1) -> str:
        return self.text[self.pos : self.pos + n]

    def advance(self, n: int) -> None:
        self.pos += n

    def fail(self, message: str, *, reason: str) -> "GrammarError":
        return GrammarError(message, reason=reason, position=self.pos)


def _parse_alnum_run(cur: _Cursor) -> str:
    start = cur.pos
    while not cur.eof() and cur.peek() in golden_corpus.SIGMA_36:
        cur.advance(1)
    return cur.text[start : cur.pos]


def _parse_one(cur: _Cursor) -> Packet:
    """Parse exactly one packet starting at cur.pos, advancing cur.pos past it."""
    if cur.peek(3) == "op<":
        cur.advance(3)
        children: list[Packet] = []
        while True:
            if cur.eof():
                raise cur.fail(
                    "reached end of input while inside an application",
                    reason="unclosed application",
                )
            if cur.peek() == ">":
                cur.advance(1)
                return App(tuple(children))
            children.append(_parse_one(cur))
    if cur.peek() == "<":
        cur.advance(1)
        word = _parse_alnum_run(cur)
        if cur.eof() or cur.peek() != ">":
            # The word run stopped on something that is neither a legal
            # Sigma36 glyph nor '>'. This single, uniform message is used
            # regardless of which forbidden character (comma, bare '>', ...)
            # caused it -- see the module docstring: this parser reports its
            # own first point of failure honestly rather than guessing which
            # one-word category a human would file the string under.
            bad_char = cur.peek(1) if not cur.eof() else "<end of input>"
            raise cur.fail(
                f"expected '>' to close an atom/diff, found {bad_char!r}",
                reason=f"unterminated atom/diff before {bad_char!r}",
            )
        cur.advance(1)  # consume '>'
        return Diff() if word == "" else Atom(word)
    # Neither "op<" nor "<": this position cannot start any packet at all --
    # whether that is the very first character of the whole input (a bare,
    # unwrapped value where an outer packet was expected) or a position deep
    # inside an application's children list (a bare, unwrapped value where a
    # self-delimited child was expected) is the same mechanical failure, and
    # is reported the same way; see the module docstring.
    bad_char = cur.peek(1) if not cur.eof() else "<end of input>"
    raise cur.fail(
        f"expected a packet ('<...' or 'op<...') but found bare content starting with {bad_char!r}",
        reason=f"unwrapped/bare content starting with {bad_char!r}",
    )


def parse(text: str) -> Packet:
    """Parse a COMPLETE input as exactly one outer packet (parsing law 1).

    Raises GrammarError if the text is not a single well-formed packet, or if
    anything trails after the outer packet's own closing delimiter.
    """
    cur = _Cursor(text)
    packet = _parse_one(cur)
    if not cur.eof():
        raise cur.fail(
            f"trailing content after the outer packet: {cur.text[cur.pos :]!r}",
            reason="more than one outer packet (parsing law 1 violation)",
        )
    return packet


def serialize(packet: Packet) -> str:
    """The inverse of parse(). Obligation #2 (doc section 18): serialize . parse
    must be the identity on the AST -- tested directly in
    tests/test_mssn_grammar.py against every VALID corpus member.
    """
    if isinstance(packet, Diff):
        return "<>"
    if isinstance(packet, Atom):
        return f"<{packet.word}>"
    if isinstance(packet, App):
        return "op<" + "".join(serialize(c) for c in packet.children) + ">"
    raise TypeError(f"unknown packet type: {type(packet)!r}")


# --- Level activation (semantic gate, orthogonal to syntax) ----------------

# The active DATA alphabet declared at each MSS level (doc section 4.2: "MSS-1
# active data alphabet: 01"). This is deliberately not extended past level 1
# with the doc's own literal "two glyphs per stage" schedule (section 12.1) --
# that schedule is explicitly declared non-canonical in the same source
# section ("This literal tower stops at MSS-18" vs. "the mathematically
# stronger interpretation... two new protected semantic generators", which the
# doc itself does not reduce to a fixed alphabet). Levels 2 and above are
# reached in this series through explicit new opcodes (graphs, simplices,
# metric structure), not through a wider raw-atom alphabet -- so no entry is
# declared for them here, and asking for one raises rather than guessing.
ACTIVE_ALPHABET_BY_LEVEL: dict[int, frozenset[str]] = {
    1: frozenset("01"),
}


def is_active_at_level(packet: Packet, level: int) -> bool:
    """Is `packet` semantically legal at MSS level `level`?

    This is a SEMANTIC check, independent of parse() succeeding. A packet can
    parse perfectly under Grammar's raw syntax and still be inactive at a
    given level -- that is exactly what golden_corpus.MSS0_FORBIDDEN and the
    sixth entry of golden_corpus.INVALID both demonstrate (the latter's `<2>`
    is a syntactically legal Sigma36 atom that is simply not in MSS-1's
    active alphabet {0, 1}).

    Level 0 (doc section 3): the ONLY legal packet is the bare genesis
    distinction. Not App -- the Up-Lift/opcode mechanism (section 4-5) does
    not exist until MSS-1 -- and not any Atom, since no named symbol exists
    yet either. This is stricter than "empty active alphabet" would imply if
    applied recursively to an App's children (an App built only from Diff
    children would incorrectly pass such a check); MSS-0 excludes App itself,
    not merely restricts what may appear inside one.

    Level n >= 1: every Atom's word, anywhere in the packet (including inside
    nested App children), must use only glyphs in that level's declared
    active alphabet. App is legal at every level >= 1 (the Up-Lift has
    already happened); Diff is legal at every level.
    """
    if level == 0:
        return isinstance(packet, Diff)
    active = ACTIVE_ALPHABET_BY_LEVEL.get(level)
    if active is None:
        raise ValueError(
            f"no declared active alphabet for level {level} "
            "(only level 0 and level 1 are modeled by this module -- see "
            "ACTIVE_ALPHABET_BY_LEVEL's docstring)"
        )

    def walk(p: Packet) -> bool:
        if isinstance(p, Diff):
            return True
        if isinstance(p, Atom):
            return all(ch in active for ch in p.word)
        if isinstance(p, App):
            return all(walk(c) for c in p.children)
        raise TypeError(f"unknown packet type: {type(p)!r}")  # pragma: no cover

    return walk(packet)
