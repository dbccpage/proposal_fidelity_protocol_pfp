"""Test suite for RFC 8785 JSON Canonicalization Scheme (JCS) and omega-canonical-v1 wire parity.

Verifies:
1. UTF-16 code unit property key sorting (RFC 8785 §3.2.3).
2. ECMAScript 7.1.12.1 number serialization (integers, negative zero, scientific exponent thresholds).
3. Minimal string escaping without solidus escaping (RFC 8785 §3.2.2.2).
4. Refusal of duplicate keys.
5. Refusal of integers exceeding 2^53 - 1 (MAX_SAFE_INTEGER).
6. Refusal of non-finite numbers (NaN, Infinity).
7. SHA-256 digest computation over canonical bytes.
8. Byte-exact cross-language wire parity with Rust omega_symbol_game_runtime.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from omega_engine_pfp.domain.canonical import (
    MAX_SAFE_INTEGER,
    JcsError,
    canonical_bytes,
    canonicalize_json_str,
    domain_digest,
    format_es_number,
    format_es_string,
    rfc8785_canonical_bytes,
    rfc8785_canonical_json,
    rfc8785_digest_sha256,
)

# ---------------------------------------------------------------------------
# 1. UTF-16 Code Unit Sorting Tests
# ---------------------------------------------------------------------------

def test_utf16_code_unit_sorting_order():
    """RFC 8785 §3.2.3: Properties are sorted by UTF-16 code unit values.

    U+FB33 (Hebrew Pointed Dalet 'דּ') has UTF-16 code unit 0xFB33.
    U+1F600 (Grinning Face '😀') in UTF-16 is surrogate pair [0xD83D, 0xDE00].
    Since 0xD83D < 0xFB33, the emoji must sort BEFORE the Hebrew character,
    contrary to Unicode scalar value sorting (where 0xFB33 < 0x1F600).
    """
    raw = '{"\uFB33": 1, "\U0001F600": 2}'
    canonical = canonicalize_json_str(raw)
    assert canonical == '{"😀":2,"דּ":1}'

    # Also via Python dict
    py_dict = {"\uFB33": 1, "\U0001F600": 2}
    assert rfc8785_canonical_json(py_dict) == '{"😀":2,"דּ":1}'


def test_ascii_property_keys_sorting():
    """Verify standard ASCII keys are sorted ordinally without extra whitespace."""
    raw = '{"b": 1, "a": 2, "aa": 3, "ab": 4}'
    assert canonicalize_json_str(raw) == '{"a":2,"aa":3,"ab":4,"b":1}'
    assert rfc8785_canonical_json({"b": 1, "a": 2, "aa": 3, "ab": 4}) == '{"a":2,"aa":3,"ab":4,"b":1}'


def test_nested_object_key_sorting():
    """Verify nested objects have their keys recursively sorted by UTF-16 code units."""
    nested = {
        "z": {"y": 1, "x": 2},
        "a": [{"c": 3, "b": 4}],
    }
    expected = '{"a":[{"b":4,"c":3}],"z":{"x":2,"y":1}}'
    assert rfc8785_canonical_json(nested) == expected


# ---------------------------------------------------------------------------
# 2. ECMAScript Number Serialization Tests
# ---------------------------------------------------------------------------

def test_number_zeroes_serialization():
    """Both +0.0 and -0.0 serialize as '0'."""
    assert format_es_number(0.0) == "0"
    assert format_es_number(-0.0) == "0"
    assert format_es_number(0) == "0"
    assert rfc8785_canonical_json([0.0, -0.0, 0]) == "[0,0,0]"


def test_standard_integers_serialization():
    """Integers within safe range format without decimal or exponent."""
    assert format_es_number(1.0) == "1"
    assert format_es_number(-1.0) == "-1"
    assert format_es_number(42.0) == "42"
    assert format_es_number(-42.0) == "-42"
    assert format_es_number(42) == "42"
    assert format_es_number(-42) == "-42"


def test_decimals_serialization():
    """Decimals within (-6, 21] exponent format with decimal point."""
    assert format_es_number(1.5) == "1.5"
    assert format_es_number(-1.5) == "-1.5"
    assert format_es_number(0.125) == "0.125"


def test_scientific_exponent_thresholds():
    """Verify exponent thresholds: >= 1e21 or < 1e-6 use exponent notation."""
    # Boundary at 1e21:
    # 10^20 -> 21 digits -> "100000000000000000000"
    assert format_es_number(1e20) == "100000000000000000000"
    # 10^21 -> exponent notation "1e+21"
    assert format_es_number(1e21) == "1e+21"
    assert format_es_number(-1e21) == "-1e+21"

    # Boundary at 1e-6:
    # 1e-6 -> "0.000001"
    assert format_es_number(1e-6) == "0.000001"
    # 1e-7 -> "1e-7"
    assert format_es_number(1e-7) == "1e-7"
    assert format_es_number(-1e-7) == "-1e-7"


def test_number_array_parity_with_rust_vector():
    """Array vector matching tests/omega_symbol_game_runtime/jcs_vectors.rs line 68."""
    raw = "[1.0, -0.0, 1e21, 0.000001, 1e-7]"
    assert canonicalize_json_str(raw) == "[1,0,1e+21,0.000001,1e-7]"
    assert rfc8785_canonical_json([1.0, -0.0, 1e21, 0.000001, 1e-7]) == "[1,0,1e+21,0.000001,1e-7]"


# ---------------------------------------------------------------------------
# 3. String Escaping & No Solidus Escape Tests
# ---------------------------------------------------------------------------

def test_minimal_escaping_and_no_solidus_escape():
    """RFC 8785 §3.2.2.2: Solidus '/' MUST NOT be escaped."""
    raw = '{"url": "https://example.com/foo/bar", "quote": "hello \\"world\\"", "newline": "a\\nb"}'
    expected = '{"newline":"a\\nb","quote":"hello \\"world\\"","url":"https://example.com/foo/bar"}'
    assert canonicalize_json_str(raw) == expected

    py_dict = {
        "url": "https://example.com/foo/bar",
        "quote": 'hello "world"',
        "newline": "a\nb",
    }
    assert rfc8785_canonical_json(py_dict) == expected


def test_control_character_escapes():
    """Control characters 0x00-0x1F are escaped."""
    s = "\x08\t\n\x0c\r\x00\x1f"
    formatted = format_es_string(s)
    assert formatted == r'"\b\t\n\f\r\u0000\u001f"'


# ---------------------------------------------------------------------------
# 4. Refusals & Boundary Tests
# ---------------------------------------------------------------------------

def test_duplicate_key_refusal():
    """Duplicate object keys fail closed with JcsError."""
    with pytest.raises(JcsError, match="duplicate object key detected"):
        canonicalize_json_str('{"key": 1, "key": 2}')


def test_max_safe_integer_boundary():
    """Integers up to 2^53 - 1 succeed; larger integers fail closed."""
    assert format_es_number(MAX_SAFE_INTEGER) == str(MAX_SAFE_INTEGER)
    assert format_es_number(-MAX_SAFE_INTEGER) == str(-MAX_SAFE_INTEGER)

    safe = f'{{"safe": {MAX_SAFE_INTEGER}}}'
    assert canonicalize_json_str(safe) == f'{{"safe":{MAX_SAFE_INTEGER}}}'

    unsafe_high = MAX_SAFE_INTEGER + 1
    with pytest.raises(JcsError, match="integer magnitude exceeds 2\\^53 - 1 safe limit"):
        format_es_number(unsafe_high)

    with pytest.raises(JcsError, match="integer magnitude exceeds 2\\^53 - 1 safe limit"):
        format_es_number(-unsafe_high)


def test_non_finite_float_refusal():
    """NaN, +Infinity, -Infinity fail closed."""
    with pytest.raises(JcsError, match="non-finite numbers are forbidden in JCS"):
        format_es_number(float("nan"))

    with pytest.raises(JcsError, match="non-finite numbers are forbidden in JCS"):
        format_es_number(float("inf"))

    with pytest.raises(JcsError, match="non-finite numbers are forbidden in JCS"):
        format_es_number(float("-inf"))

    with pytest.raises(JcsError, match="non-finite numbers are forbidden in JCS"):
        canonicalize_json_str('{"val": NaN}')


# ---------------------------------------------------------------------------
# 5. Digest & Idempotency Tests
# ---------------------------------------------------------------------------

def test_idempotency():
    """JCS canonicalization is strictly idempotent: jcs(jcs(v)) == jcs(v)."""
    raw = """{
        "z": [true, false, null, 123.456],
        "a": { "inner_b": 2, "inner_a": 1 },
        "m": "test"
    }"""
    round1 = canonicalize_json_str(raw)
    round2 = canonicalize_json_str(round1)
    assert round1 == round2
    assert round1 == '{"a":{"inner_a":1,"inner_b":2},"m":"test","z":[true,false,null,123.456]}'


def test_sha256_digest_parity():
    """Verify SHA-256 digest computation matches sha256 of canonical bytes."""
    payload = {"b": 2, "a": 1}
    digest = rfc8785_digest_sha256(payload)
    expected_bytes = b'{"a":1,"b":2}'
    assert rfc8785_canonical_bytes(payload) == expected_bytes
    assert digest == hashlib.sha256(expected_bytes).hexdigest()


# ---------------------------------------------------------------------------
# 6. Golden Canonical Vectors (omega-canonical-v1) Parity
# ---------------------------------------------------------------------------

def test_golden_canonical_vectors_omega_v1():
    """Verify that omega-canonical-v1 golden vectors match Python domain digest."""
    path = Path(__file__).resolve().parent / "golden_canonical_vectors.json"
    if not path.is_file():
        pytest.skip("golden_canonical_vectors.json not found")

    content = json.loads(path.read_text(encoding="utf-8"))
    domain = content["domain"]
    vectors = content["vectors"]

    for vec in vectors:
        raw_val = json.loads(vec["raw_input_json"])
        # Digest matching
        computed_digest = domain_digest(domain, raw_val)
        assert computed_digest == vec["domain_digest_sha256"], (
            f"Digest mismatch for vector {vec['name']}: "
            f"computed {computed_digest} != expected {vec['domain_digest_sha256']}"
        )
        # Canonical bytes hex matching
        comp_bytes = canonical_bytes(raw_val)
        assert comp_bytes.hex() == vec["canonical_bytes_hex"], (
            f"Bytes hex mismatch for vector {vec['name']}: "
            f"computed {comp_bytes.hex()} != expected {vec['canonical_bytes_hex']}"
        )
