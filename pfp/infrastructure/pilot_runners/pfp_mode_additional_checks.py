"""Connect bounded mode inputs to their mathematical owners below Woland."""
from __future__ import annotations

import importlib
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from math import factorial
from random import Random

from ...use_cases.pfp_mode_checks import _fields, _json, _require, _wire

ADDITIONAL_MODES=frozenset({9,10,11,12,16,17,18,20})


def _seed_check(seed_id, payload):
    from omega_engine_pfp.infrastructure.pilot_runners.mssn_checks import evaluate_seed_response
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import SEED_IDS
    _require(type(seed_id) is str and seed_id in SEED_IDS,"MODE_SEED_CHECKER_UNKNOWN")
    result=evaluate_seed_response(seed_id,payload)
    _require(not any("UNAVAILABLE" in reason for reason in result.failure_reasons),"MODE_CHECKER_UNAVAILABLE")
    return result


def _lean(data):
    from omega_engine_pfp.infrastructure.pilot_runners.seed_advanced_checks import advanced_check
    result=advanced_check(20,data)
    return dict(scope="Actual kernel elaboration of the declared Bit double-flip target only",evidence=result)


def _cemetery(data):
    from omega_engine_woland.stage.domain import (
        CandidateProposalV1,
        CemeteryHeadstoneV1,
        strict_json_loads,
    )
    _fields(data,{"records"})
    _require(type(data["records"]) is list and 1<=len(data["records"])<=32,"CEMETERY_RECORDS_REQUIRED")
    artifacts=[]
    for record in data["records"]:
        _fields(record,{"headstone","proposal","payload_bytes","seed_id","historical_result"})
        _require(type(record["payload_bytes"]) is str,"CEMETERY_PAYLOAD_BYTES_REQUIRED")
        raw=record["payload_bytes"].encode("utf-8")
        _require(0<len(raw)<=65536,"CEMETERY_PAYLOAD_BOUND")
        headstone=CemeteryHeadstoneV1.from_dict(record["headstone"])
        fields=dict(record["proposal"])
        _require("proposed_dda_step" not in fields,"CEMETERY_DDA_PROFILE_UNAVAILABLE")
        for name in ("artifact_refs","nonclaims"):
            _require(type(fields.get(name)) is list,"CEMETERY_PROPOSAL_FIELDS")
            fields[name]=tuple(fields[name])
        proposal=CandidateProposalV1(**fields)
        digest="sha256:"+sha256(raw).hexdigest()
        _require(headstone.candidate_id==proposal.candidate_id and headstone.candidate_payload_sha256==digest
                 and digest in proposal.artifact_refs,"CEMETERY_CANDIDATE_BINDING_MISMATCH")
        history=record["historical_result"]
        _require(type(history) is dict and history.get("seed_id")==record["seed_id"] and history.get("passed") is False,"CEMETERY_NEGATIVE_HISTORY_REQUIRED")
        historical_digest="sha256:"+sha256(_json(history).encode("ascii")).hexdigest()
        _require(historical_digest in headstone.evidence_refs,"CEMETERY_HISTORY_BINDING_MISMATCH")
        payload=strict_json_loads(raw)
        current=_seed_check(record["seed_id"],payload)
        _require(not current.passed and current.failure_reasons==history.get("failure_reasons"),"CEMETERY_FAILURE_NOT_REPRODUCED")
        # The bound headstone identifies the rejected bytes; the seed owner above
        # reproduces the rejection. No swarm runtime is needed for this replay.
        artifacts.append(dict(candidate_digest=digest,headstone_id=headstone.headstone_id,historical_digest=historical_digest,
                              current_failure_reasons=current.failure_reasons))
    return dict(scope="Exact supplied cemetery content and current rejection replay; no authentication of historical origin",records=artifacts)


