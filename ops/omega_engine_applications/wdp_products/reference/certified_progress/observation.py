"""Task-compatible quotient of the information-state arena, not world states."""

from __future__ import annotations

import json

from .model import ModelError, compile_model, graph_model


def _partition(arena, blocks):
    parsed = tuple(tuple(sorted(tuple(sorted(b)) for b in block)) for block in blocks)
    flattened = [b for block in parsed for b in block]
    if any(not block for block in parsed) or len(flattened) != len(set(flattened)):
        raise ModelError("empty or overlapping observation block")
    if set(flattened) != set(arena.reachable):
        raise ModelError("observation partition must cover exactly the belief arena")
    return tuple(sorted(parsed))


def _signatures(arena, blocks):
    index = {b: i for i, block in enumerate(blocks) for b in block}
    return {
        b: (
            b in arena.targets,
            tuple(
                (a, cost, tuple(sorted({index[y] for y in ys}))) for a, cost, ys in arena.moves(b)
            ),
        )
        for b in arena.reachable
    }


def is_congruence(model, blocks):
    arena = compile_model(model)
    partition = _partition(arena, blocks)
    signatures = _signatures(arena, partition)
    return all(all(signatures[b] == signatures[block[0]] for b in block) for block in partition)


def refine_observation(model, blocks):
    arena = compile_model(model)
    partition = _partition(arena, blocks)
    initial_size, rounds = len(partition), 0
    while True:
        signatures = _signatures(arena, partition)
        refined = []
        for block in partition:
            groups = {}
            for b in block:
                groups.setdefault(signatures[b], []).append(b)
            refined.extend(tuple(bs) for bs in groups.values())
        refined = tuple(sorted(refined))
        if refined == partition:
            break
        rounds += 1
        partition = refined
    return {
        "blocks": [[list(b) for b in block] for block in partition],
        "strict_rounds": rounds,
        "round_bound": len(arena.reachable) - initial_size,
        "model_digest": arena.model_digest,
        "authority_effect": "None",
    }


def quotient_model(model, blocks):
    """Construct the exact finite game quotient when all congruence laws hold."""
    arena = compile_model(model)
    partition = _partition(arena, blocks)
    signatures = _signatures(arena, partition)
    if not all(all(signatures[b] == signatures[block[0]] for b in block) for block in partition):
        raise ModelError("not a task-compatible belief-arena congruence")
    index = {b: i for i, block in enumerate(partition) for b in block}
    graph = {
        str(i): [
            (a, str(cost), [str(j) for j in sorted({index[y] for y in ys})])
            for a, cost, ys in arena.moves(block[0])
        ]
        for i, block in enumerate(partition)
    }
    result = graph_model(
        graph,
        initial=str(index[arena.initial]),
        targets=tuple(str(i) for i, block in enumerate(partition) if block[0] in arena.targets),
        task_id=arena.task_id + "/declared-belief-quotient",
        authorization=json.loads(arena.authorization_json),
    )
    # Witness ids are not quotiented into a new claim about original answers.
    # This quotient preserves game reachability and cost under the proved laws.
    result["assumptions"] = list(arena.assumptions)
    return result


def refine_operation_presentation(model, blocks):
    """Retain resolution IDs as well as game structure; emit checkable split rounds."""
    arena = compile_model(model)
    partition = _partition(arena, blocks)
    rounds = []
    while True:
        signatures = _signatures(arena, partition)
        refined = []
        for block in partition:
            groups = {}
            for b in block:
                groups.setdefault((signatures[b], arena.valid_resolutions(b)), []).append(b)
            refined.extend(tuple(bs) for bs in groups.values())
        refined = tuple(sorted(refined))
        rounds.append([[list(b) for b in block] for block in refined])
        if refined == partition:
            break
        partition = refined
    index = {b: i for i, block in enumerate(partition) for b in block}
    table = [
        {
            "target": block[0] in arena.targets,
            "resolutions": list(arena.valid_resolutions(block[0])),
            "moves": [
                {"action": a, "cost": str(c), "successors": sorted({index[y] for y in ys})}
                for a, c, ys in arena.moves(block[0])
            ],
        }
        for block in partition
    ]
    return {
        "refinement": {"model_digest": arena.model_digest, "rounds": rounds},
        "blocks": rounds[-1],
        "table": table,
    }
