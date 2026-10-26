"""Domain protocols for Asymmetric LGGR & AST Cochain Analysis (Prompt 11).

AuthorityEffect: None.
Clean Architecture: Domain port protocols (@runtime_checkable).
"""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence, runtime_checkable

from ..ast_cochain.models import AstCochainReceipt, DependencyEdge


@runtime_checkable
class IAstDependencyParser(Protocol):
    """Protocol for parsing codebase AST into a simplicial 1-complex of dependency edges."""

    def parse_dependency_complex(self, root_dir: str) -> Sequence[DependencyEdge]:
        """Parses Python source tree and returns directed dependency edges between modules."""
        ...


@runtime_checkable
class ILggrArbiter(Protocol):
    """Protocol for arbitrating local green vs global red cochain contract boundaries."""

    def arbitrate(
        self,
        local_test_outcomes: Mapping[str, bool],
        edges: Sequence[DependencyEdge],
    ) -> AstCochainReceipt:
        """Arbitrates whether local test passes are globally admissible or refused due to cochain defects."""
        ...
