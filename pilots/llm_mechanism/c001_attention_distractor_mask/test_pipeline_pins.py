"""
test_pipeline_pins.py - C001 pipeline.json digest pins must be real or explicitly unset.

Counterexample from the 2026-09-28 audit: pipeline.json pinned
``tokenizer_json_sha256`` to the SHA-256 of empty bytes and
``prompt_template_digest`` to the SHA-256 of ``[]``, and the only check
(test_m1_solvers.test_frozen_pipeline_json_exists_and_conforms) passed them.
"""

from __future__ import annotations

import copy
import hashlib

import pytest
from pilots.llm_mechanism.c001_attention_distractor_mask.pipeline_contract import (
    SENTINEL_DIGESTS,
    PinFinding,
    PipelinePinError,
    PipelinePinReport,
    load_pipeline,
    require_ready_pipeline,
    validate_pipeline_pins,
)

EMPTY_BYTES_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
BRACKET_PAIR_SHA256 = "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"


def _ready_pipeline() -> dict:
    """Positive control: every digest pin holds a well-formed, non-sentinel SHA-256."""
    data = copy.deepcopy(load_pipeline())
    for field in ("tokenizer_json_sha256", "prompt_template_digest"):
        data.pop(f"{field}_status", None)
        data[field] = hashlib.sha256(f"stand-in bytes for {field}".encode("utf-8")).hexdigest()
    return data


def _codes_for(report: PipelinePinReport, field: str) -> list[str]:
    return [finding.code for finding in report.findings if finding.field == field]


def test_sentinel_constants_are_the_digests_of_empty_inputs():
    assert hashlib.sha256(b"").hexdigest() == EMPTY_BYTES_SHA256
    assert hashlib.sha256(b"[]").hexdigest() == BRACKET_PAIR_SHA256
    assert SENTINEL_DIGESTS[EMPTY_BYTES_SHA256] == b""
    assert SENTINEL_DIGESTS[BRACKET_PAIR_SHA256] == b"[]"


def test_positive_control_real_looking_pins_are_ready():
    report = validate_pipeline_pins(_ready_pipeline())
    assert report.status == "READY"
    assert report.findings == ()
    assert require_ready_pipeline(_ready_pipeline()) == report


def test_counterexample_empty_bytes_tokenizer_digest_is_refused():
    data = _ready_pipeline()
    data["tokenizer_json_sha256"] = EMPTY_BYTES_SHA256
    report = validate_pipeline_pins(data)
    assert report.status == "REFUSED"
    assert _codes_for(report, "tokenizer_json_sha256") == ["PIN_UNSET_SENTINEL_DIGEST"]


def test_counterexample_bracket_pair_prompt_template_digest_is_refused():
    data = _ready_pipeline()
    data["prompt_template_digest"] = BRACKET_PAIR_SHA256
    report = validate_pipeline_pins(data)
    assert report.status == "REFUSED"
    assert _codes_for(report, "prompt_template_digest") == ["PIN_UNSET_SENTINEL_DIGEST"]


def test_counterexample_pre_audit_pipeline_values_are_refused_with_typed_error():
    """The exact pre-audit pins (both sentinels) raise a typed refusal instead of passing."""
    data = _ready_pipeline()
    data["tokenizer_json_sha256"] = EMPTY_BYTES_SHA256
    data["prompt_template_digest"] = BRACKET_PAIR_SHA256
    with pytest.raises(PipelinePinError) as excinfo:
        require_ready_pipeline(data)
    assert excinfo.value.code == "PIN_UNSET_SENTINEL_DIGEST"
    assert excinfo.value.report.codes == ("PIN_UNSET_SENTINEL_DIGEST", "PIN_UNSET_SENTINEL_DIGEST")


def test_checked_in_pipeline_is_not_ready_rather_than_valid():
    report = validate_pipeline_pins(load_pipeline())
    assert report.status == "NOT_READY"
    assert not report.is_ready
    assert report.findings == (
        PinFinding("tokenizer_json_sha256", "PIN_UNSET", "tokenizer_json_sha256_status is UNSET"),
        PinFinding("prompt_template_digest", "PIN_UNSET", "prompt_template_digest_status is UNSET"),
    )
    with pytest.raises(PipelinePinError) as excinfo:
        require_ready_pipeline(load_pipeline())
    assert excinfo.value.code == "PIN_UNSET"


@pytest.mark.parametrize(
    ("value", "status", "code"),
    [
        (None, None, "PIN_STATUS_INCONSISTENT"),
        (None, "SET", "PIN_STATUS_INCONSISTENT"),
        (hashlib.sha256(b"x").hexdigest(), "UNSET", "PIN_STATUS_INCONSISTENT"),
        (hashlib.sha256(b"x").hexdigest().upper(), None, "PIN_MALFORMED_DIGEST"),
        (hashlib.sha256(b"x").hexdigest()[:63], None, "PIN_MALFORMED_DIGEST"),
        ("", None, "PIN_MALFORMED_DIGEST"),
        (0, None, "PIN_MALFORMED_DIGEST"),
        (True, None, "PIN_MALFORMED_DIGEST"),
        (1.0, None, "PIN_MALFORMED_DIGEST"),
    ],
)
def test_trivial_pin_values_are_refused(value, status, code):
    data = _ready_pipeline()
    data["tokenizer_json_sha256"] = value
    if status is not None:
        data["tokenizer_json_sha256_status"] = status
    report = validate_pipeline_pins(data)
    assert report.status == "REFUSED"
    assert _codes_for(report, "tokenizer_json_sha256") == [code]


def test_missing_pin_is_refused_not_ignored():
    data = _ready_pipeline()
    del data["prompt_template_digest"]
    report = validate_pipeline_pins(data)
    assert report.status == "REFUSED"
    assert _codes_for(report, "prompt_template_digest") == ["PIN_MISSING"]


@pytest.mark.parametrize("data", [{}, [], None, "pipeline", 0])
def test_empty_or_non_object_pipeline_is_refused(data):
    report = validate_pipeline_pins(data)
    assert report.status == "REFUSED"
    assert report.findings


def test_report_rejects_cross_type_equality():
    report = validate_pipeline_pins(_ready_pipeline())
    assert report != ("READY", ())
    finding = PinFinding("f", "PIN_UNSET", "d")
    assert finding != ("f", "PIN_UNSET", "d")
