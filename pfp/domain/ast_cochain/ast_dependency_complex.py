from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence, Tuple

import numpy as np

from .ast_models import ASTDefect
from .ast_source_parser import ParsedSourceTree

DEFAULT_LAYER_RANKS: Dict[str, int] = {
    "domain": 1,
    "use_cases": 2,
    "controllers": 3,
    "infrastructure": 4,
    "frontend": 5,
    "entrypoints": 5,
    "cli": 5,
}


@dataclass(frozen=True)
class DependencyComplex:
    modules: tuple[str, ...]
    edges: tuple[Tuple[int, int], ...]
    edge_defects: tuple[float, ...]
    faces: tuple[Tuple[int, int, int], ...]
    defect_descriptions: tuple[str, ...]
    syntax_defects: tuple[ASTDefect, ...]
    d0: np.ndarray
    d1: np.ndarray
    omega: np.ndarray


class DependencyComplexBuilder:
    """Build dependency geometry and structural defects from parsed Python source."""

    def __init__(self, layer_ranks: Optional[Mapping[str, int]] = None):
        self.layer_ranks = dict(layer_ranks or DEFAULT_LAYER_RANKS)

    def build(self, parsed: ParsedSourceTree) -> DependencyComplex:
        modules = parsed.modules
        node_to_idx = {m: i for i, m in enumerate(modules)}
        edges: list[Tuple[int, int]] = []
        edge_defects: list[float] = []
        descriptions = [f"defect:{d.defect_type}:{d.source_module}" for d in parsed.syntax_defects]

        for source, imported_targets in parsed.imports.items():
            source_idx = node_to_idx[source]
            source_layer = self.module_layer(source)
            for target in imported_targets:
                matched = self.resolve_target_module(target, modules)
                if matched is None or matched == source:
                    continue

                target_idx = node_to_idx[matched]
                target_layer = self.module_layer(matched)
                weight = 0.0

                if source_layer is not None and target_layer is not None and source_layer < target_layer:
                    descriptions.append(f"defect:clean_arch_violation:{source}->{matched}")
                    weight += 1.5

                if source in parsed.imports.get(matched, set()):
                    if source_idx < target_idx:
                        descriptions.append(f"defect:circular_import:{source}<->{matched}")
                    weight += 1.0

                edges.append((source_idx, target_idx))
                edge_defects.append(weight)

        edges, edge_defects = self._ensure_base_structure(len(modules), edges, edge_defects)
        faces = self._faces(edges)
        d0, d1 = self._boundary_matrices(len(modules), edges, faces)
        omega = np.asarray(edge_defects, dtype=float)
        if parsed.syntax_defects:
            omega = omega + sum(d.weight for d in parsed.syntax_defects) / max(1, len(omega))

        return DependencyComplex(
            modules=modules,
            edges=tuple(edges),
            edge_defects=tuple(edge_defects),
            faces=tuple(faces),
            defect_descriptions=tuple(descriptions),
            syntax_defects=parsed.syntax_defects,
            d0=d0,
            d1=d1,
            omega=omega,
        )

    def module_layer(self, module_name: str) -> Optional[int]:
        for part in module_name.split("."):
            if part in self.layer_ranks:
                return self.layer_ranks[part]
        return None

    @staticmethod
    def resolve_target_module(target_import: str, known_modules: Sequence[str]) -> Optional[str]:
        for module in known_modules:
            if (
                target_import == module
                or target_import.startswith(module + ".")
                or module.endswith("." + target_import)
            ):
                return module
        return None

    @staticmethod
    def _ensure_base_structure(
        n_nodes: int,
        edges: list[Tuple[int, int]],
        weights: list[float],
    ) -> tuple[list[Tuple[int, int]], list[float]]:
        if edges:
            return edges, weights
        for index in range(n_nodes - 1):
            edges.append((index, index + 1))
            weights.append(0.0)
        if not edges and n_nodes:
            edges.append((0, 0))
            weights.append(0.0)
        return edges, weights

    @staticmethod
    def _faces(edges: Sequence[Tuple[int, int]]) -> list[Tuple[int, int, int]]:
        edge_to_idx = {edge: i for i, edge in enumerate(edges)}
        edge_set = set(edges)
        faces: list[Tuple[int, int, int]] = []
        for u, v in edges:
            for v2, w in edges:
                if v2 == v and (u, w) in edge_set:
                    faces.append((edge_to_idx[(u, v)], edge_to_idx[(v, w)], edge_to_idx[(u, w)]))
        return faces

    @staticmethod
    def _boundary_matrices(
        n_nodes: int,
        edges: Sequence[Tuple[int, int]],
        faces: Sequence[Tuple[int, int, int]],
    ) -> tuple[np.ndarray, np.ndarray]:
        d0 = np.zeros((len(edges), n_nodes), dtype=float)
        for i, (u, v) in enumerate(edges):
            if u != v:
                d0[i, u] = -1.0
                d0[i, v] = 1.0

        if not faces:
            return d0, np.zeros((1, len(edges)), dtype=float)

        d1 = np.zeros((len(faces), len(edges)), dtype=float)
        for face_index, (e1, e2, e3) in enumerate(faces):
            d1[face_index, e1] = 1.0
            d1[face_index, e2] = 1.0
            d1[face_index, e3] = -1.0
        return d0, d1
