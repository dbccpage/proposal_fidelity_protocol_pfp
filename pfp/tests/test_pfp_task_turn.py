"""Public task-turn controls; independent finite judges and ordinary role replies."""

import base64
import copy
import hashlib
import json
from dataclasses import replace

import pytest

from pfp.domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
from pfp.entrypoints.cli.pfp import main
from pfp.use_cases import pfp_prompt, pfp_proposal


def task(schema=None):
    return PfpTaskPrompt(
        "worker-17",
        "Summarize the supplied public issue.",
        {"issue": "A file was moved.", "expected_answer": "ORACLE_SECRET"},
        schema or {"type": "string", "minLength": 1},
    )


def prepare(source=None, attempt="attempt-1", feedback=None):
    return pfp_prompt.PreparePfpTaskTurnUseCase().execute(
        PfpPromptTemplate("Act as the requested worker.", "[USER PROMPT]", {}),
        source or task(),
        attempt,
        feedback=feedback,
    )


def reply(prompt, answer):
    properties = prompt.response_schema["properties"]
    return json.dumps(
        {
            **{key: properties[key]["const"] for key in ("task_id", "attempt_id", "input_sha256")},
            "answer": answer,
        },
        ensure_ascii=False,
    ).encode()


def check(source, prompt, raw, judges=(), required=False):
    return pfp_proposal.CheckPfpTaskTurnUseCase().execute(
        source, prompt, raw, judges=judges, require_checker=required
    )


def test_bare_expected_is_removed_before_the_provider_sees_the_task():
    schema = {
        "type": "object",
        "properties": {"phi1": {"type": "string"}},
        "required": ["phi1"],
        "additionalProperties": False,
    }
    source = PfpTaskPrompt(
        "phi-1",
        "Report the declared certificate field.",
        {
            "a": 2,
            "expected": 5,
            "phi1": "1/2",
            "certificate": {"name": "phi1", "expected": 5},
        },
        schema,
    )
    public = pfp_prompt.public_task_input(source)
    assert public["input"] == {
        "a": 2,
        "phi1": "1/2",
        "certificate": {"name": "phi1"},
    }
    prompt = prepare(source)
    delivered = json.loads(prompt.user)
    assert delivered["input"] == public["input"]
    assert "expected" not in prompt.user
    assert "5" not in json.dumps(delivered["input"])
    assert "phi1" in json.dumps(delivered["input"])
    assert delivered["input"]["certificate"] == {"name": "phi1"}


def test_public_worker_prompt_and_unverified_actual_reply_preserve_inputs():
    source = task()
    before = copy.deepcopy(source)
    prompt = prepare(source)
    assert source == before
    assert "ORACLE_SECRET" not in prompt.system + prompt.user
    assert set(prompt.response_schema["properties"]) == {
        "task_id",
        "attempt_id",
        "input_sha256",
        "answer",
    }
    assert "SPK-001" not in prompt.system
    assert "mathematical witness" not in prompt.system
    assert json.dumps(prompt.response_schema, sort_keys=True) in prompt.system
    raw = b" \n" + reply(prompt, "Moved the public file. \u03a9") + b"\r\n"
    result = check(source, prompt, raw)
    assert result["status"] == "PROVIDER_COMPLETED"
    assert result["evidence_grade"] == "UNVERIFIED"
    assert result["schema_valid"] is True
    assert base64.b64decode(result["raw_reply_base64"]) == raw
    assert result["raw_reply_sha256"] == hashlib.sha256(raw).hexdigest()
    assert result["answer"] == "Moved the public file. \u03a9"


@pytest.mark.parametrize(
    "schema,answer",
    [
        (
            {
                "type": "object",
                "properties": {"findings": {"type": "array", "items": {"type": "string"}}},
                "required": ["findings"],
                "additionalProperties": False,
            },
            {"findings": ["A caller still uses the old path."]},
        ),
        (
            {
                "type": "object",
                "properties": {
                    "kind": {"enum": ["helpful_pattern", "antibody"]},
                    "prompt_attachment": {"type": "string"},
                },
                "required": ["kind", "prompt_attachment"],
                "additionalProperties": False,
            },
            {"kind": "antibody", "prompt_attachment": "prompt://worker/17"},
        ),
    ],
)
def test_reviewer_and_learning_use_their_own_minimal_shapes(schema, answer):
    source = task(schema)
    prompt = prepare(source)
    result = check(source, prompt, reply(prompt, answer))
    assert result["schema_valid"] is True
    assert result["evidence_grade"] == "UNVERIFIED"
    assert result["status"] != "HOST_ACCEPTED"


