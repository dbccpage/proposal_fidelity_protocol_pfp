"""
dependency_complex.py
=====================

1-Skeleton Dependency Simplicial Complex builder and defect detector.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import networkx as nx

from .cycle_analysis import CycleAnalysisLimits, _validated_limits, find_dependency_cycles
from .models import ASTDefect
from .source_parser import ASTSourceParser

DEFAULT_CLEAN_ARCH_LAYERS: Dict[str, int] = {
    "domain": 0,
    "use_cases": 1,
    "application": 1,
    "infrastructure": 2,
    "controllers": 3,
    "frontend": 4,
    "entrypoints": 4,
}


class DependencyCycleDetectionError(RuntimeError):
    """Cycle enumeration failed and must not be reported as a cycle-free complex."""


class ASTDependencyComplex:
    """Constructs the 1-skeleton complex of module vertices and directed dependency edges."""

    def __init__(
        self, layer_rules: Optional[Dict[str, int]] = None, *, limits: CycleAnalysisLimits | None = None
    ):
        self.layer_rules = layer_rules or DEFAULT_CLEAN_ARCH_LAYERS
        self.limits = _validated_limits(limits)
        self.graph = nx.DiGraph()
        self.defects: List[ASTDefect] = []
        self.cycles: tuple[tuple[str, ...], ...] = ()
        self.search_steps = 0

    def _reset(self) -> None:
        self.graph.clear()
        self.defects.clear()
        self.cycles = ()
        self.search_steps = 0

    def build_complex(self, sources: Dict[str, str]) -> None:
        self._reset()
        try:
            self.limits = _validated_limits(self.limits)
            self.limits.admit_sources(sources)
            self._populate(sources)
            self._check_cycles()
        except BaseException:
            self._reset()
            raise

    def _populate(self, sources: Dict[str, str]) -> None:
        known_modules = list(sources)
        for mod_name in sources.keys():
            self.limits.check("max_nodes", self.graph.number_of_nodes() + 1)
            self.graph.add_node(mod_name, layer=self._get_layer(mod_name))

        import_count = 0
        for mod_name, src_code in sources.items():
            tree = ASTSourceParser.parse_module(src_code)
            if tree is None:
                self.defects.append(
                    ASTDefect(
                        defect_type="syntax_error",
                        source_module=mod_name,
                        target_module=None,
                        description=f"SyntaxError in module {mod_name}",
                        weight=5.0,
                    )
                )
                continue

            imports = ASTSourceParser.extract_imports(tree)
            import_count += len(imports)
            self.limits.check("max_imports", import_count)
            for imp_mod, _ in imports:
                target = self._resolve_target(imp_mod, known_modules) or imp_mod
                if target and target != mod_name:
                    self._add_import_edge(mod_name, target)

    def _add_import_edge(self, source: str, target: str) -> None:
        if not self.graph.has_node(target):
            self.limits.check("max_module_chars", len(target))
            self.limits.check("max_nodes", self.graph.number_of_nodes() + 1)
            self.graph.add_node(target, layer=self._get_layer(target))
        if not self.graph.has_edge(source, target):
            self.limits.check("max_edges", self.graph.number_of_edges() + 1)
        self.graph.add_edge(source, target)
        self._check_edge_defects(source, target)

    def _get_layer(self, mod_name: str) -> int:
        for prefix, layer_idx in self.layer_rules.items():
            if mod_name.startswith(prefix) or f".{prefix}." in mod_name or f".{prefix}" in mod_name:
                return layer_idx
        return 99

    def _resolve_target(self, imp_mod: str, known_modules: List[str]) -> Optional[str]:
        if imp_mod in known_modules:
            return imp_mod
        for known in known_modules:
            if known.endswith(f".{imp_mod}") or known == imp_mod:
                return known
        return None

    def _check_edge_defects(self, src: str, dst: str) -> None:
        src_layer = self._get_layer(src)
        dst_layer = self._get_layer(dst)

        if src_layer < dst_layer:
            self.defects.append(
                ASTDefect(
                    defect_type="clean_arch_violation",
                    source_module=src,
                    target_module=dst,
                    description=f"Inward dependency violation: {src} (layer {src_layer}) -> {dst} (layer {dst_layer})",
                    weight=3.0,
                )
            )

    def _check_cycles(self) -> None:
        try:
            cycles, search_steps = find_dependency_cycles(self.graph, self.limits)
        except (nx.NetworkXException, TypeError, ValueError, ArithmeticError, RecursionError) as exc:
            raise DependencyCycleDetectionError(
                f"dependency cycle enumeration failed: {type(exc).__name__}"
            ) from exc
        cycle_defects = []
        for cycle in cycles:
            if len(cycle) >= 2:
                cycle_defects.append(
                    ASTDefect(
                        defect_type="circular_import",
                        source_module=cycle[0],
                        target_module=cycle[1],
                        description=f"Circular dependency cycle detected: {' -> '.join(cycle)} -> {cycle[0]}",
                        weight=4.0,
                    )
                )
        self.cycles = cycles
        self.search_steps = search_steps
        self.defects.extend(cycle_defects)

    def get_stats(self) -> Dict[str, int]:
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "num_defects": len(self.defects),
        }
