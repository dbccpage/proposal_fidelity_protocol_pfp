"""Concrete witnesses exercise existing mode owners; declarations cannot substitute."""
from __future__ import annotations

import importlib
import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from random import Random

import pytest

APPLICATION=Path(__file__).resolve().parents[1]
NAMESPACE=APPLICATION.name
checks=importlib.import_module(f"{NAMESPACE}.infrastructure.pilot_runners.pfp_mode_additional_checks")
evaluate=importlib.import_module(f"{NAMESPACE}.infrastructure.pilot_runners.mssn_checks").evaluate_seed_response


def digest(value):
    return sha256(checks._json(value).encode("ascii")).hexdigest()


def candidate(gauge=0):
    return dict(potential=[gauge]*3,dual=[1,1,1],after_face=dict(
        d0=[[-1,1,0],[0,-1,1],[1,0,-1]],cochain=[1,1,1],face_boundary=[1,1,1],
        potential=[gauge]*3,dual=[1,1,1]))


def simplex():
    return dict(vertices=["a","b","c"],squared_lengths=[[0,1,1],[1,0,1],[1,1,0]],
                squared_volume="3/16",holonomy=[[[0,-1],[1,0]],[[0,1],[-1,0]]])


def adversary():
    case=dict(challenge="c011",nodes=["a","b"],edges=[["a","b"]],claims={"a->b":1})
    valid=dict(status="SOLVED",phi1=0,potential={"a":0,"b":1},repair={"a->b":0},dual={"a->b":0})
    invalid=deepcopy(valid); invalid["potential"]["b"]=2
    return dict(case=case,candidate=valid,negative_control=invalid)


def cemetery():
    from adversary.stage.domain import CandidateProposalV1, CemeteryHeadstoneV1
    raw=checks._json({})
    payload_digest="sha256:"+sha256(raw.encode("ascii")).hexdigest()
    proposal=CandidateProposalV1("proposer","sha256:"+"1"*64,(payload_digest,),
                                 "sha256:"+"2"*64,("finite seed only",))
    history=evaluate("DEMO-N08",{}).to_dict()
    headstone=CemeteryHeadstoneV1(proposal.candidate_id,"run","scene","missing witness","critic",
                                ("sha256:"+digest(history),),payload_digest)
    return dict(records=[dict(headstone=headstone.to_dict(),proposal=proposal.to_dict(),payload_bytes=raw,
                              seed_id="DEMO-N08",historical_result=history)])


def perturb():
    edges=[[0,1],[0,2],[1,2]]
    random=Random(14)
    return dict(vertices=[0,1,2],edges=edges,faces=[[0,1,2]],seed=14,
                rounds=[dict(removed_edge_index=random.randrange(len(edges)),repaired_edges=deepcopy(edges))
                        for _ in range(10)])


def consensus():
    original=candidate()
    return dict(producer_id="producer",seed_id="DEMO-N08",candidate=original,
                examiners=[dict(examiner_id=f"checker{i}",sampling_seed=i,trust_domain=f"declared{i}",
                                candidate_sha256=digest(original),artifact=candidate(i),artifact_sha256=digest(candidate(i)))
                           for i in range(3)])


def mub():
    owner=importlib.import_module("atlas.coda_atlas.F004_papers.010_mub6.code.mub_verify.mub_triples")
    columns=owner.dita_seed_triple_columns(0,8)
    return dict(field="Q(zeta24)",bases=[[[[str(v) for v in entry.coeffs] for entry in column]
                                         for column in columns[offset:offset+6]] for offset in (0,6,12)])


def debate():
    return dict(seed_id="DEMO-N08",proposer_id="proposer",adversary_id="critic",proposal=candidate(),
                challenges=[dict(witness=candidate(1),expected_accept=True),dict(witness={},expected_accept=False)])


@pytest.mark.parametrize("mode,factory",[(10,cemetery),(11,adversary),(12,simplex),(16,perturb),(17,consensus),(18,mub),(20,debate)])
def test_concrete_additional_mode_witnesses(mode,factory):
    data=factory(); original=deepcopy(data)
    artifact=checks.execute_additional_mode_check(mode,data)
    assert artifact["mode_id"]==mode and artifact["authority_effect"]=="None"
    assert artifact["scope"] and artifact["input_sha256"]==digest(data)
    assert data==original


def test_lean_mode_delegates_exact_source_to_existing_kernel_adapter(monkeypatch):
    owner=importlib.import_module(f"{NAMESPACE}.infrastructure.pilot_runners.seed_advanced_checks")
    observed=[]
    def existing(number,data):
        observed.append((number,data)); return {"test_double":"existing adapter delegation"}
    monkeypatch.setattr(owner,"advanced_check",existing)
    data={"source":"bound source"}
    assert checks.execute_additional_mode_check(9,data)["evidence"]["test_double"]
    assert observed==[(20,data)]
    def unavailable(number,data):
        raise ValueError("LEAN_EXECUTABLE_UNAVAILABLE")
    monkeypatch.setattr(owner,"advanced_check",unavailable)
    with pytest.raises(ValueError,match="LEAN_EXECUTABLE_UNAVAILABLE"):
        checks.execute_additional_mode_check(9,data)


@pytest.mark.parametrize("mutation,error",[("payload","BINDING_MISMATCH"),("history","HISTORY_BINDING_MISMATCH"),("forged_reason","FAILURE_NOT_REPRODUCED")])
def test_cemetery_requires_content_binding_and_current_reproduced_failure(mutation,error):
    data=cemetery(); row=data["records"][0]
    if mutation=="payload": row["payload_bytes"]="{\"passed\":true}"
    elif mutation=="history": row["historical_result"]["failure_reasons"]=["forged"]
    else:
        row["historical_result"]["failure_reasons"]=["forged"]
        row["headstone"]["evidence_refs"]=["sha256:"+digest(row["historical_result"])]
    with pytest.raises(ValueError,match=error): checks.execute_additional_mode_check(10,data)


