"""Reply-control port implemented by the canonical OEOS native process seam."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from omega_engine_operations.domain.rop.result import Refusal, Result
from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost


class RustReplyControlAdapter:
    def __init__(self, host: RustSymbolGameHost | None = None) -> None:
        self._host = host if host is not None else RustSymbolGameHost()

    def invoke(self, payload: Mapping[str, Any]) -> Result[Mapping[str, Any], Refusal]:
        return self._host.invoke_runtime("reply_control", payload)
