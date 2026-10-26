"""Offline decisive controls for strict simplified ingress and judge separation."""

import copy
import json

import pytest

from omega_engine_woland.tests.pilots.relational_spacetime import finite_checks as checking
from omega_engine_woland.tests.pilots.relational_spacetime import compact_checks as simplified_checking
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import proposal_body
from omega_engine_pfp.infrastructure.numbered_prompts import FIELD_CARRIERS
from omega_engine_pfp.infrastructure.numbered_prompts import prompt_id
from omega_engine_pfp.infrastructure.numbered_prompts import response_schema
from omega_engine_pfp.infrastructure.numbered_prompts import workpad_schema
from omega_engine_woland.tests.pilots.relational_spacetime.finite_fixtures import fixture_payload

PILOTS = tuple(BY_ID)


def _fixture(pilot=PILOTS[0]):
    identity = prompt_id(pilot, 1)
    packet = fixture_payload(pilot, identity)
    body = proposal_body(packet)
    body.pop("learning")
    body.pop("requested_lifts")
    body["derivation"] = {
        "argument": "Host-only fixture. No analytical proof claim.",
        "open": ["Analytical derivation remains unverified."],
    }
    body["calculations"] = {
        key: {
            "carrier": FIELD_CARRIERS[pilot][key],
            "expression": "Host-only representation; expression is unverified.",
            "result": copy.deepcopy(value),
        }
        for key, value in body["certificate"].items()
    }
    return identity, packet


def _evaluate(pilot, packet, identity=None):
    return simplified_checking.evaluate(
        pilot, identity or prompt_id(pilot, 1), json.dumps(packet, allow_nan=False)
    )


def _pad(pilot=PILOTS[0]):
    return {
        "derived_under_policy": "SPK-001",
        "prompt_id": prompt_id(pilot, 2),
        "records": [
            {
                "field": next(iter(FIELD_CARRIERS[pilot])),
                "expression": "x+x",
                "result": "unverified",
            }
        ],
        "open": ["An unresolved mathematical obligation."],
    }


@pytest.mark.parametrize("pilot", PILOTS)
def test_original_certificate_is_checked_without_historical_packet_fabrication(pilot, monkeypatch):
    identity, packet = _fixture(pilot)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("historical evaluator must not be invoked")

    monkeypatch.setattr(checking, "evaluate", forbidden)
    before = copy.deepcopy(packet)
    verdict, parsed = _evaluate(pilot, packet, identity)
    assert packet == before == parsed
    assert verdict["schema_status"] == "VALID"
    assert verdict["binding_status"] == "MATCHED"
    assert verdict["certificate_status"] == "HOST_ACCEPTED"
    assert verdict["accepted"] is True
    assert verdict["analytical_status"] == verdict["expression_status"] == "UNVERIFIED"
    assert "structural consistency only" in " ".join(verdict["claim_limits"])


@pytest.mark.parametrize("pilot", PILOTS)
def test_schema_has_same_original_certificate_field_shape(pilot):
    _, packet = _fixture(pilot)
    schema = response_schema(pilot, prompt_id=prompt_id(pilot, 1))
    row = schema["properties"]["sections"]["items"]["properties"]["rows"]["items"]
    certificate = row["properties"]["certificate"]["anyOf"][0]
    calculation = row["properties"]["calculations"]["anyOf"][0]
    assert set(certificate["properties"]) == set(proposal_body(packet)["calculations"])
    for field, value_schema in certificate["properties"].items():
        assert calculation["properties"][field]["properties"]["result"] == value_schema


