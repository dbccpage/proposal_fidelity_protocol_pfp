"""The native pharmacy adapter maps the host reply exactly and refuses everything else.

No silent fallback: a missing host, a failed crossing, a host refusal or an
unexpected reply shape is a typed `NativePharmacyUnavailable`.
"""

from __future__ import annotations

from hashlib import sha256

import pytest

from omega_engine_epistemic_immune_system.infrastructure.mssn_pharmacy import (
    DetectionContext,
    HostReplayReceipt,
)
from omega_engine_epistemic_immune_system.infrastructure.native_pharmacy import (
    NATIVE_CLASS_CODES,
    NativePharmacy,
    NativePharmacyUnavailable,
    native_context,
    parse_native_report,
)
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal

REPORT = {
    "detectors_run": list(NATIVE_CLASS_CODES.values()),
    "findings": [
        {"class": "SelfCertification", "disposition": "Refuse", "locus": "/status", "detail": "d"}
    ],
    "normalized_json_digest": "sha256:" + "1" * 64,
    "semantic_payload_digest": "sha256:" + "2" * 64,
    "subject_digest": "sha256:" + "1" * 64,
    "raw_bytes_digest": "sha256:" + sha256(b'{"status":"VERIFIED"}').hexdigest(),
}


class Host:
    def __init__(self, outcome) -> None:
        self.outcome = outcome
        self.calls: list[tuple[str, dict]] = []

    def pharmacy_detect(self, candidate, context=None):
        self.calls.append((candidate, context))
        return self.outcome


def test_codes_and_dispositions_are_mapped() -> None:
    report = parse_native_report(REPORT)
    assert [(f.failure_class, f.disposition, f.source) for f in report.findings] == [
        ("SELF_CERTIFICATION", "REFUSE", "native")
    ]


def test_the_python_only_context_field_is_not_sent() -> None:
    wire = native_context(
        DetectionContext(
            prompt="p",
            granted_persona_roles=("reviewer",),
            host_replay_receipt=HostReplayReceipt("r", "h", "sha256:" + "3" * 64, True),
        )
    )
    assert "granted_persona_roles" not in wire
    assert wire["host_replay_receipt"]["replay_passed"] is True
    assert wire["prompt"] == "p"


@pytest.mark.parametrize(
    ("outcome", "code"),
    [
        (Err(Refusal("HOST_TIMEOUT", "slow")), "FFI_CROSSING_FAILED"),
        (Ok({"success": False, "error": "invalid pharmacy_detect input: x"}), "NATIVE_PHARMACY_REFUSED"),
        (Ok({"success": True, "result": {**REPORT, "findings": [{"class": "Invented"}]}}), "NATIVE_REPLY_MALFORMED"),
        (Ok({"success": True, "result": []}), "NATIVE_REPLY_MALFORMED"),
    ],
)
def test_every_failure_is_a_typed_refusal(outcome, code: str) -> None:
    with pytest.raises(NativePharmacyUnavailable) as caught:
        NativePharmacy(Host(outcome)).detect("{}", DetectionContext())
    assert caught.value.code == code


def test_a_missing_binary_is_a_typed_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    import omega_engine_pfp.ffi as ffi

    def missing(self, binary_path=None):
        raise FileNotFoundError("HOST_BINARY_NOT_FOUND: not built")

    monkeypatch.setattr(ffi.RustSymbolGameHost, "__init__", missing)
    with pytest.raises(NativePharmacyUnavailable) as caught:
        NativePharmacy().detect("{}", DetectionContext())
    assert caught.value.code == "HOST_BINARY_NOT_FOUND"


def test_reports_are_memoised_per_candidate_and_context() -> None:
    host = Host(Ok({"success": True, "result": REPORT}))
    pharmacy = NativePharmacy(host)
    first = pharmacy.detect('{"status":"VERIFIED"}', DetectionContext())
    second = pharmacy.detect('{"status":"VERIFIED"}', DetectionContext())
    pharmacy.detect('{"status":"VERIFIED"}', DetectionContext(prompt="other"))
    assert first is second
    assert len(host.calls) == 2


@pytest.mark.parametrize("raw_digest", [None, "sha256:" + "0" * 64])
def test_unbound_or_transplanted_report_is_refused_and_not_cached(raw_digest):
    host = Host(Ok({"success": True, "result": {**REPORT, "raw_bytes_digest": raw_digest}}))
    pharmacy = NativePharmacy(host)
    with pytest.raises(NativePharmacyUnavailable) as caught:
        pharmacy.detect('{"status":"VERIFIED"}', DetectionContext())
    assert caught.value.code == "NATIVE_REPLY_MALFORMED"
    host.outcome = Ok({"success": True, "result": REPORT})
    assert pharmacy.detect('{"status":"VERIFIED"}', DetectionContext()).raw_bytes_digest == REPORT["raw_bytes_digest"]
    assert len(host.calls) == 2


def test_current_native_persona_finding_retains_native_provenance():
    result = {**REPORT, "findings": [{
        "class": "PersonaAuthorityLeak", "disposition": "Refuse", "locus": "/persona",
        "detail": "unauthorized native persona field",
    }]}
    finding, = parse_native_report(result).findings
    assert (finding.failure_class, finding.source, finding.locus) == (
        "PERSONA_AUTHORITY_LEAK", "native", "/persona"
    )
