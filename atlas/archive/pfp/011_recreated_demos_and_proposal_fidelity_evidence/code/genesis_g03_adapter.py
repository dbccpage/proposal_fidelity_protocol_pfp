"""Declared G03 chain adapter; new structure, not the withdrawn historical map."""
from __future__ import annotations

ADAPTER_ID = "G03_DECLARED_PREFIX_ANCHORS_V1"
PRIMARY = tuple(range(3, 16))
HELD_OUT = (16, 17, 18)


def coordinate(n: int, reading: str, i: int) -> int:
    if reading not in ("L", "F") or not 0 <= i <= n or n not in PRIMARY + HELD_OUT:
        raise ValueError("OUTSIDE_DECLARED_ADAPTER_DOMAIN")
    shift = int(reading == "F")
    return shift if i == 0 else shift + 1 if i == n else shift + i + 1


def specification(n: int, reading: str) -> dict:
    """All anchor/state structure is declared before oracle evaluation."""
    chain_data = n + 1 + int(reading == "F")
    count = (n - 1).bit_length()
    anchors = list(range(chain_data, chain_data + count))
    # Singleton markers distinguish chain ends and, in F, the extra inscription.
    singleton = [coordinate(n, reading, 0), coordinate(n, reading, n)]
    if reading == "F":
        singleton.append(0)
    instances = [(f, (mark,)) for f, mark in enumerate(singleton)]
    for level in range(count):
        instances += [(len(singleton) + level, (anchor,)) for anchor in anchors[:level + 1]]
    requirements = sorted((min(coordinate(n, reading, i), anchor), max(coordinate(n, reading, i), anchor))
                          for i in range(1, n) for bit, anchor in enumerate(anchors) if i & (1 << bit))
    return {"chain_data": chain_data, "anchors": anchors, "forms": [1] * (len(singleton) + count),
            "insts": sorted(instances), "reqs": requirements}


def construct(modules: dict, n: int, reading: str):
    """Extend the unchanged admission-reading prefix through original events."""
    model = modules["model"]
    prefix = modules["engine"].READING_L if reading == "L" else modules["engine"].READING_F
    declared = specification(n, reading)
    history = list(prefix.genesis)
    for i in range(1, n):
        token = f"G03:chain:{n}:{reading}:{i}"
        history += [model.Supply(token), model.AdmitDatum(token)]
    for bit in range(len(declared["anchors"])):
        token = f"G03:anchor:{n}:{reading}:{bit}"
        history += [model.Supply(token), model.AdmitDatum(token)]
    history += [model.AdmitForm(arity) for arity in declared["forms"]]
    history += [model.AdmitInst(form, args) for form, args in declared["insts"]]
    history += [model.Impose(*pair) for pair in declared["reqs"]]
    return model.replay(history), history


def reversal(n: int, reading: str, n_data: int) -> tuple[int, ...]:
    result = list(range(n_data))
    for i in range(n + 1):
        result[coordinate(n, reading, i)] = coordinate(n, reading, n - i)
    return tuple(result)


def fresh_mark(base, target, delta, candidates) -> bool:
    """A class qualifies if one member has the generator's exact larger-end mark."""
    return delta == candidates.canonical_delta((candidates.NewForm(1),
        candidates.NewInst(len(base.forms), (target[1],))))
