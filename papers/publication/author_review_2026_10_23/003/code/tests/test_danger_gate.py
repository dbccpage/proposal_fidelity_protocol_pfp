"""Tests for the two-signal decision table and the four candidate phrase detectors.

The table and detector tests run the Python reference. The last test compares the
Rust port with the Python reference; it needs a built binary and is skipped,
with the reason stated, when none is found.
"""

from __future__ import annotations

import pytest

from canaries import scan_for_canaries
from danger_gate import (
    DangerDecision,
    DangerSeverity,
    Signal1Match,
    Signal2Danger,
    evaluate_two_signal_gate,
)
from native_host_detector import (
    BINARY_ENV,
    native_binary_path,
    native_evaluate_two_signal_gate,
    native_scan_for_canaries,
)

_SIGNAL1 = [
    Signal1Match(
        epitope_name="AM-FSP-8-TROYER-WIESE",
        pattern_matched="Troyer-Wiese",
        confidence_num=1,
        confidence_den=1,
    )
]
_SIGNAL2_LOW = Signal2Danger(
    danger_type="UNOPTIMIZED_CONTRACT",
    severity=DangerSeverity.LOW.value,
    defect_count=1,
)
_SIGNAL2_MEDIUM = Signal2Danger(
    danger_type="ODD_CYCLE_OBSTRUCTION",
    severity=DangerSeverity.MEDIUM.value,
)
_SIGNAL2_CRITICAL = Signal2Danger(
    danger_type="CORRUPTED_EVENT_CHAIN",
    severity=DangerSeverity.CRITICAL.value,
    defect_count=2,
)

_TRUE_ATTRACTIVE_U = (
    "For attractive U < 0 with equal spin populations, determinant QMC is "
    "sign-problem-free on any lattice."
)

_DETECTOR_CASES = [
    ("Claiming to solve np-hard sign problem solved in p unconditionally.", "AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM"),
    ("We assume particle-hole symmetry on triangle plaquettes at half filling.", "AM-FSP-2-FRUSTRATED-OBSTRUCTION"),
    ("Defining smooth majorana representation on 2-torus without holonomy.", "AM-FSP-7-UNVERIFIED-MAJORANA-LIFT"),
    (
        "Meron cluster algorithms eliminate sign oscillations for every doped model.",
        "AM-FSP-4-ORBIT-SUM-MISMATCH",
    ),
]


def test_gate_neither_signal_is_tolerated() -> None:
    dec = evaluate_two_signal_gate([])
    assert dec.decision == DangerDecision.TOLERATED.value
    assert not dec.is_refusal
    assert not dec.is_suppressed


def test_gate_signal1_alone_is_diagnostic() -> None:
    dec = evaluate_two_signal_gate(_SIGNAL1, None)
    assert dec.decision == DangerDecision.DIAGNOSTIC_ONLY.value
    assert not dec.is_refusal
    assert not dec.is_suppressed
    assert dec.signal1_count == 1


def test_gate_signal2_alone_low_is_diagnostic() -> None:
    dec = evaluate_two_signal_gate([], _SIGNAL2_LOW)
    assert dec.decision == DangerDecision.DIAGNOSTIC_ONLY.value
    assert not dec.is_refusal


def test_gate_signal2_alone_critical_refuses() -> None:
    dec = evaluate_two_signal_gate([], _SIGNAL2_CRITICAL)
    assert dec.decision == DangerDecision.DEFENSIVE_LOCKDOWN.value
    assert dec.is_refusal
    assert dec.is_suppressed


def test_gate_both_signals_refuse() -> None:
    dec = evaluate_two_signal_gate(_SIGNAL1, _SIGNAL2_MEDIUM)
    assert dec.decision == DangerDecision.QUARANTINED.value
    assert dec.is_refusal
    assert dec.is_suppressed
    assert dec.disposition == "REFUSED_DUAL_SIGNAL_CORROBORATION"


@pytest.mark.parametrize(("text", "canary_id"), _DETECTOR_CASES)
def test_each_detector_flags_its_constructed_sentence(text: str, canary_id: str) -> None:
    assert [finding.canary_id for finding in scan_for_canaries(text)] == [canary_id]


def test_attractive_u_true_statement_is_not_flagged() -> None:
    """A true statement must not be flagged (paper Section 3.1, AM-FSP-2).

    Version 1.0.0 listed the phrase "attractive u < 0" under AM-FSP-2; it occurs in
    this true sentence, so that list would have suppressed a valid statement.
    """
    assert "attractive u < 0" in _TRUE_ATTRACTIVE_U.lower()
    assert scan_for_canaries(_TRUE_ATTRACTIVE_U) == []


def test_phrase_match_does_not_see_negation() -> None:
    """A negated sentence still matches: phrase matching cannot see negation."""
    negated = "There is no particle-hole symmetry on triangle plaquettes."
    assert [f.canary_id for f in scan_for_canaries(negated)] == ["AM-FSP-2-FRUSTRATED-OBSTRUCTION"]


def test_native_port_matches_python_reference() -> None:
    if native_binary_path() is None:
        pytest.skip(
            "Rust binary not built; run `cargo build --release -j 1 --manifest-path "
            f"code/rust/Cargo.toml` or set {BINARY_ENV}"
        )
    gate_cases = [
        ([], None),
        (_SIGNAL1, None),
        ([], _SIGNAL2_LOW),
        ([], _SIGNAL2_CRITICAL),
        (_SIGNAL1, _SIGNAL2_MEDIUM),
    ]
    for signal1, signal2 in gate_cases:
        assert native_evaluate_two_signal_gate(signal1, signal2) == evaluate_two_signal_gate(signal1, signal2)
    texts = [text for text, _ in _DETECTOR_CASES] + [
        _TRUE_ATTRACTIVE_U,
        "There is no particle-hole symmetry on triangle plaquettes.",
        "We compute the discrete cochain boundary of a 1-chain on a bipartite square lattice over Q.",
    ]
    for text in texts:
        assert native_scan_for_canaries(text) == scan_for_canaries(text)
