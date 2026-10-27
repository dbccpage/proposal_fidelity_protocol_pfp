"""Test Non-Zero Obstruction Bout and False Exactness Refusal.

Verifies:
1. Execution of a Adversary dialectic bout with non-trivial 1-cochains (Phi_1 != 0, Gamma_2 != 0).
2. Verification that DdcOperadParser correctly flags non-exact residual effects
   (residual_contractive or residual_non_contractive) from hash-chained DDC action records.
3. Strict enforcement that DdcOperadParser refuses false exactness claims
   when registering or compressing into operad_signature.json.
4. Correct registration of non-exact residual effect when recorded honestly.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from adversary.domain.models import AdversaryBoutRequestV1
from adversary.runtime import build_adversary_service
from operads.skill_operad.ddc_operad_parser import DdcOperadParser


@pytest.fixture(scope="module")
def nonzero_bout_run_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Execute a non-zero obstruction bout on the C3 triangle carrier and return run dir."""
    repo_root = Path(__file__).resolve().parents[3]
    scratch_dir = tmp_path_factory.mktemp("nonzero_bout_root")

    service = build_adversary_service(repo_root=scratch_dir)

    # Carrier: C3 triangle with non-trivial 1-cochains (all edges = 1, sum around loop = 3 != 0)
    req = AdversaryBoutRequestV1(
        objective="Verify non-zero obstruction bout on C3 triangle carrier",
        task_key="foc_006_nonzero_test_bout",
        carrier_context={
            "nodes": [1, 2, 3],
            "edges": [[1, 2], [2, 3], [3, 1]],
            "faces": [[1, 2, 3]],
            "cochains": {
                "1->2": "1",
                "2->3": "1",
                "3->1": "1",
            },
        },
        max_rounds=2,
        fixture_mode=True,
    )

    outcome_res = service.execute_bout(req)
    assert outcome_res.is_ok, f"Bout failed: {outcome_res.unwrap_err()}"
    outcome = outcome_res.unwrap()

    assert outcome.status == "BOUNDED_RESIDUAL"
    assert outcome.phi1 is not None and outcome.phi1 != "0", f"Phi_1 must be non-zero, got {outcome.phi1}"
    assert outcome.gamma2 is not None and outcome.gamma2 != "0", f"Gamma_2 must be non-zero, got {outcome.gamma2}"
    assert outcome.defect_count == 3
    assert outcome.authority_effect == "None"

    run_dir = Path(outcome.receipt_path).parent
    assert run_dir.is_dir()
    return run_dir


def test_nonzero_bout_quad_bundle_and_measurements(nonzero_bout_run_dir: Path) -> None:
    """Verify that Quad Bundle artifacts are intact and cochains are non-zero."""
    receipt_file = nonzero_bout_run_dir / "receipt.json"
    novella_file = nonzero_bout_run_dir / "novella.md"
    ddc_file = nonzero_bout_run_dir / "ddc.jsonl"
    dda_file = nonzero_bout_run_dir / "dda_actions.jsonl"
    summary_file = nonzero_bout_run_dir / "summary.json"

    for f in (receipt_file, novella_file, ddc_file, dda_file, summary_file):
        assert f.is_file(), f"Missing Quad Bundle file: {f}"

    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt["phi1"] != "0"
    assert receipt["gamma2"] != "0"
    assert receipt["measurement_status"] == "MEASURED"
    assert receipt["defect_count"] > 0
    assert "OPEN_OBSTRUCTION" in receipt["authorization_blockers"]

    # Byte-level parity between ddc.jsonl and dda_actions.jsonl
    assert receipt["ddc_sha256"] == receipt["dda_actions_sha256"]
    assert ddc_file.read_bytes() == dda_file.read_bytes()


def test_ddc_parser_flags_non_exact_residual_effect(nonzero_bout_run_dir: Path) -> None:
    """Verify that DdcOperadParser correctly classifies non-exact residual effect."""
    ddc_file = nonzero_bout_run_dir / "ddc.jsonl"
    parser = DdcOperadParser(ddc_file)
    res = parser.parse()
    assert res.is_ok, f"DDC Parser failed: {res.unwrap_err()}"

    op_receipt = res.unwrap()
    assert op_receipt.hash_chain_valid is True
    assert op_receipt.ddc_laws_valid is True
    assert op_receipt.terminal_residual is not None and op_receipt.terminal_residual != "0"

    # Must be classified as residual_contractive or residual_non_contractive, never exact
    assert op_receipt.residual_effect in ("residual_contractive", "residual_non_contractive")
    assert op_receipt.residual_effect != "exact"


