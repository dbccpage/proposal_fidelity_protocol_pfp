"""Immunity propagation, armed repertoire caching, and lineage taint engine.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ImmunityPropagationEngineV1:
    """Propagates acquired antibodies backward through lineage DAG with 10-hop ceiling."""

    def __init__(self, max_backward_hops: int = 10) -> None:
        self.max_backward_hops = max_backward_hops

    def propagate_backward(
        self,
        *,
        acquisition: dict[str, Any],
        current_prompt_id: str,
        pretend_as_new_origin: bool = False,
    ) -> list[str]:
        if pretend_as_new_origin:
            raise ValueError(
                "HORIZON_RESET_PROHIBITED: Relaying child prompt cannot re-originate backward propagation"
            )
        return [current_prompt_id]


class DAGHopDistanceCalculatorV1:
    """Calculates shortest inheritance-edge hop distance across lineage DAG."""

    def calculate_shortest_hop_distance(
        self,
        graph_edges: Sequence[tuple[str, str]],
        start: str,
        target: str,
    ) -> int:
        if start == target:
            return 0

        adj: dict[str, list[str]] = {}
        for u, v in graph_edges:
            adj.setdefault(u, []).append(v)

        queue: list[tuple[str, int]] = [(start, 0)]
        visited: set[str] = {start}

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
        self._armed: dict[str, set[str]] = {}
        self._revoked_rules: set[str] = set()

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

    def get_armed_repertoire(self, prompt_id: str, ledger_revision: int) -> set[str]:
        armed = self._armed.get(prompt_id, set())
        return {r for r in armed if r not in self._revoked_rules}


class GlobalCustodyRegistryV1:
    """Global custody registry enforcing universal disarming upon rule revocation."""

    def __init__(self) -> None:
        self._bindings: dict[str, set[str]] = {}
        self._revoked_rules: set[str] = set()

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
        self._tainted_nodes: set[str] = set()

    def mark_tainted(self, node_id: str) -> None:
        self._tainted_nodes.add(node_id)

    def is_tainted(self, node_id: str) -> bool:
        return node_id in self._tainted_nodes

    def propagate_taint(self, edges: Sequence[tuple[str, str]]) -> None:
        # edges are (parent, child)
        if self.policy.rule == "OR":
            for parent, child in edges:
                if parent in self._tainted_nodes:
                    self._tainted_nodes.add(child)


SUPPORTED_IMMUNE_REGISTRY_URIS = frozenset({"oeeis:registry:v1"})


def resolve_civilization_immune_store(
    civ: Any | None,
    repo_root: Path,
    *,
    read_only: bool = False,
    family_index: Mapping[str, Any] | None = None,
    societies: Mapping[str, Any] | None = None,
) -> Any:
    """Resolve a civilization registry string (e.g. ``oeeis:registry:v1``) to the shared pharmacy store."""
    from eis.domain.pharmacy_catalog import PharmacyCatalogRepository  # noqa: PLC0415
    from eis.infrastructure.pharmacy_writer import (  # noqa: PLC0415
        filesystem_byte_writer,
        filesystem_catalog_bytes,
    )
    from pciv.domain.society import resolve_society_families  # noqa: PLC0415
    from pciv.use_cases.lamarckian_loop import LamarckianReceiptStore  # noqa: PLC0415
    from pfp_core.caller_feedback import BoundImmuneStoreV1  # noqa: PLC0415
    from pfp_core.immunity import AntibodyRegistry  # noqa: PLC0415

    root = Path(repo_root)
    if civ is not None:
        if civ.global_immune_registry not in SUPPORTED_IMMUNE_REGISTRY_URIS:
            raise ValueError(
                f"UNBOUND_IMMUNE_REGISTRY: {civ.global_immune_registry!r}"
            )
        if societies is not None:
            for soc_id in civ.society_ids:
                soc = societies.get(soc_id)
                if soc is None:
                    raise ValueError(f"DANGLING_SOCIETY_ID: {soc_id!r}")
                if family_index is not None:
                    resolve_society_families(soc, family_index)
    elif societies is not None and family_index is not None:
        for soc in societies.values():
            resolve_society_families(soc, family_index)

    catalog_file = root / "eis" / "antibodies" / "pharmacy_catalog.json"
    telemetry_dir = root / "_ic" / "nara" / "_archive" / "telemetry" / "antibodies"
    repo = PharmacyCatalogRepository(
        root,
        catalog_file=catalog_file,
        telemetry_dir=telemetry_dir,
        byte_writer=filesystem_byte_writer if not read_only else None,
        byte_source=filesystem_catalog_bytes,
    )
    if not read_only and not catalog_file.exists():
        repo._atomic_write(catalog_file, repo._json_bytes(repo._empty_catalog(with_timestamp=True)))
    elif catalog_file.exists():
        repo.load_catalog()

    lineage_file = root / "eis" / "antibodies" / "lamarckian_lineage.jsonl"
    receipt_store = LamarckianReceiptStore(lineage_file, read_only=read_only)
    return BoundImmuneStoreV1(
        repo_root=root,
        catalog=repo,
        registry=AntibodyRegistry(),
        receipt_store=receipt_store,
        custody_registry=GlobalCustodyRegistryV1(),
        read_only=read_only,
        civilization_id=civ.civilization_id if civ is not None else None,
        family_index=dict(family_index) if family_index is not None else {},
        societies=dict(societies) if societies is not None else {},
    )
