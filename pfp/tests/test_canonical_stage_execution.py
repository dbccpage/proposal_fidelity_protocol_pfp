"""Canonical prompts carry actual predecessors. AuthorityEffect: None."""

import json
from copy import deepcopy

import pytest

from omega_engine_pfp.domain.kernel.result import RefusalCode
from omega_engine_pfp.domain.stages.stages import Stage5Response
from omega_engine_pfp.infrastructure.providers import OfflineDeterministicPfpProvider
from omega_engine_pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from omega_engine_pfp.use_cases.execute_stage_pipeline import ExecuteStagePipelineUseCase


class ObservingProvider(OfflineDeterministicPfpProvider):
    def __init__(self):
        self.packets = []

    def generate_candidate(self, packet, temperature=0.0):
        self.packets.append(packet)
        return super().generate_candidate(packet, temperature)


class Host:
    def verify(self, demo_id, prior_responses):
        assert list(prior_responses) == [1, 2, 3, 4]
        return Stage5Response(demo_id=demo_id, should_continue=True, host_verdict="PASS",
                              exact_checks_passed=True, surviving_candidates=[prior_responses[4]["candidate_id"]])


def pipeline(provider):
    storage = PfpFileSystemStorageAdapter()
    return ExecuteStagePipelineUseCase(storage, provider, catalog=storage, host_verifier=Host())


def test_canonical_schema_is_bound_and_real_predecessors_enter_the_next_prompt():
    provider = ObservingProvider()
    result = pipeline(provider).run_pipeline("demo_000", {"raw_seed": "Preserve <> exactly\n"})
    assert result.is_ok, result.error
    assert result.unwrap().all_stages_passed
    # Stage 1 is a model repair turn because the seed has no declaration; stage 11 runs because
    # the receipt keeps that repair as an obligation.
    assert [p.stage for p in provider.packets] == [1, 2, 3, 4, 6, 11]
    first, second = provider.packets[:2]
    assert first.response_schema["properties"]["demo_id"]["const"] == "demo_000"
    assert "admission_proposal" in first.response_schema["properties"]
    assert "Preserve <> exactly\\n" in second.user
    assert "prior_artifacts" in second.user
    assert "admission_proposal" in second.user
    selected = result.unwrap().stage_responses[4]["candidate_id"]
    packet = next(p for p in provider.packets if p.stage == 6)
    reference = packet.response_schema["properties"]["challenges"]["items"]["properties"]["candidate_id"]
    assert reference["const"] == selected
    assert "negative controls" in reference["description"]


def test_wrong_demo_or_unknown_candidate_reference_is_rejected():
    class Wrong(ObservingProvider):
        def generate_candidate(self, packet, temperature=0.0):
            candidate = json.loads(super().generate_candidate(packet, temperature))
            if packet.stage == 3:
                candidate["audits"][0]["candidate_id"] = "not-a-stage-two-candidate"
            return json.dumps(candidate)

    result = pipeline(Wrong()).run_pipeline("demo_000", {"raw_seed": "<>"})
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION
    assert result.unwrap_err().stage == 3


def test_mode_02_seals_source_and_tampering_does_not_reuse_the_same_envelope():
    provider = ObservingProvider()
    result = pipeline(provider).run_pipeline("demo_000", {"raw_seed": "<>"}, modes=(2,))
    assert result.is_ok, result.error
    user = json.loads(provider.packets[1].user)
    envelope = user["mode_artifacts"]["2"]
    from omega_engine_pfp.domain.prompts.packets import PacketEnvelope
    PacketEnvelope.model_validate(envelope)
    mutated = deepcopy(envelope)
    mutated["task_data"]["raw_seed"] = "<a>"
    try:
        PacketEnvelope.model_validate(mutated)
    except ValueError:
        pass
    else:
        raise AssertionError("source mutation reused a sealed envelope")


def test_mode_03_without_logit_hooks_stops_before_model_dispatch():
    provider = ObservingProvider()
    result = pipeline(provider).run_pipeline("demo_000", {"raw_seed": "<>"}, modes=(3,))
    assert result.is_err
    assert "MODE_EXECUTOR_UNAVAILABLE" in result.unwrap_err().message
    assert not provider.packets


@pytest.mark.parametrize("count", range(1, 12))
def test_requested_stage_prefix_executes_exactly_that_prefix(count):
    provider = ObservingProvider()
    result = pipeline(provider).run_pipeline("demo_000", {"raw_seed": "<>"}, stage_count=count)
    assert result.is_ok, result.error
    receipt = result.unwrap()
    assert receipt.completed_stages == tuple(range(1, count + 1))
    # Host stages make no model call; stage 1 does, as a repair turn for a seed with no declaration.
    assert [p.stage for p in provider.packets] == [n for n in range(1, count + 1) if n not in (5, 7, 8, 9, 10)]
    # Every acceptance stage, the receipt included, must have run.
    assert receipt.all_stages_passed is (count >= 9)


def test_mode14_executes_a_typed_negative_control_before_dispatch():
    from omega_engine_pfp.infrastructure.providers import SeedHostVerifier
    class Catalog:
        def get_demo(self, demo_id): return object() if demo_id=="DEMO-N02" else None
    provider=ObservingProvider()
    uc=ExecuteStagePipelineUseCase(PfpFileSystemStorageAdapter(),provider,catalog=Catalog(),host_verifier=SeedHostVerifier())
    good={14:{"payload":{},"expected_reason":"MISSING_OR_EXTRA_FIELDS: candidate"}}
    result=uc.run_pipeline("DEMO-N02",{"raw_seed":"<ab>"},stage_count=1,modes=(14,),mode_inputs=good)
    assert result.is_ok,result.error
    assert good[14]["payload"]=={}
    mode=json.loads(provider.packets[0].user)["mode_artifacts"]["14"]
    assert mode["typed_refusal"]==good[14]["expected_reason"]
    assert mode["before_digest"]==mode["after_digest"]
    provider.packets.clear()
    good[14]["expected_reason"]="MAP_UNDEFINED"
    result=uc.run_pipeline("DEMO-N02",{"raw_seed":"<ab>"},stage_count=1,modes=(14,),mode_inputs=good)
    assert result.is_err
    assert not provider.packets


def test_public_seed_verifier_consumes_the_extracted_candidate_and_checks_mutations():
    from omega_engine_pfp.infrastructure.providers import SeedHostVerifier
    verifier=SeedHostVerifier()
    witness={"pair_decoded":["a","b"],"edge_decoded":{"source":"a","target":"b"},
             "reports":[0,0],"tagged_reports":[[0,0],[0,1]],"endpoint_support":["a","b"],"occurrence_counts":[1,2,3]}
    prior={4:{"candidate":witness,"candidate_id":"from-stage2"}}
    assert verifier.verify("DEMO-N02",prior).exact_checks_passed
    witness["tagged_reports"]=[[0,0],[0,0]]
    assert not verifier.verify("DEMO-N02",prior).exact_checks_passed
