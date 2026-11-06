"""Checks that the oracle freezers are deterministic and self-consistent.

A frozen oracle is only useful if freezing it twice on the same Python
gives the same bytes, and if the recorded vectors are what the running
interpreter actually does.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

import freeze_json_acceptance
import freeze_python_case
import freeze_python_repr


def test_repr_freeze_is_deterministic_and_matches_repr(tmp_path: Path) -> None:
    first = freeze_python_repr.freeze(tmp_path / "a").read_bytes()
    second = freeze_python_repr.freeze(tmp_path / "b").read_bytes()
    assert first == second
    data = json.loads(first)
    assert data["unicode_version"] == unicodedata.unidata_version
    assert len(data["scalar_repr_sha256"]) == 64
    for vector in data["vectors"]:
        assert vector["repr"] == repr(vector["text"])
    assert {"text": "'\"", "repr": "'\\'\"'"} in data["vectors"]


def test_json_acceptance_truthiness_and_stream(tmp_path: Path) -> None:
    first = freeze_json_acceptance.freeze(tmp_path / "a").read_bytes()
    second = freeze_json_acceptance.freeze(tmp_path / "b").read_bytes()
    assert first == second
    data = json.loads(first)
    truth = {case["input_json"]: case["output"] for case in data["truthiness"]}
    # Zero, negative zero, empty containers, empty string and null are falsy.
    assert truth["0"] is False and truth["-0.0"] is False and truth["[]"] is False
    assert truth['""'] is False and truth["null"] is False and truth["{}"] is False
    # A list holding null, a NUL string and an overflowing float are truthy.
    assert truth["[null]"] is True and truth['"\\u0000"'] is True and truth["1e999"] is True
    assert data["float_stream"] == {"seed": 480, "count": 262144,
                                    "sha256": data["float_stream"]["sha256"]}
    # A different seed must give a different stream digest.
    assert freeze_json_acceptance.float_stream_sha256(seed=481, count=64) != \
        freeze_json_acceptance.float_stream_sha256(seed=480, count=64)


@pytest.mark.skipif(unicodedata.unidata_version == freeze_python_case.REQUIRED_UNICODE,
                    reason="refusal path applies only to other Unicode versions")
def test_case_freeze_refuses_other_unicode_versions(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires Python Unicode 15.0.0"):
        freeze_python_case.freeze(tmp_path)
    assert not (tmp_path / freeze_python_case.FIXTURE_NAME).exists()


@pytest.mark.skipif(unicodedata.unidata_version != freeze_python_case.REQUIRED_UNICODE,
                    reason="the casing oracle is pinned to Unicode 15.0.0 (Python 3.12)")
def test_case_freeze_is_deterministic_and_matches_str_methods(tmp_path: Path) -> None:
    first = freeze_python_case.freeze(tmp_path / "a", emit_tables=True)
    second = freeze_python_case.freeze(tmp_path / "b")
    assert first.read_bytes() == second.read_bytes()
    data = json.loads(first.read_bytes())
    for vector in data["vectors"]:
        assert vector["upper"] == vector["text"].upper()
        assert vector["lower"] == vector["text"].lower()
    upper = {point: text for point, text in data["mappings"]["upper"]}
    assert upper[ord("ß")] == "SS"
    # Final sigma: capital sigma at the end of a word lowers to the final form.
    lowered = {vector["text"]: vector["lower"] for vector in data["vectors"]}
    assert lowered["ΟΣ"] == "ος" and lowered["ΟΣΑ"] == "οσα"
    assert ord("A") in data["cased"] and ord("'") in data["case_ignorable"]
    tables = (tmp_path / "a" / freeze_python_case.TABLES_NAME).read_text(encoding="utf-8")
    assert "pub(crate) const UPPER" in tables and "pub(crate) const CASE_IGNORABLE" in tables
