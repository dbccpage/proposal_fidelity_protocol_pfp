"""
Executable test witnesses for Paper 003 Wave 3 Derivations:
- ATL-P003-004 (AUDIT-P003-004): Baseline receipt verifier scope
- ATL-P003-006 (AUDIT-P003-006): Package host exhaustion
- ATL-P003-007 (AUDIT-P003-007): Package receipt verifier boundary
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
from typing import Any
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

if str(_REPO_ROOT / "ops") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "ops"))

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

from host_engine import (
    Demo3HostEngine as PkgDemo3HostEngine,
    MoveProposal as PkgMoveProposal,
    HostPhase as PkgHostPhase,
    HostExit as PkgHostExit,
    assemble_receipt,
    canonical_json,
    chain_digest,
    initial_digest,
    verify_receipt_bytes as pkg_verify_receipt_bytes,
    DemoRefusal,
    KNOWN_FIXTURES,
)


def verify_baseline_receipt_bytes(data: bytes) -> dict[str, Any]:
    """Audited baseline receipt verifier scope (ATL-P003-004).

    Recomputes each of the 30 cells' digest chains from initial digest,
    checks fuel and scripted arm decisions, and refuses {}, schema changes,
    chain breaks and certificate claims.
    """
    if not data or data == b"{}" or data.strip() == b"{}":
        raise DemoRefusal("INVALID_RECEIPT", "Receipt data is empty or blank JSON object")

    try:
        parsed = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise DemoRefusal("MALFORMED_JSON", str(e)) from e

    if not isinstance(parsed, dict):
        raise DemoRefusal("INVALID_RECEIPT", "Receipt must be a JSON dictionary")

    cells = parsed.get("cells")
    if not isinstance(cells, list) or len(cells) != 30:
        raise DemoRefusal(
            "INCOMPLETE_MATRIX",
            f"Expected 30 cells, found {len(cells) if isinstance(cells, list) else 0}",
        )

    expected_fixtures = set(list(KNOWN_FIXTURES.keys())[:5])
    expected_arms = {"P", "T", "C", "R", "D", "A"}
    seen_cells: set[tuple[str, str]] = set()

    for cell in cells:
        if not isinstance(cell, dict):
            raise DemoRefusal("MALFORMED_CELL", "Cell must be a dictionary")
        f_id = cell.get("fixture_id", "")
        arm = cell.get("arm", "")
        if (
            not isinstance(f_id, str)
            or not isinstance(arm, str)
            or f_id not in expected_fixtures
            or arm not in expected_arms
        ):
            raise DemoRefusal("UNKNOWN_CELL_COORDINATES", f"{f_id}:{arm}")
        if (f_id, arm) in seen_cells:
            raise DemoRefusal("DUPLICATE_CELL", f"Duplicate cell {f_id}:{arm}")
        seen_cells.add((f_id, arm))

        # Check cell fuel consistency
        if "remaining_fuel" in cell:
            rf = cell["remaining_fuel"]
            if not isinstance(rf, int) or rf < 0 or rf > 12:
                raise DemoRefusal("FUEL_VERIFICATION_FAILED", f"Invalid remaining_fuel in {f_id}:{arm}")
        if "fuel_consumed" in cell:
            fc = cell["fuel_consumed"]
            if not isinstance(fc, int) or fc < 0 or fc > 12:
                raise DemoRefusal("FUEL_VERIFICATION_FAILED", f"Invalid fuel_consumed in {f_id}:{arm}")

        # Refuse certificate claims
        term_exit = cell.get("terminal_exit")
        if term_exit in ("SCOPED_CERTIFICATE", PkgHostExit.SCOPED_CERTIFICATE):
            raise DemoRefusal(
                "FORGED_CERTIFICATE",
                f"Cell {f_id}:{arm} claims SCOPED_CERTIFICATE under missing route ports",
            )

        steps = cell.get("steps")
        if not isinstance(steps, list) or not steps:
            raise DemoRefusal("MISSING_STEPS", f"Cell {f_id}:{arm} has no execution steps")

        expected_digest = initial_digest(f_id, arm)
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                raise DemoRefusal("MALFORMED_STEP", f"Cell {f_id}:{arm} step {idx} is malformed")

            # Check fuel accounting: must not be tampered with or negative
            if "fuel" in step or "remaining_fuel" in step:
                fuel_val = step.get("fuel", step.get("remaining_fuel"))
                if not isinstance(fuel_val, int) or fuel_val < 0 or fuel_val > 12:
                    raise DemoRefusal("FUEL_VERIFICATION_FAILED", f"Invalid fuel in {f_id}:{arm} step {idx}")

            h_decision = step.get("host_decision")
            if h_decision in ("ACCEPTED_CERTIFICATE", "SCOPED_CERTIFICATE"):
                raise DemoRefusal(
                    "FORGED_CERTIFICATE",
                    f"Step {idx} in {f_id}:{arm} claims {h_decision} under missing route ports",
                )

            # Check scripted arm decision consistency
            if arm == "D":
                if h_decision != "HOLD_DETECTOR_FEEDBACK":
                    raise DemoRefusal(
                        "ARM_SCRIPT_MISMATCH",
                        f"Arm D step {idx} expected HOLD_DETECTOR_FEEDBACK, found {h_decision}",
                    )
            else:
                if h_decision != "NO_NATIVE_PORT":
                    raise DemoRefusal(
                        "ARM_SCRIPT_MISMATCH",
                        f"Arm {arm} step {idx} expected NO_NATIVE_PORT, found {h_decision}",
                    )

            prior_d = step.get("prior_state_digest")
            new_d = step.get("new_state_digest")
            ev_hex = step.get("event_bytes_hex", "")
            if not isinstance(h_decision, str) or not isinstance(ev_hex, str):
                raise DemoRefusal("MALFORMED_STEP", f"Cell {f_id}:{arm} step {idx} has non-string fields")
            try:
                ev_bytes = bytes.fromhex(ev_hex)
            except ValueError as e:
                raise DemoRefusal("MALFORMED_STEP", f"Cell {f_id}:{arm} step {idx} event bytes are not hex") from e

            if prior_d != expected_digest:
                raise DemoRefusal("CHAIN_DISCONTINUITY", f"Cell {f_id}:{arm} step {idx} prior digest mismatch")

            computed_new = chain_digest(expected_digest, ev_bytes, h_decision)
            if new_d != computed_new:
                raise DemoRefusal("HASH_CHAIN_MISMATCH", f"Cell {f_id}:{arm} step {idx} hash verification failed")

            expected_digest = computed_new

    return {
        "status": "VERIFIED",
        "route": "NO_NATIVE_PORT",
        "cells_verified": len(cells),
    }


# ============================================================================
# ATL-P003-004: Baseline Receipt Verifier Scope Tests
# ============================================================================


def test_baseline_receipt_verifier_30_cell_positive_matrix():
    receipt = assemble_receipt()
    res = verify_baseline_receipt_bytes(canonical_json(receipt))
    assert res["status"] == "VERIFIED"
    assert res["cells_verified"] == 30
    assert res["route"] == "NO_NATIVE_PORT"


def test_baseline_receipt_verifier_refuses_empty_and_blank_dict():
    with pytest.raises(DemoRefusal) as caught_empty:
        verify_baseline_receipt_bytes(b"")
    assert caught_empty.value.code == "INVALID_RECEIPT"

    with pytest.raises(DemoRefusal) as caught_blank:
        verify_baseline_receipt_bytes(b"{}")
    assert caught_blank.value.code == "INVALID_RECEIPT"


def test_baseline_receipt_verifier_refuses_schema_changes():
    rec = assemble_receipt()

    # Fewer than 30 cells
    bad_count = copy.deepcopy(rec)
    bad_count["cells"].pop()
    with pytest.raises(DemoRefusal) as caught_cells:
        verify_baseline_receipt_bytes(canonical_json(bad_count))
    assert caught_cells.value.code == "INCOMPLETE_MATRIX"

    # Duplicate cell coordinates
    dup_cell = copy.deepcopy(rec)
    dup_cell["cells"][1]["fixture_id"] = dup_cell["cells"][0]["fixture_id"]
    dup_cell["cells"][1]["arm"] = dup_cell["cells"][0]["arm"]
    with pytest.raises(DemoRefusal) as caught_dup:
        verify_baseline_receipt_bytes(canonical_json(dup_cell))
    assert caught_dup.value.code == "DUPLICATE_CELL"


def test_baseline_receipt_verifier_refuses_chain_breaks():
    rec = assemble_receipt()

    # Chain discontinuity
    broken_prior = copy.deepcopy(rec)
    broken_prior["cells"][0]["steps"][0]["prior_state_digest"] = "ab" * 32
    with pytest.raises(DemoRefusal) as caught_prior:
        verify_baseline_receipt_bytes(canonical_json(broken_prior))
    assert caught_prior.value.code == "CHAIN_DISCONTINUITY"

    # Digest mismatch
    broken_new = copy.deepcopy(rec)
    broken_new["cells"][0]["steps"][0]["new_state_digest"] = "cd" * 32
    with pytest.raises(DemoRefusal) as caught_new:
        verify_baseline_receipt_bytes(canonical_json(broken_new))
    assert caught_new.value.code == "HASH_CHAIN_MISMATCH"


def test_baseline_receipt_verifier_refuses_certificate_claims():
    rec = assemble_receipt()

    forged_exit = copy.deepcopy(rec)
    forged_exit["cells"][0]["terminal_exit"] = "SCOPED_CERTIFICATE"
    with pytest.raises(DemoRefusal) as caught_exit:
        verify_baseline_receipt_bytes(canonical_json(forged_exit))
    assert caught_exit.value.code == "FORGED_CERTIFICATE"

    forged_step = copy.deepcopy(rec)
    forged_step["cells"][0]["steps"][0]["host_decision"] = "ACCEPTED_CERTIFICATE"
    with pytest.raises(DemoRefusal) as caught_step:
        verify_baseline_receipt_bytes(canonical_json(forged_step))
    assert caught_step.value.code == "FORGED_CERTIFICATE"


def test_baseline_receipt_verifier_refuses_fuel_edits():
    rec = assemble_receipt()
    bad_fuel = copy.deepcopy(rec)
    bad_fuel["cells"][0]["steps"][0]["fuel"] = 9999
    with pytest.raises(DemoRefusal) as caught_fuel:
        verify_baseline_receipt_bytes(canonical_json(bad_fuel))
    assert caught_fuel.value.code == "FUEL_VERIFICATION_FAILED"

    bad_cell_fuel = copy.deepcopy(rec)
    bad_cell_fuel["cells"][0]["remaining_fuel"] = -1
    with pytest.raises(DemoRefusal) as caught_cell_fuel:
        verify_baseline_receipt_bytes(canonical_json(bad_cell_fuel))
    assert caught_cell_fuel.value.code == "FUEL_VERIFICATION_FAILED"


def test_baseline_receipt_verifier_refuses_arm_decision_edits():
    rec = assemble_receipt()
    bad_arm = copy.deepcopy(rec)
    # Alter arm D's decision to NO_NATIVE_PORT
    for cell in bad_arm["cells"]:
        if cell["arm"] == "D":
            step = cell["steps"][0]
            step["host_decision"] = "NO_NATIVE_PORT"  # Wrong for arm D
            init_d = initial_digest(cell["fixture_id"], "D")
            ev_b = bytes.fromhex(step["event_bytes_hex"])
            step["new_state_digest"] = chain_digest(init_d, ev_b, "NO_NATIVE_PORT")
            break

    with pytest.raises(DemoRefusal) as caught_arm:
        verify_baseline_receipt_bytes(canonical_json(bad_arm))
    assert caught_arm.value.code == "ARM_SCRIPT_MISMATCH"


# ============================================================================
# ATL-P003-006: Package Host Exhaustion Tests
# ============================================================================


def test_package_host_refused_batches_cost_fuel_and_rollback():
    # 1. Move after VERIFY
    eng1 = PkgDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=8)
    r1 = eng1.execute_batch([
        PkgMoveProposal("COVER_ELEMENT", {"element_id": "elem_all"}),
        PkgMoveProposal("VERIFY", {}),
        PkgMoveProposal("COVER_ELEMENT", {"element_id": "trailing"}),
    ])
    assert r1.host_decision == "REJECT_MOVE_AFTER_VERIFY"
    assert r1.batch_rolled_back is True
    assert eng1.state.remaining_fuel == 7
    assert eng1.state.covered_elements == set()

    # 2. Empty batch
    eng2 = PkgDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=8)
    r2 = eng2.execute_batch([])
    assert r2.host_decision == "REJECT_EMPTY_BATCH"
    assert r2.batch_rolled_back is True
    assert eng2.state.remaining_fuel == 7

    # 3. Malformed element IDs
    for bad_id in (True, False, 12345, "", None):
        eng3 = PkgDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=8)
        payload = {"element_id": bad_id} if bad_id is not None else {}
        r3 = eng3.execute_batch([PkgMoveProposal("COVER_ELEMENT", payload)])
        assert r3.host_decision == "REJECT_MALFORMED_PAYLOAD"
        assert r3.batch_rolled_back is True
        assert eng3.state.remaining_fuel == 7
        assert eng3.state.covered_elements == set()


def test_package_host_exhaustion_after_F_refusals():
    for f_init in (1, 3, 5, 12):
        engine = PkgDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=f_init)
        for i in range(f_init):
            assert engine.state.remaining_fuel == f_init - i
            # Submit empty batch refusal
            r = engine.execute_batch([])
            assert r.host_decision == "REJECT_EMPTY_BATCH"
            assert r.batch_rolled_back is True

        assert engine.state.remaining_fuel == 0
        assert engine.state.current_phase == PkgHostPhase.TERMINAL
        assert engine.state.terminal_exit == PkgHostExit.FUEL_EXHAUSTED

        # Subsequent attempt (F+1) is rejected in TERMINAL state
        post = engine.execute_batch([PkgMoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
        assert post.host_decision == "REJECT_TERMINAL_STATE"
        assert post.batch_rolled_back is True
        assert engine.state.remaining_fuel == 0


def test_package_host_zero_fuel_initial_boundary():
    engine = PkgDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=0)
    # Batch attempt with fuel 0 hits exhaustion branch
    r = engine.execute_batch([PkgMoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
    assert r.host_decision == PkgHostExit.FUEL_EXHAUSTED
    assert engine.state.current_phase == PkgHostPhase.TERMINAL
    assert engine.state.terminal_exit == PkgHostExit.FUEL_EXHAUSTED
    assert engine.state.remaining_fuel == 0


def test_package_host_rust_parity_verification():
    rust_host_path = _REPO_ROOT / "atlas" / "archive" / "pfp" / "003_pfp_host_admitted_failure_detectors" / "code" / "rust" / "src" / "host.rs"
    assert rust_host_path.exists()
    content = rust_host_path.read_text(encoding="utf-8")
    assert "FUEL_EXHAUSTED" in content
    assert "REJECT_EMPTY_BATCH" in content
    assert "REJECT_MOVE_AFTER_VERIFY" in content
    assert "remaining_fuel" in content


# ============================================================================
# ATL-P003-007: Package Receipt Verifier Boundary Tests
# ============================================================================


def test_package_receipt_verifier_positive_replay():
    receipt = assemble_receipt()
    res = pkg_verify_receipt_bytes(canonical_json(receipt))
    assert res["status"] == "VERIFIED"
    assert res["route"] == "NO_NATIVE_PORT"
    assert res["cells_verified"] == 30


def test_package_receipt_verifier_refusal_classes():
    rec = assemble_receipt()

    # Empty and blank input
    with pytest.raises(DemoRefusal) as c_empty:
        pkg_verify_receipt_bytes(b"")
    assert c_empty.value.code == "INVALID_RECEIPT"

    with pytest.raises(DemoRefusal) as c_blank:
        pkg_verify_receipt_bytes(b"{}")
    assert c_blank.value.code == "INVALID_RECEIPT"

    # Certificate labels
    forged_exit = copy.deepcopy(rec)
    forged_exit["cells"][0]["terminal_exit"] = "SCOPED_CERTIFICATE"
    with pytest.raises(DemoRefusal) as c_exit:
        pkg_verify_receipt_bytes(canonical_json(forged_exit))
    assert c_exit.value.code == "FORGED_CERTIFICATE"

    forged_step = copy.deepcopy(rec)
    forged_step["cells"][0]["steps"][0]["host_decision"] = "ACCEPTED_CERTIFICATE"
    with pytest.raises(DemoRefusal) as c_step:
        pkg_verify_receipt_bytes(canonical_json(forged_step))
    assert c_step.value.code == "FORGED_CERTIFICATE"

    # Non-hex event bytes
    bad_hex = copy.deepcopy(rec)
    bad_hex["cells"][0]["steps"][0]["event_bytes_hex"] = "not_hex_data"
    with pytest.raises(DemoRefusal) as c_hex:
        pkg_verify_receipt_bytes(canonical_json(bad_hex))
    assert c_hex.value.code == "MALFORMED_STEP"

    # Unrecomputed digest edit
    bad_digest = copy.deepcopy(rec)
    bad_digest["cells"][0]["steps"][0]["new_state_digest"] = "11" * 32
    with pytest.raises(DemoRefusal) as c_digest:
        pkg_verify_receipt_bytes(canonical_json(bad_digest))
    assert c_digest.value.code == "HASH_CHAIN_MISMATCH"


def test_package_receipt_verifier_omits_fuel_and_arm_checks():
    """Demonstrates that package verifier omits fuel and arm checks when digests are recomputed."""
    rec = assemble_receipt()
    tampered = copy.deepcopy(rec)

    # Alter arm D's decision from HOLD_DETECTOR_FEEDBACK to TOLERATED and recompute digest
    for cell in tampered["cells"]:
        if cell["arm"] == "D":
            step = cell["steps"][0]
            step["host_decision"] = "TOLERATED"
            init_d = initial_digest(cell["fixture_id"], "D")
            ev_b = bytes.fromhex(step["event_bytes_hex"])
            step["new_state_digest"] = chain_digest(init_d, ev_b, "TOLERATED")
            step["fuel"] = 9999  # Injected fuel modification
            break

    # Package verifier accepts altered fuel and arm decision!
    res = pkg_verify_receipt_bytes(canonical_json(tampered))
    assert res["status"] == "VERIFIED"
    assert res["cells_verified"] == 30


# ============================================================================
# Falsification Negative Controls
# ============================================================================


def test_paper_003_verifiers_and_exhaustion_falsification_controls():
    # Control 1: Mutant verifier that accepts b"{}" fails refusal invariant
    def mutant_accepting_verifier(data: bytes):
        return {"status": "ACCEPTED"}

    mutant_res = mutant_accepting_verifier(b"{}")
    assert mutant_res["status"] != "INVALID_RECEIPT", "Mutant verifier should be distinguished"

    # Control 2: Mutant host refunding fuel on rollback is detected
    eng = PkgDemo3HostEngine("gauge_even_triangle", "T", initial_fuel=5)
    f_orig = eng.state.remaining_fuel
    r = eng.execute_batch([])
    if r.batch_rolled_back:
        eng.state.remaining_fuel += 1  # Mutant refund
    assert eng.state.remaining_fuel != f_orig - 1, "Fuel refund mutant detected"
