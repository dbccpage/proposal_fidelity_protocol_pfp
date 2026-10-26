"""Inward-facing ports for native intelligence policies. AuthorityEffect: None."""

from __future__ import annotations

from typing import Any, Protocol

from omega_engine_operations.domain.rop.result import Refusal, Result


class MetabolismKernelPort(Protocol):
    def execute(self, payload: dict[str, Any]) -> Result[Any, Refusal]: ...
