"""Named live host for source-bound finite WDP packets. AuthorityEffect: None."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from operations.domain.rop.result import Err, Refusal, Result

from .ffi import RustSymbolGameHost
from .source_packet_requests import packet_verify_payload


@dataclass(frozen=True)
class SourcePacketHost:
    """Keep the native outcome intact, including mathematical refusals."""

    host: RustSymbolGameHost = field(default_factory=RustSymbolGameHost)

    def evaluate(self, request: Mapping[str, Any]) -> Result[Mapping[str, Any], Refusal]:
        return self.host.invoke_runtime("wdp_packet_evaluate", request)

    def replay(
        self, request: Mapping[str, Any], result: Mapping[str, Any]
    ) -> Result[Mapping[str, Any], Refusal]:
        payload = packet_verify_payload(request, result)
        if isinstance(payload, Err):
            return payload
        return self.host.invoke_runtime("wdp_packet_verify", payload.value)
