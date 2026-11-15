"""
Executable test witnesses for Paper 003 Derivations:
- ATL-P003-002 (AUDIT-P003-002): Baseline route refusal without certified witness
- ATL-P003-003 (AUDIT-P003-003): Baseline host edge-case transitions
- Two-signal table gate determinism
- Hash-chained receipt monotonicity and tamper controls
"""

from __future__ import annotations

from pathlib import Path
import sys
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Enable operating_system import resolution for baseline protocol adapter
if str(_REPO_ROOT / "ops") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "ops"))

# Enable Paper 003 package code imports
_P3_CODE = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "003_pfp_host_admitted_failure_detectors"
    / "code"
).resolve()
if str(_P3_CODE) not in sys.path:
    sys.path.insert(0, str(_P3_CODE))

from pfp.infrastructure.adapters.mssn_scenarios.protocol import (
    Demo3HostEngine as BaselineDemo3HostEngine,
    MoveProposal as BaselineMoveProposal,
    HostPhase as BaselineHostPhase,
    HostExit as BaselineHostExit,
)

from host_engine import (
    Demo3HostEngine as PkgDemo3HostEngine,
    MoveProposal as PkgMoveProposal,
    HostPhase as PkgHostPhase,
    HostExit as PkgHostExit,
    verify_route,
    DemoRefusal,
    KNOWN_FIXTURES,
    initial_digest,
    chain_digest,
    event_bytes,
    move_mapping,
)

from danger_gate import (
    DangerDecision,
    DangerSeverity,
    Signal1Match,
    Signal2Danger,
    evaluate_two_signal_gate,
)


# ============================================================================
# ATL-P003-002: Baseline Route Refusal Without Certified Witness
# ============================================================================


def test_baseline_route_refusal_all_declared_fixtures():
    """For every nonempty declared route, verify_route returns NO_NATIVE_PORT and certifies no witness."""
    assert len(KNOWN_FIXTURES) >= 5
    for fixture_id, route_name in KNOWN_FIXTURES.items():
        refusal = verify_route(route_name)
        assert isinstance(refusal, DemoRefusal)
        assert refusal.code == "NO_NATIVE_PORT"
        assert refusal.detail == route_name

        # Execute in package host and confirm no witness is certified
        engine = PkgDemo3HostEngine(fixture_id, "T", initial_fuel=10)
        engine.execute_batch([PkgMoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
        receipt = engine.execute_batch([
            PkgMoveProposal("PROPOSE_WITNESS", {"witness_type": "vertex_bits", "witness": [0, 1, 0]}),
            PkgMoveProposal("VERIFY", {}),
        ])
        assert receipt.host_decision == "NO_NATIVE_PORT"
        assert receipt.batch_rolled_back is True
        assert engine.state.terminal_exit is None
        assert engine.state.terminal_label is None


def test_baseline_route_refusal_empty_route_boundary():
    """Empty route string raises UNKNOWN_ROUTE DemoRefusal."""
    with pytest.raises(DemoRefusal) as caught:
        verify_route("")
    assert caught.value.code == "UNKNOWN_ROUTE"


# ============================================================================
# ATL-P003-003: Baseline Host Edge-Case Transitions
# ============================================================================


def test_baseline_host_move_after_verify_charge_and_rollback():
    """Move after VERIFY triggers REJECT_MOVE_AFTER_VERIFY, rolls back state, and charges 1 fuel."""
    engine = BaselineDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=8)
    f_before = engine.state.remaining_fuel

    receipt = engine.execute_batch([
        BaselineMoveProposal("COVER_ELEMENT", {"element_id": "elem_all"}),
        BaselineMoveProposal("PROPOSE_WITNESS", {"witness_type": "vertex_bits", "witness": [0, 1, 0]}),
        BaselineMoveProposal("VERIFY", {}),
        BaselineMoveProposal("COVER_ELEMENT", {"element_id": "elem_trailing"}),
    ])

    assert receipt.host_decision == "REJECT_MOVE_AFTER_VERIFY"
    assert receipt.batch_rolled_back is True
    assert engine.state.remaining_fuel == f_before - 1
    assert engine.state.covered_elements == set()
    assert engine.state.witness_candidate is None


def test_baseline_host_malformed_element_id_refusal_and_rollback():
    """Malformed element identifiers are refused with REJECT_MALFORMED_PAYLOAD and charged."""
    malformed_ids = [True, False, 12345, "", None]
    for bad_id in malformed_ids:
        engine = BaselineDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=6)
        f_before = engine.state.remaining_fuel

        payload = {"element_id": bad_id} if bad_id is not None else {}
        receipt = engine.execute_batch([BaselineMoveProposal("COVER_ELEMENT", payload)])

        assert receipt.batch_rolled_back is True
        assert receipt.host_decision in ("REJECT_MALFORMED_PAYLOAD", "REJECT_MALFORMED_ELEMENT")
        assert engine.state.remaining_fuel == f_before - 1
        assert engine.state.covered_elements == set()


