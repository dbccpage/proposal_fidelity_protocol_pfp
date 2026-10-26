"""Genealogy and causal lineage graph for prompt genomes.

Enforces:
- F-LINEAGE-01: Edges exist only for witnessed causal relations; matching objectives alone never creates an edge.
- Inheritance DAG is strictly acyclic; cycles are refused before edge insertion.
- Witness receipts must be verified; unverified receipts are refused.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import threading
from typing import Any, Dict, List, Optional, Set

from omega_engine_prompt_civilization.domain.causal_witness import SealedCausalWitness


class RelationshipType(str, Enum):
    """Permitted relationship types between prompts in lineage graph."""
    DIRECT_MUTATION = "DirectMutation"
    REPAIR = "Repair"
    RETRY = "Retry"
    RETRIEVED_PRECEDENT = "RetrievedPrecedent"


INHERITANCE_RELATIONSHIPS = frozenset({
    RelationshipType.DIRECT_MUTATION,
    RelationshipType.REPAIR,
    RelationshipType.RETRY,
    "DirectMutation",
    "Repair",
    "Retry",
})


def _seal_names_edge(witness: SealedCausalWitness, parent_id: str, child_id: str) -> bool:
    try:
        body = json.loads(witness.canonical_body)
    except json.JSONDecodeError:
        return False
    if not isinstance(body, dict):
        return False
    return body.get("parent_id") == parent_id and body.get("child_id") == child_id


@dataclass(frozen=True)
class LineageEdgeV1:
    """Directed edge in the lineage graph."""
    parent_id: str
    child_id: str
    relationship: RelationshipType | str
    witness_receipt: Optional[Dict[str, Any]] = None


class LineageGraphV1:
    """Durable lineage graph tracking causal inheritance edges and reference precedents."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._edges: List[LineageEdgeV1] = []
        self._adj_inheritance: Dict[str, Set[str]] = {}
        self._nodes: Dict[str, None] = {}

    @property
    def nodes(self) -> List[str]:
        with self._lock:
            return list(self._nodes.keys())

    @property
    def edges(self) -> List[LineageEdgeV1]:
        with self._lock:
            return list(self._edges)

    def add_node(self, node_id: str) -> None:
        with self._lock:
            self._nodes[node_id] = None

    def add_genome(self, genome_id: str) -> None:
        self.add_node(genome_id)

    def has_path(self, from_id: str, to_id: str) -> bool:
        if from_id == to_id:
            return True
        visited = set()
        queue = [from_id]
        visited.add(from_id)

        while queue:
            curr = queue.pop(0)
            if curr == to_id:
                return True
            for child in self._adj_inheritance.get(curr, set()):
                if child not in visited:
                    visited.add(child)
                    queue.append(child)
        return False

    def add_edge(
        self,
        parent_id: str,
        child_id: str,
        relationship: RelationshipType | str,
        witness_receipt: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            rel_val = relationship.value if isinstance(relationship, RelationshipType) else str(relationship)

            # Objective match or non-causal relationship is refused
            if rel_val not in [r.value for r in RelationshipType]:
                raise ValueError(f"CAUSAL_WITNESS_REQUIRED: relationship {rel_val!r} is not an authorized causal relation")

            # Inheritance edges require a verified witness receipt
            if rel_val in INHERITANCE_RELATIONSHIPS:
                if not isinstance(witness_receipt, SealedCausalWitness):
                    raise ValueError(
                        "CAUSAL_WITNESS_REQUIRED: a caller dict is not a causal witness"
                    )
                if not _seal_names_edge(witness_receipt, parent_id, child_id):
                    raise ValueError(
                        "CAUSAL_WITNESS_REQUIRED: witness seal does not name this parent and child"
                    )

                # Enforce acyclicity on inheritance DAG
                if self.has_path(child_id, parent_id):
                    raise ValueError(
                        f"LINEAGE_CYCLE_REFUSED: Cycle detected in inheritance DAG between {parent_id} and {child_id}"
                    )

            edge = LineageEdgeV1(
                parent_id=parent_id,
                child_id=child_id,
                relationship=relationship,
                witness_receipt=witness_receipt,
            )
            self._edges.append(edge)
            self._nodes[parent_id] = None
            self._nodes[child_id] = None

            if rel_val in INHERITANCE_RELATIONSHIPS:
                self._adj_inheritance.setdefault(parent_id, set()).add(child_id)

    def has_inheritance_edge(self, parent_id: str, child_id: str) -> bool:
        return child_id in self._adj_inheritance.get(parent_id, set())

    def derive_descent_path(self, parent_id: str, child_id: str) -> List[str]:
        """Finds path from parent to child following inheritance edges only."""
        if parent_id == child_id:
            return [parent_id]

        queue = [(parent_id, [parent_id])]
        visited = {parent_id}

        while queue:
            curr, path = queue.pop(0)
            if curr == child_id:
                return path
            for neighbor in self._adj_inheritance.get(curr, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        raise ValueError(
            f"DESCENT_REQUIRES_INHERITANCE_EDGE: No witnessed inheritance path exists between {parent_id} and {child_id}"
        )


__all__ = ["INHERITANCE_RELATIONSHIPS", "LineageEdgeV1", "LineageGraphV1", "RelationshipType"]
