"""Exact agreement between a proposed certificate and its calculation records.

These checks establish structural consistency, not mathematical correctness.
Task owners supply field carriers and independent certificate judges.
AuthorityEffect: None.
"""

from __future__ import annotations


def same_typed_value(left: object, right: object) -> bool:
    """Compare JSON values recursively without bool/int or int/float coercion."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(
            same_typed_value(left[key], right[key]) for key in left
        )
    if type(left) is list:
        return len(left) == len(right) and all(
            same_typed_value(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def calculation_binding_failures(certificate, calculations, field_carriers) -> list[str]:
    """Identify absent, misplaced or differently typed calculation results."""
    return [
        field
        for field, carrier in field_carriers.items()
        if field not in certificate
        or field not in calculations
        or type(calculations[field]) is not dict
        or calculations[field].get("carrier") != carrier
        or "result" not in calculations[field]
        or not same_typed_value(certificate[field], calculations[field]["result"])
    ]
