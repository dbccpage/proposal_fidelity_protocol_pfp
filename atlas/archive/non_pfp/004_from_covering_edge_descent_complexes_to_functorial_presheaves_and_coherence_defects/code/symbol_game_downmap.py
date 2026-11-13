"""Finite MSS-N down-map model and declared cost-two distinction ledger.

The charge is 2 times the number of collapsed active protected records.
It is a model convention, not a derived norm of an independent curvature map.
The legacy induced_curvature_norm field stores the same charge. A separately
supplied measurement can be compared with that charge, but its truth and
mathematical interpretation require additional evidence.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from exact import exact_equal
from exactsym import Matrix
from covering_edge_poset import FinitePoset
from restriction_system import RestrictionSystem, RestrictionMap

GENESIS_COST_TWO_FLOOR: Fraction = Fraction(2, 1)


@dataclass(frozen=True)
class ProtectedDistinction:
    """An asserted pair of distinct symbolic entities that must not be collapsed."""
    item_a: str
    item_b: str
    rationale: str

    def key(self) -> Tuple[str, str]:
        a, b = sorted((self.item_a, self.item_b))
        return (a, b)


@dataclass(frozen=True)
class LossLedgerEntry:
    """A frozen ledger record; its legacy norm field is a declared charge."""
    stage_from: str
    stage_to: str
    collapsed_pairs: List[Tuple[str, str]]
    loss_count: int
    loss_cost_mu1: Fraction
    induced_curvature_norm: Fraction


class SymbolGameDownMap:
    """Manages retraction down-maps across the MSS-N tower stages."""

    def __init__(self, stages: List[str]) -> None:
        self.stages = list(stages)
        # Create linear tower poset: S0 < S1 < S2 ...
        relations = []
        for i in range(len(self.stages) - 1):
            relations.append((self.stages[i], self.stages[i + 1]))
        self.poset = FinitePoset(elements=self.stages, relations=relations)
        self.protected_distinctions: Set[ProtectedDistinction] = set()
        self.loss_ledger: List[LossLedgerEntry] = []

    def declare_protected_distinction(self, item_a: str, item_b: str, rationale: str) -> None:
        self.protected_distinctions.add(ProtectedDistinction(item_a, item_b, rationale))

    def evaluate_downmap_collapse(
        self,
        stage_from: str,
        stage_to: str,
        downmap_fn: Callable[[str], str],
        active_items: Sequence[str],
    ) -> LossLedgerEntry:
        """Evaluate whether downmap_fn collapses any protected distinctions."""
        collapsed = []
        for prot in self.protected_distinctions:
            if prot.item_a in active_items and prot.item_b in active_items:
                mapped_a = downmap_fn(prot.item_a)
                mapped_b = downmap_fn(prot.item_b)
                if mapped_a == mapped_b:
                    collapsed.append(prot.key())

        k = len(collapsed)
        cost = Fraction(k) * GENESIS_COST_TWO_FLOOR
        entry = LossLedgerEntry(
            stage_from=stage_from,
            stage_to=stage_to,
            collapsed_pairs=collapsed,
            loss_count=k,
            loss_cost_mu1=cost,
            induced_curvature_norm=cost,
        )
        self.loss_ledger.append(entry)
        return entry

    @classmethod
    def verify_antimorphic_curvature_lower_bound(
        cls,
        loss_entry: LossLedgerEntry,
        measured_curvature_l1: Fraction,
    ) -> Dict[str, Any]:
        """Compare a supplied measurement with the declared cost-two charge."""
        k = loss_entry.loss_count
        expected_floor = Fraction(k) * GENESIS_COST_TWO_FLOOR
        satisfied = measured_curvature_l1 >= expected_floor

        return {
            "satisfied": satisfied,
            "collapsed_count": k,
            "expected_floor": expected_floor,
            "measured_curvature": measured_curvature_l1,
            "duality_surplus": measured_curvature_l1 - expected_floor,
        }
