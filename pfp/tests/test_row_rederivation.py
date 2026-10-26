"""The one form this host decides, and everything it deliberately does not.

A decider is a claim that the host KNOWS the answer, so these tests are mostly
about the boundary: what it refuses to decide, what it refuses to admit, and
what it must not mistake for either.
"""

from __future__ import annotations

import pytest

from omega_engine_pfp.domain.calculus_receipt import RowOutcome
from omega_engine_pfp.domain.glyph_calculus import (
    REFUSAL_STATEMENT_ILL_FORMED,
)
from omega_engine_pfp.domain.glyph_calculus import Carrier
from omega_engine_pfp.domain.presentation_pins import (
    PinnedPresentation,
    PinnedRule,
    PresentationPins,
)
from omega_engine_pfp.domain.row_rederivation import (
    BLIND_SPOT_NOT_A_PERMUTATION,
    BLIND_SPOT_NO_CARRIER,
    BLIND_SPOT_NO_DECIDER,
    BLIND_SPOT_OPERAND_TOO_LONG,
    BLIND_SPOT_PRESENTATION_REF,
    BLIND_SPOT_PRESENTATION_UNPINNED,
    BLIND_SPOT_SYMBOL_IN_SIGNATURE,
    DeciderContext,
    rederive_statement,
    split_row,
    statement_body,
)

CARRIER_WIRE = [
    {"symbol": "alpha", "codepoint": "U+03B1"},
    {"symbol": "beta", "codepoint": "U+03B2"},
    {"symbol": "gamma", "codepoint": "U+03B3"},
    {"symbol": "delta", "codepoint": "U+03B4"},
    {"symbol": "epsilon", "codepoint": "U+03B5"},
]
GLYPHS = tuple(chr(0x03B1 + offset) for offset in range(5))


def c5() -> PinnedPresentation:
    return PinnedPresentation(
        "c5",
        GLYPHS,
        tuple(
            PinnedRule(f"succ_{index}", glyph, GLYPHS[(index + 1) % 5])
            for index, glyph in enumerate(GLYPHS)
        ),
    )


def host(*, ref: str | None = "c5", carrier: bool = True) -> DeciderContext:
    """A context with the c5 pin, as `verify_glyph_reply` would build it."""
    pins = PresentationPins({"c5": c5()})
    return DeciderContext(
        carrier=Carrier.from_wire(CARRIER_WIRE) if carrier else None,
        presentation=pins.resolve(ref) if ref else None,
        presentation_ref=ref,
        pins=pins,
    )


class TestTheRowSplit:
    @pytest.mark.parametrize(
        "sentence",
        ["REDUCE 17 mod 5 = 2", "op REDUCE 17 mod 5 = 2", "op: REDUCE 17 mod 5 = 2"],
    )
    def test_every_prefix_form_yields_the_same_op_and_body(
        self, sentence: str
    ) -> None:
        assert split_row(sentence) == ("REDUCE", "17 mod 5 = 2")

    def test_the_op_is_recorded_as_written(self) -> None:
        # Not upper-cased or repaired: rendering an unrecognised op as
        # something recognised would be a second forgery on top of the first.
        assert split_row("qed x")[0] == "qed"

    def test_repeated_whitespace_does_not_move_the_boundary(self) -> None:
        # An earlier draft of this reconstructed the body by string length,
        # which silently mis-split any row with a double space.
        assert split_row("op:   REDUCE   17 mod 5 = 2") == ("REDUCE", "17 mod 5 = 2")

    def test_an_empty_row_splits_into_nothing(self) -> None:
        assert split_row("   ") == ("", "")
        assert statement_body("") == ""

    def test_a_row_that_is_only_an_op_has_an_empty_body(self) -> None:
        assert split_row("op: LAND") == ("LAND", "")


