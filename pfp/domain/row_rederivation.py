"""What the host can decide about a ledger row, on its own, exactly.

Until this module existed, `verify_glyph_reply` recorded every admitted row as
``UNCHECKABLE``. That was honest -- nothing could re-derive an arbitrary
statement -- but it meant ``PASS`` and ``SELF_CONSISTENT_ONLY`` were
*unreachable terminals*: the ladder in :mod:`.calculus_receipt` was enforced and
tested where it lived, and no run could climb it. A receipt that can only ever
say "I could not check this" is not a receipt.

So the host decides three forms, all of them drawn from the glyph-calculus
contract's own worked examples:

    REDUCE 17 mod 5 = 2                 <- self-contained
    PROVE  period(c5) = 5               <- names its subject inline
    LAND   successor^2(alpha) = gamma   <- needs the packet's presentation_ref

Deliberately short
------------------

The list is short on purpose. A decider is a claim that the host **knows** the
answer, so each one has to be exactly decidable from the row plus **host-side**
material -- no model, no network, no heuristic.

Self-contained versus referential
---------------------------------

The three forms differ in where their subject comes from, and that difference is
the whole design.

``17 mod 5`` carries its own operands. The host reads the string and computes.

``successor^2(alpha)`` does not. ``successor`` is not arithmetic the host knows;
it is a set of rewrite rules, and a *different* successor gives a different
answer. So the row must say which presentation it means, and it does so by
**name**: the packet declares ``presentation_ref``, and the host resolves that
name against its own pins. The producer names; the host supplies the content.
There is no packet field that can carry rules.

``period(c5)`` is in between: it names its subject *inside the statement*, so it
needs no ``presentation_ref`` at all -- but the name still resolves against the
host's pins, never against anything the packet supplied.

The shortcut that was rejected: "we only pin one presentation, so use that one".
It works today and it is the failure this module exists to prevent -- the host
would decide a row against whatever it happened to pin and report ``REDERIVED``,
having **guessed the subject** of the sentence it claims to have verified. That
is strictly worse than ``UNCHECKABLE``, and it breaks silently the day a second
presentation is pinned: no error, just a wrong answer.

Three outcomes, and the middle one is the point
-----------------------------------------------

* The statement parses and the host agrees -> ``REDERIVED``.
* The statement parses and the host gets a **different** answer ->
  ``CONTRADICTED``. This is the outcome that makes
  :attr:`~.calculus_receipt.ReceiptRow.is_hallucination` reachable at all: until
  now nothing could ever contradict a producer, so the hallucination count was
  structurally always zero and read as a clean bill of health.
* The statement is not in a form this host decides -> ``UNCHECKABLE``, naming
  the blind spot.

On the sign convention, which is a cross-language hazard
--------------------------------------------------------

``mod`` here is the **least non-negative residue**, so ``-17 mod 5 = 3``.

That is what a cyclic group of order *n* means by it, and it is what Python's
``%`` computes. It is **not** what Rust, C, C++, Java or Go compute: those
truncate toward zero and give ``-2``. The Rust host in this estate is one
`%` away from disagreeing with this module about a row it re-derived, and the
disagreement would appear as a `CONTRADICTED` row rather than as an error.

This is the same shape as the canonical-JSON hazard `RoundRecord::seal` already
carries a comment about: two languages computing "the same" function differently
across a seam. It is pinned by a test here rather than left to be discovered.

Why ``mod`` is matched case-insensitively, when ops are not
-----------------------------------------------------------

The op linter is deliberately case-sensitive: ops are pinned tokens naming the
evidence class, and matching a closed set loosely silently makes it a larger
set. ``mod`` is the opposite polarity. Loosening it does not admit anything as
valid -- it admits more statements to be **checked**. Refusing to recognise
``17 MOD 5 = 99`` would file it as ``UNCHECKABLE`` and let a false claim escape
the hallucination count on a capitalisation. The safe direction for a decider is
to decide more, and for an allowlist to admit less.

AuthorityEffect: None. ``REDERIVED`` says this host recomputed the row and
agrees. It is not a promotion and it says nothing about any other row.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

from .calculus_receipt import RowOutcome
from .glyph_calculus import REFUSAL_STATEMENT_ILL_FORMED, Carrier
from .presentation_pins import PinnedPresentation, PresentationPins

__all__ = [
    "BLIND_SPOT_NOT_A_PERMUTATION",
    "BLIND_SPOT_NO_CARRIER",
    "BLIND_SPOT_NO_DECIDER",
    "BLIND_SPOT_OPERAND_TOO_LONG",
    "BLIND_SPOT_PRESENTATION_REF",
    "BLIND_SPOT_PRESENTATION_UNPINNED",
    "BLIND_SPOT_SYMBOL_IN_SIGNATURE",
    "DeciderContext",
    "Derivation",
    "rederive_statement",
    "split_row",
    "statement_body",
]

#: Named blind spot: the host has no decider for this statement's form. The
#: point of naming it is that "we did not check that" and "we cannot know what
#: we did not check" are different, and only the first is auditable.
BLIND_SPOT_NO_DECIDER = "host_decidable_form"

#: Named blind spot: the operand is longer than this interpreter will convert.
#: CPython caps int(str) at `sys.int_info.str_digits_check_threshold` (4300 by
#: default) precisely so a producer cannot hand a host quadratic parse work.
#: Hitting it is a resource bound, not a claim about the arithmetic.
BLIND_SPOT_OPERAND_TOO_LONG = "operand_within_interpreter_int_limit"

#: Named blind spot: the row is about a presentation, and the packet did not
#: say which. The host will not guess, so it declines.
BLIND_SPOT_PRESENTATION_REF = "packet_presentation_ref"

#: Named blind spot: the packet named a presentation this host does not pin.
#: A statement about THIS host, not about the name -- the row may be about
#: something perfectly legitimate that this estate simply does not pin.
BLIND_SPOT_PRESENTATION_UNPINNED = "presentation_pinned_by_this_host"

#: Named blind spot: the presentation's rules are not a permutation of its
#: signature, so it has no `successor` in the sense `successor^k(x)` means and
#: no period.
BLIND_SPOT_NOT_A_PERMUTATION = "presentation_is_a_permutation"

#: Named blind spot: the statement names carrier symbols and no carrier was
#: supplied to resolve them against, or a name it uses is not one the carrier
#: declares.
BLIND_SPOT_NO_CARRIER = "carrier_to_resolve_symbol_names"

#: Named blind spot: the symbol is a declared carrier member, and the pinned
#: presentation's signature does not cover it.
#:
#: Distinct from BLIND_SPOT_NOT_A_PERMUTATION on purpose. The carrier and the
#: presentation are INDEPENDENT pins, so a carrier may legitimately declare a
#: glyph the presentation says nothing about. Reporting that as "the rules are
#: not a permutation" is a false statement about the pinned presentation, in a
#: receipt, which is the one thing a receipt may not contain.
BLIND_SPOT_SYMBOL_IN_SIGNATURE = "symbol_within_presentation_signature"

#: `17 mod 5 = 2`, with optional signs and free whitespace. Anchored at both
#: ends: a statement with anything else in it is a different statement, and
#: this host does not decide it.
_MODULAR = re.compile(
    r"^(?P<lhs>[+-]?\d+)\s*mod\s*(?P<modulus>[+-]?\d+)\s*=\s*(?P<claimed>[+-]?\d+)$",
    re.IGNORECASE,
)

#: `period(c5) = 5`. The name is an identifier, not a term: it is a key into the
#: host's pin registry.
_PERIOD = re.compile(
    r"^period\s*\(\s*(?P<name>[A-Za-z0-9_.\-]+)\s*\)\s*=\s*(?P<claimed>\d+)$",
    re.IGNORECASE,
)

#: `successor^2(alpha) = gamma`, and `successor(alpha) = beta` for k = 1.
_SUCCESSOR = re.compile(
    r"^successor\s*(?:\^\s*(?P<times>\d+)\s*)?"
    r"\(\s*(?P<arg>[^)\s]+)\s*\)\s*=\s*(?P<claimed>\S+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class Derivation:
    """What the host established about one statement, and nothing more."""

    outcome: RowOutcome
    #: The value the host computed, when it computed one. Recorded for
    #: CONTRADICTED as well as REDERIVED: a reader must be able to see what the
    #: host held, not merely that it disagreed.
    host_value: str | None = None
    #: Fields or capabilities the row did not supply. Populated only for
    #: UNCHECKABLE.
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    #: Why the row was refused. Populated only for REFUSED.
    refusal_code: str | None = None
    #: A human-readable reason, for a finding or a log. Never load-bearing.
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class DeciderContext:
    """Everything a decider may consult, and every part of it host-side.

    Deliberately NOT a bag the packet fills. The carrier is whatever
    `verify_glyph_reply` settled on -- which is the host's own when one was
    supplied. `presentation` is already **resolved**: the packet contributed a
    name, and the lookup happened against `pins` before this object existed, so
    a decider cannot be handed rules a producer wrote.

    Empty is the honest default. A decider that needs something absent reports
    `UNCHECKABLE` and names what was missing.
    """

    carrier: Carrier | None = None
    #: The presentation the packet's `presentation_ref` named, if this host
    #: pins one under that name.
    presentation: PinnedPresentation | None = None
    #: The name the packet asked for, recorded even when it resolved to
    #: nothing, so a blind spot can say WHICH name went unfound.
    presentation_ref: str | None = None
    #: Every presentation this host pins. Consulted by forms that name their
    #: own subject, like `period(c5)`.
    pins: PresentationPins = field(default_factory=PresentationPins.empty)


def split_row(sentence: str) -> tuple[str, str]:
    """A row's op and the statement after it, from ONE split.

    `op: REDUCE x`, `op REDUCE x` and a bare `REDUCE x` all appear in the
    corpus, so the op may be the first or the second token. Both halves come out
    of a single pass on purpose: the receipt records the op and the decider is
    handed the body, and if those were computed by two separate parses they
    could disagree about where the boundary is. Counting the `op:` prefix twice
    is a bug this codebase has already shipped once.

    The op is returned exactly as written, minus a trailing colon; it is not
    upper-cased or otherwise repaired, because rendering an unrecognised op as
    something recognised would be a second forgery on top of the first.
    """
    tokens = sentence.strip().split()
    if not tokens:
        return "", ""
    start = 1 if tokens[0].rstrip(":").upper() == "OP" else 0
    op = tokens[start].rstrip(":") if start < len(tokens) else ""
    return op, " ".join(tokens[start + 1 :])


def statement_body(sentence: str) -> str:
    """Just the statement half of :func:`split_row`."""
    return split_row(sentence)[1]


def _symbol_name(carrier: Carrier, glyph: str) -> str:
    """The carrier's declared name for a glyph, or its codepoint label.

    Never the raw glyph. Findings are printed on cp1252 consoles, where
    emitting a Greek letter turns a receipt into a `UnicodeEncodeError`.
    """
    for member in carrier.members:
        if member.char == glyph:
            return member.symbol
    return f"U+{ord(glyph):04X}"


def _resolve_symbol(carrier: Carrier, token: str) -> str | None:
    """A carrier glyph, from either its declared NAME or the glyph itself.

    The corpus writes `successor^2(alpha) = gamma` -- names, not glyphs -- and
    a packet may reasonably write either. Both resolve; anything else does not.

    Matched EXACTLY, unlike the `mod` keyword which is matched
    case-insensitively. The difference is not inconsistency: `mod` is a fixed
    operator word, so loosening it only admits more statements to be checked.
    A symbol name is DECLARED BY THE CARRIER, and a carrier is free to declare
    `alpha` and `Alpha` as two different members -- folding them would make the
    host answer about a symbol the row did not name.
    """
    for member in carrier.members:
        if member.symbol == token:
            return member.char
    if len(token) == 1 and token in carrier.glyphs:
        return token
    return None


def _decide_period(body: str, context: DeciderContext) -> Derivation | None:
    """`period(NAME) = n` against the presentation pinned under NAME."""
    match = _PERIOD.match(body)
    if match is None:
        return None

    name = match["name"]
    presentation = context.pins.resolve(name)
    if presentation is None:
        return Derivation(
            RowOutcome.UNCHECKABLE,
            missing_fields=(BLIND_SPOT_PRESENTATION_UNPINNED,),
            detail=(
                f"this host pins no presentation named {name!r}; it pins "
                f"{list(context.pins.names)}"
            ),
        )

    period = presentation.period
    if period is None:
        return Derivation(
            RowOutcome.UNCHECKABLE,
            missing_fields=(BLIND_SPOT_NOT_A_PERMUTATION,),
            detail=(
                f"the rules of {name!r} are not a permutation of its signature, "
                "so it has no period"
            ),
        )

    try:
        claimed = int(match["claimed"])
    except ValueError:
        return Derivation(
            RowOutcome.UNCHECKABLE,
            missing_fields=(BLIND_SPOT_OPERAND_TOO_LONG,),
            detail="the claimed period exceeds this interpreter's int(str) limit",
        )

    if claimed == period:
        return Derivation(RowOutcome.REDERIVED, host_value=str(period))
    return Derivation(
        RowOutcome.CONTRADICTED,
        host_value=str(period),
        detail=(
            f"the row claims the period of {name!r} is {claimed}; this host "
            f"computes {period} as the order of its successor permutation"
        ),
    )


def _decide_successor(body: str, context: DeciderContext) -> Derivation | None:
    """`successor^k(X) = Y` under the presentation the packet named."""
    match = _SUCCESSOR.match(body)
    if match is None:
        return None

    if context.presentation is None:
        missing = (
            BLIND_SPOT_PRESENTATION_UNPINNED
            if context.presentation_ref
            else BLIND_SPOT_PRESENTATION_REF
        )
        detail = (
            f"the packet named presentation {context.presentation_ref!r}, which "
            "this host does not pin"
            if context.presentation_ref
            else (
                "`successor` is defined by a presentation and the packet named "
                "none; the host will not guess which one the row means"
            )
        )
        return Derivation(RowOutcome.UNCHECKABLE, missing_fields=(missing,), detail=detail)

    if context.carrier is None:
        return Derivation(
            RowOutcome.UNCHECKABLE,
            missing_fields=(BLIND_SPOT_NO_CARRIER,),
            detail="the statement names carrier symbols and no carrier was supplied",
        )

    try:
        times = int(match["times"]) if match["times"] else 1
    except ValueError:
        return Derivation(
            RowOutcome.UNCHECKABLE,
            missing_fields=(BLIND_SPOT_OPERAND_TOO_LONG,),
            detail="the exponent exceeds this interpreter's int(str) digit limit",
        )

    start = _resolve_symbol(context.carrier, match["arg"])
    if start is None:
        return Derivation(
            RowOutcome.UNCHECKABLE,
            missing_fields=(BLIND_SPOT_NO_CARRIER,),
            detail=f"{match['arg']!r} is not a declared carrier symbol",
        )

    # `apply_successor` returns None for two different reasons, and they are
    # different findings: the rules are not a permutation, or this symbol is
    # outside the presentation's signature. Attributing both to the first put a
    # false claim about the pinned presentation into a receipt.
    if context.presentation.successor_map is None:
        return Derivation(
            RowOutcome.UNCHECKABLE,
            missing_fields=(BLIND_SPOT_NOT_A_PERMUTATION,),
            detail=(
                f"the rules of {context.presentation.name!r} are not a permutation "
                "of its signature, so `successor` is not defined on it"
            ),
        )

    landed = context.presentation.apply_successor(start, times)
    if landed is None:
        return Derivation(
            RowOutcome.UNCHECKABLE,
            missing_fields=(BLIND_SPOT_SYMBOL_IN_SIGNATURE,),
            detail=(
                f"{match['arg']!r} is a declared carrier member and "
                f"{context.presentation.name!r} says nothing about it; the "
                "carrier and the presentation are independent pins"
            ),
        )

    host_value = _symbol_name(context.carrier, landed)
    claimed = _resolve_symbol(context.carrier, match["claimed"])
    if claimed is None:
        # Symmetric with the `start` path above, and it was not. A token the
        # carrier does not declare -- a typo like `gama` -- fell through to the
        # equality test and was recorded as CONTRADICTED, which this module's
        # own doctrine calls a hallucination charge against the producer. The
        # host cannot compare against a symbol it cannot resolve.
        return Derivation(
            RowOutcome.UNCHECKABLE,
            missing_fields=(BLIND_SPOT_NO_CARRIER,),
            detail=(
                f"{match['claimed']!r} is not a declared carrier symbol, so the "
                "host has nothing to compare its own answer against"
            ),
        )
    if claimed == landed:
        return Derivation(RowOutcome.REDERIVED, host_value=host_value)
    return Derivation(
        RowOutcome.CONTRADICTED,
        host_value=host_value,
        detail=(
            f"the row claims {match['claimed']!r}; under {context.presentation.name!r} "
            f"this host lands on {host_value}"
        ),
    )


def _decide_modular(body: str, context: DeciderContext) -> Derivation | None:
    """`a mod n = c` over the integers, or `None` if this is not that form."""
    match = _MODULAR.match(body)
    if match is None:
        return None

    try:
        lhs = int(match["lhs"])
        modulus = int(match["modulus"])
        claimed = int(match["claimed"])
    except ValueError:
        # CPython refuses to convert a very long digit string at all. That is a
        # resource bound on this interpreter, not a finding about the claim, so
        # it is a named blind spot rather than a contradiction.
        return Derivation(
            RowOutcome.UNCHECKABLE,
            missing_fields=(BLIND_SPOT_OPERAND_TOO_LONG,),
            detail="an operand exceeds this interpreter's int(str) digit limit",
        )

    if modulus <= 0:
        # `a mod 0` has no value, and a negative modulus is not a cyclic group
        # order. The claim is therefore neither true nor false, so it is not a
        # contradiction -- the host declines to admit the row. Checking this
        # before dividing also keeps a ZeroDivisionError out of the use case: a
        # crash is not a terminal.
        return Derivation(
            RowOutcome.REFUSED,
            refusal_code=REFUSAL_STATEMENT_ILL_FORMED,
            detail=(
                f"modulus {modulus} is not positive, so {match['lhs']} mod "
                f"{modulus} names no value; a claim with no truth value is "
                "refused rather than contradicted"
            ),
        )

    host_value = lhs % modulus
    if host_value == claimed:
        return Derivation(RowOutcome.REDERIVED, host_value=str(host_value))
    return Derivation(
        RowOutcome.CONTRADICTED,
        host_value=str(host_value),
        detail=(
            f"the row claims {claimed} and this host computes {host_value} "
            f"({lhs} mod {modulus}, least non-negative residue)"
        ),
    )


#: Every decider, tried in order. Each returns `None` for a form it does not
#: own, so adding one is additive and cannot change another's answer.
_DECIDERS: tuple[Callable[[str, DeciderContext], Derivation | None], ...] = (
    _decide_modular,
    _decide_period,
    _decide_successor,
)


def rederive_statement(
    sentence: str, context: DeciderContext | None = None
) -> Derivation:
    """Re-derive what this host can, and name the blind spot when it cannot.

    Keyed on the statement's FORM, not on the row's op. The op is the evidence
    class the producer claimed; what the host can compute does not depend on
    what the producer called it, and a host that only checked rows whose op it
    liked would be checking less for no reason.

    `context` carries host-side material -- the carrier, the resolved
    presentation, the pin registry. It defaults to empty, and an empty context
    is not an error: forms needing something absent report `UNCHECKABLE` and
    name what was missing, which is the same answer they give for a form no
    decider owns.
    """
    context = context or DeciderContext()
    body = statement_body(sentence)
    for decider in _DECIDERS:
        derivation = decider(body, context)
        if derivation is not None:
            return derivation
    return Derivation(
        RowOutcome.UNCHECKABLE,
        missing_fields=(BLIND_SPOT_NO_DECIDER,),
        detail="no decider in this host recognises this statement's form",
    )
