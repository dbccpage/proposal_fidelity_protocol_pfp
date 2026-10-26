"""Offline prompt preflights: custody, isolation, explicit scope and strict records."""

import copy
import json

import jsonschema
import pytest
import yaml

from omega_engine_woland.tests.pilots.relational_spacetime import trial_prompts as prompts
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import ROOT
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import TEMPLATE
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import response_schema
from omega_engine_pfp.infrastructure.adapters.pfp_evidence import digest


def public_workpad(pilot, loop):
    prompt = prompts.build_prompt(pilot, loop, experiment="scratchpad")
    return {
        "derived_under_policy": "SPK-001",
        "workpad_schema": prompts.WORKPAD_SCHEMA_ID,
        "prompt_id": prompt["prompt_id"],
        "stage": "draft" if loop == 2 else "audit",
        "public_records": [
            {
                "record_id": "domain_audit",
                "carrier": "declared seed carrier",
                "kind": "obligation",
                "expression": "A named mathematical obligation remains to check.",
                "justification": "No result is asserted by this test record.",
                "status": "OPEN",
            }
        ],
        "candidate_certificate": None,
        "open_obligations": ["Complete the original seed obligations."],
    }


@pytest.mark.parametrize("pilot", BY_ID)
@pytest.mark.parametrize(
    "experiment,loop",
    [("scratchpad", n) for n in range(1, 5)] + [("temperature", 1), ("temperature", 2)],
)
def test_seed_template_and_original_judge_schema_preserved(pilot, experiment, loop):
    template_before = (ROOT / TEMPLATE).read_bytes()
    prompt = prompts.build_prompt(pilot, loop, experiment=experiment)
    user = json.loads(prompt["user_prompt"])
    assert prompt["original_seed"] == user["original_seed"] == BY_ID[pilot]["text"]
    assert prompt["original_seed_sha256"] == digest(BY_ID[pilot]["text"].encode())
    assert prompt["template_sha256"] == digest(template_before)
    assert (ROOT / TEMPLATE).read_bytes() == template_before
    assert prompt["system_prompt"].startswith(yaml.safe_load(template_before)["system_prompt"])
    system = yaml.safe_load(prompt["system_prompt"])
    assert (
        "overrides the base import_boundary" in system["po035_conditional_scope_v1"]["precedence"]
    )
    assert prompt["system_variant_sha256"] == digest(prompt["system_prompt"].encode())
    jsonschema.Draft202012Validator.check_schema(prompt["response_schema"])
    if prompt["stage_config"]["response_kind"] == "spk_final":
        assert prompt["response_schema"] == response_schema(pilot)
    assert prompt["provider_dispatches"] == 0


@pytest.mark.parametrize("pilot", BY_ID)
def test_temperature_arms_have_identical_wire_except_fresh_identity(pilot):
    control = prompts.build_prompt(
        pilot, 1, {"previous_proposal": "CONTROL_SECRET"}, experiment="temperature"
    )
    variant = prompts.build_prompt(
        pilot, 2, {"previous_proposal": "OTHER_SECRET"}, experiment="temperature"
    )
    assert control["system_prompt"] == variant["system_prompt"]
    left, right = json.loads(control["user_prompt"]), json.loads(variant["user_prompt"])
    assert left.pop("prompt_id") != right.pop("prompt_id")
    assert left == right
    assert control["stage_config"]["temperature"] == 0
    assert variant["stage_config"]["temperature"] == 0.7
    assert "CONTROL_SECRET" not in control["user_prompt"]


@pytest.mark.parametrize("pilot", BY_ID)
def test_compact_hints_have_aliases_and_no_fixture_outcomes(pilot):
    prompt = prompts.build_prompt(pilot, 1, experiment="scratchpad")
    hints = prompt["guidance"]
    assert len(hints) == 3
    assert all(set(hint) == {"artifact_id", "kind", "text", "authorship"} for hint in hints)
    assert all(
        hint["artifact_id"].startswith("G") and "loop" not in hint["artifact_id"] for hint in hints
    )
    text = " ".join(hint["text"] for hint in hints)
    assert not any(char.isdigit() for char in text)
    for disclosed in ["without global conservation", "3/100000000", "7/8", "(0,-2,-1)"]:
        assert disclosed not in text
    assert "previous_model_proposal_untrusted" not in json.loads(prompt["user_prompt"])


def test_task_clarifications_and_pinned_disputed_eight_stage_source():
    pilot = "pilot_0000201"
    prompt = prompts.build_prompt(pilot, 1, experiment="scratchpad")
    user = json.loads(prompt["user_prompt"])
    source = user["source_context"]
    assert source["status"] == "DISPUTED_CLAIMS_TO_REPAIR"
    assert all(f"Stage {n}:" in source["section_5"] for n in range(1, 9))
    assert digest(source["section_5"].encode()) == prompts.SECTION_5_SHA256
    assert "FIBER_CONNECTION" in user["granted_lifts"]
    bridge = json.loads(
        prompts.build_prompt("pilot_0000202", 1, experiment="scratchpad")["user_prompt"]
    )
    assert "INTRINSIC_METRIC" in bridge["granted_lifts"]
    assert any("complex identity" in text for text in bridge["task_clarifications"])
    assert any(
        "curvature_before/after mean d1*delta" in text for text in bridge["task_clarifications"]
    )


