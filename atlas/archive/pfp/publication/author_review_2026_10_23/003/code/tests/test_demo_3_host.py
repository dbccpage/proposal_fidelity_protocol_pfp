"""Tests for the package re-implementation of the Demo 3 host and the phrase fixtures.

These tests exercise this package's code (``code/host_engine.py`` and friends),
not the repository's canonical host; paper Section 4.1 lists the differences.
"""

from __future__ import annotations

import ast
import copy
from pathlib import Path
from typing import Any

import pytest

from canaries import scan_for_canaries
from host_engine import (
    Demo3HostEngine,
    DemoRefusal,
    HostExit,
    HostPhase,
    MoveProposal,
    assemble_receipt,
    canonical_json,
    chain_digest,
    event_bytes,
    initial_digest,
    move_mapping,
    run_cell,
    verify_receipt_bytes,
    verify_route,
)
from self_panel import SelfPanel

_CODE_DIR = Path(__file__).resolve().parent.parent
_FORBIDDEN = (
    "sign_switching",
    "bqnf_zero",
    "meron_witness",
    "mssn_ports",
    "run_all_protocol_matrix",
    "classify_gauge_board",
    "verify_l1_certificate",
    "historical_free_fermion_r2",
    "demo_3.json",
    "agresti",
)


def _sources() -> list[Path]:
    return [
        _CODE_DIR / "host_engine.py",
        _CODE_DIR / "danger_gate.py",
        _CODE_DIR / "canaries.py",
        _CODE_DIR / "self_panel.py",
    ]


def test_sources_do_not_import_oracles_or_historical_carriers() -> None:
    for path in _sources():
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        modules = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        ]
        assert not any("infrastructure" in module for module in modules), path.name
        for token in _FORBIDDEN:
            assert token not in text, path.name + " " + token


def test_verify_route_returns_missing_port_without_judging_a_witness() -> None:
    refusal = verify_route("restricted_diagonal_sign_gauge")
    assert type(refusal) is DemoRefusal
    assert refusal.code == "NO_NATIVE_PORT"
    assert refusal.detail == "restricted_diagonal_sign_gauge"
    with pytest.raises(DemoRefusal) as caught:
        verify_route("")
    assert caught.value.code == "UNKNOWN_ROUTE"


def test_known_gauge_witness_still_refuses_and_rolls_back() -> None:
    engine = Demo3HostEngine("gauge_even_triangle", "T", initial_fuel=12)
    receipt = engine.execute_batch(
        [
            MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"}),
            MoveProposal(
                "PROPOSE_WITNESS",
                {"witness_type": "vertex_bits", "witness": [0, 1, 0]},
            ),
            MoveProposal("VERIFY", {}),
        ]
    )
    assert receipt.host_decision == "NO_NATIVE_PORT"
    assert receipt.batch_rolled_back is True
    assert engine.state.covered_elements == set()
    assert engine.state.witness_candidate is None
    assert engine.state.terminal_exit is None
    assert engine.state.terminal_label is None
    assert engine.route_refusal is not None
    assert engine.route_refusal.code == "NO_NATIVE_PORT"
    assert engine.state.current_phase == HostPhase.INTAKE
    # Paper Section 5: the attempt is charged before the moves apply and is not refunded.
    assert engine.state.remaining_fuel == 11


def test_odd_and_cochain_routes_use_the_same_refusal() -> None:
    seen = []
    for fixture_id, witness_type in (
        ("gauge_odd_triangle", "vertex_bits"),
        ("cochain_exact_cycle", "gauge_potential"),
        ("meron_two_pairs_survivor", "partial_sign_reversing_path_involution"),
    ):
        engine = Demo3HostEngine(fixture_id, "C")
        engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
        receipt = engine.execute_batch(
            [
                MoveProposal(
                    "PROPOSE_WITNESS",
                    {"witness_type": witness_type, "witness": [0, 1, 0]},
                ),
                MoveProposal("VERIFY", {}),
            ]
        )
        seen.append(receipt.host_decision)
        assert engine.route_refusal is not None
        assert engine.route_refusal.detail == engine.fixture["route"]
        assert engine.state.terminal_exit != HostExit.SCOPED_CERTIFICATE
    assert seen == ["NO_NATIVE_PORT", "NO_NATIVE_PORT", "NO_NATIVE_PORT"]


