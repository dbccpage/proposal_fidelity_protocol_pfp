"""Focused preflights for the new opt-in numbered PO035 prompt recipe."""

import ast
import copy
from pathlib import Path

import jsonschema
import pytest
import yaml

from omega_engine_pfp.infrastructure import numbered_prompts as prompts
from omega_engine_pfp.infrastructure.adapters.pfp_evidence import canonical, digest
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID, CERTIFICATES, ROOT
from omega_engine_woland.tests.pilots.relational_spacetime.trial_prompts import SECTION_5_SHA256


def _workpad(pilot):
    return {
        "derived_under_policy": "SPK-001",
        "prompt_id": prompts.prompt_id(pilot, 2),
        "records": [
            {
                "field": next(iter(prompts.FIELD_CARRIERS[pilot])),
                "expression": "Identify the domain of the named map.",
                "result": "Open; no mathematical result asserted.",
            }
        ],
        "open": ["Complete the original analytical obligations."],
    }


def _typed_value(schema):
    if schema["type"] == "array":
        return [_typed_value(schema["items"]) for _ in range(schema["minItems"])]
    return {"string": "13/17", "boolean": False, "integer": 7}[schema["type"]]


def _final(pilot, stage=1):
    fields = CERTIFICATES[BY_ID[pilot]["number"] - 199]["properties"]
    certificate = {field: _typed_value(schema) for field, schema in fields.items()}
    return {
        "derived_under_policy": "SPK-001",
        "summary": {
            "narrowest_defensible_thesis": "An unverified conditional proposal.",
            "evidence_scope": "Schema test data; no fixture claim.",
            "next_concrete_test": "Check the original mathematical obligations.",
        },
        "process_integrity": {
            "seed_allows_theory_refutation": True,
            "should_continue": True,
        },
        "sections": [
            {
                "name": "po035_derivation",
                "rows": [
                    {
                        "prompt_id": prompts.prompt_id(pilot, stage),
                        "status": "PROPOSAL",
                        "derivation": {
                            "argument": "An unfinished conditional argument; no theorem is asserted.",
                            "open": [],
                        },
                        "calculations": {
                            field: {
                                "carrier": prompts.FIELD_CARRIERS[pilot][field],
                                "expression": "Unverified test expression.",
                                "result": copy.deepcopy(value),
                            }
                            for field, value in certificate.items()
                        },
                        "certificate": certificate,
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize("pilot", BY_ID)
@pytest.mark.parametrize("stage", [1, 2, 3])
def test_exact_seed_source_scope_and_stage_binding(pilot, stage):
    prompt = prompts.build_prompt(pilot, stage)
    wire = yaml.safe_load(prompt["user_prompt"])
    assert wire["original_seed"] == prompt["original_seed"] == BY_ID[pilot]["text"]
    assert prompt["original_seed_sha256"] == digest(BY_ID[pilot]["text"].encode())
    assert wire["prompt_id"] == prompt["prompt_id"] == prompts.prompt_id(pilot, stage)
    assert wire["role"] == prompts.ROLES[stage - 1]
    assert len(wire["procedural_advice_untrusted"]) == 3
    assert prompt["source_obligations"] == BY_ID[pilot]["obligations"]
    assert "response_schema" not in wire
    assert "candidate_guidance" not in wire
    assert wire["output_layout"]["root_required_only"]["derived_under_policy"] == "SPK-001"
    assert prompt["schema_sidecar_only"] is True
    assert (
        prompt["stage_config"]["temperature"] == prompt["experiment_decoding"]["temperature"] == 0
    )
    assert prompt["experiment_decoding"]["seed"] == 20261012 + BY_ID[pilot]["number"]
    assert prompt["generation"] == stage
    assert prompt["max_output_tokens"] == [2500, 600, 2500][stage - 1]
    assert prompt["provider_dispatches"] == 0
    assert prompt["analytical_status"] == "UNVERIFIED"
    assert prompt["construction_sha256"] == digest(Path(prompts.__file__).read_bytes())
    assert prompt["rendered_user_sha256"] == digest(prompt["user_prompt"].encode())
    assert prompt["response_schema_sha256"] == digest(canonical(prompt["response_schema"]))
    assert prompt["rendered_prompt_sha256"] == digest(
        canonical({"system_prompt": prompt["system_prompt"], "user_prompt": prompt["user_prompt"]})
    )
    assert prompt["system_variant_sha256"] == digest(prompt["system_prompt"].encode())
    jsonschema.Draft202012Validator.check_schema(prompt["response_schema"])
    system = yaml.safe_load(prompt["system_prompt"])
    assert (
        "overrides the base import_boundary" in system["po035_conditional_scope_v1"]["precedence"]
    )
    if pilot == "pilot_0000201":
        excerpt = wire["source_context"]["section_5"]
        assert digest(excerpt.encode()) == SECTION_5_SHA256
        assert all(f"Stage {n}:" in excerpt for n in range(1, 9))


@pytest.mark.parametrize("pilot", BY_ID)
def test_final_layout_covers_every_certificate_field_and_exact_carrier(pilot):
    prompt = prompts.build_prompt(pilot, 1)
    layout = yaml.safe_load(prompt["user_prompt"])["output_layout"]
    certificate = CERTIFICATES[BY_ID[pilot]["number"] - 199]
    fields = certificate["properties"]
    assert set(layout["certificate_fields"]) == set(prompts.FIELD_CARRIERS[pilot]) == set(fields)
    schema = prompt["response_schema"]
    jsonschema.validate(_final(pilot), schema)
    row = schema["properties"]["sections"]["items"]["properties"]["rows"]["items"]
    assert set(row["required"]) == {
        "prompt_id",
        "status",
        "derivation",
        "calculations",
        "certificate",
    }
    for field in fields:
        assert (
            layout["certificate_fields"][field]["carrier"] == prompts.FIELD_CARRIERS[pilot][field]
        )
        calculation = row["properties"]["calculations"]["anyOf"][0]["properties"][field]
        assert calculation["properties"]["carrier"] == {
            "const": prompts.FIELD_CARRIERS[pilot][field]
        }
        assert calculation["properties"]["result"] == fields[field]
    assert row["properties"]["certificate"]["anyOf"][0] == certificate


@pytest.mark.parametrize("pilot", BY_ID)
def test_refusal_requires_null_calculations_and_certificate(pilot):
    schema = prompts.response_schema(pilot, prompt_id=prompts.prompt_id(pilot, 1))
    packet = _final(pilot)
    row = packet["sections"][0]["rows"][0]
    row["status"] = "TYPED_REFUSAL"
    assert not jsonschema.Draft202012Validator(schema).is_valid(packet)
    row["calculations"] = row["certificate"] = None
    jsonschema.validate(packet, schema)
    row["status"] = "PROPOSAL"
    assert not jsonschema.Draft202012Validator(schema).is_valid(packet)


@pytest.mark.parametrize("pilot", BY_ID)
def test_final_accepts_only_same_pilot_workpad_and_ignores_control_context(pilot):
    workpad = _workpad(pilot)
    context = {
        "workpad": workpad,
        "control_reply": "CONTROL_SECRET",
        "previous_proposal": "PREVIOUS_SECRET",
        "workpads": {"draft": "HISTORICAL_SECRET"},
        "guidance": [{"text": "INJECTED_SECRET"}],
    }
    before = copy.deepcopy(context)
    final = prompts.build_prompt(pilot, 3, context)
    wire = yaml.safe_load(final["user_prompt"])
    assert context == before
    assert wire["public_workpad_untrusted"] == workpad
    assert final["parent_prompt_id"] == prompts.prompt_id(pilot, 2)
    for secret in ["CONTROL_SECRET", "PREVIOUS_SECRET", "HISTORICAL_SECRET", "INJECTED_SECRET"]:
        assert secret not in final["user_prompt"]
    for stage in [1, 2]:
        earlier = prompts.build_prompt(pilot, stage, context)
        assert "public_workpad_untrusted" not in yaml.safe_load(earlier["user_prompt"])


@pytest.mark.parametrize(
    "mutation",
    [
        "control_id",
        "different_pilot",
        "old_recipe",
        "extra_key",
        "long_expression",
        "long_result",
        "too_many_records",
        "candidate_certificate",
        "wrong_stamp",
        "unknown_field",
    ],
)
def test_workpad_corruption_cannot_enter_final(mutation):
    pilot = "pilot_0000200"
    packet = _workpad(pilot)
    if mutation == "control_id":
        packet["prompt_id"] = prompts.prompt_id(pilot, 1)
    elif mutation == "different_pilot":
        packet["prompt_id"] = prompts.prompt_id("pilot_0000201", 2)
    elif mutation == "old_recipe":
        packet["prompt_id"] = "pilot_0000200:po035:experiment-v1:scratchpad:02"
    elif mutation == "extra_key":
        packet["extra"] = "UNTRUSTED"
    elif mutation == "long_expression":
        packet["records"][0]["expression"] = "x" * 181
    elif mutation == "long_result":
        packet["records"][0]["result"] = "x" * 121
    elif mutation == "too_many_records":
        packet["records"] *= 4
    elif mutation == "candidate_certificate":
        packet["candidate_certificate"] = {}
    elif mutation == "unknown_field":
        packet["records"][0]["field"] = "unknown_task_field"
    else:
        packet["derived_under_policy"] = "UNMARKED"
    with pytest.raises(ValueError, match="WORKPAD_SCHEMA_OR_IDENTITY_MISMATCH"):
        prompts.build_prompt(pilot, 3, {"workpad": packet})


def test_missing_workpad_note_is_fixed_and_never_math_feedback():
    prompt = prompts.build_prompt("pilot_0000199", 3, {"workpad_missing": True})
    wire = yaml.safe_load(prompt["user_prompt"])
    assert wire["public_workpad_untrusted"] is None
    assert wire["workpad_missing_untrusted"] == (
        "No schema-valid workpad was supplied. No mathematical failure or answer is inferred."
    )
    with pytest.raises(ValueError, match="INVALID_WORKPAD_MISSING_FLAG"):
        prompts.build_prompt("pilot_0000199", 3, {"workpad_missing": "answer feedback"})
    with pytest.raises(ValueError, match="CONFLICT"):
        prompts.build_prompt(
            "pilot_0000199", 3, {"workpad_missing": True, "workpad": _workpad("pilot_0000199")}
        )


def test_duplicate_workpad_fields_cannot_enter_final():
    packet = _workpad("pilot_0000199")
    packet["records"] *= 2
    with pytest.raises(ValueError, match="DUPLICATE_WORKPAD_FIELD"):
        prompts.build_prompt("pilot_0000199", 3, {"workpad": packet})


def test_workpad_and_final_layouts_match_strict_contract_keys():
    pilot = "pilot_0000199"
    prompt = prompts.build_prompt(pilot, 2)
    jsonschema.validate(_workpad(pilot), prompt["response_schema"])
    wire = yaml.safe_load(prompt["user_prompt"])
    assert set(wire["output_layout"]["root_required_only"]) == set(
        prompt["response_schema"]["required"]
    )
    assert "private reasoning" in wire["contract"]
    final = prompts.build_prompt(pilot, 1)
    final_wire = yaml.safe_load(final["user_prompt"])
    assert "overrides only the original seed" in final_wire["contract"]
    assert "learning is mined offline" in final_wire["contract"]
    assert "hidden" not in set(prompt["response_schema"]["properties"])


def test_registry_roles_exact_filenames_history_and_one_candidate_default():
    registry = yaml.safe_load((ROOT / prompts.REGISTRY_PATH).read_bytes())
    assert digest((ROOT / prompts.REGISTRY_PATH).read_bytes()) == prompts.REGISTRY_SHA256
    assert registry["default_recipe_within_profile"] == prompts.RECIPE
    assert registry["production_global_default_changed"] is False
    assert len(registry["recipes"]) == 1
    for stage, identity in enumerate(prompts.ROLE_IDS, 1):
        entry = registry["roles"][identity]
        assert entry["status"] == "EXPERIMENTAL_CANDIDATE"
        assert set(["owner", "status", "supersedes", "deprecates", "compatibility"]) <= set(entry)
        assert Path(entry["path"]).name == f"template_{identity.lower().replace('-', '_')}.yaml"
        template = yaml.safe_load((ROOT / entry["path"]).read_bytes())
        assert template["role"] == prompts.ROLES[stage - 1]
        assert template["max_output_tokens"] == prompts.stage_config(stage)["max_output_tokens"]
    for path, expected in registry["file_sha256"].items():
        assert digest((ROOT / path).read_bytes()) == expected
    assert registry["history"][0]["kind"] == "FROZEN_UNNUMBERED_BASE_TEMPLATE"


def test_current_profile_supersedes_without_repinning_frozen_registry():
    assert prompts.VERSION == "1.0.4"
    assert prompts.REGISTRY_PATH.startswith("omega_engine_pfp/")
    registry = prompts._registry()
    assert registry["profile_version_state"] == "CURRENT"
    frozen = registry["history"][1]
    assert frozen["kind"] == "FROZEN_PROMPT_ROLE_REGISTRY"
    assert frozen["sha256"] == "34df63f05c168570e7942dc7cd4c4ddd4911723f35996dc008390bdc4e504d68"
    from omega_engine_pfp.infrastructure.adapters.pfp_frozen_replay import read_frozen_prompt_source

    assert digest(read_frozen_prompt_source(frozen["path"])) == frozen["sha256"]
    assert all(
        not path.startswith("omega_engine_education/pfp/")
        for path in registry["file_sha256"]
    )
    for identity, entry in registry["roles"].items():
        assert entry["version"] == prompts.VERSION
        assert entry["supersedes"] == [f"{identity}-v1.0.3"]
        current = yaml.safe_load((ROOT / entry["path"]).read_bytes())
        historical_path = str(Path(frozen["path"]).with_name(f"{identity}-v1.0.0.yaml"))
        historical = yaml.safe_load(read_frozen_prompt_source(historical_path.replace("\\", "/")))
        assert current["instructions"] == historical["instructions"]


def test_tampered_versioned_input_refused_without_touching_real_files(monkeypatch):
    real_read = Path.read_bytes
    target = "template_pfp_t0001.yaml"

    def changed_read(path):
        data = real_read(path)
        return data + b" " if path.name == target else data

    monkeypatch.setattr(Path, "read_bytes", changed_read)
    with pytest.raises(ValueError, match="VERSIONED_PROMPT_INPUT_CHANGED"):
        prompts.build_prompt("pilot_0000199", 1)


def test_tampered_current_construction_input_refused(monkeypatch):
    real_read = Path.read_bytes
    target = ROOT / "omega_engine_woland/tests/pilots/relational_spacetime/tasks.py"

    def changed_read(path):
        data = real_read(path)
        return data + b" " if path == target else data

    monkeypatch.setattr(Path, "read_bytes", changed_read)
    with pytest.raises(ValueError, match="VERSIONED_PROMPT_INPUT_CHANGED"):
        prompts.build_prompt("pilot_0000199", 1)


def test_builder_has_no_oracle_imports_or_fixture_outputs_in_advice():
    source = Path(prompts.__file__).read_text(encoding="utf-8")
    imports = [
        node.module or ""
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom)
    ]
    assert all("checking" not in name and "oracle" not in name for name in imports)
    for pilot in BY_ID:
        prompt = prompts.build_prompt(pilot, 1)
        advice = yaml.safe_load(prompt["user_prompt"])["procedural_advice_untrusted"]
        text = " ".join(advice)
        assert not any(character.isdigit() for character in text)
        assert all(value not in text for value in ["7/8", "(0,-2,-1)", "3/100000000"])
        schema = prompts.response_schema(pilot)
        schema["properties"]["sections"]["items"]["properties"]["rows"]["items"]["properties"][
            "certificate"
        ]["anyOf"][0]["properties"].clear()
        assert CERTIFICATES[BY_ID[pilot]["number"] - 199]["properties"]


@pytest.mark.parametrize("stage", [0, 4, True, 1.0, "SINGLE_SHOT"])
def test_unknown_stages_fail_closed(stage):
    with pytest.raises(ValueError, match="UNKNOWN_SIMPLIFIED_STAGE"):
        prompts.stage_config(stage)


def test_invalid_context_and_unknown_pilot_fail_closed():
    with pytest.raises(ValueError, match="INVALID_SIMPLIFIED_CONTEXT"):
        prompts.build_prompt("pilot_0000199", 1, [])
    with pytest.raises(ValueError, match="UNKNOWN_PO035_PILOT"):
        prompts.build_prompt("pilot_0000001", 1)


@pytest.mark.parametrize("pilot", BY_ID)
def test_distinct_runs_are_bound_instances_of_identical_role_version(pilot):
    first = prompts.build_prompt(pilot, 1, run_id="campaign_a")
    second = prompts.build_prompt(pilot, 1, run_id="campaign_b")
    assert first["prompt_id"] != second["prompt_id"]
    assert first["prompt_uri"] != second["prompt_uri"]
    assert first["rendered_prompt_sha256"] != second["rendered_prompt_sha256"]
    for key in [
        "recipe",
        "role_id",
        "role_template_sha256",
        "registry_sha256",
        "original_seed_sha256",
        "system_prompt",
    ]:
        assert first[key] == second[key]
    assert first["run_id"] == "campaign_a"
    assert second["run_id"] == "campaign_b"
    assert prompts.prompt_id(pilot, 1) == prompts.prompt_id(pilot, 1, run_id=prompts.DEFAULT_RUN_ID)


@pytest.mark.parametrize("pilot", BY_ID)
def test_another_run_workpad_rejected_without_template_version_change(pilot):
    workpad = _workpad(pilot)
    workpad["prompt_id"] = prompts.prompt_id(pilot, 2, run_id="campaign_a")
    with pytest.raises(ValueError, match="WORKPAD_SCHEMA_OR_IDENTITY_MISMATCH"):
        prompts.build_prompt(pilot, 3, {"workpad": workpad}, run_id="campaign_b")
    own = prompts.build_prompt(pilot, 3, {"workpad": workpad}, run_id="campaign_a")
    assert own["parent_prompt_id"] == workpad["prompt_id"]
    assert yaml.safe_load(own["user_prompt"])["public_workpad_untrusted"] == workpad


@pytest.mark.parametrize(
    "run_id", [None, True, 1, "", "Uppercase", "x/y", "a:b", "a x", "a" * 65, "_bad", "ä"]
)
def test_invalid_run_ids_refused_before_render_or_context_carry(run_id):
    pilot = "pilot_0000199"
    with pytest.raises(ValueError, match="INVALID_SIMPLIFIED_RUN_ID"):
        prompts.prompt_id(pilot, 1, run_id=run_id)
    with pytest.raises(ValueError, match="INVALID_SIMPLIFIED_RUN_ID"):
        prompts.build_prompt(pilot, 1, run_id=run_id)
    with pytest.raises(ValueError, match="INVALID_SIMPLIFIED_RUN_ID"):
        prompts._own_workpad(pilot, {}, run_id=run_id)


def test_maximum_run_id_fits_full_prompt_identity_schema_bound():
    identity = prompts.prompt_id("pilot_0000199", 3, run_id="a" * 64)
    assert len(identity) <= 200
