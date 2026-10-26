"""Typed failures for Python quality policy loading and execution."""

from __future__ import annotations

from omega_engine_operads.domain.operad.errors import DomainError


class PythonQualityGateError(DomainError):
    """Base fail-closed error for the quality gate."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


class QualityPolicyLoadError(PythonQualityGateError):
    """The versioned policy could not be loaded or validated."""

    def __init__(self, detail: str) -> None:
        super().__init__("POLICY_LOAD_ERROR", detail)


class QualityInventoryExecutionError(PythonQualityGateError):
    """A required source or analyzer boundary failed."""

    def __init__(self, detail: str) -> None:
        super().__init__("INVENTORY_EXECUTION_ERROR", detail)
