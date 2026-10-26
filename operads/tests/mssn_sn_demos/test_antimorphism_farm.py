"""Antimorphism Farm Live Harvest, Confirmation, and Judge-Suite Export Tests (U19).

Enforces invariants:
- Reclassifying 112-row harvest yields 1:1 disposition bijection under pinned digest.
- AM-FSP-4 row is confirmed by exact rational detector (1 - 3/2 = -1/2 != 0).
- Unconfirmed rows cannot enter a hidden suite (mutation kill gate).
- Scripted rows are never counted as model behaviour (mutation kill gate).
AuthorityEffect: None.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_engine_operads.application.mssn_sn_demos.antimorphism_farm.judge_suite_export import (
    PINNED_CLASSIFIER_DIGEST,
    HarvestRowV2,
    export_judge_suite,
    reclassify_harvest,
    verify_am_fsp_4_orbit_sum,
)


@pytest.fixture
def harvest_file_path() -> Path:
    # Resolve repository root
    root = Path(__file__).resolve().parents[3]
    candidate = (
        root
        / "omega_engine_education"
        / "documentation"
        / "3_the_symbol_game_proposal_fidelity_protocol_pfp"
        / "demos"
        / "demos"
        / "antimorphism_farm"
        / "harvest"
        / "antimorphism_harvest.jsonl"
    )
    if candidate.exists():
        return candidate
    return (
        root
        / "omega_engine_education"
        / "curriculum"
        / "the_symbol_game"
        / "demos"
        / "antimorphism_farm"
        / "harvest"
        / "antimorphism_harvest.jsonl"
    )


def test_am_fsp_4_confirmed_by_exact_detector() -> None:
    """Exact rational detector confirmation for AM-FSP-4."""
    # 1 - 3/2 = -1/2 != 0
    passed, reason = verify_am_fsp_4_orbit_sum("1", "3/2", claimed_zero=True)
    assert passed is False
    assert "1 - 3/2 = -1/2 != 0" in reason
    assert "AM-FSP-4" in reason

    # Grounded zero cancellation
    grounded, g_reason = verify_am_fsp_4_orbit_sum("2", "2", claimed_zero=True)
    assert grounded is True
    assert "Grounded cancellation" in g_reason


def test_harvest_reclassification_stability_witness(harvest_file_path: Path) -> None:
    """Witness Test (U19):

    Reclassify the 112-row harvest under pinned classifier digest.
    Each of the distinct responses gets exactly one disposition.
    """
    assert harvest_file_path.exists(), f"Harvest file missing at {harvest_file_path}"
    raw_lines = [line.strip() for line in harvest_file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(raw_lines) >= 112, f"Expected at least 112 rows, found {len(raw_lines)}"

    raw_rows = [json.loads(line) for line in raw_lines]
    reclassified = reclassify_harvest(raw_rows, PINNED_CLASSIFIER_DIGEST)
    assert len(reclassified) == len(raw_rows)

    # Assert 1:1 disposition bijection across distinct response texts
    disposition_map: dict[str, str] = {}
    for r in reclassified:
        assert r.classifier_digest == PINNED_CLASSIFIER_DIGEST
        if r.raw_response in disposition_map:
            assert disposition_map[r.raw_response] == r.disposition, (
                f"Inconsistent disposition for response: {r.raw_response[:40]}..."
            )
        else:
            disposition_map[r.raw_response] = r.disposition

    # MERON-02 orbit sum row is confirmed by exact detector
    meron_02_rows = [r for r in reclassified if r.probe_id == "MERON-02-ORBIT-CANCELLATION"]
    assert len(meron_02_rows) > 0
    for m2 in meron_02_rows:
        if "3/2" in m2.raw_response:
            assert m2.disposition == "HALLUCINATION_DETECTED"
            assert m2.confirmed is True


def test_mutation_kill_gate_scripted_rows_never_counted_as_model_behaviour() -> None:
    """Mutation Kill Gate (U19):

    An export built from scripted rows is refused as model evidence.
    """
    scripted_row = HarvestRowV2(
        task_id="task_scripted_01",
        probe_id="MERON-01",
        domain_id="PHYSICS",
        model="qwen/qwen-2.5-7b-instruct",
        mode="scripted",
        raw_response="Canned test response",
        disposition="HALLUCINATION_DETECTED",
        confirmed=True,
        classifier_digest=PINNED_CLASSIFIER_DIGEST,
    )

    with pytest.raises(ValueError, match="scripted rows cannot be exported as model evidence"):
        export_judge_suite([scripted_row], seed=42, include_scripted_as_model_evidence=False)


def test_mutation_kill_gate_unconfirmed_rows_cannot_enter_hidden_suite() -> None:
    """Mutation Kill Gate (U19):

    Unconfirmed regex-only rows MUST NOT enter a hidden judge suite.
    """
    unconfirmed_row = HarvestRowV2(
        task_id="task_live_unconfirmed",
        probe_id="MERON-01",
        domain_id="PHYSICS",
        model="qwen/qwen-2.5-7b-instruct",
        mode="live",
        raw_response="Unconfirmed candidate response",
        disposition="CANDIDATE",
        confirmed=False,  # Unconfirmed!
        classifier_digest=PINNED_CLASSIFIER_DIGEST,
        billed_cost_micro_usd=10,
    )

    # Scan seeds until one maps this item to hidden, verifying refusal
    caught = False
    for seed in range(50):
        try:
            export_judge_suite([unconfirmed_row], seed=seed, include_scripted_as_model_evidence=True)
        except ValueError as err:
            if "unconfirmed rows cannot enter a hidden suite" in str(err):
                caught = True
                break

    assert caught, "Expected unconfirmed row in hidden partition to be refused"


def test_clean_live_export_and_commitment() -> None:
    """Verify clean live rows export with public/hidden split and commit-reveal hash."""
    confirmed_rows = [
        HarvestRowV2(
            task_id=f"live_{i}",
            probe_id=f"PROBE_{i}",
            domain_id="PHYSICS",
            model="qwen/qwen-2.5-7b-instruct",
            mode="live",
            raw_response=f"Valid live response {i}",
            disposition="HALLUCINATION_DETECTED" if i % 2 == 0 else "GROUNDED_WITNESS",
            confirmed=True,
            classifier_digest=PINNED_CLASSIFIER_DIGEST,
            billed_cost_micro_usd=10,
        )
        for i in range(10)
    ]

    suite = export_judge_suite(confirmed_rows, seed=12345)
    assert suite.total_live_rows == 10
    assert suite.deduplicated_rows == 10
    assert suite.hidden_commitment_sha256.startswith("sha256:")
    assert suite.authority_effect == "None"

    # Verify no hidden row appears in public suite
    hidden_ids = {r.task_id for r in suite.hidden_suite}
    public_ids = {r.task_id for r in suite.public_suite}
    assert hidden_ids.isdisjoint(public_ids)
    assert len(hidden_ids | public_ids) == 10
