"""Demo 004 must report checker outcomes, never a synthetic suite PASS."""

import pytest

from pfp.domain.stages.demos import DemoSpec
from pfp.infrastructure.pilot_runners import (
    challenge_host_control as runner_004,
)


def spec(**expectations):
    return DemoSpec(id="demo_004", title="Finite control", seed="C039", expectations=expectations)


@pytest.mark.parametrize("status", ["HOST_REJECTED", "CHECKER_DEFECT", "INFRASTRUCTURE_ERROR"])
def test_demo_reports_actual_failure(monkeypatch, status):
    calls = []

    def check(request, timeout):
        calls.append(request)
        return {"status": status, "failure_class": "CONTROL"}

    monkeypatch.setattr(runner_004, "isolated", check)
    result = runner_004.run_demo_004(spec())
    assert len(calls) == 1 and calls[0]["kind"] == "NO_LLM"
    assert result.all_passed is False
    assert status in result.checks[0].observed


@pytest.mark.parametrize(
    "expectations",
    [
        {"challenge_id": "missing"},
        {"ordinal": "-1"},
        {"ordinal": "oops"},
        {"split": "invalid"},
    ],
)
def test_bad_selection_never_dispatches(monkeypatch, expectations):
    def unexpected(*args, **kwargs):
        pytest.fail("Invalid selection dispatched a worker")

    monkeypatch.setattr(runner_004, "isolated", unexpected)
    assert not runner_004.run_demo_004(spec(**expectations)).all_passed


def test_demo_executes_one_real_finite_control():
    result = runner_004.run_demo_004(spec(challenge_id="C039", ordinal="0"))
    assert result.all_passed
    assert len(result.checks) == 1
    assert "FIXTURE_VERIFIED" in result.checks[0].observed
    assert result.terminal_status == "FIXTURE_VERIFIED"
    assert "150" not in result.runner_id


def test_actual_c039_judges_reject_mutated_degeneracy():
    import json

    from pfp.infrastructure.challenge_live import choose_case

    row = choose_case("C039", "development", 0)
    control = runner_004.isolated(dict(kind="NO_LLM", row=row), timeout=20)
    answer = control["answer"]
    answer["gsd"] = 2
    envelope = dict(
        derived_under_policy="SPK-001",
        sections=[],
        answer=answer,
        summary=dict(
            narrowest_defensible_thesis="Mutated host control",
            evidence_scope="NO_LLM",
            next_concrete_test="Check both judges",
        ),
        process_integrity=dict(
            seed_allows_theory_refutation=True, detected_prompt_biases=[], should_continue=False
        ),
    )
    result = runner_004.isolated(
        dict(kind="LLM", row=row, raw_reply=json.dumps(envelope)), timeout=20
    )
    assert result["status"] == "PROVIDER_COMPLETED"
    assert len(result["judges"]) == 2
    assert all(judge["accepted"] is False for judge in result["judges"])


def test_saved_real_responses_reproduce_observed_outcomes():
    import json
    from hashlib import sha256

    from pfp.infrastructure.adapters.pfp_campaign import grade_reply
    from pfp.infrastructure.challenge_execution import isolated
    from adversary.tests.pilots.challenge_suite.catalog import ROOT

    folder = (
        ROOT
        / "adversary/tests/pilots/evidence/demo004_pfp_learning/validation/implementation_20261012"
    )
    observations = json.loads((folder / "observations.json").read_bytes())
    for record in observations["records"]:
        for artifact in record["artifacts"].values():
            assert (
                sha256((folder / artifact["path"]).read_bytes()).hexdigest() == artifact["sha256"]
            )
        raw = (folder / record["artifacts"]["provider_response.json"]["path"]).read_bytes()
        checked = grade_reply(
            raw,
            record["model"],
            lambda text: isolated(dict(kind="LLM", row=record["row"], raw_reply=text), timeout=30),
        ).data
        assert checked["result"] == record["result"]
        assert checked["generation_id"] == record["generation_id"]
        assert checked["cost_microusd"] == record["cost_microusd"]
