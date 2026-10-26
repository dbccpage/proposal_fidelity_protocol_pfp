"""Test Degree-Wise DSL Verification Bout and Automatic Operadic Compression.

Verifies:
1. Woland bout execution artifact bundle for degree-wise DSL verification.
2. Exact cochain boundaries on declared C3 triangle carrier (Phi_1 = 0, Gamma_2 = 0).
3. DDC tape hash-chain validation and DDC candidate runtime law compliance.
4. Colored operad morphism compilation and exact residual calculation.
5. Automatic operadic compression into operad_signature.json and trace logging.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from omega_engine_operads.skill_operad.ddc_operad_parser import DdcOperadParser


def _find_verification_run_dir(repo_root: Path) -> Path:
    runs_dir = repo_root / "_ic" / "woland" / "runs"
    matching = sorted(runs_dir.glob("*degree_wise_dsl_verification*"))
    if not matching:
        pytest.skip(f"No verification run directory found matching *degree_wise_dsl_verification* in {runs_dir}")
    return matching[-1]


def test_quad_bundle_and_exact_cochains() -> None:
    """Verify the Woland bout run directory and exact cochains for degree-wise DSL verification."""
    repo_root = Path(__file__).resolve().parents[3]
    run_dir = _find_verification_run_dir(repo_root)

    assert run_dir.is_dir(), f"Run directory not found: {run_dir}"

    receipt_file = run_dir / "receipt.json"
    novella_file = run_dir / "novella.md"
    ddc_file = run_dir / "ddc.jsonl"
    dda_file = run_dir / "dda_actions.jsonl"
    summary_file = run_dir / "summary.json"

    for f in (receipt_file, novella_file, ddc_file, dda_file, summary_file):
        assert f.is_file(), f"Missing Quad Bundle file: {f}"

    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))

    # Assert exact cochain measurements
    assert receipt.get("phi1") == "0", "Phi_1 must be exactly 0 on declared carrier complex"
    assert receipt.get("gamma2") == "0", "Gamma_2 must be exactly 0 on declared carrier complex"
    assert receipt.get("measurement_status") == "MEASURED"
    assert receipt.get("carrier_degree") == 1
    assert receipt.get("authority_effect") == "None"

    # Assert identical dual action tapes (ddc.jsonl and dda_actions.jsonl)
    assert receipt.get("ddc_sha256") == receipt.get("dda_actions_sha256")
    assert ddc_file.read_bytes() == dda_file.read_bytes(), "Dual action stream byte mismatch"


def test_ddc_operad_parsing() -> None:
    """Verify DdcOperadParser validates hash chains, DDC laws, and generates morphisms."""
    repo_root = Path(__file__).resolve().parents[3]
    run_dir = _find_verification_run_dir(repo_root)
    ddc_file = run_dir / "ddc.jsonl"

    parser = DdcOperadParser(ddc_file)
    res = parser.parse()
    assert res.is_ok, f"Parser failed: {res.unwrap_err()}"

    op_receipt = res.unwrap()
    assert op_receipt.hash_chain_valid is True
    assert op_receipt.ddc_laws_valid is True
    assert op_receipt.residual_effect == "exact"
    assert op_receipt.initial_phi1 == "0"
    assert op_receipt.initial_gamma2 == "0"
    assert op_receipt.terminal_phi1 == "0"
    assert op_receipt.terminal_gamma2 == "0"
    assert op_receipt.step_count > 0
    assert op_receipt.morphism_count == op_receipt.step_count
    assert op_receipt.authority_effect == "None"


def test_automatic_operadic_compression(tmp_path: Path) -> None:
    """Verify automatic operadic compression into an operad directory."""
    repo_root = Path(__file__).resolve().parents[3]
    operad_orig_dir = repo_root / "omega_engine_operads" / "skill_operad"
    run_dir = _find_verification_run_dir(repo_root)
    ddc_file = run_dir / "ddc.jsonl"

    # Prepare sandbox operad directory in tmp_path
    tmp_json = tmp_path / "json"
    tmp_json.mkdir(parents=True, exist_ok=True)

    sig_orig = operad_orig_dir / "json" / "operad_signature.json"
    comp_orig = operad_orig_dir / "json" / "composition_matrix.json"
    slices_orig = operad_orig_dir / "json" / "agent_capability_slices.json"

    (tmp_json / "operad_signature.json").write_text(
        sig_orig.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_json / "composition_matrix.json").write_text(
        comp_orig.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_json / "agent_capability_slices.json").write_text(
        slices_orig.read_text(encoding="utf-8"), encoding="utf-8"
    )

    parser = DdcOperadParser(ddc_file)
    comp_res = parser.compress_to_operad_signature(
        skill_id="degree-wise-dsl-verification-test",
        skill_name="Degree-Wise DSL Cochain Verification Test",
        source_colours=("Contract", "State"),
        target_colour="Receipt",
        description="Verified exact residual contraction test",
        operad_dir=tmp_path,
        apply_changes=True,
    )

    assert comp_res.is_ok, f"Compression failed: {comp_res.unwrap_err()}"
    report_data = comp_res.unwrap()
    assert report_data["residual_effect"] == "exact"
    assert report_data["compression_report"]["status"] == "APPLIED_EXPLICITLY"

    # Verify sandbox operad_signature.json updated
    sig_updated = json.loads((tmp_json / "operad_signature.json").read_text(encoding="utf-8"))
    registered = [
        op for op in sig_updated["operations"] if op["skill_id"] == "degree-wise-dsl-verification-test"
    ]
    assert len(registered) == 1
    assert registered[0]["residual_effect"] == "exact"
    assert registered[0]["arity"] == 2
    assert registered[0]["source_colours"] == ["Contract", "State"]
    assert registered[0]["target_colour"] == "Receipt"

    # Verify sandbox evidence_trace.json recorded
    trace_file = tmp_json / "evidence_trace.json"
    assert trace_file.is_file()
    traces = json.loads(trace_file.read_text(encoding="utf-8"))
    assert any(t["skill_id"] == "degree-wise-dsl-verification-test" for t in traces)
