"""CI/CD use cases and gate resolution orchestrators.

Exports stay lazy so callers pay only for the requested application service.
"""

from __future__ import annotations

from typing import Any

__all__ = (
    "build_gate_result",
    "build_local_ci_receipt",
    "evaluate_gate_results",
    "resolve_gate_invocation",
    "verify_local_ci_receipt",
)

_RESOLUTION = frozenset(
    {
        "build_gate_result",
        "build_local_ci_receipt",
        "evaluate_gate_results",
        "resolve_gate_invocation",
    }
)
_VERIFIER = frozenset({"verify_local_ci_receipt"})


def __getattr__(name: str) -> Any:
    if name in _RESOLUTION:
        from operations.use_cases.cicd.gate_resolution import (
            build_gate_result,
            build_local_ci_receipt,
            evaluate_gate_results,
            resolve_gate_invocation,
        )

        values = {
            "build_gate_result": build_gate_result,
            "build_local_ci_receipt": build_local_ci_receipt,
            "evaluate_gate_results": evaluate_gate_results,
            "resolve_gate_invocation": resolve_gate_invocation,
        }
        globals().update(values)
        return values[name]
    if name in _VERIFIER:
        from operations.use_cases.cicd.receipt_verifier import (
            verify_local_ci_receipt,
        )

        globals()["verify_local_ci_receipt"] = verify_local_ci_receipt
        return verify_local_ci_receipt
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
