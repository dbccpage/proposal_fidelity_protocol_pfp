"""End-to-end integration test for Challenge C033.

Reads the committed records only; it never writes into the package.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.governance.commit_reveal_runner import (
    COMMITMENT_STATUS_REGENERATED,
    RECEIPT_BINDS_SUPERSEDED_COMMITMENT,
    inspect_commitments,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
COMMITMENTS_DIR = CHALLENGE_DIR / "commitments"
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"

RETIRED_SELF_SCORE_LABEL = "PASS_TO_MASTER"
"""Label that the pre-correction runner wrote into commitments/c033_scoring_receipt.json.

That receipt is a historical record and is kept unchanged. The label scored the
reference solver against its own judge packet; it was never a model evaluation or
a Adversary verdict, and the current gate emits REFERENCE_SELF_CONSISTENT instead.
"""


def test_c033_end_to_end_evaluation_and_historical_receipt():
    """Validates the C033 records end to end, reading the scoring receipt as a historical record.

    Counterexample: the historical receipt records the same manifest digest as the judge
    commitment regenerated after the judge cases were visible (the manifest bytes did not
    change), so comparing it with the current files would make it look bound to a commitment
    made after it. It must bind the superseded commitment it recorded, and the regenerated
    commitment must say that it is current and not a pre-run commitment."""
    # Check that commitment records exist
    receipt_file = COMMITMENTS_DIR / "c033_scoring_receipt.json"
    commitment_file = COMMITMENTS_DIR / "c033_judge_commitment.json"
    freeze_file = COMMITMENTS_DIR / "c033_freeze_record.json"
    assert receipt_file.is_file(), "Scoring receipt missing"

    receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt_data["final_verdict"] == RETIRED_SELF_SCORE_LABEL
    assert "gate_scope" not in receipt_data
    assert receipt_data["dual_agreements"] == receipt_data["total_cases"]
    assert receipt_data["total_cases"] >= 46

    # The regenerated records are current and not pre-run; the receipt binds the superseded commitment.
    commitment = json.loads(commitment_file.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_file.read_text(encoding="utf-8"))
    for record in (commitment, freeze):
        assert record["commitment_status"] == COMMITMENT_STATUS_REGENERATED
        assert record["regeneration_note"]
    assert (
        receipt_data["phase1_manifest_sha256"]
        == commitment["superseded_commitment"]["manifest_sha256"]
    )
    result = inspect_commitments()
    assert result.verified, f"{result.code}: {result.detail}"
    assert result.receipt_binding == RECEIPT_BINDS_SUPERSEDED_COMMITMENT
    assert result.commitment_status == COMMITMENT_STATUS_REGENERATED

    # Spot-check a sample of judge cases directly
    sample_cases = list((JUDGE_DIR / "cases/base").glob("*.json"))[:5]
    for sc in sample_cases:
        case = json.loads(sc.read_text(encoding="utf-8"))
        res = solve(case)
        ev = evaluate_dual(case, res)
        assert ev["agreed"], f"Disagreement on sample case {sc.name}"
        assert ev["verdict"] == "PASS", f"Non-pass verdict on sample case {sc.name}"
