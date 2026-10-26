"""Concrete positive witnesses plus changes that must invalidate each check."""
from copy import deepcopy
from fractions import Fraction

import pytest
import sympy as sp

from omega_engine_pfp.infrastructure.pilot_runners.mssn_checks import evaluate_seed_response
from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import _native
from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import wire
from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import seed_candidate_schema
from omega_engine_pfp.infrastructure.pilot_runners.seed_core_checks import core_expected


@pytest.mark.parametrize("number,field",[(3,"raw_source"),(11,"transported_basis_maps"),(16,"critical_overlaps")])
def test_computed_finite_certificates_require_every_source_bound_field(number,field):
    candidate=wire(_native(core_expected(number)))
    result=evaluate_seed_response(f"DEMO_{number:02d}",candidate)
    assert result.passed,result.failure_reasons
    candidate.pop(field)
    assert not evaluate_seed_response(f"DEMO_{number:02d}",candidate).passed


def test_triangle_and_bouquet_require_gauge_and_original_obstructions():
    candidate=dict(potential=[0,2,4],dual=[-1,1,-1],d1_cochain=[-1],
                   classification="NONCLOSED_NOT_H1_CLASS",repair_claim="OPTIMAL_NONZERO_RESIDUAL_NOT_EXACT_REPAIR")
    assert evaluate_seed_response("DEMO_13",candidate).passed
    changed=deepcopy(candidate); changed["potential"]=[1,3,5]
    assert not evaluate_seed_response("DEMO_13",changed).passed
    changed=deepcopy(candidate); changed["classification"]="NONZERO_H1_CLASS"
    assert not evaluate_seed_response("DEMO_13",changed).passed
    bouquet=dict(potential=[0]*5,dual=[1,1,1,5,5,5],cycles=[[1,1,1,0,0,0],[0,0,0,1,1,1]],
                 pairings=[1,2],zero_repair="IMPOSSIBLE_NONZERO_CYCLE_PAIRINGS")
    assert evaluate_seed_response("DEMO_23",bouquet).passed
    bouquet["pairings"]=[0,0]
    assert not evaluate_seed_response("DEMO_23",bouquet).passed


def test_weighted_hodge_uses_the_declared_metric_adjoint():
    d0=sp.Matrix([[-1,1,0],[-1,0,1],[0,-1,1]])
    d1=sp.Matrix([[1,-1,1]]); m1=sp.diag(1,2,3)
    adjoint=m1.inv()*d1.T*2
    # d1*c=-1, d1*d1* = 11/3, so q=-3/11.
    q=sp.Rational(-3,11)
    exact=sp.Matrix([1,4,2])-adjoint*q
    p=[0,exact[0],exact[1]]
    candidate=dict(potential=[str(v) for v in p],harmonic=[0,0,0],face_potential=[str(q)],
                   d0_adjoint=[[str(v) for v in row] for row in (d0.T*m1).tolist()],
                   d1_adjoint=[[str(v) for v in row] for row in adjoint.tolist()],
                   comparison="ORTHOGONAL_L2_IS_NOT_WEIGHTED_L1")
    result=evaluate_seed_response("DEMO_14",candidate)
    assert result.passed,result.failure_reasons
    candidate["d1_adjoint"]=[[1],[-1],[1]]
    assert not evaluate_seed_response("DEMO_14",candidate).passed


def test_declared_projective_channel_distinguishes_conditioning():
    def encoded(m): return [[[str(sp.re(z)),str(sp.im(z))] for z in row] for row in m.tolist()]
    v=sp.Matrix([1,0,0,1]);rho=v*v.T/2
    output=sp.diag(sp.Rational(1,2),0,0,sp.Rational(1,2))
    candidate=dict(kraus=[encoded(sp.diag(1,0)),encoded(sp.diag(0,1))],density=encoded(rho),
                   marginal_first=encoded(sp.eye(2)/2),marginal_second=encoded(sp.eye(2)/2),output=encoded(output),
                   remote_after=encoded(sp.eye(2)/2),branch_index=0,branch_probability="1/2",
                   branch_remote=encoded(sp.diag(1,0)),factor_order=["00","01","10","11"])
    result=evaluate_seed_response("DEMO-Q22",candidate)
    assert result.passed,result.failure_reasons
    candidate["remote_after"]=candidate["branch_remote"]
    assert not evaluate_seed_response("DEMO-Q22",candidate).passed


