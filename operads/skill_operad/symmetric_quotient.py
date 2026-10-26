"""symmetric_quotient.py

Declared symmetric normalization plus residual comparison candidates.
AuthorityEffect: None. Finite residual structure only.
"""

from __future__ import annotations

from itertools import permutations
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass, field
import json

from coloured_operad import ColouredOperad, Operation, Colour, CompositionKey
from quotient_operad import (
    QuotientFunctor,
    EvidenceLedger,
    ResidualEvidence,
    congruence_key,
)


# ---------------------------------------------------------------------------
# Symmetric orbit engine
# ---------------------------------------------------------------------------

def admissible_permutations(source: List[Colour]) -> List[Tuple[int, ...]]:
    """Return only those Ïƒ âˆˆ S_n that preserve colour equality."""
    n = len(source)
    admissible = []
    for Ïƒ in permutations(range(n)):
        if all(source[i] == source[Ïƒ[i]] for i in range(n)):
            admissible.append(Ïƒ)
    return admissible


class SymmetricOrbitEngine:
    """
    Materialises (or collapses) admissible S_n-orbits of operations.
    """

    def __init__(self, operad: ColouredOperad):
        self.operad = operad
        # op_id -> set of op_ids in its orbit (including itself)
        self.orbits: Dict[str, Set[str]] = {}
        # op_id -> canonical representative
        self.repr: Dict[str, str] = {}

    def generate_orbit(self, op_id: str) -> Set[str]:
        op = self.operad.operations.get(op_id)
        if op is None:
            return set()
        if op.arity <= 1 or not op.equivariant:
            self.orbits[op_id] = {op_id}
            self.repr[op_id] = op_id
            return {op_id}

        orbit = {op_id}
        for Ïƒ in admissible_permutations(op.source):
            if Ïƒ == tuple(range(op.arity)):
                continue
            new_id = self.operad.permute(op_id, Ïƒ)
            if new_id:
                orbit.add(new_id)
        # all members share the same representative (lowest id)
        canon = min(orbit)
        for m in orbit:
            self.orbits[m] = orbit
            self.repr[m] = canon
        return orbit

    def ensure_all_orbits(self) -> None:
        for op_id in list(self.operad.operations):
            if not op_id.startswith("id_"):
                self.generate_orbit(op_id)

    def canonical(self, op_id: str) -> str:
        return self.repr.get(op_id, op_id)


# ---------------------------------------------------------------------------
# Orbit-aware quotient functor
# ---------------------------------------------------------------------------

class SymmetricQuotientFunctor(QuotientFunctor):
    """
    Normalize permutations generated from one explicitly equivariant operation.

    Separate declared operations are never merged by scalar residual similarity.
    """

    def __init__(self, concrete: ColouredOperad, min_instances: int = 3):
        super().__init__(concrete, min_instances)
        self.orbit_engine = SymmetricOrbitEngine(concrete)
        self.orbit_engine.ensure_all_orbits()

    def _build_classes(self) -> None:
        """Preserve each declared orbit representative as its own operation."""
        self._classes.clear()
        self._candidate_classes.clear()
        self._repr.clear()

        # first collapse to orbit canonicals
        seen_canon: Set[str] = set()
        for op_id, op in self.concrete.operations.items():
            if op_id.startswith("id_"):
                continue
            canon = self.orbit_engine.canonical(op_id)
            if canon in seen_canon:
                continue
            seen_canon.add(canon)

            ledger = self.ledgers.get(canon) or self.ledgers.get(op_id)
            residual = (
                ledger.residual_class()
                if ledger is not None and ledger.is_stable(self.min_instances)
                else op.residual_effect
            )
            self._candidate_classes[congruence_key(op, residual)].append(canon)
            self._classes[("orbit", canon)].append(canon)
            for orbit_member in self.orbit_engine.orbits.get(canon, {canon}):
                self._repr[orbit_member] = canon

    def build_meta_operad(self, name: str = "MetaSkillOperad") -> ColouredOperad:
        self._build_classes()
        meta = ColouredOperad(name)
        for c in self.concrete.colours:
            meta.add_colour(c)

        for members in self._classes.values():
            cid = members[0]
            operation = self.concrete.operations[cid]
            meta.add_operation(
                op_id=cid,
                name=operation.name,
                source_colours=[colour.name for colour in operation.source],
                target_colour=operation.target.name,
                equivariant=operation.equivariant,
                residual_effect=operation.residual_effect,
            )

        # induce composition on meta representatives with explicit ROP refusal tracking
        for ck, result in self.concrete.composition.items():
            outer_m = self._repr.get(ck.outer, ck.outer)
            inner_m = self._repr.get(ck.inner, ck.inner)
            result_m = self._repr.get(result, result)
            if (
                outer_m in meta.operations
                and inner_m in meta.operations
                and result_m in meta.operations
            ):
                comp_res = meta.add_composition(outer_m, ck.slot, inner_m, result_m)
                if comp_res.is_failure:
                    # Refusal explicitly tracked in meta.refusals
                    pass

        meta.ensure_units()
        # Planar execution preserves input order; no automatic permutation expansion.
        self.meta = meta
        return meta


# ---------------------------------------------------------------------------
# Report helper
# ---------------------------------------------------------------------------

def orbit_report(engine: SymmetricOrbitEngine) -> dict:
    non_trivial = {
        k: sorted(v)
        for k, v in engine.orbits.items()
        if len(v) > 1 and k == min(v)   # print each orbit once
    }
    return {
        "non_trivial_orbits": non_trivial,
        "total_ops_with_orbits": len(engine.orbits),
        "authority_effect": "None",
    }
