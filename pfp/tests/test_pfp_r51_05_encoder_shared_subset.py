"""Literal-oracle controls for the bounded shared integer/string encoding subset."""

from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType

import pytest

from omega_engine_pfp.domain.canonical import (
    JcsError,
    canonicalize_json_str,
    format_es_string,
    rfc8785_canonical_bytes,
    rfc8785_canonical_json,
)
from omega_engine_pfp.infrastructure.serialization.rfc8785 import rfc8785_canonicalize


class _IntSubclass(int):
    pass


class _StrSubclass(str):
    pass


class _ListSubclass(list):
    pass


class _DictSubclass(dict):
    pass


def test_infrastructure_non_bmp_order_matches_literal() -> None:
    """Original-API qualifying red: ordinary two-key dict, no proposed imports."""
    value = {"\ue000": 1, "\U00010000": 2}
    encoded = rfc8785_canonicalize(value)
    assert encoded.format_name == "rfc8785"
    assert encoded.text == '{"\U00010000":2,"\ue000":1}'
    assert encoded.text.encode("utf-8") == b'{"\xf0\x90\x80\x80":2,"\xee\x80\x80":1}'


def test_domain_lone_surrogate_text_refused() -> None:
    """Original-API qualifying red: refusal before an invalid text result exists."""
    with pytest.raises(JcsError, match="surrogate"):
        rfc8785_canonical_json("\ud800")


def test_huge_integer_refusal_does_not_decimal_stringify() -> None:
    """Tiny bounded integer; avoid repr-based parametrized IDs or failure output."""
    value = 1 << 20000
    message = "integer magnitude exceeds 2^53 - 1 safe limit"
    with pytest.raises(JcsError, match="2\\^53") as domain_error:
        rfc8785_canonical_json(value)
    assert str(domain_error.value) == message
    with pytest.raises(TypeError, match="2\\^53") as infrastructure_error:
        rfc8785_canonicalize(value)
    assert str(infrastructure_error.value) == message


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ({"z": 1, "a": 2}, '{"a":2,"z":1}'),
        ({"aa": 1, "a": 2, "": 3}, '{"":3,"a":2,"aa":1}'),
        ([{"\ue000": 1, "\U00010000": 2}, 0], '[{"\U00010000":2,"\ue000":1},0]'),
        ({"\n": 1, "a": 2, "\r": 3}, '{"\\n":1,"\\r":3,"a":2}'),
        ([None, True, False, 0, -1], '[null,true,false,0,-1]'),
        (["\u00e9", "e\u0301"], '["\u00e9","e\u0301"]'),
        (["/", "\"", "\\", "\x00", "\x1f"], '["/","\\\"","\\\\","\\u0000","\\u001f"]'),
        ({"\U0001f600": "\U00010000", "\ufb33": 1}, '{"\U0001f600":"\U00010000","\ufb33":1}'),
    ],
    ids=["ascii", "prefix", "nested-array", "raw-control-order", "literals", "no-normalization", "escapes", "astral"],
)
def test_shared_subset_matches_literal(value: object, expected: str) -> None:
    domain = rfc8785_canonical_json(value, strict_no_floats=True)
    infrastructure = rfc8785_canonicalize(value)
    assert domain == expected
    assert infrastructure.text == expected
    assert infrastructure.text == domain
    assert infrastructure.format_name == "rfc8785"
    assert rfc8785_canonical_bytes(value, strict_no_floats=True) == expected.encode("utf-8")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (9_007_199_254_740_991, "9007199254740991"),
        (-9_007_199_254_740_991, "-9007199254740991"),
        (1, "1"),
        (-1, "-1"),
    ],
)
def test_safe_integer_literals(value: int, expected: str) -> None:
    assert rfc8785_canonicalize(value).text == expected
    assert rfc8785_canonical_json(value, strict_no_floats=True) == expected


@pytest.mark.parametrize("value", [9_007_199_254_740_992, -9_007_199_254_740_992])
def test_out_of_range_integer_refused(value: int) -> None:
    with pytest.raises(TypeError, match="2\\^53"):
        rfc8785_canonicalize(value)
    with pytest.raises(JcsError, match="2\\^53"):
        rfc8785_canonical_json(value, strict_no_floats=True)


@pytest.mark.parametrize("value", [0.0, -0.0, 1.25, float("nan"), float("inf"), float("-inf")])
def test_infrastructure_float_refusal(value: float) -> None:
    with pytest.raises(TypeError, match="does not encode float"):
        rfc8785_canonicalize(value)


@pytest.mark.parametrize(
    "value",
    [
        "\udfff",
        {"\ud800": 1},
        {"a": "\ud800"},
        ["\udfff"],
        {"a": [{"b": "\ud800"}]},
        "\ud800\udc00",
    ],
    ids=["value", "key", "object-value", "array", "nested", "literal-surrogate-pair"],
)
def test_invalid_scalar_strings_refused(value: object) -> None:
    with pytest.raises(TypeError, match="surrogate"):
        rfc8785_canonicalize(value)
    with pytest.raises(JcsError, match="surrogate"):
        rfc8785_canonical_json(value)
    with pytest.raises(JcsError, match="surrogate"):
        rfc8785_canonical_bytes(value)


@pytest.mark.parametrize("value", [{1: 2}, {1: 2, "1": 3}, {True: 1}])
def test_non_string_mapping_keys_refused(value: object) -> None:
    with pytest.raises(TypeError, match="keys must be strings"):
        rfc8785_canonicalize(value)
    with pytest.raises(JcsError, match="exact strings"):
        rfc8785_canonical_json(value)


@pytest.mark.parametrize(
    "value",
    [
        _IntSubclass(1),
        _StrSubclass("x"),
        _ListSubclass([1]),
        _DictSubclass(a=1),
        (1,),
        MappingProxyType({"a": 1}),
        Decimal("1"),
        b"x",
    ],
    ids=["int-subclass", "str-subclass", "list-subclass", "dict-subclass", "tuple", "mapping", "decimal", "bytes"],
)
def test_infrastructure_preserves_exact_type_refusals(value: object) -> None:
    with pytest.raises(TypeError, match="does not encode"):
        rfc8785_canonicalize(value)


def test_domain_preserves_tuple_mapping_and_bigint_extensions() -> None:
    assert rfc8785_canonical_json((MappingProxyType({"b": 2, "a": 1}),)) == '[{"a":1,"b":2}]'
    assert rfc8785_canonical_json(9_007_199_254_740_992, allow_bigint=True) == "9007199254740992"


def test_raw_json_scalar_and_duplicate_boundaries() -> None:
    assert canonicalize_json_str('"\\ud800\\udc00"') == '"\U00010000"'
    with pytest.raises(JcsError, match="surrogate"):
        canonicalize_json_str('"\\ud800"')
    with pytest.raises(JcsError, match="duplicate object key"):
        canonicalize_json_str('{"a":1,"a":2}')


def test_exact_string_keys_and_direct_string_primitive() -> None:
    with pytest.raises(JcsError, match="exact strings"):
        rfc8785_canonical_json({_StrSubclass("a"): 1})
    with pytest.raises(JcsError, match="exact strings"):
        format_es_string(_StrSubclass("a"))
    assert format_es_string("\U00010000") == '"\U00010000"'
