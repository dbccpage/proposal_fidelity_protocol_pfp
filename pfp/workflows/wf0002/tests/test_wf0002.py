"""Decisive WF2 controls; fixture replies never count as hosted model runs."""

import json
from copy import deepcopy
from hashlib import sha256

import pytest

from pfp.workflows.tests.gateways import make_gateway
from pfp.workflows.wf0001 import workflow as wf1
from pfp.workflows.wf0001.runner import runtime as wf1_runtime
from pfp.workflows.wf0002 import workflow as wf2
from pfp.workflows.wf0002.runner import runtime


@pytest.fixture
def spec():
    return json.loads(wf2.resource_text("examples/integer_sum.task.json"))


def candidate():
    slots = [
        dict(slot=row["id"], disposition="provided", value="Finite integer task.", reason="")
        for row in wf2.catalogue()["slots"]
    ]
    return dict(
        task_result={"total": 38},
        slot_report=slots,
        operad_candidates=[
            dict(
                id="sum",
                operation="sum the inputs",
                source_colours=["IntegerList"],
                target_colour="Integer",
                arity=1,
                source=dict(kind="seed_prompt", quote="input.values"),
                witness_refs=["task_result"],
            )
        ],
        ddc_moves=[
            dict(
                id="t1",
                op="T",
                operad_id="sum",
                before="input list",
                after="proposed sum",
                local_log="Candidate total emitted; host must check it.",
                refusal=None,
                witness_refs=["task_result"],
            )
        ],
    )


def reply(spec, answer):
    binding = wf2.prepare_task(spec).binding
    return json.dumps(
        {
            **{key: binding[key] for key in ("task_id", "attempt_id", "input_sha256")},
            "answer": answer,
        },
        ensure_ascii=False,
    ).encode()


def test_complete_catalogue_is_in_system_and_response_schema(spec):
    turn = wf2.prepare_task(spec)
    catalogue = wf2.catalogue()
    assert len(catalogue["slots"]) == 31
    assert len({row["group"] for row in catalogue["slots"]}) == 10
    assert all(row["id"] in turn.prompt.system for row in catalogue["slots"])
    assert catalogue["ddc_alphabet"] == ["E", "R", "C", "I", "Λ", "D", "M", "T"]
    rust = __import__("importlib.resources", fromlist=["files"]).files(wf2.PACKAGE).joinpath(catalogue["ddc_packaged_resource"])
    assert sha256(rust.read_bytes()).hexdigest() == catalogue["ddc_source_sha256"]
    assert set(turn.prompt.response_schema["properties"]["answer"]["properties"]) == {
        "task_result",
        "slot_report",
        "operad_candidates",
        "ddc_moves",
    }
    public = json.loads(turn.prompt.user)
    assert public["objective"] == spec["seed_prompt"]
    assert public["input"] == spec["input"]
    assert "answer_schema" not in public
    assert json.loads(turn.prompt.system.rsplit("\n", 1)[1]) == turn.prompt.response_schema


def test_correct_task_and_structurally_valid_candidates_are_separate_from_authority(spec):
    result = wf2.check_reply(spec, reply(spec, candidate()))
    assert result["status"] == "HOST_ACCEPTED" and result["operad_structure_valid"]
    collection = wf2.collect_emitted(spec, reply(spec, candidate()), result)
    assert collection["operads"][0]["disposition"] == "UNVERIFIED_CANDIDATE"
    assert collection["authority_effect"] == "None"


@pytest.mark.parametrize(
    "change,reason",
    [
        ("duplicate_slot", "SLOT_COVERAGE"),
        ("empty_provided", "EMPTY_PROVIDED_SLOT"),
        ("missing_reason", "MISSING_SLOT_REASON"),
        ("wrong_arity", "ARITY_MISMATCH"),
        ("bad_source", "SOURCE_QUOTE_MISSING"),
        ("missing_log", "DDC_LOG_OR_REFUSAL"),
        ("unknown_operad", "UNKNOWN_OPERAD_REF"),
        ("unknown_witness", "UNKNOWN_WITNESS_REF"),
    ],
)
def test_structural_defects_cannot_be_accepted(spec, change, reason):
    answer = candidate()
    if change == "duplicate_slot":
        answer["slot_report"][1] = deepcopy(answer["slot_report"][0])
    elif change == "empty_provided":
        answer["slot_report"][0]["value"] = ""
    elif change == "missing_reason":
        answer["slot_report"][5].update(disposition="not_applicable", value="", reason="")
    elif change == "wrong_arity":
        answer["operad_candidates"][0]["arity"] = 2
    elif change == "bad_source":
        answer["operad_candidates"][0]["source"]["quote"] = "NOT_IN_SOURCE"
    elif change == "missing_log":
        answer["ddc_moves"][0]["local_log"] = None
    elif change == "unknown_operad":
        answer["ddc_moves"][0]["operad_id"] = "invented"
    else:
        answer["ddc_moves"][0]["witness_refs"] = ["invented"]
    checked = wf2.check_reply(spec, reply(spec, answer))
    assert checked["schema_valid"] and not checked["operad_structure_valid"]
    assert checked["failure_class"] == "WF2_OPERAD_STRUCTURE"
    assert any(reason in issue for issue in checked["structure_errors"])


