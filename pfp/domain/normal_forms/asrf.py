"""Autopoietic self-reference refusal form.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

# =============================================================================
# Part 9: Autopoietic Self-Reference Refusal Form (ASRF)
# =============================================================================


@dataclass(frozen=True)
class AsrfResult:
    """Verification result for Autopoietic Self-Reference Refusal Form (ASRF)."""

    terminal: str
    action: str
    admitted: bool
    status: str
    reason: str
    cycle_detected: bool
    detected_cycle: tuple[str, ...] | None = None
    caller_hash: str = ""
    target_hash: str = ""
    call_graph_nodes: int = 0
    call_graph_edges: int = 0


@dataclass(frozen=True)
class _AsrfContext:
    caller_hash: str
    target_hash: str
    adjacency: Mapping[str, Sequence[str]]
    edge_count: int


def _asrf_result(
    context: _AsrfContext,
    status: str,
    reason: str,
    cycle: Sequence[str] | None,
) -> AsrfResult:
    refused = status != "Accept"
    return AsrfResult(
        terminal="SelfReferenceRefusal" if refused else "Accept",
        action="Refuse" if refused else "Preserve",
        admitted=not refused,
        status=status,
        reason=reason,
        cycle_detected=cycle is not None,
        detected_cycle=tuple(cycle) if cycle is not None else None,
        caller_hash=context.caller_hash,
        target_hash=context.target_hash,
        call_graph_nodes=len(context.adjacency),
        call_graph_edges=context.edge_count,
    )


def verify_asrf(
    caller_hash: str,
    target_hash: str,
    call_graph: Mapping[str, Sequence[str]] | Sequence[tuple[str, str]] | None = None,
) -> AsrfResult:
    """ASRF: Autopoietic Self-Reference Refusal Form verifier.

    Contract: nf.recursion.asrf
    Excludes: A caller that certifies the state it just generated (self-certification cycle).
    Preserves: caller_hash differs from target_hash, and detected self-cycles are refused.

    Terminal Routes:
      - Accept (Preserve): caller_hash != target_hash and no directed cycle connects them.
      - SelfReferenceRefusal (Refuse): caller_hash == target_hash or directed cycle detected.

    Non-claims:
      - Composes declared hashes and declared call graph; computes no cohomology groups
        and is not an incompleteness theorem.
    """
    if not _valid_hashes(caller_hash, target_hash):
        context = _AsrfContext(str(caller_hash), str(target_hash), {}, 0)
        return _asrf_result(
            context,
            "SelfReferenceRefusal_MalformedDeclaration",
            "Caller and target hashes must be nonempty strings.",
            None,
        )

    c_hash = caller_hash.strip()
    t_hash = target_hash.strip()

    adj, edge_count = _normalize_call_graph(call_graph)
    context = _AsrfContext(c_hash, t_hash, adj, edge_count)
    return _verify_asrf_context(context)


def _verify_asrf_context(context: _AsrfContext) -> AsrfResult:
    c_hash = context.caller_hash
    t_hash = context.target_hash
    adj = context.adjacency
    if c_hash == t_hash:
        return _asrf_result(
            context,
            "SelfReferenceRefusal_IdenticalHashes",
            "Caller hash equals target hash: direct self-certification cycle refused.",
            (c_hash, t_hash),
        )

    path_t_to_c = _find_path(adj, t_hash, c_hash)
    if path_t_to_c is not None:
        cycle = [c_hash] + path_t_to_c
        return _asrf_result(
            context,
            "SelfReferenceRefusal_CallGraphCycle",
            f"Directed cycle detected through caller and target: {' -> '.join(cycle)}",
            cycle,
        )

    path_c_to_c = _find_path(adj, c_hash, c_hash)
    if path_c_to_c is not None:
        return _asrf_result(
            context,
            "SelfReferenceRefusal_CallGraphCycle",
            f"Directed self-loop on caller detected: {' -> '.join(path_c_to_c)}",
            path_c_to_c,
        )

    return _asrf_result(
        context,
        "Accept",
        "Caller hash differs from target hash and call graph contains no cycle through caller and target.",
        None,
    )


def _valid_hashes(caller_hash: object, target_hash: object) -> bool:
    return (
        isinstance(caller_hash, str)
        and isinstance(target_hash, str)
        and bool(caller_hash.strip())
        and bool(target_hash.strip())
    )


def _normalize_call_graph(
    call_graph: Mapping[str, Sequence[str]] | Sequence[tuple[str, str]] | None,
) -> tuple[dict[str, list[str]], int]:
    adjacency: dict[str, list[str]] = {}
    edges = 0
    if isinstance(call_graph, Mapping):
        pairs = ((source, target) for source, targets in call_graph.items() for target in targets)
    elif isinstance(call_graph, Iterable):
        pairs = (
            (edge[0], edge[1])
            for edge in call_graph
            if isinstance(edge, (tuple, list)) and len(edge) == 2
        )
    else:
        pairs = iter(())
    for source, target in pairs:
        source_hash, target_hash = str(source).strip(), str(target).strip()
        adjacency.setdefault(source_hash, []).append(target_hash)
        adjacency.setdefault(target_hash, [])
        edges += 1
    return adjacency, edges


def _find_path(adjacency: Mapping[str, Sequence[str]], start: str, goal: str) -> list[str] | None:
    if start not in adjacency:
        return None
    visited: set[str] = set()
    queue: deque[list[str]] = deque([[start]])
    while queue:
        path = queue.popleft()
        current = path[-1]
        if current == goal and len(path) > 1:
            return path
        if current in visited:
            continue
        visited.add(current)
        for successor in adjacency.get(current, ()):
            if successor == goal:
                return path + [successor]
            if successor not in visited:
                queue.append(path + [successor])
    return None