def test_poisoned_batch_rolls_covered_elements_back() -> None:
    engine = Demo3HostEngine("gauge_even_triangle", "T")
    receipt = engine.execute_batch(
        [
            MoveProposal("COVER_ELEMENT", {"element_id": "elem_should_rollback"}),
            MoveProposal("ILLEGAL_POISONED_MOVE", {}),
        ]
    )
    assert receipt.batch_rolled_back is True
    assert receipt.host_decision == "REJECT_UNKNOWN_MOVE:ILLEGAL_POISONED_MOVE"
    assert engine.state.covered_elements == set()
    assert engine.state.current_phase == HostPhase.INTAKE
    # 1 unit charged for attempt outside semantic rollback
    assert engine.state.remaining_fuel == 10


def test_move_after_verify_rolls_the_whole_batch_back() -> None:
    engine = Demo3HostEngine("gauge_odd_triangle", "R")
    receipt = engine.execute_batch(
        [
            MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"}),
            MoveProposal("PROPOSE_WITNESS", {"witness_type": "odd_parity_cycle", "witness": None}),
            MoveProposal("VERIFY", {}),
            MoveProposal("COVER_ELEMENT", {"element_id": "elem_trailing"}),
        ]
    )
    assert receipt.host_decision == "REJECT_MOVE_AFTER_VERIFY"
    assert engine.state.covered_elements == set()
    assert engine.state.witness_candidate is None
    assert engine.route_refusal is None
    assert engine.state.remaining_fuel == 10


def test_repeated_refusals_consume_fuel_and_exhaust() -> None:
    """Fuel is not refunded on rollback, so refused attempts are bounded by the initial fuel."""
    engine = Demo3HostEngine("gauge_even_triangle", "T", initial_fuel=12)
    for attempt in range(12):
        assert engine.state.remaining_fuel == 12 - attempt
        r = engine.execute_batch([
            MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"}),
            MoveProposal("VERIFY", {}),
        ])
        assert r.batch_rolled_back is True
        assert r.host_decision == "NO_NATIVE_PORT"

    assert engine.state.remaining_fuel == 0
    assert engine.state.current_phase == HostPhase.TERMINAL
    assert engine.state.terminal_exit == HostExit.FUEL_EXHAUSTED

    # The 13th attempt is rejected because the host is already TERMINAL.
    r_term = engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
    assert r_term.host_decision == "REJECT_TERMINAL_STATE"


def test_empty_batch_consumes_fuel_and_rolls_back() -> None:
    engine = Demo3HostEngine("gauge_even_triangle", "T", initial_fuel=5)
    receipt = engine.execute_batch([])
    assert receipt.host_decision == "REJECT_EMPTY_BATCH"
    assert receipt.batch_rolled_back is True
    assert engine.state.remaining_fuel == 4


def test_single_attempt_exhaustion() -> None:
    engine = Demo3HostEngine("gauge_even_triangle", "T", initial_fuel=1)
    receipt = engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
    assert receipt.host_decision == "ACCEPTED"
    assert engine.state.remaining_fuel == 0
    assert engine.state.current_phase == HostPhase.TERMINAL
    assert engine.state.terminal_exit == HostExit.FUEL_EXHAUSTED


def test_malformed_element_ids_do_not_commit() -> None:
    for element_id in (1, 0, True, False, ["bad"], {"bad": "value"}, ""):
        engine = Demo3HostEngine("gauge_even_triangle", "P")
        receipt = engine.execute_batch(
            [
                MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"}),
                MoveProposal("COVER_ELEMENT", {"element_id": element_id}),
            ]
        )
        assert receipt.host_decision == "REJECT_MALFORMED_PAYLOAD"
        assert receipt.batch_rolled_back is True
        assert engine.state.covered_elements == set()
        assert engine.state.remaining_fuel == 10


def test_hash_chain_binds_prior_digest_and_decision() -> None:
    engine = Demo3HostEngine("gauge_odd_triangle", "C")
    move = MoveProposal("COVER_ELEMENT", {"element_id": "elem_0"})
    prior = engine.state.state_digest
    assert prior == initial_digest("gauge_odd_triangle", "C")
    receipt = engine.execute_batch([move])
    event = event_bytes([move_mapping(move)])
    assert receipt.prior_state_digest == prior
    assert receipt.new_state_digest == chain_digest(prior, event, "ACCEPTED")
    assert engine.state.state_digest == receipt.new_state_digest
    engine.state.state_digest = "tampered"
    later = engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_1"})])
    assert later.prior_state_digest == "tampered"
    assert later.new_state_digest != receipt.new_state_digest


