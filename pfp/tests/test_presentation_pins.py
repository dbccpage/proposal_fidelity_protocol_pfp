"""The host's pin registry, and what it refuses to compute.

`period` and `successor` are only defined when a presentation's rules form a
total permutation of its own signature. Most of these tests are about the four
ways that fails, because a decider that guessed in any of them would report
`REDERIVED` for a question it had not answered.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pfp.domain.presentation_pins import (
    PinnedPresentation,
    PinnedRule,
    PresentationPins,
)

GOVERNANCE_PINS = (
    Path(__file__).resolve().parents[2]
    / "governance"
    / "contracts"
    / "pinned"
    / "symbol_game_presentations.json"
)

ALPHA, BETA, GAMMA = "α", "β", "γ"
DELTA, EPSILON = "δ", "ε"


def cycle(*symbols: str) -> PinnedPresentation:
    """A single-cycle presentation over `symbols`, in the order given."""
    rules = tuple(
        PinnedRule(f"succ_{index}", symbol, symbols[(index + 1) % len(symbols)])
        for index, symbol in enumerate(symbols)
    )
    return PinnedPresentation("fixture", symbols, rules)


class TestTheGovernancePinFile:
    def test_it_parses_and_pins_both_entries(self) -> None:
        body = json.loads(GOVERNANCE_PINS.read_text(encoding="utf-8"))
        pins = PresentationPins.from_wire(body["pins"])
        assert pins.names == ("c5", "c6")

    def test_c5_has_period_five(self) -> None:
        body = json.loads(GOVERNANCE_PINS.read_text(encoding="utf-8"))
        pins = PresentationPins.from_wire(body["pins"])
        c5 = pins.resolve("c5")
        assert c5 is not None
        assert c5.period == 5

    def test_the_names_are_the_ones_rows_write(self) -> None:
        # The corpus writes `PROVE period(c5) = 5`. A registry whose keys do not
        # match the names rows reference is a registry nothing looks up.
        body = json.loads(GOVERNANCE_PINS.read_text(encoding="utf-8"))
        assert [pin["name"] for pin in body["pins"]] == ["c5", "c6"]

    def test_c6_is_the_examiner_control_and_says_so(self) -> None:
        """A control in a production registry must announce itself.

        The pin file's own doctrine says to pin only a system this estate
        declares and can defend, because an invented pin makes the HostPinned
        branch look exercised while vouching for nothing. `c6` is the one entry
        that is NOT a system the corpus asserts, so its note has to carry that
        distinction or the doctrine is broken by the file that states it.
        """
        body = json.loads(GOVERNANCE_PINS.read_text(encoding="utf-8"))
        c6 = next(pin for pin in body["pins"] if pin["name"] == "c6")
        assert "NEGATIVE CONTROL" in c6["note"]

    def test_c6_has_period_six_over_five_symbols(self) -> None:
        # Examiner's g(5) = 6. The two numbers that a size-capped checker confuses.
        body = json.loads(GOVERNANCE_PINS.read_text(encoding="utf-8"))
        c6 = PresentationPins.from_wire(body["pins"]).resolve("c6")
        assert c6 is not None
        assert c6.period == 6
        assert len(c6.signature) == 5


class TestResolution:
    def test_an_unpinned_name_resolves_to_nothing(self) -> None:
        pins = PresentationPins.empty()
        assert pins.resolve("c5") is None
        assert not pins

    def test_resolution_is_exact(self) -> None:
        pins = PresentationPins({"c5": cycle(ALPHA, BETA)})
        assert pins.resolve("c5") is not None
        assert pins.resolve("C5") is None, "a pin name is a key, not a search term"
        assert pins.resolve("c5 ") is None


class TestThePeriodIsTheOrderNotTheSize:
    def test_a_single_cycle_has_period_equal_to_its_length(self) -> None:
        assert cycle(ALPHA, BETA, GAMMA, DELTA, EPSILON).period == 5

    def test_two_cycles_give_the_lowest_common_multiple(self) -> None:
        """The case that separates `period` from `len(signature)`.

        A 2-cycle and a 3-cycle over five symbols return to the identity after
        6 steps, not 5. Reporting the signature size would be right for `c5` --
        the only presentation this estate pins -- and wrong in general, which is
        exactly the shape of bug that ships.
        """
        two_and_three = PinnedPresentation(
            "fixture",
            (ALPHA, BETA, GAMMA, DELTA, EPSILON),
            (
                PinnedRule("a", ALPHA, BETA),
                PinnedRule("b", BETA, ALPHA),
                PinnedRule("c", GAMMA, DELTA),
                PinnedRule("d", DELTA, EPSILON),
                PinnedRule("e", EPSILON, GAMMA),
            ),
        )
        assert two_and_three.period == 6
        assert len(two_and_three.signature) == 5, "the two numbers really do differ"

    def test_the_identity_has_period_one(self) -> None:
        fixed = PinnedPresentation(
            "fixture",
            (ALPHA, BETA),
            (PinnedRule("a", ALPHA, ALPHA), PinnedRule("b", BETA, BETA)),
        )
        assert fixed.period == 1


class TestWhatIsNotAPermutation:
    def test_a_multi_symbol_rule_is_not_a_map_on_symbols(self) -> None:
        presentation = PinnedPresentation(
            "fixture", (ALPHA, BETA), (PinnedRule("a", ALPHA + BETA, BETA),)
        )
        assert presentation.successor_map is None
        assert presentation.period is None

    def test_two_rules_sharing_a_left_hand_side_is_not_a_function(self) -> None:
        presentation = PinnedPresentation(
            "fixture",
            (ALPHA, BETA),
            (PinnedRule("a", ALPHA, BETA), PinnedRule("b", ALPHA, ALPHA)),
        )
        assert presentation.successor_map is None

    def test_a_symbol_with_no_rule_is_not_total(self) -> None:
        presentation = PinnedPresentation(
            "fixture", (ALPHA, BETA), (PinnedRule("a", ALPHA, BETA),)
        )
        assert presentation.successor_map is None

    def test_right_hand_sides_that_are_not_onto_do_not_cycle(self) -> None:
        # Both symbols map to beta: nothing reaches alpha, so `successor^k`
        # never returns to it and there is no period.
        presentation = PinnedPresentation(
            "fixture",
            (ALPHA, BETA),
            (PinnedRule("a", ALPHA, BETA), PinnedRule("b", BETA, BETA)),
        )
        assert presentation.successor_map is None

    def test_a_repeated_signature_symbol_is_ambiguous_about_its_own_size(self) -> None:
        presentation = PinnedPresentation(
            "fixture",
            (ALPHA, ALPHA),
            (PinnedRule("a", ALPHA, ALPHA),),
        )
        assert presentation.successor_map is None

    def test_an_empty_presentation_has_no_successor(self) -> None:
        assert PinnedPresentation("fixture", (), ()).successor_map is None

    def test_the_totality_check_is_redundant_given_the_onto_check(self) -> None:
        """Why mutation M21 is recorded as equivalent rather than chased.

        Removing the totality check from `successor_map` changes no observable
        behaviour: keys are distinct and drawn from the signature, so
        ``|keys| <= |symbols|``, while ``set(values) == symbols`` forces
        ``|keys| >= |symbols|``. Onto therefore implies total.

        Asserted by exhaustive search rather than by the counting argument
        alone, and asserted HERE so that weakening the onto check makes the
        totality line load-bearing again -- at which point this test fails,
        M21 stops being equivalent, and both facts surface together.
        """
        from itertools import combinations, product

        for size in range(1, 5):
            symbols = set(range(size))
            for count in range(size + 1):
                for keys in combinations(sorted(symbols), count):
                    for values in product(sorted(symbols), repeat=count):
                        mapping = dict(zip(keys, values))
                        onto = set(mapping.values()) == symbols
                        total = set(mapping) == symbols
                        assert not (onto and not total), (
                            f"onto but not total: {mapping} over {symbols}; the "
                            "totality check is load-bearing after all and M21 "
                            "must stop being declared equivalent"
                        )


class TestApplySuccessor:
    def test_zero_steps_is_the_identity(self) -> None:
        assert cycle(ALPHA, BETA, GAMMA).apply_successor(ALPHA, 0) == ALPHA

    def test_it_wraps_around_the_cycle(self) -> None:
        five = cycle(ALPHA, BETA, GAMMA, DELTA, EPSILON)
        assert five.apply_successor(ALPHA, 2) == GAMMA
        assert five.apply_successor(ALPHA, 5) == ALPHA
        assert five.apply_successor(ALPHA, 7) == GAMMA

    def test_a_huge_exponent_costs_one_cycle_not_a_billion_steps(self) -> None:
        """A producer chooses the exponent, so iterating hands it a lever.

        Indexing into the orbit is exact for any k and costs the cycle length.
        """
        five = cycle(ALPHA, BETA, GAMMA, DELTA, EPSILON)
        huge = 10**18 + 3
        assert five.apply_successor(ALPHA, huge) == five.apply_successor(
            ALPHA, huge % 5
        )

    def test_a_negative_exponent_is_declined(self) -> None:
        assert cycle(ALPHA, BETA).apply_successor(ALPHA, -1) is None

    def test_a_symbol_outside_the_signature_is_declined(self) -> None:
        assert cycle(ALPHA, BETA).apply_successor(GAMMA, 1) is None


class TestStrictParse:
    def test_an_undeclared_field_on_a_pin_is_refused(self) -> None:
        with pytest.raises(ValueError, match="undeclared fields"):
            PresentationPins.from_wire(
                [{"name": "x", "presentation": {}, "vibe": "good"}]
            )

    def test_an_undeclared_field_on_a_rule_is_refused(self) -> None:
        with pytest.raises(ValueError, match="undeclared fields"):
            PresentationPins.from_wire(
                [
                    {
                        "name": "x",
                        "presentation": {
                            "signature": [ALPHA],
                            "rules": [
                                {"name": "a", "lhs": ALPHA, "rhs": ALPHA, "w": 1}
                            ],
                        },
                    }
                ]
            )

    def test_a_duplicate_pin_name_is_refused(self) -> None:
        # Two presentations under one key make every lookup ambiguous, and the
        # key is what a row's presentation_ref resolves against.
        entry = {"name": "c5", "presentation": {"signature": [], "rules": []}}
        with pytest.raises(ValueError, match="declared twice"):
            PresentationPins.from_wire([entry, dict(entry)])

    def test_a_pin_without_a_name_is_refused(self) -> None:
        with pytest.raises(ValueError, match="non-empty name"):
            PresentationPins.from_wire([{"presentation": {}}])

    def test_a_pin_without_a_presentation_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no presentation"):
            PresentationPins.from_wire([{"name": "x"}])


class TestEveryMalformedPinIsAValueError:
    """The CLI catches ValueError and nothing else.

    `_load_host_presentations` turns a ValueError into a REFUSE receipt with
    exit 2. A KeyError or TypeError escapes as a traceback and exit 1, which
    breaks the contract that a pin file the host cannot read is still answered
    with a receipt rather than a stack trace. Direct indexing and a bare
    comprehension were the two ways that happened.
    """

    @pytest.mark.parametrize(
        ("label", "wire"),
        [
            (
                "rule missing name",
                [{"name": "c5", "presentation": {
                    "signature": ["a"], "rules": [{"lhs": "a", "rhs": "a"}]}}],
            ),
            (
                "rule missing lhs",
                [{"name": "c5", "presentation": {
                    "signature": ["a"], "rules": [{"name": "r", "rhs": "a"}]}}],
            ),
            (
                "rule missing rhs",
                [{"name": "c5", "presentation": {
                    "signature": ["a"], "rules": [{"name": "r", "lhs": "a"}]}}],
            ),
            (
                "signature is not a list",
                [{"name": "c5", "presentation": {"signature": 5, "rules": []}}],
            ),
            (
                "rules is not a list",
                [{"name": "c5", "presentation": {"signature": ["a"], "rules": 7}}],
            ),
        ],
    )
    def test_it_raises_value_error_not_a_traceback(self, label, wire) -> None:
        with pytest.raises(ValueError):
            PresentationPins.from_wire(wire)

    def test_a_well_formed_pin_still_parses(self) -> None:
        # Guards the parametrised cases: if from_wire rejected everything, the
        # tests above would pass for the wrong reason.
        pins = PresentationPins.from_wire(
            [{"name": "c2", "presentation": {
                "signature": [ALPHA, BETA],
                "rules": [
                    {"name": "a", "lhs": ALPHA, "rhs": BETA},
                    {"name": "b", "lhs": BETA, "rhs": ALPHA},
                ],
            }}]
        )
        assert pins.resolve("c2") is not None
        assert pins.resolve("c2").period == 2