class TestModularReduction:
    def test_the_contracts_own_worked_example_rederives(self) -> None:
        derivation = rederive_statement("REDUCE 17 mod 5 = 2")
        assert derivation.outcome is RowOutcome.REDERIVED
        assert derivation.host_value == "2"

    def test_a_wrong_value_is_contradicted_not_uncheckable(self) -> None:
        """The outcome the whole receipt exists to be able to reach.

        Until a decider existed, nothing could ever contradict a producer, so
        `hallucinations` was structurally always empty -- and an always-zero
        count reads as a clean bill of health rather than as an unasked
        question.
        """
        derivation = rederive_statement("REDUCE 17 mod 5 = 3")
        assert derivation.outcome is RowOutcome.CONTRADICTED
        assert derivation.host_value == "2", (
            "a reader must see what the host held, not merely that it disagreed"
        )

    def test_the_op_does_not_decide_what_is_decidable(self) -> None:
        # Keyed on the statement's form. What the host can compute does not
        # depend on what the producer called it.
        assert rederive_statement("PROVE 17 mod 5 = 2").outcome is RowOutcome.REDERIVED
        assert rederive_statement("SHOW 17 mod 5 = 9").outcome is (
            RowOutcome.CONTRADICTED
        )

    @pytest.mark.parametrize(
        ("statement", "expected"),
        [
            ("REDUCE 0 mod 5 = 0", "0"),
            ("REDUCE 5 mod 5 = 0", "0"),
            ("REDUCE 4 mod 5 = 4", "4"),
            ("REDUCE +17 mod 5 = 2", "2"),
            # 10 has order 6 mod 7 and 30 == 0 (mod 6), so this is 1.
            # The first draft of this fixture said 6, and the decider
            # caught it -- which is the whole point of having one.
            ("REDUCE 1000000000000000000000000000000 mod 7 = 1", "1"),
        ],
    )
    def test_ordinary_cases(self, statement: str, expected: str) -> None:
        derivation = rederive_statement(statement)
        assert derivation.outcome is RowOutcome.REDERIVED
        assert derivation.host_value == expected


class TestTheSignConvention:
    """`mod` is the least non-negative residue. This is a seam hazard.

    Python's `%` gives 3 for `-17 mod 5`. Rust, C, C++, Java and Go truncate
    toward zero and give -2. The Rust host in this estate is one `%` away from
    disagreeing with this module about a row it re-derived, and the
    disagreement would surface as a CONTRADICTED row rather than as an error --
    the producer blamed for a difference between two hosts.
    """

    def test_a_negative_operand_reduces_to_the_least_non_negative_residue(
        self,
    ) -> None:
        derivation = rederive_statement("REDUCE -17 mod 5 = 3")
        assert derivation.outcome is RowOutcome.REDERIVED
        assert derivation.host_value == "3"

    def test_the_truncating_convention_is_refused(self) -> None:
        # -2 is what a C-family `%` returns. It is a real answer to a different
        # question, and this host must not accept it as an answer to this one.
        derivation = rederive_statement("REDUCE -17 mod 5 = -2")
        assert derivation.outcome is RowOutcome.CONTRADICTED
        assert derivation.host_value == "3"

    def test_the_residue_is_always_in_range(self) -> None:
        for lhs in range(-12, 13):
            derivation = rederive_statement(f"REDUCE {lhs} mod 5 = {lhs % 5}")
            assert derivation.outcome is RowOutcome.REDERIVED
            assert 0 <= int(derivation.host_value or "-1") < 5


class TestWhatIsRefusedRatherThanContradicted:
    @pytest.mark.parametrize("modulus", ["0", "-5"])
    def test_a_non_positive_modulus_is_refused(self, modulus: str) -> None:
        """A claim with no truth value cannot be false.

        `17 mod 0` names no value, and a negative modulus is not a cyclic group
        order. Reporting either as CONTRADICTED would say the host holds a
        different answer, and it holds none.
        """
        derivation = rederive_statement(f"REDUCE 17 mod {modulus} = 2")
        assert derivation.outcome is RowOutcome.REFUSED
        assert derivation.refusal_code == REFUSAL_STATEMENT_ILL_FORMED
        assert derivation.host_value is None

    def test_a_zero_modulus_does_not_raise(self) -> None:
        # `17 % 0` is a ZeroDivisionError. A crash is not a terminal, so the
        # guard is checked before the division rather than caught after it.
        assert rederive_statement("REDUCE 17 mod 0 = 2") is not None

    def test_a_refusal_is_not_a_hallucination_charge(self) -> None:
        # Refusal means the host declined to admit the row, not that the
        # producer said something untrue.
        assert rederive_statement("REDUCE 1 mod 0 = 0").outcome is RowOutcome.REFUSED


