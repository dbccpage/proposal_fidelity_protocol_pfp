"""Woland composition adapter for the existing Rust two-signal screening port.

Callers supply already checked candidate-bound observations. This adapter does
not issue admissions, authenticate observers, or manufacture host findings.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import asdict

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Err
from omega_engine_operads.application.ports.immune_screen_port import (
    DetectorIdentity,
    DetectorMatch,
    HostDangerObservation,
    ImmuneEvidenceRefusal,
    ImmuneVerdict,
)


class NativeImmuneScreen:
    def __init__(self, host: RustSymbolGameHost | None = None) -> None:
        self._host = host if host is not None else RustSymbolGameHost()

    def danger_verdict(
        self, matches: Sequence[DetectorMatch], danger: HostDangerObservation | None, *,
        detector: DetectorIdentity,
    ) -> ImmuneVerdict:
        payload = {
            "matches": [asdict(match) for match in tuple(matches)],
            "danger": None if danger is None else asdict(danger),
            "detector": {"detector_id": detector.detector_id,
                         "predicates": sorted(detector.predicates),
                         "offsets_are_content": detector.offsets_are_content},
        }
        reply = self._host.invoke_runtime("immune_screen", payload)
        if isinstance(reply, Err):
            raise ImmuneEvidenceRefusal(reply.error.code, reply.error.message)
        if not reply.value["success"]:
            raise ImmuneEvidenceRefusal("IMMUNE_NATIVE_UNAVAILABLE", str(reply.value["error"]))
        wire = reply.value["result"]
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
        domain = b"omega.native.port-input.v1"
        expected = hashlib.sha256(len(domain).to_bytes(4, "big") + domain
                                  + len(raw).to_bytes(8, "big") + raw).hexdigest()
        if wire.get("input_digest") != expected:
            raise ImmuneEvidenceRefusal("IMMUNE_INPUT_BINDING_MISMATCH", "native input changed")
        if wire.get("refusal") is not None:
            refusal = wire["refusal"]
            raise ImmuneEvidenceRefusal(refusal["code"], refusal["message"])
        return ImmuneVerdict(**wire["outcome"])