def _woland(data):
    from omega_engine_pfp.domain.cohomology.certificate_checker import check_certificate
    _fields(data,{"case","candidate","negative_control"})
    results=[]
    for name in ("candidate","negative_control"):
        raw=_json(data[name]).encode("ascii")
        checked=check_certificate(data["case"],data[name])
        accepted=checked.passed and checked.status=="SOLVED"
        _require(accepted==(name=="candidate"),"WOLAND_POSITIVE_OR_NEGATIVE_CONTROL_FAILED")
        results.append(dict(candidate_id=name,candidate_content_sha256="sha256:"+sha256(raw).hexdigest(),
                            case_sha256="sha256:"+sha256(_json(data["case"]).encode("ascii")).hexdigest(),
                            verdict="ACCEPTED" if accepted else "REJECTED",reason=checked.error,
                            authority_effect="None"))
    return dict(scope="The exact C011 checker shared with Woland and an adversarial control; no thirteen-persona bout claim",checks=results)


def _simplex(data):
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import boundary, rational
    from omega_engine_pfp.domain.mssn_research.packets.invariants import _exact_det
    _fields(data,{"vertices","squared_lengths","squared_volume","holonomy"})
    vertices=data["vertices"]
    _require(type(vertices) is list and 3<=len(vertices)<=5 and all(type(v) is str and v for v in vertices)
             and len(set(vertices))==len(vertices),"SIMPLEX_VERTICES_REQUIRED")
    n=len(vertices); lengths=data["squared_lengths"]
    _require(type(lengths) is list and len(lengths)==n and all(type(row) is list and len(row)==n for row in lengths),"SIMPLEX_METRIC_SHAPE")
    lengths=[[rational(v) for v in row] for row in lengths]
    _require(all(lengths[i][j]==lengths[j][i] and (lengths[i][j]==0 if i==j else lengths[i][j]>0)
                 for i in range(n) for j in range(n)),"SIMPLEX_METRIC_INVALID")
    gram=[[(lengths[0][i+1]+lengths[0][j+1]-lengths[i+1][j+1])/2 for j in range(n-1)] for i in range(n-1)]
    _require(all(_exact_det([row[:k] for row in gram[:k]])>0 for k in range(1,n)),"SIMPLEX_GRAM_NOT_POSITIVE")
    cm=[[Fraction(0)]+[Fraction(1)]*n]+[[Fraction(1)]+row for row in lengths]
    volume=Fraction((-1)**n)*_exact_det(cm)/(2**(n-1)*factorial(n-1)**2)
    _require(volume>0 and rational(data["squared_volume"])==volume,"SIMPLEX_VOLUME_MISMATCH")
    bases=[list(combinations(vertices,k+1)) for k in range(n)]
    maps=[boundary(bases[k],bases[k-1]) for k in range(1,n)]
    import sympy as sp
    _require(all(sp.Matrix(maps[i-1])*sp.Matrix(maps[i])==sp.zeros(len(bases[i-1]),len(bases[i+1])) for i in range(1,len(maps))),"SIMPLEX_BOUNDARY_SQUARE")
    rotations=data["holonomy"]
    _require(type(rotations) is list and 1<=len(rotations)<=16,"DECLARED_CONNECTION_REQUIRED")
    product=sp.eye(n-1)
    for matrix in rotations:
        _require(type(matrix) is list and len(matrix)==n-1 and all(type(row) is list and len(row)==n-1 for row in matrix),"HOLONOMY_SHAPE")
        matrix=sp.Matrix([[rational(x) for x in row] for row in matrix])
        _require(matrix.T*matrix==sp.eye(n-1) and matrix.det()==1,"HOLONOMY_NOT_SPECIAL_ORTHOGONAL")
        product=product*matrix
    _require(product==sp.eye(n-1),"DECLARED_HOLONOMY_OPEN")
    return dict(scope="Exact Euclidean simplex and separately supplied rational connection closure; angles and physical Bianchi claims unverified",
                cayley_menger_determinant=str(_exact_det(cm)),squared_volume=str(volume),boundary_maps=maps,
                holonomy_product=[[str(v) for v in row] for row in product.tolist()])


