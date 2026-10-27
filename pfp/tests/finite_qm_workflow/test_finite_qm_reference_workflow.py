"""Answer isolation, real shared ingress, custody and native certificate controls.

Fixture submissions are NO_LLM; no provider efficacy is measured here.
"""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from pfp.entrypoints.cli.finite_qm_prompt import main, verify_source_pins
from pfp.infrastructure.finite_qm_prompt import (
    SLOTS,
    load_catalog,
    prepare_finite_qm_turn,
    render_system_prompt,
)

ROOT = Path(__file__).resolve().parents[3]
UNIT = ROOT / "pfp/fixtures/finite_qm_workflow/c4_work_unit.json"


@pytest.fixture
def unit():
    return json.loads(UNIT.read_text())


def certificate():
    def q(x):
        return dict(num=x, den=1)

    return dict(
        potential=[q(x) for x in (0, 2, -1, 4)],
        dual_witness=[q(x) for x in (-1, -1, -1, 1)],
        phi1=q(3),
        gamma2=q(3),
    )


def reply(turn, answer):
    return json.dumps(
        {
            key: turn.prompt.response_schema["properties"][key]["const"]
            for key in ("task_id", "attempt_id", "input_sha256")
        }
        | {"answer": answer}
    ).encode()


def test_system_prompt_requests_derivation_and_does_not_serialize_the_catalog():
    system = render_system_prompt()
    assert "Your job is to derive" in system
    assert "FIRST, MINE THE FOUR MISSIONS" in system
    assert "THEN DERIVE AND CHECK" in system
    assert "OPERAD TOOLBOX" in system
    assert "SOURCE-BOUNDED OPERAD REFERENCE CATALOG" not in system
    assert '"source_id"' not in system and '"executor_state"' not in system
    assert len(system.encode("utf-8")) < 20_000
    saved = (
        ROOT
        / "education/documentation/004_oepfp/_how_to_play/v4_operad_container_and_p_star_loop/finite_qm_pfp_system_prompt.md"
    )
    assert saved.read_text(encoding="utf-8") == system


def test_catalog_projection_retains_entire_registry_and_declares_execution():
    registry = json.loads((ROOT / ".agents/skill_operads/operad_signature.json").read_text())
    catalog = load_catalog()
    for kind, key in (("skill_operation", "operations"), ("identity", "identities")):
        actual = {x["name"]: x for x in catalog["entries"] if x["kind"] == kind}
        assert set(actual) == {x["skill_id"] for x in registry[key]}
        for op in registry[key]:
            assert actual[op["skill_id"]]["inputs"] == op["source_colours"]
            assert actual[op["skill_id"]]["output"] == op["target_colour"]
    for source, record in catalog["sources"].items():
        if not source.startswith("finite_qm_companion/"):
            assert sha256((ROOT / source).read_bytes()).hexdigest() == record["sha256"]


def test_preparation_preserves_input_and_does_not_run_a_checker(unit):
    original = deepcopy(unit)
    turn = prepare_finite_qm_turn(unit, attempt_id="control-1", compact=True)
    assert unit == original
    assert "OPERATIONS SELECTED FOR THIS TASK" in turn.prompt.system
    assert "- cochain_evaluate: (" in turn.prompt.system
    assert "skill_operation:governance-pfp" not in turn.prompt.system
    assert "NATIVE_CERTIFICATE_CHECKED" not in turn.prompt.system
    assert turn.binding["checker_id"] == unit["checker_id"]
    request = json.loads(turn.task.case["prompt"])
    assert request["mode_id"] == "FINITE_QM_DERIVATION"
    assert request["run_limits"]["max_candidate_attempts"] == 2
    assert "{{" not in request["instructions"]
    assert json.loads(turn.prompt.user)["objective"] == unit["objective"]
    assert len(turn.prompt.user) < len(turn.prompt.system) * 2
    verify_source_pins(unit, ROOT)


def test_compatibility_flag_cannot_restore_the_registry_dump(unit):
    full = prepare_finite_qm_turn(unit, attempt_id="same-attempt")
    compact = prepare_finite_qm_turn(unit, attempt_id="same-attempt", compact=True)
    assert full.prompt.system == compact.prompt.system
    assert full.binding["input_sha256"] == compact.binding["input_sha256"]


def test_workflow_has_linked_stages_one_mode_and_attached_llm_techniques():
    from pfp.infrastructure.yaml_loading import strict_yaml_load

    profile = ROOT / "pfp/infrastructure/yaml/prompts/finite_qm"
    template, workflow, mode = [
        strict_yaml_load((profile / name).read_text(encoding="utf-8"))
        for name in ("prompt_template.yaml", "workflow.yaml", "mode.yaml")
    ]
    assert template["workflow"] == "workflow.yaml" and workflow["mode"] == "mode.yaml"
    assert mode["mode_id"] == "FINITE_QM_DERIVATION"
    stages = {stage["id"]: stage for stage in workflow["stages"]}
    assert len(stages) == 6
    assert workflow["entry_stage"] in stages and workflow["terminal_stage"] in stages
    techniques = {item["id"] for item in mode["llm_techniques"]}
    assert len(techniques) == 6
    for stage in stages.values():
        assert stage["instruction"].strip()
        assert set(stage.get("llm_techniques", [])) <= techniques
        assert set(stage.get("transitions", {}).values()) <= set(stages)
        if "next" in stage:
            assert stage["next"] in stages


