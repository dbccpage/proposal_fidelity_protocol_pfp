"""The native anti-skill pharmacy, reached through the Symbol Game host.

`omega_prompt_civilization::pharmacy` (Rust) implements twelve failure classes.
This adapter sends a candidate to the host action `pharmacy_detect`
(`omega_engine_pfp.ffi.RustSymbolGameHost.pharmacy_detect`) and maps the
reply back to failure-class codes. Nothing is re-implemented here.

The native persona detector checks structured persona fields. `PharmacyMatcher`
also runs the separately attributed Python persona-text check.

A missing or failing host is a typed refusal (`NativePharmacyUnavailable`),
never a fallback to the Python pharmacy.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from omega_engine_epistemic_immune_system.domain.definitions_loader import (
    load_native_pharmacy,
)

from .definitions_store import read_definition
from .mssn_pharmacy import DetectionContext

_defs = load_native_pharmacy(read_definition("native_pharmacy.yaml"))

# serde variant name -> failure-class code, for the native classes.
NATIVE_CLASS_CODES: Mapping[str, str] = dict(_defs["native_class_codes"])
NATIVE_DISPOSITIONS: Mapping[str, str] = dict(_defs["native_dispositions"])

NATIVE_REFUSAL_CODES = frozenset(_defs["native_refusal_codes"])


class NativePharmacyUnavailable(RuntimeError):
    """The native pharmacy could not be reached or refused the request."""

    def __init__(self, code: str, detail: str) -> None:
        if code not in NATIVE_REFUSAL_CODES:
            raise ValueError(f"unknown native pharmacy refusal code: {code}")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True, slots=True)
class PharmacyFinding:
    """One finding: a failure-class code, where, and which implementation found it."""

    failure_class: str
    disposition: str
    locus: str
    detail: str
    source: str


@dataclass(frozen=True, slots=True)
class NativePharmacyReport:
    subject_digest: str
    semantic_payload_digest: str
    raw_bytes_digest: str | None
    detectors_run: tuple[str, ...]
    findings: tuple[PharmacyFinding, ...]


def native_context(context: DetectionContext) -> dict[str, Any]:
    """The Rust wire form of a DetectionContext.

    `granted_persona_roles` is a Python-only field (the native context refuses
    unknown fields); it is consumed by the Python persona check instead.
    """
    if type(context) is not DetectionContext:
        raise TypeError("context must be an exact DetectionContext")
    wire: dict[str, Any] = {
        "unexplored_branches": context.unexplored_branches,
        "seen_digests": list(context.seen_digests),
        "seen_semantic_digests": list(context.seen_semantic_digests),
        "semantic_replay_passed": context.semantic_replay_passed,
    }
    if context.prompt is not None:
        wire["prompt"] = context.prompt
    receipt = context.host_replay_receipt
    if receipt is not None:
        wire["host_replay_receipt"] = {
            "receipt_id": receipt.receipt_id,
            "host_signer": receipt.host_signer,
            "target_digest": receipt.target_digest,
            "replay_passed": receipt.replay_passed,
        }
    return wire


def _text(value: object, label: str) -> str:
    if type(value) is not str:
        raise NativePharmacyUnavailable("NATIVE_REPLY_MALFORMED", f"{label} is not a string")
    return value


def _digest(value: object, label: str) -> str:
    value = _text(value, label)
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise NativePharmacyUnavailable("NATIVE_REPLY_MALFORMED", f"invalid {label}")
    return value


def parse_native_report(result: object) -> NativePharmacyReport:
    """Map the host's report JSON to codes, refusing anything unexpected."""
    if type(result) is not dict:
        raise NativePharmacyUnavailable("NATIVE_REPLY_MALFORMED", "report is not an object")
    findings = []
    raw_findings = result.get("findings")
    if type(raw_findings) is not list:
        raise NativePharmacyUnavailable("NATIVE_REPLY_MALFORMED", "findings is not a list")
    for item in raw_findings:
        if type(item) is not dict:
            raise NativePharmacyUnavailable("NATIVE_REPLY_MALFORMED", "finding is not an object")
        variant = item.get("class")
        disposition = item.get("disposition")
        if (type(variant) is not str or type(disposition) is not str
                or variant not in NATIVE_CLASS_CODES or disposition not in NATIVE_DISPOSITIONS):
            raise NativePharmacyUnavailable(
                "NATIVE_REPLY_MALFORMED", f"unknown class or disposition {variant!r}/{disposition!r}"
            )
        findings.append(
            PharmacyFinding(
                failure_class=NATIVE_CLASS_CODES[variant],
                disposition=NATIVE_DISPOSITIONS[disposition],
                locus=_text(item.get("locus"), "locus"),
                detail=_text(item.get("detail"), "detail"),
                source="native",
            )
        )
    detectors = result.get("detectors_run")
    if type(detectors) is not list or any(type(code) is not str for code in detectors):
        raise NativePharmacyUnavailable("NATIVE_REPLY_MALFORMED", "detectors_run is not a list of str")
    if len(detectors) != len(set(detectors)) or set(detectors) != set(NATIVE_CLASS_CODES.values()):
        raise NativePharmacyUnavailable("NATIVE_REPLY_MALFORMED", "native detector inventory mismatch")
    raw_digest = result.get("raw_bytes_digest")
    if raw_digest is not None:
        raw_digest = _digest(raw_digest, "raw_bytes_digest")
    subject = _digest(result.get("subject_digest"), "subject_digest")
    if subject != _digest(result.get("normalized_json_digest"), "normalized_json_digest"):
        raise NativePharmacyUnavailable("NATIVE_REPLY_MALFORMED", "normalized subject binding mismatch")
    return NativePharmacyReport(
        subject_digest=subject,
        semantic_payload_digest=_digest(result.get("semantic_payload_digest"), "semantic_payload_digest"),
        raw_bytes_digest=raw_digest,
        detectors_run=tuple(detectors),
        findings=tuple(findings),
    )


