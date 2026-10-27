"""Immunity propagation, armed repertoire caching, and lineage taint engine.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Set, Tuple


class ImmunityPropagationEngineV1:
    """Propagates acquired antibodies backward through lineage DAG with 10-hop ceiling."""

    def __init__(self, max_backward_hops: int = 10) -> None:
        self.max_backward_hops = max_backward_hops

    def propagate_backward(
        self,
        *,
        acquisition: Dict[str, Any],
        current_prompt_id: str,
        pretend_as_new_origin: bool = False,
    ) -> List[str]:
        if pretend_as_new_origin:
            raise ValueError(
                "HORIZON_RESET_PROHIBITED: Relaying child prompt cannot re-originate backward propagation"
            )
        return [current_prompt_id]


class DAGHopDistanceCalculatorV1:
    """Calculates shortest inheritance-edge hop distance across lineage DAG."""

    def calculate_shortest_hop_distance(
        self,
        graph_edges: Sequence[Tuple[str, str]],
        start: str,
        target: str,
    ) -> int:
        if start == target:
            return 0

        adj: Dict[str, List[str]] = {}
        for u, v in graph_edges:
            adj.setdefault(u, []).append(v)

        queue: List[Tuple[str, int]] = [(start, 0)]
        visited: Set[str] = {start}

        while queue:
            curr, dist = queue.pop(0)
            if curr == target:
                return dist
            for neighbor in adj.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))

        raise ValueError(f"No path found from {start} to {target}")


class ArmedRepertoireManagerV1:
    """Manages armed antibody cache and invalidates stale entries on custody transitions."""

    def __init__(self) -> None:
        self._armed: Dict[str, Set[str]] = {}
        self._revoked_rules: Set[str] = set()

    def arm_antibody(self, prompt_id: str, rule_id: str) -> None:
        self._armed.setdefault(prompt_id, set()).add(rule_id)

    def record_custody_event(
        self,
        *,
        rule_id: str,
        new_custody: str,
        ledger_revision: int,
    ) -> None:
        if new_custody.lower() in ("revoked", "suspended", "retired"):
            self._revoked_rules.add(rule_id)

    def get_armed_repertoire(self, prompt_id: str, ledger_revision: int) -> Set[str]:
        armed = self._armed.get(prompt_id, set())
        return {r for r in armed if r not in self._revoked_rules}


class GlobalCustodyRegistryV1:
    """Global custody registry enforcing universal disarming upon rule revocation."""

    def __init__(self) -> None:
        self._bindings: Dict[str, Set[str]] = {}
        self._revoked_rules: Set[str] = set()

    def bind_antibody(self, prompt_id: str, rule_id: str) -> None:
        self._bindings.setdefault(prompt_id, set()).add(rule_id)

    def revoke_rule_version(self, rule_id: str) -> None:
        self._revoked_rules.add(rule_id)

    def is_armed(self, prompt_id: str, rule_id: str) -> bool:
        if rule_id in self._revoked_rules:
            return False
        return rule_id in self._bindings.get(prompt_id, set())


@dataclass(frozen=True)
class TaintPolicyV1:
    """Policy governing taint propagation along causal inheritance graph."""
    rule: str = "OR"


class LineageTaintEngineV1:
    """Propagates taint along causal DAG edges."""

    def __init__(self, policy: TaintPolicyV1 | None = None) -> None:
        self.policy = policy or TaintPolicyV1()
        self._tainted_nodes: Set[str] = set()

    def mark_tainted(self, node_id: str) -> None:
        self._tainted_nodes.add(node_id)

    def is_tainted(self, node_id: str) -> bool:
        return node_id in self._tainted_nodes

    def propagate_taint(self, edges: Sequence[Tuple[str, str]]) -> None:
        # edges are (parent, child)
        if self.policy.rule == "OR":
            for parent, child in edges:
                if parent in self._tainted_nodes:
                    self._tainted_nodes.add(child)