class TestTheBlindSpotIsNamed:
    @pytest.mark.parametrize(
        "statement",
        [
            # `period(...)` and `successor^k(...)` USED to live here. They are
            # decided now, and their blind spots are named for the specific
            # thing that was missing rather than "no decider" -- see
            # TestPeriod and TestSuccessor.
            "LAND gamma",
            "SHOW the carrier has five members",
            "REDUCE 17 mod 5",
            "REDUCE 17 mod 5 = two",
            "REDUCE 17 mod 5 = 2 and also 3",
            "REDUCE 1.5 mod 5 = 2",
        ],
    )
    def test_a_form_this_host_does_not_decide_is_uncheckable(
        self, statement: str
    ) -> None:
        derivation = rederive_statement(statement)
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_NO_DECIDER,)
        assert derivation.host_value is None

    def test_the_pattern_is_anchored_at_both_ends(self) -> None:
        # Without anchoring, "REDUCE 17 mod 5 = 2 and pigs fly" would rederive
        # clean and the trailing claim would ride out on it.
        assert (
            rederive_statement("REDUCE 17 mod 5 = 2 and pigs fly").outcome
            is RowOutcome.UNCHECKABLE
        )

    def test_an_operand_beyond_the_interpreter_limit_is_a_named_bound(self) -> None:
        # CPython refuses int(str) past ~4300 digits so a producer cannot hand a
        # host quadratic parse work. That is a resource bound on us, not a
        # finding about the claim, so it must not read as a contradiction.
        huge = "9" * 5000
        derivation = rederive_statement(f"REDUCE {huge} mod 7 = 1")
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_OPERAND_TOO_LONG,)

    def test_the_two_blind_spots_are_distinguishable(self) -> None:
        # "we have no decider for this" and "we could not parse this number"
        # are different admissions and a reader must be able to tell them apart.
        assert BLIND_SPOT_NO_DECIDER != BLIND_SPOT_OPERAND_TOO_LONG


class TestCaseHandling:
    @pytest.mark.parametrize("word", ["mod", "MOD", "Mod", "mOd"])
    def test_the_operator_word_is_matched_case_insensitively(
        self, word: str
    ) -> None:
        """The opposite polarity from the op linter, deliberately.

        Ops are pinned tokens naming the evidence class, so matching them
        loosely silently enlarges a closed set. `mod` is a form marker: matching
        it loosely admits more statements to be CHECKED. Refusing `17 MOD 5 =
        99` would file a false claim as UNCHECKABLE and let it escape the
        hallucination count on a capitalisation.
        """
        assert (
            rederive_statement(f"REDUCE 17 {word} 5 = 99").outcome
            is RowOutcome.CONTRADICTED
        )

    def test_whitespace_around_the_operator_is_free(self) -> None:
        for statement in [
            "REDUCE 17 mod 5 = 2",
            "REDUCE 17mod5=2",
            "REDUCE 17   mod   5   =   2",
        ]:
            assert rederive_statement(statement).outcome is RowOutcome.REDERIVED


class TestPeriod:
    """`period(NAME) = n`, which names its own subject inside the statement.

    No `presentation_ref` is needed: the name IS in the sentence. What the
    packet cannot do is supply the rules that name resolves to -- that lookup
    happens against the host's pins and nowhere else.
    """

    def test_the_corpus_row_rederives(self) -> None:
        derivation = rederive_statement("PROVE period(c5) = 5", host())
        assert derivation.outcome is RowOutcome.REDERIVED
        assert derivation.host_value == "5"

    def test_a_wrong_period_is_contradicted(self) -> None:
        derivation = rederive_statement("PROVE period(c5) = 7", host())
        assert derivation.outcome is RowOutcome.CONTRADICTED
        assert derivation.host_value == "5"

    def test_a_name_this_host_does_not_pin_is_a_named_blind_spot(self) -> None:
        """Not a refusal.

        The row may be about something perfectly legitimate that this estate
        simply does not pin. `UNCHECKABLE` says "I have no opinion"; refusing
        would say "you are wrong", which the host has no basis for.
        """
        derivation = rederive_statement("PROVE period(c7) = 7", host())
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_PRESENTATION_UNPINNED,)
        assert "c7" in (derivation.detail or "")

    def test_a_host_pinning_nothing_decides_nothing(self) -> None:
        derivation = rederive_statement("PROVE period(c5) = 5", DeciderContext())
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_PRESENTATION_UNPINNED,)

    def test_a_presentation_that_is_not_a_permutation_has_no_period(self) -> None:
        broken = PinnedPresentation(
            "odd", GLYPHS, (PinnedRule("a", GLYPHS[0], GLYPHS[1]),)
        )
        context = DeciderContext(pins=PresentationPins({"odd": broken}))
        derivation = rederive_statement("PROVE period(odd) = 5", context)
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_NOT_A_PERMUTATION,)

    def test_the_op_does_not_gate_the_form(self) -> None:
        assert (
            rederive_statement("SHOW period(c5) = 5", host()).outcome
            is RowOutcome.REDERIVED
        )


