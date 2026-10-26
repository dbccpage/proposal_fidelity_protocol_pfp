"""Scoring transport through the canonical OEOS seam. AuthorityEffect: None."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...domain.ports.scoring_port import NativeScoringRefusal
from ...ffi import RustSymbolGameHost, get_default_host


class RustScoringAdapter:
    def __init__(self, host: RustSymbolGameHost | None = None) -> None:
        self._host = host
        self.last_outcome: Mapping[str, Any] | None = None

    def invoke_scoring(self, action: str, payload: Mapping[str, Any]) -> Any:
        try:
            host = self._host or get_default_host()
        except FileNotFoundError as exc:
            raise NativeScoringRefusal("HOST_BINARY_NOT_FOUND", str(exc)) from exc
        result = host.invoke_runtime(action, dict(payload))
        if result.is_err:
            refusal = result.unwrap_err()
            raise NativeScoringRefusal(refusal.code, refusal.message)
        outcome = result.unwrap()
        self.last_outcome = outcome
        if (
            not isinstance(outcome, Mapping)
            or outcome.get("action") != action
            or type(outcome.get("success")) is not bool
        ):
            raise NativeScoringRefusal(
                "NATIVE_SCORING_RESULT_INVALID", "native outcome shape/action mismatch"
            )
        if outcome["success"] is not True:
            raise NativeScoringRefusal("NATIVE_SCORING_REFUSED", str(outcome.get("error")))
        return outcome.get("result")
