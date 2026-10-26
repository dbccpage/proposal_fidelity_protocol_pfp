"""Exhaustive finite checks of the three lemmas of paper Appendix A.

Every check is exact (``fractions.Fraction`` or integers), enumerates a small
finite domain completely, and uses only this package's ``code/`` folder and the
standard library. The counterexamples the lemmas predict are named in the test
names.
"""

from __future__ import annotations

import re
from fractions import Fraction
from itertools import product

import pytest

from danger_gate import Signal1Match, Signal2Danger, evaluate_two_signal_gate
from detector_lemmas import (
    DECISIONS,
    DEFENSIVE_LOCKDOWN,
    DIAGNOSTIC_ONLY,
    QUARANTINED,
    SEVERE,
    SEVERITIES,
    TOLERATED,
    LemmaInputError,
    admitted,
    audited_signal2,
    diagnostic_reachable_by_characterization,
    fires_on_self,
    gate,
    hill_activates,
    minimum_contributors,
    positive_sum,
    predicate_mask,
    reachable,
    rejects_no_harmless_rule,
    sound_for_every_panel,
    sum_threshold_activates,
)

COUNTS = (0, 1, 2, 3)
SIGNAL2_VALUES = (None,) + tuple((severity, defects) for severity in SEVERITIES for defects in (0, 1, 2))

HALF = Fraction(1, 2)
SIGNAL_VALUES = (Fraction(-1), Fraction(0), Fraction(1, 2), Fraction(1), Fraction(3, 2), Fraction(2), Fraction(3))
SIGNAL_VECTORS = tuple(vector for size in range(4) for vector in product(SIGNAL_VALUES, repeat=size))
HILL_NS = (1, 2, 3, 4)
KS = (Fraction(1, 2), Fraction(1), Fraction(2), Fraction(3))
TS = (Fraction(1, 4), Fraction(1, 3), HALF, Fraction(2, 3), Fraction(3, 4))


# Lemma A: a Signal 2 computed from Signal 1 collapses the decision table.


def test_audited_derivation_reaches_only_tolerated_or_quarantined() -> None:
    """Signal 2 = a HIGH defect counting the matches: the gate refuses exactly on a match."""
    assert reachable(audited_signal2, range(50)) == {TOLERATED, QUARANTINED}
    for count in range(50):
        expected = QUARANTINED if count > 0 else TOLERATED
        assert gate(count, audited_signal2(count)) == expected


def test_derived_signal2_exhaustive_over_every_function_of_the_match_count() -> None:
    """All 13**4 functions from match counts 0..3 to Signal 2 values."""
    hypothesis_cases = 0
    for values in product(SIGNAL2_VALUES, repeat=len(COUNTS)):
        table = dict(zip(COUNTS, values))
        decisions = reachable(table.__getitem__, COUNTS)
        assert decisions <= set(DECISIONS)
        assert (DIAGNOSTIC_ONLY in decisions) == diagnostic_reachable_by_characterization(table.__getitem__, COUNTS)
        first = table[0]
        rest = [table[count] for count in COUNTS if count > 0]
        severities = {signal[0] for signal in rest if signal is not None}
        present_exactly_with_signal1 = (
            (first is None or first[1] == 0)
            and all(signal is not None and signal[1] > 0 for signal in rest)
            and len(severities) == 1
        )
        if present_exactly_with_signal1:
            hypothesis_cases += 1
            (severity,) = severities
            refusal = QUARANTINED if severity in SEVERE else DEFENSIVE_LOCKDOWN
            assert decisions == {TOLERATED, refusal}
            assert DIAGNOSTIC_ONLY not in decisions
    assert hypothesis_cases == 160


def test_independent_signals_reach_all_four_decisions() -> None:
    decisions = {gate(count, signal2) for count in COUNTS for signal2 in SIGNAL2_VALUES}
    assert decisions == set(DECISIONS)


def test_package_gate_collapses_the_same_way_under_a_derived_signal2() -> None:
    """The package re-implementation of Section 4.1 shows the same collapse."""
    seen = set()
    for size in range(6):
        matches = [Signal1Match(epitope_name=f"E{i}", pattern_matched="p") for i in range(size)]
        signal2 = Signal2Danger(danger_type="DERIVED", severity="HIGH", defect_count=size) if matches else None
        seen.add(evaluate_two_signal_gate(matches, signal2).decision)
    assert seen == {TOLERATED, QUARANTINED}


def test_gate_refuses_booleans_as_counts() -> None:
    with pytest.raises(LemmaInputError):
        gate(True, None)
    with pytest.raises(LemmaInputError):
        gate(1, ("HIGH", True))


# Lemma B: the Hill "quorum" is a sum threshold.


def test_hill_rule_equals_sum_threshold_on_the_whole_domain() -> None:
    for signals, n, k, t in product(SIGNAL_VECTORS, HILL_NS, KS, TS):
        assert hill_activates(signals, n, k, t) == sum_threshold_activates(signals, n, k, t)


def test_half_threshold_decision_does_not_depend_on_the_hill_coefficient() -> None:
    for signals, k in product(SIGNAL_VECTORS, KS):
        theta = positive_sum(signals)
        decisions = {hill_activates(signals, n, k, HALF) for n in range(1, 7)}
        assert decisions == {theta > 0 and theta >= k}


