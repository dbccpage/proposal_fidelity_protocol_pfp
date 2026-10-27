"""Local witness-schema admission controls; no corpus or mathematical replay."""

from copy import deepcopy
from fractions import Fraction

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from pfp.infrastructure.pilot_runners.seed_checks import (
    _seed_rational_schema,
    _seed_value_schema,
    seed_candidate_schema,
)


def manual_ground_boundary_witness():
    """Literal-seed fixture; not a reference-builder round trip."""
    return {
        "raw": "<>",
        "admitted_data": [],
        "admitted_forms": [],
        "admitted_instances": [],
        "replay_packets": ["<>"],
        "profile": "mss0_ground_boundary",
    }


def test_demo01_schema_is_admitted_by_local_draft202012_metaschema():
    schema = seed_candidate_schema("DEMO_01")
    Draft202012Validator.check_schema(schema)
    invalid = deepcopy(schema)
    invalid["properties"]["admitted_data"]["prefixItems"] = []
    with pytest.raises(SchemaError):
        Draft202012Validator.check_schema(invalid)


def test_demo01_schema_admits_the_manual_witness_shape():
    schema = seed_candidate_schema("DEMO_01")
    Draft202012Validator(schema).validate(manual_ground_boundary_witness())
    missing_field = manual_ground_boundary_witness()
    del missing_field["admitted_data"]
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(missing_field)


@pytest.mark.parametrize("field", ("admitted_data", "admitted_forms", "admitted_instances"))
def test_demo01_empty_admission_arrays_refuse_an_extra_element(field):
    schema = seed_candidate_schema("DEMO_01")
    candidate = manual_ground_boundary_witness()
    candidate[field].append("a")
    assert not Draft202012Validator(schema).is_valid(candidate)


def test_nonempty_replay_tuple_preserves_length_and_item_type():
    schema = seed_candidate_schema("DEMO_01")
    replay_schema = schema["properties"]["replay_packets"]
    assert replay_schema == {
        "type": "array", "prefixItems": [{"type": "string"}], "minItems": 1, "maxItems": 1,
    }
    for replay in ([], ["<>", "<>"], [False]):
        candidate = manual_ground_boundary_witness()
        candidate["replay_packets"] = replay
        assert not Draft202012Validator(schema).is_valid(candidate)


def test_demo02_nonempty_language_shapes_keep_the_existing_tuple_semantics():
    schema = seed_candidate_schema("DEMO_02")
    Draft202012Validator.check_schema(schema)
    language = schema["properties"]["new_language"]
    assert language == {
        "type": "array", "prefixItems": [{"type": "string"}, {"type": "string"}],
        "minItems": 2, "maxItems": 2,
    }
    validator = Draft202012Validator(language)
    assert validator.is_valid(["<>", "<a>"])
    for invalid in ([], ["<>"], ["<>", "<a>", "<b>"], ["<>", False]):
        assert not validator.is_valid(invalid)


def test_nested_empty_faces_remain_empty_in_real_attachment_schema():
    # Generator only: no candidate comparison or attachment checker is executed.
    schema = seed_candidate_schema("DEMO-N15")
    Draft202012Validator.check_schema(schema)
    denied = schema["properties"]["denied"]["properties"]
    for state in ("before", "after"):
        faces = denied[state]["properties"]["faces"]
        validator = Draft202012Validator(faces)
        assert validator.is_valid([])
        assert not validator.is_valid([["a", "b", "c"]])
    events = Draft202012Validator(denied["executed_events"])
    assert events.is_valid([])
    assert not events.is_valid([{}])


def test_shape_admission_does_not_authenticate_raw_bytes_or_profile():
    schema = seed_candidate_schema("DEMO_01")
    candidate = deepcopy(manual_ground_boundary_witness())
    candidate["raw"] = "><"
    candidate["profile"] = "raw_glyphs"
    assert Draft202012Validator(schema).is_valid(candidate)


def test_direct_nested_empty_array_schema_rejects_an_added_element():
    value = {"nested": [{"empty": []}]}
    schema = _seed_value_schema(value, _seed_rational_schema())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    assert validator.is_valid({"nested": [{"empty": []}]})
    assert not validator.is_valid({"nested": [{"empty": [0]}]})


def test_direct_scalar_shapes_preserve_boolean_integer_and_exact_rational_types():
    value = {"flag": True, "count": 0, "ratio": Fraction(1, 2)}
    schema = _seed_value_schema(value, _seed_rational_schema())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    assert validator.is_valid({"flag": False, "count": 1, "ratio": "1/2"})
    assert not validator.is_valid({"flag": False, "count": True, "ratio": "1/2"})
    assert not validator.is_valid({"flag": False, "count": 1, "ratio": 0.5})