@pytest.mark.parametrize("candidate,accepted", [(5, True), (8, False)])
def test_schema_valid_finite_answer_reaches_independent_judge(candidate, accepted):
    source = PfpTaskPrompt("sum-1", "Add a and b.", {"a": 2, "b": 3}, {"type": "integer"})
    prompt = prepare(source)
    calls = []

    def judge(case, answer):
        calls.append((case, answer))
        case["a"] = -100  # A checker cannot mutate the original input.
        return answer == 2 + 3, "Computed the sum independently."

    result = check(source, prompt, reply(prompt, candidate), [("sum", judge)], True)
    assert len(calls) == 1
    assert source.case == {"a": 2, "b": 3}
    assert result["schema_valid"] is True
    assert result["status"] == ("HOST_ACCEPTED" if accepted else "PROVIDER_COMPLETED")
    assert result["failure_class"] == ("NONE" if accepted else "CERTIFICATE")


@pytest.mark.parametrize("field", ["task_id", "attempt_id", "input_sha256"])
def test_wrong_binding_refuses_before_a_checker_runs(field):
    source = task()
    prompt = prepare(source)
    payload = json.loads(reply(prompt, "public candidate"))
    payload[field] = "different"
    calls = []
    result = check(
        source, prompt, json.dumps(payload).encode(), [("spy", lambda *a: calls.append(a))]
    )
    assert result["schema_valid"] is False
    assert result["status"] != "HOST_ACCEPTED"
    assert calls == []


@pytest.mark.parametrize(
    "raw", [b"```json\n{}\n```", b'{"answer": 1, "answer": 2}', b'{"answer": NaN}', b"\xff"]
)
def test_malformed_actual_json_never_gets_repaired(raw):
    source = task()
    result = check(source, prepare(source), raw)
    assert result["schema_valid"] is False
    assert result["status"] != "HOST_ACCEPTED"
    assert base64.b64decode(result["raw_reply_base64"]) == raw


@pytest.mark.parametrize("candidate", [1.0, True, "1"])
def test_native_integer_types_are_exact(candidate):
    source = task({"type": "integer"})
    prompt = prepare(source)
    calls = []
    result = check(source, prompt, reply(prompt, candidate), [("spy", lambda *a: calls.append(a))])
    assert result["schema_valid"] is False
    assert calls == []


def test_required_missing_checker_is_unavailable_not_acceptance():
    source = task()
    prompt = prepare(source)
    result = check(source, prompt, reply(prompt, "Valid unverified prose."), required=True)
    assert result["schema_valid"] is True
    assert result["status"] == "INFRASTRUCTURE_ERROR"
    assert result["failure_class"] == "UNREGISTERED_CHECKER"


def test_changed_public_input_cannot_reuse_a_prepared_turn():
    source = task()
    prompt = prepare(source)
    changed = task()
    changed.case["issue"] = "Different issue."
    result = check(changed, prompt, reply(prompt, "A stale answer."))
    assert result["schema_valid"] is False
    assert result["status"] != "HOST_ACCEPTED"


@pytest.mark.parametrize("change", ["objective", "answer_schema", "required_binding"])
def test_stale_or_weakened_task_contract_cannot_admit_a_reply(change):
    source = task()
    prompt = prepare(source)
    raw = reply(prompt, "Stale candidate.")
    if change == "objective":
        source = replace(source, task_text="Perform a different task.")
    elif change == "answer_schema":
        source = replace(source, answer_schema={"type": "integer"})
    else:
        prompt.response_schema["required"].remove("task_id")
        packet = json.loads(raw)
        del packet["task_id"]
        raw = json.dumps(packet).encode()
    assert check(source, prompt, raw)["schema_valid"] is False


@pytest.mark.parametrize("keyword", ["$ref", "$dynamicRef"])
def test_external_schema_references_refuse_during_offline_preparation(keyword):
    source = task({keyword: "https://example.invalid/should-never-be-retrieved"})
    with pytest.raises(ValueError, match="EXTERNAL_SCHEMA_REFERENCE"):
        prepare(source)


def test_local_definition_reference_is_supported():
    source = task({"$defs": {"text": {"type": "string"}}, "$ref": "#/$defs/text"})
    prompt = prepare(source)
    assert check(source, prompt, reply(prompt, "Ordinary prose."))["schema_valid"] is True


