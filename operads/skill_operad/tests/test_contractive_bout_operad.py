"""Test Contractive Non-Zero Obstruction Bout and Operad Signature Verification.

Verifies:
1. Execution and ingestion of a contractive non-zero obstruction bout
   (Phi_1 > 0 -> 0 < Phi_{1,term} < Phi_{1,init}, Delta_T < Delta_0).
2. DdcOperadParser verification of DDC candidate runtime laws (including Law 7:
   Exact Repair Monotonicity).
3. Classification of the trace as strictly "residual_contractive" (never "exact"
   and never "residual_non_contractive").
4. Refusal of false exactness claims in operad_signature.json:
   - Refusal when claimed_residual_effect is "exact".
   - Refusal when expected_residual_effect is "exact".
   - Refusal when expected_residual_effect is "residual_non_contractive".
5. Successful registration and evidence tracing of honest "residual_contractive"
   morphisms into operad_signature.json and evidence_trace.json.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest
from omega_engine_operads.skill_operad.ddc_operad_parser import (
    DdcOperadParser,
    OperadCompositionReceipt,
)


def _build_hash_chained_ddc_tape(steps_payload: list[dict]) -> list[dict]:
    """Helper generating a cryptographically valid hash-chained DDC action tape."""
    tape = []
    head: str | None = None
    for seq, payload in enumerate(steps_payload):
        sorted_payload = {
            k: payload[k] for k in sorted(payload.keys(), key=lambda key: key.encode("utf-8"))
        }
        material = json.dumps(
            {"sequence": seq, "parent_sha256": head, "payload": sorted_payload},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        rec_sha = hashlib.sha256(material).hexdigest()
        tape.append({
            "sequence": seq,
            "parent_sha256": head,
            "payload": sorted_payload,
            "record_sha256": rec_sha,
        })
        head = rec_sha
    return tape


@pytest.fixture
def contractive_ddc_tape_file(tmp_path: Path) -> Path:
    """Create a DDC action tape representing a contractive non-zero bout.

    Initial obstruction: Phi_1 = 4, Gamma_2 = 0 (Total = 4).
    Terminal obstruction after Exact Repair E: Phi_1 = 1, Gamma_2 = 0 (Total = 1).
    Contraction delta: Delta = 1 - 4 = -3 < 0.
    Terminal obstruction remains non-zero: Delta_T = 1 != 0.
    """
    records = _build_hash_chained_ddc_tape([
        {
            "letter": "C",
            "before_class": "Uninitialized",
            "after_class": "CarrierExposed",
            "carrier_hash": "sha256:carrier_contractive_base",
            "witness_hash": "sha256:w_carrier",
            "phi_1": "4",
            "gamma_2": "0",
            "receipt_sha256": "sha256:r0",
            "timestamp": "2026-10-03T05:00:00Z",
        },
        {
            "letter": "R",
            "before_class": "CarrierExposed",
            "after_class": "ObstructionIdentified",
            "carrier_hash": "sha256:carrier_contractive_base",
            "witness_hash": "sha256:w_initial_obs",
            "phi_1": "4",
            "gamma_2": "0",
            "receipt_sha256": "sha256:r1",
            "timestamp": "2026-10-03T05:01:00Z",
        },
        {
            "letter": "D",
            "before_class": "ObstructionIdentified",
            "after_class": "AdjointDeformed",
            "carrier_hash": "sha256:carrier_contractive_base",
            "witness_hash": "sha256:w_variation",
            "phi_1": "4",
            "gamma_2": "0",
            "receipt_sha256": "sha256:r2",
            "timestamp": "2026-10-03T05:02:00Z",
        },
        {
            "letter": "E",
            "before_class": "AdjointDeformed",
            "after_class": "ExactRepaired",
            "carrier_hash": "sha256:carrier_contractive_base",
            "witness_hash": "sha256:w_exact_retraction",
            "phi_1": "1",
            "gamma_2": "0",
            "receipt_sha256": "sha256:r3",
            "timestamp": "2026-10-03T05:03:00Z",
        },
        {
            "letter": "I",
            "before_class": "ExactRepaired",
            "after_class": "LedgerIntegrated",
            "carrier_hash": "sha256:carrier_contractive_base",
            "witness_hash": "sha256:w_ledger",
            "phi_1": "1",
            "gamma_2": "0",
            "receipt_sha256": "sha256:r4",
            "timestamp": "2026-10-03T05:04:00Z",
        },
        {
            "letter": "T",
            "before_class": "LedgerIntegrated",
            "after_class": "TerminalVerdict",
            "carrier_hash": "sha256:carrier_contractive_base",
            "witness_hash": "sha256:w_terminal",
            "phi_1": "1",
            "gamma_2": "0",
            "receipt_sha256": "sha256:r5",
            "timestamp": "2026-10-03T05:05:00Z",
        },
    ])

    tape_path = tmp_path / "contractive_ddc.jsonl"
    with open(tape_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return tape_path


def test_contractive_bout_classification(contractive_ddc_tape_file: Path) -> None:
    """Verify that DdcOperadParser strictly classifies a contractive non-zero bout."""
    parser = DdcOperadParser(contractive_ddc_tape_file)
    res = parser.parse()
    assert res.is_ok, f"Parser failed: {res.unwrap_err()}"

    receipt: OperadCompositionReceipt = res.unwrap()
    assert receipt.hash_chain_valid is True
    assert receipt.ddc_laws_valid is True
    assert len(receipt.law_violations) == 0

    # Residual verification
    assert receipt.initial_phi1 == "4"
    assert receipt.initial_gamma2 == "0"
    assert receipt.initial_residual == "4"

    assert receipt.terminal_phi1 == "1"
    assert receipt.terminal_gamma2 == "0"
    assert receipt.terminal_residual == "1"

    assert receipt.residual_delta == "-3"
    assert receipt.residual_effect == "residual_contractive"
    assert receipt.residual_effect != "exact"
    assert receipt.residual_effect != "residual_non_contractive"


def test_contractive_bout_signature_refusal_of_false_exactness(
    contractive_ddc_tape_file: Path, tmp_path: Path
) -> None:
    """Verify that DdcOperadParser refuses false exactness claims for contractive non-zero bouts."""
    repo_root = Path(__file__).resolve().parents[3]
    operad_orig_dir = repo_root / "omega_engine_operads" / "skill_operad"

    # Set up sandbox operad directory
    tmp_json = tmp_path / "json"
    tmp_json.mkdir(parents=True, exist_ok=True)
    sig_orig = operad_orig_dir / "json" / "operad_signature.json"
    comp_orig = operad_orig_dir / "json" / "composition_matrix.json"
    slices_orig = operad_orig_dir / "json" / "agent_capability_slices.json"

    (tmp_json / "operad_signature.json").write_text(sig_orig.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_json / "composition_matrix.json").write_text(comp_orig.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_json / "agent_capability_slices.json").write_text(slices_orig.read_text(encoding="utf-8"), encoding="utf-8")

    parser = DdcOperadParser(contractive_ddc_tape_file)

    # 1. Refusal when caller explicitly claims 'exact' on a contractive non-zero run
    false_exact_res = parser.compress_to_operad_signature(
        skill_id="test-contractive-false-exact",
        skill_name="Test False Exact Contractive Op",
        claimed_residual_effect="exact",
        operad_dir=tmp_path,
        apply_changes=False,
    )
    assert false_exact_res.is_err
    refusal = false_exact_res.unwrap_err()
    assert refusal.code == "FALSE_EXACTNESS_CLAIM"
    assert "measured terminal residual is 1 != 0" in refusal.message
    assert "actual measured effect is 'residual_contractive'" in refusal.message

    # 2. Refusal when caller declares expected_residual_effect="exact"
    mismatch_exact_res = parser.compress_to_operad_signature(
        skill_id="test-contractive-mismatch",
        skill_name="Test Mismatch Op",
        expected_residual_effect="exact",
        operad_dir=tmp_path,
        apply_changes=False,
    )
    assert mismatch_exact_res.is_err
    assert mismatch_exact_res.unwrap_err().code == "RESIDUAL_EFFECT_MISMATCH"

    # 3. Refusal when caller expects "residual_non_contractive" on a contractive run
    mismatch_noncontract_res = parser.compress_to_operad_signature(
        skill_id="test-contractive-mismatch-2",
        skill_name="Test Mismatch Op 2",
        expected_residual_effect="residual_non_contractive",
        operad_dir=tmp_path,
        apply_changes=False,
    )
    assert mismatch_noncontract_res.is_err
    assert mismatch_noncontract_res.unwrap_err().code == "RESIDUAL_EFFECT_MISMATCH"

    # 4. Refusal when updating an existing exact operation without allow_downgrade
    sig_data = json.loads((tmp_json / "operad_signature.json").read_text(encoding="utf-8"))
    sig_data["operations"].append({
        "skill_id": "test-existing-exact-target",
        "name": "Existing Exact Target",
        "arity": 2,
        "source_colours": ["Contract", "State"],
        "target_colour": "Receipt",
        "residual_effect": "exact",
        "description": "Pre-existing verified exact operation",
    })
    (tmp_json / "operad_signature.json").write_text(json.dumps(sig_data, indent=2) + "\n", encoding="utf-8")

    downgrade_refusal_res = parser.compress_to_operad_signature(
        skill_id="test-existing-exact-target",
        skill_name="Existing Exact Target",
        operad_dir=tmp_path,
        apply_changes=False,
        allow_downgrade=False,
    )
    assert downgrade_refusal_res.is_err
    assert downgrade_refusal_res.unwrap_err().code == "FALSE_EXACTNESS_CLAIM"


def test_contractive_bout_honest_registration(
    contractive_ddc_tape_file: Path, tmp_path: Path
) -> None:
    """Verify that honest registration of residual_contractive updates operad_signature.json."""
    repo_root = Path(__file__).resolve().parents[3]
    operad_orig_dir = repo_root / "omega_engine_operads" / "skill_operad"

    # Set up sandbox operad directory
    tmp_json = tmp_path / "json"
    tmp_json.mkdir(parents=True, exist_ok=True)
    sig_orig = operad_orig_dir / "json" / "operad_signature.json"
    comp_orig = operad_orig_dir / "json" / "composition_matrix.json"
    slices_orig = operad_orig_dir / "json" / "agent_capability_slices.json"

    (tmp_json / "operad_signature.json").write_text(sig_orig.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_json / "composition_matrix.json").write_text(comp_orig.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_json / "agent_capability_slices.json").write_text(slices_orig.read_text(encoding="utf-8"), encoding="utf-8")

    parser = DdcOperadParser(contractive_ddc_tape_file)

    # Honest registration
    honest_res = parser.compress_to_operad_signature(
        skill_id="foc-006-contractive-dsl-spec",
        skill_name="Contractive Obstruction Calculus Specification",
        source_colours=("Contract", "State"),
        target_colour="Receipt",
        description="Measured contractive residual cochain transition",
        operad_dir=tmp_path,
        expected_residual_effect="residual_contractive",
        apply_changes=True,
    )
    assert honest_res.is_ok, f"Honest registration failed: {honest_res.unwrap_err()}"
    res_data = honest_res.unwrap()

    assert res_data["skill_id"] == "foc-006-contractive-dsl-spec"
    assert res_data["residual_effect"] == "residual_contractive"
    assert "compression_report" in res_data

    # Verify operad_signature.json on disk
    updated_sig = json.loads((tmp_json / "operad_signature.json").read_text(encoding="utf-8"))
    found_op = next(
        (op for op in updated_sig["operations"] if op["skill_id"] == "foc-006-contractive-dsl-spec"),
        None,
    )
    assert found_op is not None
    assert found_op["residual_effect"] == "residual_contractive"
    assert found_op["name"] == "Contractive Obstruction Calculus Specification"

    # Verify evidence_trace.json on disk
    evidence_file = tmp_json / "evidence_trace.json"
    assert evidence_file.is_file()
    traces = json.loads(evidence_file.read_text(encoding="utf-8"))
    found_trace = next(
        (t for t in traces if t["skill_id"] == "foc-006-contractive-dsl-spec"),
        None,
    )
    assert found_trace is not None
    assert found_trace["phi_before"] == 4.0
    assert found_trace["phi_after"] == 1.0
