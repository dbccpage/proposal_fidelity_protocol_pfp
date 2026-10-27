"""The retired aggregate cannot borrow success from current finite scenarios."""

from types import SimpleNamespace

import pytest

from pfp.controllers.pfp_controller import PfpController
from pfp.domain.kernel.result import RefusalCode
from pfp.domain.stages.demos import DemoRunReceipt
from pfp.infrastructure.demos.execution import run, verify
from pfp.infrastructure.pilot_runners.pilot_dispatch import (
    UnifiedPfpDemoRunner,
)
from pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from pfp.tests.test_pilot_use_cases import _make_sample_pilot
from pfp.use_cases.run_demo import RunDemoUseCase


def test_public_demo_003_retains_original_unexecuted_obligations():
    receipt = PfpController().run_demo("demo_003").unwrap()
    assert not receipt.all_passed
    assert receipt.terminal_status == "Refused"
    assert receipt.runner_id == "runner_003_master"
    assert receipt.authority_effect == "None"
    assert [check.name for check in receipt.checks] == [
        "sub_demo_census",
        "mub6_regge_triangulation",
        "cohomology_battery",
    ]
    assert all(not check.passed and check.error_message for check in receipt.checks)
    assert all(check.observed is None for check in receipt.checks)
    assert "DEMO_003_AGGREGATE_RETIRED" in receipt.checks[0].error_message
    assert "ILLUSTRATION_ONLY" in receipt.checks[1].error_message
    assert "SCENARIO_RETIRED" in receipt.checks[2].error_message


def test_public_pilot_retains_refused_receipt_and_cannot_default_to_pass():
    pilot = _make_sample_pilot(target="demo_003", eval_status="NOT_RUN")
    updated = RunDemoUseCase(
        PfpFileSystemStorageAdapter(), UnifiedPfpDemoRunner()
    ).run_pilot(pilot).unwrap()
    assert updated.trial_status.value == "FAIL"
    receipt = DemoRunReceipt.model_validate_json(updated.execution_receipt_evidence)
    assert not receipt.all_passed
    assert receipt.terminal_status == "Refused"
    assert receipt.demo_id == pilot.target
    assert pilot.trial_status.value == "NOT_RUN"


@pytest.mark.parametrize(
    "receipt", [None, SimpleNamespace(all_checks_passed=True), SimpleNamespace(all_passed="false")]
)
def test_missing_or_untyped_runner_result_is_not_pilot_success(receipt):
    runner = SimpleNamespace(run_demo=lambda spec: receipt)
    result = RunDemoUseCase(PfpFileSystemStorageAdapter(), runner).run_pilot(
        _make_sample_pilot(target="demo_003", eval_status="NOT_RUN")
    )
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.INFRASTRUCTURE_FAILURE


def test_existing_executed_demo_000_still_passes():
    updated = RunDemoUseCase(
        PfpFileSystemStorageAdapter(), UnifiedPfpDemoRunner()
    ).run_pilot(_make_sample_pilot(target="demo_000", eval_status="NOT_RUN")).unwrap()
    receipt = DemoRunReceipt.model_validate_json(updated.execution_receipt_evidence)
    assert updated.trial_status.value == "PASS"
    assert receipt.all_passed
    assert receipt.checks and all(check.passed for check in receipt.checks)


def test_explicit_current_finite_scenario_executes_and_replays_without_promoting_aggregate(tmp_path):
    output = tmp_path / "frontier"
    receipt = run("demo_token_frontier", output)
    scenarios = receipt["result"]["result"]["scenarios"]
    assert receipt["result"]["status"] == "CHECKED"
    assert receipt["transport"] == "fixture"
    assert scenarios["scenario_1_digits_mask"]["retained_mass"] == "1/2"
    assert scenarios["scenario_3_zero_retained_mass_refusal"]["status"] == "REFUSED_EXPECTED"
    assert scenarios["scenario_4_packet_trajectory"]["status"] == "ILLUSTRATION_ONLY"
    assert verify(output / "receipt.json")["status"] == "VERIFIED_FIXTURE"
    assert not PfpController().run_demo("demo_003").unwrap().all_passed
