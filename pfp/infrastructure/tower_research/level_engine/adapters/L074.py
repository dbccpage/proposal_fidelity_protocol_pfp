# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 074: the engine's types, tables, rows, question and
claimed answers written as the target checker's domains, relations, rows,
query and answers.  Types, values, tables, columns and variables are named
``T<k>``, ``v<k>``, ``R<k>``, ``c<k>`` and ``?x<k>`` by position; a table's
columns and a row's values follow the declared column order; an atom's
bindings are sorted by column name.  Written against the registered
stage-74 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_074"
CLAUSES = (("C1", "R074_ABSENT_COLUMN"), ("C2", "R074_TYPE_CLASH"), ("C3", "R074_UNSAFE_OUTPUT"),
           ("C4", "R074_ROW_TYPE"), ("C5", "R074_ANSWER_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "finite typed values", "target": "finite typed values"}
SORTS = (("type", "domain"), ("value", "value"), ("table", "relation"), ("column", "column"), ("row", "row"),
         ("atom", "atom"), ("var", "variable"), ("slot", "output position"), ("answer", "answer"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.semantics", "set semantics, no equality or negation", "set semantics", "PRESERVED"),)
NEAR = (("own_neg", "R074_ABSENT_COLUMN"),)
MUTATIONS = (("C1", "R074_ABSENT_COLUMN", "column_absent", "own_neg"),
             ("C2", "R074_TYPE_CLASH", "constant_untyped", "near_clash"),
             ("C3", "R074_UNSAFE_OUTPUT", "output_unbound", "near_unsafe"),
             ("C4", "R074_ROW_TYPE", "cell_untyped", "near_row"),
             ("C5", "R074_ANSWER_MISMATCH", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    rel = [(n, list(a)) for n, a in structure["relations"]]
    nm: dict[int, str] = {}
    for sort, prefix in (("type", "T"), ("value", "v"), ("table", "R"), ("column", "c"), ("var", "?x")):
        for k, e in enumerate(_sort(structure, sort)):
            nm[e] = f"{prefix}{k}"
    cols = _sort(structure, "column")
    col_of = {a[0]: a[1] for n, a in rel if n == "column_of"}
    typed = {a[0]: a[1] for n, a in rel if n == "typed"}
    table_cols = {t: [c for c in cols if col_of.get(c) == t] for t in _sort(structure, "table")}
    cell = {(a[0], a[1]): a[2] for n, a in rel if n == "cell"}
    stored = {a[0]: a[1] for n, a in rel if n == "stored"}
    out = {a[0]: a[1] for n, a in rel if n == "out"}
    gives = {(a[0], a[1]): a[2] for n, a in rel if n == "gives"}
    slots = _sort(structure, "slot")
    return {
        "answers": [[nm[gives[(n, s)]] for s in slots] for n in _sort(structure, "answer")],
        "domains": {nm[t]: [nm[a[0]] for n, a in rel if n == "member" and a[1] == t] for t in _sort(structure, "type")},
        "query": {"atoms": [[nm[next(a[1] for n, a in rel if n == "atom_on" and a[0] == at)],
                             sorted([nm[a[1]], nm[a[2]]] for n, a in rel if n in ("binds_var", "binds_const")
                                    and a[0] == at)] for at in _sort(structure, "atom")],
                  "output": [nm[out[s]] for s in slots]},
        "relations": [{"columns": [[nm[c], nm[typed[c]]] for c in table_cols[t]], "name": nm[t]}
                      for t in _sort(structure, "table")],
        "rows": [[nm[stored[r]], [nm[cell[(r, c)]] for c in table_cols[stored[r]]]] for r in _sort(structure, "row")],
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"table:{k}", f"relation:{r['name']}"] for k, r in enumerate(positive["relations"])]