def _perturb(data):
    from ...domain.normal_forms.topology import verify_tsnf
    _fields(data,{"vertices","edges","faces","seed","rounds"})
    vertices,edges,faces=data["vertices"],data["edges"],data["faces"]
    _require(type(vertices) is list and 2<=len(vertices)<=8 and vertices==list(range(len(vertices))) and all(type(v) is int for v in vertices),"BOUNDARY_CARRIER_REQUIRED")
    for cells,width in ((edges,2),(faces,3)):
        _require(type(cells) is list and all(type(row) is list and len(row)==width and all(type(v) is int and v in vertices for v in row) for row in cells),"BOUNDARY_CELLS_REQUIRED")
    _require(edges and len(edges)<=28 and verify_tsnf(vertices,[tuple(e) for e in edges],[tuple(f) for f in faces]).is_tsnf,"BOUNDARY_COMPLEX_INVALID")
    _require(type(data["seed"]) is int and type(data["rounds"]) is list and len(data["rounds"])==10,"TEN_SEEDED_REPAIR_ROUNDS_REQUIRED")
    random=Random(data["seed"]); actual=[]
    for round_id in range(10):
        chosen=random.randrange(len(edges))
        damaged=[edge for i,edge in enumerate(edges) if i!=chosen]
        supplied=data["rounds"][round_id]
        _fields(supplied,{"removed_edge_index","repaired_edges"})
        _require(type(supplied["removed_edge_index"]) is int and supplied["removed_edge_index"]==chosen,"PERTURBATION_REPLAY_MISMATCH")
        repaired=supplied["repaired_edges"]
        _require(_json(repaired)==_json(edges),"BOUNDARY_REPAIR_NOT_ORIGINAL_CARRIER")
        verified=verify_tsnf(vertices,[tuple(e) for e in repaired],[tuple(f) for f in faces])
        _require(verified.is_tsnf and damaged!=repaired,"BOUNDARY_DISSOLUTION_OR_PASSIVE_DRIFT")
        actual.append(dict(round=round_id,removed_edge_index=chosen,damaged_edges=damaged,repaired_edges=repaired,betti=verified.betti_numbers))
    return dict(scope="Ten seeded finite edge perturbations with checked restoration of the declared simplicial boundary; no general 4E cognition claim",rounds=actual)


def _consensus(data):
    _fields(data,{"producer_id","seed_id","candidate","examiners"})
    _require(type(data["producer_id"]) is str and data["producer_id"],"CONSENSUS_PRODUCER_REQUIRED")
    rows=data["examiners"]
    _require(type(rows) is list and 3<=len(rows)<=8,"THREE_EXAMINER_ARTIFACTS_REQUIRED")
    names=[]; seeds=[]; domains=[]; digests=[]
    candidate_digest=sha256(_json(data["candidate"]).encode("ascii")).hexdigest()
    checks=[]
    for row in rows:
        _fields(row,{"examiner_id","sampling_seed","trust_domain","candidate_sha256","artifact","artifact_sha256"})
        _require(type(row["examiner_id"]) is str and row["examiner_id"] and type(row["sampling_seed"]) is int
                 and type(row["trust_domain"]) is str and row["trust_domain"],"EXAMINER_PROVENANCE_REQUIRED")
        _require(row["candidate_sha256"]==candidate_digest,"EXAMINER_CANDIDATE_BINDING_MISMATCH")
        digest=sha256(_json(row["artifact"]).encode("ascii")).hexdigest()
        _require(digest==row["artifact_sha256"],"EXAMINER_ARTIFACT_DIGEST_MISMATCH")
        result=_seed_check(data["seed_id"],row["artifact"])
        _require(result.passed,"EXAMINER_WITNESS_REFUSED")
        names.append(row["examiner_id"]); seeds.append(row["sampling_seed"]); domains.append(row["trust_domain"]); digests.append(digest)
        checks.append(result.to_dict())
    _require(data["producer_id"] not in names and
             all(len(set(values))==len(values) for values in (names,seeds,domains,digests)),
             "COLLUSIVE_OR_DUPLICATED_ARTIFACTS")
    original=_seed_check(data["seed_id"],data["candidate"])
    _require(original.passed,"CONSENSUS_ORIGINAL_CANDIDATE_REFUSED")
    return dict(scope="Host replay of distinct supplied certificates and declared provenance diversity; no authenticated independence or voting authority",candidate_sha256=candidate_digest,checks=checks)