class NativePharmacy:
    """`pharmacy_detect` through the Symbol Game host; the host is located lazily.

    Reports are memoised per (candidate text, wire context) for the lifetime of
    the instance: detection is deterministic, and the thymus screens every rule
    against the same self fixture.
    """

    def __init__(self, host: object | None = None) -> None:
        self._host = host
        self._cache: dict[tuple[str, str], NativePharmacyReport] = {}

    def _ensure_host(self) -> object:
        if self._host is None:
            from omega_engine_pfp.ffi import RustSymbolGameHost

            try:
                self._host = RustSymbolGameHost()
            except FileNotFoundError as exc:
                raise NativePharmacyUnavailable("HOST_BINARY_NOT_FOUND", str(exc)) from exc
        return self._host

    def detect(self, candidate_json: str, context: DetectionContext) -> NativePharmacyReport:
        if type(candidate_json) is not str:
            raise TypeError("candidate_json must be the exact candidate text")
        wire = native_context(context)
        key = (candidate_json, json.dumps(wire, sort_keys=True, ensure_ascii=True))
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        host = self._ensure_host()
        outcome = host.pharmacy_detect(candidate_json, context=wire)  # type: ignore[attr-defined]
        if not outcome.is_ok:
            raise NativePharmacyUnavailable("FFI_CROSSING_FAILED", str(outcome.unwrap_err()))
        record = outcome.unwrap()
        if type(record) is not dict or record.get("success") is not True:
            error = record.get("error") if type(record) is dict else record
            raise NativePharmacyUnavailable("NATIVE_PHARMACY_REFUSED", str(error))
        report = parse_native_report(record.get("result"))
        expected = "sha256:" + hashlib.sha256(candidate_json.encode("utf-8")).hexdigest()
        if report.raw_bytes_digest != expected:
            raise NativePharmacyUnavailable("NATIVE_REPLY_MALFORMED", "raw candidate binding mismatch")
        self._cache[key] = report
        return report


__all__ = [
    "NATIVE_CLASS_CODES",
    "NativePharmacy",
    "NativePharmacyReport",
    "NativePharmacyUnavailable",
    "PharmacyFinding",
    "native_context",
    "parse_native_report",
]