def test_repair_stage_uses_fresh_original_input_and_only_bounded_guidance(unit):
    first = prepare_finite_qm_turn(unit, attempt_id="same-attempt")
    repaired = prepare_finite_qm_turn(
        unit, attempt_id="same-attempt", stage_id="P3_REPAIR", failure_codes=("G3_WITNESS",)
    )
    initial_data, repair_data = [json.loads(t.task.case["prompt"]) for t in (first, repaired)]
    assert initial_data["operad_slots"] == repair_data["operad_slots"]
    assert "G3_WITNESS" in repair_data["instructions"]
    assert "complete replacement certificate" in repair_data["instructions"]
    assert first.binding["input_sha256"] != repaired.binding["input_sha256"]
    assert repaired.check(reply(first, certificate()))["schema_valid"] is False


@pytest.mark.parametrize(
    "stage,codes",
    [
        ("P2_VERIFY", ()),
        ("P3_REPAIR", ()),
        ("P1_DERIVE", ("G3_WITNESS",)),
        ("P3_REPAIR", ("expected answer = 3",)),
    ],
)
def test_invalid_stage_or_leaking_feedback_is_not_dispatched(unit, stage, codes):
    with pytest.raises(ValueError):
        prepare_finite_qm_turn(unit, attempt_id="a", stage_id=stage, failure_codes=codes)


@pytest.mark.parametrize("slot", SLOTS)
def test_unfilled_mission_stops_before_dispatch(unit, slot):
    unit["operad_slots"][slot]["mining_status"] = "UNFILLED"
    with pytest.raises(ValueError, match="UNFILLED_OR_INVALID_MISSION"):
        prepare_finite_qm_turn(unit, attempt_id="a")


@pytest.mark.parametrize(
    "key", ["ground_truth", "oracle_answer", "expected_answer", "value_expected"]
)
def test_labelled_judge_data_is_rejected_at_any_depth(unit, key):
    unit["operad_slots"][SLOTS[0]]["public_input"]["nested"] = [{key: "PRIVATE_ORACLE_CANARY"}]
    with pytest.raises(ValueError, match="PRIVATE_OR_INVALID_PUBLIC_FIELD"):
        prepare_finite_qm_turn(unit, attempt_id="a")


@pytest.mark.parametrize("change", ["constant", "example", "default", "float_type"])
def test_witness_schema_cannot_encode_reference_values(unit, change):
    target = unit["answer_schema"]["$defs"]["rational"]["properties"]["num"]
    target.update(
        {
            "constant": {"const": 982451653},
            "example": {"examples": [982451653]},
            "default": {"default": 982451653},
            "float_type": {"type": "number"},
        }[change]
    )
    with pytest.raises(ValueError):
        prepare_finite_qm_turn(unit, attempt_id="a")


@pytest.mark.parametrize("change", ["unknown", "signature", "duplicate"])
def test_catalog_slice_and_signature_are_bound(unit, change):
    if change == "unknown":
        unit["selected_catalog_ids"] = ["skill_operation:invented-capability"]
    elif change == "signature":
        unit["operad_slots"][SLOTS[1]]["operations"][0]["inputs"].reverse()
    else:
        unit["selected_catalog_ids"] *= 2
    with pytest.raises(ValueError):
        prepare_finite_qm_turn(unit, attempt_id="a")


def test_literature_reference_cannot_become_an_executable_generator(unit):
    unit["selected_catalog_ids"] = ["literature:As"]
    unit["operad_slots"][SLOTS[1]]["operations"][0]["catalog_id"] = "literature:As"
    with pytest.raises(ValueError, match="REFERENCE_ONLY_CATALOG_ENTRY"):
        prepare_finite_qm_turn(unit, attempt_id="a")


def test_source_bytes_cannot_change_behind_the_pin(unit, tmp_path):
    path = tmp_path / "source.json"
    path.write_bytes(b'{"task":1}')
    unit["operad_slots"][SLOTS[0]]["source_pins"] = [
        dict(path="source.json", sha256=sha256(path.read_bytes()).hexdigest())
    ]
    verify_source_pins(unit, tmp_path)
    path.write_bytes(b'{"task":2}')
    with pytest.raises(ValueError, match="SOURCE_DIGEST_MISMATCH"):
        verify_source_pins(unit, tmp_path)


def test_pin_cannot_escape_source_root(unit, tmp_path):
    unit["operad_slots"][SLOTS[0]]["source_pins"][0]["path"] = "../escape"
    with pytest.raises(ValueError, match="SOURCE_OUTSIDE_DECLARED_ROOT"):
        verify_source_pins(unit, tmp_path)


