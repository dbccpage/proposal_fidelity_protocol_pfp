"""Transfer and mutation checks for reusable PFP contracts. AuthorityEffect: None."""

from copy import deepcopy

import jsonschema
import pytest

from omega_engine_pfp.domain.contracts.pfp_calculations import (
    calculation_binding_failures,
    same_typed_value,
)
from omega_engine_pfp.use_cases.pfp_calculation_contracts import (
    calculation_schema,
    public_workpad_schema,
)


@pytest.mark.parametrize("other", [True, 1.0, "1", [1]])
def test_typed_agreement_never_coerces_numbers(other):
    assert not same_typed_value({"vector": [1]}, {"vector": [other]})


def test_contract_transfers_to_an_unregistered_task_without_answer_values():
    certificate = {"properties": {"orchards": {"type": "integer"}}}
    carriers = {"orchards": "inventory.disjoint_orchards"}
    schema = calculation_schema(certificate, carriers)
    candidate = {
        "orchards": {"carrier": carriers["orchards"], "expression": "sum(counts)", "result": 17}
    }
    jsonschema.Draft202012Validator(schema).validate(candidate)
    assert calculation_binding_failures({"orchards": 17}, candidate, carriers) == []
    candidate["orchards"]["result"] = 17.0
    assert calculation_binding_failures({"orchards": 17}, candidate, carriers) == ["orchards"]
    assert certificate == {"properties": {"orchards": {"type": "integer"}}}


def test_contract_refuses_mismatched_carrier_fields():
    with pytest.raises(ValueError, match="CALCULATION_CARRIER_FIELDS_MISMATCH"):
        calculation_schema({"properties": {"x": {"type": "integer"}}}, {"y": "other"})


def test_public_workpad_is_bounded_and_identity_bound():
    schema = public_workpad_schema({"orchards": "inventory.disjoint_orchards"}, prompt_id="own-run")
    validator = jsonschema.Draft202012Validator(schema)
    record = {"field": "orchards", "expression": "sum(counts)", "result": "unverified"}
    valid = {
        "derived_under_policy": "SPK-001",
        "prompt_id": "own-run",
        "records": [record],
        "open": [],
    }
    assert validator.is_valid(valid)
    for key, value in [("prompt_id", "another-run"), ("records", [record] * 4)]:
        changed = deepcopy(valid)
        changed[key] = value
        assert not validator.is_valid(changed)


@pytest.mark.parametrize(
    "record", [{}, {"carrier": "other", "result": 1}, {"carrier": "correct", "result": True}]
)
def test_binding_refuses_missing_misplaced_or_coerced_results(record):
    assert calculation_binding_failures({"x": 1}, {"x": record}, {"x": "correct"}) == ["x"]
