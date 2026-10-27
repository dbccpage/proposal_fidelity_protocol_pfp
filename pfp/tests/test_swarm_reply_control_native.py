"""Native reply control versus the frozen, independent Python regex contract."""

from __future__ import annotations

import re

import pytest

from operations.domain.rop.result import Err, Refusal
from pfp.entrypoints.api.swarm_api import (
    parse_machine_block,
    validate_reply_residual,
)
from pfp.infrastructure.serialization import CanonicalizationError


# The retired frontend algorithm is retained here only as a parity oracle.
# It never supplies a production fallback when the native host is unavailable.
def legacy_fields(reply):
    match = re.search(r"```machine\s*\n(.*?)```", reply, re.DOTALL)
    if match is None:
        return {}
    fields = {}
    for field in re.finditer(r"^([A-Z_]+)=(.*)$", match.group(1), re.MULTILINE):
        key, value = field.group(1), field.group(2).strip()
        if key in fields:
            raise CanonicalizationError(f"duplicate machine-block field: {key}")
        fields[key] = value
    return fields


@pytest.mark.parametrize(
    "reply",
    [
        "no machine block",
        "```machineKEY=value```",
        "```machine\nKEY=unterminated",
        "```machine\nSUMMARY= first \r\nAUTHORITY_EFFECT=None\n```\n```machine\nSUMMARY=second\n```",
        "```machine\n \n KEY=indented\nKEY2=ignored\nKEY= a=b \n_=ok\n```",
        "```machine\x1c\nKEY=\x1funicode\x85\n```",
        "```machine\u3000\nKEY=\u00a0unicode\u202f\n```",
        "```machine bad\nKEY=ignored```\n```machine\nKEY=valid\n```",
        "```machine\nKEY=\n```",
        "```machine\r\nKEY=value\r\n```",
    ],
)
def test_native_parser_matches_retired_regex_contract(reply):
    expected = legacy_fields(reply)
    actual = parse_machine_block(reply)
    assert actual == expected
    assert list(actual) == list(expected)


def test_native_parser_refuses_duplicate_fields():
    with pytest.raises(CanonicalizationError, match="duplicate machine-block field: KEY"):
        parse_machine_block("```machine\nKEY=a\nKEY=b\n```")


@pytest.mark.parametrize(
    "fields,digest,expected",
    [
        ({}, None, ("Open", ["AUTHORITY_EFFECT_NON_NONE"])),
        ({"AUTHORITY_EFFECT": "None", "RESIDUAL_COLOUR": "Closed"}, None, ("Closed", [])),
        ({"AUTHORITY_EFFECT": "None", "RESIDUAL_COLOUR": "bogus"}, None, ("Open", [])),
        (
            {"AUTHORITY_EFFECT": "Promote", "RESIDUAL_COLOUR": "Exact"},
            None,
            ("Open", ["AUTHORITY_EFFECT_NON_NONE", "EXACT_WITHOUT_DUAL_WITNESS"]),
        ),
        ({"AUTHORITY_EFFECT": "None", "RESIDUAL_COLOUR": "Exact"}, "", ("Exact", [])),
        ({"AUTHORITY_EFFECT": "None"}, None, ("Open", [])),
    ],
)
def test_native_residual_gate_preserves_declared_contract(fields, digest, expected):
    assert validate_reply_residual(fields, dual_witness_digest=digest) == expected


def test_native_unavailable_refuses_without_python_fallback():
    class MissingHost:
        def invoke(self, payload):
            return Err(Refusal(code="HOST_BINARY_NOT_FOUND", message="fixture missing host"))

    with pytest.raises(CanonicalizationError, match="HOST_BINARY_NOT_FOUND"):
        parse_machine_block("```machine\nKEY=value\n```", port=MissingHost())