def test_decision_depends_only_on_the_positive_sum_and_is_monotone() -> None:
    for n, k, t in product(HILL_NS, KS, TS):
        by_sum: dict[Fraction, bool] = {}
        for signals in SIGNAL_VECTORS:
            decision = hill_activates(signals, n, k, t)
            assert by_sum.setdefault(positive_sum(signals), decision) == decision
        ordered = [by_sum[total] for total in sorted(by_sum)]
        assert ordered == sorted(ordered)


def test_one_sensor_alone_can_activate_every_threshold() -> None:
    """No agent-count property: a single large signal reaches any threshold."""
    for n, k, t in product(HILL_NS, KS, TS):
        single = k * max(Fraction(1), t / (1 - t))
        assert hill_activates([single], n, k, t)


def test_agent_count_follows_only_from_a_per_sensor_bound() -> None:
    bound = Fraction(1)
    for n, k, t in product(HILL_NS, KS, TS):
        needed = minimum_contributors(n, k, t, bound)
        for signals in SIGNAL_VECTORS:
            if all(value <= bound for value in signals) and hill_activates(signals, n, k, t):
                assert sum(1 for value in signals if value > 0) >= needed
    # The audited defaults (K = 2, t = 1/2) need two unit signals, but one signal of 2 suffices.
    assert minimum_contributors(3, Fraction(2), HALF, bound) == 2
    assert hill_activates([Fraction(2)], 3, Fraction(2), HALF)


def test_threshold_zero_activates_without_any_signal_and_one_never_activates() -> None:
    for n, k in product(HILL_NS, KS):
        assert hill_activates([], n, k, 0)
        assert not any(hill_activates(signals, n, k, 1) for signals in SIGNAL_VECTORS)


def test_hill_rule_refuses_float_and_boolean_signals() -> None:
    with pytest.raises(LemmaInputError):
        hill_activates([0.5], 2, Fraction(2), HALF)
    with pytest.raises(LemmaInputError):
        hill_activates([True], 2, Fraction(2), HALF)
    with pytest.raises(LemmaInputError):
        hill_activates([Fraction(1)], 2, 2.0, HALF)

@pytest.mark.parametrize("n", (True, 1.5, Fraction(3, 2), 0, -1))
def test_sum_threshold_refuses_exponents_outside_the_exact_contract(n: object) -> None:
    with pytest.raises(LemmaInputError):
        sum_threshold_activates([2], n, 2, HALF)


@pytest.mark.parametrize("k", (0, -1, 2.0, True))
def test_sum_threshold_refuses_inexact_or_nonpositive_scales(k: object) -> None:
    with pytest.raises(LemmaInputError):
        sum_threshold_activates([2], 2, k, HALF)


# Lemma C: negative selection is sound only when the screened predicate is executed.

UNIVERSE_BITS = 6

@pytest.mark.parametrize("mask", (True, 1.0, -1))
def test_panel_entry_points_refuse_non_masks(mask: object) -> None:
    with pytest.raises(LemmaInputError):
        admitted(mask, 1)
    with pytest.raises(LemmaInputError):
        fires_on_self(mask, 1)
    with pytest.raises(LemmaInputError):
        admitted(1, mask)
    with pytest.raises(LemmaInputError):
        fires_on_self(1, mask)


@pytest.mark.parametrize("check", (sound_for_every_panel, rejects_no_harmless_rule))
def test_universal_panel_checks_bind_the_declared_universe(check) -> None:
    with pytest.raises(LemmaInputError):
        check(4, 0, 2)
    with pytest.raises(LemmaInputError):
        check(0, 4, 2)
    with pytest.raises(LemmaInputError):
        check(0, 0, True)


def test_screening_is_sound_for_every_panel_iff_executed_implies_screened() -> None:
    """All pairs of predicates and all nonempty self panels over a six-string universe."""
    full = (1 << UNIVERSE_BITS) - 1
    for executed in range(1 << UNIVERSE_BITS):
        for screened in range(1 << UNIVERSE_BITS):
            assert sound_for_every_panel(executed, screened, UNIVERSE_BITS) == (executed & (full ^ screened) == 0)
            assert rejects_no_harmless_rule(executed, screened, UNIVERSE_BITS) == (screened & (full ^ executed) == 0)


def test_pattern_ignoring_matcher_is_admitted_and_fires_on_a_self_fixture() -> None:
    """Counterexample: the screen tests the class name, the matcher tests the structure."""
    self_panel = ['{"claim": "x", "witness": "w"}', '{"claim": "y", "evidence": []}']
    other = ['{"claim": "z"}', "MISSING_WITNESS reported"]
    universe = self_panel + other
    screened = predicate_mask(lambda text: re.search(re.escape("MISSING_WITNESS"), text, re.IGNORECASE) is not None, universe)
    executed = predicate_mask(lambda text: '"witness"' not in text, universe)
    panel = predicate_mask(lambda text: text in self_panel, universe)
    assert admitted(screened, panel)
    assert fires_on_self(executed, panel)


def test_screening_the_executed_predicate_rejects_that_rule() -> None:
    self_panel = ['{"claim": "x", "witness": "w"}', '{"claim": "y", "evidence": []}']
    universe = self_panel + ['{"claim": "z"}']
    executed = predicate_mask(lambda text: '"witness"' not in text, universe)
    panel = predicate_mask(lambda text: text in self_panel, universe)
    assert not admitted(executed, panel)
