"""Twenty-five original Q40 cases through PFP ingress and the real Rust host.

NO_LLM fixtures: reference witnesses are explicitly controls. AuthorityEffect: None.
"""

import json
import os
from copy import deepcopy

import pytest

from omega_engine_adversary.tests.pilots.challenge_suite.catalog import load_case
from omega_engine_adversary.tests.pilots.challenge_suite.catalog import load_plan
from omega_engine_pfp.tests.demo_004.c_quantum.c021_q40_r.reference_solver.solver import (
    solve,
)
from omega_engine_pfp.ffi import RustSymbolGameHost
from omega_engine_pfp.infrastructure.adapters.pfp_proposals import SymbolGameProposalAdapter

ROWS = next(
    c["cases"] for f in load_plan()["families"] for c in f["challenges"] if c["challenge"] == "C021"
)[:25]


def host_fixture(answer):
    return json.dumps(
        dict(
            derived_under_policy="SPK-001",
            answer=answer,
            sections=[],
            summary=dict(
                narrowest_defensible_thesis="NO_LLM control",
                evidence_scope="Finite Q40 case",
                next_concrete_test="Native certificate verification",
            ),
            process_integrity=dict(
                seed_allows_theory_refutation=True, detected_prompt_biases=[], should_continue=False
            ),
        )
    )


@pytest.fixture(scope="module")
def adapter():
    binary = os.environ.get("OMEGA_SYMBOL_GAME_HOST")
    if not binary:
        pytest.skip("Explicit current native host binary required")
    return SymbolGameProposalAdapter(RustSymbolGameHost(binary))


@pytest.mark.parametrize("row", ROWS, ids=[r["case_id"] for r in ROWS])
def test_original_q40_native_certificate(adapter, row):
    case = load_case(row)
    answer = solve(case)
    native = adapter.verify_q40(case, host_fixture(answer)).unwrap()
    assert native["success"] is True
    assert "Pass" in native["result"]


@pytest.mark.parametrize("mutation", ["energy", "degeneracy", "basis", "case_id"])
def test_native_rejects_corrupted_witness(adapter, mutation):
    case = load_case(ROWS[0])
    answer = deepcopy(solve(case))
    if mutation == "energy":
        answer["energy"] = [999, 1]
    elif mutation == "degeneracy":
        answer["degeneracy"] = True
    elif mutation == "basis":
        answer["basis"] = []
    else:
        answer["id"] = "different-case"
    native = adapter.verify_q40(case, host_fixture(answer)).unwrap()
    assert native["success"] is True
    assert "Fail" in native["result"]