@pytest.mark.parametrize(
    "mutation", ["bool", "float", "numeric_string", "duplicate_key", "fences", "binding"]
)
def test_real_shared_ingress_rejects_bad_reply_before_judge(unit, mutation):
    turn = prepare_finite_qm_turn(unit, attempt_id="a", compact=True)
    answer = certificate()
    if mutation in ("bool", "float", "numeric_string"):
        answer["phi1"]["num"] = {"bool": True, "float": 3.0, "numeric_string": "3"}[mutation]
    raw = reply(turn, answer)
    if mutation == "duplicate_key":
        raw = raw.replace(b'"num": 3', b'"num": 3, "num": 3', 1)
    elif mutation == "fences":
        raw = b"```json\n" + raw + b"\n```"
    elif mutation == "binding":
        data = json.loads(raw)
        data["input_sha256"] = "0" * 64
        raw = json.dumps(data).encode()
    calls = []
    result = turn.check(
        raw, judges=(("spy", lambda *args: calls.append(args)),), require_checker=True
    )
    assert result["schema_valid"] is False and result["status"] != "HOST_ACCEPTED"
    assert calls == []


def test_missing_checker_never_becomes_acceptance(unit):
    turn = prepare_finite_qm_turn(unit, attempt_id="a", compact=True)
    result = turn.check(reply(turn, certificate()), require_checker=True)
    assert result["failure_class"] == "UNREGISTERED_CHECKER"
    assert result["status"] == "INFRASTRUCTURE_ERROR"


def test_recorded_bytes_replay_and_one_byte_tamper(unit):
    turn = prepare_finite_qm_turn(unit, attempt_id="a", compact=True)
    record = turn.check(reply(turn, certificate()))
    assert turn.replay(record)["schema_valid"] is True
    record["raw_reply_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="REPLAY_RAW_MISMATCH"):
        turn.replay(record)


def test_native_certificate_positive_and_decisive_mutations(unit):
    from pfp.ffi import RustSymbolGameHost
    from pfp.infrastructure.finite_qm_cochain_judge import (
        CHECKER_ID,
        NativeCochainJudge,
    )

    judge = NativeCochainJudge(RustSymbolGameHost())
    turn = prepare_finite_qm_turn(unit, attempt_id="native-control", compact=True)
    good = certificate()
    accepted = turn.check(reply(turn, good), judges=((CHECKER_ID, judge),), require_checker=True)
    assert accepted["status"] == "HOST_ACCEPTED", accepted
    for field in ("potential", "dual_witness", "phi1", "gamma2"):
        bad = deepcopy(good)
        target = bad[field][0] if isinstance(bad[field], list) else bad[field]
        target["num"] += 1
        result = turn.check(reply(turn, bad), judges=((CHECKER_ID, judge),), require_checker=True)
        assert result["status"] == "PROVIDER_COMPLETED", (field, result)
        assert result["failure_class"] == "CERTIFICATE"
    bad = deepcopy(good)
    bad["phi1"] = dict(num=6, den=2)
    assert (
        turn.check(reply(turn, bad), judges=((CHECKER_ID, judge),), require_checker=True)[
            "failure_class"
        ]
        == "CERTIFICATE"
    )
    assert len(judge.receipts) == 5
    changed = deepcopy(unit)
    changed["operad_slots"][SLOTS[0]]["coefficient_ring"] = "F2"
    other = prepare_finite_qm_turn(changed, attempt_id="different-ring", compact=True)
    assert (
        other.check(reply(other, good), judges=((CHECKER_ID, judge),), require_checker=True)[
            "failure_class"
        ]
        == "CERTIFICATE"
    )
    # Constant shifts really are a gauge symmetry: the native checker accepts a
    # new potential with the same edge coboundary, rather than comparing a vector.
    shifted = deepcopy(good)
    for value in shifted["potential"]:
        value["num"] += 7
    assert (
        turn.check(reply(turn, shifted), judges=((CHECKER_ID, judge),), require_checker=True)[
            "status"
        ]
        == "HOST_ACCEPTED"
    )


def test_cli_prepares_and_checks_actual_fixture_bytes(unit, tmp_path, capsys):
    prepared = ["prepare", str(UNIT), "--source-root", str(ROOT), "--attempt", "cli-1", "--compact"]
    assert main(prepared) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["provider_calls"] == 0 and printed["checker_status"] == "NOT_RUN"
    turn = prepare_finite_qm_turn(unit, attempt_id="cli-1", compact=True)
    path = tmp_path / "no_llm_fixture_reply.json"
    path.write_bytes(reply(turn, certificate()))
    assert (
        main(
            [
                "check",
                str(UNIT),
                str(path),
                "--source-root",
                str(ROOT),
                "--attempt",
                "cli-1",
                "--compact",
            ]
        )
        == 0
    )
    checked = json.loads(capsys.readouterr().out)
    assert checked["status"] == "HOST_ACCEPTED"
    assert checked["capture_origin"] == "SUBMITTED_BYTES_NOT_A_LIVE_RUN"
