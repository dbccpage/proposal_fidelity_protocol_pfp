"""Separate table checker for an exact belief quotient and refinement receipt.

No strategy or partition producer is imported. Terminal truth here is the declared
game predicate. Transport of actual task witnesses is an additional obligation.
"""

from .model import ModelError, compile_model, digest


def check_quotient(model, blocks, table):
    try:
        arena = compile_model(model)
        flat = [tuple(b) for block in blocks for b in block]
        if (
            any(not block for block in blocks)
            or len(flat) != len(set(flat))
            or set(flat) != set(arena.reachable)
            or len(table) != len(blocks)
        ):
            return False
        index = {tuple(b): i for i, block in enumerate(blocks) for b in block}
        for i, block in enumerate(blocks):
            row = table[i]
            if set(row) != {"target", "moves", "resolutions"} or type(row["target"]) is not bool:
                return False
            for b in block:
                b = tuple(b)
                expected = [
                    {"action": a, "cost": str(c), "successors": sorted({index[y] for y in ys})}
                    for a, c, ys in arena.moves(b)
                ]
                if row != {
                    "target": b in arena.targets,
                    "moves": expected,
                    "resolutions": list(arena.valid_resolutions(b)),
                }:
                    return False
        return True
    except (ModelError, KeyError, TypeError, ValueError):
        return False


def check_refinement(model, seed, certificate):
    """Check exact successive splits, stability, and the bound N-|seed|."""
    try:
        arena = compile_model(model)
        if set(certificate) != {"model_digest", "rounds"} or certificate["model_digest"] != digest(
            model
        ):
            return False

        def normalize(p):
            return tuple(sorted(tuple(sorted(tuple(b) for b in block)) for block in p))

        previous = normalize(seed)
        flat = [b for block in previous for b in block]
        if (
            any(not b for b in previous)
            or len(flat) != len(set(flat))
            or set(flat) != set(arena.reachable)
        ):
            return False
        for supplied in certificate["rounds"]:
            index = {b: i for i, block in enumerate(previous) for b in block}
            groups = []
            for block in previous:
                local = {}
                for b in block:
                    signature = (
                        b in arena.targets,
                        arena.valid_resolutions(b),
                        tuple(
                            (a, c, tuple(sorted({index[y] for y in ys})))
                            for a, c, ys in arena.moves(b)
                        ),
                    )
                    local.setdefault(signature, []).append(b)
                groups.extend(local.values())
            expected = normalize(groups)
            if normalize(supplied) != expected:
                return False
            previous = expected
        if (
            not certificate["rounds"]
            or len(certificate["rounds"]) > len(arena.reachable) - len(seed) + 1
        ):
            return False
        table = []
        index = {b: i for i, block in enumerate(previous) for b in block}
        for block in previous:
            b = block[0]
            table.append(
                {
                    "target": b in arena.targets,
                    "resolutions": list(arena.valid_resolutions(b)),
                    "moves": [
                        {"action": a, "cost": str(c), "successors": sorted({index[y] for y in ys})}
                        for a, c, ys in arena.moves(b)
                    ],
                }
            )
        return check_quotient(model, previous, table)
    except (ModelError, KeyError, TypeError, ValueError):
        return False
