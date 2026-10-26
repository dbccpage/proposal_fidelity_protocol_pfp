"""The rewrite presentations this host recognises, and what it can compute.

Why this exists
---------------

`REDUCE 17 mod 5 = 2` carries its own operands: the host reads the string and
computes. `LAND successor^2(alpha) = gamma` does not. `successor` is not
arithmetic the host knows -- it is a set of rewrite rules, and a *different*
`successor` gives a different answer. So a decider for that form needs to know
**which** presentation the row is about, and it must learn that from somewhere
the producer cannot forge.

The channel is a name. The packet says ``presentation_ref: "c5"``; the host
looks that name up **in its own pin set** and supplies the rules. The producer
*names*, the host *resolves*. This is the same shape as ``--carrier``: naming a
pin is not the same as supplying its content, and there is no packet field that
can carry rules.

What was rejected, and why
--------------------------

The shortcut is "we only pin one presentation, so use that one". It works today
and it is the failure this module exists to prevent: the host would decide a row
against whatever it happened to pin and report ``REDERIVED``, having *guessed
the subject* of the sentence it claims to have verified. That is strictly worse
than ``UNCHECKABLE``, which is at least honest -- and it breaks silently the day
a second presentation is pinned, with no error, just a wrong answer.

A name the host does not pin is therefore ``UNCHECKABLE`` with the blind spot
named, never a refusal. The row may be about something perfectly legitimate that
this estate simply does not pin.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import gcd

__all__ = [
    "PinnedPresentation",
    "PinnedRule",
    "PresentationPins",
]


@dataclass(frozen=True, slots=True)
class PinnedRule:
    """One oriented rewrite rule, as the governance pin file declares it."""

    name: str
    lhs: str
    rhs: str


@dataclass(frozen=True, slots=True)
class PinnedPresentation:
    """A finite rewrite presentation the host recognises, under a name.

    The name is the lookup key and is part of the wire contract: it is what a
    row's ``presentation_ref`` and what ``period(NAME)`` resolve against.
    """

    name: str
    signature: tuple[str, ...]
    rules: tuple[PinnedRule, ...]

    @property
    def successor_map(self) -> dict[str, str] | None:
        """The rules as a permutation of the signature, or `None`.

        Only a presentation whose rules form a **total permutation** of its own
        signature has a `successor` in the sense `successor^k(x)` means, and only
        such a presentation has a period. Everything else returns `None` and the
        deciders that need one report `UNCHECKABLE` rather than guessing.

        Four ways to fail, each checked rather than assumed:

        * a rule whose left- or right-hand side is not exactly one symbol -- a
          rewriting system in general is not a map on symbols;
        * two rules sharing a left-hand side, so the relation is not a function;
        * a signature symbol with no rule, so it is not total;
        * right-hand sides that are not a permutation of the signature, so it
          does not cycle and `successor^k` need never return.
        """
        symbols = set(self.signature)
        if not symbols or len(symbols) != len(self.signature):
            # A signature that repeats a symbol is ambiguous about its own size,
            # and the size is what `period` reports.
            return None

        mapping: dict[str, str] = {}
        for rule in self.rules:
            if len(rule.lhs) != 1 or len(rule.rhs) != 1:
                return None
            if rule.lhs in mapping:
                return None
            if rule.lhs not in symbols or rule.rhs not in symbols:
                return None
            mapping[rule.lhs] = rule.rhs

        # Totality. Provably REDUNDANT given the onto check below -- keys are
        # distinct and drawn from the signature, so |keys| <= |symbols|, while
        # `set(values) == symbols` forces |keys| >= |symbols|. Mutation M21
        # removes this line and is recorded as an EQUIVALENT mutant rather than
        # chased; `test_the_totality_check_is_redundant_given_the_onto_check`
        # pins the claim so that weakening the onto check makes this line
        # load-bearing again, and M21 stops being equivalent.
        #
        # Kept because it states the intent directly. A reader should not have
        # to reconstruct the counting argument to see that the map is total.
        if set(mapping) != symbols:
            return None
        if set(mapping.values()) != symbols:
            return None
        return mapping

    def cycle_containing(self, symbol: str) -> tuple[str, ...] | None:
        """The orbit of `symbol` under the successor map, in order."""
        mapping = self.successor_map
        if mapping is None or symbol not in mapping:
            return None
        orbit = [symbol]
        current = mapping[symbol]
        while current != symbol:
            orbit.append(current)
            current = mapping[current]
        return tuple(orbit)

    def apply_successor(self, symbol: str, times: int) -> str | None:
        """`successor^times(symbol)`, exactly, for any non-negative `times`.

        Computed by indexing into the orbit rather than by iterating, so a row
        claiming `successor^999999999(alpha)` costs the length of one cycle
        instead of a billion steps. A producer chooses that exponent, so
        iterating would hand it a lever on the host's running time.
        """
        if times < 0:
            return None
        orbit = self.cycle_containing(symbol)
        if orbit is None:
            return None
        return orbit[times % len(orbit)]

    @property
    def period(self) -> int | None:
        """The order of the successor permutation.

        The least `k > 0` with `successor^k = identity`, which is the lowest
        common multiple of the cycle lengths -- **not** the size of the
        signature. Those coincide for a single cycle like `c5` and diverge the
        moment a presentation has two orbits, so reporting `len(signature)`
        would be right for the one pin we have and wrong in general.
        """
        mapping = self.successor_map
        if mapping is None:
            return None
        seen: set[str] = set()
        order = 1
        for symbol in self.signature:
            if symbol in seen:
                continue
            orbit = self.cycle_containing(symbol)
            if orbit is None:
                return None
            seen.update(orbit)
            order = order * len(orbit) // gcd(order, len(orbit))
        return order


@dataclass(frozen=True, slots=True)
class PresentationPins:
    """Every presentation this host recognises, by name.

    Built from the governance pin file by a caller in the entrypoint layer.
    Nothing here reads a file, and nothing here accepts a presentation from a
    packet: a pin set the producer can extend is not a pin set.
    """

    by_name: Mapping[str, PinnedPresentation]

    @classmethod
    def empty(cls) -> "PresentationPins":
        return cls({})

    @classmethod
    def from_wire(cls, pins: Iterable[object]) -> "PresentationPins":
        """Parse the `pins` array of the governance file, strictly.

        Unknown fields are refused rather than ignored, for the same reason the
        packet surface refuses them: an ignored field is one a reader believes
        is load-bearing while it is inert.
        """
        by_name: dict[str, PinnedPresentation] = {}
        for entry in pins:
            if not isinstance(entry, dict):
                raise ValueError("each pin must be a mapping")
            unknown = sorted(set(entry) - {"name", "note", "presentation"})
            if unknown:
                raise ValueError(f"pin has undeclared fields {unknown}")
            name = str(entry.get("name", ""))
            if not name:
                raise ValueError("a pin declares a non-empty name")
            if name in by_name:
                raise ValueError(f"pin name {name!r} is declared twice")
            body = entry.get("presentation")
            if not isinstance(body, dict):
                raise ValueError(f"pin {name!r} declares no presentation")
            unknown = sorted(set(body) - {"signature", "rules"})
            if unknown:
                raise ValueError(
                    f"pin {name!r} presentation has undeclared fields {unknown}"
                )
            # Every failure here must be a ValueError. The CLI loader catches
            # exactly that and turns it into a REFUSE receipt with exit 2; a
            # KeyError or TypeError escapes as a traceback and exit 1, which
            # breaks the contract that a pin file the host cannot read is still
            # answered with a receipt. Direct indexing and a bare comprehension
            # were the two ways that happened.
            raw_signature = body.get("signature", ())
            if not isinstance(raw_signature, (list, tuple)):
                raise ValueError(
                    f"pin {name!r} declares a non-list signature "
                    f"({type(raw_signature).__name__})"
                )
            signature = tuple(str(s) for s in raw_signature)
            raw_rules = body.get("rules", ())
            if not isinstance(raw_rules, (list, tuple)):
                raise ValueError(
                    f"pin {name!r} declares a non-list rules "
                    f"({type(raw_rules).__name__})"
                )
            rules: list[PinnedRule] = []
            for raw in raw_rules:
                if not isinstance(raw, dict):
                    raise ValueError(f"pin {name!r} has a non-mapping rule")
                unknown = sorted(set(raw) - {"name", "lhs", "rhs"})
                if unknown:
                    raise ValueError(f"pin {name!r} rule has undeclared fields {unknown}")
                missing = sorted({"name", "lhs", "rhs"} - set(raw))
                if missing:
                    raise ValueError(f"pin {name!r} rule is missing {missing}")
                rules.append(
                    PinnedRule(str(raw["name"]), str(raw["lhs"]), str(raw["rhs"]))
                )
            by_name[name] = PinnedPresentation(name, signature, tuple(rules))
        return cls(by_name)

    def resolve(self, name: str) -> PinnedPresentation | None:
        """The presentation pinned under `name`, or `None`.

        `None` is a statement about this HOST, not about the name: it means we
        pin nothing by it, so a decider must decline rather than guess.
        """
        return self.by_name.get(name)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self.by_name))

    def __bool__(self) -> bool:
        return bool(self.by_name)
