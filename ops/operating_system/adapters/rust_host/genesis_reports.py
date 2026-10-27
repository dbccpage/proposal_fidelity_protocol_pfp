"""Transport for the native admission-report profile. AuthorityEffect: None."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from operations.domain.rop.result import Refusal, Result

from .ffi import RustSymbolGameHost


def source_bundle(model: bytes, observe: bytes) -> bytes:
    """Frame both preserved sources exactly as the compiled native pin does."""
    if type(model) is not bytes or type(observe) is not bytes:
        raise TypeError("original source bytes required")
    return b"core.genesis.source-bundle.v1\0" + b"".join(
        len(raw).to_bytes(8, "big") + raw for raw in (model, observe)
    )


@dataclass(frozen=True)
class GenesisReportHost:
    host: RustSymbolGameHost = field(default_factory=RustSymbolGameHost)

    def evaluate(self, request: Mapping[str, Any]) -> Result[Mapping[str, Any], Refusal]:
        return self.host.invoke_runtime("genesis_report_evaluate", request)

    def replay(
        self, request: Mapping[str, Any], candidate: Mapping[str, Any]
    ) -> Result[Mapping[str, Any], Refusal]:
        return self.host.invoke_runtime(
            "genesis_report_verify", {"request": request, "result": candidate}
        )