class TestSuccessor:
    """`successor^k(X) = Y`, which does NOT name its own subject.

    `successor` is a set of rewrite rules, and a different presentation gives a
    different answer. So this form needs the packet's `presentation_ref`, and
    without one the host declines rather than guessing.
    """

    def test_the_corpus_row_rederives(self) -> None:
        derivation = rederive_statement("LAND successor^2(alpha) = gamma", host())
        assert derivation.outcome is RowOutcome.REDERIVED
        assert derivation.host_value == "gamma"

    def test_without_a_presentation_ref_the_host_declines_to_guess(self) -> None:
        """The safety property this whole design exists for.

        With one pin on file the "obvious" shortcut is to use it. That would
        report REDERIVED having guessed the SUBJECT of the sentence, and would
        break silently the day a second presentation is pinned -- no error,
        just a wrong answer.
        """
        derivation = rederive_statement(
            "LAND successor^2(alpha) = gamma", host(ref=None)
        )
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_PRESENTATION_REF,)

    def test_an_unpinned_ref_names_a_different_blind_spot(self) -> None:
        # "you told us nothing" and "you told us something we do not pin" are
        # different admissions and a reader must be able to tell them apart.
        derivation = rederive_statement(
            "LAND successor^2(alpha) = gamma", host(ref="c7")
        )
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_PRESENTATION_UNPINNED,)
        assert BLIND_SPOT_PRESENTATION_REF != BLIND_SPOT_PRESENTATION_UNPINNED

    def test_a_wrong_landing_is_contradicted(self) -> None:
        derivation = rederive_statement("LAND successor^2(alpha) = delta", host())
        assert derivation.outcome is RowOutcome.CONTRADICTED
        assert derivation.host_value == "gamma"

    @pytest.mark.parametrize(
        ("statement", "expected"),
        [
            ("LAND successor(alpha) = beta", "beta"),
            ("LAND successor^0(alpha) = alpha", "alpha"),
            ("LAND successor^5(alpha) = alpha", "alpha"),
            ("LAND successor^7(alpha) = gamma", "gamma"),
            ("LAND successor^4(epsilon) = delta", "delta"),
        ],
    )
    def test_it_wraps_around_the_cycle(self, statement: str, expected: str) -> None:
        derivation = rederive_statement(statement, host())
        assert derivation.outcome is RowOutcome.REDERIVED
        assert derivation.host_value == expected

    def test_a_glyph_argument_resolves_as_well_as_a_name(self) -> None:
        # A packet may reasonably write either. Both are the same symbol.
        derivation = rederive_statement(
            f"LAND successor^2({GLYPHS[0]}) = {GLYPHS[2]}", host()
        )
        assert derivation.outcome is RowOutcome.REDERIVED

    def test_a_symbol_name_is_matched_exactly(self) -> None:
        """Deliberately unlike `mod`, which is case-insensitive.

        `mod` is a fixed operator word, so loosening it only admits more
        statements to be checked. A symbol name is DECLARED BY THE CARRIER, and
        a carrier is free to declare `alpha` and `Alpha` as two members --
        folding them would make the host answer about a symbol the row did not
        name.
        """
        derivation = rederive_statement("LAND successor^2(Alpha) = gamma", host())
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_NO_CARRIER,)

    def test_a_host_value_is_never_a_raw_glyph(self) -> None:
        # Receipts print on cp1252 consoles, where a Greek letter turns a
        # finding into a UnicodeEncodeError.
        derivation = rederive_statement("LAND successor^2(alpha) = delta", host())
        assert derivation.host_value == "gamma"
        (derivation.host_value or "").encode("cp1252")
        (derivation.detail or "").encode("cp1252")

    def test_without_a_carrier_symbol_names_cannot_resolve(self) -> None:
        derivation = rederive_statement(
            "LAND successor^2(alpha) = gamma", host(carrier=False)
        )
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_NO_CARRIER,)

    def test_a_huge_exponent_does_not_hang(self) -> None:
        # The producer picks the exponent. Iterating would hand it a lever on
        # the host's running time; the orbit index is exact and costs the cycle.
        derivation = rederive_statement(
            f"LAND successor^{10**18 + 2}(alpha) = gamma", host()
        )
        assert derivation.outcome is RowOutcome.REDERIVED

    def test_an_exponent_beyond_the_interpreter_limit_is_a_named_bound(self) -> None:
        derivation = rederive_statement(
            f"LAND successor^{'9' * 5000}(alpha) = gamma", host()
        )
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_OPERAND_TOO_LONG,)