def test_schema_exposes_types_without_reference_answer_constants():
    schema=seed_candidate_schema("DEMO_13")
    assert schema["properties"]["potential"]["minItems"]==3
    assert "const" not in str(schema)


@pytest.mark.parametrize("seed,reason", [
    ("DEMO-N00", "NATIVE_GENESIS_SOURCE_UNAVAILABLE"),
    ("DEMO_03", "GRAMMAR_SOURCE_UNAVAILABLE"),
])
def test_missing_source_bytes_are_unavailable_instead_of_a_negative_oracle(monkeypatch, seed, reason):
    from pathlib import Path
    from omega_engine_pfp.infrastructure.providers import SeedHostVerifier

    def missing_source(path):
        raise FileNotFoundError(path)

    monkeypatch.setattr(Path, "read_bytes", missing_source)
    result = evaluate_seed_response(seed, {})
    assert result.passed is False
    assert result.failure_reasons == [reason + ": FileNotFoundError"]
    with pytest.raises(ValueError, match="UNAVAILABLE_IS_NOT_A_REFUSAL_ORACLE"):
        SeedHostVerifier().verify_refusal(seed, {"payload": {}, "expected_reason": result.failure_reasons[0]})


def test_rational_source_fields_accept_equivalent_strings_without_coercing_integer_geometry():
    cases=[
        ("DEMO_07",dict(potential=[0,2,-1],d0=[[-1,1,0],[0,-1,1]],original=["2","-6/2"],residual=[0,0]),"original"),
        ("DEMO_08",dict(potential=[0,2,5],d0=[[-1,1,0],[-1,0,1],[0,-1,1]],original=["2","10/2","3"],residual=[0,0,0]),"original"),
        ("DEMO-N08",dict(potential=[0,0,0],dual=[1,1,1],after_face=dict(d0=[[-1,1,0],[0,-1,1],[1,0,-1]],cochain=["1","2/2","1"],face_boundary=[1,1,1],potential=[0,0,0],dual=[1,1,1])),None),
        ("DEMO_13",dict(potential=[0,2,4],dual=[-1,1,-1],d1_cochain=["-2/2"],classification="NONCLOSED_NOT_H1_CLASS",repair_claim="OPTIMAL_NONZERO_RESIDUAL_NOT_EXACT_REPAIR"),"d1_cochain"),
        ("DEMO_23",dict(potential=[0]*5,dual=[1,1,1,5,5,5],cycles=[[1,1,1,0,0,0],[0,0,0,1,1,1]],pairings=["2/2","2"],zero_repair="IMPOSSIBLE_NONZERO_CYCLE_PAIRINGS"),"pairings"),
    ]
    for seed,candidate,field in cases:
        result=evaluate_seed_response(seed,candidate)
        assert result.passed,(seed,result.failure_reasons)
        bad=deepcopy(candidate)
        values=bad[field] if field else bad["after_face"]["cochain"]
        values[0]=True
        assert not evaluate_seed_response(seed,bad).passed
        values[0]=1.0
        assert not evaluate_seed_response(seed,bad).passed
    incidence=deepcopy(cases[0][1]); incidence["d0"][0][0]="-1"
    assert not evaluate_seed_response("DEMO_07",incidence).passed
    cycle=deepcopy(cases[2][1]); cycle["after_face"]["face_boundary"][0]="1"
    assert not evaluate_seed_response("DEMO-N08",cycle).passed
