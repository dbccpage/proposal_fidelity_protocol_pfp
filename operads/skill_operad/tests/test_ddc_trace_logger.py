"""Focused checks for the self-contained DDC trace logger.

AuthorityEffect: None. These tests verify tape grammar and byte-level hash
linkage only; they do not certify the actions described by a trace.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import pytest

_SHARED_DIR = Path(__file__).resolve().parents[1]
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from ddc_trace_logger import (
    DDATapeDFA,
    DDATapeValidationError,
    DDCTapeDFA,
    DDCTapeValidationError,
    DdaDialect,
    DdaLetter,
    DdcDialect,
    DdcLetter,
    TraceLogger,
    _get_default_trace_dir,
)


def _record_hash(record: dict) -> str:
    payload = {key: value for key, value in record.items() if key != "step_hash"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_success_trace_is_grammar_valid_and_hash_chained(tmp_path: Path):
    logger = TraceLogger("test-runner", trace_dir=tmp_path, auto_lifecycle=False)
    logger.record_step(
        letter=DdcLetter.C,
        action_name="expose",
        input_state="before",
        output_state="exposed",
        witness="W-C",
    )
    logger.finalize_success(
        input_state="exposed", output_state="complete", witness="W-I"
    )

    rows = [
        json.loads(line)
        for line in logger.jsonl_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["letter"] for row in rows] == ["C", "I", "T"]
    assert DDCTapeDFA.validate("C.I.T", dialect=DdcDialect.LEGACY_V1.value)
    assert rows[0]["prev_step_hash"] is None
    assert rows[1]["prev_step_hash"] == rows[0]["step_hash"]
    assert rows[2]["prev_step_hash"] == rows[1]["step_hash"]
    assert all(row["step_hash"] == _record_hash(row) for row in rows)


def test_experimental_refusal_requires_z_then_terminal():
    assert DDCTapeDFA.validate("R.Z.T", dialect="experimental-z-v1")
    with pytest.raises(DDCTapeValidationError):
        DDCTapeDFA.validate("R.Z", dialect="experimental-z-v1")


def test_default_trace_directory_stays_outside_the_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))

    trace_dir = _get_default_trace_dir()

    assert trace_dir == tmp_path / "coda_ddc_traces"
    assert trace_dir.is_dir()
    assert "_intelligence" not in trace_dir.parts


def test_backward_compatibility_aliases():
    assert DdaLetter is DdcLetter
    assert DdaDialect is DdcDialect
    assert DDATapeDFA is DDCTapeDFA
    assert DDATapeValidationError is DDCTapeValidationError
