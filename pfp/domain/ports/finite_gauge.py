"""Inward finite-gauge checker port.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Protocol

from pfp.domain.finite_gauge import (
    CheckerIdentity,
    GaugeRefusal,
    GraphSpec,
    SearchReceipt,
)
from pfp.domain.kernel.result import Result


class FiniteGaugeCheckerPort(Protocol):
    """Exact checker boundary consumed by the finite-gauge use case."""

    def identity(self) -> Result[CheckerIdentity, GaugeRefusal]: ...

    def graph_digest(self, graph: GraphSpec) -> Result[str, GaugeRefusal]: ...

    def verify_candidate(
        self, graph: GraphSpec, bits: tuple[int, ...]
    ) -> Result[bool, GaugeRefusal]: ...

    def search_and_replay(
        self, graph: GraphSpec, node_budget: int
    ) -> Result[SearchReceipt, GaugeRefusal]: ...


__all__ = ["FiniteGaugeCheckerPort"]
