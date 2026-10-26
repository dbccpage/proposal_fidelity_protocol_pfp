"""Missing task data is an explicit residual, never a fluent substitute."""

from copy import deepcopy

import pytest

from omega_engine_operations.domain.rop.result import Err, Ok
from omega_engine_pfp.use_cases.clarification import check_clarification

SEED = "Define a potato as a homological object."
FIELDS = ("object_model", "coefficient_domain", "requested_invariant")


def candidate(fields=FIELDS):
    return {"outcome": "QUERY_USER_MORE_INFO", "seed": SEED,
        "missing_fields": list(fields), "proposal": "",
        "questions": [{"field": field, "question": "Which " + field + " should be used?"} for field in fields]}


def checked(value, supplied=None):
    return check_clarification(value, seed=SEED, required_fields=FIELDS, supplied_fields=supplied or {})


def test_checked_query_is_not_a_mathematical_solution():
    result = checked(candidate())
    assert isinstance(result, Ok)
    assert result.value.outcome == "QUERY_USER_MORE_INFO"
    assert result.value.mathematical_acceptance == "NOT_SOLVED"


@pytest.mark.parametrize("mutation", [
    lambda value: value.update(outcome="ACCEPTED"),
    lambda value: value.update(seed="Define a tomato as a homological object."),
    lambda value: value.update(proposal="Assume a sphere and conclude H2=Q."),
    lambda value: value.update(missing_fields=[]),
    lambda value: value.update(questions=[]),
    lambda value: value["questions"][0].update(question=" "),
    lambda value: value["questions"][0].update(field="made_up"),
    lambda value: value.update(accepted=True),
])
def test_changed_identity_fake_solution_and_incomplete_queries_refuse(mutation):
    value = deepcopy(candidate())
    mutation(value)
    assert isinstance(checked(value), Err)


def test_supplied_fields_are_not_queried_again():
    fields = FIELDS[1:]
    assert isinstance(checked(candidate(fields), {"object_model": "declared complex"}), Ok)
    assert isinstance(checked(candidate(), {"object_model": "declared complex"}), Err)


def test_fully_supplied_task_cannot_claim_missing_inputs():
    assert isinstance(checked(candidate(), dict.fromkeys(FIELDS, "provided")), Err)


@pytest.mark.parametrize("value", [False, 0])
def test_false_and_zero_explicit_inputs_are_preserved(value):
    result = checked(candidate(FIELDS[1:]), {"object_model": value})
    assert isinstance(result, Ok)


def test_duplicate_requirements_and_nonfinite_data_refuse():
    assert isinstance(check_clarification(candidate(), seed=SEED,
        required_fields=("object_model", "object_model"), supplied_fields={}), Err)
    assert isinstance(checked(candidate(FIELDS[1:]), {"object_model": float("nan")}), Err)


@pytest.mark.parametrize("value", [(1, 2), b"bytes", "\ud800", {1: "non-string key"}])
def test_non_json_and_invalid_unicode_premises_refuse(value):
    assert isinstance(checked(candidate(FIELDS[1:]), {"object_model": value}), Err)


def test_invalid_unicode_seed_is_a_typed_refusal():
    value = candidate()
    value["seed"] = "\ud800"
    result = check_clarification(value, seed=value["seed"], required_fields=FIELDS, supplied_fields={})
    assert isinstance(result, Err)
