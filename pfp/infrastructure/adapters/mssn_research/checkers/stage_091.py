"""Target checker of record for MSS-091, row 91 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 91): check semantics on the declared decidable fragment.
Negative instance: changing quantifier order without proof is rejected.

Input (closed): ``{"source_symbols": {R: arity}, "target_symbols": {R:
arity}, "map": {R: R'}, "source": formula, "target": formula, "bound": k}``.
A formula is ``{"prefix": word, "matrix": ast}``: the prefix is a string of
quantifier letters ``A`` (for all) and ``E`` (exists), each followed by a
one-letter variable, outermost first; the matrix is quantifier-free:
``["rel", R, x]``, ``["rel", R, x, y]``, ``["eq", x, y]``, ``["not", p]``,
``["and", p, q]``, ``["or", p, q]``.

The declared decidable fragment is every structure for the source symbols
(arity 1 or 2) on the domains {0, ..., n - 1} for 1 <= n <= k. The target is
read through the map (a typed translation: the map must be total on the source
symbols and preserve arity). The checker evaluates both formulas on every
structure of the fragment, so "equivalent" is decided by exhaustion there and
nowhere else. A target whose prefix reorders the source's and that disagrees
somewhere in the fragment is refused as a quantifier swap without proof,
whatever else it changed; a reordering that agrees on the whole fragment is
proved within it.

Declared input class: prenex formulas, unary and binary symbols, bound k <= 3
and at most 12 relation bits at the top domain size.

Clauses, decided in this order:

- C1 ``R091_MAP``: the map is not total on the source symbols, or names an
  undeclared target symbol, or changes an arity;
- C2 ``R091_UNTYPED``: a formula uses an undeclared symbol, a wrong arity, or
  a variable its prefix does not bind (or binds twice);
- C3 ``R091_QUANTIFIER_SWAP``: the target's prefix reorders the source's
  (same quantifiers and variables, another order), and the two disagree on
  some structure of the fragment (the level's negative);
- C4 ``R091_SEMANTICS_DIFFER``: any other disagreement on the fragment.
"""

from itertools import product

