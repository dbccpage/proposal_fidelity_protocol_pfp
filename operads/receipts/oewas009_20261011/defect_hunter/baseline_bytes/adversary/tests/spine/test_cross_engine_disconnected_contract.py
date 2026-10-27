"""The real OEWAS/Adversary wire boundary refuses identity loss before dispatch."""
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

import pytest

from operations.domain.rop.result import Err, Ok
from adversary.infrastructure.estates import oewas_anti_skill as adapter_module
from adversary.infrastructure.estates.oewas_anti_skill import OewasAntiSkillAdapter
from adversary.runtime import build_adversary_swarm
from adversary.use_cases.base_swarm.specializations import RESEARCH_PROFILE_V01
from adversary.use_cases.base_swarm.adversary_swarm import AdversarySwarm
from workflows_agents_skills.domain.anti_skills.anti_skill_v2 import AntiSkillSubjectV1


@pytest.fixture
def wire():
    return AntiSkillSubjectV1(
        claim_scope=("candidate_result",), evidence_scope=("finite_fixture",),
        producer_identity="research.candidate", verifier_identity="native.checker",
        claim_mode="PROPOSAL", requested_effect="NONE",
        nonclaims=("No authority or mathematical theorem is conferred.",),
    ).to_dict()


@pytest.mark.parametrize("stage", ["PRE_DISPATCH", "PRE_SEAL"])
def test_valid_wire_keeps_subject_identity_and_holds_without_runtime(wire, stage):
    result = OewasAntiSkillAdapter().evaluate(stage, wire)
    assert isinstance(result, Ok)
    assert result.value.subject_id == wire["subject_id"]
    assert result.value.stage == stage
    assert result.value.disposition == "HOLD"
    assert result.value.registry_id == ""
    assert result.value.activation_profile_digest == ""


@pytest.mark.parametrize("stage", ["PRE_DISPATCH", "PRE_SEAL"])
@pytest.mark.parametrize("field,value", [
    ("claim_scope", "abc"),
    ("evidence_scope", "xyz"),
    ("nonclaims", "xyz"),
    ("claim_scope", ("candidate_result",)),
    ("authority_effect", "ADMIT"),
    ("schema_version", "foreign.v9"),
    ("subject_id", "sha256:" + "1" * 64),
    ("unexpected_field", "ignored before repair"),
])
def test_adapter_refuses_coerced_or_rebound_wire(wire, stage, field, value):
    wire[field] = value
    result = OewasAntiSkillAdapter().evaluate(stage, wire)
    assert isinstance(result, Err)
    assert result.error.code == "ANTI_SKILL_SUBJECT_INVALID"


@pytest.mark.parametrize("field", ["claim_scope", "evidence_scope", "producer_identity", "verifier_identity", "claim_mode", "requested_effect", "approval_reference", "nonclaims", "authority_effect", "schema_version", "subject_id"])
def test_missing_wire_field_is_typed_refusal(wire, field):
    del wire[field]
    result = OewasAntiSkillAdapter().evaluate("PRE_DISPATCH", wire)
    assert isinstance(result, Err)
    assert result.error.code == "ANTI_SKILL_SUBJECT_INVALID"