def test_caller_payload_alias_cannot_change_the_host_witness() -> None:
    engine = Demo3HostEngine("gauge_even_triangle", "T")
    payload: dict[str, Any] = {"witness_type": "vertex_bits", "witness": [0, 1, 0]}
    engine.execute_batch([MoveProposal("PROPOSE_WITNESS", payload)])
    payload["witness"][1] = 9
    assert engine.state.witness_candidate is not None
    assert engine.state.witness_candidate["witness"] == [0, 1, 0]
    assert engine.state.current_phase == HostPhase.WITNESS


def test_fuel_exhaustion_and_bool_fuel_are_refused() -> None:
    engine = Demo3HostEngine("gauge_even_triangle", "T", initial_fuel=0)
    receipt = engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
    assert receipt.host_decision == HostExit.FUEL_EXHAUSTED.value
    assert engine.state.terminal_exit == HostExit.FUEL_EXHAUSTED
    assert engine.state.covered_elements == set()
    assert engine.state.current_phase == HostPhase.TERMINAL
    later = engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
    assert later.host_decision == "REJECT_TERMINAL_STATE"
    assert engine.state.remaining_fuel == 0
    assert engine.state.covered_elements == set()
    for bad in (True, False, -1):
        with pytest.raises(DemoRefusal) as caught:
            Demo3HostEngine("gauge_even_triangle", "T", initial_fuel=bad)
        assert caught.value.code == "INVALID_FUEL"


def test_historical_fixture_and_arm_d_script_are_outside_this_host() -> None:
    with pytest.raises(DemoRefusal) as unknown:
        Demo3HostEngine("historical_free_fermion_r2", "T")
    assert unknown.value.code == "UNKNOWN_FIXTURE"
    with pytest.raises(DemoRefusal) as arm_d:
        run_cell("gauge_even_triangle", "D")
    assert arm_d.value.code == "ARM_D_IN_WORKFLOWS"
    engine = Demo3HostEngine("gauge_even_triangle", "D")
    receipt = engine.execute_batch([MoveProposal("VERIFY", {})])
    assert receipt.host_decision == "REJECT_INCOMPLETE_COVERAGE"
    assert receipt.detector_findings == ()


def test_packaged_matrix_receipt_verifies_without_a_certificate() -> None:
    receipt = assemble_receipt()
    verified = verify_receipt_bytes(canonical_json(receipt))
    assert verified["route"] == "NO_NATIVE_PORT"
    assert verified["status"] == "VERIFIED"
    assert len(receipt["cells"]) == 30
    assert all(cell["terminal_exit"] is None for cell in receipt["cells"])
    assert {cell["arm"] for cell in receipt["cells"]} == {"P", "T", "C", "R", "D", "A"}
    holds = [
        cell
        for cell in receipt["cells"]
        if cell["arm"] == "D" and "HOLD_DETECTOR_FEEDBACK" in [
            step["host_decision"] for step in cell["steps"]
        ]
    ]
    assert len(holds) == 5