@pytest.mark.parametrize(
    "schema,reason",
    [
        ({"$ref": "#/$defs/missing"}, "UNRESOLVED_TASK_SCHEMA_REFERENCE"),
        ({"$ref": "#missing"}, "UNRESOLVED_TASK_SCHEMA_REFERENCE"),
        ({"$ref": "#"}, "NONPRODUCTIVE_TASK_SCHEMA_REFERENCE"),
        ({"allOf": [{"$ref": "#"}]}, "NONPRODUCTIVE_TASK_SCHEMA_REFERENCE"),
        ({"$defs": {"left": {"$ref": "#/$defs/right"}, "right": {"$ref": "#/$defs/left"}},
          "$ref": "#/$defs/left"}, "NONPRODUCTIVE_TASK_SCHEMA_REFERENCE"),
        ({"$dynamicAnchor": "node", "$dynamicRef": "#node"}, "NONPRODUCTIVE_TASK_SCHEMA_REFERENCE"),
        ({"$defs": {"a": {"$anchor": "node"}, "b": {"$anchor": "node"}}, "$ref": "#node"},
         "DUPLICATE_TASK_SCHEMA_ANCHOR"),
    ],
)
def test_invalid_local_reference_contracts_refuse_before_provider_admission(schema, reason):
    from pfp.infrastructure.task_turn import complete_task_turn
    from adversary.domain.providers.types import CandidateRequest, Provider

    class NoSendGateway:
        calls = 0

        def complete(self, *_args, **_kwargs):
            self.calls += 1
            pytest.fail("Invalid host schema reached provider admission")

    gateway = NoSendGateway()
    with pytest.raises(ValueError, match=reason):
        complete_task_turn(
            gateway, CandidateRequest("Inspect input.", "Input"),
            task_id="invalid-schema", attempt_id="invalid-schema", answer_schema=schema,
            provider=Provider.OPENROUTER, model="fixture/typed-task",
        )
    assert gateway.calls == 0


@pytest.mark.parametrize(
    "schema,valid,invalid",
    [
        ({"type": ["object", "null"], "properties": {"next": {"$ref": "#"}},
          "additionalProperties": False}, {"next": {"next": None}}, {"next": 42}),
        ({"type": ["array", "integer"], "items": {"$ref": "#"}}, [1, [2, 3]], [1, ["bad"]]),
        ({"$dynamicAnchor": "node", "type": ["object", "null"],
          "properties": {"next": {"$dynamicRef": "#node"}}}, {"next": None}, {"next": "bad"}),
        ({"$defs": {"a b": {"type": "integer"}}, "$ref": "#/$defs/a%20b"}, 3, "bad"),
        ({"$defs": {"child": {"$id": "urn:pfp:child", "$defs": {"text": {"type": "string"}},
                             "$ref": "#/$defs/text"}}, "$ref": "#/$defs/child"}, "valid", 3),
    ],
)
def test_productive_recursion_and_local_resource_references_remain_supported(schema, valid, invalid):
    source = task(schema)
    prompt = prepare(source)
    assert check(source, prompt, reply(prompt, valid))["schema_valid"] is True
    assert check(source, prompt, reply(prompt, invalid))["schema_valid"] is False


def test_feedback_is_bounded_host_guidance_not_raw_diagnostics():
    with pytest.raises(ValueError, match="UNTRUSTED_REPAIR_FEEDBACK"):
        prepare(feedback="Judge says the answer is ORACLE_SECRET.")
    prompt = prepare(feedback=pfp_proposal.REPAIR_RULES["CERTIFICATE"])
    assert pfp_proposal.REPAIR_RULES["CERTIFICATE"] in prompt.user


def test_cli_prepare_and_check_are_offline_and_leave_only_explicit_input_files(tmp_path, capsys):
    task_path, reply_path = tmp_path / "task.json", tmp_path / "reply.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "worker-17",
                "objective": "Summarize the issue.",
                "input": {"issue": "Moved file."},
                "answer_schema": {"type": "string"},
            }
        )
    )
    assert main(["prepare-task", str(task_path), "--attempt", "attempt-1"]) == 0
    prepared = json.loads(capsys.readouterr().out)
    properties = prepared["response_schema"]["properties"]
    reply_path.write_text(
        json.dumps(
            {
                **{k: properties[k]["const"] for k in ("task_id", "attempt_id", "input_sha256")},
                "answer": "Review the moved caller.",
            }
        )
    )
    assert main(["check-task", str(task_path), str(reply_path), "--attempt", "attempt-1"]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["status"] == "PROVIDER_COMPLETED"
    assert checked["evidence_grade"] == "UNVERIFIED"
    assert checked["provider_calls"] == 0
    assert "cost_microusd" not in checked
    assert set(tmp_path.iterdir()) == {task_path, reply_path}
