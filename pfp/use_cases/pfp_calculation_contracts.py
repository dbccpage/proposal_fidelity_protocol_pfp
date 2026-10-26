"""Construct answer-free calculation and public workpad contracts for any task.

No campaign identifiers, expected answers, provider calls or filesystem reads.
AuthorityEffect: None.
"""

from __future__ import annotations

from copy import deepcopy


def required_object(properties):
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def calculation_schema(certificate_schema, field_carriers):
    fields = certificate_schema["properties"]
    if set(fields) != set(field_carriers):
        raise ValueError("CALCULATION_CARRIER_FIELDS_MISMATCH")
    return required_object(
        {
            key: required_object(
                {
                    "carrier": {"const": field_carriers[key]},
                    "expression": {"type": "string", "minLength": 1, "maxLength": 360},
                    "result": deepcopy(value),
                }
            )
            for key, value in fields.items()
        }
    )


def public_workpad_schema(field_carriers, *, prompt_id=None):
    """At most three public records, bound to the caller's exact prompt identity."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **required_object(
            {
                "derived_under_policy": {"const": "SPK-001"},
                "prompt_id": {"const": prompt_id}
                if prompt_id is not None
                else {"type": "string", "minLength": 1, "maxLength": 200},
                "records": {
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 3,
                    "items": required_object(
                        {
                            "field": {"enum": list(field_carriers)},
                            "expression": {"type": "string", "minLength": 1, "maxLength": 180},
                            "result": {"type": "string", "minLength": 1, "maxLength": 120},
                        }
                    ),
                },
                "open": {
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 8,
                    "items": {"type": "string", "minLength": 1, "maxLength": 160},
                },
            }
        ),
    }
