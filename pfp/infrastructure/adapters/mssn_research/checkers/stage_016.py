"""Target checker of record for MSS-016, row 16 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 16): check composition on generators and all source
relations. Negative instance: an injective generator map that collapses a
source equation is rejected.

Input (closed): ``{"stages": [{"generators": [str], "relations": [[str,
str]]}], "maps": [{"source": i, "target": j, "on_generators": [[x, y]]}]}``.
Stages are finite presentations whose relations are equations between
generators; the fragment is decided by union-find. Every consecutive map
``i -> i+1`` must be declared; any other declared map ``i -> k`` is checked
for coherence against the composite through every declared intermediate.

Clauses, recomputed from the presentations:

- C1 ``R016_MAP_PARTIAL``: a map is not total on its source generators, or
  lands outside its target generators;
- C2 ``R016_RELATION_NOT_PRESERVED``: a source relation is not sent to a
  consequence of the target relations;
- C3 ``R016_COLLAPSES_EQUATION``: two source generators apart in the source
  are identified in the target, directly or through a chain. The map may be
  injective on generators and still fail here: that is the negative;
- C4 ``R016_NOT_COHERENT``: a declared map differs from the composite of
  declared maps through an intermediate stage, on some generator.
"""

STAGE = 16
ROW_SHA256 = "sha256:62eadc3ea2c0deb80717534c3fcd7d31fe6334d9671d2641216bdb2322abe069"
FIELDS = ("maps", "stages")
CLAUSES = (
    ("C1", "R016_MAP_PARTIAL"),
    ("C2", "R016_RELATION_NOT_PRESERVED"),
    ("C3", "R016_COLLAPSES_EQUATION"),
    ("C4", "R016_NOT_COHERENT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ("stage_transition",)
OWN_NEGATIVE = {
    "maps": [{"on_generators": [["a", "a"], ["b", "b"]], "source": 0, "target": 1}],
    "stages": [
        {"generators": ["a", "b"], "relations": []},
        {"generators": ["a", "b", "c"], "relations": [["a", "b"]]},
    ],
}
OWN_NEGATIVE_CODE = "R016_COLLAPSES_EQUATION"


def _presentation(stage):
    _require(isinstance(stage, dict) and set(stage) == {"generators", "relations"}, "R_SCHEMA")
    generators = [_text(g) for g in _seq(stage["generators"])]
    _require(generators and len(set(generators)) == len(generators), "R_SCHEMA")
    parent = {g: g for g in generators}

    def root(x):
        while parent[x] != x:
            x = parent[x]
        return x

    relations = []
    for pair in _seq(stage["relations"]):
        _seq(pair, 2)
        left, right = _text(pair[0]), _text(pair[1])
        _require(left in parent and right in parent, "R_SCHEMA")
        relations.append((left, right))
        a, b = root(left), root(right)
        if a != b:
            parent[max(a, b)] = min(a, b)
    return generators, relations, {g: root(g) for g in generators}


def _decide(payload):
    stages = [_presentation(stage) for stage in _seq(payload["stages"])]
    _require(len(stages) >= 2, "R_SCHEMA")
    maps = {}
    for entry in _seq(payload["maps"]):
        _require(isinstance(entry, dict) and set(entry) == {"on_generators", "source", "target"}, "R_SCHEMA")
        source, target = _nat(entry["source"]), _nat(entry["target"])
        _require(source < target < len(stages) and (source, target) not in maps, "R_SCHEMA")
        table = {}
        for pair in _seq(entry["on_generators"]):
            _seq(pair, 2)
            _require(isinstance(pair[0], str) and pair[0] not in table, "R_SCHEMA")
            table[pair[0]] = pair[1]
        maps[(source, target)] = table
    _require(all((i, i + 1) in maps for i in range(len(stages) - 1)), "R_SCHEMA")
    for (source, target), table in sorted(maps.items()):
        s_generators, s_relations, s_root = stages[source]
        t_generators, _, t_root = stages[target]
        _require(set(table) == set(s_generators) and all(v in t_generators for v in table.values()), "R016_MAP_PARTIAL")
        for left, right in s_relations:
            _require(t_root[table[left]] == t_root[table[right]], "R016_RELATION_NOT_PRESERVED")
        for index, x in enumerate(s_generators):
            for y in s_generators[index + 1 :]:
                if t_root[table[x]] == t_root[table[y]]:
                    _require(s_root[x] == s_root[y], "R016_COLLAPSES_EQUATION")
    for (i, k), direct in sorted(maps.items()):
        for j in range(i + 1, k):
            if (i, j) in maps and (j, k) in maps:
                for x in stages[i][0]:
                    _require(maps[(j, k)][maps[(i, j)][x]] == direct[x], "R016_NOT_COHERENT")