def test_adversary_negative_control_must_actually_fail():
    data=adversary(); data["negative_control"]=data["candidate"]
    with pytest.raises(ValueError,match="NEGATIVE_CONTROL_FAILED"):
        checks.execute_additional_mode_check(11,data)


@pytest.mark.parametrize("mutation,error",[("volume","VOLUME_MISMATCH"),("gram","GRAM_NOT_POSITIVE"),("holonomy","HOLONOMY_OPEN"),("float","NON_EXACT_RATIONAL")])
def test_simplex_recomputes_geometry_and_connection(mutation,error):
    data=simplex()
    if mutation=="volume": data["squared_volume"]="1/16"
    elif mutation=="gram": data["squared_lengths"][1][2]=data["squared_lengths"][2][1]=5
    elif mutation=="holonomy": data["holonomy"].pop()
    else: data["squared_lengths"][0][1]=1.0
    with pytest.raises(ValueError,match=error): checks.execute_additional_mode_check(12,data)


@pytest.mark.parametrize("mutation",["count","noise","repair"])
def test_perturbation_requires_ten_actual_seeded_repairs(mutation):
    data=perturb()
    if mutation=="count": data["rounds"].pop()
    elif mutation=="noise": data["rounds"][0]["removed_edge_index"]=(data["rounds"][0]["removed_edge_index"]+1)%3
    else: data["rounds"][0]["repaired_edges"].pop()
    with pytest.raises(ValueError): checks.execute_additional_mode_check(16,data)


@pytest.mark.parametrize("mutation",["self","seed","domain","copy","binding","witness"])
def test_consensus_does_not_promote_votes_or_self_reported_pass(mutation):
    data=consensus(); row=data["examiners"][1]
    if mutation=="self": row["examiner_id"]=data["producer_id"]
    elif mutation=="seed": row["sampling_seed"]=0
    elif mutation=="domain": row["trust_domain"]=data["examiners"][0]["trust_domain"]
    elif mutation=="copy": row["artifact"]=candidate(); row["artifact_sha256"]=digest(row["artifact"])
    elif mutation=="binding": row["candidate_sha256"]="0"*64
    else: row["artifact"]={"passed":True}; row["artifact_sha256"]=digest(row["artifact"])
    with pytest.raises(ValueError): checks.execute_additional_mode_check(17,data)


@pytest.mark.parametrize("mutation,error",[("entry","UNBIASEDNESS_FAILED"),("shape","COLUMN_SHAPE"),("float","NON_EXACT_RATIONAL")])
def test_mub_requires_actual_exact_orthogonality_and_unbiasedness(mutation,error):
    data=mub()
    if mutation=="entry": data["bases"][0][0][0][0]="2"
    elif mutation=="shape": data["bases"][0][0].pop()
    else: data["bases"][0][0][0][0]=1.0
    with pytest.raises(ValueError,match=error): checks.execute_additional_mode_check(18,data)


@pytest.mark.parametrize("mutation,error",[("rhetoric","PROPOSAL_NOT_CHECKED"),("claim","CHALLENGE_FALSIFIED"),("no_negative","NEGATIVE_CONTROL_REQUIRED"),("roles","ROLE_SEPARATION_REQUIRED")])
def test_debate_is_decided_by_host_witnesses(mutation,error):
    data=debate()
    if mutation=="rhetoric": data["proposal"]={"passed":True}
    elif mutation=="claim": data["challenges"][1]["expected_accept"]=True
    elif mutation=="no_negative": data["challenges"].pop()
    else: data["adversary_id"]=data["proposer_id"]
    with pytest.raises(ValueError,match=error): checks.execute_additional_mode_check(20,data)


def test_additional_mode_artifacts_enter_worker_prompt_and_invalid_input_calls_no_provider():
    providers=importlib.import_module(f"{NAMESPACE}.infrastructure.providers")
    storage=importlib.import_module(f"{NAMESPACE}.infrastructure.storage").PfpFileSystemStorageAdapter()
    pipeline=importlib.import_module(f"{NAMESPACE}.use_cases.execute_stage_pipeline").ExecuteStagePipelineUseCase
    class Observing(providers.OfflineDeterministicPfpProvider):
        def __init__(self): self.packets=[]
        def generate_candidate(self,packet,temperature=0.0):
            self.packets.append(packet); return super().generate_candidate(packet,temperature)
    provider=Observing(); use_case=pipeline(storage,provider,catalog=storage,host_verifier=providers.SeedHostVerifier())
    result=use_case.run_pipeline("demo_000",{"raw_seed":"<>"},stage_count=1,modes=(12,),mode_inputs={12:simplex()})
    assert result.is_ok, result.error
    artifact=json.loads(provider.packets[0].user)["mode_artifacts"]["12"]
    assert artifact["squared_volume"]=="3/16" and artifact["boundary_maps"]
    provider.packets.clear(); bad=simplex(); bad["squared_volume"]="0"
    result=use_case.run_pipeline("demo_000",{"raw_seed":"<>"},stage_count=1,modes=(12,),mode_inputs={12:bad})
    assert result.is_err and "VOLUME_MISMATCH" in result.error.message and not provider.packets
    missing=pipeline(storage,provider,catalog=storage)
    result=missing.run_pipeline("demo_000",{"raw_seed":"<>"},stage_count=1,modes=(12,),mode_inputs={12:simplex()})
    assert result.is_err and "MODE_HOST_VERIFIER_REQUIRED" in result.error.message and not provider.packets
