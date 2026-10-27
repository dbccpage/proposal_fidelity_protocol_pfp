"""Typed-contract tests for the PFP rewriting folder.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pfp.domain.rewriting import rewriting_types as M

_here = Path(__file__).resolve()
ROOT = _here.parents[2] / "infrastructure" / "yaml"

CATALOG = yaml.safe_load((ROOT / "rewriting/rewriting_types.yaml").read_text(encoding="utf-8"))
EXAMPLE = CATALOG["example"]


def _receipt(data: dict):
    return M.CompilationReceipt.model_validate(data, strict=False)


def test_yaml_example_validates_against_model():
    receipt = _receipt(EXAMPLE)
    assert receipt.authority_effect == "None"
    assert receipt.wire.term == "<<p><v1><<q><s0>><<c><s1>>>"


def test_yaml_roles_match_enum():
    assert [r.value for r in M.SpanRole] == CATALOG["span_roles"]


def test_yaml_wire_profile_matches_model():
    assert CATALOG["wire_profile"]["name"] == "mss-boundary-v1"
    with pytest.raises(ValidationError):
        M.BoundaryWire.model_validate({"profile": "mss-boundary-v2", "term": "x"}, strict=False)


def _spans(*triples):
    return [{"start_byte": a, "end_byte": b, "role": r} for a, b, r in triples]


def _partition(length, spans):
    return M.SpanPartition.model_validate(
        {"prompt_byte_length": length, "spans": spans}, strict=False
    )


def test_partition_accepts_contiguous_cover():
    assert len(_partition(10, _spans((0, 4, "task"), (4, 10, "context"))).spans) == 2


@pytest.mark.parametrize(
    "length,spans",
    [
        (10, _spans((0, 4, "task"), (5, 10, "context"))),  # gap
        (10, _spans((0, 6, "task"), (4, 10, "context"))),  # overlap
        (10, _spans((0, 4, "task"), (0, 4, "task"), (4, 10, "context"))),  # duplication
        (10, _spans((1, 10, "task"))),  # does not start at 0
        (10, _spans((0, 8, "task"))),  # does not cover whole prompt
        (10, _spans((0, 11, "task"))),  # exceeds prompt
        (10, _spans((0, 0, "task"), (0, 10, "context"))),  # empty span
        (10, _spans((0, 10, "bogus"))),  # unknown role
    ],
)
def test_partition_rejects_malformed(length, spans):
    with pytest.raises(ValidationError):
        _partition(length, spans)


def test_bool_rejected_for_byte_offsets():
    with pytest.raises(ValidationError):
        M.ByteSpan(start_byte=False, end_byte=1, role=M.SpanRole.TASK)


@pytest.mark.parametrize(
    "term",
    [
        "<<p><v1>>",
        "<<p><v1><<q><s1>>>",  # symbols must start at s0
        "<<p><v1><<q><s0>><<c><s0>>>",  # duplicate symbol
        "<<p><v1><<q><s0>> <<c><s1>>>",  # whitespace is not part of the wire
        "<<p><v2><<q><s0>>>",
    ],
)
def test_wire_rejects_malformed(term):
    with pytest.raises(ValidationError):
        M.BoundaryWire(profile="mss-boundary-v1", term=term)


def test_receipt_rejects_mutated_symbol_text():
    bad = copy.deepcopy(EXAMPLE)
    bad["symbols"][0]["text"] = "Summarize It."
    with pytest.raises(ValidationError):
        _receipt(bad)


def test_receipt_rejects_wrong_digest():
    bad = copy.deepcopy(EXAMPLE)
    bad["prompt_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        _receipt(bad)


def test_receipt_rejects_dropped_symbol():
    bad = copy.deepcopy(EXAMPLE)
    bad["symbols"] = bad["symbols"][:1]
    with pytest.raises(ValidationError):
        _receipt(bad)


def test_receipt_rejects_partition_shorter_than_prompt():
    bad = copy.deepcopy(EXAMPLE)
    bad["partition"]["prompt_byte_length"] = 13
    bad["partition"]["spans"] = bad["partition"]["spans"][:1]
    with pytest.raises(ValidationError):
        _receipt(bad)


def test_receipt_rejects_non_none_authority_and_extra_fields():
    bad = copy.deepcopy(EXAMPLE)
    bad["authority_effect"] = "Grant"
    with pytest.raises(ValidationError):
        _receipt(bad)
    extra = copy.deepcopy(EXAMPLE)
    extra["verdict"] = "ok"
    with pytest.raises(ValidationError):
        _receipt(extra)


def test_multibyte_prompt_uses_utf8_byte_offsets():
    import hashlib

    prompt = "café ok"  # 6 bytes + ... e-acute is 2 bytes
    raw = prompt.encode("utf-8")
    data = {
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(raw).hexdigest(),
        "partition": {
            "prompt_byte_length": len(raw),
            "spans": _spans((0, 5, "task"), (5, len(raw), "context")),
        },
        "wire": {"profile": "mss-boundary-v1", "term": "<<p><v1><<q><s0>><<c><s1>>>"},
        "symbols": [
            {"symbol_token": "s0", "start_byte": 0, "end_byte": 5, "text": "café"},
            {"symbol_token": "s1", "start_byte": 5, "end_byte": len(raw), "text": " ok"},
        ],
        "authority_effect": "None",
    }
    assert _receipt(data).partition.prompt_byte_length == len(raw)
    data["partition"]["prompt_byte_length"] = len(prompt)  # character count is wrong
    with pytest.raises(ValidationError):
        _receipt(data)


def test_cross_type_equality_rejected():
    a = M.ByteSpan(start_byte=0, end_byte=1, role=M.SpanRole.TASK)

    class Other(M.ByteSpan):
        pass

    b = Other(start_byte=0, end_byte=1, role=M.SpanRole.TASK)
    assert a != b
    assert a == M.ByteSpan(start_byte=0, end_byte=1, role=M.SpanRole.TASK)