@pytest.mark.parametrize(
    "change", ["bool_arity", "bad_letter", "extra_authority", "bare_task_result"]
)
def test_exact_wire_contract_refuses_invalid_records(spec, change):
    answer = candidate()
    if change == "bool_arity":
        answer["operad_candidates"][0]["arity"] = True
    elif change == "bad_letter":
        answer["ddc_moves"][0]["op"] = "import"
    elif change == "extra_authority":
        answer["ddc_moves"][0]["authority_effect"] = "Granted"
    else:
        answer = answer["task_result"]
    checked = wf2.check_reply(spec, reply(spec, answer))
    assert not checked["schema_valid"] and checked["status"] != "HOST_ACCEPTED"


def test_wrong_task_result_is_not_rescued_by_rich_metadata(spec):
    answer = candidate()
    answer["task_result"]["total"] = 39
    result = wf2.check_reply(spec, reply(spec, answer))
    assert result["operad_structure_valid"]
    assert result["failure_class"] == "CERTIFICATE" and result["status"] != "HOST_ACCEPTED"


def test_duplicate_occurrences_are_kept_with_exact_utf8_spans(spec):
    answer = candidate()
    answer["operad_candidates"][0]["operation"] += " Ω"
    answer["operad_candidates"].append(deepcopy(answer["operad_candidates"][0]))
    answer["ddc_moves"].append(deepcopy(answer["ddc_moves"][0]))
    raw = reply(spec, answer)
    checked = wf2.check_reply(spec, raw)
    collection = wf2.collect_emitted(spec, raw, checked)
    assert len(collection["operads"]) == len(collection["ddc_moves"]) == 2
    assert collection["operads"][1]["duplicate_of"] == "operads:0000"
    for row in collection["operads"] + collection["ddc_moves"]:
        original = raw[row["start_byte"] : row["end_byte"]]
        assert json.loads(original) == row["record"]
        assert sha256(original).hexdigest() == row["raw_record_sha256"]
        assert row["disposition"] == "QUARANTINED"


@pytest.mark.parametrize("raw", [b"not json", b"{}", b'{"answer":{},"answer":{}}', b"\xff"])
def test_unparseable_material_remains_raw_without_invented_records(spec, raw):
    checked = wf2.check_reply(spec, raw)
    collection = wf2.collect_emitted(spec, raw, checked)
    assert not collection["operads"] and not collection["ddc_moves"]
    assert collection["raw_reply_sha256"] == sha256(raw).hexdigest()
    assert collection["residual_text_ledger"] or collection["status"] == "COLLECTED"


def test_schema_invalid_records_are_still_collected_and_quarantined(spec):
    answer = candidate()
    answer["operad_candidates"][0]["arity"] = "1"
    raw = reply(spec, answer)
    checked = wf2.check_reply(spec, raw)
    result = wf2.collect_emitted(spec, raw, checked)
    assert not checked["schema_valid"]
    assert result["operads"][0]["record"]["arity"] == "1"
    assert result["operads"][0]["disposition"] == "QUARANTINED"


def test_accounted_wf2_uses_one_call_and_replays_collection(tmp_path, spec):
    gateway, provider = make_gateway(tmp_path, max_calls=1, answer=candidate())
    root = tmp_path / "wf2"
    result = runtime.run_accounted(
        spec, root, gateway=gateway, model="vendor/model", max_output_tokens=256
    )
    assert result["status"] == "HOST_ACCEPTED" and len(provider.calls) == 1
    assert (root / "collection.json").exists()
    assert runtime.replay_run(root)["status"] == "HOST_ACCEPTED"
    assert result["provider"]["provider_elapsed_seconds"] >= 0


def test_collection_tampering_is_detected_even_with_rebound_manifest(tmp_path, spec):
    root = tmp_path / "wf2"
    runtime.prepare_run(spec, root)
    raw = tmp_path / "reply.json"
    raw.write_bytes(reply(spec, candidate()))
    runtime.check_run(root, raw, fixture=True)
    collection_path = root / "collection.json"
    collection = json.loads(collection_path.read_text())
    collection["operads"].clear()
    collection_path.write_text(json.dumps(collection))
    manifest_path = root / "receipt_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["collection.json"] = sha256(collection_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="COLLECTION_REPLAY_MISMATCH"):
        runtime.replay_run(root)


def test_wf1_and_wf2_are_segregated(tmp_path, spec):
    plain = dict(spec, task_id="wf1-separate")
    plain_reply = wf1.prepare_task(plain)
    assert "slot_report" not in plain_reply.prompt.response_schema["properties"]["answer"].get(
        "properties", {}
    )
    root = tmp_path / "wf2"
    runtime.prepare_run(spec, root)
    with pytest.raises(ValueError, match="WF1_MANIFEST_INVALID"):
        wf1_runtime._load_preparation(root)
    binding = plain_reply.binding
    wrong = json.dumps(
        {
            **{k: binding[k] for k in ("task_id", "attempt_id", "input_sha256")},
            "answer": candidate(),
        }
    ).encode()
    assert not wf2.check_reply(spec, wrong)["schema_valid"]


@pytest.mark.parametrize(
    "feature", ["pre_mining", "agents", "seed_rewrite", "lggr", "maximum_retries"]
)
def test_later_workflow_features_are_rejected(spec, feature):
    spec[feature] = True
    with pytest.raises(ValueError, match="WF2_INVALID_TASK_SPECIFICATION"):
        wf2.prepare_task(spec)