def _mub(data):
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import rational
    _fields(data,{"field","bases"})
    _require(data["field"]=="Q(zeta24)","MUB_FIELD_UNAVAILABLE")
    owner=importlib.import_module("omega_engine_atlas.coda_atlas.F004_papers.010_mub6.code.mub_verify.mub_triples")
    bases=data["bases"]
    _require(type(bases) is list and len(bases)==3,"MUB_CANDIDATE_TRIAD_REQUIRED")
    columns=[]
    for basis in bases:
        _require(type(basis) is list and len(basis)==6,"MUB_BASIS_SHAPE")
        for column in basis:
            _require(type(column) is list and len(column)==6,"MUB_COLUMN_SHAPE")
            entries=[]
            for scalar in column:
                _require(type(scalar) is list and len(scalar)==8,"MUB_CYCLOTOMIC_COEFFICIENTS_REQUIRED")
                entries.append(owner.Cyc24([rational(x) for x in scalar]))
            columns.append(tuple(entries))
    _require(owner.verify_triple_pairwise_mu(columns),"MUB_ORTHOGONALITY_OR_UNBIASEDNESS_FAILED")
    return dict(scope="Exact supplied dimension-six basis triad over Q(zeta24); no maximality or MUB6 nonexistence claim",basis_count=3,dimension=6,
                owner="canonical atlas mub_verify.mub_triples",orthogonality_pairs_checked=108,unbiased_pairs_checked=108)


def _debate(data):
    _fields(data,{"seed_id","proposer_id","adversary_id","proposal","challenges"})
    _require(type(data["proposer_id"]) is str and type(data["adversary_id"]) is str and data["proposer_id"] and data["adversary_id"] and data["proposer_id"]!=data["adversary_id"],"DEBATE_ROLE_SEPARATION_REQUIRED")
    proposed=_seed_check(data["seed_id"],data["proposal"])
    _require(proposed.passed,"DEBATE_PROPOSAL_NOT_CHECKED")
    challenges=data["challenges"]
    _require(type(challenges) is list and 1<=len(challenges)<=16,"BOUNDED_DEBATE_CHALLENGES_REQUIRED")
    checked=[]; refusals=0
    for challenge in challenges:
        _fields(challenge,{"witness","expected_accept"})
        _require(type(challenge["expected_accept"]) is bool,"DEBATE_EXPECTATION_TYPE")
        result=_seed_check(data["seed_id"],challenge["witness"])
        _require(result.passed==challenge["expected_accept"],"DEBATE_CHALLENGE_FALSIFIED")
        refusals+=not result.passed
        checked.append(result.to_dict())
    _require(refusals>0,"DEBATE_NEGATIVE_CONTROL_REQUIRED")
    return dict(scope="Bounded supplied debate witnesses judged by the existing deterministic seed checker; no live agents or model oversight improvement claim",
                proposal=proposed.to_dict(),challenges=checked,terminal="FINITE_WITNESSES_CHECKED")


def execute_additional_mode_check(mode_id,data):
    _require(mode_id in ADDITIONAL_MODES,"MODE_EXECUTOR_UNAVAILABLE")
    _require(type(data) is dict,"MODE_INPUT_REQUIRED")
    result={9:_lean,10:_cemetery,11:_woland,12:_simplex,16:_perturb,17:_consensus,18:_mub,20:_debate}[mode_id](data)
    return dict(_wire(result),mode_id=mode_id,input_sha256=sha256(_json(data).encode("ascii")).hexdigest(),authority_effect="None")
