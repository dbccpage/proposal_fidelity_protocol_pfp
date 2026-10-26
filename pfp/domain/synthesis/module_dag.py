"""Module DAG for program synthesis decomposition (U10).

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ModuleStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    SYNTHESIZING = "synthesizing"
    FROZEN = "frozen"
    FAILED = "failed"


@dataclass
class ModuleNode:
    name: str
    dependencies: list[str] = field(default_factory=list)
    status: ModuleStatus = ModuleStatus.PENDING
    code: str | None = None
    attempts: int = 0
    authority_effect: str = "None"


@dataclass
class ModuleDag:
    nodes: dict[str, ModuleNode] = field(default_factory=dict)
    authority_effect: str = "None"

    def add_module(self, name: str, dependencies: list[str] | None = None) -> None:
        deps = dependencies or []
        self.nodes[name] = ModuleNode(name=name, dependencies=deps)

    def next_schedulable_module(self) -> ModuleNode | None:
        """Finds next module whose dependencies are all FROZEN."""
        frozen_names = {
            name for name, node in self.nodes.items() if node.status == ModuleStatus.FROZEN
        }
        for node in self.nodes.values():
            if node.status == ModuleStatus.PENDING:
                if all(dep in frozen_names for dep in node.dependencies):
                    node.status = ModuleStatus.READY
                    return node
        return None

    def freeze_module(self, name: str, code: str) -> None:
        if name not in self.nodes:
            raise KeyError(f"Module {name} not found in DAG")
        node = self.nodes[name]
        node.status = ModuleStatus.FROZEN
        node.code = code

    def fail_module(self, name: str) -> None:
        if name not in self.nodes:
            raise KeyError(f"Module {name} not found in DAG")
        self.nodes[name].status = ModuleStatus.FAILED

    def is_all_frozen(self) -> bool:
        return bool(self.nodes) and all(
            node.status == ModuleStatus.FROZEN for node in self.nodes.values()
        )
