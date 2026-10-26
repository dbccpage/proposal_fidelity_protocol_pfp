"""Target checker of record for MSS-006, row 6 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 6): check old presentations embed conservatively and boundary
endpoints match. Negative instance: a new relation collapsing old generators
is rejected.

Input (closed):
``{"old_generators": [str], "old_relations": [[str, str]],
"new_generators": [str], "new_relations": [[str, str]],
"embedding": [[old, new]], "arrows": [[name, src, tgt]],
"cells": [[[arrow name], [arrow name]]]}``.

Declared class: presentations whose relations are equations between
generators, decided by union-find (the decidable fragment named in W2-DA order
006). Conservativity is R_new restricted to the image of the old generators
equal to R_old: two old generators are identified in the new presentation
exactly when they were identified in the old one. The cells half is a 2-cell
between two paths of arrows.

Clauses:

- C1 ``R006_COLLAPSES_OLD``: the new relations identify two old generators
  that the old relations kept apart, directly or through a chain;
- C2 ``R006_RELATION_LOST``: two old generators identified before are apart in
  the new presentation, so the embedding is not a presentation map;
- C3 ``R006_EMBEDDING_PARTIAL``: an old generator has no image, or its image
  is not a new generator;
- C4 ``R006_ENDPOINT_MISMATCH``: a 2-cell joins paths whose sources or targets
  differ;
- C5 ``R006_PATH_BROKEN``: a path in a 2-cell is not composable.
"""

STAGE = 6
ROW_SHA256 = "sha256:f343b508ae29aefa417d3fb91994b41cacdbf848fec0cebc2e095cf71653bcef"
FIELDS = ("arrows", "cells", "embedding", "new_generators", "new_relations", "old_generators", "old_relations")
CLAUSES = (
    ("C1", "R006_COLLAPSES_OLD"),
    ("C2", "R006_RELATION_LOST"),
    ("C3", "R006_EMBEDDING_PARTIAL"),
    ("C4", "R006_ENDPOINT_MISMATCH"),
    ("C5", "R006_PATH_BROKEN"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ("stage_embedding",)
OWN_NEGATIVE = {
    "arrows": [["f", 0, 1]],
    "cells": [[["f"], ["f"]]],
    "embedding": [["a", "a"], ["b", "b"]],
    "new_generators": ["a", "b", "c"],
    "new_relations": [["a", "b"]],
    "old_generators": ["a", "b"],
    "old_relations": [],
}
OWN_NEGATIVE_CODE = "R006_COLLAPSES_OLD"


def _names(value):
    names = [_text(item) for item in _seq(value)]
    _require(len(set(names)) == len(names), "R_SCHEMA")
    return names


def _classes(generators, relations):
    """Union-find over the generators; returns each generator's root."""
    parent = {g: g for g in generators}

    def root(x):
        while parent[x] != x:
            x = parent[x]
        return x

    for pair in _seq(relations):
        _seq(pair, 2)
        left, right = _text(pair[0]), _text(pair[1])
        _require(left in parent and right in parent, "R_SCHEMA")
        a, b = root(left), root(right)
        if a != b:
            parent[max(a, b)] = min(a, b)
    return {g: root(g) for g in generators}


def _decide(payload):
    old = _names(payload["old_generators"])
    new = _names(payload["new_generators"])
    image = {}
    for pair in _seq(payload["embedding"]):
        _seq(pair, 2)
        source, target = _text(pair[0]), _text(pair[1])
        _require(source in old and source not in image, "R_SCHEMA")
        image[source] = target
    _require(set(image) == set(old) and all(t in new for t in image.values()), "R006_EMBEDDING_PARTIAL")
    old_root = _classes(old, payload["old_relations"])
    new_root = _classes(new, payload["new_relations"])
    for index, x in enumerate(old):
        for y in old[index + 1 :]:
            same_old = old_root[x] == old_root[y]
            same_new = new_root[image[x]] == new_root[image[y]]
            _require(same_old or not same_new, "R006_COLLAPSES_OLD")
            _require(same_new or not same_old, "R006_RELATION_LOST")
    arrows = {}
    for entry in _seq(payload["arrows"]):
        _seq(entry, 3)
        name = _text(entry[0])
        _require(name not in arrows, "R_SCHEMA")
        arrows[name] = (_nat(entry[1]), _nat(entry[2]))
    for cell in _seq(payload["cells"]):
        _seq(cell, 2)
        ends = []
        for path in cell:
            names = _seq(path)
            _require(names and all(isinstance(n, str) and n in arrows for n in names), "R_SCHEMA")
            for first, second in zip(names, names[1:]):
                _require(arrows[first][1] == arrows[second][0], "R006_PATH_BROKEN")
            ends.append((arrows[names[0]][0], arrows[names[-1]][1]))
        _require(ends[0] == ends[1], "R006_ENDPOINT_MISMATCH")
