"""Replay submitted witnesses without attractor, minimax or strategy search."""

from __future__ import annotations

import json

from .model import ModelError, belief, compile_model, fields, rational

KEYS = {"schema", "kind", "model_digest", "task_id", "assumptions", "authorization",
        "initial", "winning", "losing", "stalled", "closure", "strategy", "ranks",
        "values", "resolutions", "optimality_requested"}


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ModelError(reason)


def _set(rows: object, arena) -> set:
    _require(type(rows) is list, "belief set must be a list")
    parsed = [belief(row, arena.states) for row in rows]
    _require(len(parsed) == len(set(parsed)), "duplicate certificate belief")
    return set(parsed)


def _map(rows: object, arena, field: str) -> dict:
    _require(type(rows) is list, "certificate map must be a list")
    result = {}
    for entry in rows:
        row = fields(entry, {"belief", field})
        b = belief(row["belief"], arena.states)
        _require(b not in result, "duplicate certificate map row")
        result[b] = row[field]
    return result


def check_certificate(model: object, certificate: object) -> dict:
    try:
        arena = compile_model(model)
        c = fields(certificate, KEYS)
        _require(c["schema"] == "wdp-progress-certificate-v1", "unknown certificate schema")
        _require(c["kind"] in {"LOSS", "WIN_OPTIMAL", "WIN_FEASIBLE"}, "unknown claim type")
        _require(c["model_digest"] == arena.model_digest and c["task_id"] == arena.task_id,
                 "original model or task binding mismatch")
        _require(c["assumptions"] == list(arena.assumptions), "assumptions changed")
        _require(json.dumps(c["authorization"], sort_keys=True, separators=(",", ":"), allow_nan=False)
                 == arena.authorization_json, "authorization binding changed")
        _require(belief(c["initial"], arena.states) == arena.initial, "initial belief mismatch")
        _require(type(c["optimality_requested"]) is bool, "optimality flag is not boolean")
        reachable = set(arena.reachable)
        targets = reachable & arena.targets  # Entirely model-derived.
        winning, losing = _set(c["winning"], arena), _set(c["losing"], arena)
        stalled = _set(c["stalled"], arena)
        _require(winning <= reachable and losing <= reachable, "certificate outside reachable arena")
        _require(not losing & targets, "losing region contains a successful terminal")
        _require(stalled == {b for b in losing if not arena.moves(b)},
                 "fabricated or incomplete stalled classification")
        _require(type(c["closure"]) is list, "closure map must be a list")
        closure = {}
        for entry in c["closure"]:
            row = fields(entry, {"belief", "action", "successor"})
            key = (belief(row["belief"], arena.states), row["action"])
            _require(key not in closure, "duplicate closure row")
            closure[key] = belief(row["successor"], arena.states)
        required_closure = {(b, a) for b in losing for a, _, _ in arena.moves(b)}
        _require(set(closure) == required_closure, "missing or extraneous losing closure witness")
        for b in losing:
            for a, _, ys in arena.moves(b):
                _require(closure[b, a] in ys and closure[b, a] in losing,
                         "adversary transition leaves the losing region")
        if c["kind"] == "LOSS":
            _require(arena.initial in losing, "initial belief outside submitted losing region")
            _require(not winning and all(c[k] == [] for k in ("strategy", "ranks", "values", "resolutions"))
                     and not c["optimality_requested"], "loss certificate carries incompatible win fields")
            return {"accepted": True, "claim": "LOSS", "status": "Refuted",
                    "termination": "Stalled" if arena.initial in stalled else "Trapped",
                    "model_digest": arena.model_digest, "authority_effect": "None"}
        _require(arena.initial in winning, "winning certificate omits the initial belief")
        _require(not winning & losing and winning | losing == reachable,
                 "incomplete or overlapping reachable partition")
        _require(targets <= winning, "winning region omits a successful terminal")
        values = {b: rational(v) for b, v in _map(c["values"], arena, "value").items()}
        ranks = _map(c["ranks"], arena, "rank")
        strategy = _map(c["strategy"], arena, "action")
        resolutions = _map(c["resolutions"], arena, "resolution")
        _require(set(values) == winning and set(ranks) == winning,
                 "value and rank maps must cover exactly the winning region")
        _require(all(type(v) is int and v >= 0 for v in ranks.values()), "rank is not a natural number")
        _require(set(strategy) == winning - targets, "strategy domain differs from nonterminal winners")
        _require(set(resolutions) == {b for b in winning if arena.valid_resolutions(b)},
                 "missing or extraneous resolution witness")
        for b, resolution in resolutions.items():
            _require(resolution in arena.valid_resolutions(b), "resolution fails a supplied world check")
        for b in targets:
            _require(values[b] == 0 and ranks[b] == 0, "terminal value and rank must be zero")
        optimal = c["kind"] == "WIN_OPTIMAL"
        _require(c["optimality_requested"] == optimal, "optimality obligation omitted or mistyped")
        for b in winning - targets:
            move = next((m for m in arena.moves(b) if m[0] == strategy[b]), None)
            _require(move is not None, "selected action is not admissible")
            _, cost, ys = move
            _require(all(y in winning and ranks[y] < ranks[b] for y in ys),
                     "strategy leaves winners or fails strict rank descent")
            _require(values[b] == cost + max(values[y] for y in ys), "upper equality failed")
            if optimal:
                for _, alternative_cost, successors in arena.moves(b):
                    # Infinity is justified only by the already checked trap.
                    if any(y in losing for y in successors):
                        continue
                    _require(all(y in winning for y in successors), "unclassified successor")
                    _require(values[b] <= alternative_cost + max(values[y] for y in successors),
                             "lower inequality failed: a cheaper action exists")
        return {"accepted": True, "claim": c["kind"], "status": "Proved",
                "initial_value": str(values[arena.initial]), "model_digest": arena.model_digest,
                "authority_effect": "None"}
    except (ModelError, TypeError, KeyError, ValueError, OverflowError) as error:
        return {"accepted": False, "status": "Refused", "reason": str(error),
                "authority_effect": "None"}
