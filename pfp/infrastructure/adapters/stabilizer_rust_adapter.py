"""Native stabilizer transport and complete outcome custody. AuthorityEffect: None."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from operations.domain.rop.result import Err
from operating_system.adapters.rust_host.ffi import (
    RustSymbolGameHost,
    locate_host_binary,
)
from pfp.domain.ports.stabilizer_port import StabilizerPort


class StabilizerRustAdapter(StabilizerPort):
    """Delegate through the canonical process seam; retain every native envelope."""

    def __init__(self, host: RustSymbolGameHost | None = None) -> None:
        self._host = host if host is not None else RustSymbolGameHost()
        self._native_outcomes: list[Mapping[str, Any]] = []

    @property
    def has_native_host(self) -> bool:
        return not isinstance(locate_host_binary(self._host._explicit, self._host.BINARY_NAME), Err)

    @property
    def native_outcomes(self) -> tuple[Mapping[str, Any], ...]:
        """Complete outcomes, including dispatch failures, before any extraction."""
        return tuple(deepcopy(self._native_outcomes))

    def _invoke(self, action: str, payload: Mapping[str, Any]) -> tuple[Any, str | None]:
        produced = self._host.invoke_runtime(action, payload)
        if isinstance(produced, Err):
            return None, produced.error.code
        outcome = produced.value
        self._native_outcomes.append(deepcopy(outcome))
        if outcome.get("success") is not True:
            return None, "NATIVE_DISPATCH_REFUSED"
        return outcome.get("result"), None

    def solve(self, case: Mapping[str, Any]) -> dict[str, Any]:
        result, refusal = self._invoke("stabilizer_solve", {"case": case})
        if refusal is not None or not isinstance(result, dict):
            return {
                "id": str(case.get("id") or case.get("case_id") or "unnamed"),
                "status": "UNKNOWN",
                "refusal_code": refusal or "NATIVE_RESULT_SHAPE_INVALID",
                "message": "Native stabilizer solve unavailable; no Python fallback",
            }
        return result

    def check(self, case: Mapping[str, Any], result: Any) -> dict[str, Any]:
        checked, refusal = self._invoke("stabilizer_check", {"case": case, "result": result})
        case_id = str(case.get("id") or case.get("case_id") or "unnamed")
        if refusal is not None or not isinstance(checked, dict):
            return {
                "verdict": "FAIL",
                "case_id": case_id,
                "refusal_code": refusal or "NATIVE_RESULT_SHAPE_INVALID",
                "error": "Native stabilizer checker unavailable; no Python fallback",
            }
        if set(checked) == {"Pass"} and isinstance(checked["Pass"], dict):
            return {
                "verdict": "PASS",
                "case_id": checked["Pass"].get("case_id", case_id),
                "details": checked["Pass"].get("details"),
            }
        if set(checked) == {"Fail"} and isinstance(checked["Fail"], dict):
            return {
                "verdict": "FAIL",
                "case_id": checked["Fail"].get("case_id", case_id),
                "error": checked["Fail"].get("reason", "Native certificate refused"),
            }
        return {
            "verdict": "FAIL",
            "case_id": case_id,
            "refusal_code": "NATIVE_RESULT_SHAPE_INVALID",
            "error": "Unrecognized native checker result",
        }