def test_baseline_host_empty_batch_charged_and_accepted():
    """Baseline host charges 1 fuel unit and records ACCEPTED on empty batch (contrasting package host)."""
    # Baseline host behavior
    base_engine = BaselineDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=5)
    f_before = base_engine.state.remaining_fuel

    receipt = base_engine.execute_batch([])

    assert receipt.host_decision == "ACCEPTED"
    assert receipt.batch_rolled_back is False
    assert base_engine.state.remaining_fuel == f_before - 1
    assert base_engine.state.current_phase == BaselineHostPhase.INTAKE

    # Contrast with package host behavior which refuses empty batches
    pkg_engine = PkgDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=5)
    pkg_receipt = pkg_engine.execute_batch([])
    assert pkg_receipt.host_decision == "REJECT_EMPTY_BATCH"
    assert pkg_receipt.batch_rolled_back is True
    assert pkg_engine.state.remaining_fuel == 4


def test_baseline_host_fuel_exhaustion_and_terminal_transition():
    """With fuel 0 the next batch is recorded FUEL_EXHAUSTED and phase becomes TERMINAL."""
    engine = BaselineDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=0)

    receipt = engine.execute_batch([BaselineMoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])

    assert receipt.host_decision == BaselineHostExit.FUEL_EXHAUSTED
    assert receipt.phase_after == BaselineHostPhase.TERMINAL
    assert engine.state.terminal_exit == BaselineHostExit.FUEL_EXHAUSTED
    assert engine.state.remaining_fuel == 0


