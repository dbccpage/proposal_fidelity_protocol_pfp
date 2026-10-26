"""Bounded dependency-cycle analysis; caps are structural, not runtime guarantees.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

import networkx as nx


class DependencyAnalysisLimitError(RuntimeError):
    """Analysis refused; no complete cycle or functional report was established."""

    def __init__(self, name: str, observed: int, limit: int):
        self.reason = name.removeprefix("max_").upper() + "_LIMIT"
        self.observed = observed
        self.limit = limit
        super().__init__(f"{self.reason}: {observed} exceeds {limit}")


@dataclass(frozen=True, slots=True)
class CycleAnalysisLimits:
    """Positive integer caps; callers may lower, but cannot exceed policy defaults.

    Source lengths count Unicode characters, not allocated bytes. Search steps
    charge graph-copy adjacency visits, DFS adjacency visits and a structural
    nodes+edges allowance before each SCC decomposition. These counters do not
    measure every library/interpreter operation or impose wall-clock deadlines.
    """

    max_modules: int = 256
    max_module_chars: int = 256
    max_source_chars: int = 65_536
    max_total_source_chars: int = 1_048_576
    max_nodes: int = 512
    max_edges: int = 4096
    max_imports: int = 8192
    max_search_steps: int = 100_000
    max_cycles: int = 1024
    max_cycle_vertices: int = 65_536
    max_d0_cells: int = 262_144
    max_d1_cells: int = 1_048_576

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or not 1 <= value <= field.default:
                raise ValueError(f"{field.name} must be an integer in [1, {field.default}]")

    def check(self, name: str, observed: int) -> None:
        limit = getattr(self, name)
        if observed > limit:
            raise DependencyAnalysisLimitError(name, observed, limit)

    def admit_sources(self, sources: dict[str, str]) -> None:
        if type(sources) is not dict:
            raise TypeError("dependency sources must be a dict of strings")
        self.check("max_modules", len(sources))
        total = 0
        for module, source in sources.items():
            if type(module) is not str or type(source) is not str:
                raise TypeError("dependency module names and sources must be strings")
            self.check("max_module_chars", len(module))
            self.check("max_source_chars", len(source))
            total += len(source)
            self.check("max_total_source_chars", total)

    def admit_matrices(self, nodes: int, edges: int, cycles: int) -> None:
        self.check("max_d0_cells", nodes * edges)
        self.check("max_d1_cells", cycles * edges)


def _validated_limits(limits: CycleAnalysisLimits | None) -> CycleAnalysisLimits:
    """Take a fresh exact-type, constructor-validated policy snapshot."""
    if limits is None:
        return CycleAnalysisLimits()
    if type(limits) is not CycleAnalysisLimits:
        raise TypeError("limits must be a concrete CycleAnalysisLimits or None")
    return CycleAnalysisLimits(**{field.name: getattr(limits, field.name)
                                 for field in fields(CycleAnalysisLimits)})


@dataclass
class _SearchBudget:
    limits: CycleAnalysisLimits
    steps: int = 0
    vertices: int = 0

    def charge(self, amount: int = 1) -> None:
        self.limits.check("max_search_steps", self.steps + amount)
        self.steps += amount


def _cycles_through_root(graph, root, budget, cycles) -> None:
    """Iterative simple-path DFS, with a check before every adjacency visit."""
    path = [root]
    on_path = {root}
    stack = [iter(graph[root])]
    while stack:
        neighbor = next(stack[-1], None)
        if neighbor is None:
            stack.pop()
            on_path.remove(path.pop())
            continue
        budget.charge()
        if neighbor == root:
            budget.limits.check("max_cycles", len(cycles) + 1)
            budget.limits.check("max_cycle_vertices", budget.vertices + len(path))
            cycles.append(tuple(path))
            budget.vertices += len(path)
        elif neighbor not in on_path:
            path.append(neighbor)
            on_path.add(neighbor)
            stack.append(iter(graph[neighbor]))


def find_dependency_cycles(
    graph: nx.DiGraph, limits: CycleAnalysisLimits
) -> tuple[tuple[tuple[str, ...], ...], int]:
    """Complete directed cycles of length >=2, or an explicit refusal.

    Match NetworkX's directed SCC/root partition and adjacency order so cycle
    representatives retain their first-edge defect semantics. SCC decomposition
    is linear on structurally admitted graphs, and its calls are precharged.
    Never call the unbounded simple_cycles generator. Loops are ignored as in
    the existing defect/d1 consumers; parallel imports collapse in the DiGraph.
    """
    limits = _validated_limits(limits)
    limits.check("max_nodes", graph.number_of_nodes())
    limits.check("max_edges", graph.number_of_edges())
    budget = _SearchBudget(limits)
    reduced = nx.DiGraph()
    for node, adjacency in graph.adj.items():
        if type(node) is not str:
            raise TypeError("dependency graph nodes must be module-name strings")
        limits.check("max_module_chars", len(node))
        budget.charge()
        for neighbor in adjacency:
            budget.charge()
            if neighbor != node:
                reduced.add_edge(node, neighbor)

    def components_of(component_graph):
        budget.charge(component_graph.number_of_nodes() + component_graph.number_of_edges())
        return [c for c in nx.strongly_connected_components(component_graph) if len(c) >= 2]

    cycles: list[tuple[str, ...]] = []
    components = components_of(reduced)
    while components:
        component = components.pop()
        subgraph = reduced.subgraph(component)
        root = next(iter(component))
        _cycles_through_root(subgraph, root, budget, cycles)
        reduced.remove_node(root)
        components.extend(components_of(subgraph))
    return tuple(cycles), budget.steps
