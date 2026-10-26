"""Provider budget boundary; concrete native binding is composed outside domain."""

from typing import Any, Protocol

from omega_engine_woland.domain.providers.types import ProviderConfigError


class BudgetRuntime(Protocol):
    def invoke(self, operation: str, **payload: object) -> Any: ...
    def utc_now(self) -> str: ...


_runtime: BudgetRuntime | None = None


def configure_budget_runtime(runtime: BudgetRuntime) -> None:
    global _runtime
    _runtime = runtime


def budget_runtime() -> BudgetRuntime:
    if _runtime is None:
        raise ProviderConfigError("NATIVE_BUDGET_UNAVAILABLE: inject a budget runtime")
    return _runtime
