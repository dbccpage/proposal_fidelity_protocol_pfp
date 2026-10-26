"""Glyph-calculus analyzer: carrier codepoint pin, op linter, strict parse.

WP-4 of the OEv1.0 Symbol Game build. These are the checks a host must run
before it treats a reply as anything but prose, and they are deliberately the
cheapest ones in the programme: each is decidable from the declared packet
alone, with no grammar, no decoder and no probability model.

Three checks live here.

* **Carrier codepoint pin.** The declared carrier is an allowlist of exact
  codepoints. Any character outside it is refused.
* **First-token op linter.** Every ledger row begins with exactly one op drawn
  from a closed set.
* **Strict parse.** Duplicate keys and unknown fields are refusals, not
  last-one-wins.

On why the pin is an allowlist and not a normalisation
-----------------------------------------------------

The obvious implementation is to fold a suspect character with NFKC and see
whether it lands on a carrier member. Measured on this interpreter, that does
not work for the attack it would be built to stop:

    NFKC(U+237A APL FUNCTIONAL SYMBOL ALPHA) == U+237A   # unchanged
    NFKC(U+1D6C2 MATHEMATICAL BOLD SMALL ALPHA) == U+03B1

The APL alpha -- the one actually used in the document that motivated this
module -- has no compatibility decomposition, so a normalising check passes it
straight through. Cyrillic small a is the same story. An allowlist refuses all
three without needing to anticipate any of them, which is the whole argument
for allowlists over blocklists.

Unicode name similarity is used only to *describe* a refusal, never to decide
one. `looks_like` in a finding is a courtesy to a human reader.

AuthorityEffect: None. A clean lint is not an admission and licenses nothing.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

__all__ = [
    "CLOSED_OPS",
    "REFUSAL_CARRIER_CODEPOINT",
    "REFUSAL_CARRIER_MISMATCH",
    "REFUSAL_DUPLICATE_KEY",
    "REFUSAL_OP_UNDECLARED",
    "REFUSAL_STATEMENT_ILL_FORMED",
    "REFUSAL_UNKNOWN_FIELD",
    "Carrier",
    "CarrierMember",
    "Finding",
    "check_no_duplicate_keys",
    "check_no_unknown_fields",
    "lint_ledger_row",
    "lint_rows",
]

#: The closed op set, from the glyph-calculus contract in the design note.
#:
#: Nine ops, and `LAND` is among them. The document this module was written
#: against declared only eight and omitted `LAND` while using it three times;
#: the contract closed that gap by declaring it rather than by dropping the
#: usages. `QED` was never declared and is still not.
CLOSED_OPS: tuple[str, ...] = (
    "PROVE",
    "SHOW",
    "DECIDE",
    "EXHAUST",
    "REDUCE",
    "LAND",
    "PIN",
    "REFUSE",
    "OPEN",
)

REFUSAL_CARRIER_CODEPOINT = "FW-CARRIER-CODEPOINT"
#: The packet declares a carrier, and it is not the one the host pins.
#: Distinct from FW-CARRIER-CODEPOINT: every character may be perfectly
#: legal under the carrier the packet supplied, and the objection is that
#: the packet supplied it.
REFUSAL_CARRIER_MISMATCH = "FW-CARRIER-MISMATCH"
REFUSAL_OP_UNDECLARED = "FW-OP-UNDECLARED"
REFUSAL_DUPLICATE_KEY = "FW-DUPLICATE-KEY"
#: The statement parsed into a form the host decides, and then named
#: something with no value -- `17 mod 0 = 2`. Not a contradiction: a
#: claim with no truth value cannot be false, so the host declines to
#: admit the row rather than holding a different answer to it.
REFUSAL_STATEMENT_ILL_FORMED = "FW-STATEMENT-ILL-FORMED"
REFUSAL_UNKNOWN_FIELD = "FW-UNKNOWN-FIELD"


@dataclass(frozen=True, slots=True)
class Finding:
    """One refusal, with the code a receipt would carry."""

    code: str
    detail: str
    row: int | None = None

    def __str__(self) -> str:
        where = "" if self.row is None else f" (row {self.row})"
        return f"{self.code}{where}: {self.detail}"


def _codepoint_label(char: str) -> str:
    """`U+03B1 GREEK SMALL LETTER ALPHA`, and never the raw glyph.

    Findings are printed on Windows consoles that are cp1252 by default, where
    emitting the glyph itself raises `UnicodeEncodeError` and turns a refusal
    into a crash.
    """
    name = unicodedata.name(char, "<unnamed>")
    return f"U+{ord(char):04X} {name}"


def _last_name_word(char: str) -> str:
    name = unicodedata.name(char, "")
    return name.rsplit(" ", 1)[-1] if name else ""


@dataclass(frozen=True, slots=True)
class CarrierMember:
    """One declared carrier symbol, pinned to an exact codepoint."""

    symbol: str
    codepoint: str

    @property
    def char(self) -> str:
        if not self.codepoint.startswith("U+"):
            raise ValueError(
                f"carrier member {self.symbol!r} declares {self.codepoint!r}, "
                "which is not a U+XXXX codepoint"
            )
        return chr(int(self.codepoint[2:], 16))


@dataclass(frozen=True, slots=True)
class Carrier:
    """A finite allowlist of codepoints, and nothing else is admissible."""

    members: tuple[CarrierMember, ...]

    @classmethod
    def from_wire(cls, wire: Iterable[object]) -> "Carrier":
        members: list[CarrierMember] = []
        seen_symbols: set[str] = set()
        seen_chars: set[str] = set()
        for entry in wire:
            if not isinstance(entry, dict):
                raise ValueError("each carrier member must be a mapping")
            missing = {"symbol", "codepoint"} - set(entry)
            if missing:
                raise ValueError(f"carrier member is missing {sorted(missing)}")
            extra = set(entry) - {"symbol", "codepoint"}
            if extra:
                raise ValueError(f"carrier member has unknown fields {sorted(extra)}")
            member = CarrierMember(str(entry["symbol"]), str(entry["codepoint"]))
            if member.symbol in seen_symbols:
                raise ValueError(f"carrier declares {member.symbol!r} twice")
            # Two names for one codepoint make the pin ambiguous, so it is
            # refused at declaration rather than at use.
            if member.char in seen_chars:
                raise ValueError(
                    f"carrier binds {_codepoint_label(member.char)} to more than one symbol"
                )
            seen_symbols.add(member.symbol)
            seen_chars.add(member.char)
            members.append(member)
        if not members:
            raise ValueError("a carrier declares at least one member")
        return cls(tuple(members))

    @property
    def glyphs(self) -> frozenset[str]:
        return frozenset(member.char for member in self.members)

    def check_term(self, term: str, *, row: int | None = None) -> tuple[Finding, ...]:
        """Refuse every character of `term` that the carrier does not declare.

        For a carrier *term* -- a landing value, a cycle listing -- where the
        rule is absolute: the declared members and nothing else.

        Reports each offending codepoint once, in first-appearance order, so a
        long term does not bury the finding under repetitions.
        """
        return self._check(term, row=row, skip_ascii=False)

    def check_ledger_text(
        self, sentence: str, *, row: int | None = None
    ) -> tuple[Finding, ...]:
        """Refuse non-ASCII characters in a ledger row that are not members.

        A ledger row is prose plus carrier glyphs, so `check_term` is the wrong
        instrument for it -- it would refuse the prose. The rule that does hold
        is narrower and still exact: **the ledger is ASCII plus carrier.** Every
        character above U+007F in a row is either a declared member or an
        impostor, and a homoglyph substitution is always the latter.

        This is a rule about the ledger surface, not a softening of the pin. A
        term still gets `check_term`.
        """
        return self._check(sentence, row=row, skip_ascii=True)

    def _check(
        self, text: str, *, row: int | None, skip_ascii: bool
    ) -> tuple[Finding, ...]:
        allowed = self.glyphs
        findings: list[Finding] = []
        reported: set[str] = set()
        for char in text:
            if char in allowed or char in reported:
                continue
            if skip_ascii and char.isascii():
                continue
            reported.add(char)
            detail = (
                f"{_codepoint_label(char)} is not a declared carrier member; "
                f"declared: {', '.join(sorted(_codepoint_label(g) for g in allowed))}"
            )
            confusable = sorted(
                member.symbol
                for member in self.members
                if _last_name_word(member.char)
                and _last_name_word(member.char) == _last_name_word(char)
            )
            if confusable:
                # Advisory only. The refusal above already stands on the
                # allowlist; this line exists so a human can see why the
                # substitution was invisible on the page.
                detail += f" -- looks like {', '.join(confusable)}"
            findings.append(Finding(REFUSAL_CARRIER_CODEPOINT, detail, row))
        return tuple(findings)


def lint_ledger_row(sentence: str, *, row: int | None = None) -> tuple[Finding, ...]:
    """Every ledger row begins with exactly one op from the closed set."""
    stripped = sentence.strip()
    if not stripped:
        return (Finding(REFUSAL_OP_UNDECLARED, "row is empty", row),)

    tokens = stripped.split()
    # `op: PROVE`, `op PROVE` and a bare `PROVE` all appear in the corpus, so
    # the op may be the first or the second token. Index it rather than
    # re-splitting, or the prefix form makes its own op look like a second one.
    start = 1 if tokens[0].rstrip(":").upper() == "OP" else 0
    token = tokens[start].rstrip(":") if start < len(tokens) else ""
    following = tokens[start + 1].rstrip(":") if start + 1 < len(tokens) else None

    if not token:
        return (Finding(REFUSAL_OP_UNDECLARED, "row declares no op", row),)
    if token not in CLOSED_OPS:
        # Case-sensitive on purpose. The ops are pinned tokens, not words: a
        # closed set matched case-insensitively is a different, larger set, and
        # the caller downstream builds a receipt row keyed on the op exactly as
        # written.
        hint = ""
        if token.upper() in CLOSED_OPS:
            hint = f" (case variant of {token.upper()}; ops are pinned tokens)"
        return (
            Finding(
                REFUSAL_OP_UNDECLARED,
                f"{token!r} is not a declared op{hint}; the closed set is "
                f"{', '.join(CLOSED_OPS)}",
                row,
            ),
        )

    # "Every ledger row begins with exactly ONE declared op." A second op token
    # makes the row's evidence class ambiguous -- the op IS the evidence class,
    # so two of them claim two, and a reader cannot tell which the statement is
    # offered under.
    if following is not None and following in CLOSED_OPS:
        return (
            Finding(
                REFUSAL_OP_UNDECLARED,
                f"row opens with {token!r} and then {following!r}; a row "
                "declares exactly one op, and the op is the evidence class",
                row,
            ),
        )
    return ()


def lint_rows(
    rows: Sequence[str], carrier: Carrier | None = None
) -> tuple[Finding, ...]:
    """Lint a whole ledger: op discipline, then carrier discipline.

    Rows are numbered from 1 so a finding names the row a reader would count.
    """
    findings: list[Finding] = []
    for index, sentence in enumerate(rows, start=1):
        findings.extend(lint_ledger_row(sentence, row=index))
        if carrier is not None:
            findings.extend(carrier.check_ledger_text(sentence, row=index))
    return tuple(findings)


def check_no_duplicate_keys(
    pairs: Iterable[tuple[str, object]]
) -> tuple[Finding, ...]:
    """Refuse a mapping that names any key twice.

    Both JSON and YAML resolve a repeated key by keeping the last one, silently.
    A packet whose meaning depends on which parser read it is not a packet, so
    the repetition is a refusal rather than a resolution. Wire this in as
    `json.load(..., object_pairs_hook=...)`.
    """
    seen: set[str] = set()
    findings: list[Finding] = []
    for key, _ in pairs:
        if key in seen:
            findings.append(
                Finding(
                    REFUSAL_DUPLICATE_KEY,
                    f"key {key!r} appears more than once; last-one-wins is not a "
                    "reading this host will perform",
                )
            )
            continue
        seen.add(key)
    return tuple(findings)


def check_no_unknown_fields(
    mapping: dict[str, object], allowed: Iterable[str]
) -> tuple[Finding, ...]:
    """Refuse fields the schema does not declare.

    The Rust wire side gets this from 26 `deny_unknown_fields` structs. The
    prompt surfaces had no equivalent, so an unrecognised field was accepted
    and ignored -- which is how a field that a reader believes is load-bearing
    turns out to be inert.
    """
    permitted = set(allowed)
    unknown = sorted(set(mapping) - permitted)
    return tuple(
        Finding(
            REFUSAL_UNKNOWN_FIELD,
            f"field {name!r} is not declared by the schema; declared: "
            f"{', '.join(sorted(permitted))}",
        )
        for name in unknown
    )