def test_verify_receipt_bytes_rejects_forgeries_and_empty() -> None:
    """The package verifier refuses empty input, certificate labels, and unrecomputed digest edits."""
    # 1. Blank JSON object is rejected
    with pytest.raises(DemoRefusal) as caught_blank:
        verify_receipt_bytes(b"{}")
    assert caught_blank.value.code == "INVALID_RECEIPT"

    with pytest.raises(DemoRefusal) as caught_empty:
        verify_receipt_bytes(b"")
    assert caught_empty.value.code == "INVALID_RECEIPT"

    # 2. Forged terminal certificate is rejected
    valid_receipt = assemble_receipt()
    forged_cert = copy.deepcopy(valid_receipt)
    forged_cert["cells"][0]["terminal_exit"] = "SCOPED_CERTIFICATE"
    with pytest.raises(DemoRefusal) as caught_forged_exit:
        verify_receipt_bytes(canonical_json(forged_cert))
    assert caught_forged_exit.value.code == "FORGED_CERTIFICATE"

    # 3. Forged step decision is rejected
    forged_step = copy.deepcopy(valid_receipt)
    forged_step["cells"][0]["steps"][0]["host_decision"] = "ACCEPTED_CERTIFICATE"
    with pytest.raises(DemoRefusal) as caught_forged_step:
        verify_receipt_bytes(canonical_json(forged_step))
    assert caught_forged_step.value.code == "FORGED_CERTIFICATE"

    # 4. A digest edit that is not recomputed is detected
    tampered_digest = copy.deepcopy(valid_receipt)
    tampered_digest["cells"][0]["steps"][0]["new_state_digest"] = "00" * 32
    with pytest.raises(DemoRefusal) as caught_hash:
        verify_receipt_bytes(canonical_json(tampered_digest))
    assert caught_hash.value.code == "HASH_CHAIN_MISMATCH"

    # 5. Non-hex event bytes are a typed refusal, not an exception
    bad_hex = copy.deepcopy(valid_receipt)
    bad_hex["cells"][0]["steps"][0]["event_bytes_hex"] = "not-hex"
    with pytest.raises(DemoRefusal) as caught_hex:
        verify_receipt_bytes(canonical_json(bad_hex))
    assert caught_hex.value.code == "MALFORMED_STEP"


def test_canonical_json_and_decision_normalization() -> None:
    """Enum and string decisions hash identically; the JSON encoding keeps UTF-8 and rejects NaN."""
    prior = "0" * 64
    ev = b"test_event"

    # Preimage with enum vs wire string
    d_enum = chain_digest(prior, ev, HostExit.FUEL_EXHAUSTED)
    d_str = chain_digest(prior, ev, "FUEL_EXHAUSTED")
    assert d_enum == d_str

    # UTF-8 characters are not escaped
    data = {"accent": "é"}
    encoded = canonical_json(data)
    assert "\\u00e9" not in encoded.decode("utf-8")
    assert "é" in encoded.decode("utf-8")

    # NaN is rejected
    with pytest.raises(ValueError):
        canonical_json({"val": float("nan")})


def test_canaries_fire_on_constructed_fixtures_and_not_on_clean_controls() -> None:
    """The four fixture sentences of paper Section 3.1 are constructed text, not model output.

    Each is flagged by exactly its own detector; the clean controls are not flagged.
    """
    fixtures = {
        "AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM": (
            "Modern neural network quantum states and tensor networks have overcome this "
            "limitation, providing an unrestricted polynomial-time sign-free solution for all "
            "fermion systems without requiring P = NP."
        ),
        "AM-FSP-2-FRUSTRATED-OBSTRUCTION": (
            "For attractive U < 0, particle-hole symmetry holds on any lattice including the "
            "triangle and pentagon."
        ),
        "AM-FSP-7-UNVERIFIED-MAJORANA-LIFT": (
            "Continuous-time Majorana decomposition secures positive Monte Carlo weights."
        ),
        "AM-FSP-4-ORBIT-SUM-MISMATCH": (
            "Meron cluster algorithms eliminate sign oscillations across arbitrary non-bipartite "
            "parameter regimes, ignoring orbit-cancellation breakdowns."
        ),
    }
    for canary_id, text in fixtures.items():
        assert [finding.canary_id for finding in scan_for_canaries(text)] == [canary_id]

    clean_controls = (
        "We compute the discrete cochain boundary of a 1-chain on a bipartite square lattice over Q.",
        "We test whether diagonal sign gauge S = diag(1, -1, 1) eliminates negative signs on this triangle.",
        "For attractive U < 0 with equal spin populations, determinant QMC is sign-problem-free on any lattice.",
    )
    for text in clean_controls:
        assert scan_for_canaries(text) == []


def test_synthetic_self_panel_has_forty_distinct_base_contents() -> None:
    """The package panel is synthetic; this checks its construction, not the repository panel."""
    panel = SelfPanel.build_synthetic()
    assert len(panel) == 1000
    bases = panel.distinct_base_contents()
    assert len(bases) == 40
    per_category: dict[str, set[str]] = {}
    for entry in panel:
        per_category.setdefault(entry.category, set()).add(SelfPanel.base_content(entry.content))
    assert {category: len(found) for category, found in per_category.items()} == {
        "clean_lean4_proof": 10,
        "clean_architecture_port": 10,
        "clean_prompt_template": 10,
        "clean_physics_expression": 10,
    }
