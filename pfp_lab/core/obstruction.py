"""Exact defect, primary obstruction Phi_1 and the idempotent projection P_S.

AuthorityEffect: None.
Contract: urn:pfp-lab:core:obstruction:v1
Provenance: ported from ``compute_coboundary``, ``find_spanning_forest_potentials``,
``compute_phi1`` and ``L1SymbolGameGovernor.project`` in the Paper 005 governor;
``pfp_lab/core/PROVENANCE.md`` records the digest and every change.

Profile: Exact. For claims ``c`` on the declared edges and a section ``s`` on
the vertices:

* section defect  ``D(s) = sum_e w_e |c_e - (s(v) - s(u))|``;
* obstruction     ``Phi_1(c) = min_f D(f)``, attained at a spanning-forest
  potential (a basic solution of the totally unimodular L1 problem);
* projection      ``P_S(s) = s + f*`` where ``f*`` minimises the defect of the
  residual claims, so ``D(P_S(s)) = Phi_1(c)`` and ``P_S(P_S(s)) = P_S(s)``.

Cost: the defect is ``O(E)``. Phi_1 enumerates spanning trees of each connected
component separately (the defect is a sum over components), so the work is the
sum, not the product, of per-component tree counts. Graphs are bounded by
``MAX_VERTICES`` and ``MAX_EDGES``, and every enumeration step is charged to an
explicit budget that raises ``BudgetExceededError`` instead of running on.
Ties are broken exactly as the Paper 005 enumeration does: the all-zero
potential first, then trees in include-before-exclude edge order, keeping the
first strict minimum.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from fractions import Fraction

from pfp_lab.core.admission import AdmissionError, BudgetExceededError
from pfp_lab.core.graph import ConstraintGraph, Edge, EdgeKey

DEFAULT_SEARCH_BUDGET = 1_000_000

Section = Mapping[str, Fraction]
Claims = Mapping[EdgeKey, Fraction]

_ZERO = Fraction(0)


class SearchBudget:
    """A countdown of enumeration steps; exhausting it is a typed failure."""

    def __init__(self, steps: int) -> None:
        if type(steps) is not int or steps < 1:
            raise AdmissionError("search budget must be a positive integer")
        self.remaining = steps

    def charge(self) -> None:
        if self.remaining <= 0:
            raise BudgetExceededError("obstruction search exceeded its step budget")
        self.remaining -= 1


def edge_residual(item: Edge, claims: Claims, section: Section) -> Fraction:
    """``c_e - (s(v) - s(u))`` for one edge; absent values read as zero."""
    claim = claims.get(item.key, _ZERO)
    return claim - (section.get(item.target, _ZERO) - section.get(item.source, _ZERO))


def section_defect(graph: ConstraintGraph, claims: Claims, section: Section) -> Fraction:
    """``D(s)``: the weighted L1 distance between the claims and ``ds``."""
    total = _ZERO
    for item in graph.edges:
        total += item.weight * abs(edge_residual(item, claims, section))
    return total


def check_claims(graph: ConstraintGraph, claims: Claims) -> None:
    """Refuse claims on undeclared edges or with non-Fraction values."""
    for key, value in claims.items():
        if graph.edge(*key) is None:
            raise AdmissionError(f"claim on undeclared edge {key[0]} -> {key[1]}")
        if type(value) is not Fraction:
            raise AdmissionError(f"claim on {key[0]} -> {key[1]} must be an exact Fraction")


def obstruction(
    graph: ConstraintGraph,
    claims: Claims,
    *,
    budget: int = DEFAULT_SEARCH_BUDGET,
) -> tuple[Fraction, dict[str, Fraction]]:
    """``Phi_1(c)`` and the first potential (in Paper 005 order) attaining it."""
    check_claims(graph, claims)
    counter = SearchBudget(budget)
    total = _ZERO
    potential: dict[str, Fraction] = {}
    for component in graph.components():
        value, best = _component_minimum(graph, component, claims, counter)
        total += value
        potential.update(best)
    return total, potential


def project(
    graph: ConstraintGraph,
    claims: Claims,
    section: Section,
    *,
    budget: int = DEFAULT_SEARCH_BUDGET,
) -> dict[str, Fraction]:
    """``P_S(s)``: shift ``s`` by the gauge that minimises the residual defect."""
    residual = {item.key: edge_residual(item, claims, section) for item in graph.edges}
    _, gauge = obstruction(graph, residual, budget=budget)
    return {name: section.get(name, _ZERO) + gauge[name] for name in graph.vertices}


def _component_minimum(
    graph: ConstraintGraph,
    component: tuple[str, ...],
    claims: Claims,
    counter: SearchBudget,
) -> tuple[Fraction, dict[str, Fraction]]:
    members = set(component)
    edges = tuple(item for item in graph.edges if item.source in members)
    best = {name: _ZERO for name in component}
    best_value = _component_defect(edges, claims, best)
    for tree in _spanning_trees(component, edges, counter):
        candidate = _tree_potential(component, tree, claims)
        value = _component_defect(edges, claims, candidate)
        if value < best_value:
            best, best_value = candidate, value
    return best_value, best


def _component_defect(edges: tuple[Edge, ...], claims: Claims, section: Section) -> Fraction:
    total = _ZERO
    for item in edges:
        total += item.weight * abs(edge_residual(item, claims, section))
    return total


def _spanning_trees(
    component: tuple[str, ...],
    edges: tuple[Edge, ...],
    counter: SearchBudget,
) -> Iterator[tuple[Edge, ...]]:
    """Every spanning tree of one component, include-before-exclude order."""
    if len(component) < 2:
        return
    parents = {name: name for name in component}
    yield from _extend(edges, 0, (), parents, len(component) - 1, counter)


def _extend(
    edges: tuple[Edge, ...],
    index: int,
    chosen: tuple[Edge, ...],
    parents: dict[str, str],
    needed: int,
    counter: SearchBudget,
) -> Iterator[tuple[Edge, ...]]:
    counter.charge()
    if len(chosen) == needed:
        yield chosen
        return
    if len(chosen) + (len(edges) - index) < needed:
        return
    item = edges[index]
    root_source = _root(parents, item.source)
    root_target = _root(parents, item.target)
    if root_source != root_target:
        joined = dict(parents)
        joined[root_source] = root_target
        yield from _extend(edges, index + 1, (*chosen, item), joined, needed, counter)
    yield from _extend(edges, index + 1, chosen, parents, needed, counter)


def _root(parents: dict[str, str], name: str) -> str:
    current = name
    while parents[current] != current:
        current = parents[current]
    return current


def _tree_potential(
    component: tuple[str, ...],
    tree: tuple[Edge, ...],
    claims: Claims,
) -> dict[str, Fraction]:
    """The potential, rooted at zero on the first vertex, that satisfies every tree claim."""
    steps: dict[str, list[tuple[str, Fraction]]] = {name: [] for name in component}
    for item in tree:
        claim = claims.get(item.key, _ZERO)
        steps[item.source].append((item.target, claim))
        steps[item.target].append((item.source, -claim))
    root = component[0]
    potential = {root: _ZERO}
    stack = [root]
    while stack:
        current = stack.pop()
        for neighbour, delta in steps[current]:
            if neighbour not in potential:
                potential[neighbour] = potential[current] + delta
                stack.append(neighbour)
    return potential


__all__ = [
    "DEFAULT_SEARCH_BUDGET",
    "Claims",
    "SearchBudget",
    "Section",
    "check_claims",
    "edge_residual",
    "obstruction",
    "project",
    "section_defect",
]
