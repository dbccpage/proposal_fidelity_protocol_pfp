"""Exact finite forms of the three lemmas of paper Appendix A ("Two signals, one detector").

This module is vendored: it imports only the Python standard library and nothing
from the repository. Each function states one side of a lemma in exact
arithmetic (``fractions.Fraction``; floats and Booleans are refused), so that the
tests in ``code/tests/test_two_signals_one_detector.py`` can check the lemmas
exhaustively on small finite domains.

- Lemma A: if Signal 2 is computed from Signal 1, the two-signal decision table
  collapses. ``gate`` is a copy of the decision table of the audited repository
  gate (``eis/domain/danger_gate.py`` at commit
  ``30609de2c3928238715375a9bac608256fa381d8``).
- Lemma B: the Hill-style "quorum" ``H(sum of positive signals) >= t`` is a sum
  threshold. ``hill_activates`` evaluates the Hill ratio exactly for an integer
  Hill coefficient; ``sum_threshold_activates`` clears denominators instead.
- Lemma C: negative selection (screening a detector against a self panel) is
  sound for every panel exactly when the executed predicate implies the screened one.
  Soundness and rejection of no harmless rule together require equality. Predicates
  and panels over a finite universe are encoded as bit masks.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from fractions import Fraction

TOLERATED = "TOLERATED"
DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
DEFENSIVE_LOCKDOWN = "DEFENSIVE_LOCKDOWN"
QUARANTINED = "QUARANTINED"
DECISIONS = (TOLERATED, DIAGNOSTIC_ONLY, DEFENSIVE_LOCKDOWN, QUARANTINED)
SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
SEVERE = frozenset({"HIGH", "CRITICAL"})

Signal2 = tuple[str, int] | None


class LemmaInputError(TypeError):
    """A value outside the exact domain of a lemma (for example a float or a Boolean)."""


def _count(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise LemmaInputError(f"{label} must be a non-negative int, not {type(value).__name__}")
    return value


def _exact(value: object, label: str) -> Fraction:
    if type(value) is Fraction:
        return value
    if type(value) is int:
        return Fraction(value)
    raise LemmaInputError(f"{label} must be an int or a Fraction, not {type(value).__name__}")


# Lemma A -------------------------------------------------------------------


def gate(signal1_count: int, signal2: Signal2) -> str:
    """Decision of the audited two-signal table for a match count and an optional
    Signal 2 record ``(severity, defect_count)``.

    Signal 2 counts as present only when its defect count is positive.
    """
    has_signal1 = _count(signal1_count, "signal1_count") > 0
    has_signal2 = False
    severity = ""
    if signal2 is not None:
        severity, defects = signal2
        if severity not in SEVERITIES:
            raise LemmaInputError(f"unknown severity {severity!r}")
        has_signal2 = _count(defects, "defect_count") > 0
    if not has_signal1 and not has_signal2:
        return TOLERATED
    if has_signal1 and not has_signal2:
        return DIAGNOSTIC_ONLY
    if not has_signal1:
        return DEFENSIVE_LOCKDOWN if severity in SEVERE else DIAGNOSTIC_ONLY
    return QUARANTINED if severity in SEVERE else DEFENSIVE_LOCKDOWN


def audited_signal2(signal1_count: int) -> Signal2:
    """Signal 2 as the audited demonstration computes it: a HIGH defect whose count
    is the number of Signal 1 matches, or nothing when there is no match."""
    count = _count(signal1_count, "signal1_count")
    return ("HIGH", count) if count > 0 else None


def reachable(derive: Callable[[int], Signal2], counts: Iterable[int]) -> frozenset[str]:
    """Decisions reachable when Signal 2 is ``derive`` applied to the match count."""
    return frozenset(gate(count, derive(count)) for count in counts)


def diagnostic_reachable_by_characterization(derive: Callable[[int], Signal2], counts: Iterable[int]) -> bool:
    """Lemma A (ii): DIAGNOSTIC_ONLY is reachable exactly when Signal 2 disagrees with
    Signal 1 about presence, either as a match without a positive defect or as a
    low or medium defect without a match."""
    for count in counts:
        signal2 = derive(count)
        positive = signal2 is not None and signal2[1] > 0
        if count > 0 and not positive:
            return True
        if count == 0 and positive and signal2 is not None and signal2[0] not in SEVERE:
            return True
    return False


# Lemma B -------------------------------------------------------------------


def positive_sum(signals: Sequence[object]) -> Fraction:
    """Sum of the strictly positive signals, as the audited gate aggregates them."""
    total = Fraction(0)
    for index, value in enumerate(signals):
        exact = _exact(value, f"signal {index}")
        if exact > 0:
            total += exact
    return total


def hill_activates(signals: Sequence[object], n: int, k: object, t: object) -> bool:
    """``H(theta) >= t`` with ``H(theta) = theta**n / (k**n + theta**n)`` and ``H(0) = 0``,
    evaluated as an exact fraction (integer Hill coefficient ``n``)."""
    if type(n) is not int or n < 1:
        raise LemmaInputError("the Hill coefficient must be a positive int here")
    k_exact, t_exact = _exact(k, "k"), _exact(t, "t")
    if k_exact <= 0:
        raise LemmaInputError("k must be positive")
    theta = positive_sum(signals)
    hill = Fraction(0) if theta == 0 else theta**n / (k_exact**n + theta**n)
    return hill >= t_exact


def sum_threshold_activates(signals: Sequence[object], n: int, k: object, t: object) -> bool:
    """Lemma B (i): for ``0 < t < 1`` the same decision is ``theta >= k * (t / (1 - t)) ** (1/n)``,
    compared exactly as ``theta**n * (1 - t) >= t * k**n`` with ``theta > 0``."""
    if type(n) is not int or n < 1:
        raise LemmaInputError("the Hill coefficient must be a positive int here")
    k_exact, t_exact = _exact(k, "k"), _exact(t, "t")
    if k_exact <= 0:
        raise LemmaInputError("k must be positive")
    if not 0 < t_exact < 1:
        raise LemmaInputError("the sum-threshold form needs 0 < t < 1")
    theta = positive_sum(signals)
    return theta > 0 and theta**n * (1 - t_exact) >= t_exact * k_exact**n


def minimum_contributors(n: int, k: object, t: object, bound: object, limit: int = 64) -> int:
    """Lemma B (iii): the least number m of sensors, each with signal at most ``bound``,
    whose sum can activate the gate (m * bound reaches the threshold)."""
    bound_exact = _exact(bound, "bound")
    if bound_exact <= 0:
        raise LemmaInputError("bound must be positive")
    for m in range(1, limit + 1):
        if sum_threshold_activates([m * bound_exact], n, k, t):
            return m
    raise ValueError("no activating count within the limit")


# Lemma C -------------------------------------------------------------------

def _validate_predicates(executed: int, screened: int, universe_bits: int) -> None:
    size = _count(universe_bits, "universe_bits")
    for name, value in (("executed", executed), ("screened", screened)):
        if _count(value, name) >= 1 << size:
            raise LemmaInputError(f"{name} has bits outside the declared universe")


def admitted(screened: int, panel: int) -> bool:
    """The screen admits a rule when its screened predicate matches no self string."""
    return _count(screened, "screened") & _count(panel, "panel") == 0


def fires_on_self(executed: int, panel: int) -> bool:
    """The admitted rule, as executed, flags some string of the self panel."""
    return _count(executed, "executed") & _count(panel, "panel") != 0


def sound_for_every_panel(executed: int, screened: int, universe_bits: int) -> bool:
    """Negative selection is sound when no admitted rule fires on its own panel."""
    _validate_predicates(executed, screened, universe_bits)
    return all(
        not (admitted(screened, panel) and fires_on_self(executed, panel))
        for panel in range(1, 1 << universe_bits)
    )


def rejects_no_harmless_rule(executed: int, screened: int, universe_bits: int) -> bool:
    """No panel rejects a rule whose executed predicate would not fire on that panel."""
    _validate_predicates(executed, screened, universe_bits)
    return all(
        not (not admitted(screened, panel) and not fires_on_self(executed, panel))
        for panel in range(1, 1 << universe_bits)
    )


def predicate_mask(predicate: Callable[[str], bool], universe: Sequence[str]) -> int:
    """Encode a predicate on a finite universe of strings as a bit mask."""
    mask = 0
    for index, word in enumerate(universe):
        if predicate(word):
            mask |= 1 << index
    return mask
