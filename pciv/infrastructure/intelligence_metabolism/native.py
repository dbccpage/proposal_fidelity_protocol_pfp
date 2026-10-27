"""Canonical Rust host adapter for intelligence policies. AuthorityEffect: None."""

from __future__ import annotations

from typing import Any

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from operations.domain.rop.result import Err, Ok, Refusal, Result


class NativeMetabolismKernel:
    def __init__(self, host: RustSymbolGameHost | None = None) -> None:
        self.host = host or RustSymbolGameHost()

    def execute(self, payload: dict[str, Any]) -> Result[Any, Refusal]:
        response = self.host.invoke_runtime_with_file(
            "prompt_metabolism", payload, file_action="prompt_metabolism_file"
        )
        if isinstance(response, Err):
            return response
        envelope = response.value
        if not envelope["success"]:
            return Err(Refusal("METABOLISM_HOST_FAILED", str(envelope["error"])))
        result = envelope["result"]
        if result["refusal"] is not None:
            failure = result["refusal"]
            return Err(Refusal(failure["code"], failure["message"]))
        return Ok(result["outcome"])
