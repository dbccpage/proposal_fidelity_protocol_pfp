"""Adapter for level 091: the engine's two formulas, languages, renaming and
bound written as the target checker's source and target formulas, symbol
tables, map and bound.  The formula ``f`` of ``translates(g, f)`` is the
source and ``g`` the target; a symbol's name and a variable's letter are
its hosted text; a symbol's arity is 1 when it is hosted ``unary`` and 2
when ``binary``; a prefix is its quantifiers in declared order, each written
``A`` (``every``) or ``E`` (``some``) followed by its variable's letter; the
quantifier-free part is written node by node (``reads`` as ``rel``,
``equal`` as ``eq``, ``negates`` as ``not``, ``both`` as ``and``,
``either`` as ``or``).  Written against the registered stage-91 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_091"
CLAUSES = (("C1", "R091_MAP"), ("C2", "R091_UNTYPED"), ("C3", "R091_QUANTIFIER_SWAP"),
           ("C4", "R091_SEMANTICS_DIFFER"))
COEFFICIENT_DOMAIN = {"source": "finite structures of one to three elements",
                      "target": "finite structures of one to three elements"}
SORTS = (("formula", "formula"), ("variable", "variable letter"), ("symbol", "relation symbol"),
         ("quantifier", "prefix quantifier"), ("node", "matrix node"), ("bound", "bound"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = ""
LOSS_ROWS = (
    ("target.names", "symbols and variables named by hosted texts", "names as strings", "PRESERVED"),
    ("target.prefix_order", "the declared order of a formula's quantifiers", "the order of the prefix word",
     "PRESERVED"),
    ("target.arity", "unary or binary as a hosted relation", "an arity number", "PRESERVED"),
)
NEAR = (("own_neg", "R091_QUANTIFIER_SWAP"), ("near_arity", "R091_MAP"), ("near_unbound", "R091_UNTYPED"),
        ("near_twice", "R091_UNTYPED"))
MUTATIONS = (("C1", "R091_MAP", "map_dropped", "near_unmapped"),
             ("C2", "R091_UNTYPED", "symbol_undeclared", "near_undeclared"),
             ("C3", "R091_QUANTIFIER_SWAP", "quantifiers_swapped", "mut"),
             ("C4", "R091_SEMANTICS_DIFFER", "quantifier_changed", "near_kinds"))
WORDS = {"reads": "rel", "equal": "eq", "negates": "not", "both": "and", "either": "or"}


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


class _Claim:
    def __init__(self, structure: dict[str, Any]) -> None:
        self.s = structure
        self.rel = [(str(n), [int(x) for x in a]) for n, a in structure["relations"]]
        self.text = {int(e): str(t) for e, t in structure.get("texts", [])}
        self.value = {int(e): int(Fraction(str(v))) for e, v in structure["values"]}
        (self.target, self.source), = [a for n, a in self.rel if n == "translates"]

    def has(self, name: str, *args: int) -> bool:
        return (name, list(args)) in self.rel

    def arity(self, s: int) -> int:
        return 1 if self.has("unary", s) else 2 if self.has("binary", s) else 0

    def language(self, side: int) -> dict[str, int]:
        return {self.text[a[0]]: self.arity(a[0]) for n, a in self.rel if n == "declared" and a[1] == side}

    def prefix(self, side: int) -> str:
        out = ""
        for q in _sort(self.s, "quantifier"):
            if self.has("opens", q, side):
                v = next(a[1] for n, a in self.rel if n == "binds" and a[0] == q)
                out += ("A" if self.has("every", q) else "E") + self.text[v]
        return out

    def node(self, n: int) -> list[Any]:
        for name, a in self.rel:
            if a[0] != n or name not in WORDS:
                continue
            if name == "negates":
                return ["not", self.node(a[1])]
            if name in ("both", "either"):
                return [WORDS[name], self.node(a[1]), self.node(a[2])]
            places = [self.text[b[1]] for m in ("first", "second") for k, b in self.rel if k == m and b[0] == n]
            return (["rel", self.text[a[1]]] if name == "reads" else ["eq"]) + places
        raise KeyError(n)

    def formula(self, side: int) -> dict[str, Any]:
        top = next(a[0] for n, a in self.rel if n == "matrix" and a[1] == side)
        return {"matrix": self.node(top), "prefix": self.prefix(side)}


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    c = _Claim(structure)
    return {"bound": c.value[_sort(structure, "bound")[0]],
            "map": {c.text[a[0]]: c.text[a[1]] for n, a in c.rel if n == "renamed"},
            "source": c.formula(c.source), "source_symbols": c.language(c.source),
            "target": c.formula(c.target), "target_symbols": c.language(c.target)}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def squares(source: object, positive: object) -> list[tuple[str, object, object]]:
    """The symbol translation: each hosted renaming ``s -> t`` with the arity
    ``s`` is hosted with (left), against the positive's map with the arity
    the target's table gives each image (right).  They agree exactly when
    the map is restated as hosted and keeps every arity."""
    assert isinstance(source, dict) and isinstance(positive, dict)
    c = _Claim(source)
    carried = sorted([c.text[a[0]], c.text[a[1]], c.arity(a[0])] for n, a in c.rel if n == "renamed")
    read = sorted([s, t, positive["target_symbols"][t]] for s, t in positive["map"].items())
    return [("symbol_translation", carried, read)]


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return ([["formula:0", "source"], ["formula:1", "target"], ["bound:0", "bound"]]
            + [[f"symbol:source:{n}", f"source_symbols:{n}"] for n in sorted(positive["source_symbols"])]
            + [[f"symbol:target:{n}", f"target_symbols:{n}"] for n in sorted(positive["target_symbols"])])