def test_refuse_false_exactness_claim(nonzero_bout_run_dir: Path, tmp_path: Path) -> None:
    """Verify that DdcOperadParser refuses false exactness claims in operad_signature.json."""
    repo_root = Path(__file__).resolve().parents[3]
    operad_orig_dir = repo_root / "operads" / "skill_operad"
    ddc_file = nonzero_bout_run_dir / "ddc.jsonl"

    # Set up sandbox operad directory
    tmp_json = tmp_path / "json"
    tmp_json.mkdir(parents=True, exist_ok=True)
    sig_orig = operad_orig_dir / "json" / "operad_signature.json"
    comp_orig = operad_orig_dir / "json" / "composition_matrix.json"
    slices_orig = operad_orig_dir / "json" / "agent_capability_slices.json"

    (tmp_json / "operad_signature.json").write_text(sig_orig.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_json / "composition_matrix.json").write_text(comp_orig.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_json / "agent_capability_slices.json").write_text(slices_orig.read_text(encoding="utf-8"), encoding="utf-8")

    parser = DdcOperadParser(ddc_file)

    # 1. Refusal when caller explicitly claims 'exact' on a non-exact run
    false_claim_res = parser.compress_to_operad_signature(
        skill_id="test-false-claim-op",
        skill_name="Test False Claim Op",
        claimed_residual_effect="exact",
        operad_dir=tmp_path,
        apply_changes=False,
    )
    assert false_claim_res.is_err, "Expected FALSE_EXACTNESS_CLAIM refusal"
    refusal = false_claim_res.unwrap_err()
    assert refusal.code == "FALSE_EXACTNESS_CLAIM"
    assert "Delta_T = 0" in refusal.message

    # 2. Refusal when expected_residual_effect does not match
    mismatch_res = parser.compress_to_operad_signature(
        skill_id="test-mismatch-op",
        skill_name="Test Mismatch Op",
        expected_residual_effect="exact",
        operad_dir=tmp_path,
        apply_changes=False,
    )
    assert mismatch_res.is_err, "Expected RESIDUAL_EFFECT_MISMATCH refusal"
    assert mismatch_res.unwrap_err().code == "RESIDUAL_EFFECT_MISMATCH"

    # 3. Refusal when attempting to update an existing operation that claims 'exact' without allow_downgrade
    sig_data = json.loads((tmp_json / "operad_signature.json").read_text(encoding="utf-8"))
    sig_data["operations"].append({
        "skill_id": "test-existing-exact-op",
        "name": "Existing Exact Operation",
        "arity": 2,
        "source_colours": ["Contract", "State"],
        "target_colour": "Receipt",
        "residual_effect": "exact",
        "description": "Pre-existing verified exact operation",
    })
    (tmp_json / "operad_signature.json").write_text(json.dumps(sig_data, indent=2) + "\n", encoding="utf-8")

    existing_exact_res = parser.compress_to_operad_signature(
        skill_id="test-existing-exact-op",
        skill_name="Existing Exact Operation",
        operad_dir=tmp_path,
        apply_changes=False,
        allow_downgrade=False,
    )
    assert existing_exact_res.is_err, "Expected refusal on existing exact operation without allow_downgrade"
    assert existing_exact_res.unwrap_err().code == "FALSE_EXACTNESS_CLAIM"

    # 4. Honest registration of non-exact residual effect succeeds
    honest_res = parser.compress_to_operad_signature(
        skill_id="foc-006-nonzero-test-skill",
        skill_name="Non-Zero Obstruction Specification",
        source_colours=("Contract", "State"),
        target_colour="Receipt",
        description="Measured non-zero residual cochain",
        operad_dir=tmp_path,
        apply_changes=True,
    )
    assert honest_res.is_ok, f"Honest non-exact registration failed: {honest_res.unwrap_err()}"
    report_data = honest_res.unwrap()
    assert report_data["residual_effect"] in ("residual_contractive", "residual_non_contractive")
    assert report_data["residual_effect"] != "exact"

    # Verify sandbox operad_signature.json reflects the honest non-exact effect
    sig_updated = json.loads((tmp_json / "operad_signature.json").read_text(encoding="utf-8"))
    registered_ops = [op for op in sig_updated["operations"] if op["skill_id"] == "foc-006-nonzero-test-skill"]
    assert len(registered_ops) == 1
    assert registered_ops[0]["residual_effect"] in ("residual_contractive", "residual_non_contractive")
    assert registered_ops[0]["residual_effect"] != "exact"
