"""The allosteric gate: exact arithmetic, no activation on silence, an honest quorum.

Counterexamples from the study (`domain/allostery.py`):

- float arithmetic with a non-integer Hill coefficient (2.5);
- `activation_threshold=0` activated with no signal at all (H(0) = 0 >= 0);
- large inputs raised a bare `OverflowError`;
- the "quorum" was a threshold on the sum, so one large sensor activated it;
- the signals were a list, so one caller could repeat itself and count twice.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from omega_engine_epistemic_immune_system.domain.allostery import (
    DEFAULT_PARAMETERS,
    AllostericConsensusGate,
    minimal_quorum,
)
from omega_engine_epistemic_immune_system.domain.value_objects import (
    AllosteryRefusal,
    HillParameters,
)


def test_hill_response_is_an_exact_fraction() -> None:
    params = HillParameters(hill_coefficient=3, half_maximal_constant=2)
    assert params.calculate_cooperativity(1) == Fraction(1, 9)
    assert params.calculate_cooperativity(Fraction(5, 2)) == Fraction(125, 189)
    assert type(params.calculate_cooperativity(0)) is Fraction


@pytest.mark.parametrize("bad", [2.5, True, "2", None])
def test_a_non_integer_hill_coefficient_is_refused(bad: object) -> None:
    """Counterexample: HillParameters(2.5, 2.0) used to be the default."""
    with pytest.raises(AllosteryRefusal) as caught:
        HillParameters(hill_coefficient=bad, half_maximal_constant=2)  # type: ignore[arg-type]
    assert caught.value.code == "NOT_EXACT"


@pytest.mark.parametrize("bad", [0, -1, 17])
def test_hill_coefficient_out_of_range_is_refused(bad: int) -> None:
    with pytest.raises(AllosteryRefusal) as caught:
        HillParameters(hill_coefficient=bad, half_maximal_constant=2)
    assert caught.value.code == "HILL_COEFFICIENT_OUT_OF_RANGE"


@pytest.mark.parametrize("signal", [0.5, True, 1e300])
def test_float_or_bool_signals_are_refused(signal: object) -> None:
    gate = AllostericConsensusGate()
    with pytest.raises(AllosteryRefusal) as caught:
        gate.evaluate_quorum({"s1": signal})
    assert caught.value.code == "NOT_EXACT"


def test_huge_signals_get_a_typed_refusal_not_overflow() -> None:
    """Old code: float(1e200) ** 2.5 raised OverflowError."""
    gate = AllostericConsensusGate(per_sensor_cap=None)
    with pytest.raises(AllosteryRefusal) as caught:
        gate.evaluate_quorum({"s1": 10**200})
    assert caught.value.code == "SIGNAL_OUT_OF_RANGE"


@pytest.mark.parametrize("threshold", [0, 1, Fraction(-1, 2), Fraction(3, 2)])
def test_a_threshold_that_fires_on_silence_or_never_is_refused(threshold: object) -> None:
    """Old code: activation_threshold=0 activated with zero signals."""
    with pytest.raises(AllosteryRefusal) as caught:
        AllostericConsensusGate(activation_threshold=threshold)
    assert caught.value.code == "THRESHOLD_OUT_OF_RANGE"


def test_no_signal_never_activates() -> None:
    gate = AllostericConsensusGate(activation_threshold=Fraction(1, 1000))
    for signals in ([], [0], [0, 0, 0]):
        decision = gate.evaluate_quorum({f"s{i}": value for i, value in enumerate(signals)})
        assert decision.is_activated is False
        assert decision.hill_value == 0


def test_the_default_gate_is_a_sum_threshold_at_two() -> None:
    """At n = 2, K = 2, t = 1/2 the gate activates exactly when the sum reaches 2."""
    gate = AllostericConsensusGate()
    assert gate.evaluate_quorum({"a": 1, "b": 1}).is_activated is True
    assert gate.evaluate_quorum({"a": 1, "b": Fraction(999, 1000)}).is_activated is False
    assert gate.evaluate_quorum({f"s{i}": Fraction(1, 2) for i in range(4)}).is_activated is True


def test_the_per_sensor_cap_makes_the_quorum_real() -> None:
    """One sensor can no longer carry the sum: a signal above the cap is refused."""
    gate = AllostericConsensusGate()
    assert gate.quorum_size == 2
    with pytest.raises(AllosteryRefusal) as caught:
        gate.evaluate_quorum({"s1": 2})
    assert caught.value.code == "SIGNAL_ABOVE_SENSOR_CAP"
    # Without a cap, one sensor suffices, and the gate says it makes no quorum claim.
    uncapped = AllostericConsensusGate(per_sensor_cap=None)
    single = uncapped.evaluate_quorum({"s1": 2})
    assert single.is_activated is True and single.quorum_size is None
    assert "no quorum claim" in single.rationale


@pytest.mark.parametrize("n", [1, 2, 3, 5])
@pytest.mark.parametrize("cap", [Fraction(1), Fraction(1, 3), Fraction(7, 5)])
def test_fewer_than_quorum_size_sensors_never_activate(n: int, cap: Fraction) -> None:
    params = HillParameters(hill_coefficient=n, half_maximal_constant=2)
    gate = AllostericConsensusGate(parameters=params, per_sensor_cap=cap)
    quorum = gate.quorum_size
    assert quorum == minimal_quorum(params, Fraction(1, 2), cap)
    if quorum > 1:
        assert gate.evaluate_quorum({f"s{i}": cap for i in range(quorum - 1)}).is_activated is False
    assert gate.evaluate_quorum({f"s{i}": cap for i in range(quorum)}).is_activated is True


def test_decision_values_are_exact_and_equality_is_exact() -> None:
    gate = AllostericConsensusGate(parameters=DEFAULT_PARAMETERS)
    a = gate.evaluate_quorum({"a": 1, "b": 1})
    b = gate.evaluate_quorum({"a": 1, "b": 1})
    assert a == b and hash(a) == hash(b)
    assert type(a.hill_value) is Fraction and a.hill_value == Fraction(1, 2)
    assert a.aggregate_signal == 2 and a.positive_sensors == 2


def test_one_sensor_cannot_count_twice() -> None:
    """Counterexample: `evaluate_quorum([1, 1])` from a single caller activated the
    gate, because the quorum counted list entries rather than distinct sensors."""
    gate = AllostericConsensusGate()
    with pytest.raises(AllosteryRefusal) as caught:
        gate.evaluate_quorum([1, 1])
    assert caught.value.code == "SIGNALS_NOT_KEYED"
    with pytest.raises(AllosteryRefusal) as caught:
        gate.evaluate_quorum({"sensor": 1, "SENSOR": 1})
    assert caught.value.code == "DUPLICATE_SENSOR"
    with pytest.raises(AllosteryRefusal) as caught:
        gate.evaluate_quorum({"": 1, "b": 1})
    assert caught.value.code == "BAD_SENSOR_ID"
    # One sensor alone, at the cap, stays below the two-sensor quorum.
    assert gate.evaluate_quorum({"sensor": 1}).is_activated is False
    assert gate.evaluate_quorum({"sensor": 1, "other": 1}).positive_sensors == 2