STAGE = 91
ROW_SHA256 = "sha256:08f97c298b12e3a68c48c2ba13e81bd68a165ae6893ae4c865ff5e6877bb87ae"
FIELDS = ("bound", "map", "source", "source_symbols", "target", "target_symbols")
CLAUSES = (
    ("C1", "R091_MAP"),
    ("C2", "R091_UNTYPED"),
    ("C3", "R091_QUANTIFIER_SWAP"),
    ("C4", "R091_SEMANTICS_DIFFER"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ("symbol_translation",)
OWN_NEGATIVE = {
    "bound": 2,
    "map": {"E": "Adj"},
    "source": {"matrix": ["rel", "E", "x", "y"], "prefix": "AxEy"},
    "source_symbols": {"E": 2},
    "target": {"matrix": ["rel", "Adj", "x", "y"], "prefix": "EyAx"},
    "target_symbols": {"Adj": 2},
}
OWN_NEGATIVE_CODE = "R091_QUANTIFIER_SWAP"
_PREFIX = re.compile(r"(?:[AE][a-z])*")


def _symbols(value):
    _require(isinstance(value, dict) and value, "R_SCHEMA")
    for name, arity in value.items():
        _text(name)
        _require(arity in (1, 2) and not isinstance(arity, bool), "R_SCHEMA")
    return value


def _formula(value):
    _require(isinstance(value, dict) and set(value) == {"matrix", "prefix"}, "R_SCHEMA")
    prefix = value["prefix"]
    _require(isinstance(prefix, str) and _PREFIX.fullmatch(prefix) is not None, "R_SCHEMA")
    return [(prefix[i], prefix[i + 1]) for i in range(0, len(prefix), 2)], value["matrix"]


def _typed(matrix, symbols, bound):
    """Refuse unless the matrix is well formed over ``symbols`` with variables in ``bound``."""
    _require(isinstance(matrix, list) and matrix, "R_SCHEMA")
    head = matrix[0]
    if head == "rel":
        _require(len(matrix) in (3, 4) and all(isinstance(t, str) for t in matrix[1:]), "R_SCHEMA")
        _require(symbols.get(matrix[1]) == len(matrix) - 2, "R091_UNTYPED")
        _require(all(t in bound for t in matrix[2:]), "R091_UNTYPED")
    elif head == "eq":
        _require(len(matrix) == 3 and all(isinstance(t, str) for t in matrix[1:]), "R_SCHEMA")
        _require(all(t in bound for t in matrix[1:]), "R091_UNTYPED")
    elif head == "not":
        _require(len(matrix) == 2, "R_SCHEMA")
        _typed(matrix[1], symbols, bound)
    else:
        _require(head in ("and", "or") and len(matrix) == 3, "R_SCHEMA")
        _typed(matrix[1], symbols, bound)
        _typed(matrix[2], symbols, bound)


def _holds(matrix, model, env, rename):
    head = matrix[0]
    if head == "rel":
        return tuple(env[t] for t in matrix[2:]) in model[rename.get(matrix[1], matrix[1])]
    if head == "eq":
        return env[matrix[1]] == env[matrix[2]]
    if head == "not":
        return not _holds(matrix[1], model, env, rename)
    left = _holds(matrix[1], model, env, rename)
    right = _holds(matrix[2], model, env, rename)
    return (left and right) if head == "and" else (left or right)


def _truth(prefix, matrix, model, size, rename, env=None):
    env = {} if env is None else env
    if not prefix:
        return _holds(matrix, model, env, rename)
    (kind, var), rest = prefix[0], prefix[1:]
    values = (_truth(rest, matrix, model, size, rename, dict(env, **{var: d})) for d in range(size))
    return all(values) if kind == "A" else any(values)


def _structures(symbols, size):
    names = sorted(symbols)
    tuples = {name: [t for t in product(range(size), repeat=symbols[name])] for name in names}
    cells = [(name, t) for name in names for t in tuples[name]]
    for bits in product((False, True), repeat=len(cells)):
        model = {name: set() for name in names}
        for (name, t), bit in zip(cells, bits):
            if bit:
                model[name].add(t)
        yield model


def _decide(payload):
    source_symbols = _symbols(payload["source_symbols"])
    target_symbols = _symbols(payload["target_symbols"])
    mapping = payload["map"]
    _require(isinstance(mapping, dict), "R_SCHEMA")
    bound = _nat(payload["bound"])
    _require(1 <= bound <= 3, "R_SCHEMA")
    _require(sum(bound ** arity for arity in source_symbols.values()) <= 12, "R_SCHEMA")
    source_prefix, source_matrix = _formula(payload["source"])
    target_prefix, target_matrix = _formula(payload["target"])
    _require(set(mapping) == set(source_symbols), "R091_MAP")
    for name, image in mapping.items():
        _require(target_symbols.get(image) == source_symbols[name], "R091_MAP")
    for prefix, matrix, symbols in ((source_prefix, source_matrix, source_symbols),
                                    (target_prefix, target_matrix, target_symbols)):
        variables = [var for _, var in prefix]
        _require(len(set(variables)) == len(variables), "R091_UNTYPED")
        _typed(matrix, symbols, set(variables))
    inverse = {image: name for name, image in mapping.items()}
    agree = True
    for size in range(1, bound + 1):
        for model in _structures(source_symbols, size):
            left = _truth(source_prefix, source_matrix, model, size, {})
            right = _truth(target_prefix, target_matrix, model, size, inverse)
            if left != right:
                agree = False
    swap = sorted(source_prefix) == sorted(target_prefix) and source_prefix != target_prefix
    _require(agree or not swap, "R091_QUANTIFIER_SWAP")
    _require(agree, "R091_SEMANTICS_DIFFER")