def test_unverified_probe_is_disconnected_without_constructing_subject(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("disconnected probe must not construct a native-bound subject")
    monkeypatch.setattr("adversary.infrastructure.estates.oewas_anti_skill.AntiSkillSubjectV1", forbidden)
    receipt = OewasAntiSkillAdapter().probe(str(tmp_path))
    assert not receipt.connected
    assert receipt.effect_digest is None
    assert receipt.detail.startswith("NO_VERIFIED_RUNTIME")


def test_production_swarm_holds_before_native_dispatch(tmp_path: Path):
    class BoutObserver:
        calls = 0

        def execute_bout(self, request):
            self.calls += 1
            raise AssertionError("unverified runtime reached native/provider dispatch")

    built = build_adversary_swarm(
        AdversarySwarm, specialization=RESEARCH_PROFILE_V01, repo_root=tmp_path,
    )
    observer = BoutObserver()
    swarm = build_adversary_swarm(
        AdversarySwarm, specialization=RESEARCH_PROFILE_V01,
        spine=replace(built.spine, bout=observer),
    )
    assert type(swarm.spine.anti_skill) is OewasAntiSkillAdapter
    assert swarm.spine.anti_skill.runtime is None
    result = swarm.run_bout("Bounded cross-engine refusal control.", "oewas009-held", fixture_mode=False)
    assert isinstance(result, Err)
    assert result.error.code == "ANTI_SKILL_PRE_DISPATCH_UNCLEARED"
    assert observer.calls == 0

@pytest.mark.parametrize("payload", [None, False, [], "wire", 7])
def test_non_object_wire_refuses_before_gate_evaluation(monkeypatch, payload):
    def forbidden(**kwargs):
        raise AssertionError("malformed wire reached the detector")

    monkeypatch.setattr(adapter_module, "evaluate_adversary_anti_skill_gate", forbidden)
    result = OewasAntiSkillAdapter().evaluate("PRE_DISPATCH", payload)
    assert isinstance(result, Err)
    assert result.error.code == "ANTI_SKILL_SUBJECT_INVALID"


@pytest.mark.parametrize("wrapper", [MappingProxyType, type("WireSubclass", (dict,), {})])
def test_non_exact_mapping_refuses_without_copying(wire, wrapper):
    result = OewasAntiSkillAdapter().evaluate("PRE_DISPATCH", wrapper(wire))
    assert isinstance(result, Err)
    assert result.error.code == "ANTI_SKILL_SUBJECT_INVALID"


@pytest.mark.parametrize("field,value", [
    ("producer_identity", False),
    ("verifier_identity", None),
    ("claim_mode", ["PROPOSAL"]),
    ("requested_effect", 0),
    ("approval_reference", False),
    ("subject_id", ""),
    ("claim_scope", []),
    ("claim_scope", ["candidate_result", "candidate_result"]),
    ("claim_scope", [4]),
    ("evidence_scope", [False]),
    ("nonclaims", [""]),
    ("nonclaims", ["x" * 4097]),
    ("evidence_scope", [f"fixture_{index}" for index in range(65)]),
])
def test_closed_scalar_and_collection_limits_refuse_before_detector(
    monkeypatch, wire, field, value,
):
    def forbidden(**kwargs):
        raise AssertionError("malformed wire reached the detector")

    monkeypatch.setattr(adapter_module, "evaluate_adversary_anti_skill_gate", forbidden)
    wire[field] = value
    result = OewasAntiSkillAdapter().evaluate("PRE_DISPATCH", wire)
    assert isinstance(result, Err)
    assert result.error.code == "ANTI_SKILL_SUBJECT_INVALID"


@pytest.mark.parametrize("stage", ["POST_SEAL", "pre_dispatch"])
def test_unknown_stage_is_typed_refusal(wire, stage):
    result = OewasAntiSkillAdapter().evaluate(stage, wire)
    assert isinstance(result, Err)
    assert result.error.code == "ANTI_SKILL_SUBJECT_INVALID"


@pytest.mark.parametrize("stage", ["PRE_DISPATCH", "PRE_SEAL"])
def test_real_subject_transplant_refuses_and_original_recovers(wire, stage):
    adapter = OewasAntiSkillAdapter()
    before = adapter.evaluate(stage, wire)
    assert isinstance(before, Ok)
    assert before.value.disposition == "HOLD"
    other = AntiSkillSubjectV1.from_dict(wire)
    changed = replace(other, evidence_scope=("different_fixture",), subject_id="").to_dict()
    assert changed["subject_id"] != wire["subject_id"]
    changed["subject_id"] = wire["subject_id"]
    transplanted = adapter.evaluate(stage, changed)
    assert isinstance(transplanted, Err)
    assert transplanted.error.code == "ANTI_SKILL_SUBJECT_INVALID"
    restored = adapter.evaluate(stage, wire)
    assert isinstance(restored, Ok)
    assert restored.value == before.value
    assert restored.value.subject_id == wire["subject_id"]
    assert restored.value.disposition == "HOLD"
    assert restored.value.registry_id == ""
    assert restored.value.activation_profile_digest == ""