@pytest.mark.parametrize("pilot", PILOTS)
def test_host_mutations_separate_binding_from_unchanged_sovereign_predicate(pilot):
    identity, packet = _fixture(pilot)
    before = copy.deepcopy(packet)
    controls = simplified_checking.negative_controls(pilot, identity, packet)
    assert packet == before
    assert controls["checked"]
    assert controls["original_certificate_status"] == "HOST_ACCEPTED"
    binding = controls["binding_only"]
    assert binding["checked"] and binding["rejected"] and binding["certificate_unchanged"]
    assert binding["verdict"]["schema_status"] == "VALID"
    assert binding["verdict"]["binding_status"] == "REFUSED"
    assert binding["verdict"]["certificate_status"] == "HOST_ACCEPTED"
    coupled = controls["coupled_wrong_value"]
    assert coupled["checked"] and coupled["rejected"]
    assert coupled["verdict"]["schema_status"] == "VALID"
    assert coupled["verdict"]["binding_status"] == "MATCHED"
    assert coupled["verdict"]["certificate_status"] == "REFUSED"
    assert not coupled["verdict"]["accepted"]


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_calculations",
        "missing_calculation_field",
        "missing_result",
        "missing_expression",
        "missing_carrier",
        "wrong_carrier",
        "extra_calculation_field",
        "extra_calculation_property",
        "missing_certificate_field",
        "missing_stamp",
        "wrong_stamp",
        "wrong_prompt_id",
        "wrong_section",
        "historical_row",
        "float_rational",
        "bool_rational",
        "integer_rational",
        "null_proposal_calculations",
        "null_proposal_certificate",
        "blank_expression",
        "long_expression",
        "extra_root",
        "bare_row",
    ),
)
def test_decisive_structural_mutations_fail_closed(mutation):
    pilot = PILOTS[0]
    identity, packet = _fixture(pilot)
    body = proposal_body(packet)
    calculation = body["calculations"]["l1_radius"]
    if mutation == "missing_calculations":
        del body["calculations"]
    elif mutation == "missing_calculation_field":
        del body["calculations"]["l1_radius"]
    elif mutation.startswith("missing_") and mutation[8:] in calculation:
        del calculation[mutation[8:]]
    elif mutation == "wrong_carrier":
        calculation["carrier"] = "other_fixture"
    elif mutation == "extra_calculation_field":
        body["calculations"]["other_field"] = copy.deepcopy(calculation)
    elif mutation == "extra_calculation_property":
        calculation["proof_verified"] = True
    elif mutation == "missing_certificate_field":
        del body["certificate"]["l1_radius"]
    elif mutation == "missing_stamp":
        del packet["derived_under_policy"]
    elif mutation == "wrong_stamp":
        packet["derived_under_policy"] = "OTHER"
    elif mutation == "wrong_prompt_id":
        body["prompt_id"] = "foreign"
    elif mutation == "wrong_section":
        packet["sections"][0]["name"] = "summary"
    elif mutation == "historical_row":
        packet = fixture_payload(pilot, identity)
    elif mutation in ("float_rational", "bool_rational", "integer_rational"):
        value = {"float_rational": 2.0, "bool_rational": True, "integer_rational": 2}[mutation]
        body["certificate"]["l1_radius"] = calculation["result"] = value
    elif mutation == "null_proposal_calculations":
        body["calculations"] = None
    elif mutation == "null_proposal_certificate":
        body["certificate"] = None
    elif mutation == "blank_expression":
        calculation["expression"] = ""
    elif mutation == "long_expression":
        calculation["expression"] = "x" * 361
    elif mutation == "extra_root":
        packet["certified_proof"] = True
    elif mutation == "bare_row":
        packet = body
    verdict, parsed = _evaluate(pilot, packet, identity)
    assert verdict["schema_status"] == "REFUSED", (mutation, verdict)
    assert verdict["binding_status"] == verdict["certificate_status"] == "NOT_CHECKED"
    assert parsed is None
    assert not verdict["accepted"]


@pytest.mark.parametrize("location", ("certificate", "calculations", "both"))
@pytest.mark.parametrize("value", (1.0, True))
def test_exact_integer_rejects_jsonschema_float_and_bool_masquerade(location, value):
    pilot = PILOTS[3]
    _, packet = _fixture(pilot)
    body = proposal_body(packet)
    if location in ("certificate", "both"):
        body["certificate"]["quotient_domain_degree"] = value
    if location in ("calculations", "both"):
        body["calculations"]["quotient_domain_degree"]["result"] = value
    verdict, parsed = _evaluate(pilot, packet)
    assert verdict["schema_status"] == "REFUSED"
    assert parsed is None


@pytest.mark.parametrize("value", (0.0, False))
def test_exact_integer_is_required_at_nested_vector_leaves(value):
    pilot = PILOTS[4]
    _, packet = _fixture(pilot)
    body = proposal_body(packet)
    body["certificate"]["continuing_transition"][0] = value
    body["calculations"]["continuing_transition"]["result"][0] = value
    verdict, parsed = _evaluate(pilot, packet)
    assert verdict["schema_status"] == "REFUSED"
    assert parsed is None


