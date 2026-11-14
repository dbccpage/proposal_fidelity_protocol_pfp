"""The transport to the Rust operad host, and what WF2 records from it.

These tests run the real ``pfp_operad`` binary. Build it first:
``cargo build --release -p pfp_operads`` in ``code/rust``.
"""

import json
import sys
from copy import deepcopy

import pytest

from pfp.infrastructure import operad_host
from pfp.infrastructure.workflow_tasks import integer_sum_judge
from pfp.workflows.wf0002 import workflow as wf2
from pfp.workflows.wf0002.runner import runtime
from pfp.workflows.wf0002.scripted import candidate

SPEC = json.loads(wf2.resource_text("examples/integer_sum.task.json"))


def reply(answer):
    binding = wf2.prepare_task(wf2.validate_task(deepcopy(SPEC))).binding
    body = {key: binding[key] for key in ("task_id", "attempt_id", "input_sha256")}
    return json.dumps({**body, "answer": answer}).encode()


def test_the_host_states_its_name_version_and_canon():
    assert operad_host.binary().is_file()
    identity = operad_host.identity()
    assert set(identity) == {"name", "version", "canon"}
    assert identity["name"] == "pfp_operads" and identity["canon"] == "core.operad-canon.v1"


def test_the_binary_is_taken_from_the_environment_then_path_then_a_checkout(monkeypatch, tmp_path):
    named = tmp_path / "named-host"
    monkeypatch.setenv(operad_host.ENVIRONMENT, str(named))
    assert operad_host.binary() == named
    monkeypatch.delenv(operad_host.ENVIRONMENT)
    monkeypatch.setattr(operad_host.shutil, "which", lambda name: str(tmp_path / name))
    assert operad_host.binary() == tmp_path / operad_host.NAME
    monkeypatch.setattr(operad_host.shutil, "which", lambda name: None)
    built = tmp_path / "built-host"
    built.write_bytes(b"")
    monkeypatch.setattr(operad_host, "_checkout_builds", lambda: iter([tmp_path / "absent", built]))
    assert operad_host.binary() == built
    monkeypatch.setattr(operad_host, "_checkout_builds", lambda: iter([]))
    with pytest.raises(operad_host.OperadHostError, match="OPERAD_HOST_NOT_FOUND"):
        operad_host.binary()


def test_a_host_that_cannot_run_or_answer_is_an_error_not_a_verdict(monkeypatch, tmp_path):
    monkeypatch.setenv(operad_host.ENVIRONMENT, str(tmp_path / "no-such-binary"))
    with pytest.raises(operad_host.OperadHostError, match="OPERAD_HOST_DID_NOT_RUN"):
        operad_host.call(("version",))
    monkeypatch.setenv(operad_host.ENVIRONMENT, sys.executable)
    with pytest.raises(operad_host.OperadHostError, match="OPERAD_HOST_NO_OUTCOME"):
        operad_host.call(("-c", "print('not json')"))
    monkeypatch.delenv(operad_host.ENVIRONMENT)
    with pytest.raises(operad_host.OperadHostError, match="OPERAD_HOST_NO_OUTCOME"):
        operad_host.call(("judge",))
    with pytest.raises(ValueError):
        operad_host.call(("judge",), {"case": float("nan")})


def test_outcomes_pass_through_and_a_refusal_has_no_result():
    case = {"values": [17, 25, -4]}
    passed = operad_host.call(("judge",), dict(checker="integer_sum_v1", case=case, answer={"total": 38}))
    failed = operad_host.call(("judge",), dict(checker="integer_sum_v1", case=case, answer={"total": 39}))
    refused = operad_host.call(("judge",), dict(checker="no_such_checker", case=case, answer={}))
    assert (passed["status"], failed["status"], refused["status"]) == ("PASS", "FAIL", "REFUSED")
    assert operad_host.result(failed) == {"accepted": False, "reason": "Incorrect integer sum."}
    with pytest.raises(operad_host.OperadHostError, match="OPERAD_HOST_REFUSED: UNKNOWN_CHECKER"):
        operad_host.result(refused)


def test_the_integer_sum_judge_is_the_hosts_exact_sum():
    huge = 10**120
    assert integer_sum_judge({"values": [17, 25, -4]}, {"total": 38}) == (True, "Exact integer sum agrees.")
    assert integer_sum_judge({"values": [huge, 1, -huge]}, {"total": 1})[0] is True
    assert integer_sum_judge({"values": [huge, huge]}, {"total": 2 * huge + 1})[0] is False
    for wrong in ({"total": 38.0}, {"total": "38"}, {"total": True}, {"total": 38, "note": ""}, 38, None):
        assert integer_sum_judge({"values": [17, 25, -4]}, wrong) == (False, "Incorrect integer sum.")


def test_wf2_records_the_hosts_typing_and_ddc_word():
    checked = wf2.check_reply(SPEC, reply(candidate()))
    assert checked["status"] == "HOST_ACCEPTED" and checked["operad_structure_valid"] is True
    assert checked["structure_errors"] == []
    assert checked["operad_typing"] == [dict(id="sum", typed=True, licensed_as="integer_list_sum")]
    assert checked["ddc_trace"] == "T"


def test_a_colour_outside_the_canon_is_reported_untyped_and_does_not_change_the_verdict():
    answer = candidate()
    answer["operad_candidates"][0].update(source_colours=["Z", "Z", "Z"], target_colour="Z", arity=3)
    checked = wf2.check_reply(SPEC, reply(answer))
    assert checked["status"] == "HOST_ACCEPTED" and checked["structure_errors"] == []
    assert checked["operad_typing"] == [dict(id="sum", typed=False, licensed_as=None)]


def test_a_structure_error_comes_from_the_host_with_its_code():
    answer = candidate()
    answer["ddc_moves"][0]["operad_id"] = "product"
    checked = wf2.check_reply(SPEC, reply(answer))
    assert checked["structure_errors"] == ["UNKNOWN_OPERAD_REF:t1"]
    assert (checked["status"], checked["failure_class"]) == ("PROVIDER_COMPLETED", "WF2_OPERAD_STRUCTURE")
    assert (checked["task_status"], checked["task_failure_class"]) == ("HOST_ACCEPTED", "NONE")


def test_a_run_is_bound_to_the_host_that_checked_it(tmp_path):
    root = tmp_path / "run"
    runtime.prepare_run(deepcopy(SPEC), root)
    manifest = json.loads((root / "preparation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["implementation"]["operad_host"] == operad_host.identity()
    assert "infrastructure/operad_host.py" in manifest["implementation"]["sources"]
