"""Target checker of record for MSS-074, row 74 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 74): check typed columns and exact finite query semantics.
Negative instance: an absent column is refused during translation.

Input (closed): ``{"domains": {type: [value]}, "relations": [{"name": R,
"columns": [[column, type]]}], "rows": [[R, [value]]], "query": {"atoms":
[[R, [[column, term]]]], "output": [variable]}, "answers": [[value]]}``. A
term is a variable (``?name``) or a constant. An atom binds the columns it
names and leaves the others free; a stored row matches it when they agree on
every bound column.

Translation comes first: every atom names a declared relation and only its
columns, every constant lies in its column's type, and every variable has one
type. Then the stored rows are typed, and the query is evaluated by
enumerating matching rows atom by atom (a finite join, no sampling). The
claimed answers are compared with the recomputed answer set.

Declared input class: conjunctive queries with named-column atoms and
constants over finite typed domains; set semantics; no equality, negation,
disjunction or aggregation atoms.

Clauses, decided in this order:

- C1 ``R074_ABSENT_COLUMN``: an atom names an undeclared relation, or a
  column its relation does not have (the level's negative);
- C2 ``R074_TYPE_CLASH``: a variable is used at columns of two types, or a
  constant is not a value of its column's type;
- C3 ``R074_UNSAFE_OUTPUT``: an output variable occurs in no atom;
- C4 ``R074_ROW_TYPE``: a stored row has the wrong width, or a value outside
  its column's type;
- C5 ``R074_ANSWER_MISMATCH``: the claimed answers are not exactly the
  recomputed answer set.
"""

STAGE = 74
ROW_SHA256 = "sha256:45743e31540f0ecfef9ed17dac47e8c8f443254532ec9f6e6dde1f8fc8b5925e"
FIELDS = ("answers", "domains", "query", "relations", "rows")
CLAUSES = (
    ("C1", "R074_ABSENT_COLUMN"),
    ("C2", "R074_TYPE_CLASH"),
    ("C3", "R074_UNSAFE_OUTPUT"),
    ("C4", "R074_ROW_TYPE"),
    ("C5", "R074_ANSWER_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "answers": [["a"]],
    "domains": {"node": ["a", "b", "c"]},
    "query": {"atoms": [["edge", [["src", "?x"], ["weight", "?w"]]]], "output": ["?x"]},
    "relations": [{"columns": [["src", "node"], ["dst", "node"]], "name": "edge"}],
    "rows": [["edge", ["a", "b"]]],
}
OWN_NEGATIVE_CODE = "R074_ABSENT_COLUMN"


def _is_var(term):
    return term.startswith("?")


def _decide(payload):
    domains = payload["domains"]
    _require(isinstance(domains, dict) and domains, "R_SCHEMA")
    for values in domains.values():
        _require(len(set(_text(v) for v in _seq(values))) == len(values), "R_SCHEMA")
    schema = {}
    for relation in _seq(payload["relations"]):
        _require(isinstance(relation, dict) and set(relation) == {"columns", "name"}, "R_SCHEMA")
        name = _text(relation["name"])
        columns = {}
        order = []
        for column in _seq(relation["columns"]):
            _seq(column, 2)
            _require(_text(column[1]) in domains and _text(column[0]) not in columns, "R_SCHEMA")
            columns[column[0]] = column[1]
            order.append(column[0])
        _require(name not in schema and order, "R_SCHEMA")
        schema[name] = (order, columns)
    query = payload["query"]
    _require(isinstance(query, dict) and set(query) == {"atoms", "output"}, "R_SCHEMA")
    atoms = []
    for atom in _seq(query["atoms"]):
        _seq(atom, 2)
        bindings = []
        for pair in _seq(atom[1]):
            _seq(pair, 2)
            bindings.append((_text(pair[0]), _text(pair[1])))
        _require(len({column for column, _ in bindings}) == len(bindings), "R_SCHEMA")
        atoms.append((_text(atom[0]), bindings))
    output = [_text(v) for v in _seq(query["output"])]
    _require(atoms and output and all(_is_var(v) for v in output), "R_SCHEMA")
    # Translation.
    for relation, bindings in atoms:
        _require(relation in schema, "R074_ABSENT_COLUMN")
        for column, _ in bindings:
            _require(column in schema[relation][1], "R074_ABSENT_COLUMN")
    typing = {}
    for relation, bindings in atoms:
        for column, term in bindings:
            kind = schema[relation][1][column]
            if _is_var(term):
                _require(typing.setdefault(term, kind) == kind, "R074_TYPE_CLASH")
            else:
                _require(term in domains[kind], "R074_TYPE_CLASH")
    _require(all(v in typing for v in output), "R074_UNSAFE_OUTPUT")
    # Stored rows.
    table = {name: [] for name in schema}
    for row in _seq(payload["rows"]):
        _seq(row, 2)
        _require(_text(row[0]) in schema, "R074_ROW_TYPE")
        order, columns = schema[row[0]]
        values = _seq(row[1])
        _require(len(values) == len(order), "R074_ROW_TYPE")
        for column, value in zip(order, values):
            _require(isinstance(value, str) and value in domains[columns[column]], "R074_ROW_TYPE")
        table[row[0]].append(dict(zip(order, values)))
    # Evaluation: a finite join, atom by atom.
    found = set()

    def extend(index, assignment):
        if index == len(atoms):
            found.add(tuple(assignment[v] for v in output))
            return
        relation, bindings = atoms[index]
        for stored in table[relation]:
            trial = dict(assignment)
            fits = True
            for column, term in bindings:
                value = stored[column]
                if _is_var(term):
                    if trial.setdefault(term, value) != value:
                        fits = False
                        break
                elif term != value:
                    fits = False
                    break
            if fits:
                extend(index + 1, trial)

    extend(0, {})
    claimed = []
    for answer in _seq(payload["answers"]):
        claimed.append(tuple(_text(v) for v in _seq(answer, len(output))))
    _require(len(set(claimed)) == len(claimed), "R_SCHEMA")
    _require(set(claimed) == found, "R074_ANSWER_MISMATCH")