class TestTheTwoCausesOfNoAnswerAreDistinguished:
    """`apply_successor` returns None for two different reasons.

    Attributing both to "the rules are not a permutation" put a FALSE claim
    about a pinned presentation into a receipt -- and a receipt is the one place
    a false claim may not appear.
    """

    def test_a_symbol_outside_the_signature_is_not_a_broken_presentation(
        self,
    ) -> None:
        # The carrier and the presentation are INDEPENDENT pins, so a carrier
        # may legitimately declare a glyph the presentation says nothing about.
        wide_carrier = Carrier.from_wire(
            [*CARRIER_WIRE, {"symbol": "zeta", "codepoint": "U+03B6"}]
        )
        pins = PresentationPins({"c5": c5()})
        context = DeciderContext(
            carrier=wide_carrier,
            presentation=pins.resolve("c5"),
            presentation_ref="c5",
            pins=pins,
        )
        derivation = rederive_statement("LAND successor(zeta) = alpha", context)
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_SYMBOL_IN_SIGNATURE,)
        assert "not a permutation" not in (derivation.detail or ""), (
            "c5 IS a permutation; saying otherwise is a false claim about a pin"
        )

    def test_a_genuinely_broken_presentation_still_says_so(self) -> None:
        # The other half: the NOT_A_PERMUTATION blind spot must still be
        # reachable, or the fix above simply deleted a finding.
        broken = PinnedPresentation(
            "odd", GLYPHS, (PinnedRule("a", GLYPHS[0], GLYPHS[1]),)
        )
        pins = PresentationPins({"odd": broken})
        context = DeciderContext(
            carrier=Carrier.from_wire(CARRIER_WIRE),
            presentation=broken,
            presentation_ref="odd",
            pins=pins,
        )
        derivation = rederive_statement("LAND successor(alpha) = beta", context)
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_NOT_A_PERMUTATION,)

    def test_an_unresolvable_claim_is_uncheckable_not_contradicted(self) -> None:
        """A typo is not a lie.

        The `start` path already returned UNCHECKABLE for a name the carrier
        does not declare; the `claimed` path fell through to the equality test
        and recorded CONTRADICTED, which this module's own doctrine calls a
        hallucination charge against the producer. Row-level carrier linting
        does not catch it either -- symbol names are ASCII and pass
        `check_ledger_text`.
        """
        derivation = rederive_statement("LAND successor^2(alpha) = gama", host())
        assert derivation.outcome is RowOutcome.UNCHECKABLE
        assert derivation.missing_fields == (BLIND_SPOT_NO_CARRIER,)
        assert "gama" in (derivation.detail or "")

    def test_a_resolvable_wrong_answer_is_still_contradicted(self) -> None:
        # Guards the fix: `delta` IS declared, so disagreeing about it is a real
        # contradiction and must not have become uncheckable.
        derivation = rederive_statement("LAND successor^2(alpha) = delta", host())
        assert derivation.outcome is RowOutcome.CONTRADICTED
        assert derivation.host_value == "gamma"
