"""Tests for StructureBench exact terminal parsing and linear gate-incidence audit.

Verifies:
1. Exact typed terminal token parsing (no substring or float matching).
2. Exact linear gate-incidence audit calling native lggr_soundness via FFI.
3. Unsoundness witness detection when gate coverage is deficient.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from omega_engine_operads.structurebench import (
    BUNDLE_FILES,
    CONSTRAINT_IDS,
    VALID_TERMINAL_VERDICTS,
    ConstraintOutcome,
    ConstraintResult,
    GateIncidenceAuditReport,
    StructureBenchEvaluator,
    StructureBenchReport,
    audit_gate_incidence,
    build_gate_incidence_matrix,
)


def _write_minimal_bundle(
    tmp_path: Path,
    terminal_verdict: str = "COMPOSTED",
    terminal_phi1: int | float | str = 0,
    terminal_gamma2: int | float | str = 0,
    novella_header_prefix: str = "##",
) -> Path:
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    summary_data = {
        "task_key": "test_task",
        "receipt_id": "r_123",
        "selected_candidate_id": "c_456",
        "terminal_verdict": terminal_verdict,
    }
    (bundle_dir / "summary.json").write_text(
        json.dumps(summary_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    novella_lines = [
        f"{novella_header_prefix} Act I: The Beginning",
        "Scene 1 content at 2026-09-26T00:00:00Z",
        f"{novella_header_prefix} Act II: Debate",
        f"{novella_header_prefix} Act III: Sieve",
        f"{novella_header_prefix} Act IV: Trial",
        f"{novella_header_prefix} Act V: Verdict",
        f"{novella_header_prefix} Act VI: Report",
        f"{novella_header_prefix} Act VII: Resolution",
        "Terminal resolution turns.",
    ]
    (bundle_dir / "novella.md").write_text("\n".join(novella_lines) + "\n", encoding="utf-8")

    dda_lines = [
        json.dumps({"step": 1, "timestamp": "2026-09-26T00:00:00Z", "phi_1": 1, "gamma_2": 1}, sort_keys=True),
        json.dumps({"step": 2, "timestamp": "2026-09-26T00:00:00Z", "phi_1": terminal_phi1, "gamma_2": terminal_gamma2}, sort_keys=True),
    ]
    (bundle_dir / "dda_actions.jsonl").write_text("\n".join(dda_lines) + "\n", encoding="utf-8")

    import hashlib
    receipt_data = {
        "task_key": "test_task",
        "receipt_id": "r_123",
        "selected_candidate_id": "c_456",
        "summary_sha256": hashlib.sha256((bundle_dir / "summary.json").read_bytes()).hexdigest(),
        "novella_sha256": hashlib.sha256((bundle_dir / "novella.md").read_bytes()).hexdigest(),
        "dda_actions_sha256": hashlib.sha256((bundle_dir / "dda_actions.jsonl").read_bytes()).hexdigest(),
        "lean4_proof_hash": "a" * 64,
    }
    (bundle_dir / "receipt.json").write_text(
        json.dumps(receipt_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return bundle_dir


def test_gate_incidence_matrix_shape_and_content():
    gates, artifacts, matrix = build_gate_incidence_matrix()
    assert gates == CONSTRAINT_IDS
    assert artifacts == BUNDLE_FILES
    assert len(matrix) == 11
    for row in matrix:
        assert len(row) == 4
        assert all(cell in ("0", "1") for cell in row)


def test_audit_gate_incidence_sound_on_full_coverage():
    audit = audit_gate_incidence()
    assert isinstance(audit, GateIncidenceAuditReport)
    assert audit.sound is True
    assert audit.d_rank == 3
    assert audit.qd_rank == 3
    assert audit.witness is None
    assert audit.authority_effect == "None"


def test_audit_gate_incidence_detects_unsoundness_with_witness():
    # Build a synthetic report where every gate that touches novella.md is UNVERIFIABLE
    novella_touching = {
        "C1_FILES_PRESENT",
        "C1_UTF8_NO_BOM",
        "C2_HASH_BINDING",
        "C2_NOVELLA_ACTION_BIJECTION",
        "C3_ACT_SECTIONS_PRESENT",
        "C3_NO_TRUNCATION_MARKERS",
        "C3_PASS_TO_MASTER_OBLIGATIONS",
    }
    results = []
    for cid in CONSTRAINT_IDS:
        outcome = (
            ConstraintOutcome.UNVERIFIABLE
            if cid in novella_touching
            else ConstraintOutcome.SATISFIED
        )
        results.append(ConstraintResult(cid, outcome, f"{cid} evaluated"))
    report = StructureBenchReport(results=tuple(results))

    audit = audit_gate_incidence(report)
    assert audit.sound is False
    assert audit.d_rank == 3
    assert audit.qd_rank == 2
    # Witness vector v has D v != 0 and Q D v = 0.
    # Column 1 corresponds to novella.md: ('receipt.json', 'novella.md', 'dda_actions.jsonl', 'summary.json')
    assert audit.witness == ("0", "1", "0", "0")
    assert audit.authority_effect == "None"


def test_terminal_verdict_requires_typed_token(tmp_path: Path):
    # Untyped substring 'PASS' should be violated
    bundle = _write_minimal_bundle(tmp_path, terminal_verdict="PASS")
    evaluator = StructureBenchEvaluator(bundle)
    res = evaluator._c3_pass_to_master()
    assert res.outcome is ConstraintOutcome.VIOLATED
    assert "not a valid typed token" in res.detail

    # Valid tokens. Only PASS_TO_MASTER carries obligations; for every other
    # verdict the constraint holds vacuously and is NOT_APPLICABLE, not
    # SATISFIED (this test used to require SATISFIED, which counted the vacuous
    # case as a decided pass).
    for token in VALID_TERMINAL_VERDICTS:
        bundle_v = _write_minimal_bundle(tmp_path / token, terminal_verdict=token)
        ev = StructureBenchEvaluator(bundle_v)
        res_v = ev._c3_pass_to_master()
        expected = (
            ConstraintOutcome.SATISFIED
            if token == "PASS_TO_MASTER"
            else ConstraintOutcome.NOT_APPLICABLE
        )
        assert res_v.outcome is expected


def test_terminal_step_phi1_gamma2_rejects_floats(tmp_path: Path):
    # Float phi_1 = 0.0 must be rejected
    bundle_float = _write_minimal_bundle(
        tmp_path / "float",
        terminal_verdict="PASS_TO_MASTER",
        terminal_phi1=0.0,
        terminal_gamma2=0,
    )
    ev_float = StructureBenchEvaluator(bundle_float)
    res_float = ev_float._c3_pass_to_master()
    assert res_float.outcome is ConstraintOutcome.VIOLATED
    assert "terminal step has float values" in res_float.detail

    # Exact integer 0 must pass
    bundle_exact = _write_minimal_bundle(
        tmp_path / "exact",
        terminal_verdict="PASS_TO_MASTER",
        terminal_phi1=0,
        terminal_gamma2=0,
    )
    ev_exact = StructureBenchEvaluator(bundle_exact)
    res_exact = ev_exact._c3_pass_to_master()
    assert res_exact.outcome is ConstraintOutcome.SATISFIED
