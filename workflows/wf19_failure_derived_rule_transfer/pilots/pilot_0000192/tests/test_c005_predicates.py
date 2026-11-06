"""Thirty original public C005 witnesses plus domain corruptions. NO_LLM."""

import pytest

from omega_engine_pfp.infrastructure.challenge_execution import c005_gate
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.cases import (
    get_public_examples,
)

CASES = get_public_examples()


def fixture(case):
    if case["kind"] == "consistency":
        return dict(verdict=case["expected_verdict"], certificate=case["expected_certificate"])
    return dict(
        status="SOLVED",
        repaired=case["expected_repaired"],
        weighted_l1=case["expected_weighted_l1"],
    )


@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_original_public_witness(case):
    assert c005_gate(case, fixture(case))[0] is True


@pytest.mark.parametrize(
    "mutant", ["wrong_verdict", "missing_potential", "wrong_repair", "wrong_cost"]
)
def test_domain_corruption(mutant):
    if mutant in ("wrong_verdict", "missing_potential"):
        case = next(c for c in CASES if c.get("expected_verdict") == "CONSISTENT")
        answer = fixture(case)
        if mutant == "wrong_verdict":
            answer["verdict"] = "INCONSISTENT"
            answer["certificate"] = {}
        else:
            answer["certificate"] = {}
    else:
        case = next(c for c in CASES if c["kind"] == "cycle_repair")
        answer = fixture(case)
        if mutant == "wrong_repair":
            answer["repaired"] = ["0"]
        else:
            answer["weighted_l1"] = "999999"
    assert c005_gate(case, answer)[0] is False


@pytest.mark.parametrize("bad", ["01", "+1", " 1", "-0", True, 1.0])
def test_canonical_potential_types(bad):
    case = next(c for c in CASES if c.get("expected_verdict") == "CONSISTENT")
    answer = fixture(case)
    answer["certificate"] = dict(answer["certificate"])
    answer["certificate"][next(iter(answer["certificate"]))] = bad
    assert c005_gate(case, answer)[0] is False


def test_unparseable_status_cannot_be_accepted_as_solved():
    case = next(c for c in CASES if c["kind"] == "cycle_repair")
    answer = dict(fixture(case), status="UNPARSEABLE")
    assert c005_gate(case, answer)[0] is False


def test_inconsistent_status_requires_empty_certificate():
    case = next(c for c in CASES if c.get("expected_verdict") == "INCONSISTENT")
    assert c005_gate(case, dict(verdict="INCONSISTENT", certificate={"unbound": "0"}))[0] is False
