"""Command DTOs for OEWAS V3 Application Handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ...domain.value_objects.identifier import (
    CausationId,
    CorrelationId,
    EstateRef,
    IdempotencyKey,
)


@dataclass(frozen=True, slots=True)
class CompileCatalogCommand:
    estate_ref: EstateRef
    correlation_id: CorrelationId
    causation_id: CausationId
    idempotency_key: Optional[IdempotencyKey] = None
    expected_version: Optional[int] = None
    # An estate with no skill documents is refused unless the caller says, in
    # the command, that an empty epoch is what it wants.
    allow_empty_estate: bool = False

    def __post_init__(self) -> None:
        if type(self.allow_empty_estate) is not bool:
            raise TypeError(
                "allow_empty_estate must be an exact bool, got "
                f"{type(self.allow_empty_estate).__name__}"
            )


@dataclass(frozen=True, slots=True)
class VerifyCatalogCommand:
    catalog_id: str
    correlation_id: CorrelationId
    causation_id: CausationId


@dataclass(frozen=True, slots=True)
class CompileProjectionCommand:
    catalog_id: str
    target_format: str
    correlation_id: CorrelationId
    causation_id: CausationId


@dataclass(frozen=True, slots=True)
class CompileLicensedTermCommand:
    agent_id: str
    term_expr: str
    correlation_id: CorrelationId
    causation_id: CausationId