@pytest.mark.parametrize("value", (1, 1.0, "true"))
def test_boolean_field_rejects_integer_float_or_string_masquerade(value):
    pilot = PILOTS[0]
    _, packet = _fixture(pilot)
    body = proposal_body(packet)
    body["certificate"]["cone_order_preserved"] = value
    body["calculations"]["cone_order_preserved"]["result"] = value
    verdict, parsed = _evaluate(pilot, packet)
    assert verdict["schema_status"] == "REFUSED"
    assert parsed is None


def test_equal_rational_numbers_with_different_typed_representation_do_not_bind():
    pilot = PILOTS[3]
    _, packet = _fixture(pilot)
    proposal_body(packet)["calculations"]["cosine_before"]["result"] = "2/4"
    verdict, parsed = _evaluate(pilot, packet)
    assert parsed is not None
    assert verdict["binding_status"] == "REFUSED"
    assert verdict["binding_fields"] == ["cosine_before"]
    assert verdict["certificate_status"] == "HOST_ACCEPTED"
    assert not verdict["accepted"]


def test_nested_calculation_difference_is_not_hidden_by_valid_certificate():
    pilot = PILOTS[1]
    _, packet = _fixture(pilot)
    proposal_body(packet)["calculations"]["residual"]["result"][1][1] = "9"
    verdict, _ = _evaluate(pilot, packet)
    assert verdict["binding_fields"] == ["residual"]
    assert verdict["certificate_status"] == "HOST_ACCEPTED"


def test_arithmetic_wrong_but_bound_results_fail_original_judge():
    pilot = PILOTS[0]
    _, packet = _fixture(pilot)
    body = proposal_body(packet)
    body["certificate"]["l1_radius"] = "3"
    body["calculations"]["l1_radius"]["result"] = "3"
    body["calculations"]["l1_radius"]["expression"] = "1+1"
    verdict, parsed = _evaluate(pilot, packet)
    assert parsed == packet
    assert verdict["binding_status"] == "MATCHED"
    assert verdict["certificate_status"] == "REFUSED"
    assert verdict["certificate_code"] == "SPATIAL_NORM"
    assert not verdict["accepted"]


def test_wrong_expression_is_explicitly_unverified_even_with_finite_correct_certificate():
    pilot = PILOTS[0]
    _, packet = _fixture(pilot)
    body = proposal_body(packet)
    body["calculations"]["l1_radius"]["expression"] = "1+99"
    body["derivation"]["argument"] = "An unsupported claim of universal proof."
    verdict, _ = _evaluate(pilot, packet)
    assert verdict["accepted"]
    assert verdict["expression_status"] == verdict["analytical_status"] == "UNVERIFIED"


@pytest.mark.parametrize("nulls", ("both", "calculations", "certificate", "neither"))
def test_refusal_requires_both_null_and_never_becomes_mathematical_success(nulls):
    pilot = PILOTS[0]
    identity, packet = _fixture(pilot)
    body = proposal_body(packet)
    body["status"] = "TYPED_REFUSAL"
    if nulls in ("both", "calculations"):
        body["calculations"] = None
    if nulls in ("both", "certificate"):
        body["certificate"] = None
    verdict, parsed = _evaluate(pilot, packet)
    assert verdict["schema_status"] == ("VALID" if nulls == "both" else "REFUSED")
    assert (parsed is not None) == (nulls == "both")
    assert verdict["binding_status"] == verdict["certificate_status"] == "NOT_CHECKED"
    assert not verdict["accepted"]
    assert not simplified_checking.negative_controls(pilot, identity, parsed)["checked"]


@pytest.mark.parametrize(
    "mutation", ("root_duplicate", "nested_duplicate", "fenced", "trailing", "nan", "infinity")
)
def test_raw_json_rejects_duplicate_keys_nonfinite_and_output_repair(mutation):
    pilot = PILOTS[0]
    identity, packet = _fixture(pilot)
    raw = json.dumps(packet)
    if mutation == "root_duplicate":
        raw = raw[:-1] + ',"derived_under_policy":"SPK-001"}'
    elif mutation == "nested_duplicate":
        raw = raw.replace('"l1_radius": "2"', '"l1_radius":"2","l1_radius":"2"', 1)
    elif mutation == "fenced":
        raw = f"```json\n{raw}\n```"
    elif mutation == "trailing":
        raw += " additional commentary"
    elif mutation == "nan":
        raw = raw[:-1] + ',"foreign":NaN}'
    else:
        raw = raw[:-1] + ',"foreign":1e999}'
    verdict, parsed = simplified_checking.evaluate(pilot, identity, raw)
    assert verdict["code"] == "INVALID_JSON"
    assert parsed is None


