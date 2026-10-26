"""Supervised Python transport for the native intelligence lifecycle kernel.

AuthorityEffect: None. Python moves DTOs and keeps filesystem custody; Rust
owns state-transition, transfer, certificate, and retention decisions.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Err


class NativeLifecycleError(RuntimeError):
    """The host seam or native lifecycle port could not produce a decision."""


class NativeIntelligenceLifecycle:
    """Adapter for the ``intelligence_lifecycle`` runtime action."""

    def __init__(self, host: RustSymbolGameHost | None = None) -> None:
        self._host = host or RustSymbolGameHost()

    def _call(self, operation: str, request: Mapping[str, Any]) -> Mapping[str, Any]:
        response = self._host.invoke_runtime_with_file(
            "intelligence_lifecycle",
            {"operation": operation, **dict(request)},
            file_action="intelligence_lifecycle_file",
        )
        if isinstance(response, Err):
            refusal = response.error
            raise NativeLifecycleError(f"{refusal.code}: {refusal.message}")
        envelope = response.value
        if not envelope["success"]:
            raise NativeLifecycleError(str(envelope["error"]))
        wire = envelope["result"]
        refusal = wire.get("refusal") if isinstance(wire, Mapping) else None
        if refusal is not None:
            code = refusal.get("code", "INTELLIGENCE_NATIVE_REFUSAL")
            message = refusal.get("message", "native lifecycle refused the request")
            raise NativeLifecycleError(f"{code}: {message}")
        outcome = wire.get("outcome") if isinstance(wire, Mapping) else None
        if not isinstance(outcome, Mapping):
            raise NativeLifecycleError(
                "INTELLIGENCE_NATIVE_OUTPUT_INVALID: outcome must be an object"
            )
        return outcome

    def seal_manifest(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._call("seal_manifest", request)

    def evaluate_lifecycle(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._call("evaluate_lifecycle", request)

    def evaluate_retention(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._call("evaluate_retention", request)
