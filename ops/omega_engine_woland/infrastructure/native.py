"""Real Woland support composition over the established OS host.

Each invocation acquires one host, preserving the old per-operation default.
AuthorityEffect: None.
"""
from __future__ import annotations

from typing import Any, Mapping

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Refusal, Result
from omega_engine_woland.domain import native as domain_native


class DefaultNativeOperationPort:
    """Acquire the concrete host at the outer process boundary, per invocation."""

    def invoke_runtime_with_file(
        self, action: str, payload: Any, *, file_action: str
    ) -> Result[Mapping[str, Any], Refusal]:
        return RustSymbolGameHost().invoke_runtime_with_file(action, payload, file_action=file_action)


def invoke(operation: str, **payload: Any) -> Result[Any, Refusal]:
    return domain_native.invoke(DefaultNativeOperationPort(), operation, **payload)


def value(operation: str, **payload: Any) -> Any:
    return domain_native.value(DefaultNativeOperationPort(), operation, **payload)