@pytest.mark.parametrize("pilot", PILOTS)
def test_workpad_ingress_checks_only_small_schema(pilot):
    packet = _pad(pilot)
    verdict, parsed = simplified_checking.validate_workpad(
        pilot, packet["prompt_id"], json.dumps(packet)
    )
    assert parsed == packet
    assert verdict["schema_status"] == "VALID"
    assert verdict["code"] == "PUBLIC_WORKPAD_SCHEMA_VALID"
    assert verdict["binding_status"] == verdict["certificate_status"] == "NOT_CHECKED"
    assert verdict["expression_status"] == verdict["analytical_status"] == "UNVERIFIED"
    assert not verdict["accepted"]
    assert set(workpad_schema(pilot)["required"]) == set(packet)


@pytest.mark.parametrize(
    "mutation",
    ("foreign", "extra", "too_many", "typed_result", "certificate", "fenced", "duplicate"),
)
def test_invalid_workpad_never_enters_next_stage(mutation):
    pilot = PILOTS[0]
    packet = _pad(pilot)
    identity = packet["prompt_id"]
    if mutation == "foreign":
        packet["prompt_id"] = prompt_id(PILOTS[1], 2)
    elif mutation == "extra":
        packet["records"][0]["private_reasoning"] = "not permitted"
    elif mutation == "too_many":
        packet["records"] *= 4
    elif mutation == "typed_result":
        packet["records"][0]["result"] = 2
    elif mutation == "certificate":
        packet["certificate"] = {}
    raw = json.dumps(packet)
    if mutation == "fenced":
        raw = f"```json\n{raw}\n```"
    elif mutation == "duplicate":
        raw = raw[:-1] + ',"derived_under_policy":"SPK-001"}'
    verdict, parsed = simplified_checking.validate_workpad(pilot, identity, raw)
    assert verdict["schema_status"] == "REFUSED"
    assert parsed is None
    assert not verdict["accepted"]


def test_duplicate_named_workpad_field_is_ambiguous_even_with_distinct_expressions():
    pilot = PILOTS[0]
    packet = _pad(pilot)
    packet["records"].append(
        {"field": packet["records"][0]["field"], "expression": "y+y", "result": "different"}
    )
    verdict, parsed = simplified_checking.validate_workpad(
        pilot, packet["prompt_id"], json.dumps(packet)
    )
    assert verdict["schema_status"] == "REFUSED"
    assert verdict["code"] == "DUPLICATE_WORKPAD_FIELD"
    assert parsed is None


def test_negative_control_on_initially_wrong_certificate_cannot_be_a_positive_baseline():
    pilot = PILOTS[0]
    identity, packet = _fixture(pilot)
    body = proposal_body(packet)
    body["certificate"]["l1_radius"] = "1"
    body["calculations"]["l1_radius"]["result"] = "1"
    controls = simplified_checking.negative_controls(pilot, identity, packet)
    assert controls["original_certificate_status"] == "REFUSED"
    assert controls["coupled_wrong_value"]["rejected"]  # +1 would accidentally repair it.
    assert controls["coupled_wrong_value"]["verdict"]["certificate_code"] == "SPATIAL_NORM"


def test_strict_equality_has_no_numeric_or_container_coercion():
    from omega_engine_pfp.domain.contracts.pfp_calculations import same_typed_value

    equal = same_typed_value
    assert not equal(True, 1)
    assert not equal(1.0, 1)
    assert not equal([True], [1])
    assert not equal({"a": 1}, {"a": 1.0})
    assert not equal([1], (1,))
    assert equal({"a": ["1", 1, True]}, {"a": ["1", 1, True]})


def test_unknown_pilot_and_invalid_api_flags_fail_closed():
    with pytest.raises(ValueError, match="UNKNOWN_PO035_PILOT"):
        simplified_checking.evaluate("foreign", "id", "{}")
    with pytest.raises(ValueError, match="INVALID_PROMPT_ID"):
        simplified_checking.evaluate(PILOTS[0], True, "{}")
    with pytest.raises(ValueError, match="INVALID_WORKPAD_FLAG"):
        simplified_checking.evaluate(PILOTS[0], "id", "{}", workpad=1)
