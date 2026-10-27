"""Concrete provider gateways and wire adapters. AuthorityEffect: None."""

from adversary.domain.providers.ports import configure_budget_runtime
from adversary.infrastructure.providers.rust_budget import RustBudgetRuntime

# Compatibility composition: no process, filesystem, or network access on import.
configure_budget_runtime(RustBudgetRuntime())

from adversary.infrastructure.providers.llm_gateway import (  # noqa: E402
    LlmGateway,
    LlmReply,
)

__all__ = ["LlmGateway", "LlmReply"]
