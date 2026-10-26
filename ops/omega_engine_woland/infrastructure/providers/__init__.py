"""Concrete provider gateways and wire adapters. AuthorityEffect: None."""

from omega_engine_woland.domain.providers.ports import configure_budget_runtime
from omega_engine_woland.infrastructure.providers.rust_budget import RustBudgetRuntime

# Compatibility composition: no process, filesystem, or network access on import.
configure_budget_runtime(RustBudgetRuntime())

from omega_engine_woland.infrastructure.providers.llm_gateway import (  # noqa: E402
    LlmGateway,
    LlmReply,
)

__all__ = ["LlmGateway", "LlmReply"]
