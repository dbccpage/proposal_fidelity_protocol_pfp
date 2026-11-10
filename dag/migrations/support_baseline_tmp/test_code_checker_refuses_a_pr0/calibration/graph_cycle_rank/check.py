"""Independent checker for the graph cycle-rank calibration task. AuthorityEffect: None.

Exit 0 when the answer file holds exactly the required JSON object with correct
invariants and a valid spanning forest; exit 1 otherwise. Output follows review_common.run:
only pass or fail unless --detail is given.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

VERTICES = tuple("abcdefghijkl")
EDGES = (("a", "b"), ("b", "c"), ("c", "a"), ("c", "d"), ("d", "e"), ("e", "f"), ("f", "d"),
         ("f", "g"), ("g", "a"), ("b", "c"), ("e", "e"), ("h", "i"), ("i", "j"), ("j", "k"),
         ("k", "h"), ("h", "j"))
FIELDS = ("vertices", "edges", "components", "component_sizes", "cycle_rank", "spanning_forest_edge_ids")


def _find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def reference() -> dict:
    parent = {v: v for v in VERTICES}
    for u, v in EDGES:
        parent[_find(parent, u)] = _find(parent, v)
    sizes = {}
    for v in VERTICES:
        root = _find(parent, v)
        sizes[root] = sizes.get(root, 0) + 1
    components = len(sizes)
    return {"vertices": len(VERTICES), "edges": len(EDGES), "components": components,
            "component_sizes": sorted(sizes.values(), reverse=True),
            "cycle_rank": len(EDGES) - len(VERTICES) + components}


def forest_problems(ids, components) -> list[str]:
    if type(ids) is not list or any(type(i) is not int for i in ids):
        return ["spanning_forest_edge_ids must be a list of integers"]
    problems = []
    if ids != sorted(ids) or len(set(ids)) != len(ids):
        problems.append("spanning_forest_edge_ids must be sorted ascending without repeats")
    if any(not 0 <= i < len(EDGES) for i in ids):
        return problems + ["spanning_forest_edge_ids names an edge outside 0..15"]
    parent = {v: v for v in VERTICES}
    for i in ids:
        u, v = EDGES[i]
        ru, rv = _find(parent, u), _find(parent, v)
        if ru == rv:
            problems.append(f"edge {i} closes a cycle")
        parent[ru] = rv
    if len(ids) != len(VERTICES) - components:
        problems.append(f"a spanning forest has {len(VERTICES) - components} edges, got {len(ids)}")
    return problems


def check(text: str) -> dict:
    try:
        answer = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"pass": False, "problems": [f"not a JSON object: {exc.msg}"]}
    if type(answer) is not dict:
        return {"pass": False, "problems": ["top level must be a JSON object"]}
    expected = reference()
    problems = [f"missing field {name}" for name in FIELDS if name not in answer]
    problems += [f"unexpected field {name}" for name in answer if name not in FIELDS]
    for name, value in expected.items():
        if name in answer and (answer[name] != value or type(answer[name]) is not type(value)):
            problems.append(f"{name} is wrong")
    if "spanning_forest_edge_ids" in answer:
        problems += forest_problems(answer["spanning_forest_edge_ids"], expected["components"])
    return {"pass": not problems, "problems": problems,
            "answer": {key: answer.get(key) for key in FIELDS}}


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import review_common

    return review_common.run(argv, check=check, reference=reference,
        prompt=Path(__file__).resolve().parent / "prompt.md",
        fragments=[f"| {i} | {u} {v} |" for i, (u, v) in enumerate(EDGES)])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
