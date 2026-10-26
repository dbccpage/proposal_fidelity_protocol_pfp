"""Thin transport for the native PFP immune-fence renderer."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Err


class ImmuneFenceRefusal(ValueError):
    """A typed renderer refusal, including an unavailable native host."""

    def __init__(self, message: str):
        self.code = message.partition(":")[0]
        super().__init__(message)


class NativeImmuneFenceRenderer:
    def __init__(self, host: RustSymbolGameHost | None = None):
        self._host = host if host is not None else RustSymbolGameHost()

    def render(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        reply = self._host.invoke_runtime("immune_fence_render", dict(payload))
        if isinstance(reply, Err):
            raise ImmuneFenceRefusal(f"{reply.error.code}: {reply.error.message}")
        if not reply.value["success"]:
            raise ImmuneFenceRefusal(str(reply.value["error"]))
        result = reply.value["result"]
        raw = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode("utf-8")
        if not isinstance(result, dict) or result.get("request_digest") != hashlib.sha256(raw).hexdigest():
            raise ImmuneFenceRefusal("IMMUNE_FENCE_INPUT_BINDING_MISMATCH")
        return result