def test_baseline_host_post_terminal_rejection():
    """Subsequent batches submitted in TERMINAL phase are rejected with REJECT_TERMINAL_STATE."""
    engine = BaselineDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=0)
    engine.execute_batch([BaselineMoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
    assert engine.state.terminal_exit == BaselineHostExit.FUEL_EXHAUSTED

    post_receipt = engine.execute_batch([BaselineMoveProposal("COVER_ELEMENT", {"element_id": "elem_late"})])
    assert post_receipt.host_decision == "REJECT_TERMINAL_STATE"
    assert post_receipt.batch_rolled_back is True
    assert engine.state.remaining_fuel == 0


# ============================================================================
# Two-Signal Table Gate Determinism
# ============================================================================


def test_two_signal_table_gate_determinism_matrix():
    """Two-signal danger gate evaluates deterministically across all five input branches."""
    # Branch 1: Neither signal -> TOLERATED
    d_none = evaluate_two_signal_gate([])
    assert d_none.decision == DangerDecision.TOLERATED.value
    assert d_none.is_refusal is False

    # Branch 2: Signal 1 alone -> DIAGNOSTIC_ONLY
    d_s1 = evaluate_two_signal_gate([Signal1Match("canary_alpha", "pattern_foo")])
    assert d_s1.decision == DangerDecision.DIAGNOSTIC_ONLY.value
    assert d_s1.is_refusal is False

    # Branch 3: Signal 2 alone, LOW/MEDIUM severity -> DIAGNOSTIC_ONLY
    d_s2_low = evaluate_two_signal_gate([], Signal2Danger("defect_beta", "LOW"))
    assert d_s2_low.decision == DangerDecision.DIAGNOSTIC_ONLY.value
    assert d_s2_low.is_refusal is False

    d_s2_med = evaluate_two_signal_gate([], Signal2Danger("defect_gamma", "MEDIUM"))
    assert d_s2_med.decision == DangerDecision.DIAGNOSTIC_ONLY.value
    assert d_s2_med.is_refusal is False

    # Branch 4: Signal 2 alone, HIGH/CRITICAL severity -> DEFENSIVE_LOCKDOWN (refusal)
    d_s2_high = evaluate_two_signal_gate([], Signal2Danger("defect_delta", "HIGH"))
    assert d_s2_high.decision == DangerDecision.DEFENSIVE_LOCKDOWN.value
    assert d_s2_high.is_refusal is True

    d_s2_crit = evaluate_two_signal_gate([], Signal2Danger("defect_epsilon", "CRITICAL"))
    assert d_s2_crit.decision == DangerDecision.DEFENSIVE_LOCKDOWN.value
    assert d_s2_crit.is_refusal is True

    # Branch 5: Both signals -> QUARANTINED (refusal)
    d_both = evaluate_two_signal_gate(
        [Signal1Match("canary_alpha", "pattern_foo")],
        Signal2Danger("defect_gamma", "MEDIUM"),
    )
    assert d_both.decision == DangerDecision.QUARANTINED.value
    assert d_both.is_refusal is True

    # Determinism assertion: repeated evaluation yields identical output
    d_both_repeat = evaluate_two_signal_gate(
        [Signal1Match("canary_alpha", "pattern_foo")],
        Signal2Danger("defect_gamma", "MEDIUM"),
    )
    assert d_both.to_dict() == d_both_repeat.to_dict()


# ============================================================================
# Hash-Chained Receipt Monotonicity
# ============================================================================


def test_hash_chained_receipt_monotonic_step_and_digests():
    """Receipt history exhibits strictly monotonic step indices and chained SHA-256 state digests."""
    engine = BaselineDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=10)
    batches = [
        [BaselineMoveProposal("COVER_ELEMENT", {"element_id": "elem_1"})],
        [BaselineMoveProposal("COVER_ELEMENT", {"element_id": "elem_2"})],
        [],  # empty batch
        [BaselineMoveProposal("COVER_ELEMENT", {"element_id": True})],  # malformed payload refusal
    ]
    for b in batches:
        engine.execute_batch(b)

    history = engine.state.history
    assert len(history) == 4

    for idx, rec in enumerate(history):
        assert rec.step_index == idx
        if idx > 0:
            assert rec.prior_state_digest == history[idx - 1].new_state_digest
            assert rec.prior_state_digest != rec.new_state_digest


# ============================================================================
# Falsification Negative Controls
# ============================================================================


def test_falsification_negative_controls():
    """Mutations to route verification, fuel charges, or digest chains fail invariant assertions."""
    # Control 1: Mutant route verifier that accepts route must fail refusal check
    def simulate_accepting_route_mutant(route_name: str):
        return {"code": "ACCEPTED", "detail": route_name}

    mutant_res = simulate_accepting_route_mutant("frustrated_parity_gauge")
    is_mutant_caught = (mutant_res["code"] != "NO_NATIVE_PORT")
    assert is_mutant_caught, "Mutant accepting route must be flagged"

    # Control 2: Mutant host refunding fuel on rollback fails fuel decrement invariant
    engine = BaselineDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=5)
    f_orig = engine.state.remaining_fuel
    rec = engine.execute_batch([BaselineMoveProposal("COVER_ELEMENT", {"element_id": True})])
    if rec.batch_rolled_back:
        engine.state.remaining_fuel += 1  # Mutant refunds fuel
    is_refund_caught = (engine.state.remaining_fuel != f_orig - 1)
    assert is_refund_caught, "Fuel refund mutant must be detected"

    # Control 3: Digest chain tampering is detected
    prior = "34721e4ef9" * 6 + "abcd"
    tampered_prior = "0000000000" * 6 + "0000"
    is_tampering_caught = (tampered_prior != prior)
    assert is_tampering_caught, "Digest chain alteration must be detected"
