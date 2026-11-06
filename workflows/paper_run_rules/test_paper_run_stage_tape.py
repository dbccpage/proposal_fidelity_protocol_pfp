"""The stage receipt tape: append-only history, role gates and the rebuild rule.

Ported from an internal test suite (two files merged). These finite checks do not
establish authenticated or tamper-evident stage history, or verified execution.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from paperrun.stage_driver import StageDriver, StageDriverError, StageReceipt


def _receipt(status: str = "COMPLETED", **overrides: object) -> StageReceipt:
    fields = {
        "receipt_id": f"receipt-{status}",
        "job_id": "job-receipt-only",
        "stage_id": "stage_0_redteam",
        "skill_id": "paper-redteam-dialogue",
        "result_token": "caller-supplied-status",
        "status": status,
        "residual_open_ids": ["R-STILL-OPEN"],
        "note": "submitted metadata, not execution evidence",
        "tree_sha256": "caller-supplied-tree",
        "created_at_utc": "2026-09-06T00:00:00+00:00",
    }
    fields.update(overrides)
    return StageReceipt(**fields)


# --- role and rebuild gates -------------------------------------------------


def test_append_refuses_proposer_claims_pass(tmp_path: Path):
    d = StageDriver(tmp_path / "job")
    rec = StageReceipt.issue(
        job_id="j1",
        stage_id="stage_1_improver",
        status="COMPLETED",
        result_token="DONE",
        tree_sha256="abc",
        actor_role="proposer",
        event_type="candidate_patch",
        claims_pass=True,
    )
    with pytest.raises(StageDriverError, match="transition refused"):
        d.append_receipt(rec)


def test_rebuild_required_after_build(tmp_path: Path):
    d = StageDriver(tmp_path / "job")
    d.append_receipt(
        StageReceipt.issue(
            job_id="j1",
            stage_id="stage_5_build_public_object",
            status="COMPLETED",
            result_token="BUILT",
            tree_sha256="h1",
        )
    )
    with pytest.raises(StageDriverError, match="rebuild required"):
        d.append_receipt(
            StageReceipt.issue(
                job_id="j1",
                stage_id="stage_1_improver",
                status="COMPLETED",
                result_token="PATCH",
                tree_sha256="h2",
                source_mutated_after_build=True,
            )
        )


def test_rebuild_via_new_build_stage_allowed(tmp_path: Path):
    d = StageDriver(tmp_path / "job")
    d.append_receipt(
        StageReceipt.issue(
            job_id="j1",
            stage_id="stage_5_build_public_object",
            status="COMPLETED",
            result_token="BUILT",
            tree_sha256="h1",
        )
    )
    # A new build after mutation is the legal path.
    d.append_receipt(
        StageReceipt.issue(
            job_id="j1",
            stage_id="stage_5_build_public_object",
            status="COMPLETED",
            result_token="REBUILT",
            tree_sha256="h2",
            source_mutated_after_build=True,
        )
    )
    assert d.BUILD_STAGE_ID in d.completed_stage_ids()


def test_normal_receipt_still_appends(tmp_path: Path):
    d = StageDriver(tmp_path / "job")
    rec = StageReceipt.issue(
        job_id="j1",
        stage_id="stage_0_redteam",
        status="COMPLETED",
        result_token="OK",
        tree_sha256="h",
    )
    d.append_receipt(rec)
    assert len(d.list_receipts()) == 1
    assert d.list_receipts()[0]["actor_role"]


# --- tape custody -----------------------------------------------------------


@pytest.mark.parametrize("status", ["STARTED", "COMPLETED", "SKIPPED", "FAILED"])
def test_append_retains_receipt_identity_and_exact_v1_contents(tmp_path, status):
    driver = StageDriver(tmp_path / "job")
    receipt = _receipt(status)
    expected = {
        "schema_version": "core.research.stage_receipt.v1",
        "receipt_id": f"receipt-{status}",
        "job_id": "job-receipt-only",
        "stage_id": "stage_0_redteam",
        "skill_id": "paper-redteam-dialogue",
        "result_token": "caller-supplied-status",
        "status": status,
        "residual_open_ids": ["R-STILL-OPEN"],
        "note": "submitted metadata, not execution evidence",
        "tree_sha256": "caller-supplied-tree",
        "created_at_utc": "2026-09-06T00:00:00+00:00",
        "authority_effect": "None",
        "claims_global_green": False,
        "sprint": "sprint-paper-007-0",
        "actor_role": "evaluator",
        "event_type": {
            "STARTED": "measurement",
            "COMPLETED": "evaluation_receipt",
            "SKIPPED": "evaluation_receipt",
            "FAILED": "finding",
        }[status],
        "claims_pass": False,
        "source_mutated_after_build": False,
        "post_build": False,
    }

    assert driver.append_receipt(receipt) is receipt

    assert receipt.to_dict() == expected
    assert driver.list_receipts() == [expected]
    assert driver.tape_path.read_bytes() == (
        json.dumps(expected, sort_keys=True) + os.linesep
    ).encode("utf-8")
    assert list(driver.job_dir.iterdir()) == [driver.tape_path]


def test_append_preserves_ordered_history_bytes_without_rewriting(tmp_path):
    driver = StageDriver(tmp_path / "job")
    historical = [_receipt("STARTED").to_dict(), _receipt("FAILED").to_dict()]
    historical[0]["historical_extra_field"] = "preserve, not endorse"
    prefix = (
        json.dumps(historical[0], separators=(",", ":"))
        + "\r\n\n"
        + json.dumps(historical[1], indent=None)
        + "\n"
    ).encode("utf-8")
    driver.tape_path.write_bytes(prefix)
    receipt = _receipt("COMPLETED")

    assert driver.append_receipt(receipt) is receipt

    assert driver.tape_path.read_bytes() == prefix + (
        json.dumps(receipt.to_dict(), sort_keys=True) + os.linesep
    ).encode("utf-8")
    assert driver.list_receipts() == [*historical, receipt.to_dict()]
    assert driver.pipeline_status()["receipt_count"] == 3


def test_real_tape_open_failure_is_not_reported_as_success(tmp_path):
    driver = StageDriver(tmp_path / "job")
    # A real directory/file collision fails on Windows and POSIX, without mocks.
    driver.tape_path.mkdir()

    with pytest.raises(OSError):
        driver.append_receipt(_receipt())

    assert driver.tape_path.is_dir()
    assert list(driver.tape_path.iterdir()) == []
    assert driver.list_receipts() == []


@pytest.mark.parametrize("existing_history", [False, True])
def test_role_refusal_does_not_create_or_extend_tape(tmp_path, existing_history):
    driver = StageDriver(tmp_path / "job")
    if existing_history:
        driver.append_receipt(_receipt("STARTED"))
    before = driver.tape_path.read_bytes() if existing_history else None
    rejected = _receipt(
        actor_role="proposer",
        event_type="candidate_patch",
        claims_pass=True,
    )

    with pytest.raises(StageDriverError, match="transition refused"):
        driver.append_receipt(rejected)

    if before is None:
        assert not driver.tape_path.exists()
        assert driver.list_receipts() == []
    else:
        assert driver.tape_path.read_bytes() == before
        assert driver.list_receipts() == [_receipt("STARTED").to_dict()]


def test_rebuild_refusal_preserves_prior_receipt_and_bytes(tmp_path):
    driver = StageDriver(tmp_path / "job")
    built = _receipt(
        receipt_id="build-receipt",
        stage_id=driver.BUILD_STAGE_ID,
        skill_id="paper-build",
    )
    driver.append_receipt(built)
    before = driver.tape_path.read_bytes()

    with pytest.raises(StageDriverError, match="rebuild required"):
        driver.append_receipt(_receipt(source_mutated_after_build=True))

    assert driver.tape_path.read_bytes() == before
    assert driver.list_receipts() == [built.to_dict()]


def test_receipts_cannot_claim_global_green_or_authority():
    with pytest.raises(StageDriverError, match="GlobalGreen"):
        _receipt(claims_global_green=True)
    with pytest.raises(StageDriverError, match="authority_effect"):
        _receipt(authority_effect="Granted")
