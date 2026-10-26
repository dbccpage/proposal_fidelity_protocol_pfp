"""Target checker of record for MSS-008, row 8 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 8): replay triangle identities and rational primal-dual
feasibility. Negative instance: a zero-gap string without dual feasibility is
rejected.

Input (closed):
``{"vertices": [nat], "edges": [[tail, head]], "weights": [q], "cochain": [q],
"potential": [q], "flow": [q], "value": q, "adjunction": {"set": [str],
"pointed": [str], "base": str, "unit": [[x, image]], "counit": [[y, image]]}}``,
every ``q`` a canonical rational string.

The l1 half. For weights w > 0, cochain c and potential s (one entry per
vertex, in the order of ``vertices``), the primal value is
sum_e w_e |c_e - (s_head - s_tail)|. The flow y is a dual witness when it is
divergence-free and |y_e| <= w_e; its value is sum_e c_e y_e. Zero gap is the
two recomputed values being equal.

The adjunction half. The free pointed set on X is X + {"*"}, left adjoint to
the forgetful map. ``unit`` is eta_X : X -> X + {*}; ``counit`` is
epsilon_(Y,p) : Y + {*} -> Y. Both triangle identities are replayed element by
element: epsilon_F(X) . F(eta) = id on X + {*}, and U(epsilon) . eta_U = id on
Y. ``*`` is reserved and may not be an element of either set.

Clauses:

- C1 ``R008_CAPACITY``: |y_e| > w_e;
- C2 ``R008_NOT_DIVERGENCE_FREE``: the flow has nonzero divergence at a vertex;
- C3 ``R008_GAP``: primal and dual values differ;
- C4 ``R008_VALUE_MISMATCH``: the declared value is not the recomputed one;
- C5 ``R008_COUNIT_NOT_POINTED``: the counit does not send ``*`` to the base;
- C6 ``R008_TRIANGLE_LEFT``: epsilon_F . F(eta) is not the identity;
- C7 ``R008_TRIANGLE_RIGHT``: U(epsilon) . eta_U is not the identity (the
  constant counit, a legal pointed map, fails here).
"""

STAGE = 8
ROW_SHA256 = "sha256:45ac62cf9ddea213239162614f8989268ac11fb0ad76b479fd9ee2e53712fad8"
FIELDS = ("adjunction", "cochain", "edges", "flow", "potential", "value", "vertices", "weights")
CLAUSES = (
    ("C1", "R008_CAPACITY"),
    ("C2", "R008_NOT_DIVERGENCE_FREE"),
    ("C3", "R008_GAP"),
    ("C4", "R008_VALUE_MISMATCH"),
    ("C5", "R008_COUNIT_NOT_POINTED"),
    ("C6", "R008_TRIANGLE_LEFT"),
    ("C7", "R008_TRIANGLE_RIGHT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ("adjunction_unit",)
_ADJUNCTION = {
    "base": "p",
    "counit": [["*", "p"], ["p", "p"], ["q", "q"]],
    "pointed": ["p", "q"],
    "set": ["a"],
    "unit": [["a", "a"]],
}
OWN_NEGATIVE = {
    "adjunction": _ADJUNCTION,
    "cochain": ["1/1", "0/1", "0/1"],
    "edges": [[0, 1], [1, 2], [2, 0]],
    "flow": ["1/1", "0/1", "0/1"],
    "potential": ["0/1", "0/1", "0/1"],
    "value": "1/1",
    "vertices": [0, 1, 2],
    "weights": ["1/1", "1/1", "1/1"],
}
OWN_NEGATIVE_CODE = "R008_NOT_DIVERGENCE_FREE"
POINT = "*"


def _function(pairs, domain, codomain):
    table = {}
    for pair in _seq(pairs):
        _seq(pair, 2)
        _require(pair[0] in domain and pair[0] not in table and pair[1] in codomain, "R_SCHEMA")
        table[pair[0]] = pair[1]
    _require(set(table) == set(domain), "R_SCHEMA")
    return table


def _elements(value):
    items = [_text(item) for item in _seq(value)]
    _require(len(set(items)) == len(items) and not any(i.startswith(POINT) for i in items), "R_SCHEMA")
    return items


def _decide(payload):
    vertices = [_nat(v) for v in _seq(payload["vertices"])]
    _require(vertices and len(set(vertices)) == len(vertices), "R_SCHEMA")
    edges = []
    for edge in _seq(payload["edges"]):
        _seq(edge, 2)
        tail, head = _nat(edge[0]), _nat(edge[1])
        _require(tail in vertices and head in vertices, "R_SCHEMA")
        edges.append((tail, head))
    m = len(edges)
    _require(m >= 1, "R_SCHEMA")
    weights = _rats(payload["weights"], m)
    cochain = _rats(payload["cochain"], m)
    flow = _rats(payload["flow"], m)
    potential = dict(zip(vertices, _rats(payload["potential"], len(vertices))))
    _require(all(w > 0 for w in weights), "R_SCHEMA")
    for y, w in zip(flow, weights):
        _require(abs(y) <= w, "R008_CAPACITY")
    for x in vertices:
        divergence = sum((y for (t, h), y in zip(edges, flow) if h == x), Fraction(0)) - sum(
            (y for (t, h), y in zip(edges, flow) if t == x), Fraction(0)
        )
        _require(divergence == 0, "R008_NOT_DIVERGENCE_FREE")
    primal = sum(
        (w * abs(c - (potential[h] - potential[t])) for (t, h), w, c in zip(edges, weights, cochain)), Fraction(0)
    )
    dual = sum((c * y for c, y in zip(cochain, flow)), Fraction(0))
    _require(primal == dual, "R008_GAP")
    _require(_rat(payload["value"]) == primal, "R008_VALUE_MISMATCH")

    adjunction = payload["adjunction"]
    _require(isinstance(adjunction, dict) and set(adjunction) == {"base", "counit", "pointed", "set", "unit"}, "R_SCHEMA")
    xs = _elements(adjunction["set"])
    ys = _elements(adjunction["pointed"])
    base = _text(adjunction["base"])
    _require(base in ys, "R_SCHEMA")
    unit = _function(adjunction["unit"], xs, xs + [POINT])
    counit = _function(adjunction["counit"], ys + [POINT], ys)
    _require(counit[POINT] == base, "R008_COUNIT_NOT_POINTED")
    # epsilon at F(X) sends the new base point to the old one and fixes the rest;
    # F(eta) sends x to eta(x) and the base point to the new base point.
    new_point = POINT + POINT

    def epsilon_free(element):
        return POINT if element == new_point else element

    def free_eta(element):
        return new_point if element == POINT else unit[element]

    for element in xs + [POINT]:
        _require(epsilon_free(free_eta(element)) == element, "R008_TRIANGLE_LEFT")
    for element in ys:
        _require(counit[element] == element, "R008_TRIANGLE_RIGHT")
