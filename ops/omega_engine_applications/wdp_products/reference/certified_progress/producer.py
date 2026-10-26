"""Certificate search. The checker imports no code from this module."""

from __future__ import annotations

import json

from .model import compile_model


def solve_progress(model: object, *, max_horizon: int | None = None) -> dict:
    arena = compile_model(model)
    targets = set(arena.reachable) & arena.targets
    winning, attractor_rank = set(targets), {b: 0 for b in targets}
    layer = 0
    while True:
        layer += 1
        admitted = {b for b in arena.reachable if b not in winning
                    and any(set(ys) <= winning for _, _, ys in arena.moves(b))}
        if not admitted:
            break
        attractor_rank.update({b: layer for b in admitted})
        winning |= admitted
    losing = set(arena.reachable) - winning
    stalled = {b for b in losing if not arena.moves(b)}
    closure = [{"belief": list(b), "action": a,
                "successor": list(next(y for y in ys if y in losing))}
               for b in sorted(losing) for a, _, ys in arena.moves(b)]
    certificate = {"schema": "wdp-progress-certificate-v1", "kind": "LOSS",
                   "model_digest": arena.model_digest, "task_id": arena.task_id,
                   "assumptions": list(arena.assumptions),
                   "authorization": json.loads(arena.authorization_json),
                   "initial": list(arena.initial), "winning": [],
                   "losing": [list(b) for b in sorted(losing)],
                   "stalled": [list(b) for b in sorted(stalled)], "closure": closure,
                   "strategy": [], "ranks": [], "values": [], "resolutions": [],
                   "optimality_requested": False}
    if arena.initial in losing:
        return {"status": "Refuted", "certificate": certificate,
                "producer": {"attractor_rank": [{"belief": list(b), "rank": rank}
                                                 for b, rank in sorted(attractor_rank.items())]}}
    # A common attractor-policy cost bound bounds the horizon of every cheaper
    # strategy. Use synchronous finite-horizon minimax, with None for infinity.
    costs = [c for _, _, c, _ in arena.edges]
    epsilon = min(costs) if costs else 1
    ceiling = (max(costs) if costs else 0) * max(attractor_rank.values(), default=0)
    horizon = int(ceiling // epsilon)
    if max_horizon is not None:
        if type(max_horizon) is not int or max_horizon < 0:
            raise ValueError("max_horizon must be a natural number")
        if horizon > max_horizon:
            return {"status": "Undetermined", "certificate": None,
                    "reason": "finite minimax horizon exceeds declared resource limit",
                    "remaining_horizon": horizon}
    values = {b: (0 if b in targets else None) for b in arena.reachable}
    rounds = 0
    for _ in range(horizon):
        updated = dict(values)
        for b in winning - targets:
            alternatives = [c + max(values[y] for y in ys)
                            for _, c, ys in arena.moves(b)
                            if all(values[y] is not None for y in ys)]
            updated[b] = min(alternatives) if alternatives else None
        rounds += 1
        if updated == values:
            break
        values = updated
    if any(values[b] is None for b in winning):
        raise RuntimeError("finite-horizon construction did not cover the attractor")
    strategy, rank = {}, {b: 0 for b in targets}
    for b in sorted(winning - targets, key=lambda b: (values[b], b)):
        a, c, ys = next((a, c, ys) for a, c, ys in arena.moves(b)
                       if all(values[y] is not None for y in ys)
                       and c + max(values[y] for y in ys) == values[b])
        strategy[b] = a
        rank[b] = 1 + max(rank[y] for y in ys)
    certificate.update(kind="WIN_OPTIMAL", optimality_requested=True,
                       winning=[list(b) for b in sorted(winning)],
                       strategy=[{"belief": list(b), "action": a} for b, a in sorted(strategy.items())],
                       ranks=[{"belief": list(b), "rank": rank[b]} for b in sorted(winning)],
                       values=[{"belief": list(b), "value": str(values[b])} for b in sorted(winning)],
                       resolutions=[{"belief": list(b), "resolution": arena.valid_resolutions(b)[0]}
                                    for b in sorted(winning) if arena.valid_resolutions(b)])
    return {"status": "Proved", "certificate": certificate,
            "producer": {"horizon_bound": horizon, "minimax_rounds": rounds,
                         "attractor_rank": [{"belief": list(b), "rank": r}
                                            for b, r in sorted(attractor_rank.items())]}}
