"""Allosteric consensus gate: an exact threshold on summed sensor signals.

What the gate decides. The input maps each sensor id to that sensor's exact
non-negative signal (`int` or `Fraction`; floats and booleans are refused).
Sensor ids are compared case-insensitively and each sensor counts once: a
list of values, or two ids that differ only in case, is refused, so one caller
cannot supply the whole quorum by repeating itself. The gate sums the
signals to S and computes the Hill response H(S) = S**n / (K**n + S**n) with an
integer coefficient n. It activates when H(S) >= t for a threshold 0 < t < 1
and at least one signal is positive.

Because H is strictly increasing in S, H(S) >= t holds exactly when
S**n * (1 - t) >= t * K**n. So the gate is a threshold on the sum of the
signals; the Hill form changes the reported response value, not which sums
activate. At the defaults (n = 2, K = 2, t = 1/2) it activates exactly when
S >= 2.

The quorum statement. A sum threshold alone does not require several sensors:
one sensor reporting a large enough value would activate it. The gate therefore
bounds every signal by a per-sensor cap c (default 1) and refuses any signal
above it. With every signal at most c, no set of fewer than `quorum_size`
distinct positive sensors can reach the threshold, where `quorum_size` is the least m
with H(m * c) >= t. At the defaults `quorum_size` is 2. With `per_sensor_cap`
set to None the gate is a plain sum threshold and makes no quorum claim
(`quorum_size` is None).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping

from .value_objects import AllosteryRefusal, HillParameters, exact_rational

DEFAULT_PARAMETERS = HillParameters(hill_coefficient=2, half_maximal_constant=Fraction(2))
DEFAULT_ACTIVATION_THRESHOLD = Fraction(1, 2)
DEFAULT_PER_SENSOR_CAP = Fraction(1)
MAX_SENSORS = 4096


def _reaches_threshold(parameters: HillParameters, total: Fraction, threshold: Fraction) -> bool:
    """H(total) >= threshold, decided without division: total**n (1 - t) >= t K**n."""
    if total <= 0:
        return False
    n = parameters.hill_coefficient
    return total ** n * (1 - threshold) >= threshold * parameters.half_maximal_constant ** n


def minimal_quorum(parameters: HillParameters, threshold: Fraction, per_sensor_cap: Fraction) -> int:
    """The least m >= 1 with H(m * cap) >= threshold (exact search)."""
    high = 1
    while not _reaches_threshold(parameters, high * per_sensor_cap, threshold):
        high *= 2
    low = high // 2 + 1 if high > 1 else 1
    while low < high:
        middle = (low + high) // 2
        if _reaches_threshold(parameters, middle * per_sensor_cap, threshold):
            high = middle
        else:
            low = middle + 1
    return high


@dataclass(frozen=True, slots=True)
class AllostericDecision:
    """Exact-type decision emitted by AllostericConsensusGate."""
    is_activated: bool
    hill_value: Fraction
    aggregate_signal: Fraction
    threshold: Fraction
    parameters: HillParameters
    rationale: str
    positive_sensors: int = 0
    quorum_size: int | None = None
    per_sensor_cap: Fraction | None = None

    def __post_init__(self) -> None:
        if type(self.is_activated) is not bool:
            raise TypeError("is_activated must be a boolean")
        for label in ("hill_value", "aggregate_signal", "threshold"):
            if type(getattr(self, label)) is not Fraction:
                raise TypeError(f"{label} must be a Fraction")
        if not 0 <= self.hill_value <= 1:
            raise ValueError(f"hill_value must be in [0, 1], got {self.hill_value}")
        if self.aggregate_signal < 0:
            raise ValueError("aggregate_signal must be non-negative")
        if not 0 < self.threshold < 1:
            raise ValueError("threshold must be in (0, 1)")
        if type(self.parameters) is not HillParameters:
            raise TypeError("parameters must be a HillParameters value object")
        if type(self.rationale) is not str or not self.rationale.strip():
            raise ValueError("rationale must be non-empty string")
        if type(self.positive_sensors) is not int or self.positive_sensors < 0:
            raise ValueError("positive_sensors must be a non-negative int")
        if self.quorum_size is not None and (type(self.quorum_size) is not int or self.quorum_size < 1):
            raise ValueError("quorum_size must be a positive int or None")
        if self.per_sensor_cap is not None and type(self.per_sensor_cap) is not Fraction:
            raise TypeError("per_sensor_cap must be a Fraction or None")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.is_activated is other.is_activated
            and self.hill_value == other.hill_value
            and self.aggregate_signal == other.aggregate_signal
            and self.threshold == other.threshold
            and self.parameters == other.parameters
            and self.rationale == other.rationale
            and self.positive_sensors == other.positive_sensors
            and self.quorum_size == other.quorum_size
            and self.per_sensor_cap == other.per_sensor_cap
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.is_activated,
            self.hill_value,
            self.aggregate_signal,
            self.threshold,
            self.parameters,
            self.rationale,
            self.positive_sensors,
            self.quorum_size,
            self.per_sensor_cap,
        ))


class AllostericConsensusGate:
    """Exact sum-threshold gate with an optional per-sensor cap (see module docstring)."""

    def __init__(
        self,
        parameters: HillParameters | None = None,
        activation_threshold: object = DEFAULT_ACTIVATION_THRESHOLD,
        per_sensor_cap: object = DEFAULT_PER_SENSOR_CAP,
    ) -> None:
        if parameters is None:
            parameters = DEFAULT_PARAMETERS
        if type(parameters) is not HillParameters:
            raise TypeError("parameters must be a HillParameters value object")
        threshold = exact_rational(activation_threshold, "activation_threshold")
        # t = 0 would activate on silence; t = 1 can never be reached for finite S.
        if not 0 < threshold < 1:
            raise AllosteryRefusal("THRESHOLD_OUT_OF_RANGE", "activation_threshold must satisfy 0 < t < 1")
        cap: Fraction | None
        if per_sensor_cap is None:
            cap = None
        else:
            cap = exact_rational(per_sensor_cap, "per_sensor_cap")
            if cap <= 0:
                raise AllosteryRefusal("SENSOR_CAP_OUT_OF_RANGE", "per_sensor_cap must be > 0")
        self.parameters = parameters
        self.activation_threshold = threshold
        self.per_sensor_cap = cap
        self.quorum_size = (
            None if cap is None else minimal_quorum(parameters, threshold, cap)
        )

    def _signals(self, sensor_signals: object) -> tuple[Fraction, ...]:
        if not isinstance(sensor_signals, Mapping):
            raise AllosteryRefusal(
                "SIGNALS_NOT_KEYED",
                f"sensor signals must map sensor ids to values, got {type(sensor_signals).__name__}",
            )
        if len(sensor_signals) > MAX_SENSORS:
            raise AllosteryRefusal("SIGNAL_OUT_OF_RANGE", f"more than {MAX_SENSORS} sensors")
        seen: set[str] = set()
        signals = []
        for sensor_id, raw in sensor_signals.items():
            if type(sensor_id) is not str or not sensor_id.strip():
                raise AllosteryRefusal("BAD_SENSOR_ID", f"sensor id {sensor_id!r} is not a non-empty str")
            folded = sensor_id.strip().casefold()
            if folded in seen:
                raise AllosteryRefusal(
                    "DUPLICATE_SENSOR", f"sensor {sensor_id!r} appears more than once"
                )
            seen.add(folded)
            value = exact_rational(raw, f"sensor {sensor_id!r}")
            if value < 0:
                raise AllosteryRefusal("SIGNAL_OUT_OF_RANGE", f"sensor {sensor_id!r} is negative")
            if self.per_sensor_cap is not None and value > self.per_sensor_cap:
                raise AllosteryRefusal(
                    "SIGNAL_ABOVE_SENSOR_CAP",
                    f"sensor {sensor_id!r} = {value} exceeds the per-sensor cap {self.per_sensor_cap}",
                )
            signals.append(value)
        return tuple(signals)

    def evaluate_quorum(self, sensor_signals: Mapping[str, object]) -> AllostericDecision:
        """Sum the exact signals of distinct sensors and apply the threshold."""
        signals = self._signals(sensor_signals)
        aggregate = sum(signals, Fraction(0))
        positive = sum(1 for value in signals if value > 0)
        hill_value = self.parameters.calculate_cooperativity(aggregate)
        is_activated = positive > 0 and _reaches_threshold(
            self.parameters, aggregate, self.activation_threshold
        )
        n = self.parameters.hill_coefficient
        k = self.parameters.half_maximal_constant
        verdict = "ACTIVATED" if is_activated else "NOT ACTIVATED"
        comparison = ">=" if is_activated else "<"
        rationale = (
            f"{verdict}: {positive} positive sensor(s) sum to S = {aggregate}; "
            f"H(S) = {hill_value} {comparison} t = {self.activation_threshold} "
            f"(n = {n}, K = {k})."
        )
        if self.quorum_size is not None:
            rationale += (
                f" Per-sensor cap {self.per_sensor_cap}: activation needs at least "
                f"{self.quorum_size} positive sensor(s)."
            )
        else:
            rationale += " No per-sensor cap: this is a sum threshold with no quorum claim."
        return AllostericDecision(
            is_activated=is_activated,
            hill_value=hill_value,
            aggregate_signal=aggregate,
            threshold=self.activation_threshold,
            parameters=self.parameters,
            rationale=rationale,
            positive_sensors=positive,
            quorum_size=self.quorum_size,
            per_sensor_cap=self.per_sensor_cap,
        )


__all__ = [
    "AllostericConsensusGate",
    "AllostericDecision",
    "DEFAULT_ACTIVATION_THRESHOLD",
    "DEFAULT_PARAMETERS",
    "DEFAULT_PER_SENSOR_CAP",
    "minimal_quorum",
]