@pytest.mark.parametrize("pilot", BY_ID)
def test_final_sees_only_own_valid_draft_and_audit(pilot):
    draft, audit = public_workpad(pilot, 2), public_workpad(pilot, 3)
    context = {
        "control_reply": "CONTROL_SECRET",
        "previous_proposal": "PREVIOUS_SECRET",
        "guidance": [{"text": "INJECTED_SECRET"}],
        "workpads": {"draft": draft, "audit": audit, "control": "CONTROL_SECRET"},
        "workpad_feedback": ["DRAFT_SCHEMA_VIOLATION"],
    }
    original = copy.deepcopy(context)
    final = prompts.build_prompt(pilot, 4, context, experiment="scratchpad")
    user = json.loads(final["user_prompt"])
    assert user["public_workpads_untrusted"] == {"draft": draft, "audit": audit}
    assert user["workpad_feedback_codes"] == ["DRAFT_SCHEMA_VIOLATION"]
    assert context == original
    for secret in ["CONTROL_SECRET", "PREVIOUS_SECRET", "INJECTED_SECRET"]:
        assert secret not in final["user_prompt"]
    assert final["response_schema"] == response_schema(pilot)
    audit_prompt = prompts.build_prompt(pilot, 3, context, experiment="scratchpad")
    assert json.loads(audit_prompt["user_prompt"])["public_workpads_untrusted"] == {"draft": draft}


@pytest.mark.parametrize(
    "mutation", ["identity", "stage", "extra_field", "malformed_pair", "wrong_pilot"]
)
def test_workpad_mutations_cannot_enter_final(mutation):
    pilot = "pilot_0000200"
    draft = public_workpad(pilot, 2)
    if mutation == "identity":
        draft["prompt_id"] = "old-control-prompt"
    elif mutation == "stage":
        draft["stage"] = "audit"
    elif mutation == "extra_field":
        draft["expected_answer"] = "not allowed"
    elif mutation == "malformed_pair":
        draft["candidate_certificate"] = {"residual": [["i", "0"]]}
    else:
        draft = public_workpad("pilot_0000199", 2)
    with pytest.raises(ValueError, match="WORKPAD_SCHEMA_OR_IDENTITY_MISMATCH"):
        prompts.build_prompt(pilot, 4, {"workpads": {"draft": draft}}, experiment="scratchpad")


def test_missing_workpads_do_not_invent_or_repair_records():
    final = prompts.build_prompt("pilot_0000199", 4, {}, experiment="scratchpad")
    user = json.loads(final["user_prompt"])
    assert user["public_workpads_untrusted"] == {}
    assert "derive afresh" in user["instructions"]
    with pytest.raises(ValueError, match="CODES_ONLY"):
        prompts.build_prompt(
            "pilot_0000199",
            4,
            {"workpad_feedback": ["expected radius is ..."]},
            experiment="scratchpad",
        )


def test_invalid_context_types_and_workpad_stages_fail_closed():
    with pytest.raises(ValueError, match="INVALID_EXPERIMENT_CONTEXT"):
        prompts.build_prompt("pilot_0000199", 1, [], experiment="scratchpad")
    with pytest.raises(ValueError, match="INVALID_PUBLIC_WORKPAD_STAGE"):
        prompts.workpad_schema("pilot_0000199", stage="control")


def test_returned_schema_cannot_mutate_the_frozen_certificate_definitions():
    pilot = "pilot_0000199"
    baseline = copy.deepcopy(response_schema(pilot))
    prompt = prompts.build_prompt(pilot, 1, experiment="scratchpad")
    fields = prompt["response_schema"]["properties"]["sections"]["items"]["properties"]["rows"][
        "items"
    ]["properties"]
    fields["certificate"]["anyOf"][0]["properties"]["l1_radius"]["const"] = "MUTATED"
    assert response_schema(pilot) == baseline


@pytest.mark.parametrize(
    "experiment,loop,temperature",
    [
        ("scratchpad", 0, 0),
        ("scratchpad", 5, 0),
        ("temperature", 3, 0),
        ("unknown", 1, 0),
        ("scratchpad", 1, True),
        ("scratchpad", True, 0),
        ("temperature", 2, 0.5),
    ],
)
def test_unsupported_experiment_configuration_refused(experiment, loop, temperature):
    with pytest.raises(ValueError):
        prompts.stage_config(experiment, loop, temperature)


def test_bounded_stage_configuration():
    stages = [prompts.stage_config("scratchpad", n) for n in range(1, 5)]
    assert [stage["max_output_tokens"] for stage in stages] == [2500, 1000, 1000, 2500]
    assert [stage["stage_name"] for stage in stages] == list(prompts.SCRATCHPAD_STAGES)
    assert set(stages[0]) == {"stage_name", "max_output_tokens", "temperature", "response_kind"}
