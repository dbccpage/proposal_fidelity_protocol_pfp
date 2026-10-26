"""Read port for the governance corpora. Writes go through the apply store."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ...domain.governance_digest.records import GovernanceCorpus


class GovernanceCorpusPort(ABC):
    @abstractmethod
    def load(self) -> GovernanceCorpus:
        """Read canon corpora once. Anti-pattern files are included only here."""
