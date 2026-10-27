"""Inbound domain ports for MSSN grammar persistence."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pfp.domain.mssn_research.shared_kernel.result import Result

from .entities import EpistemicQuarantineLedger
from .errors import GrammarDomainError

LocationT = TypeVar("LocationT", covariant=True)


@runtime_checkable
class EpistemicQuarantineLedgerRepository(Protocol[LocationT]):
    """Persistence capability required by ledger application services."""

    def save(
        self,
        ledger: EpistemicQuarantineLedger,
    ) -> Result[LocationT, GrammarDomainError]: ...

    def load(
        self,
        ledger_id: str,
    ) -> Result[EpistemicQuarantineLedger, GrammarDomainError]: ...
