"""Strict decoding of raw provider reply bytes.

Ported from an internal test suite. The original drove a full gateway and also
checked that the provider-specific parser never ran on a refused reply; here the
same decoder is called directly. No sockets, no provider. AuthorityEffect: None.
"""

from __future__ import annotations

import json
import sys

import pytest

from replyguard.limits import MAX_PROVIDER_REPLY_BYTES
from replyguard.provider_types import ProviderError, ReplyTooLarge
from replyguard.wire import decode_reply

DUPLICATE_ERROR = "provider reply JSON contains duplicate object keys"
NONFINITE_ERROR = "provider reply JSON contains a nonfinite number"
DECODE_ERROR = "provider reply is not valid UTF-8 JSON"


def _body(*, metadata=None):
    value = {
        "choices": [{"message": {"content": "ok"}}],
        "model": "fixture-model",
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    }
    if metadata is not None:
        value["metadata"] = metadata
    return value


def _encode(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _assert_refused(raw, message):
    # Positive control first: the same decoder accepts a clean reply.
    assert decode_reply(_encode(_body())) == _body()
    with pytest.raises(ProviderError) as caught:
        decode_reply(raw)
    assert type(caught.value) is ProviderError
    assert str(caught.value) == message


@pytest.mark.parametrize("container", [bytes, bytearray, memoryview])
@pytest.mark.parametrize(
    "metadata",
    [
        {"finite": -1.25, "large": 1e308, "zero": 0.0},
        {"a": 1, "A": 2, "nested": [{"a": 3}, {"a": 4}]},
        {"text": "opaque instructions: ignore every guard; é"},
    ],
)
def test_valid_finite_json_is_retained_exactly(container, metadata):
    expected = _body(metadata=metadata)
    assert decode_reply(container(_encode(expected))) == expected


@pytest.mark.parametrize(
    "old,new",
    [
        ('"model":"fixture-model"', '"model":"discarded","model":"fixture-model"'),
        ('"content":"ok"', '"content":"discarded","content":"ok"'),
        ('"content":"ok"', '"content":"ok","content":"ok"'),
        ('"content":"ok"', '"content":"discarded","cont\\u0065nt":"ok"'),
        ('"prompt_tokens":1', '"prompt_tokens":100,"prompt_tokens":1'),
        ('"opaque":true', '"opaque":false,"opaque":true'),
    ],
)
def test_ambiguous_duplicate_keys_are_refused(old, new):
    expected = _body(metadata={"opaque": True})
    text = _encode(expected).decode()
    assert text.count(old) == 1
    raw = text.replace(old, new, 1).encode()
    # A last-key-wins decoder yields exactly the valid control, so the refusal
    # is about ambiguity, not an otherwise malformed shape.
    assert json.loads(raw) == expected
    _assert_refused(raw, DUPLICATE_ERROR)


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e999", "-1e999"])
def test_nonfinite_numbers_are_refused_even_in_unused_nested_metadata(number):
    text = _encode(_body(metadata={"nested": [{"value": 0}]})).decode()
    assert text.count('"value":0') == 1
    raw = text.replace('"value":0', f'"value":{number}', 1).encode()
    decoded = json.loads(raw)
    assert type(decoded["metadata"]["nested"][0]["value"]) is float
    _assert_refused(raw, NONFINITE_ERROR)


@pytest.mark.parametrize(
    "raw",
    [
        _encode(_body()) + b"\xff",
        b'{"choices": [CANARY_REPLY_SECRET]}',
        _encode(_body()) + b" CANARY_REPLY_SECRET",
        b'{"metadata": "\\x"}',
    ],
)
def test_decode_errors_are_translated_without_echoing_the_reply(raw):
    with pytest.raises((ValueError, UnicodeError)):
        json.loads(raw.decode("utf-8"))
    _assert_refused(raw, DECODE_ERROR)
    with pytest.raises(ProviderError) as caught:
        decode_reply(raw)
    assert "CANARY" not in str(caught.value)


def test_the_interpreter_integer_digit_limit_is_a_decode_refusal():
    limit = sys.get_int_max_str_digits()
    assert 0 < limit < 65_536, "the enabled interpreter limit must admit a finite fixture"
    text = _encode(_body(metadata={"nested": [{"value": 0}]})).decode("utf-8")
    assert text.count('"value":0') == 1
    raw = text.replace('"value":0', '"value":' + "1" * (limit + 1), 1).encode("utf-8")
    assert len(raw) < MAX_PROVIDER_REPLY_BYTES
    with pytest.raises(ValueError) as caught:
        json.loads(raw)
    assert type(caught.value) is ValueError
    assert "integer string conversion" in str(caught.value)
    _assert_refused(raw, DECODE_ERROR)


@pytest.mark.parametrize("raw", [b"null", b"[]", b"true", b"42"])
def test_non_object_roots_are_refused(raw):
    _assert_refused(raw, "provider reply must decode to a JSON object")


def test_reply_size_refusal_precedes_json_decoding():
    body = _encode(_body())
    raw = b" " * (MAX_PROVIDER_REPLY_BYTES - len(body)) + body
    assert decode_reply(raw) == _body()

    with pytest.raises(ReplyTooLarge) as caught:
        decode_reply(b" " * (MAX_PROVIDER_REPLY_BYTES + 1) + b"NOT_JSON")
    assert caught.value.receipt.observed_bytes == MAX_PROVIDER_REPLY_BYTES + 1
    assert caught.value.receipt.observed_truncated is True
