"""Retained pharmacy receipts consumed by the actual native runtime action."""

from __future__ import annotations

import copy

import pytest

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost


def _request(raw=b'{"persona":"worker","note":"step"}'):
    return {
        "mode": "raw_receipt",
        "raw_candidate": list(raw),
        "task_key": "raw-control",
        "stage": "POST_PRODUCTION",
        "request_digest": "sha256:" + "a" * 64,
        "context": {},
    }


def _call(payload):
    crossed = RustSymbolGameHost().invoke_runtime("pharmacy_detect", payload)
    assert crossed.is_ok, crossed
    return crossed.unwrap()


def test_actual_pharmacy_port_issues_and_consumes_its_own_retained_raw_receipt():
    request = _request()
    issued = _call(request)
    assert issued["success"], issued
    receipt = issued["result"]
    assert receipt["report"]["raw_bytes_digest"].startswith("sha256:")
    verified = _call({**request, "mode": "verify_raw_receipt", "receipt": receipt})
    assert verified["success"], verified
    assert verified["result"]["accepted"] is True
    assert verified["result"]["authority_effect"] == "None"


def test_equivalent_valid_encodings_retain_distinct_raw_identities_and_recover():
    first = _request()
    second = _request(b' {"note":"st\\u0065p","persona":"worker"} ')
    a, b = (_call(request)["result"] for request in (first, second))
    assert a["report"]["normalized_json_digest"] == b["report"]["normalized_json_digest"]
    assert a["report"]["semantic_payload_digest"] == b["report"]["semantic_payload_digest"]
    assert a["report"]["raw_bytes_digest"] != b["report"]["raw_bytes_digest"]
    assert not _call({**second, "mode": "verify_raw_receipt", "receipt": a})["success"]
    assert _call({**second, "mode": "verify_raw_receipt", "receipt": b})["success"]


def test_authority_unicode_nested_and_exact_number_controls_remain_detector_evidence():
    raw = '{"items":[{"persona":"admin"}],"note":"δ","big":123456789012345678901234567890,"huge":1e400}'.encode()
    request = _request(raw)
    issued = _call(request)
    assert issued["success"], issued
    receipt = issued["result"]
    assert any(
        f["class"] == "PersonaAuthorityLeak" and f["disposition"] == "Refuse"
        for f in receipt["report"]["findings"]
    )
    assert receipt["authority_effect"] == "None"
    assert _call({**request, "mode": "verify_raw_receipt", "receipt": receipt})["success"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("raw_candidate", list(b' {"note":"st\\u0065p","persona":"worker"} ')),
        ("task_key", "foreign-task"),
        ("stage", "PRE_SELECTION"),
        ("request_digest", "sha256:" + "b" * 64),
        ("context", {"unexplored_branches": 1}),
    ],
)
def test_receipt_transplants_refuse_at_consuming_port(field, value):
    request = _request()
    receipt = _call(request)["result"]
    changed = {**request, "mode": "verify_raw_receipt", "receipt": receipt, field: value}
    assert _call(changed)["success"] is False


@pytest.mark.parametrize(
    "raw",
    [
        b'{"persona":"admin","per\\u0073ona":"worker"}',
        b"\xef\xbb\xbf{}",
        b'{"note":"\xff"}',
        b"{",
        b"{}{}",
        b"",
    ],
)
def test_strict_raw_mode_cannot_turn_malformed_or_ambiguous_bytes_into_clean_prose(raw):
    assert _call(_request(raw))["success"] is False


def test_report_and_implementation_tampering_refuse_and_prose_remains_usable():
    request = _request()
    receipt = _call(request)["result"]
    for field in ("implementation_digest", "canonicalization_profile"):
        changed = copy.deepcopy(receipt)
        changed[field] = "foreign"
        assert not _call({**request, "mode": "verify_raw_receipt", "receipt": changed})["success"]
    changed = copy.deepcopy(receipt)
    changed["report"]["findings"] = [{"class": "PersonaAuthorityLeak"}]
    assert not _call({**request, "mode": "verify_raw_receipt", "receipt": changed})["success"]
    assert _call({"candidate": "plain bounded prose"})["success"] is True
